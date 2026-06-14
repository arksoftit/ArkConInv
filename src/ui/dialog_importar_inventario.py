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

class DialogImportarInventario(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Importar Inventario desde DBISAM")
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

        self.btn_importar.config(state=tk.DISABLED)
        self.progress['value'] = 0
        
        thread = threading.Thread(target=self._ejecutar_importacion, daemon=True)
        thread.start()

    def _ejecutar_importacion(self):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                conexiones = json.load(f)
            if not conexiones:
                raise Exception("No hay conexiones guardadas.")

            conn_info = conexiones[0]
            dsn = conn_info['dsn']
            user = conn_info['usuario']
            pwd = conn_info['password']

            conn_str = f"DSN={dsn};UID={user};PWD={pwd};"
            dbisam_conn = pyodbc.connect(conn_str, autocommit=True)
            cursor_dbisam = dbisam_conn.cursor()

            query_dbisam = """
                SELECT FI_CODIGO, FI_DESCRIPCION, FI_CATEGORIA, FI_DESCRIPCIONDETALLADA,
                FI_VENDEDOR, FI_STATUS, FI_UNIDAD, FI_TIPOCODIGOBARRA, FI_IMAGEN,
                FI_SUSTITUTO1, FI_SUSTITUTO2, FI_SUSTITUTO3, FI_REFERENCIA, FI_MARCA,
                FI_MONEDA, FI_FACTORCONVERSION, FI_UNDEXISTENCIA2, FI_PUESTO,
                FI_SUJETOACOMISION, FI_MONTOCOMISION, FI_CUENTASCONTABLES, FI_PESOPRODUCTO,
                FI_DIASDEREPOSICION, FI_PRESENTACION, FI_GARANTIA, FI_SUSTITUTO4,
                FI_SUSTITUTO5, FI_MONTOCOMISIONP, FI_DEPOSITOS, FI_OFERTAS,
                FI_VENCIMIENTOS, FI_CLASIFICACION, FI_MANEJOINVENTARIO, FI_SERIALES,
                FI_CREACION, FI_INVENTARIOINICIALUNIDADES, FI_INVENTARIOINICIALCOSTO,
                FI_CAPACIDAD, FI_EXISTDECIMAL, FI_COMPUESTOSERIALES, FI_VENDEDORFIJO,
                FI_VENDEDORFIJOACTIVO, FI_MODELO, FI_SUBCATEGORIA, FI_PESOAFECTACOSTO,
                FI_IMPRESORA, BASE_AUTOINCREMENT, FI_ZEXTRA1, FI_ZEXTRA2, FI_ZEXTRA3,
                FI_ZEXTRA4, FI_ZEXTRA5, FI_ZEXTRA6, FI_ZEXTRA1VENTA, FI_ZEXTRA2VENTA,
                FI_ZEXTRA3VENTA, FI_ZEXTRA4VENTA, FI_ZEXTRA5VENTA, FI_ZEXTRA6VENTA,
                FI_ZEXTRA1VENTAMOD, FI_ZEXTRA2VENTAMOD, FI_ZEXTRA3VENTAMOD, FI_ZEXTRA4VENTAMOD,
                FI_ZEXTRA5VENTAMOD, FI_ZEXTRA6VENTAMOD, FI_INTERNET, FI_BALANZA,
                FI_CODIGOBARRA, FI_PRECIOLISTA, FI_APROVECHAPORC, FI_ARANCEL,
                FI_POSENTREGA, FI_CARGOSEXTRAS
                FROM SInventario
            """
            cursor_dbisam.execute(query_dbisam)
            rows = cursor_dbisam.fetchall()
            total = len(rows)
            dbisam_conn.close()

            sqlite_conn = get_db_connection()
            sqlite_cursor = sqlite_conn.cursor()

            sqlite_cursor.execute("DELETE FROM ark_inventario")

            query_sqlite = """
                INSERT INTO ark_inventario (
                    inv_codigo, inv_descripcion, inv_categoria, inv_descripciondetallada,
                    inv_vendedor, inv_status, inv_unidad, inv_tipocodigobarra, inv_imagen,
                    inv_sustituto1, inv_sustituto2, inv_sustituto3, inv_referencia, inv_marca,
                    inv_moneda, inv_factorconversion, inv_undexistencia2, inv_puesto,
                    inv_sujetoacomision, inv_montocomision, inv_cuentascontables, inv_pesoproducto,
                    inv_diasdereposicion, inv_presentacion, inv_garantia, inv_sustituto4,
                    inv_sustituto5, inv_montocomisionp, inv_depositos, inv_ofertas,
                    inv_vencimientos, inv_clasificacion, inv_manejoinventario, inv_seriales,
                    inv_creacion, inv_inventarioinicialunidades, inv_inventarioinicialcosto,
                    inv_capacidad, inv_existdecimal, inv_compuestoseriales, inv_vendedorfijo,
                    inv_vendedorfijoactivo, inv_modelo, inv_subcategoria, inv_pesoafectacosto,
                    inv_impresora, base_autoincrement, inv_zextra1, inv_zextra2, inv_zextra3,
                    inv_zextra4, inv_zextra5, inv_zextra6, inv_zextra1venta, inv_zextra2venta,
                    inv_zextra3venta, inv_zextra4venta, inv_zextra5venta, inv_zextra6venta,
                    inv_zextra1ventamod, inv_zextra2ventamod, inv_zextra3ventamod, inv_zextra4ventamod,
                    inv_zextra5ventamod, inv_zextra6ventamod, inv_internet, inv_balanza,
                    inv_codigobarra, inv_preciolista, inv_aprovechaporc, inv_arancel,
                    inv_posentrega, inv_cargosextras,
                    inv_SystemDate, inv_SystemTime, inv_NameMachine, inv_UserCreator,
                    inv_LastUpdateDate, inv_LastUpdateTime, inv_LastMachine, inv_UserLastUpdate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            user_creator = get_current_user()
            machine_name = get_machine_name()
            sys_date = date.today().isoformat()
            sys_time = datetime.now().time().isoformat()
            
            audit_values = [
                sys_date, sys_time, machine_name, user_creator,
                sys_date, sys_time, machine_name, user_creator
            ]

            for i, row in enumerate(rows):
                data = []
                for value in row:
                    if type(value).__name__ == 'Decimal':
                        data.append(float(value) if value is not None else None)
                    else:
                        data.append(value)
                data.extend(audit_values)
                
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
            messagebox.showinfo("Éxito", f"Importación de Inventario completada.\nRegistros importados: {total_registros}")
        else:
            self.progress['value'] = 0
            messagebox.showerror("Error", f"Falló la importación: {error_msg}")