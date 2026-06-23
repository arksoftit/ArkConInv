import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.generar_pdf import generar_reporte_categorias

class DialogReporteCategorias(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Reporte General de Categorías")
        self.geometry("500x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (500 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (350 // 2)
        self.geometry(f"+{x}+{y}")

        self._create_widgets()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Filtro 1: Status
        ttk.Label(frame, text="Status:").grid(row=0, column=0, sticky=tk.W, pady=10)
        self.cmb_status = ttk.Combobox(frame, state="readonly", width=40, values=["Todos", "Activo", "Inactivo"])
        self.cmb_status.set("Todos")
        self.cmb_status.grid(row=0, column=1, pady=10, padx=10)

        # Filtro 2: Maneja Depósitos
        ttk.Label(frame, text="Maneja Depósitos:").grid(row=1, column=0, sticky=tk.W, pady=10)
        self.cmb_depositos = ttk.Combobox(frame, state="readonly", width=40, values=["Todos", "Si", "No"])
        self.cmb_depositos.set("Todos")
        self.cmb_depositos.grid(row=1, column=1, pady=10, padx=10)

        # Separador
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=20)

        # Botones de Acción
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Generar PDF", command=self._generar_pdf).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cerrar", command=self.destroy).pack(side=tk.LEFT, padx=10)

    def _generar_pdf(self):
        ruta_salida = filedialog.asksaveasfilename(
            title="Guardar Reporte de Categorías",
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")],
            initialfile="Reporte_General_Categorias.pdf"
        )
        
        if not ruta_salida:
            return
            
        try:
            self.config(cursor="watch")
            self.update()
            
            status_filtro = self.cmb_status.get()
            maneja_depositos_filtro = self.cmb_depositos.get()
            
            generar_reporte_categorias(
                ruta_salida, 
                status_filtro=status_filtro, 
                maneja_depositos_filtro=maneja_depositos_filtro
            )
            
            self.config(cursor="")
            messagebox.showinfo("Éxito", f"Reporte generado exitosamente en:\n{ruta_salida}")
            os.startfile(ruta_salida)
            
        except Exception as e:
            self.config(cursor="")
            messagebox.showerror("Error", f"Ocurrió un error al generar el PDF:\n{e}")