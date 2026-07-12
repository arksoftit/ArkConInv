import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.embedded_db import get_db_connection
from core.system_info import get_current_user, get_machine_name
from core.utils import formato_monto, formato_cantidad

class DialogPreliminar(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Procesamiento Preliminar de Existencias")
        self.geometry("650x450")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (650 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (450 // 2)
        self.geometry(f"+{x}+{y}")
        
        self.uo_data = {}
        self.deposito_data = {}
        self._create_widgets()
        self._cargar_datos_iniciales()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        info_lbl = ttk.Label(
            frame, 
            text="Este proceso calculará preliminarmente los saldos de inventario.\n"
                 "Aplica la regla: Costo de Entradas > Costo Histórico de Ventas.",
            font=("Segoe UI", 9, "italic"), foreground="#2874A6", justify=tk.LEFT
        )
        info_lbl.grid(row=0, column=0, columnspan=3, pady=(0, 15), sticky=tk.W)
        
        ttk.Label(frame, text="Unidad Operativa:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.cmb_uo = ttk.Combobox(frame, state="readonly", width=50)
        self.cmb_uo.grid(row=1, column=1, columnspan=2, pady=5, padx=10)
        
        ttk.Label(frame, text="Rango de Fechas:", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky=tk.W, pady=10)
        fecha_frame = ttk.Frame(frame)
        fecha_frame.grid(row=2, column=1, columnspan=2, pady=5, padx=10, sticky=tk.W)
        
        ttk.Label(fecha_frame, text="Desde:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fecha_desde = ttk.Entry(fecha_frame, width=12)
        self.entry_fecha_desde.pack(side=tk.LEFT, padx=(0, 10))
        self.entry_fecha_desde.bind("<KeyRelease>", self._aplicar_mascara_fecha)
        
        ttk.Label(fecha_frame, text="Hasta:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fecha_hasta = ttk.Entry(fecha_frame, width=12)
        self.entry_fecha_hasta.pack(side=tk.LEFT, padx=(0, 10))
        self.entry_fecha_hasta.bind("<KeyRelease>", self._aplicar_mascara_fecha)
        
        ttk.Label(frame, text="Depósito:", font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.cmb_deposito = ttk.Combobox(frame, state="readonly", width=50)
        self.cmb_deposito.grid(row=3, column=1, columnspan=2, pady=5, padx=10)
        
        self.progress_lbl = ttk.Label(frame, text="", font=("Segoe UI", 9))
        self.progress_lbl.grid(row=4, column=0, columnspan=3, pady=(20, 5), sticky=tk.W)
        self.progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="determinate", length=550)
        self.progress_bar.grid(row=5, column=0, columnspan=3, pady=5, sticky=tk.W)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=3, pady=25)
        ttk.Button(btn_frame, text="Procesar Existencias", command=self._procesar_preliminar).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cerrar", command=self.destroy).pack(side=tk.LEFT, padx=10)

    def _cargar_datos_iniciales(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            self.uo_data = {"0": "Todas las UO"}
            cursor.execute("SELECT uo_id, uo_Codigo, uo_nombre FROM ark_unds_operativas WHERE uo_active = 1 ORDER BY uo_Codigo")
            for row in cursor.fetchall():
                self.uo_data[str(row[0])] = f"{row[1]} - {row[2]}"
            self.cmb_uo['values'] = list(self.uo_data.values())
            self.cmb_uo.current(0)
            
            self.deposito_data = {"0": "Todos los depósitos"}
            cursor.execute("SELECT dep_IDauto, dep_codigo, dep_descripcion FROM ark_depositos ORDER BY dep_codigo")
            for row in cursor.fetchall():
                self.deposito_data[str(row[0])] = f"{row[1]} - {row[2]}"
            self.cmb_deposito['values'] = list(self.deposito_data.values())
            self.cmb_deposito.current(0)
            
            hoy = datetime.now()
            self.entry_fecha_desde.insert(0, hoy.replace(day=1).strftime("%d/%m/%Y"))
            self.entry_fecha_hasta.insert(0, hoy.strftime("%d/%m/%Y"))
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los datos iniciales: {e}")

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

    def _procesar_preliminar(self):
        try:
            uo_display = self.cmb_uo.get()
            uo_id = next((k for k, v in self.uo_data.items() if v == uo_display), "0")
            uo_codigo_filtro = uo_display.split(" - ")[0] if uo_id != "0" else None
            
            fecha_desde = self.entry_fecha_desde.get().strip()
            fecha_hasta = self.entry_fecha_hasta.get().strip()
            
            if not fecha_desde or not fecha_hasta:
                messagebox.showwarning("Advertencia", "Debe ingresar un rango de fechas.")
                return
                
            try:
                fecha_desde_sql = datetime.strptime(fecha_desde, "%d/%m/%Y").strftime("%Y-%m-%d")
                fecha_hasta_sql = datetime.strptime(fecha_hasta, "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("Advertencia", "Formato de fecha inválido. Use DD/MM/AAAA")
                return

            deposito_display = self.cmb_deposito.get()
            deposito_id = next((k for k, v in self.deposito_data.items() if v == deposito_display), "0")
            dep_codigo_filtro = deposito_display.split(" - ")[0] if deposito_id != "0" else None

            self.config(cursor="watch")
            self.progress_lbl.config(text="Analizando movimientos de costo y cantidad...")
            self.progress_bar['value'] = 10
            self.update()

            conn = get_db_connection()
            cursor = conn.cursor()
            
            tipos_entrada_costo = [2, 4, 6, 8]
            tipos_salida = [3, 11, 13]
            tipos_devolucion_entrada = [12]
            tipos_traslado = [1] 

            query_costos_entradas = """
            SELECT dtc_codigo, dtc_depositosource, dtc_uo_Codigo, SUM(dtc_cantidad) as cant, SUM(dtc_cantidad * dtc_costo) as val
            FROM ark_detalletrancomp 
            WHERE dtc_tipooperacion IN (?, ?, ?, ?) AND dtc_fechaoperacion BETWEEN ? AND ?
            GROUP BY dtc_codigo, dtc_depositosource, dtc_uo_Codigo
            
            UNION ALL
            
            SELECT dti_codigo, dti_depositosource, dti_uo_Codigo, SUM(dti_cantidad) as cant, SUM(dti_cantidad * dti_costo) as val
            FROM ark_detalletraninv 
            WHERE dti_tipooperacion IN (?, ?) AND dti_fechaoperacion BETWEEN ? AND ? AND dti_cantidad > 0
            GROUP BY dti_codigo, dti_depositosource, dti_uo_Codigo
            """
            
            cursor.execute(query_costos_entradas, (2, 4, 6, 8, fecha_desde_sql, fecha_hasta_sql, 2, 4, fecha_desde_sql, fecha_hasta_sql))
            costos_entradas = cursor.fetchall()

            query_costos_ventas = """
            SELECT dtv_codigo, dtv_depositosource, dtv_uo_Codigo, AVG(dtv_costo) as costo_prom
            FROM ark_detalletranvtas 
            WHERE dtv_tipooperacion IN (?) AND dtv_fechaoperacion BETWEEN ? AND ? AND dtv_costo > 0
            GROUP BY dtv_codigo, dtv_depositosource, dtv_uo_Codigo
            """
            cursor.execute(query_costos_ventas, (11, fecha_desde_sql, fecha_hasta_sql))
            costos_historicos_ventas = { (row[0], row[1], row[2]): row[3] for row in cursor.fetchall() }

            mapa_costos_unitarios = {}
            
            for row in costos_entradas:
                codigo, dep, uo, cant, val = row
                clave = (uo, dep, codigo)
                if cant and cant > 0:
                    mapa_costos_unitarios[clave] = abs(val / cant)

            for clave, costo_venta in costos_historicos_ventas.items():
                if clave not in mapa_costos_unitarios and costo_venta > 0:
                    mapa_costos_unitarios[clave] = costo_venta

            query_cantidades = """
            SELECT dtv_codigo, dtv_tipooperacion, dtv_cantidad, dtv_uo_Codigo, dtv_depositosource, dtv_depositotarget
            FROM ark_detalletranvtas WHERE dtv_fechaoperacion BETWEEN ? AND ?
            UNION ALL
            SELECT dtc_codigo, dtc_tipooperacion, dtc_cantidad, dtc_uo_Codigo, dtc_depositosource, dtc_depositotarget
            FROM ark_detalletrancomp WHERE dtc_fechaoperacion BETWEEN ? AND ?
            UNION ALL
            SELECT dti_codigo, dti_tipooperacion, dti_cantidad, dti_uo_Codigo, dti_depositosource, dti_depositotarget
            FROM ark_detalletraninv WHERE dti_fechaoperacion BETWEEN ? AND ?
            """
            cursor.execute(query_cantidades, (fecha_desde_sql, fecha_hasta_sql, fecha_desde_sql, fecha_hasta_sql, fecha_desde_sql, fecha_hasta_sql))
            rows_movimientos = cursor.fetchall()

            balance_existencias = {}
            total_rows = len(rows_movimientos)
            
            for i, row in enumerate(rows_movimientos):
                if i % 100 == 0:
                    porcentaje = 10 + int((i / total_rows) * 60)
                    self.progress_bar['value'] = porcentaje
                    self.progress_lbl.config(text=f"Procesando movimientos: {i}/{total_rows}")
                    self.update()

                item_cod, tipo, cant, uo, dep_origen, dep_destino = row
                cant = float(cant) if cant else 0.0
                
                if uo_codigo_filtro and uo != uo_codigo_filtro: continue
                if dep_codigo_filtro and dep_origen != dep_codigo_filtro and dep_destino != dep_codigo_filtro: continue

                definitivos = []
                if tipo == 1:
                    if dep_origen and (not dep_codigo_filtro or dep_origen == dep_codigo_filtro):
                        definitivos.append((dep_origen, 'trans_menos', cant))
                    if dep_destino and (not dep_codigo_filtro or dep_destino == dep_codigo_filtro):
                        definitivos.append((dep_destino, 'trans_mas', cant))
                else:
                    dep_afectado = dep_origen
                    if not dep_afectado: continue
                    if dep_codigo_filtro and dep_afectado != dep_codigo_filtro: continue

                    if tipo in [2, 8]: definitivos.append((dep_afectado, 'entradas_valorizadas', cant))
                    elif tipo == 6: definitivos.append((dep_afectado, 'compras', cant))
                    elif tipo == 12: definitivos.append((dep_afectado, 'dev_ventas', cant))
                    elif tipo == 4:
                        if cant > 0: definitivos.append((dep_afectado, 'ajustes_mas', cant))
                        else: definitivos.append((dep_afectado, 'ajustes_menos', abs(cant)))
                    elif tipo in [3, 11, 13]: definitivos.append((dep_afectado, 'salidas', cant))
                    elif tipo == 7: definitivos.append((dep_afectado, 'dev_compras', cant))

                for dep, col, q_val in definitivos:
                    clave = (uo, dep, item_cod)
                    if clave not in balance_existencias:
                        balance_existencias[clave] = {
                            'compras': 0, 'cargos': 0, 'notas_entrega_prov': 0, 'dev_ventas': 0,
                            'ajustes_mas': 0, 'ajustes_menos': 0, 'salidas': 0, 'dev_compras': 0,
                            'trans_mas': 0, 'trans_menos': 0
                        }
                    
                    if col == 'entradas_valorizadas':
                         balance_existencias[clave]['cargos'] += q_val
                    else:
                        balance_existencias[clave][col] += q_val

            usuario = get_current_user()
            maquina = get_machine_name()
            fecha_hoy = datetime.now().strftime("%Y-%m-%d")
            hora_hoy = datetime.now().strftime("%H:%M:%S")
            
            total_registros = len(balance_existencias)
            procesados = 0
            
            for (uo, dep, item), datos in balance_existencias.items():
                entradas = datos['compras'] + datos['cargos'] + datos['notas_entrega_prov'] + datos['dev_ventas'] + datos['ajustes_mas'] + datos['trans_mas']
                salidas = datos['salidas'] + datos['dev_compras'] + datos['ajustes_menos'] + datos['trans_menos']
                
                saldo_final = entradas - salidas
                
                clave_costo = (uo, dep, item)
                costo_unitario = mapa_costos_unitarios.get(clave_costo, 0.0)
                
                valor_saldo = saldo_final * costo_unitario

                cursor.execute("""
                    INSERT OR REPLACE INTO ark_existencia_calculadas (
                        exc_uo_Codigo, exc_dep_codigo, exc_item_codigo, exc_inicial, exc_costos_local, 
                        exc_compras, exc_cargos, exc_nota_entrega_proveedor, exc_dev_ventas, 
                        exc_ajustes_mas, exc_ajustes_menos, exc_transferencias_mas, exc_transferencias_menos,
                        exc_ventas, exc_descargos, exc_nota_entrega_clientes, exc_dev_compras,
                        exc_final, exc_SystemDate, exc_SystemTime, exc_NameMachine, exc_UserCreator
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    uo, dep, item, 0.0, formato_monto(costo_unitario),
                    formato_cantidad(datos['compras']), formato_cantidad(datos['cargos']), 
                    formato_cantidad(datos['notas_entrega_prov']), formato_cantidad(datos['dev_ventas']),
                    formato_cantidad(datos['ajustes_mas']), formato_cantidad(datos['ajustes_menos']),
                    formato_cantidad(datos['trans_mas']), formato_cantidad(datos['trans_menos']),
                    formato_cantidad(datos['salidas']), 0, 0, formato_cantidad(datos['dev_compras']),
                    formato_cantidad(saldo_final), fecha_hoy, hora_hoy, maquina, usuario
                ))
                
                procesados += 1
                if procesados % 50 == 0:
                    porcentaje = 70 + int((procesados / total_registros) * 30)
                    self.progress_bar['value'] = porcentaje
                    self.progress_lbl.config(text=f"Guardando resultados: {procesados}/{total_registros}")
                    self.update()

            conn.commit()
            conn.close()
            self.config(cursor="")
            messagebox.showinfo("Éxito", f"Cálculo preliminar finalizado.\nSe procesaron {total_registros} combinaciones únicas.")
            self.destroy()

        except Exception as e:
            self.config(cursor="")
            messagebox.showerror("Error Crítico", f"Falló el procesamiento:\n{e}")