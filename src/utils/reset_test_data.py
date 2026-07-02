import os
import sys
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import getpass  # Para obtener el usuario de Windows

# ============================================================
# DETECCIÓN DINÁMICA DE LA RAÍZ DEL PROYECTO
# ============================================================
def encontrar_raiz_proyecto():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    current_dir = script_dir
    while True:
        if os.path.isdir(os.path.join(current_dir, 'src')) and \
           os.path.isdir(os.path.join(current_dir, 'config')):
            return current_dir
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            raise Exception("No se pudo encontrar la raíz del proyecto.")
        current_dir = parent_dir

ROOT_DIR = encontrar_raiz_proyecto()
sys.path.insert(0, ROOT_DIR)

from src.db.embedded_db import get_db_connection


class DialogResetTestData:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Reset de Datos de Prueba")
        self.root.geometry("600x600")
        self.root.resizable(False, False)
        
        # Centrar ventana
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.root.winfo_screenheight() // 2) - (600 // 2)
        self.root.geometry(f"+{x}+{y}")
        
        self._crear_widgets()
        self.root.mainloop()
    
    def _crear_widgets(self):
        # Frame principal que se expande
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título
        titulo = tk.Label(
            frame,
            text="⚠️ RESET DE DATOS DE PRUEBA",
            font=("Segoe UI", 14, "bold"),
            fg="#D32F2F"
        )
        titulo.pack(pady=(0, 15))
        
        # Mensaje
        mensaje = (
            "Esta acción ELIMINARÁ TODOS los registros de las tablas de\n"
            "transacciones y movimientos de inventario.\n\n"
            "Tablas que serán limpiadas:\n"
            "  • ark_transacciones\n"
            "  • ark_detalletranvtas\n"
            "  • ark_detalletrancomp\n"
            "  • ark_detalletraninv\n\n"
            "⚠️ Esta operación NO SE PUEDE DESHACER."
        )
        lbl_mensaje = tk.Label(
            frame,
            text=mensaje,
            font=("Segoe UI", 10),
            justify=tk.LEFT
        )
        lbl_mensaje.pack(pady=(0, 20))
        
        # Frame para botones
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=10)
        
        # Botón Limpiar (rojo)
        btn_limpiar = tk.Button(
            btn_frame,
            text="🗑️ Limpiar Datos",
            font=("Segoe UI", 10, "bold"),
            bg="#D32F2F",
            fg="white",
            padx=20,
            pady=8,
            width=15,
            command=self._confirmar_limpieza
        )
        btn_limpiar.pack(side=tk.LEFT, padx=10)
        
        # Botón Cancelar
        btn_cancelar = tk.Button(
            btn_frame,
            text="Cancelar",
            font=("Segoe UI", 10),
            padx=20,
            pady=8,
            width=15,
            command=self.root.destroy
        )
        btn_cancelar.pack(side=tk.LEFT, padx=10)
    
    def _confirmar_limpieza(self):
        respuesta = messagebox.askyesno(
            "Confirmación Final",
            "¿Está SEGURO de que desea eliminar TODOS los datos de prueba?\n\n"
            "Esta acción es irreversible.",
            icon='warning'
        )
        if respuesta:
            self._ejecutar_limpieza()
    
    def _generar_log(self, datos_eliminados, total_eliminados):
        """Genera un archivo de log con la información de la limpieza"""
        try:
            # Obtener usuario de Windows
            usuario_windows = getpass.getuser()
            
            # Fecha y hora actual
            ahora = datetime.now()
            fecha_hora = ahora.strftime("%Y-%m-%d %H:%M:%S")
            fecha_archivo = ahora.strftime("%Y%m%d_%H%M%S")
            
            # Crear carpeta logs si no existe
            log_dir = os.path.join(ROOT_DIR, 'logs')
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Nombre del archivo de log
            log_file = os.path.join(log_dir, f"reset_data_{fecha_archivo}.log")
            
            # Escribir el log
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("="*70 + "\n")
                f.write("REGISTRO DE LIMPIEZA DE DATOS DE PRUEBA\n")
                f.write("="*70 + "\n")
                f.write(f"Fecha y hora: {fecha_hora}\n")
                f.write(f"Usuario Windows: {usuario_windows}\n")
                f.write(f"Raíz del proyecto: {ROOT_DIR}\n")
                f.write("-"*70 + "\n")
                f.write("TABLAS LIMPIADAS:\n")
                for tabla, cantidad in datos_eliminados:
                    f.write(f"  • {tabla}: {cantidad} registros eliminados\n")
                f.write("-"*70 + "\n")
                f.write(f"TOTAL DE REGISTROS ELIMINADOS: {total_eliminados}\n")
                f.write("="*70 + "\n")
                f.write("FIN DEL REGISTRO\n")
            
            print(f"📄 Log generado: {log_file}")
            return log_file
            
        except Exception as e:
            print(f"⚠️ Error al generar el log: {e}")
            return None
    
    def _ejecutar_limpieza(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA foreign_keys = OFF;")
            
            tablas = [
                'ark_detalletranvtas',
                'ark_detalletrancomp',
                'ark_detalletraninv',
                'ark_transacciones'
            ]
            
            datos_eliminados = []
            total_eliminados = 0
            
            for tabla in tablas:
                cursor.execute(f"DELETE FROM {tabla};")
                eliminados = cursor.rowcount
                total_eliminados += eliminados
                datos_eliminados.append((tabla, eliminados))
                print(f"  ✅ {tabla}: {eliminados} registros eliminados")
            
            cursor.execute("PRAGMA foreign_keys = ON;")
            
            for tabla in tablas:
                try:
                    cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{tabla}';")
                except:
                    pass
            
            conn.commit()
            conn.close()
            
            # ============================================================
            # GENERAR LOG CON LA INFORMACIÓN DE LA LIMPIEZA
            # ============================================================
            log_file = self._generar_log(datos_eliminados, total_eliminados)
            # ============================================================
            
            mensaje_exito = f"✅ Datos de prueba eliminados correctamente.\n\nTotal de registros eliminados: {total_eliminados}"
            if log_file:
                mensaje_exito += f"\n\n📄 Log guardado en:\n{log_file}"
            
            messagebox.showinfo("Éxito", mensaje_exito)
            self.root.destroy()
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"❌ Error al limpiar los datos:\n\n{str(e)}"
            )


def main():
    print("="*60)
    print("⚠️  RESET DE DATOS DE PRUEBA")
    print("="*60)
    print(f"📂 Raíz del proyecto detectada: {ROOT_DIR}")
    print("="*60)
    DialogResetTestData()


if __name__ == "__main__":
    main()