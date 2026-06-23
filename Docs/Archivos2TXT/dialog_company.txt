import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.system_info import get_current_user, get_machine_name
from db.embedded_db import get_db_connection

class DialogCompany(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Registro de Empresa")
        self.geometry("720x580")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (720 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (580 // 2)
        self.geometry(f"+{x}+{y}")

        self.db_conn = None
        self.current_id = None

        self._create_widgets()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Sección: Datos Generales ---
        frame_general = ttk.Labelframe(main_frame, text="Datos Generales", padding=10)
        frame_general.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(frame_general, text="Código:").grid(row=0, column=0, sticky="w", pady=3)
        self.ent_codigo = ttk.Entry(frame_general, width=20)
        self.ent_codigo.grid(row=0, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(frame_general, text="Razón Social:").grid(row=1, column=0, sticky="w", pady=3)
        self.ent_razon = ttk.Entry(frame_general, width=60)
        self.ent_razon.grid(row=1, column=1, columnspan=2, padx=5, pady=3, sticky="ew")

        ttk.Label(frame_general, text="ID Fiscal (RIF):").grid(row=2, column=0, sticky="w", pady=3)
        self.ent_rif = ttk.Entry(frame_general, width=20)
        self.ent_rif.grid(row=2, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(frame_general, text="Estado:").grid(row=3, column=0, sticky="w", pady=3)
        self.cmb_estado = ttk.Combobox(frame_general, values=["Activo", "Inactivo"], state="readonly", width=12)
        self.cmb_estado.grid(row=3, column=1, padx=5, pady=3, sticky="w")
        self.cmb_estado.set("Activo")

        ttk.Label(frame_general, text="Tipo Contribuyente:").grid(row=4, column=0, sticky="w", pady=3)
        self.cmb_tipo = ttk.Combobox(frame_general, values=["Ordinario", "Especial", "No Contribuyente"], state="readonly", width=12)
        self.cmb_tipo.grid(row=4, column=1, padx=5, pady=3, sticky="w")
        self.cmb_tipo.set("Ordinario")

        # --- Sección: Dirección y Teléfonos ---
        frame_direc = ttk.Labelframe(main_frame, text="Dirección y Teléfonos", padding=10)
        frame_direc.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(frame_direc, text="Dirección Fiscal:").grid(row=0, column=0, sticky="w", pady=3)
        self.ent_dir_fiscal = ttk.Entry(frame_direc, width=50)
        self.ent_dir_fiscal.grid(row=0, column=1, columnspan=2, padx=5, pady=3, sticky="ew")

        ttk.Label(frame_direc, text="Dirección Local:").grid(row=1, column=0, sticky="w", pady=3)
        self.ent_dir_local = ttk.Entry(frame_direc, width=50)
        self.ent_dir_local.grid(row=1, column=1, columnspan=2, padx=5, pady=3, sticky="ew")

        ttk.Label(frame_direc, text="Teléfono Ppal.:").grid(row=2, column=0, sticky="w", pady=3)
        self.ent_tel_ppal = ttk.Entry(frame_direc, width=20)
        self.ent_tel_ppal.grid(row=2, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(frame_direc, text="Teléfono Móvil:").grid(row=2, column=2, sticky="w", pady=3)
        self.ent_tel_movil = ttk.Entry(frame_direc, width=20)
        self.ent_tel_movil.grid(row=2, column=3, padx=5, pady=3, sticky="w")

        ttk.Label(frame_direc, text="Email Empresa:").grid(row=3, column=0, sticky="w", pady=3)
        self.ent_email_emp = ttk.Entry(frame_direc, width=50)
        self.ent_email_emp.grid(row=3, column=1, columnspan=2, padx=5, pady=3, sticky="ew")

        # --- Sección: Contactos (ahora debajo de Dirección y Teléfonos) ---
        frame_contacto = ttk.Labelframe(main_frame, text="Contactos", padding=10)
        frame_contacto.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(frame_contacto, text="Representante Legal:").grid(row=0, column=0, sticky="w", pady=3)
        self.ent_rep_legal = ttk.Entry(frame_contacto, width=40)
        self.ent_rep_legal.grid(row=0, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(frame_contacto, text="Cédula:").grid(row=1, column=0, sticky="w", pady=3)
        self.ent_cedula = ttk.Entry(frame_contacto, width=20)
        self.ent_cedula.grid(row=1, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(frame_contacto, text="Teléfono Contacto:").grid(row=2, column=0, sticky="w", pady=3)
        self.ent_tel_contacto = ttk.Entry(frame_contacto, width=20)
        self.ent_tel_contacto.grid(row=2, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(frame_contacto, text="Email Contacto:").grid(row=3, column=0, sticky="w", pady=3)
        self.ent_email_contacto = ttk.Entry(frame_contacto, width=40)
        self.ent_email_contacto.grid(row=3, column=1, padx=5, pady=3, sticky="ew")

        # --- Barra de acciones (fuera de main_frame, al final) ---
        # btn_frame = ttk.Frame(self)
        # btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # ttk.Button(btn_frame, text="Incluir", command=self._incluir).pack(side=tk.LEFT, padx=5)
        # ttk.Button(btn_frame, text="Guardar", command=self._guardar).pack(side=tk.LEFT, padx=5)
        # ttk.Button(btn_frame, text="Editar", command=self._editar).pack(side=tk.LEFT, padx=5)
        # ttk.Button(btn_frame, text="Borrar", command=self._borrar).pack(side=tk.LEFT, padx=5)
        # ttk.Button(btn_frame, text="Cancelar", command=self._cancelar).pack(side=tk.LEFT, padx=5)
        # ttk.Button(btn_frame, text="Salir", command=self._salir).pack(side=tk.RIGHT, padx=5)
        
        # --- Botones de acción (dentro de main_frame, como antes) ---
        btn_frame = ttk.Frame(main_frame) # <--- CAMBIADO: Dentro de main_frame, no de self
        btn_frame.grid(row=3, column=0, sticky="ew", pady=15, padx=10) # <--- CAMBIADO: grid en main_frame

        # ttk.Button(btn_frame, text="Incluir", command=self._incluir).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Guardar", command=self._guardar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Editar", command=self._editar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Borrar", command=self._borrar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancelar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Salir", command=self._salir).pack(side=tk.RIGHT, padx=5) # Puede ser LEFT también si se prefiere
    

    def _guardar(self):
        try:
            if not self.ent_codigo.get().strip():
                messagebox.showwarning("Advertencia", "El campo 'Código' es obligatorio.")
                return

            if messagebox.askyesno("Confirmar Guardado", "¿Guardar los datos de la empresa?"):
                conn = get_db_connection()
                cursor = conn.cursor()
                status = 1 if self.cmb_estado.get() == "Activo" else 0
                tipo = {"Ordinario": 1, "Especial": 2, "No Contribuyente": 3}[self.cmb_tipo.get()]

                if self.current_id is None:
                    cursor.execute("""
                        INSERT INTO ark_company (
                            com_Codigo, com_Descripcion, com_IDfiscal,
                            com_Status, com_TipoContribuyente,
                            com_DireccionF, com_DireccionL,
                            com_Telefono1, com_Telefono2,
                            com_EmailEmpresa,
                            com_Representante, com_TelefonoContacto,
                            com_EmailContacto,
                            com_UserCreator, com_NameMachine
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        self.ent_codigo.get().strip(),
                        self.ent_razon.get().strip(),
                        self.ent_rif.get().strip(),
                        status,
                        tipo,
                        self.ent_dir_fiscal.get().strip(),
                        self.ent_dir_local.get().strip(),
                        self.ent_tel_ppal.get().strip(),
                        self.ent_tel_movil.get().strip(),
                        self.ent_email_emp.get().strip(),
                        self.ent_rep_legal.get().strip(),
                        self.ent_tel_contacto.get().strip(),
                        self.ent_email_contacto.get().strip(),
                        get_current_user(),
                        get_machine_name()
                    ))
                    self.current_id = cursor.lastrowid
                    self._limpiar_campos()
                else:
                    messagebox.showinfo("Info", "Se ha presentado un error al guardar la empresa.")
                    return

                conn.commit()
                conn.close()
                messagebox.showinfo("Éxito", "Empresa guardada correctamente.")
    
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
            if messagebox.askyesno("Confirmar Borrado", "¿Eliminar esta empresa? Esta acción no se puede deshacer."):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM ark_company WHERE com_IDauto = ?", (self.current_id,))
                conn.commit()
                conn.close()
                messagebox.showinfo("Éxito", "Empresa eliminada.")
                
                self._limpiar_campos()
                self.current_id = None
        except Exception as e:
            messagebox.showerror("Error en Borrar", f"{type(e).__name__}: {e}")

    def _cancelar(self):
        try:
            if any([
                self.ent_codigo.get(), self.ent_razon.get(), self.ent_rif.get(),
                self.ent_dir_fiscal.get(), self.ent_dir_local.get(),
                self.ent_tel_ppal.get(), self.ent_tel_movil.get(),
                self.ent_email_emp.get(), self.ent_rep_legal.get(),
                self.ent_cedula.get(), self.ent_tel_contacto.get(),
                self.ent_email_contacto.get()
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
        self.ent_razon.delete(0, tk.END)
        self.ent_rif.delete(0, tk.END)
        self.ent_dir_fiscal.delete(0, tk.END)
        self.ent_dir_local.delete(0, tk.END)
        self.ent_tel_ppal.delete(0, tk.END)
        self.ent_tel_movil.delete(0, tk.END)
        self.ent_email_emp.delete(0, tk.END)
        self.ent_rep_legal.delete(0, tk.END)
        self.ent_cedula.delete(0, tk.END)
        self.ent_tel_contacto.delete(0, tk.END)
        self.ent_email_contacto.delete(0, tk.END)

        # Reiniciar comboboxes a sus valores por defecto
        self.cmb_estado.set("Activo")
        self.cmb_tipo.set("Ordinario")