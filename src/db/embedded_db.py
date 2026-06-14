import sqlite3
import os

# Ruta relativa al archivo de base de datos principal
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'ArkConInvDB', 'database', 'arkconinv.db'))

def get_db_connection():
    """Obtiene una conexión a la base de datos embebida."""
    conn = sqlite3.connect(DB_PATH)
    # Devolver la conexión para que el llamador sea responsable de cerrarla
    return conn

def init_database():
    """Inicializa la base de datos creando las tablas si no existen."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True) # Asegurar que el directorio existe
    conn = get_db_connection()
    cursor = conn.cursor()

    # Leer el esquema desde el archivo schema.sql
    schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'ArkConInvDB', 'database', 'schema.sql'))
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    try:
        cursor.executescript(schema_sql)
        conn.commit()
        print(f"Base de datos inicializada correctamente en: {DB_PATH}")
    except sqlite3.Error as e:
        print(f"Error al inicializar la base de datos: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    init_database()