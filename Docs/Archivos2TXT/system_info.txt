import platform
import getpass
import socket
from datetime import datetime

APP_VERSION = "0.1.01Beta"
APP_DEVELOPER = "Juan E. Páez M. - JUEPAE"
APP_DATE = "Junio 2026"

def get_date_audit():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def get_current_user():
    return getpass.getuser()

def get_machine_name():
    return socket.gethostname()

def get_app_version():
    return f"ArkConInv v{APP_VERSION}"

def get_system_info_dict():
    return {
        "fecha": get_date_audit(),
        "usuario": get_current_user(),
        "equipo": get_machine_name(),
        "version": get_app_version()
    }
