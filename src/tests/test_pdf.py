import os
import sys

# Asegurar que Python encuentre los módulos de la carpeta src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.generar_pdf import generar_reporte_depositos

if __name__ == '__main__':
    # Guardar el PDF en la raíz del proyecto para fácil visualización
    ruta_salida = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Reporte_Depositos_Prueba.pdf'))
    
    print("Generando reporte de prueba...")
    try:
        generar_reporte_depositos(ruta_salida)
        print(f"¡Éxito! PDF generado en: {ruta_salida}")
        print("Abriendo el archivo para visualización...")
        os.startfile(ruta_salida)
    except Exception as e:
        print(f"Error al generar el PDF: {e}")