import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import sqlite3
import hashlib # Para encriptar la contraseña si es necesario

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.system_info import get_current_user, get_machine_name
from db.embedded_db import get_db_connection

class DialogUsers(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Registro de Usuarios")
        self.geometry("720x580")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (720 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (580 // 2)
        self.geometry(f"+{x}+{y}")

        self.current_id = None # Para manejar edición/borrado
        self.empresa_ids = [] # Lista de IDs de empresas
        self.empresa_display = [] # Lista de cadenas para mostrar en Combobox
        self._load_empresa_options() # Cargar opciones de empresa antes de crear widgets

        self._create_widgets()

    def _load_empresa_options(self):
        """Carga las opciones del Combobox de Empresa desde ark_company."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT com_IDauto, com_Codigo, com_Descripcion FROM ark_company ORDER BY com_Codigo")
            rows = cursor.fetchall()
            conn.close()
            self.empresa_options = [(row[0], f"{row[1]} - {row[2]}") for row in rows]
            self.empresa_ids = [opt[0] for opt in self.empresa_options]
            self.empresa_display = [opt[1] for opt in self.empresa_options]
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las empresas: {e}")
            self.empresa_options = []
            self.empresa_ids = []
            self.empresa_display = []

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Sección: Datos Generales ---
        frame_general = ttk.Labelframe(main_frame, text="Datos Generales", padding=10)
        frame_general.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(frame_general, text="Código:").grid(row=0, column=0, sticky="w", pady=3)
        self.ent_codigo = ttk.Entry(frame_general, width=20)
        self.ent_codigo.grid(row=0, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(frame_general, text="Login:").grid(row=1, column=0, sticky="w", pady=3)
        self.ent_login = ttk.Entry(frame_general, width=20)
        self.ent_login.grid(row=1, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(frame_general, text="Descripción:").grid(row=2, column=0, sticky="w", pady=3)
        self.ent_descripcion = ttk.Entry(frame_general, width=60)
        self.ent_descripcion.grid(row=2, column=1, columnspan=2, padx=5, pady=3, sticky="ew")

        ttk.Label(frame_general, text="Contraseña:").grid(row=3, column=0, sticky="w", pady=3)
        self.ent_password = ttk.Entry(frame_general, width=20, show="*") # Ocultar caracteres
        self.ent_password.grid(row=3, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(frame_general, text="Estado:").grid(row=4, column=0, sticky="w", pady=3)
        self.cmb_estado = ttk.Combobox(frame_general, values=["Activo", "Inactivo"], state="readonly", width=12)
        self.cmb_estado.grid(row=4, column=1, padx=5, pady=3, sticky="w")
        self.cmb_estado.set("Activo")

        ttk.Label(frame_general, text="Rol:").grid(row=5, column=0, sticky="w", pady=3)
        self.cmb_rol = ttk.Combobox(frame_general, values=["Administrador", "Operador", "Consulta"], state="readonly", width=12)
        self.cmb_rol.grid(row=5, column=1, padx=5, pady=3, sticky="w")
        self.cmb_rol.set("Consulta") # Valor por defecto


        # --- Sección: Información Adicional ---
        frame_adicional = ttk.Labelframe(main_frame, text="Información Adicional", padding=10)
        frame_adicional.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(frame_adicional, text="Teléfono:").grid(row=0, column=0, sticky="w", pady=3)
        self.ent_telefono = ttk.Entry(frame_adicional, width=20) # Nuevo campo
        self.ent_telefono.grid(row=0, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(frame_adicional, text="Cargo:").grid(row=1, column=0, sticky="w", pady=3)
        self.ent_cargo = ttk.Entry(frame_adicional, width=30)
        self.ent_cargo.grid(row=1, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(frame_adicional, text="Email Usuario:").grid(row=2, column=0, sticky="w", pady=3)
        self.ent_email_usuario = ttk.Entry(frame_adicional, width=40)
        self.ent_email_usuario.grid(row=2, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(frame_adicional, text="Empresa:").grid(row=3, column=0, sticky="w", pady=3)
        self.cmb_empresa = ttk.Combobox(frame_adicional, values=self.empresa_display, state="readonly", width=58)
        self.cmb_empresa.grid(row=3, column=1, columnspan=2, padx=5, pady=3, sticky="ew")
        # No seleccionamos nada por defecto


        # --- Botones de acción ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, sticky="ew", pady=15, padx=10)

        ttk.Button(btn_frame, text="Guardar", command=self._guardar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Editar", command=self._editar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Borrar", command=self._borrar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancelar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Salir", command=self._salir).pack(side=tk.RIGHT, padx=5)

    def _guardar(self):
        try:
            if not self.ent_codigo.get().strip():
                messagebox.showwarning("Advertencia", "El campo 'Código' es obligatorio.")
                return

            # Validar que se haya seleccionado una empresa (opcional, si no es requerido dejar NULL)
            empresa_id = None
            empresa_seleccionada_idx = self.cmb_empresa.current()
            if empresa_seleccionada_idx != -1: # Si se seleccionó algo
                empresa_id = self.empresa_ids[empresa_seleccionada_idx]

            status = 1 if self.cmb_estado.get() == "Activo" else 0
            rol_map = {"Administrador": "Admin", "Operador": "Oper", "Consulta": "Cons"} # Ajustar según tu esquema
            rol = rol_map[self.cmb_rol.get()]
            # Considerar encriptar la contraseña aquí si no lo haces en la base de datos
            password_hash = hashlib.sha256(self.ent_password.get().encode()).hexdigest() if self.ent_password.get() else None

            if messagebox.askyesno("Confirmar Guardado", "¿Guardar los datos del usuario?"):
                conn = get_db_connection()
                cursor = conn.cursor()

                if self.current_id is None:
                    # Insertar nuevo
                    cursor.execute("""
                        INSERT INTO ark_users (
                            usr_Codigo, usr_login, usr_Descripcion,
                            usr_Status, usr_Telefono, usr_Rol, usr_Password, -- Añadido usr_Telefono
                            id_company, usr_Cargo, usr_EmailUsuario,
                            usr_UserCreator, usr_NameMachine
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        self.ent_codigo.get().strip(),
                        self.ent_login.get().strip(),
                        self.ent_descripcion.get().strip(),
                        status,
                        self.ent_telefono.get().strip(), # Nuevo campo
                        rol,
                        password_hash, # Guardar hash en lugar de texto plano
                        empresa_id,
                        self.ent_cargo.get().strip(),
                        self.ent_email_usuario.get().strip(),
                        get_current_user(),
                        get_machine_name()
                    ))
                    self.current_id = cursor.lastrowid
                    messagebox.showinfo("Éxito", "Usuario guardado correctamente.")
                    self._limpiar_campos()
                else:
                    # Actualizar existente (pendiente para ticket especial)
                    # UPDATE query aquí si se implementa edición
                    messagebox.showinfo("Info", "La edición de usuarios no está implementada aún.")
                    conn.close()
                    return

                conn.commit()
                conn.close()


        except Exception as e:
            messagebox.showerror("Error en Guardar", f"{type(e).__name__}: {e}")

    def _editar(self):
        try:
            messagebox.showinfo("Pendiente", "Funcionalidad de edición será implementada en ticket especial.")
        except Exception as e:
            messagebox.showerror("Error en Editar", f"{type(e).__name__}: {e}")

    def _borrar(self):
        try:
            if self.current_id is None:
                messagebox.showwarning("Advertencia", "No hay registro seleccionado para borrar.")
                return
            if messagebox.askyesno("Confirmar Borrado", "¿Eliminar este usuario? Esta acción no se puede deshacer."):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM ark_users WHERE usr_IDauto = ?", (self.current_id,))
                conn.commit()
                conn.close()
                messagebox.showinfo("Éxito", "Usuario eliminado.")
                self._limpiar_campos()
                self.current_id = None
        except Exception as e:
            messagebox.showerror("Error en Borrar", f"{type(e).__name__}: {e}")

    def _cancelar(self):
        try:
            if any([
                self.ent_codigo.get(), self.ent_login.get(), self.ent_descripcion.get(),
                self.ent_password.get(), self.ent_telefono.get(), # Añadido ent_telefono
                self.ent_cargo.get(), self.ent_email_usuario.get()
            ]):
                if not messagebox.askyesno("Confirmar Cancelar", "¿Descartar todos los cambios?"):
                    return
            self._limpiar_campos()
        except Exception as e:
            messagebox.showerror("Error en Cancelar", f"{type(e).__name__}: {e}")

    def _salir(self):
        try:
            if messagebox.askyesno("Confirmar Salida", "¿Cerrar este diálogo?"):
                self.destroy()
        except Exception as e:
            messagebox.showerror("Error en Salir", f"{type(e).__name__}: {e}")

    def _limpiar_campos(self):
        # Limpiar entradas de texto
        self.ent_codigo.delete(0, tk.END)
        self.ent_login.delete(0, tk.END)
        self.ent_descripcion.delete(0, tk.END)
        self.ent_password.delete(0, tk.END) # Considera limpiar también el hash si se almacena temporalmente
        self.ent_telefono.delete(0, tk.END) # Nuevo campo
        self.ent_cargo.delete(0, tk.END)
        self.ent_email_usuario.delete(0, tk.END)
        # Limpiar selecciones de Combobox
        self.cmb_estado.set("Activo")
        self.cmb_rol.set("Consulta")
        self.cmb_empresa.set('') # Limpiar selección de empresa
        # Reiniciar current_id
        self.current_id = None
