import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.dbconnection import DBConnectionManager

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'conexiones.json'))

def main():
    print("--- Iniciando prueba de DBConnectionManager ---")
    manager = DBConnectionManager(CONFIG_PATH)

    print("\n1. Buscando DSNs de 32 bits en el registro...")
    dsn_list = manager.get_dsn_list()
    if dsn_list:
        print(f"   DSNs de DBISAM encontrados: {dsn_list}")
    else:
        print("   No se encontraron DSNs de DBISAM en el registro de 32 bits.")

    print("\n2. Probando guardado y lectura de conexiones (JSON)...")
    if dsn_list:
        test_dsn = dsn_list[0]
        manager.save_connection(test_dsn, "usuario_prueba", "pass_prueba")
        print(f"   Conexión de prueba guardada para: {test_dsn}")

    conexiones = manager.load_connections()
    print(f"   Total de conexiones en JSON: {len(conexiones)}")
    for c in conexiones:
        print(f"   - DSN: {c['dsn']} | Usuario: {c['usuario']} | Fecha: {c['fecha']}")

    print("\n--- Prueba finalizada ---")

if __name__ == "__main__":
    main()