import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import sqlite3
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.system_info import get_current_user, get_machine_name
from db.embedded_db import get_db_connection

class DialogUndsOperativas(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Registro de Unidades Operativas")
        self.geometry("720x500") # Ajustar altura, puede no necesitar tantos campos como Company
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (720 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (500 // 2)
        self.geometry(f"+{x}+{y}")

        self.current_id = None # Para manejar edición/borrado
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
            # Crear una lista de strings para el Combobox, guardando el ID
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

        ttk.Label(frame_general, text="Nombre:").grid(row=1, column=0, sticky="w", pady=3)
        self.ent_nombre = ttk.Entry(frame_general, width=60)
        self.ent_nombre.grid(row=1, column=1, columnspan=2, padx=5, pady=3, sticky="ew")

        ttk.Label(frame_general, text="Descripción:").grid(row=2, column=0, sticky="w", pady=3)
        self.ent_descripcion = ttk.Entry(frame_general, width=60)
        self.ent_descripcion.grid(row=2, column=1, columnspan=2, padx=5, pady=3, sticky="ew")

        ttk.Label(frame_general, text="Empresa:").grid(row=3, column=0, sticky="w", pady=3)
        self.cmb_empresa = ttk.Combobox(frame_general, values=self.empresa_display, state="readonly", width=58)
        self.cmb_empresa.grid(row=3, column=1, columnspan=2, padx=5, pady=3, sticky="ew")
        # No seleccionamos nada por defecto


        # --- Sección: Conexión ---
        frame_conexion = ttk.Labelframe(main_frame, text="Conexión a Base de Datos (DBISAM)", padding=10)
        frame_conexion.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(frame_conexion, text="DSN:").grid(row=0, column=0, sticky="w", pady=3)
        self.cmb_dsn = ttk.Combobox(frame_conexion, width=58, state="readonly") # Valores se cargarán dinámicamente
        self.cmb_dsn.grid(row=0, column=1, columnspan=2, padx=5, pady=3, sticky="ew")
        # Cargar DSNs desde conexiones.json aquí, después de crear el widget
        self._load_dsn_options_from_json()

        ttk.Label(frame_conexion, text="Ruta Base de Datos:").grid(row=1, column=0, sticky="w", pady=3)
        self.ent_db_path = ttk.Entry(frame_conexion, width=58)
        self.ent_db_path.grid(row=1, column=1, columnspan=2, padx=5, pady=3, sticky="ew")

        ttk.Label(frame_conexion, text="Activa:").grid(row=2, column=0, sticky="w", pady=3)
        self.cmb_activa = ttk.Combobox(frame_conexion, values=["Sí", "No"], state="readonly", width=10)
        self.cmb_activa.grid(row=2, column=1, padx=5, pady=3, sticky="w")
        self.cmb_activa.set("Sí")


        # --- Botones de acción ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, sticky="ew", pady=15, padx=10)

        # ttk.Button(btn_frame, text="Incluir", command=self._incluir).pack(side=tk.LEFT, padx=5) # Removido
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

            # Validar que se haya seleccionado una empresa
            empresa_seleccionada_idx = self.cmb_empresa.current()
            if empresa_seleccionada_idx == -1:
                 messagebox.showwarning("Advertencia", "Debe seleccionar una Empresa.")
                 return
            empresa_id = self.empresa_ids[empresa_seleccionada_idx]

            # Obtener ID de DSN (asumiendo que cmb_dsn tiene una lógica similar)
            dsn_name = self.cmb_dsn.get() # Asumiendo que el valor mostrado es el nombre del DSN
            if not dsn_name:
                 messagebox.showwarning("Advertencia", "Debe seleccionar un DSN.")
                 return

            activa = 1 if self.cmb_activa.get() == "Sí" else 0

            if messagebox.askyesno("Confirmar Guardado", "¿Guardar los datos de la Unidad Operativa?"):
                conn = get_db_connection()
                cursor = conn.cursor()

                if self.current_id is None:
                    # Insertar nuevo
                    cursor.execute("""
                        INSERT INTO ark_unds_operativas (
                            uo_codigo, uo_nombre, uo_descripcion,
                            uo_empresa_id, uo_dsn_name, uo_db_path, uo_active,
                            uo_UserCreator, uo_NameMachine
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        self.ent_codigo.get().strip(),
                        self.ent_nombre.get().strip(),
                        self.ent_descripcion.get().strip(),
                        empresa_id,
                        dsn_name,
                        self.ent_db_path.get().strip(),
                        activa,
                        get_current_user(),
                        get_machine_name()
                    ))
                    self.current_id = cursor.lastrowid
                else:
                    # Actualizar existente (pendiente para ticket especial)
                    messagebox.showinfo("Info", "Edición no implementada aún. Use 'Cancelar' para limpiar.")
                    conn.close()
                    return # No cerrar la conexión aún si no se guarda

                conn.commit()
                conn.close()
                messagebox.showinfo("Éxito", "Unidad Operativa guardada correctamente.")
                self._limpiar_campos()

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
            if messagebox.askyesno("Confirmar Borrado", "¿Eliminar esta Unidad Operativa? Esta acción no se puede deshacer."):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM ark_unds_operativas WHERE uo_id = ?", (self.current_id,))
                conn.commit()
                conn.close()
                messagebox.showinfo("Éxito", "Unidad Operativa eliminada.")
                self._limpiar_campos()
                self.current_id = None
        except Exception as e:
            messagebox.showerror("Error en Borrar", f"{type(e).__name__}: {e}")

    def _cancelar(self):
        try:
            if any([
                self.ent_codigo.get(), self.ent_nombre.get(), self.ent_descripcion.get(),
                self.ent_db_path.get()
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
        self.ent_nombre.delete(0, tk.END)
        self.ent_descripcion.delete(0, tk.END)
        self.ent_db_path.delete(0, tk.END)
        # Limpiar selecciones de Combobox
        self.cmb_empresa.set('')
        self.cmb_dsn.set('')
        self.cmb_activa.set("Sí") # Valor por defecto
        # Reiniciar current_id
        self.current_id = None
    
    def _load_dsn_options_from_json(self):
        """Carga las opciones del Combobox de DSN desde conexiones.json."""
        try:
            # Construir la ruta al archivo JSON
            config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'conexiones.json'))
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    conexiones = json.load(f)
                # Extraer DSNs únicos
                dsn_list = list(set([conn['dsn'] for conn in conexiones if 'dsn' in conn]))
                # Asignar la lista al Combobox
                self.cmb_dsn['values'] = dsn_list
            else:
                # Si el archivo no existe, dejar la lista vacía
                self.cmb_dsn['values'] = []
        except Exception as e:
            # En caso de error (archivo corrupto, sin permiso, etc.), mostrar un mensaje y dejar la lista vacía
            messagebox.showerror("Error", f"No se pudieron cargar los DSNs desde conexiones.json: {e}")
            self.cmb_dsn['values'] = []

