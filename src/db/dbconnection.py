import pyodbc
import json
import os
import winreg
from datetime import datetime

class DBConnectionManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.connection = None
        self.dsn_actual = None

    def get_dsn_list(self):
        dsn_list = []
        # Claves base para DSNs de Sistema y Usuario
        keys_to_check = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\ODBC\ODBC.INI\ODBC Data Sources"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\ODBC\ODBC.INI\ODBC Data Sources")
        ]

        for hkey, sub_key_path in keys_to_check:
            try:
                # Abrir la clave con el flag WOW64_32KEY para leer DSNs de 32 bits
                key = winreg.OpenKey(hkey, sub_key_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_32KEY)
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        # Verificar si el driver asociado contiene "DBISAM"
                        if "DBISAM" in value.upper():
                            # Asegurar unicidad en la lista
                            if name not in dsn_list:
                                dsn_list.append(name)
                        i += 1
                    except OSError:
                        # Se llegó al final de los valores de la clave
                        break
                winreg.CloseKey(key)
            except FileNotFoundError:
                # La clave no existe (por ejemplo, no hay DSNs de Usuario)
                continue
            except PermissionError:
                # No se tienen permisos para leer la clave (raro con HKEY_CURRENT_USER)
                continue
            except Exception:
                # Otro error inesperado al leer la clave
                continue

        return dsn_list

    def load_connections(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        return []
                    return json.loads(content)
            except json.JSONDecodeError:
                return []
        return []

    def save_connection(self, dsn, usuario, password):
        conexiones = self.load_connections()
        nueva_conexion = {
            'dsn': dsn,
            'usuario': usuario,
            'password': password,
            'fecha': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }
        conexiones = [c for c in conexiones if c['dsn'] != dsn]
        conexiones.insert(0, nueva_conexion)
        conexiones = conexiones[:10]
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(conexiones, f, indent=4)

    def connect(self, dsn, usuario, password):
        try:
            conn_str = f"DSN={dsn};UID={usuario};PWD={password};"
            self.connection = pyodbc.connect(conn_str, autocommit=True)
            self.dsn_actual = dsn
            return True, "Conexión exitosa"
        except pyodbc.Error as e:
            return False, str(e)

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            self.dsn_actual = None

    def get_data_directory(self):
        if not self.dsn_actual:
            return None

        # Rutas del registro para buscar DBISAM (32 bits en Windows 64)
        rutas_registro = [
            f"SOFTWARE\\WOW6432Node\\ODBC\\ODBC.INI\\{self.dsn_actual}",  # System DSN 32-bit
            f"SOFTWARE\\ODBC\\ODBC.INI\\{self.dsn_actual}",                # System DSN 64-bit (fallback)
            f"SOFTWARE\\WOW6432Node\\ODBC\\ODBC.INI\\{self.dsn_actual}",  # User DSN 32-bit (duplicado intencional para claridad)
            f"SOFTWARE\\ODBC\\ODBC.INI\\{self.dsn_actual}"                 # User DSN 64-bit (fallback)
        ]

        for ruta in rutas_registro:
            try:
                # Intentar con HKEY_LOCAL_MACHINE primero
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, ruta, 0, winreg.KEY_READ | winreg.KEY_WOW64_32KEY) as key:
                    # Probar las claves comunes de DBISAM
                    for clave in ["CatalogName", "Database", "DatabaseFile"]:
                        try:
                            valor, _ = winreg.QueryValueEx(key, clave)
                            # Si es un archivo .db o .ism, devolver la carpeta padre
                            if valor and os.path.exists(valor):
                                if valor.lower().endswith(('.db', '.ism', '.dat')):
                                    return os.path.dirname(valor)
                                else:
                                    return valor
                        except FileNotFoundError:
                            continue
            except (FileNotFoundError, PermissionError):
                pass

        # Si no encontró en HKLM, probar en HKCU
        for ruta in rutas_registro:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, ruta, 0, winreg.KEY_READ) as key:
                    for clave in ["CatalogName", "Database", "DatabaseFile"]:
                        try:
                            valor, _ = winreg.QueryValueEx(key, clave)
                            if valor and os.path.exists(valor):
                                if valor.lower().endswith(('.db', '.ism', '.dat')):
                                    return os.path.dirname(valor)
                                else:
                                    return valor
                        except FileNotFoundError:
                            continue
            except (FileNotFoundError, PermissionError):
                pass

        return None