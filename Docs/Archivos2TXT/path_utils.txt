import sys
import os
from datetime import datetime

# ============================================================================
# FUNCIONES BASE (MANTENIDAS Y MEJORADAS)
# ============================================================================

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

def get_app_root():
    """
    Obtiene la ruta raíz de la aplicación.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


# ============================================================================
# RUTAS EXISTENTES (COMPLETAMENTE RESPETADAS)
# ============================================================================

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

def get_app_logo_path():
    """Ruta al logo de ArkConInv (centrado)"""
    return get_resource_path(os.path.join("assets", "LogoApp_ArkConInv.png"))


# ============================================================================
# NUEVAS FUNCIONES PARA BACKUPS (AGREGADAS SIN AFECTAR LO EXISTENTE)
# ============================================================================

def get_backup_dir():
    """
    Obtiene el directorio donde se almacenarán los respaldos.
    Crea el directorio si no existe.
    """
    backup_dir = os.path.join(get_app_root(), 'ArkConInvDB', 'databackup')
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

def get_backup_file_path(prefix="backup", extension=".db"):
    """
    Genera una ruta completa para un archivo de respaldo con timestamp.
    
    Args:
        prefix (str): Prefijo para el nombre del archivo (por defecto "backup")
        extension (str): Extensión del archivo (por defecto ".db")
    
    Returns:
        str: Ruta completa al archivo de respaldo con timestamp
    """
    backup_dir = get_backup_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{prefix}_{timestamp}{extension}"
    return os.path.join(backup_dir, filename)

def get_latest_backup():
    """
    Obtiene la ruta del respaldo más reciente.
    
    Returns:
        str: Ruta al backup más reciente o None si no hay backups
    """
    backup_dir = get_backup_dir()
    
    try:
        # Obtener todos los archivos .db en el directorio
        backups = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
        
        if not backups:
            return None
        
        # Ordenar por fecha de modificación (más reciente primero)
        backups.sort(key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)), reverse=True)
        
        return os.path.join(backup_dir, backups[0])
    
    except Exception:
        return None

def get_backup_list():
    """
    Obtiene una lista de todos los respaldos disponibles con sus fechas.
    
    Returns:
        list: Lista de diccionarios con nombre y ruta de cada backup
    """
    backup_dir = get_backup_dir()
    backups = []
    
    try:
        for file in os.listdir(backup_dir):
            if file.endswith('.db'):
                full_path = os.path.join(backup_dir, file)
                # Extraer fecha del nombre (formato: prefix_YYYYMMDD_HHMMSS.db)
                try:
                    # Intentar extraer timestamp del nombre
                    name_parts = file.replace('.db', '').split('_')
                    if len(name_parts) >= 2:
                        timestamp_str = '_'.join(name_parts[1:])
                        timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                    else:
                        timestamp = datetime.fromtimestamp(os.path.getmtime(full_path))
                except:
                    timestamp = datetime.fromtimestamp(os.path.getmtime(full_path))
                
                backups.append({
                    'name': file,
                    'path': full_path,
                    'timestamp': timestamp,
                    'size': os.path.getsize(full_path),
                    'size_mb': round(os.path.getsize(full_path) / (1024 * 1024), 2)
                })
        
        # Ordenar por fecha (más reciente primero)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        
    except Exception:
        pass
    
    return backups

def get_backup_count():
    """
    Retorna el número total de respaldos disponibles.
    
    Returns:
        int: Cantidad de archivos de respaldo
    """
    return len(get_backup_list())

def get_backup_size_total():
    """
    Retorna el tamaño total de todos los respaldos en MB.
    
    Returns:
        float: Tamaño total en MB
    """
    backups = get_backup_list()
    total_bytes = sum(b['size'] for b in backups)
    return round(total_bytes / (1024 * 1024), 2)


# ============================================================================
# FUNCIONES DE UTILIDAD PARA GESTIÓN DE BACKUPS
# ============================================================================

def get_backup_directory_info():
    """
    Obtiene información del directorio de backups.
    
    Returns:
        dict: Información del directorio (ruta, cantidad, tamaño, etc.)
    """
    backup_dir = get_backup_dir()
    backups = get_backup_list()
    
    return {
        'directory': backup_dir,
        'exists': os.path.exists(backup_dir),
        'count': len(backups),
        'total_size_mb': sum(b['size_mb'] for b in backups),
        'latest': backups[0] if backups else None,
        'backups': backups
    }

def clean_old_backups(keep_count=5):
    """
    Elimina los respaldos más antiguos manteniendo solo los más recientes.
    
    Args:
        keep_count (int): Número de respaldos a mantener
    
    Returns:
        tuple: (eliminados, conservados)
    """
    backups = get_backup_list()
    
    if len(backups) <= keep_count:
        return 0, len(backups)
    
    # Los más recientes primero, eliminar los últimos (más antiguos)
    to_keep = backups[:keep_count]
    to_remove = backups[keep_count:]
    
    removed_count = 0
    for backup in to_remove:
        try:
            os.remove(backup['path'])
            removed_count += 1
        except Exception:
            pass
    
    return removed_count, len(to_keep)


# ============================================================================
# FUNCIONES PARA COMPATIBILIDAD CON MÓDULO DE RESPALDOS EXISTENTE
# ============================================================================

# Mantener compatibilidad con tu módulo de respaldos actual
def get_backup_database_path():
    """
    [Compatibilidad] Alias de get_backup_dir() para mantener compatibilidad
    con código existente que espera esta función.
    """
    return get_backup_dir()

def get_restore_path(backup_filename=None):
    """
    Obtiene la ruta de un archivo específico para restaurar.
    
    Args:
        backup_filename (str): Nombre del archivo de backup a restaurar.
                              Si es None, retorna el más reciente.
    
    Returns:
        str: Ruta completa al archivo de backup
    """
    if backup_filename:
        return os.path.join(get_backup_dir(), backup_filename)
    else:
        return get_latest_backup()


# ============================================================================
# EJEMPLO DE USO (SOLO PARA PRUEBAS)
# ============================================================================

if __name__ == "__main__":
    # Prueba rápida de las nuevas funciones
    print("=== RUTAS EXISTENTES ===")
    print(f"DB Path: {get_db_path()}")
    print(f"Schema Path: {get_schema_path()}")
    print(f"Icon Path: {get_icon_path()}")
    
    print("\n=== NUEVAS RUTAS DE BACKUP ===")
    print(f"Backup Dir: {get_backup_dir()}")
    print(f"New Backup: {get_backup_file_path('ArkConInv_backup')}")
    print(f"Latest Backup: {get_latest_backup()}")
    
    print("\n=== INFORMACIÓN DE BACKUPS ===")
    info = get_backup_directory_info()
    print(f"Total backups: {info['count']}")
    print(f"Total size: {info['total_size_mb']} MB")
    
    print("\n=== LISTA DE BACKUPS ===")
    for b in get_backup_list()[:3]:  # Mostrar solo los 3 más recientes
        print(f"  • {b['name']} ({b['size_mb']} MB) - {b['timestamp']}")