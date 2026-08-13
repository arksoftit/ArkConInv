import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.embedded_db import get_db_connection
from core.system_info import get_current_user, get_machine_name

CAMPOS_CONSOLIDACION = [
    "codigo", "descripcion", "categoria", "descripciondetallada", "vendedor",
    "status", "unidad", "tipocodigobarra", "imagen", "sustituto1", "sustituto2",
    "sustituto3", "referencia", "marca", "moneda", "factorconversion",
    "undexistencia2", "puesto", "sujetoacomision", "montocomision",
    "cuentascontables", "pesoproducto", "diasdereposicion", "presentacion",
    "garantia", "sustituto4", "sustituto5", "montocomisionp", "depositos",
    "ofertas", "vencimientos", "clasificacion", "manejoinventario", "seriales",
    "creacion", "inventarioinicialunidades", "inventarioinicialcosto",
    "capacidad", "existdecimal", "compuestoseriales", "vendedorfijo",
    "vendedorfijoactivo", "modelo", "subcategoria", "pesoafectacosto",
    "impresora", "base_autoincrement", "zextra1", "zextra2", "zextra3",
    "zextra4", "zextra5", "zextra6", "zextra1venta", "zextra2venta",
    "zextra3venta", "zextra4venta", "zextra5venta", "zextra6venta",
    "zextra1ventamod", "zextra2ventamod", "zextra3ventamod", "zextra4ventamod",
    "zextra5ventamod", "zextra6ventamod", "internet", "balanza", "codigobarra",
    "preciolista", "aprovechaporc", "arancel", "posentrega", "cargosextras"
]

class DialogConsolidarInventario(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Consolidación de Inventario")
        self.geometry("550x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (550 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (400 // 2)
        self.geometry(f"+{x}+{y}")
        self._create_widgets()
        self._cargar_contadores()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        info_lbl = ttk.Label(
            frame,
            text="Este proceso reconstruirá totalmente la tabla ark_maestro_inventario\n"
                 "consolidando un registro único por código de artículo, tomando como\n"
                 "referencia la unidad operativa con uo_id = 1.",
            font=("Segoe UI", 9, "italic"), foreground="#2874A6", justify=tk.LEFT
        )
        info_lbl.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky=tk.W)
        self.lbl_reg_inventario = ttk.Label(frame, text="", font=("Segoe UI", 9))
        self.lbl_reg_inventario.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
        self.lbl_cod_distintos = ttk.Label(frame, text="", font=("Segoe UI", 9))
        self.lbl_cod_distintos.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)
        self.lbl_reg_maestro = ttk.Label(frame, text="", font=("Segoe UI", 9))
        self.lbl_reg_maestro.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
        self.progress_lbl = ttk.Label(frame, text="", font=("Segoe UI", 9))
        self.progress_lbl.grid(row=4, column=0, columnspan=2, pady=(20, 5), sticky=tk.W)
        self.progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="determinate", length=450)
        self.progress_bar.grid(row=5, column=0, columnspan=2, pady=5, sticky=tk.W)
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=25)
        ttk.Button(btn_frame, text="Consolidar Inventario", command=self._consolidar_inventario).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cerrar", command=self.destroy).pack(side=tk.LEFT, padx=10)

    def _cargar_contadores(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ark_inventario")
        total_inv = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT inv_codigo) FROM ark_inventario")
        total_cod = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ark_maestro_inventario")
        total_mts = cursor.fetchone()[0]
        conn.close()
        self.lbl_reg_inventario.config(text=f"Registros en ark_inventario (todas las UO): {total_inv}")
        self.lbl_cod_distintos.config(text=f"Códigos distintos a consolidar: {total_cod}")
        self.lbl_reg_maestro.config(text=f"Registros actuales en ark_maestro_inventario: {total_mts}")

    def _consolidar_inventario(self):
        if not messagebox.askyesno("Confirmar Consolidación",
                                   "Se limpiará y reconstruirá totalmente ark_maestro_inventario.\n"
                                   "¿Desea continuar?"):
            return
        try:
            self.config(cursor="watch")
            self.progress_lbl.config(text="Leyendo artículos consolidados...")
            self.progress_bar['value'] = 10
            self.update()
            conn = get_db_connection()
            cursor = conn.cursor()
            cols_origen = ", ".join(f"inv_{c}" for c in CAMPOS_CONSOLIDACION)
            cursor.execute(f"""
                SELECT {cols_origen}, MIN(inv_uo_id)
                FROM ark_inventario
                GROUP BY inv_codigo
                ORDER BY inv_codigo
            """)
            articulos = [row[:-1] for row in cursor.fetchall()]
            total_articulos = len(articulos)
            if total_articulos == 0:
                conn.close()
                self.config(cursor="")
                self.progress_bar['value'] = 0
                self.progress_lbl.config(text="")
                messagebox.showwarning("Advertencia", "No hay registros en ark_inventario para consolidar.")
                return
            self.progress_lbl.config(text="Reconstruyendo ark_maestro_inventario...")
            self.progress_bar['value'] = 30
            self.update()
            cursor.execute("DELETE FROM ark_maestro_inventario")
            cols_destino = ", ".join(f"mts_{c}" for c in CAMPOS_CONSOLIDACION)
            marcadores = ", ".join(["?"] * len(CAMPOS_CONSOLIDACION))
            usuario = get_current_user()
            maquina = get_machine_name()
            procesados = 0
            for row in articulos:
                cursor.execute(f"""
                    INSERT INTO ark_maestro_inventario
                    ({cols_destino}, mts_SystemDate, mts_SystemTime, mts_NameMachine, mts_UserCreator,
                     mts_LastUpdateDate, mts_LastUpdateTime, mts_LastMachine, mts_UserLastUpdate)
                    VALUES ({marcadores}, date('now'), time('now'), ?, ?, date('now'), time('now'), ?, ?)
                """, (*row, maquina, usuario, maquina, usuario))
                procesados += 1
                if procesados % 50 == 0:
                    porcentaje = 30 + int((procesados / total_articulos) * 60)
                    self.progress_bar['value'] = porcentaje
                    self.progress_lbl.config(text=f"Procesando: {procesados}/{total_articulos} artículos...")
                    self.update()
            conn.commit()
            cursor.execute("SELECT COUNT(*) FROM ark_maestro_inventario")
            total_mts = cursor.fetchone()[0]
            conn.close()
            self.progress_bar['value'] = 100
            self.config(cursor="")
            self._cargar_contadores()
            messagebox.showinfo("Éxito",
                                f"Consolidación completada.\n"
                                f"Artículos consolidados: {total_articulos}\n"
                                f"Registros en ark_maestro_inventario: {total_mts}")
            self.destroy()
        except Exception as e:
            self.config(cursor="")
            self.progress_bar['value'] = 0
            self.progress_lbl.config(text="")
            messagebox.showerror("Error Crítico", f"Falló el proceso de consolidación:\n{e}")