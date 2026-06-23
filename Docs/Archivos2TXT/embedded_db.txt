import sqlite3
import os
import sys

# Agregar la ruta del directorio src al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.path_utils import get_db_path, get_schema_path

def get_db_connection():
    """Obtiene una conexión a la base de datos embebida."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    return conn

def init_database():
    """Inicializa la base de datos creando las tablas si no existen."""
    db_path = get_db_path()
    schema_path = get_schema_path()
    
    # Asegurar que el directorio existe
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Leer el esquema desde el archivo schema.sql
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    try:
        cursor.executescript(schema_sql)
        conn.commit()
        print(f"Base de datos inicializada correctamente en: {db_path}")
    except sqlite3.Error as e:
        print(f"Error al inicializar la base de datos: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    init_database()