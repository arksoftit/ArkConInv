import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import json
import threading
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.embedded_db import get_db_connection
from db.dbconnection import DBConnectionManager

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'conexiones.json'))

class DialogImportTransacciones(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Importar Transacciones")
        self.geometry("600x550")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (600 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (550 // 2)
        self.geometry(f"+{x}+{y}")

        self.uo_data = {}
        self.deposito_data = {}
        self.manager = DBConnectionManager(CONFIG_PATH)
        
        self._create_widgets()
        self._cargar_unidades_operativas()
        self._verificar_estado_conexion()
        

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Unidad Operativa:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=10)
        self.cmb_uo = ttk.Combobox(frame, state="readonly", width=55)
        self.cmb_uo.grid(row=0, column=1, columnspan=2, pady=5, padx=10)
        self.cmb_uo.bind("<<ComboboxSelected>>", self._on_uo_change)

        ttk.Label(frame, text="Rango de Fechas:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=10)
        fecha_frame = ttk.Frame(frame)
        fecha_frame.grid(row=1, column=1, columnspan=2, pady=5, padx=10, sticky=tk.W)
        
        ttk.Label(fecha_frame, text="Desde:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fecha_desde = ttk.Entry(fecha_frame, width=12)
        self.entry_fecha_desde.pack(side=tk.LEFT, padx=(0, 10))
        self.entry_fecha_desde.bind("<KeyRelease>", self._aplicar_mascara_fecha)
        self.entry_fecha_desde.bind("<Return>", lambda event: self.entry_fecha_hasta.focus_set())
        
        ttk.Label(fecha_frame, text="Hasta:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fecha_hasta = ttk.Entry(fecha_frame, width=12)
        self.entry_fecha_hasta.pack(side=tk.LEFT, padx=(0, 10))
        self.entry_fecha_hasta.bind("<KeyRelease>", self._aplicar_mascara_fecha)
        self.entry_fecha_hasta.bind("<Return>", lambda event: self.cmb_deposito.focus_set())
        
        ttk.Label(frame, text="Depósito:", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky=tk.W, pady=10)
        self.cmb_deposito = ttk.Combobox(frame, state="readonly", width=55)
        self.cmb_deposito.grid(row=2, column=1, columnspan=2, pady=5, padx=10)

        ttk.Label(frame, text="Status:", font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky=tk.W, pady=10)
        self.cmb_status = ttk.Combobox(frame, state="readonly", width=55, values=["Todos", "Procesada (1)", "Tránsito (4)"
        ])
        self.cmb_status.grid(row=3, column=1, columnspan=2, pady=5, padx=10)
        self.cmb_status.set("Todos")

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=4, column=0, columnspan=3, sticky=tk.EW, pady=15)

        ttk.Label(frame, text="Tablas a importar:", font=("Segoe UI", 10, "bold")).grid(row=5, column=0, sticky=tk.NW, pady=5)
        self.var_soperacioninv = tk.BooleanVar(value=False)
        self.var_sdetalleventa = tk.BooleanVar(value=False)
        self.var_sdetallecomp = tk.BooleanVar(value=False)
        self.var_sdetalleinv = tk.BooleanVar(value=False)
        self.var_sinvdep = tk.BooleanVar(value=False)
        chk_frame = ttk.Frame(frame)
        chk_frame.grid(row=5, column=1, columnspan=2, sticky=tk.W, padx=10)
        self.chk_soperacioninv = ttk.Checkbutton(
            chk_frame, text="SOperacionInv (Cabecera)",
            variable=self.var_soperacioninv,
            command=self._on_chk_tabla)
        self.chk_soperacioninv.pack(anchor=tk.W, pady=2)
        self.chk_sdetalleventa = ttk.Checkbutton(
            chk_frame, text="SDetalleVenta (Detalle Ventas)",
            variable=self.var_sdetalleventa,
            command=self._on_chk_tabla)
        self.chk_sdetalleventa.pack(anchor=tk.W, pady=2)
        self.chk_sdetallecomp = ttk.Checkbutton(
            chk_frame, text="SDetalleCompra (Detalle Compras)",
            variable=self.var_sdetallecomp,
            command=self._on_chk_tabla)
        self.chk_sdetallecomp.pack(anchor=tk.W, pady=2)
        self.chk_sdetalleinv = ttk.Checkbutton(
            chk_frame, text="SDetalleInv (Detalle Inventario)",
            variable=self.var_sdetalleinv,
            command=self._on_chk_tabla)
        self.chk_sdetalleinv.pack(anchor=tk.W, pady=2)
        self.chk_sinvdep = ttk.Checkbutton(
            chk_frame, text="Existencia Actual",
            variable=self.var_sinvdep,
            command=self._on_chk_existencia)
        self.chk_sinvdep.pack(anchor=tk.W, pady=2)

        self.lbl_estado_conexion = ttk.Label(frame, text="", font=("Segoe UI", 9, "bold"), wraplength=560, justify=tk.CENTER)
        self.lbl_estado_conexion.grid(row=6, column=0, columnspan=3, pady=10)

        self.progress = ttk.Progressbar(frame, orient="horizontal", length=560, mode="determinate")
        self.progress.grid(row=7, column=0, columnspan=3, pady=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=8, column=0, columnspan=3, pady=15)
        self.btn_importar = ttk.Button(btn_frame, text="Importar", command=self._iniciar_importacion)
        self.btn_importar.pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cerrar", command=self.destroy).pack(side=tk.LEFT, padx=10)

    def _cargar_unidades_operativas(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # cursor.execute("SELECT uo_id, uo_Codigo, uo_nombre FROM ark_unds_operativas WHERE uo_active = 1 ORDER BY uo_Codigo")
            cursor.execute(
                "SELECT uo_id, uo_Codigo, uo_nombre, "
                "uo_dsn_name FROM ark_unds_operativas "
                "WHERE uo_active = 1 "
                "ORDER BY uo_Codigo")
            rows = cursor.fetchall()
            conn.close()
            
            # self.uo_data = {row[0]: {"codigo": row[1], "nombre": row[2], "display": f"{row[1]} - {row[2]}"} for row in rows}
            self.uo_data = {
                row[0]: {
                    "codigo": row[1],
                    "nombre": row[2],
                    "dsn": row[3],
                    "display": f"{row[1]} - {row[2]}"}
                for row in rows}
            
            self.cmb_uo['values'] = [data["display"] for data in self.uo_data.values()]
            if self.uo_data:
                self.cmb_uo.current(0)
                self._cargar_depositos(list(self.uo_data.keys())[0])
                
                hoy = datetime.now()
                primer_dia = hoy.replace(day=1)
                self.entry_fecha_desde.insert(0, primer_dia.strftime("%d/%m/%Y"))
                self.entry_fecha_hasta.insert(0, hoy.strftime("%d/%m/%Y"))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las UO: {e}")

    def _cargar_depositos(self, uo_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT dep_IDauto, dep_codigo, dep_descripcion FROM ark_depositos WHERE dep_uo_origen = ? ORDER BY dep_codigo", (uo_id,))
            rows = cursor.fetchall()
            conn.close()

            self.deposito_data = {0: "Todos los depósitos"}
            for row in rows:
                self.deposito_data[row[0]] = f"{row[1]} - {row[2]}"

            self.cmb_deposito["values"] = list(self.deposito_data.values())
            self.cmb_deposito.current(0)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los depósitos: {e}")

    def _on_uo_change(self, event):
        uo_display = self.cmb_uo.get()
        if uo_display:
            # uo_id = next((k for k, v in self.uo_data.items() if v == uo_display), None)
            uo_id = next(
                (k for k, v in self.uo_data.items()
                 if v["display"] == uo_display), None)
            if uo_id:
                self._cargar_depositos(uo_id)
                self._verificar_estado_conexion()
                
    def _on_chk_existencia(self):
        if self.var_sinvdep.get():
            self.var_soperacioninv.set(False)
            self.var_sdetalleventa.set(False)
            self.var_sdetallecomp.set(False)
            self.var_sdetalleinv.set(False)
            for chk in (self.chk_soperacioninv,
                        self.chk_sdetalleventa,
                        self.chk_sdetallecomp,
                        self.chk_sdetalleinv):
                chk.config(state=tk.DISABLED)
            self.entry_fecha_desde.config(state=tk.DISABLED)
            self.entry_fecha_hasta.config(state=tk.DISABLED)
            self.cmb_deposito.config(state=tk.DISABLED)
            self.cmb_status.config(state=tk.DISABLED)
        else:
            for chk in (self.chk_soperacioninv,
                        self.chk_sdetalleventa,
                        self.chk_sdetallecomp,
                        self.chk_sdetalleinv):
                chk.config(state=tk.NORMAL)
            self.entry_fecha_desde.config(state=tk.NORMAL)
            self.entry_fecha_hasta.config(state=tk.NORMAL)
            self.cmb_deposito.config(state="readonly")
            self.cmb_status.config(state="readonly")

    def _on_chk_tabla(self):
        alguna = (self.var_soperacioninv.get()
                  or self.var_sdetalleventa.get()
                  or self.var_sdetallecomp.get()
                  or self.var_sdetalleinv.get())
        if alguna:
            self.var_sinvdep.set(False)
            self.chk_sinvdep.config(state=tk.DISABLED)
        else:
            self.chk_sinvdep.config(state=tk.NORMAL)
        
    def _aplicar_mascara_fecha(self, event):
        entry = event.widget
        valor = entry.get()
        
        solo_numeros = ''.join(c for c in valor if c.isdigit())
        
        if len(solo_numeros) > 8:
            solo_numeros = solo_numeros[:8]
        
        formateado = ""
        if len(solo_numeros) >= 1:
            formateado = solo_numeros[:2]
        if len(solo_numeros) >= 3:
            formateado += "/" + solo_numeros[2:4]
        if len(solo_numeros) >= 5:
            formateado += "/" + solo_numeros[4:8]
        
        entry.delete(0, tk.END)
        entry.insert(0, formateado)
        
        entry.icursor(len(formateado))
        
    def _verificar_estado_conexion(self):
        uo_display = self.cmb_uo.get()
        if not uo_display:
            self.lbl_estado_conexion.config(
                text="Seleccione una Unidad Operativa.",
                foreground="red")
            self.btn_importar.config(state=tk.DISABLED)
            return
        uo = next(
            (d for d in self.uo_data.values()
             if d["display"] == uo_display), None)
        if not uo:
            self.lbl_estado_conexion.config(
                text="Unidad Operativa no válida.",
                foreground="red")
            self.btn_importar.config(state=tk.DISABLED)
            return
        activa = self.manager.get_active_connection()
        if not activa:
            self.lbl_estado_conexion.config(
                text="No hay conexión activa. "
                     "Actívela desde "
                     "Configuración → Conexiones ODBC.",
                foreground="red")
            self.btn_importar.config(state=tk.DISABLED)
            return
        dsn_activa = str(activa.get('dsn', '')).strip()
        dsn_uo = str(uo["dsn"]).strip()
        if dsn_activa == dsn_uo:
            self.lbl_estado_conexion.config(
                text=f"Conexión activa correcta para "
                     f"la UO {uo['codigo']}: {dsn_activa}",
                foreground="green")
            self.btn_importar.config(state=tk.NORMAL)
        else:
            self.lbl_estado_conexion.config(
                text=f"La conexión activa es {dsn_activa}. "
                     f"Para importar la UO {uo['codigo']} "
                     f"active {dsn_uo} desde "
                     f"Configuración → Conexiones ODBC.",
                foreground="red")
            self.btn_importar.config(state=tk.DISABLED)

    def _iniciar_importacion(self):
        if not self.cmb_uo.get():
            messagebox.showwarning("Advertencia", "Debe seleccionar una Unidad Operativa.")
            return

        try:
            fecha_desde = datetime.strptime(self.entry_fecha_desde.get(), "%d/%m/%Y")
            fecha_hasta = datetime.strptime(self.entry_fecha_hasta.get(), "%d/%m/%Y")
            if fecha_desde > fecha_hasta:
                messagebox.showwarning("Advertencia", "La fecha 'Desde' no puede ser mayor que 'Hasta'")
                return
        except ValueError:
            messagebox.showwarning("Advertencia", "Formato de fecha inválido. Use DD/MM/AAAA")
            return

        tablas = []
        if self.var_soperacioninv.get(): tablas.append("SOperacionInv")
        if self.var_sdetalleventa.get(): tablas.append("SDetalleVenta")
        if self.var_sdetallecomp.get(): tablas.append("SDetalleCompra")
        if self.var_sdetalleinv.get(): tablas.append("SDetalleInv")
        if self.var_sinvdep.get(): tablas.append("SinvDep")

        if not tablas:
            messagebox.showwarning("Advertencia", "Debe seleccionar al menos una tabla para importar")
            return

        uo_display = self.cmb_uo.get()
        uo_id, uo_codigo, uo_nombre = next((uid, d["codigo"], d["nombre"]) for uid, d in self.uo_data.items() if d["display"] == uo_display)
        
        deposito_display = self.cmb_deposito.get()
        deposito_id = next((k for k, v in self.deposito_data.items() if v == deposito_display), 0)

        status_map = {"Todos": None, "Procesada (1)": 1, "Tránsito (4)": 4, }
        status_valor = status_map.get(self.cmb_status.get())

        self.btn_importar.config(state=tk.DISABLED)
        self.progress['value'] = 0
        
        thread = threading.Thread(target=self._ejecutar_importacion, args=(uo_id, uo_codigo, uo_nombre, fecha_desde, fecha_hasta, deposito_id, status_valor, tablas), daemon=True)
        thread.start()

    def _ejecutar_importacion(self, uo_id, uo_codigo, uo_nombre, fecha_desde, fecha_hasta, deposito_id, status_valor, tablas):
        try:
            from core.importar_transacciones import importar_transacciones
            conn_info = self.manager.get_active_connection()
            if not conn_info:
                raise RuntimeError(
                    "No hay conexión activa. "
                    "Actívela desde Configuración → Conexiones ODBC.")
            uo = self.uo_data.get(uo_id)
            dsn_uo = str(uo["dsn"]).strip() if uo else ""
            dsn_activa = str(conn_info.get('dsn', '')).strip()
            if dsn_activa != dsn_uo:
                raise RuntimeError(
                    f"La conexión activa es {dsn_activa}. "
                    f"Para importar la UO {uo_codigo} "
                    f"active {dsn_uo} desde "
                    f"Configuración → Conexiones ODBC.")
            
            # Callback para actualizar progreso
            def callback_progreso(porcentaje, mensaje=""):
                self.after(0, self._actualizar_progreso, porcentaje, mensaje)
            
            resultado = importar_transacciones(
                uo_id, uo_codigo, uo_nombre,
                fecha_desde.strftime("%Y-%m-%d"), fecha_hasta.strftime("%Y-%m-%d"),
                deposito_id, status_valor, tablas,
                conn_info['dsn'], conn_info['usuario'], conn_info['password'],
                callback_progreso
            )
            
            self.after(0, self._finalizar_importacion, True, resultado)
        # except Exception as e:
        #    self.after(0, self._finalizar_importacion, False, str(e))
        except Exception as e:
            error_msg = str(e)
            if "UNIQUE constraint failed" in error_msg:
                error_msg = (
                    "Se encontraron registros duplicados.\n"
                    "La operación será detenida.\n"
                    "Revise que el período no haya sido importado previamente.\n\n"
                    f"Detalle: {e}"
                )
            self.after(0, self._finalizar_importacion, False, error_msg)

    def _finalizar_importacion(self, exito, mensaje):
        self.btn_importar.config(state=tk.NORMAL)
        self.progress['value'] = 100 if exito else 0
        if exito:
            messagebox.showinfo("Éxito", mensaje)
        else:
            messagebox.showerror("Error", f"Falló la importación: {mensaje}")
    
    def _actualizar_progreso(self, porcentaje, mensaje=""):
        self.progress['value'] = porcentaje
        if mensaje:
            self.lbl_estado_conexion.config(text=mensaje, foreground="blue")
            self.update_idletasks()
    