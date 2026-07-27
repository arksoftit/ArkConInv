import tkinter as tk
from tkinter import ttk, messagebox
from core.reset_data import TABLAS_RESET, obtener_conteo_tablas, ejecutar_reset
from core.backup_restore import crear_backup


class DialogResetData(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Reset de Datos de Prueba")
        self.geometry("620x620")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._center_on_parent()
        self.configure(bg="#F5F5F5")

        self.check_vars = {}
        self.conteo_tablas = {}
        self.lbl_total = None

        self._cargar_conteos()
        self._crear_widgets()
        self._actualizar_conteo()

        self.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.wait_window(self)

    def _center_on_parent(self):
        self.update_idletasks()
        pw = self.parent.winfo_width()
        ph = self.parent.winfo_height()
        px = self.parent.winfo_x()
        py = self.parent.winfo_y()
        w = 620
        h = 620
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _cargar_conteos(self):
        try:
            self.conteo_tablas = obtener_conteo_tablas()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron contar los registros:\n\n{e}")
            self.conteo_tablas = {}

    def _crear_widgets(self):
        frame_principal = ttk.Frame(self, padding=15)
        frame_principal.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame_principal,
            text="⚠️ RESET DE DATOS DE PRUEBA",
            font=("Segoe UI", 14, "bold"),
            foreground="#D32F2F"
        ).pack(pady=(0, 10))

        ttk.Label(
            frame_principal,
            text="Seleccione las tablas que desea limpiar. Esta acción es irreversible.",
            font=("Segoe UI", 10),
            wraplength=560,
            justify=tk.CENTER
        ).pack(pady=(0, 10))

        frame_grupos = ttk.Frame(frame_principal)
        frame_grupos.pack(fill=tk.BOTH, expand=True, pady=5)

        canvas = tk.Canvas(frame_grupos, bg="#F5F5F5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame_grupos, orient=tk.VERTICAL, command=canvas.yview)
        self.frame_inner = ttk.Frame(canvas)

        self.frame_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.frame_inner, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        for grupo, tablas in TABLAS_RESET.items():
            self._crear_grupo(grupo, tablas)

        frame_total = ttk.Frame(frame_principal)
        frame_total.pack(fill=tk.X, pady=(10, 5))

        ttk.Separator(frame_total, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 8))

        ttk.Label(
            frame_total,
            text="Total de registros a eliminar:",
            font=("Segoe UI", 10, "bold")
        ).pack(side=tk.LEFT)

        self.lbl_total = ttk.Label(
            frame_total,
            text="0",
            font=("Segoe UI", 12, "bold"),
            foreground="#D32F2F"
        )
        self.lbl_total.pack(side=tk.RIGHT)

        frame_botones = ttk.Frame(frame_principal)
        frame_botones.pack(fill=tk.X, pady=(10, 0))

        btn_ejecutar = tk.Button(
            frame_botones,
            text="🗑️ Ejecutar Reset",
            font=("Segoe UI", 10, "bold"),
            bg="#D32F2F",
            fg="white",
            activebackground="#B71C1C",
            activeforeground="white",
            padx=20,
            pady=6,
            command=self._confirmar_y_ejecutar
        )
        btn_ejecutar.pack(side=tk.RIGHT, padx=5)

        btn_cancelar = ttk.Button(
            frame_botones,
            text="Cancelar",
            command=self._cerrar
        )
        btn_cancelar.pack(side=tk.RIGHT, padx=5)

    def _crear_grupo(self, nombre_grupo, tablas):
        frame_grupo = ttk.LabelFrame(self.frame_inner, text=f" {nombre_grupo} ", padding=8)
        frame_grupo.pack(fill=tk.X, pady=5, padx=5)

        var_grupo = tk.BooleanVar(value=False)
        chk_grupo = ttk.Checkbutton(
            frame_grupo,
            text=f"Seleccionar todo ({self._suma_grupo(tablas)} registros)",
            variable=var_grupo,
            command=lambda g=nombre_grupo, t=tablas, v=var_grupo: self._toggle_grupo(g, t, v)
        )
        chk_grupo.pack(anchor=tk.W)

        for tabla, descripcion in tablas:
            var_tabla = tk.BooleanVar(value=False)
            self.check_vars[tabla] = var_tabla
            conteo = self.conteo_tablas.get(tabla, 0)
            chk_tabla = ttk.Checkbutton(
                frame_grupo,
                text=f"{tabla}  —  {descripcion}  [{conteo} registros]",
                variable=var_tabla,
                command=self._actualizar_conteo
            )
            chk_tabla.pack(anchor=tk.W, padx=20, pady=1)

    def _suma_grupo(self, tablas):
        return sum(self.conteo_tablas.get(t, 0) for t, _ in tablas)

    def _toggle_grupo(self, nombre_grupo, tablas, var_grupo):
        valor = var_grupo.get()
        for tabla, _ in tablas:
            self.check_vars[tabla].set(valor)
        self._actualizar_conteo()

    def _actualizar_conteo(self):
        total = 0
        for tabla, var in self.check_vars.items():
            if var.get():
                total += self.conteo_tablas.get(tabla, 0)
        if self.lbl_total:
            self.lbl_total.config(text=f"{total:,}".replace(",", "."))

    def _confirmar_y_ejecutar(self):
        tablas_sel = [t for t, v in self.check_vars.items() if v.get()]

        if not tablas_sel:
            messagebox.showwarning("Atención", "Debe seleccionar al menos una tabla para limpiar.")
            return

        total = sum(self.conteo_tablas.get(t, 0) for t in tablas_sel)
        detalle = "\n".join(f"  • {t}: {self.conteo_tablas.get(t, 0):,} registros".replace(",", ".") for t in tablas_sel)

        confirmar = messagebox.askyesno(
            "Confirmación Final",
            f"¿Está SEGURO de eliminar {total:,} registros?\n\n".replace(",", ".") +
            f"Tablas afectadas:\n{detalle}\n\n"
            "Esta acción es IRREVERSIBLE.",
            icon="warning"
        )

        if not confirmar:
            return

        try:
            ruta_backup = crear_backup()
        except Exception as e:
            messagebox.showerror(
                "Error de Respaldo", 
                f"No se pudo crear el respaldo obligatorio antes del reset:\n\n{e}\n\n"
                "La operación de limpieza ha sido cancelada por seguridad."
            )
            return

        try:
            resultado = ejecutar_reset(tablas_sel)
            self._mostrar_resultado(resultado, ruta_backup)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo ejecutar el reset:\n\n{e}")

    def _mostrar_resultado(self, resultado, ruta_backup=None):
        total = resultado["total"]
        detalle = "\n".join(f"  • {t}: {c} registros" for t, c in resultado["detalle"])
        log = resultado.get("log_file") or "No generado"

        mensaje = (
            f"✅ Limpieza ejecutada correctamente.\n\n"
            f"Total de registros eliminados: {total:,}\n\n".replace(",", ".") +
            f"Detalle:\n{detalle}\n\n"
            f" Log guardado en:\n{log}"
        )

        if ruta_backup:
            mensaje += f"\n\n💾 Respaldo automático creado en:\n{ruta_backup}"

        messagebox.showinfo("Reset Completado", mensaje)
        self._cerrar()

    def _cerrar(self):
        self.grab_release()
        self.destroy()