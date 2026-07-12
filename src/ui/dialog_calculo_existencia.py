import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.embedded_db import get_db_connection
from core.calculo_existencias import calcular_existencia_inicial_periodo
from core.system_info import get_current_user, get_machine_name


class DialogCalculoExistencia(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Cálculo de Existencias")
        self.geometry("850x600")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (850 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (600 // 2)
        self.geometry(f"+{x}+{y}")

        self.periodos_data = {}
        self.uo_data = {}
        self._resultados_originales = {}

        self.cmb_periodo = None
        self.cmb_uo = None
        self.cmb_deposito = None
        self.tree_resultados = None
        self.btn_filtrar_negativos_inicial = None
        self.btn_filtrar_negativos_actual = None
        self.btn_calcular_ajustes = None

        self._create_widgets()
        self._cargar_datos_iniciales()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        filtros_frame = ttk.LabelFrame(main_frame, text="Filtros de Cálculo", padding=10)
        filtros_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(filtros_frame, text="Periodo:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.cmb_periodo = ttk.Combobox(filtros_frame, state="readonly", width=30)
        self.cmb_periodo.grid(row=0, column=1, sticky=tk.W, padx=(0, 10), pady=2)

        ttk.Label(filtros_frame, text="Unidad Operativa:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.cmb_uo = ttk.Combobox(filtros_frame, state="readonly", width=30)
        self.cmb_uo.grid(row=1, column=1, sticky=tk.W, padx=(0, 10), pady=2)

        ttk.Label(filtros_frame, text="Depósito:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.cmb_deposito = ttk.Combobox(filtros_frame, state="readonly", width=30)
        self.cmb_deposito.grid(row=2, column=1, sticky=tk.W, padx=(0, 10), pady=2)

        ttk.Button(filtros_frame, text="Calcular Existencia Inicial", command=self._calcular_existencia).grid(row=0, column=2, rowspan=3, padx=(20, 0), pady=2, sticky=tk.N)

        resultados_frame = ttk.LabelFrame(main_frame, text="Resultados del Cálculo", padding=10)
        resultados_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("Producto", "Descripción", "UO", "Depósito", "Ex. Actual", "Entradas", "Salidas", "Saldo Inicial Teórico", "Inicial Simulado", "Final Simulado", "Ajuste Total")
        self.tree_resultados = ttk.Treeview(resultados_frame, columns=columns, show="headings", height=15)
        
        # Definir ancho y alineación por columna
        for col in columns:
            if col in ("Ex. Actual", "Entradas", "Salidas", "Saldo Inicial Teórico", "Inicial Simulado", "Final Simulado", "Ajuste Total"):
                self.tree_resultados.heading(col, text=col)
                self.tree_resultados.column(col, anchor=tk.E, width=90)  # Alineación a la derecha
            else:
                self.tree_resultados.heading(col, text=col)
                self.tree_resultados.column(col, anchor=tk.W, width=90)  # Alineación a la izquierda

        scrollbar_y = ttk.Scrollbar(resultados_frame, orient=tk.VERTICAL, command=self.tree_resultados.yview)
        scrollbar_x = ttk.Scrollbar(resultados_frame, orient=tk.HORIZONTAL, command=self.tree_resultados.xview)
        self.tree_resultados.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree_resultados.grid(row=0, column=0, sticky=tk.NSEW)
        scrollbar_y.grid(row=0, column=1, sticky=tk.NS)
        scrollbar_x.grid(row=1, column=0, sticky=tk.EW)
        resultados_frame.grid_rowconfigure(0, weight=1)
        resultados_frame.grid_columnconfigure(0, weight=1)

        operacion_frame = ttk.Frame(main_frame)
        operacion_frame.pack(fill=tk.X, padx=5, pady=5)

        self.btn_filtrar_negativos_inicial = ttk.Button(operacion_frame, text="Mostrar Solo Saldo Inicial Negativo", command=self._filtrar_saldo_inicial_negativo, state=tk.DISABLED)
        self.btn_filtrar_negativos_actual = ttk.Button(operacion_frame, text="Mostrar Solo Existencia Actual Negativa", command=self._filtrar_existencia_actual_negativa, state=tk.DISABLED)
        self.btn_calcular_ajustes = ttk.Button(operacion_frame, text="Calcular Ajustes Requeridos", command=self._calcular_ajustes_requeridos, state=tk.DISABLED)

        self.btn_filtrar_negativos_inicial.pack(side=tk.LEFT, padx=5, pady=2)
        self.btn_filtrar_negativos_actual.pack(side=tk.LEFT, padx=5, pady=2)
        self.btn_calcular_ajustes.pack(side=tk.LEFT, padx=5, pady=2)

    def _cargar_datos_iniciales(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            self.periodos_data = {"0": "Seleccionar Periodo"}
            cursor.execute("""
                SELECT pdo_Idauto, pdo_fecha_ini, pdo_fecha_fin, pdo_uo_Codigo
                FROM ark_periodos
                ORDER BY pdo_fecha_ini DESC
            """)
            for row in cursor.fetchall():
                id_auto = str(row[0])
                fecha_ini = row[1]
                fecha_fin = row[2]
                uo_codigo = row[3]
                descripcion = f"{uo_codigo} - {fecha_ini} al {fecha_fin}"
                self.periodos_data[id_auto] = descripcion
            self.cmb_periodo['values'] = list(self.periodos_data.values())
            self.cmb_periodo.current(0)

            self.uo_data = {"0": "Todas las UO"}
            cursor.execute("SELECT uo_id, uo_Codigo, uo_nombre FROM ark_unds_operativas WHERE uo_active = 1 ORDER BY uo_Codigo")
            for row in cursor.fetchall():
                self.uo_data[str(row[0])] = f"{row[1]} - {row[2]}"
            self.cmb_uo['values'] = list(self.uo_data.values())
            self.cmb_uo.current(0)

            deposito_data = {"0": "Todos los depósitos"}
            cursor.execute("SELECT dep_IDauto, dep_codigo, dep_descripcion FROM ark_depositos ORDER BY dep_codigo")
            for row in cursor.fetchall():
                deposito_data[str(row[0])] = f"{row[1]} - {row[2]}"
            self.cmb_deposito['values'] = list(deposito_data.values())
            self.cmb_deposito.current(0)

            conn.close()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los datos iniciales: {e}")

    def _habilitar_botones_operacion(self):
        self.btn_filtrar_negativos_inicial.config(state=tk.NORMAL)
        self.btn_filtrar_negativos_actual.config(state=tk.NORMAL)
        self.btn_calcular_ajustes.config(state=tk.NORMAL)

    def _deshabilitar_botones_operacion(self):
        self.btn_filtrar_negativos_inicial.config(state=tk.DISABLED)
        self.btn_filtrar_negativos_actual.config(state=tk.DISABLED)
        self.btn_calcular_ajustes.config(state=tk.DISABLED)

    def _calcular_existencia(self):
        try:
            periodo_display = self.cmb_periodo.get()
            periodo_id = next((k for k, v in self.periodos_data.items() if v == periodo_display), "0")

            uo_display = self.cmb_uo.get()
            uo_id = next((k for k, v in self.uo_data.items() if v == uo_display), "0")

            deposito_display = self.cmb_deposito.get()
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT dep_IDauto FROM ark_depositos WHERE dep_codigo || ' - ' || dep_descripcion = ?", (deposito_display,))
            row = cursor.fetchone()
            deposito_id = str(row[0]) if row else "0"
            conn.close()

            for item in self.tree_resultados.get_children():
                self.tree_resultados.delete(item)

            resultados = calcular_existencia_inicial_periodo(periodo_id, uo_id, deposito_id)

            self._resultados_originales = {}
            for i, res in enumerate(resultados):
                item_id = f"res_{i}"
                self._resultados_originales[item_id] = res
                self.tree_resultados.insert("", tk.END, iid=item_id, values=(
                    res.get('codigo_producto', ''),
                    res.get('descripcion_producto', ''),
                    res.get('uo_codigo', ''),
                    res.get('deposito_codigo', ''),
                    f"{res.get('existencia_actual', 0.0):,.2f}",
                    f"{res.get('entradas', 0.0):,.2f}",
                    f"{res.get('salidas', 0.0):,.2f}",
                    f"{res.get('saldo_inicial_calculado', 0.0):,.2f}",
                    "",
                    "",
                    ""
                ))

            self._habilitar_botones_operacion()

        except Exception as e:
            self._deshabilitar_botones_operacion()
            messagebox.showerror("Error", f"Ocurrió un error al calcular las existencias: {e}")

    def _filtrar_saldo_inicial_negativo(self):
        for item in self.tree_resultados.get_children():
            self.tree_resultados.delete(item)
        for item_id, res in self._resultados_originales.items():
            if res['saldo_inicial_calculado'] < 0:
                self.tree_resultados.insert("", tk.END, iid=item_id, values=(
                    res.get('codigo_producto', ''),
                    res.get('descripcion_producto', ''),
                    res.get('uo_codigo', ''),
                    res.get('deposito_codigo', ''),
                    f"{res.get('existencia_actual', 0.0):,.2f}",
                    f"{res.get('entradas', 0.0):,.2f}",
                    f"{res.get('salidas', 0.0):,.2f}",
                    f"{res.get('saldo_inicial_calculado', 0.0):,.2f}",
                    "",
                    "",
                    ""
                ))

    def _filtrar_existencia_actual_negativa(self):
        for item in self.tree_resultados.get_children():
            self.tree_resultados.delete(item)
        for item_id, res in self._resultados_originales.items():
            if res['existencia_actual'] < 0:
                self.tree_resultados.insert("", tk.END, iid=item_id, values=(
                    res.get('codigo_producto', ''),
                    res.get('descripcion_producto', ''),
                    res.get('uo_codigo', ''),
                    res.get('deposito_codigo', ''),
                    f"{res.get('existencia_actual', 0.0):,.2f}",
                    f"{res.get('entradas', 0.0):,.2f}",
                    f"{res.get('salidas', 0.0):,.2f}",
                    f"{res.get('saldo_inicial_calculado', 0.0):,.2f}",
                    "",
                    "",
                    ""
                ))

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
            self.tree_resultados.insert("", tk.END, iid=item_id, values=(
                res.get('codigo_producto', ''),
                res.get('descripcion_producto', ''),
                res.get('uo_codigo', ''),
                res.get('deposito_codigo', ''),
                f"{exa_actual:,.2f}",
                f"{entradas:,.2f}",
                f"{salidas:,.2f}",
                f"{si_teorico:,.2f}",
                f"{inicial_simulado:,.2f}",
                f"{final_simulado:,.2f}",
                f"{ajuste_total:,.2f}"
            ))