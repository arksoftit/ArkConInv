import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
import sqlite3
import csv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.embedded_db import get_db_connection

class DialogMonedas(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Registro de Monedas y Factores Históricos")
        self.geometry("720x650") 
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (720 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (650 // 2)
        self.geometry(f"+{x}+{y}")

        self.current_id = None 
        
        self.protocol("WM_DELETE_WINDOW", self._salir)
    
        self._create_widgets()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Sección: Datos Generales ---
        frame_general = ttk.LabelFrame(main_frame, text=" Datos de la Moneda ", padding=10)
        frame_general.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(frame_general, text="Código:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.ent_codigo = ttk.Entry(frame_general, width=15)
        self.ent_codigo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(frame_general, text="Descripción:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.ent_descripcion = ttk.Entry(frame_general, width=35)
        self.ent_descripcion.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        ttk.Label(frame_general, text="Símbolo:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.ent_simbolo = ttk.Entry(frame_general, width=15)
        self.ent_simbolo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(frame_general, text="Tasa de Cambio:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.ent_tasa = ttk.Entry(frame_general, width=15)
        self.ent_tasa.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)

        # --- Sección: Botones de Acción ---
        frame_botones = ttk.Frame(main_frame)
        frame_botones.pack(fill=tk.X, pady=(0, 5))

        self.btn_guardar = ttk.Button(frame_botones, text="Guardar", command=self._guardar)
        self.btn_guardar.pack(side=tk.LEFT, padx=5)

        self.btn_borrar = ttk.Button(frame_botones, text="Borrar", command=self._borrar)
        self.btn_borrar.pack(side=tk.LEFT, padx=5)

        self.btn_cancelar = ttk.Button(frame_botones, text="Cancelar", command=self._cancelar)
        self.btn_cancelar.pack(side=tk.LEFT, padx=5)

        self.btn_importar = ttk.Button(frame_botones, text="Importar Factores Historicos", command=self._importar)
        self.btn_importar.pack(side=tk.LEFT, padx=5)

        self.btn_salir = ttk.Button(frame_botones, text="Salir", command=self._salir)
        self.btn_salir.pack(side=tk.RIGHT, padx=5)

        # --- Sección: Vista de Monedas (Treeview Superior) ---
        frame_tree = ttk.LabelFrame(main_frame, text=" Monedas Registradas ", padding=5)
        frame_tree.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        columnas = ("id", "codigo", "descripcion", "simbolo", "tasa")
        self.tree = ttk.Treeview(frame_tree, columns=columnas, show="headings", selectmode="browse")
        
        # Configuración de cabeceras llamando a la función de ordenamiento
        self.tree.heading("id", text="ID ↕", command=lambda: self._ordenar_columna(self.tree, "id", False))
        self.tree.heading("codigo", text="Código ↕", command=lambda: self._ordenar_columna(self.tree, "codigo", False))
        self.tree.heading("descripcion", text="Descripción ↕", command=lambda: self._ordenar_columna(self.tree, "descripcion", False))
        self.tree.heading("simbolo", text="Símbolo ↕", command=lambda: self._ordenar_columna(self.tree, "simbolo", False))
        self.tree.heading("tasa", text="Tasa ↕", command=lambda: self._ordenar_columna(self.tree, "tasa", False))

        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("codigo", width=80, anchor=tk.CENTER)
        self.tree.column("descripcion", width=250, anchor=tk.W)
        self.tree.column("simbolo", width=80, anchor=tk.CENTER)
        self.tree.column("tasa", width=100, anchor=tk.E)

        vsb = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        
        # --- Sección: Vista de Históricos (Treeview Inferior) ---
        frame_historico = ttk.LabelFrame(main_frame, text=" Factores Históricos de la Moneda Seleccionada ", padding=5)
        frame_historico.pack(fill=tk.BOTH, expand=True)

        cols_hist = ("id_hist", "fecha", "tasa_dia")
        self.tree_hist = ttk.Treeview(frame_historico, columns=cols_hist, show="headings", selectmode="browse")
        
        # Configuración de cabeceras de histórico con ordenamiento funcional
        self.tree_hist.heading("id_hist", text="ID Reg ↕", command=lambda: self._ordenar_columna(self.tree_hist, "id_hist", False))
        self.tree_hist.heading("fecha", text="Fecha Factor ↕", command=lambda: self._ordenar_columna(self.tree_hist, "fecha", False))
        self.tree_hist.heading("tasa_dia", text="Tasa del Día (Bs) ↕", command=lambda: self._ordenar_columna(self.tree_hist, "tasa_dia", False))

        self.tree_hist.column("id_hist", width=80, anchor=tk.CENTER)
        self.tree_hist.column("fecha", width=200, anchor=tk.CENTER)
        self.tree_hist.column("tasa_dia", width=250, anchor=tk.E)

        vsb_hist = ttk.Scrollbar(frame_historico, orient="vertical", command=self.tree_hist.yview)
        self.tree_hist.configure(yscrollcommand=vsb_hist.set)

        self.tree_hist.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb_hist.pack(side=tk.RIGHT, fill=tk.Y)

        self._cargar_tabla()

    def _ordenar_columna(self, tv, col, reverse):
        """Reordena el contenido de un Treeview al hacer clic sobre su cabecera."""
        lista_elementos = [(tv.set(k, col), k) for k in tv.get_children("")]
        
        # Intentar conversión analítica a valores flotantes/enteros si aplica para ordenar numéricamente
        try:
            lista_elementos.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            # Ordenamiento alfabético estándar si son cadenas de caracteres o fechas formateadas
            lista_elementos.sort(reverse=reverse)

        for index, (val, k) in enumerate(lista_elementos):
            tv.move(k, "", index)

        # Invertir la dirección para el siguiente clic en la misma columna
        tv.heading(col, command=lambda: self._ordenar_columna(tv, col, not reverse))

    def _cargar_tabla(self):
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT mon_idauto, mon_codigo, mon_descripcion, mon_simbolo, mon_tasa FROM ark_monedas ORDER BY mon_codigo")
            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                self.tree.insert("", tk.END, values=row)
            
            for item in self.tree_hist.get_children():
                self.tree_hist.delete(item)
        except Exception as e:
            messagebox.showerror("Error al cargar datos", f"{type(e).__name__}: {e}")

    def _on_tree_select(self, event):
        try:
            item_seleccionado = self.tree.selection()
            if not item_seleccionado:
                return

            valores = self.tree.item(item_seleccionado, "values")
            self.current_id = valores[0]

            self._limpiar_campos()

            self.ent_codigo.insert(0, valores[1])
            self.ent_descripcion.insert(0, valores[2])
            self.ent_simbolo.insert(0, valores[3])
            self.ent_tasa.insert(0, valores[4])

            self._cargar_historico(self.current_id)
        except Exception as e:
            messagebox.showerror("Error de Selección", f"{type(e).__name__}: {e}")

    def _cargar_historico(self, id_moneda):
        try:
            for item in self.tree_hist.get_children():
                self.tree_hist.delete(item)

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT fac_Idauto, fac_fecha, fac_tasa_dia 
                FROM ark_factor_hstorico 
                WHERE fac_mon_codigo = ? 
                ORDER BY fac_fecha DESC
            """, (id_moneda,))
            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                self.tree_hist.insert("", tk.END, values=row)
        except Exception as e:
            messagebox.showerror("Error al cargar histórico", f"{type(e).__name__}: {e}")

    def _guardar(self):
        try:
            codigo = self.ent_codigo.get().strip()
            descripcion = self.ent_descripcion.get().strip()
            simbolo = self.ent_simbolo.get().strip()
            tasa_raw = self.ent_tasa.get().strip()

            if not codigo or not descripcion or not simbolo or not tasa_raw:
                messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.")
                return

            try:
                tasa_cambio = float(tasa_raw)
                if tasa_cambio <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Error de Dato", "La Tasa de Cambio debe ser un número mayor a cero.")
                return

            conn = get_db_connection()
            cursor = conn.cursor()

            if self.current_id is None:
                cursor.execute("""
                    INSERT INTO ark_monedas (
                        mon_codigo, mon_descripcion, mon_simbolo, mon_tasa
                    ) VALUES (?, ?, ?, ?)
                """, (codigo, descripcion, simbolo, tasa_cambio))
                messagebox.showinfo("Éxito", "Moneda registrada correctamente.")
            else:
                cursor.execute("""
                    UPDATE ark_monedas SET 
                        mon_codigo = ?, mon_descripcion = ?, mon_simbolo = ?, mon_tasa = ?
                    WHERE mon_idauto = ?
                """, (codigo, descripcion, simbolo, tasa_cambio, self.current_id))
                messagebox.showinfo("Éxito", "Moneda actualizada correctamente.")

            conn.commit()
            conn.close()

            self._limpiar_campos()
            self.current_id = None
            self._cargar_tabla()

        except Exception as e:
            messagebox.showerror("Error en Guardar", f"{type(e).__name__}: {e}")

    def _borrar(self):
        try:
            if self.current_id is None:
                messagebox.showwarning("Advertencia", "Seleccione una moneda de la lista para borrar.")
                return

            if messagebox.askyesno("Confirmar Borrado", "¿Está seguro de eliminar esta moneda definitivamente?"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM ark_monedas WHERE mon_idauto = ?", (self.current_id,))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Éxito", "Moneda eliminada.")
                self._limpiar_campos()
                self.current_id = None
                self._cargar_tabla()
        except Exception as e:
            messagebox.showerror("Error en Borrar", f"{type(e).__name__}: {e}")

    def _cancelar(self):
        try:
            if any([
                self.ent_codigo.get(), self.ent_descripcion.get(), self.ent_simbolo.get(),
                self.ent_tasa.get()
            ]):
                if not messagebox.askyesno("Confirmar Cancelar", "¿Descartar todos los cambios?"):
                    return
            self._limpiar_campos()
            self.current_id = None
            for item in self.tree_hist.get_children():
                self.tree_hist.delete(item)
        except Exception as e:
            messagebox.showerror("Error en Cancelar", f"{type(e).__name__}: {e}")

    def _importar(self):
        item_seleccionado = self.tree.selection()
        if not item_seleccionado:
            messagebox.showwarning("Advertencia", "Debe seleccionar primero la moneda en la lista superior para poder importarle sus factores históricos.")
            return

        valores_moneda = self.tree.item(item_seleccionado, "values")
        mon_id_auto = int(valores_moneda[0]) 
        mon_codigo = valores_moneda[1]       

        ruta_archivo = filedialog.askopenfilename(
            title=f"Seleccionar Histórico CSV para {mon_codigo}",
            filetypes=[("Archivos CSV", "*.csv")]
        )
        if not ruta_archivo:
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            registrados = 0
            actualizados = 0
            omitidos = 0

            with open(ruta_archivo, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                
                encabezado = next(reader, None)
                if encabezado and ('fecha' in encabezado[0].lower() or 'tasa' in encabezado[0].lower()):
                    pass
                else:
                    f.seek(0)

                for row in reader:
                    if not row or len(row) < 2 or row[0] is None:
                        continue

                    fecha_raw = row[0].strip()
                    tasa_raw = row[1].strip()
                    
                    if not fecha_raw or not tasa_raw:
                        omitidos += 1
                        continue

                    try:
                        cursor.execute("""
                            INSERT INTO ark_factor_hstorico (
                                fac_mon_codigo, fac_fecha, fac_tasa_dia
                            ) VALUES (?, ?, ?)
                        """, (mon_id_auto, fecha_raw, tasa_raw))
                        registrados += 1
                    except sqlite3.IntegrityError:
                        cursor.execute("""
                            UPDATE ark_factor_hstorico 
                            SET fac_tasa_dia = ?
                            WHERE fac_mon_codigo = ? AND fac_fecha = ?
                        """, (tasa_raw, mon_id_auto, fecha_raw))
                        actualizados += 1
                    except sqlite3.Error:
                        omitidos += 1
                        continue

            conn.commit()
            conn.close()

            messagebox.showinfo(
                "Importación Finalizada", 
                f"Factores históricos procesados para: {mon_codigo} (ID: {mon_id_auto})\n\n"
                f"• Nuevos registrados: {registrados}\n"
                f"• Actualizados por fecha: {actualizados}\n"
                f"• Filas omitidas / errores: {omitidos}"
            )
            
            self._cargar_historico(mon_id_auto)

        except Exception as e:
            messagebox.showerror("Error en Importación", f"{type(e).__name__}: {e}")

    def _salir(self):
        try:
            if messagebox.askyesno("Confirmar Salida", "¿Cerrar este diálogo?"):
                self.destroy()
        except Exception as e:
            messagebox.showerror("Error en Salir", f"{type(e).__name__}: {e}")

    def _limpiar_campos(self):
        self.ent_codigo.delete(0, tk.END)
        self.ent_descripcion.delete(0, tk.END)
        self.ent_simbolo.delete(0, tk.END)
        self.ent_tasa.delete(0, tk.END)