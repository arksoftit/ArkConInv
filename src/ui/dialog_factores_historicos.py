import tkinter as tk
from tkinter import ttk
from db.embedded_db import get_db_connection

class DialogFactoresHistoricos(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Maestro de Factores Históricos")
        self.geometry("800x500")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (800 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (500 // 2)
        self.geometry(f"+{x}+{y}")

        self._create_widgets()
        self._cargar_datos()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        columns = ("Código", "Descripción", "Status", "Simbolo")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        self.tree.heading("Código", text="Código")
        self.tree.heading("Descripción", text="Descripción")
        self.tree.heading("Simbolo", text="Simbolo")
        self.tree.heading("Tasa", text="Tasa")
        self.tree.heading("Status", text="Status")
        self.tree.column("Código", width=100)
        self.tree.column("Descripción", width=500)
        self.tree.column("Simbolo", width=80, anchor=tk.CENTER)
        self.tree.column("Tasa", width=100, anchor=tk.CENTER)
        self.tree.column("Status", width=80, anchor=tk.CENTER)
        

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(btn_frame, text="Refrescar", command=self._cargar_datos).pack(side=tk.LEFT, padx=5)
        
        self.lbl_contador = ttk.Label(btn_frame, text="Total de registros: 0", anchor=tk.CENTER, font=("Segoe UI", 9, "bold"))
        self.lbl_contador.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        ttk.Button(btn_frame, text="Cerrar", command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def _cargar_datos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        total_registros = 0
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT mon_idauto, mon_codigo, mon_descripcion, mon_simbolo, mon_tasa, mon_status FROM ark_monedas")
            rows = cursor.fetchall()
            for row in rows:
                status_text = "Activo" if row[5] == 1 else "Inactivo"
                self.tree.insert("", "end", values=(row[0], row[1], row[2], row[3], row[4], status_text))
                total_registros += 1
            conn.close()
        except Exception as e:
            print(f"Error al cargar monedas: {e}")
        
        self.lbl_contador.config(text=f"Total de registros: {total_registros}")