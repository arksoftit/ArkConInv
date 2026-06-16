import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.embedded_db import get_db_connection
from core.generar_pdf import generar_reporte_depositos

class DialogReporteDepositos(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Reporte General de Depósitos")
        self.geometry("500x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (500 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (350 // 2)
        self.geometry(f"+{x}+{y}")

        self.uo_data = {}
        self._create_widgets()
        self._cargar_filtros()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Filtro 1: Unidad Operativa
        ttk.Label(frame, text="Unidad Operativa:").grid(row=0, column=0, sticky=tk.W, pady=10)
        self.cmb_uo = ttk.Combobox(frame, state="readonly", width=40)
        self.cmb_uo.grid(row=0, column=1, pady=10, padx=10)

        # Filtro 2: Status
        ttk.Label(frame, text="Status:").grid(row=1, column=0, sticky=tk.W, pady=10)
        self.cmb_status = ttk.Combobox(frame, state="readonly", width=40, values=["Todos", "Activo", "Inactivo"])
        self.cmb_status.set("Todos")
        self.cmb_status.grid(row=1, column=1, pady=10, padx=10)

        # Separador
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=20)

        # Botones de Acción
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Generar PDF", command=self._generar_pdf).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cerrar", command=self.destroy).pack(side=tk.LEFT, padx=10)

    def _cargar_filtros(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT uo_id, uo_Codigo, uo_nombre FROM ark_unds_operativas WHERE uo_active = 1 ORDER BY uo_Codigo")
            rows = cursor.fetchall()
            conn.close()
            
            # Opción "Todas las UO"
            self.uo_data = {0: "Todas las Unidades Operativas"}
            for row in rows:
                self.uo_data[row[0]] = f"{row[1]} - {row[2]}"
                
            self.cmb_uo['values'] = list(self.uo_data.values())
            self.cmb_uo.current(0)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los filtros: {e}")

    def _generar_pdf(self):
        ruta_salida = filedialog.asksaveasfilename(
            title="Guardar Reporte de Depósitos",
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")],
            initialfile="Reporte_General_Depositos.pdf"
        )
        
        if not ruta_salida:
            return
            
        try:
            self.config(cursor="watch")
            self.update()
            
            # Obtener IDs de los filtros
            uo_display = self.cmb_uo.get()
            uo_id = [k for k, v in self.uo_data.items() if v == uo_display][0]
            status_filtro = self.cmb_status.get()
            
            # Llamar al motor de PDF pasando los filtros
            # generar_reporte_depositos(ruta_salida, uo_id=uo_id, status_filtro=status_filtro)
            # Obtener el nombre de la UO seleccionada para mostrarlo en el reporte
            uo_nombre = self.uo_data.get(uo_id, "Todas")
            
            # Llamar al motor de PDF pasando los filtros
            generar_reporte_depositos(ruta_salida, uo_id=uo_id, uo_nombre=uo_nombre, status_filtro=status_filtro)
            
            self.config(cursor="")
            messagebox.showinfo("Éxito", f"Reporte generado exitosamente en:\n{ruta_salida}")
            os.startfile(ruta_salida)
            
        except Exception as e:
            self.config(cursor="")
            messagebox.showerror("Error", f"Ocurrió un error al generar el PDF:\n{e}")