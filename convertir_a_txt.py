import os
import shutil

# --- CONFIGURA AQUÍ ---
# Directorio donde están tus archivos .py (usa '.' para el actual)
origen = r'H:\Desarrollos\MyPython\Tkinter\ArkConInv\src\ui'  
# Directorio destino (cámbialo si quieres)
destino = r'H:\Desarrollos\MyPython\Tkinter\ArkConInv\Docs\Archivos2TXT'
# ----------------------

# Crea el directorio destino si no existe
os.makedirs(destino, exist_ok=True)

# Recorre todos los archivos del directorio origen
for archivo in os.listdir(origen):
    if archivo.endswith('.py'):
        ruta_origen = os.path.join(origen, archivo)
        nombre_base = os.path.splitext(archivo)[0]   # quita la extensión .py
        ruta_destino = os.path.join(destino, nombre_base + '.txt')
        
        try:
            # Lee el contenido del .py (con codificación UTF-8)
            with open(ruta_origen, 'r', encoding='utf-8') as f:
                contenido = f.read()
            # Escribe el mismo contenido en el .txt
            with open(ruta_destino, 'w', encoding='utf-8') as f:
                f.write(contenido)
            print(f'✅ Creado: {ruta_destino}')
        except Exception as e:
            print(f'❌ Error con {archivo}: {e}')