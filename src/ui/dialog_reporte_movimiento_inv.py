import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.embedded_db import get_db_connection
from core.generar_pdf import generar_pdf_movimiento_inventario


class DialogMovimientoInventario(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Reporte de Movimiento de Inventario")
        self.geometry("650x480")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (650 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (480 // 2)
        self.geometry(f"+{x}+{y}")

        self.uo_data = {}
        self.deposito_data = {}
        self.tipos_operacion = {
            'cargos': tk.BooleanVar(value=True),
            'descargos': tk.BooleanVar(value=True),
            'transferencias': tk.BooleanVar(value=True),
            'facturas': tk.BooleanVar(value=True),
            'notas_entrega_vtas': tk.BooleanVar(value=True),
            'compras': tk.BooleanVar(value=True),
            'notas_entrega_comp': tk.BooleanVar(value=True)
        }

        self._create_widgets()
        self._cargar_datos_iniciales()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # --- Selección de Unidad Operativa ---
        ttk.Label(frame, text="Unidad Operativa:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.cmb_uo = ttk.Combobox(frame, state="readonly", width=50)
        self.cmb_uo.grid(row=0, column=1, columnspan=2, pady=5, padx=10)

        # --- Rango de Fechas ---
        ttk.Label(frame, text="Rango de Fechas:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=10)
        fecha_frame = ttk.Frame(frame)
        fecha_frame.grid(row=1, column=1, columnspan=2, pady=5, padx=10, sticky=tk.W)
        
        ttk.Label(fecha_frame, text="Desde:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fecha_desde = ttk.Entry(fecha_frame, width=12)
        self.entry_fecha_desde.pack(side=tk.LEFT, padx=(0, 10))
        self.entry_fecha_desde.bind("<KeyRelease>", self._aplicar_mascara_fecha)
        
        ttk.Label(fecha_frame, text="Hasta:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fecha_hasta = ttk.Entry(fecha_frame, width=12)
        self.entry_fecha_hasta.pack(side=tk.LEFT, padx=(0, 10))
        self.entry_fecha_hasta.bind("<KeyRelease>", self._aplicar_mascara_fecha)

        # --- Depósito ---
        ttk.Label(frame, text="Depósito:", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.cmb_deposito = ttk.Combobox(frame, state="readonly", width=50)
        self.cmb_deposito.grid(row=2, column=1, columnspan=2, pady=5, padx=10)

        # --- Filtros por Tipo de Operación ---
        ttk.Label(frame, text="Tipos de Operación:", font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky=tk.NW, pady=5)

        tipos_frame = ttk.Frame(frame)
        tipos_frame.grid(row=3, column=1, columnspan=2, pady=5, padx=10, sticky=tk.W)

        row1 = ttk.Frame(tipos_frame)
        row1.pack(anchor=tk.W)
        ttk.Checkbutton(row1, text="Cargos", variable=self.tipos_operacion['cargos']).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(row1, text="Descargos", variable=self.tipos_operacion['descargos']).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(row1, text="Transferencias", variable=self.tipos_operacion['transferencias']).pack(side=tk.LEFT, padx=10)

        row2 = ttk.Frame(tipos_frame)
        row2.pack(anchor=tk.W, pady=5)
        ttk.Checkbutton(row2, text="Facturas", variable=self.tipos_operacion['facturas']).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(row2, text="Notas Entrega Vtas", variable=self.tipos_operacion['notas_entrega_vtas']).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(row2, text="Compras", variable=self.tipos_operacion['compras']).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(row2, text="Notas Entrega Comp", variable=self.tipos_operacion['notas_entrega_comp']).pack(side=tk.LEFT, padx=10)

        # --- Botones ---
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=20)

        ttk.Button(btn_frame, text="Generar PDF", command=self._generar_pdf).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cerrar", command=self.destroy).pack(side=tk.LEFT, padx=10)

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

            hoy = datetime.now()
            primer_dia = hoy.replace(day=1)
            self.entry_fecha_desde.insert(0, primer_dia.strftime("%d/%m/%Y"))
            self.entry_fecha_hasta.insert(0, hoy.strftime("%d/%m/%Y"))

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los datos: {e}")

    def _aplicar_mascara_fecha(self, event):
        entry = event.widget
        valor = entry.get()
        
        solo_numeros = ''.join(c for c in valor if c.isdigit())
        
        if len(solo_numeros) > 8:
            solo_numeros = solo_numeros[:8]
        
        formateado = ""
        if len(solo_numeros) >= 1:
            formateado = solo_numeros[:2]
        if len(solo_numeros) >= 3:
            formateado += "/" + solo_numeros[2:4]
        if len(solo_numeros) >= 5:
            formateado += "/" + solo_numeros[4:8]
        
        entry.delete(0, tk.END)
        entry.insert(0, formateado)
        entry.icursor(len(formateado))

    def _generar_pdf(self):
        try:
            uo_display = self.cmb_uo.get()
            uo_id = next((k for k, v in self.uo_data.items() if v == uo_display), "0")

            fecha_desde = self.entry_fecha_desde.get().strip()
            fecha_hasta = self.entry_fecha_hasta.get().strip()

            if not fecha_desde or not fecha_hasta:
                messagebox.showwarning("Advertencia", "Debe ingresar un rango de fechas válido.")
                return

            try:
                fecha_desde_obj = datetime.strptime(fecha_desde, "%d/%m/%Y")
                fecha_hasta_obj = datetime.strptime(fecha_hasta, "%d/%m/%Y")
                fecha_desde_sql = fecha_desde_obj.strftime("%Y-%m-%d")
                fecha_hasta_sql = fecha_hasta_obj.strftime("%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("Advertencia", "Formato de fecha inválido. Use DD/MM/AAAA")
                return

            deposito_display = self.cmb_deposito.get()
            deposito_id = next((k for k, v in self.deposito_data.items() if v == deposito_display), "0")

            tipos_seleccionados = [key for key, var in self.tipos_operacion.items() if var.get()]

            if not tipos_seleccionados:
                messagebox.showwarning("Advertencia", "Debe seleccionar al menos un tipo de operación.")
                return

            ruta_salida = filedialog.asksaveasfilename(
                title="Guardar Reporte de Movimiento de Inventario",
                defaultextension=".pdf",
                filetypes=[("Archivos PDF", "*.pdf")],
                initialfile="Reporte_Movimiento_Inventario.pdf"
            )

            if not ruta_salida:
                return

            self.config(cursor="watch")
            self.update()

            generar_pdf_movimiento_inventario(
                ruta_salida=ruta_salida,
                uo_id=uo_id,
                fecha_desde=fecha_desde_sql,
                fecha_hasta=fecha_hasta_sql,
                deposito_id=deposito_id,
                tipos=tipos_seleccionados
            )

            self.config(cursor="")
            messagebox.showinfo("Éxito", f"Reporte generado exitosamente en:\n{ruta_salida}")
            os.startfile(ruta_salida)

        except Exception as e:
            self.config(cursor="")
            messagebox.showerror("Error", f"Ocurrió un error al generar el PDF:\n{e}")