import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.embedded_db import get_db_connection
from core.generar_pdf import generar_reporte_inventario

class DialogReporteInventario(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Reporte General de Inventario")
        self.geometry("500x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (500 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (350 // 2)
        self.geometry(f"+{x}+{y}")

        self.categoria_data = {}
        self._create_widgets()
        self._cargar_categorias()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Filtro 1: Status
        ttk.Label(frame, text="Status:").grid(row=0, column=0, sticky=tk.W, pady=10)
        self.cmb_status = ttk.Combobox(frame, state="readonly", width=40, values=["Todos", "Activo", "Inactivo"])
        self.cmb_status.set("Todos")
        self.cmb_status.grid(row=0, column=1, pady=10, padx=10)

        # Filtro 2: Categoría
        ttk.Label(frame, text="Categoría:").grid(row=1, column=0, sticky=tk.W, pady=10)
        self.cmb_categoria = ttk.Combobox(frame, state="readonly", width=40)
        self.cmb_categoria.grid(row=1, column=1, pady=10, padx=10)

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=20)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Generar PDF", command=self._generar_pdf).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cerrar", command=self.destroy).pack(side=tk.LEFT, padx=10)

    def _cargar_categorias(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT cat_codigo, cat_descripcion FROM ark_categoria ORDER BY cat_codigo")
            rows = cursor.fetchall()
            conn.close()
            
            self.categoria_data = {"Todas": "Todas las Categorías"}
            for row in rows:
                self.categoria_data[row[0]] = f"{row[0]} - {row[1]}"
                
            self.cmb_categoria['values'] = list(self.categoria_data.values())
            self.cmb_categoria.current(0)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las categorías: {e}")

    def _generar_pdf(self):
        ruta_salida = filedialog.asksaveasfilename(
            title="Guardar Reporte de Inventario",
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")],
            initialfile="Reporte_General_Inventario.pdf"
        )
        
        if not ruta_salida:
            return
            
        try:
            self.config(cursor="watch")
            self.update()
            
            status_filtro = self.cmb_status.get()
            
            # Pasar el string completo concatenado (ej: "00009 - MAQUINAS")
            categoria_filtro = self.cmb_categoria.get()
            
            generar_reporte_inventario(
                ruta_salida, 
                status_filtro=status_filtro, 
                categoria_filtro=categoria_filtro
            )
            
            self.config(cursor="")
            messagebox.showinfo("Éxito", f"Reporte generado exitosamente en:\n{ruta_salida}")
            os.startfile(ruta_salida)
            
        except Exception as e:
            self.config(cursor="")
            messagebox.showerror("Error", f"Ocurrió un error al generar el PDF:\n{e}")