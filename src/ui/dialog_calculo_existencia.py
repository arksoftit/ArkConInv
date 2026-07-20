import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.embedded_db import get_db_connection
from core.system_info import get_current_user, get_machine_name


class DialogCalculoExistencia(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Cálculo y Valorización de Existencias por Periodo")
        self.geometry("1150x680")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (1150 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (680 // 2)
        self.geometry(f"+{x}+{y}")

        # Estructuras de datos para filtros seguros
        self.uo_map = {}       
        self.deposito_map = {} 
        self._resultados_originales = {}
        
        # Variables para ordenamiento
        self._sort_column = None
        self._sort_reverse = False
        
        self._create_widgets()
        self._cargar_datos_filtro()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Frame de Filtros Reconstruido ---
        filtro_frame = ttk.LabelFrame(main_frame, text="Filtros de Cálculo", padding=10)
        filtro_frame.pack(fill=tk.X, padx=5, pady=5)

        lbl_uo = ttk.Label(filtro_frame, text="Unidad Operativa:", font=("Segoe UI", 9, "bold"))
        lbl_uo.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.cmb_uo = ttk.Combobox(filtro_frame, state="readonly", width=35, font=("Segoe UI", 9))
        self.cmb_uo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.cmb_uo.bind("<<ComboboxSelected>>", lambda e: self.btn_calcular.focus_set())

        lbl_dep = ttk.Label(filtro_frame, text="Depósito:", font=("Segoe UI", 9, "bold"))
        lbl_dep.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.cmb_deposito = ttk.Combobox(filtro_frame, state="readonly", width=35, font=("Segoe UI", 9))
        self.cmb_deposito.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        self.btn_calcular = ttk.Button(
            filtro_frame, 
            text="Calcular Existencia Inicial", 
            command=self._calcular_existencia,
            style="Accent.TButton"
        )
        self.btn_calcular.grid(row=0, column=2, rowspan=2, padx=20, pady=5, sticky=tk.NS)

        self.lbl_status = ttk.Label(filtro_frame, text="", font=("Segoe UI", 9), foreground="#0055AA")
        self.lbl_status.grid(row=2, column=0, columnspan=3, padx=5, pady=(5,0), sticky=tk.W)

        # --- Frame de Resultados (Treeview) ---
        resultados_frame = ttk.LabelFrame(main_frame, text="Resultados del Cálculo y Valorización", padding=10)
        resultados_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = (
            "Producto", "Descripción", "UO", "Depósito",
            "Ex. Actual", "Entradas", "Salidas",
            "Inicial Calculado", "Inicial Simulado", "Final Calculado", "Ajuste Estimado",
            "Costo Local", "Costo Ref.", "Valor Inicial (Bs)"
        )

        self.tree_resultados = ttk.Treeview(resultados_frame, columns=columns, show="headings", height=18)

        col_widths = {
            "Producto": 80, "Descripción": 180, "UO": 60, "Depósito": 60,
            "Ex. Actual": 80, "Entradas": 80, "Salidas": 80,
            "Inicial Calculado": 110, "Inicial Simulado": 100,
            "Final Calculado": 100, "Ajuste Estimado": 100,
            "Costo Local": 90, "Costo Ref.": 90, "Valor Inicial (Bs)": 110
        }

        # Configuración de cabeceras con soporte para ordenamiento
        for col in columns:
            self.tree_resultados.heading(col, text=col, command=lambda c=col: self._toggle_sort(c))
            width = col_widths.get(col, 80)
            anchor = tk.E if any(k in col for k in ["Actual", "Entradas", "Salidas", "Calculado", "Simulado", "Ajuste", "Costo", "Valor"]) else tk.W
            self.tree_resultados.column(col, anchor=anchor, width=width)

        scrollbar_y = ttk.Scrollbar(resultados_frame, orient=tk.VERTICAL, command=self.tree_resultados.yview)
        scrollbar_x = ttk.Scrollbar(resultados_frame, orient=tk.HORIZONTAL, command=self.tree_resultados.xview)
        self.tree_resultados.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree_resultados.grid(row=0, column=0, sticky=tk.NSEW)
        scrollbar_y.grid(row=0, column=1, sticky=tk.NS)
        scrollbar_x.grid(row=1, column=0, sticky=tk.EW)

        resultados_frame.grid_rowconfigure(0, weight=1)
        resultados_frame.grid_columnconfigure(0, weight=1)

        # --- Frame de Operaciones (Botones) ---
        operacion_frame = ttk.Frame(main_frame)
        operacion_frame.pack(fill=tk.X, padx=5, pady=5)

        self.btn_filtrar_negativos_inicial = ttk.Button(operacion_frame, text="Mostrar Solo Saldo Inicial Negativo", command=self._filtrar_saldo_inicial_negativo, state=tk.DISABLED)
        self.btn_filtrar_negativos_actual = ttk.Button(operacion_frame, text="Mostrar Solo Existencia Actual Negativa", command=self._filtrar_existencia_actual_negativa, state=tk.DISABLED)
        self.btn_calcular_ajustes = ttk.Button(operacion_frame, text="Calcular Ajustes Requeridos", command=self._calcular_ajustes_requeridos, state=tk.DISABLED)
        self.btn_guardar = ttk.Button(operacion_frame, text="Guardar en ark_existencia_periodo", command=self._guardar_en_periodo, state=tk.DISABLED)
        
        # NUEVO BOTÓN LIMPIAR
        self.btn_limpiar = ttk.Button(operacion_frame, text="Limpiar", command=self._limpiar_treeview, style="Danger.TButton")

        self.btn_filtrar_negativos_inicial.pack(side=tk.LEFT, padx=5, pady=2)
        self.btn_filtrar_negativos_actual.pack(side=tk.LEFT, padx=5, pady=2)
        self.btn_calcular_ajustes.pack(side=tk.LEFT, padx=5, pady=2)
        self.btn_guardar.pack(side=tk.LEFT, padx=5, pady=2)
        self.btn_limpiar.pack(side=tk.LEFT, padx=5, pady=2)
        
        ttk.Button(operacion_frame, text="Cerrar", command=self.destroy).pack(side=tk.RIGHT, padx=5, pady=2)

    def _cargar_datos_filtro(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT exc_uo_Codigo FROM ark_existencia_calculadas ORDER BY exc_uo_Codigo")
            uos = [row[0] for row in cursor.fetchall()]
            
            self.uo_map = {"Todas las UO": None}
            uo_values = ["Todas las UO"]
            for uo in uos:
                display = f"{uo} - Gestion Administrativa" if uo == "010101" else f"{uo} - Gestion Financiera"
                self.uo_map[display] = uo
                uo_values.append(display)
            
            self.cmb_uo['values'] = uo_values
            self.cmb_uo.current(0)

            cursor.execute("SELECT DISTINCT exc_dep_codigo FROM ark_existencia_calculadas ORDER BY exc_dep_codigo")
            deps = [row[0] for row in cursor.fetchall()]
            
            self.deposito_map = {"Todos los depósitos": None}
            dep_values = ["Todos los depósitos"]
            for dep in deps:
                display = f"{dep} - Almacén Principal"
                self.deposito_map[display] = dep
                dep_values.append(display)
                
            self.cmb_deposito['values'] = dep_values
            self.cmb_deposito.current(0)
            
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los filtros:\n{e}")

    def _toggle_sort(self, col):
        """Maneja el ordenamiento ascendente/descendente al hacer clic en la cabecera."""
        if self._sort_column == col:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = col
            self._sort_reverse = False

        # Determinar si es numérico o texto
        numeric_cols = ["Ex. Actual", "Entradas", "Salidas", "Inicial Calculado", 
                        "Inicial Simulado", "Final Calculado", "Ajuste Estimado", 
                        "Costo Local", "Costo Ref.", "Valor Inicial (Bs)"]
        
        is_numeric = col in numeric_cols

        # Obtener todos los items actuales
        items = [(self.tree_resultados.set(item, col), item) for item in self.tree_resultados.get_children('')]
        
        # Función de clave para ordenar
        def sort_key(t):
            val = t[0]
            if is_numeric:
                try:
                    return float(val.replace(',', '').replace('.', '')) if val else 0.0
                except ValueError:
                    return 0.0
            return val.lower() if val else ""

        items.sort(key=sort_key, reverse=self._sort_reverse)

        # Reordenar en el treeview
        for index, (_, item) in enumerate(items):
            self.tree_resultados.move(item, '', index)

        # Actualizar texto de cabecera con indicador
        arrow = " ▲" if not self._sort_reverse else " ▼"
        for c in self.tree_resultados["columns"]:
            current_text = self.tree_resultados.heading(c)["text"]
            clean_text = current_text.replace(" ▲", "").replace(" ▼", "")
            if c == col:
                self.tree_resultados.heading(c, text=f"{clean_text}{arrow}")
            else:
                self.tree_resultados.heading(c, text=clean_text)

    def _limpiar_treeview(self):
        """Vacia el Treeview y resetea el estado de la ventana."""
        for item in self.tree_resultados.get_children():
            self.tree_resultados.delete(item)
        
        self._resultados_originales.clear()
        self._sort_column = None
        self._sort_reverse = False
        
        # Resetear cabeceras
        columns = self.tree_resultados["columns"]
        for col in columns:
            current_text = self.tree_resultados.heading(col)["text"]
            clean_text = current_text.replace(" ▲", "").replace(" ▼", "")
            self.tree_resultados.heading(col, text=clean_text)
            
        self.lbl_status.config(text="Vista limpiada. Seleccione filtros y calcule nuevamente.", foreground="orange")
        self._deshabilitar_botones_operacion()

    def _habilitar_botones_operacion(self):
        self.btn_filtrar_negativos_inicial.config(state=tk.NORMAL)
        self.btn_filtrar_negativos_actual.config(state=tk.NORMAL)
        self.btn_calcular_ajustes.config(state=tk.NORMAL)
        self.btn_guardar.config(state=tk.NORMAL)

    def _deshabilitar_botones_operacion(self):
        self.btn_filtrar_negativos_inicial.config(state=tk.DISABLED)
        self.btn_filtrar_negativos_actual.config(state=tk.DISABLED)
        self.btn_calcular_ajustes.config(state=tk.DISABLED)
        self.btn_guardar.config(state=tk.DISABLED)

    def _calcular_existencia(self):
        try:
            for item in self.tree_resultados.get_children():
                self.tree_resultados.delete(item)
            self._resultados_originales.clear()
            self._sort_column = None
            self._sort_reverse = False

            self.config(cursor="watch")
            self.update()

            uo_display = self.cmb_uo.get()
            dep_display = self.cmb_deposito.get()
            
            uo_codigo_filtro = self.uo_map.get(uo_display)
            dep_codigo_filtro = self.deposito_map.get(dep_display)

            conn = get_db_connection()
            cursor = conn.cursor()

            query_actual = "SELECT exa_codigoproducto, exa_uo_Codigo, exa_codigodeposito, exa_existencia FROM ark_existencia_actual WHERE 1=1"
            params_actual = []
            if uo_codigo_filtro:
                query_actual += " AND exa_uo_Codigo = ?"
                params_actual.append(uo_codigo_filtro)
            if dep_codigo_filtro:
                query_actual += " AND exa_codigodeposito = ?"
                params_actual.append(dep_codigo_filtro)
            
            cursor.execute(query_actual, params_actual)
            existencias_actuales = {}
            for row in cursor.fetchall():
                codigo, uo, dep, existencia = row
                clave = (uo, dep, codigo)
                existencias_actuales[clave] = existencia or 0.0

            query_movimientos = """
                SELECT exc_uo_Codigo, exc_dep_codigo, exc_item_codigo,
                       exc_compras, exc_cargos, exc_nota_entrega_proveedor, exc_dev_ventas,
                       exc_ajustes_mas, exc_transferencias_mas,
                       exc_ventas, exc_descargos, exc_nota_entrega_clientes,
                       exc_dev_compras, exc_ajustes_menos, exc_transferencias_menos,
                       exc_costos_local, exc_costos_referencial, exc_factor_referencial
                FROM ark_existencia_calculadas
                WHERE 1=1
            """
            params_mov = []
            if uo_codigo_filtro:
                query_movimientos += " AND exc_uo_Codigo = ?"
                params_mov.append(uo_codigo_filtro)
            if dep_codigo_filtro:
                query_movimientos += " AND exc_dep_codigo = ?"
                params_mov.append(dep_codigo_filtro)
            
            query_movimientos += " ORDER BY exc_uo_Codigo, exc_dep_codigo, exc_item_codigo"
            
            cursor.execute(query_movimientos, params_mov)
            movimientos = cursor.fetchall()

            cursor.execute("SELECT inv_codigo, inv_descripcion FROM ark_inventario")
            productos = {row[0]: row[1] for row in cursor.fetchall()}

            conn.close()

            for i, row in enumerate(movimientos):
                item_id = f"res_{i}"
                uo, dep, item = row[0], row[1], row[2]

                compras, cargos, notas_prov, dev_ventas, aj_mas, trans_mas = [row[j] or 0.0 for j in range(3, 9)]
                ventas, descargos, notas_cli, dev_compras, aj_menos, trans_menos = [row[j] or 0.0 for j in range(9, 15)]
                costo_local, costo_ref, factor = row[15] or 0.0, row[16] or 0.0, row[17] or 1.0

                entradas = compras + cargos + notas_prov + dev_ventas + aj_mas + trans_mas
                salidas = ventas + descargos + notas_cli + dev_compras + aj_menos + trans_menos

                clave = (uo, dep, item)
                exa_real = existencias_actuales.get(clave, 0.0)
                saldo_inicial_teorico = exa_real - entradas + salidas

                res = {
                    'codigo_producto': item,
                    'descripcion_producto': productos.get(item, ''),
                    'uo_codigo': uo,
                    'deposito_codigo': dep,
                    'existencia_actual': exa_real,
                    'entradas': entradas,
                    'salidas': salidas,
                    'saldo_inicial_calculado': saldo_inicial_teorico,
                    'costo_local': costo_local,
                    'costo_referencial': costo_ref,
                    'factor': factor
                }

                self._resultados_originales[item_id] = res

                self.tree_resultados.insert("", tk.END, iid=item_id, values=(
                    item,
                    productos.get(item, ''),
                    uo, dep,
                    f"{exa_real:,.2f}",
                    f"{entradas:,.2f}",
                    f"{salidas:,.2f}",
                    f"{saldo_inicial_teorico:,.2f}",
                    "", "", "",
                    f"{costo_local:,.4f}",
                    f"{costo_ref:,.4f}",
                    f"{saldo_inicial_teorico * costo_local:,.2f}"
                ))

            self._habilitar_botones_operacion()
            self.config(cursor="")

            uos_unicas = sorted(set(r['uo_codigo'] for r in self._resultados_originales.values()))
            msg = f"Cálculo finalizado. Registros: {len(movimientos)} | UOs: {', '.join(uos_unicas)}"
            self.lbl_status.config(text=f"✔ {msg}", foreground="green")

        except Exception as e:
            self.config(cursor="")
            self._deshabilitar_botones_operacion()
            messagebox.showerror("Error Crítico", f"Ocurrió un error al calcular las existencias:\n\n{e}")

    def _filtrar_saldo_inicial_negativo(self):
        for item in self.tree_resultados.get_children():
            self.tree_resultados.delete(item)
        for item_id, res in self._resultados_originales.items():
            if res['saldo_inicial_calculado'] < 0:
                self._insertar_fila(item_id, res)

    def _filtrar_existencia_actual_negativa(self):
        for item in self.tree_resultados.get_children():
            self.tree_resultados.delete(item)
        for item_id, res in self._resultados_originales.items():
            if res['existencia_actual'] < 0:
                self._insertar_fila(item_id, res)

    def _calcular_ajustes_requeridos(self):
        try:
            for item in self.tree_resultados.get_children():
                self.tree_resultados.delete(item)

            for item_id, res in self._resultados_originales.items():
                try:
                    exa_actual = float(res.get('existencia_actual', 0.0) or 0.0)
                    entradas = float(res.get('entradas', 0.0) or 0.0)
                    salidas = float(res.get('salidas', 0.0) or 0.0)

                    si_teorico = exa_actual - entradas + salidas
                    ajuste_inicial = max(0.0, -si_teorico)
                    inicial_simulado = si_teorico + ajuste_inicial
                    final_simulado = inicial_simulado - entradas + salidas
                    ajuste_total = max(0.0, -si_teorico, -final_simulado)

                    res['saldo_inicial_calculado'] = si_teorico
                    res['inicial_simulado'] = inicial_simulado
                    res['final_simulado'] = final_simulado
                    res['ajuste_requerido'] = ajuste_total

                    self.tree_resultados.insert("", tk.END, iid=item_id, values=(
                        str(res.get('codigo_producto', '')),
                        str(res.get('descripcion_producto', '')),
                        str(res.get('uo_codigo', '')),
                        str(res.get('deposito_codigo', '')),
                        f"{exa_actual:,.2f}",
                        f"{entradas:,.2f}",
                        f"{salidas:,.2f}",
                        f"{si_teorico:,.2f}",
                        f"{inicial_simulado:,.2f}",
                        f"{final_simulado:,.2f}",
                        f"{ajuste_total:,.2f}",
                        f"{float(res.get('costo_local', 0.0) or 0.0):,.4f}",
                        f"{float(res.get('costo_referencial', 0.0) or 0.0):,.4f}",
                        f"{inicial_simulado * float(res.get('costo_local', 0.0) or 0.0):,.2f}"
                    ))
                except Exception as e:
                    print(f"Error procesando {item_id}: {e}")
                    continue

            messagebox.showinfo("Éxito", f"Ajustes calculados. {len(self._resultados_originales)} registros procesados.")

        except Exception as e:
            messagebox.showerror("Error Crítico", f"Falló el cálculo de ajustes:\n{e}")

    def _insertar_fila(self, item_id, res):
        tiene_ajustes = 'inicial_simulado' in res
        if tiene_ajustes:
            self.tree_resultados.insert("", tk.END, iid=item_id, values=(
                res.get('codigo_producto', ''),
                res.get('descripcion_producto', ''),
                res.get('uo_codigo', ''),
                res.get('deposito_codigo', ''),
                f"{res['existencia_actual']:,.2f}",
                f"{res['entradas']:,.2f}",
                f"{res['salidas']:,.2f}",
                f"{res['saldo_inicial_calculado']:,.2f}",
                f"{res['inicial_simulado']:,.2f}",
                f"{res['final_simulado']:,.2f}",
                f"{res.get('ajuste_requerido', 0.0):,.2f}",
                f"{res.get('costo_local', 0.0):,.4f}",
                f"{res.get('costo_referencial', 0.0):,.4f}",
                f"{res['inicial_simulado'] * res.get('costo_local', 0.0):,.2f}"
            ))
        else:
            self.tree_resultados.insert("", tk.END, iid=item_id, values=(
                res.get('codigo_producto', ''),
                res.get('descripcion_producto', ''),
                res.get('uo_codigo', ''),
                res.get('deposito_codigo', ''),
                f"{res['existencia_actual']:,.2f}",
                f"{res['entradas']:,.2f}",
                f"{res['salidas']:,.2f}",
                f"{res['saldo_inicial_calculado']:,.2f}",
                "", "", "",
                f"{res.get('costo_local', 0.0):,.4f}",
                f"{res.get('costo_referencial', 0.0):,.4f}",
                f"{res['saldo_inicial_calculado'] * res.get('costo_local', 0.0):,.2f}"
            ))

    def _guardar_en_periodo(self):
        if not self._resultados_originales:
            messagebox.showwarning("Advertencia", "No hay resultados para guardar.")
            return

        if messagebox.askyesno("Confirmar Guardado", f"¿Guardar {len(self._resultados_originales)} registros en ark_existencia_periodo?"):
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                usuario = get_current_user()
                maquina = get_machine_name()
                fecha_hoy = datetime.now().strftime("%Y-%m-%d")
                hora_hoy = datetime.now().strftime("%H:%M:%S")

                for i, res in enumerate(self._resultados_originales.values()):
                    inicial_a_guardar = res.get('inicial_simulado', res.get('saldo_inicial_calculado', 0.0))
                    cursor.execute("""
                        INSERT OR REPLACE INTO ark_existencia_periodo (
                            exp_uo_Codigo, exp_dep_codigo, exp_item_codigo,
                            exp_costos_local, exp_costos_referencial, exp_factor_referencial,
                            exp_inicial, exp_op_entradas, exp_op_salidas,
                            exp_cant_entradas, exp_cant_salidas, exp_final,
                            exp_fecha_ini, exp_fecha_fin,
                            exp_SystemDate, exp_SystemTime, exp_NameMachine, exp_UserCreator
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        res.get('uo_codigo'),
                        res.get('deposito_codigo'),
                        res.get('codigo_producto'),
                        res.get('costo_local', 0.0),
                        res.get('costo_referencial', 0.0),
                        res.get('factor', 1.0),
                        inicial_a_guardar,
                        res.get('entradas', 0.0) * res.get('costo_local', 0.0),
                        res.get('salidas', 0.0) * res.get('costo_local', 0.0),
                        res.get('entradas', 0.0),
                        res.get('salidas', 0.0),
                        res.get('existencia_actual', 0.0),
                        fecha_hoy, fecha_hoy,
                        fecha_hoy, hora_hoy, maquina, usuario
                    ))
                    if i % 100 == 0:
                        conn.commit()

                conn.commit()
                conn.close()
                messagebox.showinfo("Éxito", "Registros guardados exitosamente en ark_existencia_periodo.")
                self.btn_guardar.config(state=tk.DISABLED)

            except Exception as e:
                messagebox.showerror("Error Crítico", f"Falló el guardado:\n{e}")