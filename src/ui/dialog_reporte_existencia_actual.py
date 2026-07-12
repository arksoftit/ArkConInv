import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
from datetime import datetime

# Ajusta la ruta de sys.path si es necesario para encontrar los módulos core y db
# Asumiendo que la estructura es similar a otros diálogos (DialogImportTransacciones)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.embedded_db import get_db_connection
from core.generar_pdf import generar_pdf_existencia_actual # Importa la función específica


class DialogReporteExistenciaActual(tk.Toplevel): # Cambié el nombre de la clase para reflejar el propósito
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Reporte Existencia Actual de Inventario")
        self.geometry("650x400") # Ajusté el tamaño vertical, ya que no hay fechas ni tipos de operación
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (650 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (400 // 2) # Ajusté la altura aquí también
        self.geometry(f"+{x}+{y}")

        self.uo_data = {}
        self.deposito_data = {}

        # No se necesitan tipos de operación para este reporte
        # self.tipos_operacion = {...}

        self._create_widgets()
        self._cargar_datos_iniciales()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # --- Selección de Unidad Operativa ---
        ttk.Label(frame, text="Unidad Operativa:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.cmb_uo = ttk.Combobox(frame, state="readonly", width=50)
        self.cmb_uo.grid(row=0, column=1, columnspan=2, pady=5, padx=10)

        # --- Depósito ---
        ttk.Label(frame, text="Depósito:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.cmb_deposito = ttk.Combobox(frame, state="readonly", width=50)
        self.cmb_deposito.grid(row=1, column=1, columnspan=2, pady=5, padx=10)

        # --- Filtros por Tipo de Operación ---
        # Este bloque se elimina completamente para este reporte
        # ttk.Label(frame, text="Tipos de Operación:", ...)

        # --- Botones ---
        btn_frame = ttk.Frame(frame)
        # Ajusté la fila para que quede debajo de los combos
        btn_frame.grid(row=2, column=0, columnspan=3, pady=20) 

        ttk.Button(btn_frame, text="Generar PDF", command=self._generar_pdf).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cerrar", command=self.destroy).pack(side=tk.LEFT, padx=10)

    def _cargar_datos_iniciales(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            self.uo_data = {"0": "Todas las UO"}
            # Selecciona uo_id y uo_Codigo/nombre para poblar el combo
            cursor.execute("SELECT uo_id, uo_Codigo, uo_nombre FROM ark_unds_operativas WHERE uo_active = 1 ORDER BY uo_Codigo")
            for row in cursor.fetchall():
                # Clave: uo_id como string, Valor: Cadena formateada
                self.uo_data[str(row[0])] = f"{row[1]} - {row[2]}"
            self.cmb_uo['values'] = list(self.uo_data.values())
            self.cmb_uo.current(0) # Selecciona "Todas las UO"

            self.deposito_data = {"0": "Todos los depósitos"}
            # Selecciona dep_IDauto y dep_codigo/descripcion para poblar el combo
            cursor.execute("SELECT dep_IDauto, dep_codigo, dep_descripcion FROM ark_depositos ORDER BY dep_codigo")
            for row in cursor.fetchall():
                 # Clave: dep_IDauto como string, Valor: Cadena formateada
                self.deposito_data[str(row[0])] = f"{row[1]} - {row[2]}"
            self.cmb_deposito['values'] = list(self.deposito_data.values())
            self.cmb_deposito.current(0) # Selecciona "Todos los depósitos"

            conn.close()

            # Se eliminan las operaciones relacionadas con fechas

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los datos: {e}")

    # Se elimina el método _aplicar_mascara_fecha ya que no se usan campos de fecha

    def _generar_pdf(self):
        try:
            uo_display = self.cmb_uo.get()
            # Obtiene el uo_id correspondiente al valor mostrado en el combo
            uo_id = next((k for k, v in self.uo_data.items() if v == uo_display), "0")

            # Se eliminan las operaciones relacionadas con fechas
            # fecha_desde = ...
            # fecha_hasta = ...

            deposito_display = self.cmb_deposito.get()
            # Obtiene el deposito_id correspondiente al valor mostrado en el combo
            deposito_id = next((k for k, v in self.deposito_data.items() if v == deposito_display), "0")

            # Se eliminan las operaciones relacionadas con tipos de operación
            # tipos_seleccionados = ...

            # Mensaje de advertencia si no se selecciona una UO o depósito específicos
            # Opcional: Puedes permitirlo o no, dependiendo de la lógica de negocio
            # if uo_id == "0" and deposito_id == "0":
            #    messagebox.showwarning("Advertencia", "Seleccionar 'Todas las UO' y 'Todos los depósitos' puede generar un reporte muy grande.")
            #    # Puedes usar result = messagebox.askyesno(...) para confirmar

            ruta_salida = filedialog.asksaveasfilename(
                title="Guardar Reporte de Existencia Actual",
                defaultextension=".pdf",
                filetypes=[("Archivos PDF", "*.pdf")],
                initialfile=f"Reporte_Existencia_Actual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf" # Nombre de archivo dinámico
            )

            if not ruta_salida:
                return # El usuario canceló la operación

            self.config(cursor="watch") # Cursor de reloj durante la generación
            self.update()

            # Llama a la función específica para generar el reporte de existencia actual
            # Solo pasa los parámetros que la función necesita: ruta_salida, uo_id, deposito_id
            generar_pdf_existencia_actual(
                ruta_salida=ruta_salida,
                uo_id=uo_id,
                deposito_id=deposito_id,
                # No se pasa fecha_desde, fecha_hasta ni tipos
            )

            self.config(cursor="") # Restaura el cursor normal
            messagebox.showinfo("Éxito", f"Reporte generado exitosamente en:\n{ruta_salida}")
            # Opcional: Abrir el archivo automáticamente
            # os.startfile(ruta_salida) # Solo funciona en Windows

        except Exception as e:
            self.config(cursor="") # Asegura restaurar el cursor en caso de error
            messagebox.showerror("Error", f"Ocurrió un error al generar el PDF:\n{e}")
