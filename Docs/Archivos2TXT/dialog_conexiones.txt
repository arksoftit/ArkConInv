import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.dbconnection import DBConnectionManager

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'conexiones.json'))

class DialogConexiones(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Gestión de Conexiones ODBC - DBISAM")
        self.geometry("500x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # --- Centrar el diálogo respecto a la ventana principal ---
        parent.update_idletasks()  # Asegura que las dimensiones de parent estén actualizadas
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (500 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (350 // 2)
        self.geometry(f"+{x}+{y}")
        # --- Fin del centrado ---

        self.manager = DBConnectionManager(CONFIG_PATH)
        self.dsn_list = self.manager.get_dsn_list()

        self._create_widgets()
        self._cargar_dsn()
        self._cargar_ultimas_conexiones()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Seleccionar DSN (32 bits):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.cmb_dsn = ttk.Combobox(frame, state="readonly", width=40)
        self.cmb_dsn.grid(row=0, column=1, pady=5)
        self.cmb_dsn.bind("<<ComboboxSelected>>", self._seleccionar_dsn)

        ttk.Label(frame, text="Usuario:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.entry_user = ttk.Entry(frame, width=42)
        self.entry_user.grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Contraseña:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.entry_pass = ttk.Entry(frame, width=42, show="*")
        self.entry_pass.grid(row=2, column=1, pady=5)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Probar Conexión", command=self._probar_conexion).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Guardar", command=self._guardar_conexion).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cerrar", command=self.destroy).pack(side=tk.LEFT, padx=5)

        self.lbl_estado = ttk.Label(frame, text="", foreground="blue")
        self.lbl_estado.grid(row=4, column=0, columnspan=2, pady=5)

    def _cargar_dsn(self):
        if self.dsn_list:
            self.cmb_dsn['values'] = self.dsn_list
            self.cmb_dsn.current(0)
            self._seleccionar_dsn(None)
        else:
            self.lbl_estado.config(text="No se encontraron DSNs de DBISAM en el registro.", foreground="red")

    def _cargar_ultimas_conexiones(self):
        conexiones = self.manager.load_connections()
        if conexiones:
            self.entry_user.insert(0, conexiones[0]['usuario'])
            self.entry_pass.insert(0, conexiones[0]['password'])

    def _seleccionar_dsn(self, event):
        dsn_seleccionado = self.cmb_dsn.get()
        conexiones = self.manager.load_connections()
        for c in conexiones:
            if c['dsn'] == dsn_seleccionado:
                self.entry_user.delete(0, tk.END)
                self.entry_pass.delete(0, tk.END)
                self.entry_user.insert(0, c['usuario'])
                self.entry_pass.insert(0, c['password'])
                return

    def _probar_conexion(self):
        dsn = self.cmb_dsn.get()
        user = self.entry_user.get()
        pwd = self.entry_pass.get()
        if not dsn:
            self.lbl_estado.config(text="Seleccione un DSN.", foreground="red")
            return
        
        ok, msg = self.manager.connect(dsn, user, pwd)
        if ok:
            # Obtener la ruta de la base de datos desde el DSN
            db_path = self.manager.get_data_directory()
            if db_path:
                self.lbl_estado.config(
                    text=f"Conexión exitosa a {dsn}.\nRuta: {db_path}",
                    foreground="green"
                )
            else:
                self.lbl_estado.config(
                    text=f"Conexión exitosa a {dsn}.",
                    foreground="green"
                )
            self.manager.disconnect()
        else:
            self.lbl_estado.config(text=f"Error: {msg}", foreground="red")

    def _guardar_conexion(self):
        dsn = self.cmb_dsn.get()
        user = self.entry_user.get()
        pwd = self.entry_pass.get()
        if not dsn:
            messagebox.showwarning("Advertencia", "Debe seleccionar un DSN.")
            return
        
        self.manager.save_connection(dsn, user, pwd)
        self.lbl_estado.config(text="Conexión guardada correctamente.", foreground="green")
        messagebox.showinfo("Éxito", f"Conexión para '{dsn}' guardada en el historial.")