import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from datetime import datetime, date
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.embedded_db import get_db_connection
from core.system_info import get_current_user, get_machine_name

class DialogPeriodos(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Generación de Períodos Fiscales")
        self.geometry("860x520")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (860 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (520 // 2)
        self.geometry(f"+{x}+{y}")
        self._periodos_incluidos = []
        self._dia_ini = None
        self._mes_ini = None
        self._dia_fin = None
        self._mes_fin = None
        self._create_widgets()
        self._cargar_configuracion_fiscal()
        self._cargar_periodos_existentes()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        config_frame = ttk.LabelFrame(main_frame, text="Configuración Fiscal de la Empresa", padding=10)
        config_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(config_frame, text="Día Inicio Fiscal:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.lbl_dia_ini = ttk.Label(config_frame, text="--", font=("Segoe UI", 10))
        self.lbl_dia_ini.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(config_frame, text="Mes Inicio Fiscal:", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.lbl_mes_ini = ttk.Label(config_frame, text="--", font=("Segoe UI", 10))
        self.lbl_mes_ini.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        ttk.Label(config_frame, text="Día Fin Fiscal:", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.lbl_dia_fin = ttk.Label(config_frame, text="--", font=("Segoe UI", 10))
        self.lbl_dia_fin.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(config_frame, text="Mes Fin Fiscal:", font=("Segoe UI", 9, "bold")).grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.lbl_mes_fin = ttk.Label(config_frame, text="--", font=("Segoe UI", 10))
        self.lbl_mes_fin.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)

        filtro_frame = ttk.LabelFrame(main_frame, text="Selección de Año Fiscal", padding=10)
        filtro_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(filtro_frame, text="Año Fiscal:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.cmb_anio = ttk.Combobox(filtro_frame, state="readonly", width=12, font=("Segoe UI", 10))
        self.cmb_anio.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(filtro_frame, text="InvDeclarado Inicial:", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, padx=(15, 5), pady=5, sticky=tk.W)
        self.ent_inv_ini = ttk.Entry(filtro_frame, width=16, font=("Segoe UI", 10))
        self.ent_inv_ini.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        self.ent_inv_ini.insert(0, "0,00")
        self.ent_inv_ini.config(state=tk.DISABLED)

        ttk.Label(filtro_frame, text="InvDeclarado Final:", font=("Segoe UI", 9, "bold")).grid(row=0, column=4, padx=(15, 5), pady=5, sticky=tk.W)
        self.ent_inv_fin = ttk.Entry(filtro_frame, width=16, font=("Segoe UI", 10))
        self.ent_inv_fin.grid(row=0, column=5, padx=5, pady=5, sticky=tk.W)
        self.ent_inv_fin.insert(0, "0,00")
        self.ent_inv_fin.config(state=tk.DISABLED)

        self.ent_inv_ini.bind("<FocusOut>", self._on_monto_editado)
        self.ent_inv_fin.bind("<FocusOut>", self._on_monto_editado)

        tree_frame = ttk.LabelFrame(main_frame, text="Períodos Incluidos", padding=10)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("N°", "Año Fiscal", "Fecha Inicio", "Fecha Fin", "Días", "Inv. Inicial", "Inv. Final")
        self.tree_periodos = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)
        col_widths = {"N°": 50, "Año Fiscal": 100, "Fecha Inicio": 130, "Fecha Fin": 130, "Días": 70, "Inv. Inicial": 110, "Inv. Final": 110}
        for col in columns:
            self.tree_periodos.heading(col, text=col)
            anchor = tk.CENTER if col in ("N°", "Año Fiscal", "Días") else tk.W
            self.tree_periodos.column(col, anchor=anchor, width=col_widths[col])
        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree_periodos.yview)
        self.tree_periodos.configure(yscrollcommand=scrollbar_y.set)
        self.tree_periodos.grid(row=0, column=0, sticky=tk.NSEW)
        scrollbar_y.grid(row=0, column=1, sticky=tk.NS)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_periodos.bind("<<TreeviewSelect>>", self._on_periodo_seleccionado)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        self.btn_incluir = ttk.Button(btn_frame, text="Incluir", command=self._incluir_periodo, state=tk.DISABLED)
        self.btn_incluir.pack(side=tk.LEFT, padx=5)
        self.btn_guardar = ttk.Button(btn_frame, text="Guardar", command=self._guardar_periodos, state=tk.DISABLED)
        self.btn_guardar.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cerrar", command=self.destroy).pack(side=tk.LEFT, padx=5)

        self.lbl_status = ttk.Label(main_frame, text="", font=("Segoe UI", 9), foreground="#0055AA")
        self.lbl_status.pack(fill=tk.X, padx=5, pady=(5, 0))

    def _cargar_configuracion_fiscal(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT com_Dia_Inicio_Fiscal, com_Mes_Inicio_Fiscal,
                       com_Dia_Fin_Fiscal, com_Mes_Fin_Fiscal
                FROM ark_company
                WHERE com_Status = 1
                LIMIT 1
            """)
            row = cursor.fetchone()
            conn.close()
            if not row or not all(row):
                messagebox.showwarning("Configuración Fiscal", "No hay empresa con configuración fiscal definida.")
                return
            mapeo_meses = {"Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5, "Junio": 6,
                           "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12}
            self._dia_ini = int(row[0])
            self._mes_ini = mapeo_meses.get(row[1], 1)
            self._dia_fin = int(row[2])
            self._mes_fin = mapeo_meses.get(row[3], 12)
            self.lbl_dia_ini.config(text=f"{self._dia_ini:02d}")
            self.lbl_mes_ini.config(text=f"{self._mes_ini:02d} - {row[1]}")
            self.lbl_dia_fin.config(text=f"{self._dia_fin:02d}")
            self.lbl_mes_fin.config(text=f"{self._mes_fin:02d} - {row[3]}")
            anios = [str(a) for a in range(date.today().year, 2019, -1)]
            self.cmb_anio['values'] = anios
            self.cmb_anio.current(0)
            self.btn_incluir.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la configuración fiscal:\n{e}")

    def _cargar_periodos_existentes(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pdo_Idauto, pdo_anio, pdo_fecha_ini, pdo_fecha_fin,
                       pdo_inv_declarado_ini_l, pdo_inv_declarado_fin_l
                FROM ark_periodos
                ORDER BY pdo_anio DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            for row in rows:
                pdo_id, anio, f_ini, f_fin, ini_l, fin_l = row
                try:
                    dias = (date.fromisoformat(f_fin) - date.fromisoformat(f_ini)).days + 1
                except ValueError:
                    dias = 0
                self._periodos_incluidos.append({
                    'anio': anio,
                    'fecha_ini': f_ini,
                    'fecha_fin': f_fin,
                    'dias': dias,
                    'id': pdo_id,
                    'ini_l': ini_l or 0.0,
                    'fin_l': fin_l or 0.0
                })
            self._refrescar_treeview()
            if self._periodos_incluidos:
                self.btn_guardar.config(state=tk.NORMAL)
                self.lbl_status.config(text=f"Períodos cargados desde ark_periodos: {len(self._periodos_incluidos)}", foreground="green")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los períodos existentes:\n{e}")

    def _refrescar_treeview(self):
        for item in self.tree_periodos.get_children():
            self.tree_periodos.delete(item)
        orden = sorted(self._periodos_incluidos, key=lambda p: p['fecha_ini'])
        for n, p in enumerate(orden, start=1):
            self.tree_periodos.insert("", tk.END, values=(
                n,
                p['anio'],
                date.fromisoformat(p['fecha_ini']).strftime("%d/%m/%Y"),
                date.fromisoformat(p['fecha_fin']).strftime("%d/%m/%Y"),
                p['dias'],
                self._formatear_monto(p['ini_l']),
                self._formatear_monto(p['fin_l'])
            ))

    def _incluir_periodo(self):
        if not self.cmb_anio.get():
            messagebox.showwarning("Advertencia", "Seleccione un año fiscal.")
            return
        anio_seleccionado = int(self.cmb_anio.get())
        for p in self._periodos_incluidos:
            if p['anio'] == anio_seleccionado:
                messagebox.showwarning("Advertencia", f"El año {anio_seleccionado} ya fue incluido.")
                return
        anio_inicio = anio_seleccionado
        anio_fin = anio_seleccionado + 1 if self._mes_fin < self._mes_ini else anio_seleccionado
        try:
            fecha_ini = date(anio_inicio, self._mes_ini, self._dia_ini)
            fecha_fin = date(anio_fin, self._mes_fin, self._dia_fin)
        except ValueError as e:
            messagebox.showerror("Error", f"Fecha inválida: {e}")
            return
        dias = (fecha_fin - fecha_ini).days + 1
        self._periodos_incluidos.append({
            'anio': anio_seleccionado,
            'fecha_ini': fecha_ini.strftime("%Y-%m-%d"),
            'fecha_fin': fecha_fin.strftime("%Y-%m-%d"),
            'dias': dias,
            'id': None,
            'ini_l': 0.0,
            'fin_l': 0.0
        })
        self._refrescar_treeview()
        self.btn_guardar.config(state=tk.NORMAL)
        self.lbl_status.config(
            text=f"Período {anio_seleccionado} incluido. Total: {len(self._periodos_incluidos)}",
            foreground="green"
        )

    def _on_periodo_seleccionado(self, event=None):
        sel = self.tree_periodos.selection()
        if not sel:
            return
        values = self.tree_periodos.item(sel[0], "values")
        periodo = next((p for p in self._periodos_incluidos if p['anio'] == int(values[1])), None)
        if not periodo:
            return
        self.ent_inv_ini.config(state=tk.NORMAL)
        self.ent_inv_fin.config(state=tk.NORMAL)
        self.ent_inv_ini.delete(0, tk.END)
        self.ent_inv_ini.insert(0, self._formatear_monto(periodo.get('ini_l', 0.0)))
        self.ent_inv_fin.delete(0, tk.END)
        self.ent_inv_fin.insert(0, self._formatear_monto(periodo.get('fin_l', 0.0)))

    def _on_monto_editado(self, event=None):
        sel = self.tree_periodos.selection()
        if not sel:
            return
        values = self.tree_periodos.item(sel[0], "values")
        periodo = next((p for p in self._periodos_incluidos if p['anio'] == int(values[1])), None)
        if not periodo:
            return
        periodo['ini_l'] = self._parse_monto(self.ent_inv_ini.get())
        periodo['fin_l'] = self._parse_monto(self.ent_inv_fin.get())
        self._refrescar_treeview()

    def _parse_monto(self, texto):
        try:
            limpio = (texto or "").replace(".", "").replace(",", ".").strip()
            return float(limpio) if limpio else 0.0
        except ValueError:
            return 0.0

    def _formatear_monto(self, valor):
        parte_entera = f"{int(valor):,}".replace(",", ".")
        parte_decimal = f"{int(round((valor - int(valor)) * 100)):02d}"
        return f"{parte_entera},{parte_decimal}"

    def _guardar_periodos(self):
        if not self._periodos_incluidos:
            messagebox.showwarning("Advertencia", "No hay períodos para guardar.")
            return
        confirm = messagebox.askyesno(
            "Confirmar Guardado",
            f"¿Guardar {len(self._periodos_incluidos)} períodos en ark_periodos?\n\n"
            "Se aplicará continuidad fiscal: el Inv. Final de cada período\n"
            "será el Inv. Inicial del período siguiente."
        )
        if not confirm:
            return
        try:
            orden = sorted(self._periodos_incluidos, key=lambda p: p['fecha_ini'])
            avisos = []
            for i in range(len(orden) - 1):
                actual = orden[i]
                siguiente = orden[i + 1]
                if siguiente['ini_l'] != actual['fin_l']:
                    siguiente['ini_l'] = actual['fin_l']
                    avisos.append(f"Período {siguiente['anio']}: Inv. Inicial ajustado a {self._formatear_monto(actual['fin_l'])} (Inv. Final de {actual['anio']}).")
            if avisos:
                messagebox.showinfo("Verificación de Continuidad Fiscal", "\n".join(avisos))
            conn = get_db_connection()
            cursor = conn.cursor()
            usuario = get_current_user()
            maquina = get_machine_name()
            fecha_hoy = date.today().isoformat()
            hora_hoy = datetime.now().strftime("%H:%M:%S")
            insertados = 0
            actualizados = 0
            for p in orden:
                if p['id'] is None:
                    cursor.execute("""
                        INSERT INTO ark_periodos (
                            pdo_fecha_ini, pdo_fecha_fin, pdo_anio, pdo_status,
                            pdo_inv_declarado_ini_l, pdo_inv_declarado_fin_l,
                            pdo_SystemDate, pdo_SystemTime, pdo_NameMachine, pdo_UserCreator
                        ) VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
                    """, (
                        p['fecha_ini'], p['fecha_fin'], p['anio'],
                        p['ini_l'], p['fin_l'],
                        fecha_hoy, hora_hoy, maquina, usuario
                    ))
                    p['id'] = cursor.lastrowid
                    insertados += 1
                else:
                    cursor.execute("""
                        UPDATE ark_periodos SET
                            pdo_inv_declarado_ini_l = ?, pdo_inv_declarado_fin_l = ?,
                            pdo_LastUpdateDate = ?, pdo_LastUpdateTime = ?,
                            pdo_LastMachine = ?, pdo_UserLastUpdate = ?
                        WHERE pdo_Idauto = ?
                    """, (
                        p['ini_l'], p['fin_l'],
                        fecha_hoy, hora_hoy, maquina, usuario,
                        p['id']
                    ))
                    actualizados += 1
            conn.commit()
            conn.close()
            self._refrescar_treeview()
            messagebox.showinfo("Éxito", f"Proceso completado.\n\nPeríodos insertados: {insertados}\nPeríodos actualizados: {actualizados}")
            self.lbl_status.config(text=f"Guardado: {insertados} insertados, {actualizados} actualizados", foreground="green")
        except Exception as e:
            messagebox.showerror("Error Crítico", f"Falló el guardado de períodos:\n{e}")