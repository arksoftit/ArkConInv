import sys
import os

def get_resource_path(relative_path):
    """
    Obtiene la ruta absoluta a un recurso, funcionando tanto en desarrollo
    como en la aplicación compilada con PyInstaller.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    return os.path.join(base_path, relative_path)

def get_db_path():
    """Ruta absoluta al archivo de base de datos SQLite."""
    return get_resource_path(os.path.join('ArkConInvDB', 'database', 'arkconinv.db'))

def get_schema_path():
    """Ruta absoluta al archivo schema.sql."""
    return get_resource_path(os.path.join('ArkConInvDB', 'database', 'schema.sql'))

def get_icon_path():
    """Ruta absoluta al icono de la aplicación."""
    return get_resource_path(os.path.join('assets', 'icons', 'ArkToolsPC_02.ico'))

def get_logo_path():
    """Ruta absoluta al logo principal."""
    return get_resource_path(os.path.join('assets', 'images', 'LogoJ_Juepae_06X400.png'))