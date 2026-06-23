# ArkConInv - Consolidación de Inventario
# Desarrollado por Juan E. Páez M. (JUEPAE)
# Fecha: Junio 2026
# Version: 0.1.01Beta
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from ui.dialog_conexiones import DialogConexiones
from core.system_info import get_date_audit, get_current_user, get_machine_name, get_app_version
from db.embedded_db import init_database
from ui.dialog_company import DialogCompany
from ui.dialog_unds_operativas import DialogUndsOperativas
from ui.dialog_users import DialogUsers
from ui.dialog_depositos import DialogDeposito
from ui.dialog_categoria import DialogCategoria
from ui.dialog_inventario import DialogInventario
from ui.dialog_importar_categorias import DialogImportarCategorias
from ui.dialog_importar_depositos import DialogImportarDepositos
from ui.dialog_importar_inventario import DialogImportarInventario


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.system_info import get_date_audit, get_current_user, get_machine_name, get_app_version


class ArkConInvApp(tk.Tk):
    def __init__(self):
        super().__init__()
        init_database()
        self.title("ArkConInv - Consolidación de Inventario")
        self.minsize(800, 600)
        
        self._center_window(800, 600)

        self._create_menu()
        self._create_main_frame()
        self._create_status_bar()
        self.actualizar_barra_estado()
        self.protocol("WM_DELETE_WINDOW", self._confirmar_salida)
    
    def _center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        menu_maestros = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivos Maestros", menu=menu_maestros)
        menu_maestros.add_command(label="Depósitos", command=self._abrir_depositos)
        menu_maestros.add_command(label="Categorías", command=self._abrir_categorias)
        menu_maestros.add_command(label="Inventario", command=self._abrir_inventario)

        menu_transacciones = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Transacciones", menu=menu_transacciones)
        menu_transacciones.add_command(label="Cálculo de Existencias", command=self._placeholder)
        
        menu_importaciones = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Importaciones", menu=menu_importaciones)
        menu_importaciones.add_command(label="Importar Depósitos", command=self._abrir_importar_depositos)
        menu_importaciones.add_command(label="Importar Categorías", command=self._abrir_importar_categorias)
        menu_importaciones.add_command(label="Importar Inventario", command=self._abrir_importar_inventario)
        menu_importaciones.add_command(label="Importar Movimientos", command=self._abrir_importar_movimientos)

        menu_reportes = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Reportes", menu=menu_reportes)
        menu_reportes.add_command(label="Movimiento Art. 177 ISLR", command=self._placeholder)

        menu_config = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Configuración", menu=menu_config)
        menu_config.add_command(label="Registro de Empresa", command=self._abrir_dialogo_empresa)
        menu_config.add_command(label="Unidad Operativa", command=self._abrir_unds_operativas)
        menu_config.add_command(label="Usuarios", command=self._abrir_dialogo_usuarios)
        menu_config.add_command(label="Conexiones ODBC", command=self._abrir_dialogo_conexiones)

        menu_ayuda = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=menu_ayuda)
        menu_ayuda.add_command(label="Acerca de...", command=self.mostrar_acerca)
        
        menu_salida = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Salir", menu=menu_salida)
        menu_salida.add_command(label="Cerrar Aplicación", command=self._confirmar_salida)

    def _create_main_frame(self):
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

    def _create_status_bar(self):
        self.status_bar = ttk.Frame(self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_var = tk.StringVar()
        self.status_var.set("Iniciando...")

        self.status_label = ttk.Label(
            self.status_bar,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.CENTER,
            padding=(5, 2)
        )
        self.status_label.pack(fill=tk.X)

    def actualizar_barra_estado(self):
        try:
            fecha = get_date_audit()
            user = get_current_user()
            equipo = get_machine_name()
            version = get_app_version()

            info_sesion = (
                f" SESIÓN ACTIVA | Usuario: {user} | "
                f"Equipo: {equipo} | Fecha: {fecha} | Versión: {version}"
            )

            self.status_var.set(info_sesion)

        except Exception as e:
            self.status_var.set(f"Error al actualizar barra de estado: {e}")
            
    def _confirmar_salida(self):
        if messagebox.askyesno("Confirmar Salida", 
                            "¿Está seguro que desea cerrar ArkConInv?\n\n"
                            "Se cerrará la aplicación.",
                            icon='question'):
            self.destroy()

    def mostrar_acerca(self):
        info_acerca = (
            "ArkConInv v0.1.01Beta\n\n"
            "Desarrollado por Juan E. Páez M.\n"
            "JUEPAE\n"
            "Fecha: Junio 2026\n\n"
            "Consolidación de Inventario"
        )
        messagebox.showinfo("Acerca de ArkConInv", info_acerca)
    
    def _abrir_dialogo_empresa(self):
        DialogCompany(self)
    
    def _abrir_unds_operativas(self):
        DialogUndsOperativas(self)
    
    def _abrir_dialogo_usuarios(self):
        DialogUsers(self)

    def _abrir_dialogo_conexiones(self):
        DialogConexiones(self)
    
    def _abrir_categorias(self):
        DialogCategoria(self)

    def _abrir_inventario(self):
        DialogInventario(self)
        
    def _abrir_depositos(self):
        DialogDeposito(self)

    def _abrir_importar_categorias(self):
        DialogImportarCategorias(self)

    def _abrir_importar_depositos(self):
        DialogImportarDepositos(self)
    
    def _abrir_importar_inventario(self):
        DialogImportarInventario(self)
    
    def _abrir_importar_movimientos(self):
     #   DialogImportarMovimientos(self)
        messagebox.showinfo("Información", "Funcionalidad en desarrollo.")

    def _placeholder(self):
        messagebox.showinfo("Información", "Funcionalidad en desarrollo.")


if __name__ == "__main__":
    app = ArkConInvApp()
    app.mainloop()