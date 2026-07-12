# ArkConInv - Diálogo de Procesamiento Preliminar de Existencias
# Desarrollado por Juan E. Páez M. (JUEPAE) - Julio 2026
# version (100720261.2043beta)
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.embedded_db import get_db_connection
from core.system_info import get_current_user, get_machine_name


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
            text="Este proceso calculará preliminarmente los saldos de inventario basándose en las transacciones\n"
                 "procesadas e importadas, volcando los resultados en la tabla de existencias calculadas.",
            font=("Segoe UI", 9, "italic"), foreground="#2874A6", justify=tk.LEFT
        )
        info_lbl.grid(row=0, column=0, columnspan=3, pady=(0, 15), sticky=tk.W)

        # Selección de Unidad Operativa
        ttk.Label(frame, text="Unidad Operativa:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.cmb_uo = ttk.Combobox(frame, state="readonly", width=50)
        self.cmb_uo.grid(row=1, column=1, columnspan=2, pady=5, padx=10)

        # Rango de Fechas
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

        # Depósito
        ttk.Label(frame, text="Depósito:", font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.cmb_deposito = ttk.Combobox(frame, state="readonly", width=50)
        self.cmb_deposito.grid(row=3, column=1, columnspan=2, pady=5, padx=10)

        # Barra de progreso usando 'length' para corregir TclError
        self.progress_lbl = ttk.Label(frame, text="", font=("Segoe UI", 9))
        self.progress_lbl.grid(row=4, column=0, columnspan=3, pady=(20, 5), sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="determinate", length=550)
        self.progress_bar.grid(row=5, column=0, columnspan=3, pady=5, sticky=tk.W)

        # Botones
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

            conn.close()

            hoy = datetime.now()
            self.entry_fecha_desde.insert(0, hoy.replace(day=1).strftime("%d/%m/%Y"))
            self.entry_fecha_hasta.insert(0, hoy.strftime("%d/%m/%Y"))

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
            self.progress_lbl.config(text="Consolidando detalles de transacciones (UNION ALL)...")
            self.progress_bar['value'] = 10
            self.update()

            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Universo total de IDs válidos según tus exclusiones de importación
            tipos_validos = [1, 2, 3, 4, 6, 7, 8, 11, 12, 13]
            placeholders = ','.join(['?'] * len(tipos_validos))

            # REPLICACIÓN DE LA LÓGICA DE DETALLES UNIFICADOS (Idéntica al Reporte)
            query = f"""
            WITH movimientos AS (
                SELECT dtv_codigo as codigo, dtv_tipooperacion as tipooperacion, dtv_costo as costo, dtv_cantidad as cantidad, dtv_uo_Codigo as uo_codigo, dtv_depositosource as deposito, NULL as deposito_destino, dtv_moneda as moneda, dtv_factorcambio as factorcambio
                FROM ark_detalletranvtas WHERE dtv_tipooperacion IN ({placeholders}) AND dtv_fechaoperacion BETWEEN ? AND ?
                UNION ALL
                SELECT dtc_codigo as codigo, dtc_tipooperacion as tipooperacion, dtc_costo as costo, dtc_cantidad as cantidad, dtc_uo_Codigo as uo_codigo, dtc_depositosource as deposito, NULL as deposito_destino, dtc_moneda as moneda, dtc_factorcambio as factorcambio
                FROM ark_detalletrancomp WHERE dtc_tipooperacion IN ({placeholders}) AND dtc_fechaoperacion BETWEEN ? AND ?
                UNION ALL
                SELECT dti_codigo as codigo, dti_tipooperacion as tipooperacion, dti_cantidad as cantidad, dti_costo as costo, dti_uo_Codigo as uo_codigo, dti_depositosource as deposito, dti_depositotarget as deposito_destino, dti_moneda as moneda, dti_factorcambio as factorcambio
                FROM ark_detalletraninv WHERE dti_tipooperacion IN ({placeholders}) AND dti_fechaoperacion BETWEEN ? AND ?
            )
            SELECT codigo, tipooperacion, costo, cantidad, uo_codigo, deposito, deposito_destino, moneda, factorcambio
            FROM movimientos WHERE 1=1
            """
            
            # Armamos los parámetros duplicados para los 3 bloques del UNION
            params = (tipos_validos + [fecha_desde_sql, fecha_hasta_sql] + 
                      tipos_validos + [fecha_desde_sql, fecha_hasta_sql] + 
                      tipos_validos + [fecha_desde_sql, fecha_hasta_sql])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            if not rows:
                self.config(cursor="")
                self.progress_bar['value'] = 0
                self.progress_lbl.config(text="")
                messagebox.showinfo("Información", "No se encontraron movimientos detallados para los filtros seleccionados.")
                conn.close()
                return

            # Consolidación estructurada en memoria agrupada por (UO, Depósito, Ítem)
            balance_existencias = {}

            for row in rows:
                # item_cod, tipo, cant, uo, dep_origen, dep_destino = rowx
                item_cod, tipo, costo, cant, uo, dep_origen, dep_destino, moneda, factorcambio = row
                cant = float(cant) if cant else 0.0

                # Aplicar filtros dinámicos de la UI si se seleccionó una UO específica
                if uo_codigo_filtro and uo != uo_codigo_filtro:
                    continue

                # Manejo de los flujos de inventario por Depósito
                definitivos = []
                if tipo == 1:  # Traslado / Transferencia
                    # Resta en origen
                    if not dep_codigo_filtro or dep_origen == dep_codigo_filtro:
                        if dep_origen: definitivos.append((dep_origen, 'trans_menos', cant))
                    # Suma en destino
                    if not dep_codigo_filtro or dep_destino == dep_codigo_filtro:
                        if dep_destino: definitivos.append((dep_destino, 'trans_mas', cant))
                else:
                    # Documentos regulares (afectan al depósito origen indicado en la transacción)
                    if not dep_codigo_filtro or dep_origen == dep_codigo_filtro:
                        if dep_origen:
                            if tipo == 2: definitivos.append((dep_origen, 'cargos', cant))
                            elif tipo == 3: definitivos.append((dep_origen, 'descargos', cant))
                            elif tipo == 4:
                                label = 'ajustes_mas' if cant >= 0 else 'ajustes_menos'
                                definitivos.append((dep_origen, label, abs(cant)))
                            elif tipo == 6: definitivos.append((dep_origen, 'compras', cant))
                            elif tipo == 7: definitivos.append((dep_origen, 'dev_compras', cant))
                            elif tipo == 8: definitivos.append((dep_origen, 'notas_entrega_prov', cant))
                            elif tipo == 11: definitivos.append((dep_origen, 'ventas', cant))
                            elif tipo == 12: definitivos.append((dep_origen, 'dev_ventas', cant))
                            elif tipo == 13: definitivos.append((dep_origen, 'notas_entrega_cli', cant))

                # Volcar al diccionario consolidado
                for dep_afectado, columna, q_val in definitivos:
                    clave = (uo, dep_afectado, item_cod)
                    if clave not in balance_existencias:
                        balance_existencias[clave] = {
                        'cargos': 0.0, 'descargos': 0.0, 'trans_mas': 0.0, 'trans_menos': 0.0,
                        'compras': 0.0, 'notas_entrega_prov': 0.0, 'dev_ventas': 0.0, 'dev_compras': 0.0,
                        'ventas': 0.0, 'notas_entrega_cli': 0.0, 'ajustes_mas': 0.0, 'ajustes_menos': 0.0,
                        'total_cantidad': 0.0, 'costo_local_acumulado': 0.0, 'factor_ref_acumulado': 0.0, 
                        'costo_ref_acumulado': 0.0 
                        }
                    balance_existencias[clave][columna] += q_val
                    
                    # Convertir costo, moneda, factorcambio locales si no se hicieron antes
                    costo = float(costo) if costo else 0.0
                    moneda = int(moneda) if moneda else 1 # Asumir moneda local por defecto
                    factorcambio = float(factorcambio) if factorcambio else 1.0 # Factor neutro por defecto
                    # Calcular costo referencial para este movimiento
                    costo_ref = costo * factorcambio if moneda == 2 else costo
                    # Acumular cantidad total para cálculo de promedios ponderados
                    balance_existencias[clave]['total_cantidad'] += abs(q_val) # Usamos valor absoluto para ponderación
                    # Acumular costos y factores ponderados (por cantidad)
                    balance_existencias[clave]['costo_local_acumulado'] += abs(q_val) * costo
                    balance_existencias[clave]['factor_ref_acumulado'] += abs(q_val) * factorcambio
                    balance_existencias[clave]['costo_ref_acumulado'] += abs(q_val) * costo_ref

            # Volcado masivo a la tabla física ark_existencia_calculadas
            usuario = get_current_user()
            maquina = get_machine_name()
            fecha_hoy = datetime.now().strftime("%Y-%m-%d")
            hora_hoy = datetime.now().strftime("%H:%M:%S")

            total_registros = len(balance_existencias)
            procesados = 0

            for (uo, dep, item), datos in balance_existencias.items():
                # Calcular promedios ponderados de costos y factores
                total_cant = datos['total_cantidad']
                costo_local_prom = (datos['costo_local_acumulado'] / total_cant) if total_cant > 0 else 0.0
                factor_ref_prom = (datos['factor_ref_acumulado'] / total_cant) if total_cant > 0 else 0.0
                costo_ref_prom = (datos['costo_ref_acumulado'] / total_cant) if total_cant > 0 else 0.0
                inicial = 0.0
                saldo_final = (inicial + datos['cargos'] + datos['trans_mas'] + datos['compras'] + 
                               datos['notas_entrega_prov'] + datos['dev_ventas'] + datos['ajustes_mas'] - 
                               datos['descargos'] - datos['trans_menos'] - datos['ventas'] - 
                               datos['notas_entrega_cli'] - datos['dev_compras'] - datos['ajustes_menos'])

                cursor.execute("""
                    INSERT OR REPLACE INTO ark_existencia_calculadas (
                        exc_uo_Codigo, exc_dep_codigo, exc_item_codigo, exc_inicial, exc_costos_local, exc_costos_referencial, exc_factor_referencial,
                        exc_transferencias_mas, exc_cargos, exc_ajustes_mas, exc_compras,
                        exc_nota_entrega_proveedor, exc_dev_ventas, exc_descargos, exc_dev_compras,
                        exc_ventas, exc_nota_entrega_clientes, exc_transferencias_menos, exc_ajustes_menos,
                        exc_final, exc_SystemDate, exc_SystemTime, exc_NameMachine, exc_UserCreator
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    uo, dep, item, inicial, costo_local_prom, costo_ref_prom, factor_ref_prom,
                    datos['trans_mas'], datos['cargos'], datos['ajustes_mas'], datos['compras'],
                    datos['notas_entrega_prov'], datos['dev_ventas'], datos['descargos'], datos['dev_compras'],
                    datos['ventas'], datos['notas_entrega_cli'], datos['trans_menos'], datos['ajustes_menos'],
                    saldo_final, fecha_hoy, hora_hoy, maquina, usuario # <--- saldo_final en la posición correcta
                ))

                procesados += 1
                if procesados % 50 == 0 or procesados == total_registros:
                    porcentaje = int((procesados / total_registros) * 80) + 20
                    self.progress_bar['value'] = porcentaje
                    self.progress_lbl.config(text=f"Guardando en BD: {procesados}/{total_registros} registros...")
                    self.update()

            conn.commit()
            conn.close()

            self.config(cursor="")
            messagebox.showinfo("Éxito", f"Cálculo preliminar finalizado.\nSe procesaron con éxito {total_registros} registros.")
            self.destroy()

        except Exception as e:
            self.config(cursor="")
            self.progress_bar['value'] = 0
            self.progress_lbl.config(text="")
            messagebox.showerror("Error", f"Ocurrió un error en la consolidación de datos:\n{e}")