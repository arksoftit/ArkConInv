import tkinter as tk
from tkinter import ttk, messagebox
import os
from core.backup_restore import crear_backup, listar_backups, eliminar_backup
from core.path_utils import get_backup_dir
from ui.dialog_main_browser import DialogMainBrowser

class DialogBackupRestore(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Gestión de Base de Datos")
        self.geometry("720x500")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (720 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (500 // 2)
        self.geometry(f"+{x}+{y}")

        self._create_widgets()
        self._cargar_lista()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(btn_frame, text="Hacer Respaldo", command=self._hacer_respaldo).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Restaurar Respaldo", command=self._restaurar_respaldo).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Eliminar Respaldo", command=self._eliminar_respaldo).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cerrar", command=self.destroy).pack(side=tk.RIGHT, padx=5)

        frame_tree = ttk.Frame(main_frame)
        frame_tree.pack(fill=tk.BOTH, expand=True)

        columns = ("nombre", "tamaño")
        self.tree = ttk.Treeview(frame_tree, columns=columns, show='headings', selectmode='browse')
        self.tree.heading("nombre", text="Nombre del Respaldo")
        self.tree.heading("tamaño", text="Tamaño")
        self.tree.column("nombre", width=450, anchor=tk.W)
        self.tree.column("tamaño", width=150, anchor=tk.CENTER)

        scrollbar_y = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(frame_tree, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x.grid(row=1, column=0, sticky='ew')
        frame_tree.grid_rowconfigure(0, weight=1)
        frame_tree.grid_columnconfigure(0, weight=1)

        self.tree.bind('<Double-1>', lambda e: self._restaurar_respaldo())

        lbl_status = ttk.Label(main_frame, text="", foreground="gray")
        lbl_status.pack(fill=tk.X, pady=(5, 0))
        self.lbl_status = lbl_status

    def _cargar_lista(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        backups = listar_backups()
        for b in backups:
            self.tree.insert('', 'end', values=[b['nombre'], f"{b['tamano']:,} bytes"], tags=(b['ruta'],))

        total = len(backups)
        self.lbl_status.config(text=f"Total de respaldos: {total}")

    def _hacer_respaldo(self):
        try:
            ruta = crear_backup()
            messagebox.showinfo("Respaldo Completado", f"Respaldo exitoso:\n{ruta}")
            self._cargar_lista()
        except Exception as e:
            messagebox.showerror("Error en Respaldo", str(e))

    def _restaurar_respaldo(self):
        config = {
            'titulo': 'Seleccionar Respaldo para Restaurar',
            'modo_archivos': True,
            'columnas': [
                ('Nombre', 'nombre', 400),
                ('Tamaño', 'tamaño', 150)
            ]
        }
        dialog = DialogMainBrowser(self, config)
        self.wait_window(dialog)
        
        if dialog.resultado:
            ruta_backup = dialog.resultado['ruta']
            if messagebox.askyesno("Confirmar Restauración", 
                f"¿Está seguro que desea restaurar:\n{dialog.resultado['nombre']}\n\nEsto sobrescribirá la base de datos actual."):
                try:
                    from core.backup_restore import restaurar_backup
                    restaurar_backup(ruta_backup)
                    messagebox.showinfo("Restauración Exitosa", "Base de datos restaurada correctamente.")
                    self._cargar_lista()
                except Exception as e:
                    messagebox.showerror("Error en Restauración", str(e))

    def _eliminar_respaldo(self):
        config = {
            'titulo': 'Seleccionar Respaldo para Eliminar',
            'modo_archivos': True,
            'columnas': [
                ('Nombre', 'nombre', 400),
                ('Tamaño', 'tamaño', 150)
            ]
        }
        dialog = DialogMainBrowser(self, config)
        self.wait_window(dialog)
        
        if dialog.resultado:
            ruta_backup = dialog.resultado['ruta']
            if messagebox.askyesno("Confirmar Eliminación", 
                f"¿Está seguro que desea eliminar:\n{dialog.resultado['nombre']}"):
                try:
                    eliminar_backup(ruta_backup)
                    messagebox.showinfo("Eliminación Exitosa", "Respaldo eliminado correctamente.")
                    self._cargar_lista()
                except Exception as e:
                    messagebox.showerror("Error al Eliminar", str(e))