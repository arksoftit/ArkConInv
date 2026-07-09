# ArkConInv - Consolidación de Inventario
# Desarrollado por Juan E. Páez M. (JUEPAE)
# Fecha: Junio 2026
# Version: 0.1.01.08Beta
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
from ui.dialog_monedas import DialogMonedas
from ui.dialog_factores_historicos import DialogFactoresHistoricos
from ui.dialog_importar_categorias import DialogImportarCategorias
from ui.dialog_importar_depositos import DialogImportarDepositos
from ui.dialog_importar_inventario import DialogImportarInventario
# from ui.dialog_import_existencia import DialogImportExistencia
from ui.dialog_import_transacciones import DialogImportTransacciones
from ui.dialog_reporte_depositos import DialogReporteDepositos
from ui.dialog_reporte_categorias import DialogReporteCategorias
from ui.dialog_reporte_inventario import DialogReporteInventario
from ui.dialog_reporte_movimiento_inv import DialogMovimientoInventario
from ui.dialog_resumen_preliminar import DialogResumenPreliminar
from ui.dialog_preliminar import DialogPreliminar


from PIL import Image, ImageTk
from core.path_utils import get_icon_path, get_logo_path


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.system_info import get_date_audit, get_current_user, get_machine_name, get_app_version


class ArkConInvApp(tk.Tk):
    def __init__(self):
        super().__init__()
        init_database()
        self.title("ArkConInv - Consolidación de Inventario")
        self.minsize(800, 600)
        self._center_window(800, 600)
        try:
            self.iconbitmap(get_icon_path())
        except tk.TclError:
            pass # Evita error si el icono no se encuentra en tiempo de ejecución

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
        menu_maestros.add_command(label="Monedas y Factores Históricos", command=self._abrir_monedas)
        

        menu_transacciones = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Transacciones", menu=menu_transacciones)
        # menu_transacciones.add_command(label="Preliminar", command=self._placeholder)
        menu_transacciones.add_command(label="Preliminar", command=self._abrir_preliminar)
        menu_transacciones.add_command(label="Iniciales", command=self._placeholder)
        menu_transacciones.add_command(label="Cálculo de Existencias", command=self._placeholder)
        menu_transacciones.add_command(label="Ajustes de Existencias", command=self._placeholder)
        menu_transacciones.add_command(label="Recalculo de un Periodo", command=self._placeholder)
        menu_transacciones.add_command(label="Cierre de un Periodo", command=self._placeholder)
        
        
        
        menu_importaciones = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Importaciones", menu=menu_importaciones)
        menu_importaciones.add_command(label="Importar Depósitos", command=self._abrir_importar_depositos)
        menu_importaciones.add_command(label="Importar Categorías", command=self._abrir_importar_categorias)
        menu_importaciones.add_command(label="Importar Inventario", command=self._abrir_importar_inventario)
        # menu_importaciones.add_command(label="Importar Existencia Actual", command=self._abrir_importar_existencia_actual)
        menu_importaciones.add_command(label="Importar Transacciones", command=self._abrir_importar_transacciones)

        # --- MENÚ REPORTES ---
        menu_reportes = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Reportes", menu=menu_reportes)
        
        # Reportes Generales Directos
        menu_reportes.add_command(label="General de Depósitos", command=self._abrir_reporte_depositos)
        menu_reportes.add_command(label="General de Categorias", command=self._abrir_reporte_categorias)
        menu_reportes.add_command(label="General de Inventario", command=self._abrir_reporte_inventario)
        
        # Separador visual antes del Submenú
        menu_reportes.add_separator()
        
        # CREACIÓN DEL SUBMENÚ: Gestión de Inventario
        submenu_gestion = tk.Menu(menu_reportes, tearoff=0)
        menu_reportes.add_cascade(label="Gestión de Inventario", menu=submenu_gestion)
        
        # Opciones dentro del Submenú "Gestión de Inventario"
        submenu_gestion.add_command(label="Movimiento de Inventario", command=self._abrir_reporte_movimiento_inv)
        submenu_gestion.add_command(label="Resumen Preliminar de Transacciones", command=self._abrir_resumen_preliminar)        
        submenu_gestion.add_command(label="Movimiento Art. 177 ISLR", command=self._placeholder)
        

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
        # Configurar un estilo personalizado para el fondo del main_frame
        style = ttk.Style()
        # Color azul cielo claro similar al fondo del logo (puedes ajustar el hex si lo deseas)
        style.configure('Main.TFrame', background="#AED6F1") 
        
        self.main_frame = ttk.Frame(self, style='Main.TFrame')
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Cargar y mostrar el logo en la parte superior derecha
        try:
            from core.path_utils import get_logo_path
            from PIL import Image, ImageTk
            
            logo_path = get_logo_path()
            image = Image.open(logo_path)
            self.logo_image = ImageTk.PhotoImage(image)
            logo_label = ttk.Label(self.main_frame, image=self.logo_image, background='#EAF2F8')
            logo_label.image = self.logo_image # Evita que el garbage collector elimine la imagen
            logo_label.pack(side=tk.TOP, anchor=tk.NE, padx=10, pady=10)
        except Exception as e:
            print(f"No se pudo cargar el logo: {e}")

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
            "ArkConInv v0.1.01.08Beta\n\n"
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
    
    def _abrir_depositos(self):
        DialogDeposito(self)
    
    def _abrir_categorias(self):
        DialogCategoria(self)

    def _abrir_inventario(self):
        DialogInventario(self)
        
    def _abrir_monedas(self):
        DialogMonedas(self)
        
    def _abrir_factores_historicos(self):
        DialogFactoresHistoricos(self)

    def _abrir_importar_categorias(self):
        DialogImportarCategorias(self)

    def _abrir_importar_depositos(self):
        DialogImportarDepositos(self)
    
    def _abrir_importar_inventario(self):
        DialogImportarInventario(self)
    
    def _abrir_importar_transacciones(self):
        DialogImportTransacciones(self)
    
    # def _abrir_importar_existencia_actual(self):
    #    DialogImportExistencia(self)
        
    def _abrir_preliminar(self):
        DialogPreliminar(self)

    def _placeholder(self):
        messagebox.showinfo("Información", "Funcionalidad en desarrollo.")
    
    def _abrir_reporte_depositos(self):
        DialogReporteDepositos(self)
    
    def _abrir_reporte_categorias(self):
        DialogReporteCategorias(self)
    
    def _abrir_reporte_inventario(self):
        DialogReporteInventario(self)
    
    def _abrir_reporte_movimiento_inv(self):
        DialogMovimientoInventario(self)
        
    def _abrir_resumen_preliminar(self):
        DialogResumenPreliminar(self)
        
    
    


if __name__ == "__main__":
    app = ArkConInvApp()
    app.mainloop()