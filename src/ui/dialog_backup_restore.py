import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from core.backup_restore import crear_backup, restaurar_backup, listar_backups, eliminar_backup

class DialogBackupRestore(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Gestión de Respaldos (Backup/Restore)")
        self.geometry("700x500")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._center_on_parent()
        self.configure(bg="#F5F5F5")

        self._crear_widgets()
        self._cargar_backups()

        self.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.wait_window(self)

    def _center_on_parent(self):
        self.update_idletasks()
        pw = self.parent.winfo_width()
        ph = self.parent.winfo_height()
        px = self.parent.winfo_x()
        py = self.parent.winfo_y()
        w = 700
        h = 500
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _crear_widgets(self):
        frame_principal = ttk.Frame(self, padding=15)
        frame_principal.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame_principal,
            text="💾 GESTIÓN DE RESPALDOS",
            font=("Segoe UI", 14, "bold"),
            foreground="#1976D2"
        ).pack(pady=(0, 10))

        frame_lista = ttk.Frame(frame_principal)
        frame_lista.pack(fill=tk.BOTH, expand=True, pady=5)

        columns = ("nombre", "fecha", "tamano")
        self.tree = ttk.Treeview(frame_lista, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("nombre", text="Nombre del Archivo")
        self.tree.heading("fecha", text="Fecha de Creación")
        self.tree.heading("tamano", text="Tamaño")

        self.tree.column("nombre", width=350)
        self.tree.column("fecha", width=200, anchor=tk.CENTER)
        self.tree.column("tamano", width=100, anchor=tk.E)

        scrollbar = ttk.Scrollbar(frame_lista, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        frame_botones = ttk.Frame(frame_principal)
        frame_botones.pack(fill=tk.X, pady=(10, 0))

        btn_crear = ttk.Button(frame_botones, text="Crear Respaldo", command=self._crear_respaldo)
        btn_crear.pack(side=tk.LEFT, padx=5)

        btn_restaurar = ttk.Button(frame_botones, text="Restaurar Seleccionado", command=self._restaurar_respaldo)
        btn_restaurar.pack(side=tk.LEFT, padx=5)

        btn_eliminar = ttk.Button(frame_botones, text="Eliminar Seleccionado", command=self._eliminar_respaldo)
        btn_eliminar.pack(side=tk.LEFT, padx=5)

        btn_cerrar = ttk.Button(frame_botones, text="Cerrar", command=self._cerrar)
        btn_cerrar.pack(side=tk.RIGHT, padx=5)

    def _cargar_backups(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            backups = listar_backups()
            for b in backups:
                tamano_mb = b["tamano"] / (1024 * 1024)
                self.tree.insert("", tk.END, values=(b["nombre"], b["fecha"], f"{tamano_mb:.2f} MB"))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los respaldos:\n\n{e}")

    def _get_seleccion(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Debe seleccionar un respaldo de la lista.")
            return None
        item = self.tree.item(seleccion[0])
        return item["values"][0]

    def _crear_respaldo(self):
        nombre = simpledialog.askstring("Nuevo Respaldo", "Nombre del archivo (opcional, dejar vacío para automático):")
        try:
            ruta = crear_backup(nombre if nombre else None)
            messagebox.showinfo("Éxito", f"Respaldo creado correctamente:\n\n{ruta}")
            self._cargar_backups()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el respaldo:\n\n{e}")

    def _restaurar_respaldo(self):
        nombre_archivo = self._get_seleccion()
        if not nombre_archivo:
            return

        from core.path_utils import get_project_root
        ruta_completa = os.path.join(get_project_root(), "ArkConInvDB", "databackup", nombre_archivo)

        confirmar = messagebox.askyesno(
            "Confirmación de Restauración",
            f"¿Está SEGURO de restaurar la base de datos con el respaldo:\n\n'{nombre_archivo}'?\n\n"
            "⚠️ ADVERTENCIA: Esta acción sobrescribirá la base de datos actual.\n"
            "Si la base de datos está en uso, la restauración podría fallar o requerir reiniciar la aplicación.",
            icon="warning"
        )

        if not confirmar:
            return

        try:
            restaurar_backup(ruta_completa)
            messagebox.showinfo(
                "Restauración Exitosa", 
                "La base de datos ha sido restaurada.\n\n"
                "⚠️ Se recomienda cerrar y volver a abrir la aplicación para asegurar la integridad de los datos."
            )
        except PermissionError:
            messagebox.showerror(
                "Error de Permisos", 
                "No se pudo restaurar porque la base de datos está en uso.\n\n"
                "Por favor, cierre la aplicación y ejecute la restauración nuevamente, o reemplace el archivo manualmente."
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo restaurar el respaldo:\n\n{e}")

    def _eliminar_respaldo(self):
        nombre_archivo = self._get_seleccion()
        if not nombre_archivo:
            return

        confirmar = messagebox.askyesno(
            "Confirmación de Eliminación",
            f"¿Está seguro de eliminar permanentemente el respaldo:\n\n'{nombre_archivo}'?",
            icon="warning"
        )

        if not confirmar:
            return

        from core.path_utils import get_project_root
        ruta_completa = os.path.join(get_project_root(), "ArkConInvDB", "databackup", nombre_archivo)

        try:
            eliminar_backup(ruta_completa)
            self._cargar_backups()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el respaldo:\n\n{e}")

    def _cerrar(self):
        self.grab_release()
        self.destroy()