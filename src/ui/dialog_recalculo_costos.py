import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.embedded_db import get_db_connection
from core.system_info import get_current_user, get_machine_name
from core.utils import formato_monto, formato_cantidad

class DialogRecalculoCostos(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Recálculo de Costos por Periodo")
        self.geometry("550x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (550 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (350 // 2)
        self.geometry(f"+{x}+{y}")
        
        self._create_widgets()
        self._cargar_datos_iniciales()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        info_lbl = ttk.Label(
            frame, 
            text="Este proceso actualizará la tabla ark_costos con el costo unitario fiscal\n"
                 "de cada artículo para el periodo seleccionado.",
            font=("Segoe UI", 9, "italic"), foreground="#2874A6", justify=tk.LEFT
        )
        info_lbl.grid(row=0, column=0, columnspan=3, pady=(0, 15), sticky=tk.W)
        
        ttk.Label(frame, text="Rango de Fechas:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=10)
        fecha_frame = ttk.Frame(frame)
        fecha_frame.grid(row=1, column=1, columnspan=2, pady=5, padx=10, sticky=tk.W)
        
        ttk.Label(fecha_frame, text="Desde:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fecha_desde = ttk.Entry(fecha_frame, width=12)
        self.entry_fecha_desde.pack(side=tk.LEFT, padx=(0, 10))
        self.entry_fecha_desde.bind("<KeyRelease>", self._aplicar_mascara_fecha)
        
        ttk.Label(fecha_frame, text="Hasta:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fecha_hasta = ttk.Entry(fecha_frame, width=12)
        self.entry_fecha_hasta.pack(side=tk.LEFT, padx=(0, 10))
        self.entry_fecha_hasta.bind("<KeyRelease>", self._aplicar_mascara_fecha)
        
        self.progress_lbl = ttk.Label(frame, text="", font=("Segoe UI", 9))
        self.progress_lbl.grid(row=2, column=0, columnspan=3, pady=(20, 5), sticky=tk.W)
        self.progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="determinate", length=450)
        self.progress_bar.grid(row=3, column=0, columnspan=3, pady=5, sticky=tk.W)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=25)
        ttk.Button(btn_frame, text="Actualizar Costos", command=self._actualizar_costos_periodo).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cerrar", command=self.destroy).pack(side=tk.LEFT, padx=10)

    def _cargar_datos_iniciales(self):
        hoy = datetime.now()
        primer_dia_mes = hoy.replace(day=1)
        self.entry_fecha_desde.insert(0, primer_dia_mes.strftime("%d/%m/%Y"))
        self.entry_fecha_hasta.insert(0, hoy.strftime("%d/%m/%Y"))

    def _aplicar_mascara_fecha(self, event):
        entry = event.widget
        valor = entry.get()
        solo_numeros = ''.join(c for c in valor if c.isdigit())
        if len(solo_numeros) > 8: solo_numeros = solo_numeros[:8]
        formateado = ""
        if len(solo_numeros) >= 1: formateado = solo_numeros[:2]
        if len(solo_numeros) >= 3: formateado += "/" + solo_numeros[2:4]
        if len(solo_numeros) >= 5: formateado += "/" + solo_numeros[4:8]
        entry.delete(0, tk.END)
        entry.insert(0, formateado)
        entry.icursor(len(formateado))

    def _actualizar_costos_periodo(self):
        try:
            fecha_desde = self.entry_fecha_desde.get().strip()
            fecha_hasta = self.entry_fecha_hasta.get().strip()
            
            if not fecha_desde or not fecha_hasta:
                messagebox.showwarning("Advertencia", "Debe ingresar un rango de fechas.")
                return
                
            try:
                f_desde = datetime.strptime(fecha_desde, "%d/%m/%Y")
                f_hasta = datetime.strptime(fecha_hasta, "%d/%m/%Y")
                
                if f_desde > f_hasta:
                    messagebox.showerror("Error", "La fecha 'Desde' no puede ser posterior a 'Hasta'.")
                    return
                    
                diferencia_dias = (f_hasta - f_desde).days
                if diferencia_dias < 30:
                    messagebox.showerror("Error", "El periodo mínimo debe ser de 1 mes calendario (30 días).")
                    return
                if diferencia_dias > 365:
                    messagebox.showerror("Error", "El periodo máximo permitido es de 1 año (365 días).")
                    return
                    
                fecha_desde_sql = f_desde.strftime("%Y-%m-%d")
                fecha_hasta_sql = f_hasta.strftime("%Y-%m-%d")
                
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use DD/MM/AAAA.")
                return

            self.config(cursor="watch")
            self.progress_lbl.config(text="Obteniendo costos de compras...")
            self.progress_bar['value'] = 10
            self.update()

            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM ark_costos 
                WHERE cts_periodo_desde = ? AND cts_periodo_hasta = ?
            """, (fecha_desde_sql, fecha_hasta_sql))
            
            query_compras = """
                SELECT dtc_codigo, dtc_costo, dtc_cantidad, dtc_moneda, dtc_factorcambio, dtc_fechaoperacion
                FROM ark_detalletrancomp 
                WHERE dtc_tipooperacion IN (2, 6, 8) 
                  AND dtc_fechaoperacion BETWEEN ? AND ?
                  AND dtc_costo > 0
            """
            cursor.execute(query_compras, (fecha_desde_sql, fecha_hasta_sql))
            compras_data = {}
            for row in cursor.fetchall():
                codigo, costo, cant, moneda, factor, fecha = row
                if codigo not in compras_data or fecha > compras_data[codigo][5]:
                    compras_data[codigo] = (codigo, costo, cant, moneda, factor, fecha)

            self.progress_lbl.config(text="Obteniendo costos de ventas...")
            self.progress_bar['value'] = 30
            self.update()

            query_ventas = """
                SELECT dtv_codigo, dtv_costo, dtv_cantidad, dtv_moneda, dtv_factorcambio, dtv_fechaoperacion
                FROM ark_detalletranvtas 
                WHERE dtv_tipooperacion IN (11, 12, 13) 
                  AND dtv_fechaoperacion BETWEEN ? AND ?
                  AND dtv_costo > 0
            """
            cursor.execute(query_ventas, (fecha_desde_sql, fecha_hasta_sql))
            ventas_data = {}
            for row in cursor.fetchall():
                codigo, costo, cant, moneda, factor, fecha = row
                if codigo not in ventas_data or fecha > ventas_data[codigo][5]:
                    ventas_data[codigo] = (codigo, costo, cant, moneda, factor, fecha)

            self.progress_lbl.config(text="Obteniendo costos de inventario...")
            self.progress_bar['value'] = 50
            self.update()

            query_inventario = """
                SELECT dti_codigo, dti_costooperacion, dti_cantidad, dti_moneda, dti_factorcambio, dti_fechaoperacion
                FROM ark_detalletraninv 
                WHERE dti_tipooperacion IN (2, 3, 4) 
                  AND dti_fechaoperacion BETWEEN ? AND ?
                  AND dti_costooperacion > 0
            """
            cursor.execute(query_inventario, (fecha_desde_sql, fecha_hasta_sql))
            inventario_data = {}
            for row in cursor.fetchall():
                codigo, costo, cant, moneda, factor, fecha = row
                if codigo not in inventario_data or fecha > inventario_data[codigo][5]:
                    inventario_data[codigo] = (codigo, costo, cant, moneda, factor, fecha)

            self.progress_lbl.config(text="Consolidando costos por artículo...")
            self.progress_bar['value'] = 70
            self.update()

            cursor.execute("SELECT inv_codigo FROM ark_inventario WHERE inv_status = 1")
            articulos = [row[0] for row in cursor.fetchall()]
            
            total_articulos = len(articulos)
            procesados = 0
            usuario = get_current_user()
            maquina = get_machine_name()
            fecha_hoy = datetime.now().strftime("%Y-%m-%d")
            hora_hoy = datetime.now().strftime("%H:%M:%S")

            for codigo in articulos:
                dtc_costo = dtc_cant = dtc_moneda = dtc_factor = dtc_fecha = None
                dtv_costo = dtv_cant = dtv_moneda = dtv_factor = dtv_fecha = None
                dti_costo = dti_cant = dti_moneda = dti_factor = dti_fecha = None
                
                if codigo in compras_data:
                    _, dtc_costo, dtc_cant, dtc_moneda, dtc_factor, dtc_fecha = compras_data[codigo]
                if codigo in ventas_data:
                    _, dtv_costo, dtv_cant, dtv_moneda, dtv_factor, dtv_fecha = ventas_data[codigo]
                if codigo in inventario_data:
                    _, dti_costo, dti_cant, dti_moneda, dti_factor, dti_fecha = inventario_data[codigo]
                
                # Determinar costo vigente según jerarquía (solo para referencia, no se usa en INSERT)
                costo_vigente = dtc_costo if dtc_costo else (dtv_costo if dtv_costo else (dti_costo if dti_costo else 0))
                fecha_ultima = dtc_fecha if dtc_fecha else (dtv_fecha if dtv_fecha else (dti_fecha if dti_fecha else None))
                
                cursor.execute("""
                    INSERT INTO ark_costos 
                    (cts_codigo, cts_periodo_desde, cts_periodo_hasta,
                    cts_dtv_costo, cts_dtc_costo, cts_dti_costo,
                    cts_dtv_cantidad, cts_dtc_cantidad, cts_dti_cantidad,
                    cts_dtv_moneda, cts_dtv_factorcambio, 
                    cts_dtc_moneda, cts_dtc_factorcambio,
                    cts_dti_moneda, cts_dti_factorcambio, 
                    cts_fecha_ultima_operacion,
                    cts_SystemDate, cts_SystemTime, cts_NameMachine, cts_UserCreator)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    codigo, fecha_desde_sql, fecha_hasta_sql,
                    formato_monto(dtv_costo or 0), formato_monto(dtc_costo or 0), formato_monto(dti_costo or 0),
                    formato_cantidad(dtv_cant or 0), formato_cantidad(dtc_cant or 0), formato_cantidad(dti_cant or 0),
                    dtv_moneda or 1, dtv_factor or 1.0,
                    dtc_moneda or 1, dtc_factor or 1.0,
                    dti_moneda or 1, dti_factor or 1.0,
                    fecha_ultima,
                    fecha_hoy, hora_hoy, maquina, usuario
                ))
                
                procesados += 1
                if procesados % 50 == 0:
                    porcentaje = 70 + int((procesados / total_articulos) * 30)
                    self.progress_bar['value'] = porcentaje
                    self.progress_lbl.config(text=f"Procesando: {procesados}/{total_articulos} artículos...")
                    self.update()

            conn.commit()
            conn.close()
            self.config(cursor="")
            messagebox.showinfo("Éxito", f"Costos actualizados para el periodo {fecha_desde} a {fecha_hasta}.\nArtículos procesados: {total_articulos}")
            self.destroy()

        except Exception as e:
            self.config(cursor="")
            self.progress_bar['value'] = 0
            self.progress_lbl.config(text="")
            messagebox.showerror("Error Crítico", f"Falló el proceso de recálculo:\n{e}")