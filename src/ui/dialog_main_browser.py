import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.embedded_db import get_db_connection
from core.path_utils import get_backup_dir

class DialogMainBrowser(tk.Toplevel):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.parent = parent
        self.config = config
        self.resultado = None
        self.modo_archivos = self.config.get('modo_archivos', False)
        
        self.title(self.config.get('titulo', 'Navegador de Registros'))
        self.geometry("850x550")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (850 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (550 // 2)
        self.geometry(f"+{x}+{y}")
        
        self._create_widgets()
        self._cargar_datos()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        frame_busqueda = ttk.Labelframe(main_frame, text="Filtros de Búsqueda", padding=10)
        frame_busqueda.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(frame_busqueda, text="Buscar por:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.check_vars = {}
        for i, (display_name, field_name) in enumerate(self.config.get('campos_busqueda', [])):
            var = tk.BooleanVar(value=True if i == 0 else False)
            self.check_vars[field_name] = var
            ttk.Checkbutton(frame_busqueda, text=display_name, variable=var).pack(side=tk.LEFT, padx=5)

        self.ent_busqueda = ttk.Entry(frame_busqueda, width=40)
        self.ent_busqueda.pack(side=tk.LEFT, padx=10)
        self.ent_busqueda.focus_set()
        self.ent_busqueda.bind('<Return>', lambda e: self._buscar())

        ttk.Button(frame_busqueda, text="Buscar", command=self._buscar).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_busqueda, text="Limpiar", command=self._limpiar_busqueda).pack(side=tk.LEFT, padx=5)

        frame_tree = ttk.Frame(main_frame)
        frame_tree.pack(fill=tk.BOTH, expand=True)

        columns = [field for _, field, _ in self.config.get('columnas', [])]
        
        self.tree = ttk.Treeview(frame_tree, columns=columns, show='headings', selectmode='browse')
        
        for i, (display, field, width) in enumerate(self.config.get('columnas', [])):
            self.tree.heading(columns[i], text=display)
            self.tree.column(columns[i], width=width, anchor=tk.CENTER if i > 0 else tk.W)

        scrollbar_y = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(frame_tree, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x.grid(row=1, column=0, sticky='ew')
        
        frame_tree.grid_rowconfigure(0, weight=1)
        frame_tree.grid_columnconfigure(0, weight=1)

        self.tree.bind('<Double-1>', lambda e: self._seleccionar())

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text="Seleccionar", command=self._seleccionar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT, padx=5)

        lbl_status = ttk.Label(main_frame, text="", foreground="gray")
        lbl_status.pack(fill=tk.X, pady=(5, 0))
        self.lbl_status = lbl_status

    def _cargar_datos(self, filtro_sql="", params=None):
        try:
            if self.modo_archivos:
                self._cargar_archivos()
            else:
                self._cargar_desde_bd(filtro_sql, params)
        except Exception as e:
            messagebox.showerror("Error al Cargar Datos", f"{type(e).__name__}: {e}")
            self.lbl_status.config(text="Error al cargar datos")
            
    def _cargar_archivos(self):
        backup_dir = get_backup_dir()
        archivos = []
        
        if os.path.exists(backup_dir):
            for f in os.listdir(backup_dir):
                if f.endswith(".db"):
                    ruta = os.path.join(backup_dir, f)
                    tamanio = os.path.getsize(ruta)
                    archivos.append((f, tamanio))
        
        archivos.sort(key=lambda x: x[0], reverse=True)
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for nombre, tamanio in archivos:
            ruta_backup = os.path.join(backup_dir, nombre)
            tamanio_mb = round(tamanio / (1024 * 1024), 2)
            self.tree.insert('', 'end', values=[nombre, f"{tamanio_mb} MB"], tags=(ruta_backup,))
        
        self.lbl_status.config(text=f"Total de respaldos: {len(archivos)}")

    def _cargar_desde_bd(self, filtro_sql, params):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        tabla = self.config.get('tabla')
        columnas = [field for _, field, _ in self.config.get('columnas', [])]
        id_field = self.config.get('id_field')
        orden_por = self.config.get('orden_por', f"{columnas[0]} ASC")
        filtro_adicional = self.config.get('filtro_adicional', '')
        
        columnas_str = ", ".join(columnas)
        
        sql = f"""
            SELECT {id_field}, {columnas_str}
            FROM {tabla}
            {filtro_adicional}
            {filtro_sql}
            ORDER BY {orden_por}
        """
        
        params = params or ()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for row in rows:
            registro_id = row[0]
            valores_fila = row[1:]
            
            valores_formateados = []
            for i, valor in enumerate(valores_fila):
                if valor is None:
                    valores_formateados.append("")
                elif isinstance(valor, int):
                    if columnas[i] == 'com_Status' or columnas[i] == 'uo_active':
                        valores_formateados.append("Activo" if valor == 1 else "Inactivo")
                    else:
                        valores_formateados.append(str(valor))
                else:
                    valores_formateados.append(str(valor))
            
            self.tree.insert('', 'end', values=valores_formateados, tags=(str(registro_id),))
        
        total_registros = len(rows)
        self.lbl_status.config(text=f"Total de registros: {total_registros}")
        
        conn.close()

    def _buscar(self):
        if self.modo_archivos:
            return
        texto = self.ent_busqueda.get().strip()
            
        if not texto:
            self._cargar_datos()
            return
            
        campos_activos = [field for field, var in self.check_vars.items() if var.get()]
            
        if not campos_activos:
            messagebox.showwarning("Advertencia", "Debe seleccionar al menos un campo para buscar.")
            return
            
        condiciones = []
        params = []
            
        for campo in campos_activos:
            condiciones.append(f"{campo} LIKE ?")
            params.append(f"%{texto}%")
            
        filtro_sql = f"AND ({' OR '.join(condiciones)})"
            
        self._cargar_datos(filtro_sql=filtro_sql, params=params)

    def _limpiar_busqueda(self):
        if self.modo_archivos:
            return
        self.ent_busqueda.delete(0, tk.END)
        for var in self.check_vars.values():
            var.set(False)
        if self.check_vars:
            list(self.check_vars.values())[0].set(True)
        self._cargar_datos()

    def _seleccionar(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Debe seleccionar un registro de la lista.")
            return
        
        item = self.tree.item(seleccion[0])
        valores = item['values']
        tags = item.get('tags', [])
        
        if self.modo_archivos:
            ruta_completa = tags[0] if tags else None
            if not ruta_completa:
                messagebox.showerror("Error", "No se pudo identificar el archivo seleccionado.")
                return
            self.resultado = {'ruta': ruta_completa, 'nombre': valores[0]}
        else:
            registro_id = tags[0] if tags else None
            if not registro_id:
                messagebox.showerror("Error", "No se pudo identificar el registro seleccionado.")
                return
            self.resultado = {'id': int(registro_id), 'valores': valores}
        
        self.destroy()