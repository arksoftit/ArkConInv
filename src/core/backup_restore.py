import os
import sqlite3
import shutil
from datetime import datetime
from db.embedded_db import get_db_connection
from core.path_utils import get_backup_dir, get_backup_file_path, get_latest_backup

def crear_backup(nombre_archivo=None):
    if not nombre_archivo:
        nombre_archivo = os.path.basename(get_backup_file_path("arkconinv_backup"))

    backup_dir = get_backup_dir()
    ruta_destino = os.path.join(backup_dir, nombre_archivo)

    conn_source = get_db_connection()
    try:
        conn_target = sqlite3.connect(ruta_destino)
        conn_source.backup(conn_target)
        conn_target.close()
        return ruta_destino
    except Exception as e:
        raise Exception(f"Error al crear el respaldo: {e}")
    finally:
        conn_source.close()

def restaurar_backup(ruta_backup):
    if not os.path.exists(ruta_backup):
        raise FileNotFoundError("El archivo de respaldo no existe.")

    conn_source = get_db_connection()
    try:
        db_path = conn_source.execute("PRAGMA database_list;").fetchone()[2]
    except Exception:
        db_path = None
    finally:
        conn_source.close()

    if not db_path:
        raise Exception("No se pudo determinar la ruta de la base de datos actual.")

    try:
        shutil.copy2(ruta_backup, db_path)
        return True
    except Exception as e:
        raise Exception(f"Error al restaurar el respaldo: {e}")

def listar_backups():
    backup_dir = get_backup_dir()
    archivos = []
    if os.path.exists(backup_dir):
        for f in os.listdir(backup_dir):
            if f.endswith(".db"):
                ruta = os.path.join(backup_dir, f)
                fecha = datetime.fromtimestamp(os.path.getmtime(ruta)).strftime("%Y-%m-%d %H:%M:%S")
                archivos.append({
                    "nombre": f, 
                    "ruta": ruta, 
                    "fecha": fecha, 
                    "tamano": os.path.getsize(ruta)
                })
    return sorted(archivos, key=lambda x: x["fecha"], reverse=True)

def eliminar_backup(ruta_backup):
    if os.path.exists(ruta_backup):
        os.remove(ruta_backup)