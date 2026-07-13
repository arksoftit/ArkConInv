import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.embedded_db import get_db_connection
from core.system_info import get_current_user, get_machine_name
from core.utils import formato_monto, formato_cantidad

class DialogCalculoExistencia(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Cálculo y Valorización de Existencias por Periodo")
        self.geometry("1100x650")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (1100 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (650 // 2)
        self.geometry(f"+{x}+{y}")
        
        self.uo_data = {}
        self.deposito_data = {}
        self._resultados_originales = {}
        
        self._create_widgets()
        self._cargar_datos_iniciales()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Frame de Filtros (sin periodo, basado en ark_existencia_calculadas) ---
        filtros_frame = ttk.LabelFrame(main_frame, text="Filtros de Cálculo", padding=10)
        filtros_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(filtros_frame, text="Unidad Operativa:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.cmb_uo = ttk.Combobox(filtros_frame, state="readonly", width=30)
        self.cmb_uo.grid(row=0, column=1, sticky=tk.W, padx=(0, 10), pady=2)
        
        ttk.Label(filtros_frame, text="Depósito:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.cmb_deposito = ttk.Combobox(filtros_frame, state="readonly", width=30)
        self.cmb_deposito.grid(row=1, column=1, sticky=tk.W, padx=(0, 10), pady=2)
        
        self.btn_calcular = ttk.Button(filtros_frame, text="Calcular Existencia Inicial", command=self._calcular_existencia)
        self.btn_calcular.grid(row=0, column=2, rowspan=2, padx=(20, 0), pady=2, sticky=tk.N)
        
        # --- Frame de Resultados (Treeview) ---
        resultados_frame = ttk.LabelFrame(main_frame, text="Resultados del Cálculo y Valorización", padding=10)
        resultados_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = (
            "Producto", "Descripción", "UO", "Depósito", 
            "Ex. Actual", "Entradas", "Salidas", 
            "Saldo Inicial Teórico", "Inicial Simulado", "Final Simulado", "Ajuste Total",
            "Costo Local", "Costo Ref.", "Valor Inicial (Bs)"
        )
        
        self.tree_resultados = ttk.Treeview(resultados_frame, columns=columns, show="headings", height=18)
        
        col_widths = {
            "Producto": 80, "Descripción": 180, "UO": 60, "Depósito": 60,
            "Ex. Actual": 80, "Entradas": 80, "Salidas": 80,
            "Saldo Inicial Teórico": 110, "Inicial Simulado": 100, 
            "Final Simulado": 100, "Ajuste Total": 90,
            "Costo Local": 90, "Costo Ref.": 90, "Valor Inicial (Bs)": 110
        }
        
        for col in columns:
            self.tree_resultados.heading(col, text=col)
            width = col_widths.get(col, 80)
            anchor = tk.E if "Actual" in col or "Entradas" in col or "Salidas" in col or "Teórico" in col or "Simulado" in col or "Ajuste" in col or "Costo" in col or "Valor" in col else tk.W
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
        
        self.btn_filtrar_negativos_inicial.pack(side=tk.LEFT, padx=5, pady=2)
        self.btn_filtrar_negativos_actual.pack(side=tk.LEFT, padx=5, pady=2)
        self.btn_calcular_ajustes.pack(side=tk.LEFT, padx=5, pady=2)
        self.btn_guardar.pack(side=tk.LEFT, padx=5, pady=2)
        ttk.Button(operacion_frame, text="Cerrar", command=self.destroy).pack(side=tk.RIGHT, padx=5, pady=2)

    def _cargar_datos_iniciales(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            self.uo_data = {"0": "Todas las UO"}
            cursor.execute("SELECT uo_id, uo_Codigo, uo_nombre FROM ark_unds_operativas WHERE uo_active = 1 ORDER BY uo_Codigo")
            for row in cursor.fetchall():
                self.uo_data[str(row[0])] = f"{row[1]} - {row[2]}"
            self.cmb_uo['values'] = list(self.uo_data.values())
            self.cmb_uo.current(0)
            
            self.deposito_data = {"0": "Todos los depósitos"}
            cursor.execute("SELECT dep_IDauto, dep_codigo, dep_descripcion FROM ark_depositos ORDER BY dep_codigo")
            for row in cursor.fetchall():
                self.deposito_data[str(row[0])] = f"{row[1]} - {row[2]}"
            self.cmb_deposito['values'] = list(self.deposito_data.values())
            self.cmb_deposito.current(0)
            
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los datos iniciales: {e}")

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
        """
        Calcula el saldo inicial teórico a partir de ark_existencia_calculadas
        usando la fórmula inversa: Inicial = Final - Entradas + Salidas
        """
        try:
            uo_display = self.cmb_uo.get()
            uo_id = next((k for k, v in self.uo_data.items() if v == uo_display), "0")
            uo_codigo_filtro = uo_display.split(" - ")[0] if uo_id != "0" else None
            
            deposito_display = self.cmb_deposito.get()
            deposito_id = next((k for k, v in self.deposito_data.items() if v == deposito_display), "0")
            dep_codigo_filtro = deposito_display.split(" - ")[0] if deposito_id != "0" else None

            for item in self.tree_resultados.get_children():
                self.tree_resultados.delete(item)
                
            self.config(cursor="watch")
            self.update()

            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Consulta a ark_existencia_calculadas (datos ya consolidados del periodo)
            query = """
                SELECT 
                    exc_uo_Codigo, exc_dep_codigo, exc_item_codigo,
                    exc_final,
                    exc_compras, exc_cargos, exc_nota_entrega_proveedor, exc_dev_ventas,
                    exc_ajustes_mas, exc_transferencias_mas,
                    exc_ventas, exc_descargos, exc_nota_entrega_clientes, 
                    exc_dev_compras, exc_ajustes_menos, exc_transferencias_menos,
                    exc_costos_local, exc_costos_referencial, exc_factor_referencial
                FROM ark_existencia_calculadas
                WHERE 1=1
            """
            params = []
            if uo_codigo_filtro:
                query += " AND exc_uo_Codigo = ?"
                params.append(uo_codigo_filtro)
            if dep_codigo_filtro:
                query += " AND exc_dep_codigo = ?"
                params.append(dep_codigo_filtro)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Obtener descripción de productos
            cursor.execute("SELECT inv_codigo, inv_descripcion FROM ark_inventario")
            productos = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            self._resultados_originales = {}
            for i, row in enumerate(rows):
                item_id = f"res_{i}"
                
                uo, dep, item, final = row[0], row[1], row[2], row[3] or 0.0
                compras, cargos, notas_prov, dev_ventas, aj_mas, trans_mas = [row[j] or 0.0 for j in range(4, 10)]
                ventas, descargos, notas_cli, dev_compras, aj_menos, trans_menos = [row[j] or 0.0 for j in range(10, 16)]
                costo_local, costo_ref, factor = row[16] or 0.0, row[17] or 0.0, row[18] or 1.0
                
                entradas = compras + cargos + notas_prov + dev_ventas + aj_mas + trans_mas
                salidas = ventas + descargos + notas_cli + dev_compras + aj_menos + trans_menos
                
                # Fórmula inversa: Inicial = Final - Entradas + Salidas
                saldo_inicial_teorico = final - entradas + salidas
                
                res = {
                    'codigo_producto': item,
                    'descripcion_producto': productos.get(item, ''),
                    'uo_codigo': uo,
                    'deposito_codigo': dep,
                    'existencia_actual': final,  # En este contexto, el "actual" es el final calculado
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
                    formato_cantidad(final),
                    formato_cantidad(entradas),
                    formato_cantidad(salidas),
                    formato_cantidad(saldo_inicial_teorico),
                    "", "", "",
                    formato_monto(costo_local),
                    formato_monto(costo_ref),
                    formato_monto(saldo_inicial_teorico * costo_local)
                ))
                
            self._habilitar_botones_operacion()
            self.config(cursor="")
            messagebox.showinfo("Éxito", f"Cálculo finalizado. {len(rows)} registros procesados.")
            
        except Exception as e:
            self.config(cursor="")
            self._deshabilitar_botones_operacion()
            messagebox.showerror("Error", f"Ocurrió un error al calcular las existencias: {e}")

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
        for item in self.tree_resultados.get_children():
            self.tree_resultados.delete(item)
        for item_id, res in self._resultados_originales.items():
            exa_actual = res['existencia_actual']
            entradas = res['entradas']
            salidas = res['salidas']
            si_teorico = exa_actual - entradas + salidas
            
            ajuste_inicial = max(0.0, -si_teorico)
            inicial_simulado = si_teorico + ajuste_inicial
            final_simulado = inicial_simulado - entradas + salidas
            ajuste_total = max(0.0, -si_teorico, -final_simulado)
            
            # Actualizar resultado con ajustes
            res['ajuste_requerido'] = ajuste_total
            res['inicial_simulado'] = inicial_simulado
            res['final_simulado'] = final_simulado
            
            self.tree_resultados.insert("", tk.END, iid=item_id, values=(
                res.get('codigo_producto', ''),
                res.get('descripcion_producto', ''),
                res.get('uo_codigo', ''),
                res.get('deposito_codigo', ''),
                formato_cantidad(exa_actual),
                formato_cantidad(entradas),
                formato_cantidad(salidas),
                formato_cantidad(si_teorico),
                formato_cantidad(inicial_simulado),
                formato_cantidad(final_simulado),
                formato_cantidad(ajuste_total),
                formato_monto(res.get('costo_local', 0.0)),
                formato_monto(res.get('costo_referencial', 0.0)),
                formato_monto(inicial_simulado * res.get('costo_local', 0.0))
            ))

    def _insertar_fila(self, item_id, res):
        """Helper para insertar fila con o sin ajustes"""
        tiene_ajustes = 'inicial_simulado' in res
        if tiene_ajustes:
            self.tree_resultados.insert("", tk.END, iid=item_id, values=(
                res.get('codigo_producto', ''),
                res.get('descripcion_producto', ''),
                res.get('uo_codigo', ''),
                res.get('deposito_codigo', ''),
                formato_cantidad(res['existencia_actual']),
                formato_cantidad(res['entradas']),
                formato_cantidad(res['salidas']),
                formato_cantidad(res['saldo_inicial_calculado']),
                formato_cantidad(res['inicial_simulado']),
                formato_cantidad(res['final_simulado']),
                formato_cantidad(res.get('ajuste_requerido', 0.0)),
                formato_monto(res.get('costo_local', 0.0)),
                formato_monto(res.get('costo_referencial', 0.0)),
                formato_monto(res['inicial_simulado'] * res.get('costo_local', 0.0))
            ))
        else:
            self.tree_resultados.insert("", tk.END, iid=item_id, values=(
                res.get('codigo_producto', ''),
                res.get('descripcion_producto', ''),
                res.get('uo_codigo', ''),
                res.get('deposito_codigo', ''),
                formato_cantidad(res['existencia_actual']),
                formato_cantidad(res['entradas']),
                formato_cantidad(res['salidas']),
                formato_cantidad(res['saldo_inicial_calculado']),
                "", "", "",
                formato_monto(res.get('costo_local', 0.0)),
                formato_monto(res.get('costo_referencial', 0.0)),
                formato_monto(res['saldo_inicial_calculado'] * res.get('costo_local', 0.0))
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
                
                total = len(self._resultados_originales)
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
                messagebox.showerror("Error Crítico", f"Falló el guardado: {e}")