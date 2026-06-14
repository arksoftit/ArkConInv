import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import json
import threading
import pyodbc
from datetime import date, datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.embedded_db import get_db_connection
from core.system_info import get_current_user, get_machine_name

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'conexiones.json'))

class DialogImportarDepositos(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Importar Depósitos desde DBISAM")
        self.geometry("600x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (600 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (400 // 2)
        self.geometry(f"+{x}+{y}")

        self.uo_data = {}
        self._create_widgets()
        self._cargar_unidades_operativas()
        self._verificar_estado_conexion()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Seleccione la Unidad Operativa de Origen:").grid(row=0, column=0, sticky=tk.W, pady=10)
        self.cmb_uo = ttk.Combobox(frame, state="readonly", width=50)
        self.cmb_uo.grid(row=1, column=0, columnspan=2, pady=5)

        self.lbl_estado_conexion = ttk.Label(frame, text="", font=("Segoe UI", 9, "bold"))
        self.lbl_estado_conexion.grid(row=2, column=0, columnspan=2, pady=10)

        self.progress = ttk.Progressbar(frame, orient="horizontal", length=560, mode="determinate")
        self.progress.grid(row=3, column=0, columnspan=2, pady=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        self.btn_importar = ttk.Button(btn_frame, text="Importar", command=self._iniciar_importacion)
        self.btn_importar.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(btn_frame, text="Cerrar", command=self.destroy).pack(side=tk.LEFT, padx=10)

    def _cargar_unidades_operativas(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT uo_id, uo_Codigo, uo_nombre FROM ark_unds_operativas WHERE uo_active = 1 ORDER BY uo_Codigo")
            rows = cursor.fetchall()
            conn.close()
            
            self.uo_data = {row[0]: f"{row[1]} - {row[2]}" for row in rows}
            self.cmb_uo['values'] = list(self.uo_data.values())
            if self.uo_data:
                self.cmb_uo.current(0)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las Unidades Operativas: {e}")

    def _verificar_estado_conexion(self):
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    conexiones = json.load(f)
                if conexiones and len(conexiones) > 0:
                    dsn_actual = conexiones[0].get('dsn', 'Desconocido')
                    self.lbl_estado_conexion.config(text=f"Conexión configurada: {dsn_actual}", foreground="blue")
                    self.btn_importar.config(state=tk.NORMAL)
                    return
        except Exception:
            pass
        
        self.lbl_estado_conexion.config(
            text="Debe realizar la conexión previamente desde el Módulo de Conexiones en el menú Configuración", 
            foreground="red"
        )
        self.btn_importar.config(state=tk.DISABLED)

    def _iniciar_importacion(self):
        if not self.cmb_uo.get():
            messagebox.showwarning("Advertencia", "Debe seleccionar una Unidad Operativa.")
            return

        selected_uo_id = list(self.uo_data.keys())[self.cmb_uo.current()]
        
        self.btn_importar.config(state=tk.DISABLED)
        self.progress['value'] = 0
        
        thread = threading.Thread(target=self._ejecutar_importacion, args=(selected_uo_id,), daemon=True)
        thread.start()

    def _ejecutar_importacion(self, uo_id):
        try:
            # Cargar credenciales
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                conexiones = json.load(f)
            if not conexiones:
                raise Exception("No hay conexiones guardadas.")

            conn_info = conexiones[0]
            dsn = conn_info['dsn']
            user = conn_info['usuario']
            pwd = conn_info['password']

            # Conectar a DBISAM
            conn_str = f"DSN={dsn};UID={user};PWD={pwd};"
            dbisam_conn = pyodbc.connect(conn_str, autocommit=True)
            cursor_dbisam = dbisam_conn.cursor()

            # SELECT con los 8 campos de DBISAM
            query_dbisam = """
                SELECT FDP_CODIGO, FDP_DESCRIPCION, FDP_STATUS,
                FDP_DESCRIPCIONDETALLADA, FDP_RESPONSABLE, BASE_AUTOINCREMENT,
                FDP_CODE, FDP_SERIE
                FROM Sdepositos
            """
            cursor_dbisam.execute(query_dbisam)
            rows = cursor_dbisam.fetchall()
            total = len(rows)
            dbisam_conn.close()

            # Conectar a SQLite
            sqlite_conn = get_db_connection()
            sqlite_cursor = sqlite_conn.cursor()

            # Limpiar tabla
            sqlite_cursor.execute("DELETE FROM ark_depositos")

            # INSERT con 17 columnas (8 datos + 1 uo_id + 8 auditoría)
            query_sqlite = """
                INSERT INTO ark_depositos (
                    dep_codigo, dep_descripcion, dep_status,
                    dep_descripciondetallada, dep_responsable, dep_base_autoincrement,
                    dep_code, dep_serie, dep_uo_origen,
                    dep_SystemDate, dep_SystemTime, dep_NameMachine, dep_UserCreator,
                    dep_LastUpdateDate, dep_LastUpdateTime, dep_LastMachine, dep_UserLastUpdate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            # Valores de auditoría
            user_creator = get_current_user()
            machine_name = get_machine_name()
            sys_date = date.today().isoformat()
            sys_time = datetime.now().time().isoformat()
            
            audit_values = [
                sys_date,           # dep_SystemDate
                sys_time,           # dep_SystemTime
                machine_name,       # dep_NameMachine
                user_creator,       # dep_UserCreator
                sys_date,           # dep_LastUpdateDate
                sys_time,           # dep_LastUpdateTime
                machine_name,       # dep_LastMachine
                user_creator        # dep_UserLastUpdate
            ]

            # Insertar registros
            for i, row in enumerate(rows):
                data = list(row) + [uo_id] + audit_values
                sqlite_cursor.execute(query_sqlite, data)

                if (i + 1) % 10 == 0 or i == total - 1:
                    porcentaje = int(((i + 1) / total) * 100)
                    self.after(0, self._actualizar_progreso, porcentaje)

            sqlite_conn.commit()
            sqlite_conn.close()

           # self.after(0, self._finalizar_importacion, True)
            self.after(0, self._finalizar_importacion, True, total)

        except Exception as e:
            self.after(0, self._finalizar_importacion, False, str(e))

    def _actualizar_progreso(self, valor):
        self.progress['value'] = valor

    def _finalizar_importacion(self, exito, total_registros=0, error_msg=""):
        self.btn_importar.config(state=tk.NORMAL)
        if exito:
            self.progress['value'] = 100
            messagebox.showinfo("Éxito", f"Importación de Depósitos completada.\nRegistros importados: {total_registros}")
        else:
            self.progress['value'] = 0
            messagebox.showerror("Error", f"Falló la importación: {error_msg}")