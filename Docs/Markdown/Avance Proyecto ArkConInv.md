# 📦 ArkConInv - Consolidación de Inventario

**Versión**: 0.1.01Beta  
**Fecha**: Junio 2026  
**Desarrollador**: Juan E. Páez M. (JUEPAE)

## 📋 Descripción

Aplicación de escritorio para la **gestión y consolidación de inventarios** desde múltiples unidades operativas con bases de datos DBISAM hacia una base de datos centralizada SQLite embebida. Permite importar, visualizar y calcular existencias de inventario partiendo de saldos iniciales, sumando entradas (compras, cargos, notas de entrega de proveedores) y restando salidas (ventas, descargos, notas de entrega a clientes).

## 🏗️ Arquitectura Técnica

### **Stack Tecnológico**

- **Lenguaje**: Python 3.14.4 (32 bits) ⚠️ *Obligatorio por compatibilidad con driver ODBC*

- **Base de Datos Local**: SQLite 3.48.0 (embebida)

- **Base de Datos Origen**: DBISAM 4 (solo lectura)

- **Driver ODBC**: DBISAM 4 ODBC Driver 4.29.00.01

- **Interfaz Gráfica**: tkinter/ttk

- **Conexión BD**: pyodbc

- **Empaquetado**: PyInstaller (compatible con Windows 64 bits vía WOW6432Node)

### **Características Técnicas**

- Lectura de DSN desde registro de Windows (WOW6432Node para compatibilidad 32/64 bits)

- Gestión de hasta 10 conexiones ODBC recientes en `conexiones.json`

- Auditoría automática de operaciones (fecha, hora, máquina, usuario)

- Threading para operaciones no bloqueantes

- Manejo de códigos alfanuméricos con ceros a la izquierda (tipo TEXT)

## ✅ Estado del Proyecto - Avance Actual

### **Módulos Completados (100%)**

#### **1. Configuración**

- ✅ Registro de Empresa

- ✅ Unidades Operativas (con ID único y conexión ODBC independiente)

- ✅ Gestión de Usuarios

- ✅ Configuración de Conexiones ODBC (DSN, usuario, contraseña)

#### **2. Importaciones desde DBISAM**

| Módulo | Registros Importados | Estado |
| - | - | - |
| **Categorías** | 34 | ✅ Completado |
| **Depósitos** | 2 | ✅ Completado |
| **Inventario** | 4,314 | ✅ Completado |


**Características de Importación**:

- ✅ Mensajes de éxito con conteo de registros importados

- ✅ Barra de progreso visual

- ✅ Conversión de tipos de datos (INTEGER → TEXT para preservar ceros a la izquierda)

- ✅ Manejo de campos DECIMAL de DBISAM a FLOAT en SQLite

- ✅ Auditoría automática (SystemDate, SystemTime, NameMachine, UserCreator, etc.)

- ✅ Vinculación por Unidad Operativa de origen

#### **3. Archivos Maestros (Visualización)**

| Formulario | Contador de Registros | Estado |
| - | - | - |
| **Maestro de Categorías** | ✅ Visible | Completado |
| **Maestro de Depósitos** | ✅ Visible | Completado |
| **Maestro de Inventario** | ✅ Visible | Completado |


**Características de Visualización**:

- ✅ Treeview con scrollbars

- ✅ Formato de columnas adaptado (ID, Código, Descripción, Status, etc.)

- ✅ Contador de registros en tiempo real ("Total de registros: X")

- ✅ Botón de refrescar datos

- ✅ Conversión de status (1 → "Activo", 0 → "Inactivo")

### **Módulos Pendientes de Desarrollo**

#### **1. Transacciones**

- ⏳ Cálculo de Existencias por período

  - Cálculo directo: Inventario Inicial + Entradas - Salidas

  - Cálculo inverso: Para clientes sin control de saldos iniciales

#### **2. Importaciones**

- ⏳ Importar Movimientos (compras, ventas, cargos, descargos)

#### **3. Reportes**

- ⏳ Movimiento de Artículos Art. 177 ISLR

## 📊 Estructura de Base de Datos SQLite

### **Tablas Implementadas**

1. **ark\_company** - Datos de la empresa

2. **ark\_unds\_operativas** - Unidades operativas con conexión ODBC

3. **ark\_users** - Usuarios del sistema

4. **ark\_categoria** - Categorías de inventario (82 campos)

5. **ark\_inventario** - Inventario general (91 campos)

6. **ark\_depositos** - Depósitos/Almacenes (18 campos)

**Nota**: Todas las tablas incluyen campos de auditoría (SystemDate, SystemTime, NameMachine, UserCreator, LastUpdateDate, LastUpdateTime, LastMachine, UserLastUpdate)

## 🎯 Objetivo Principal

Consolidar información de inventario desde **dos o más unidades operativas** con bases de datos DBISAM, permitiendo:

- Centralización de datos en SQLite

- Cálculo de existencias por período configurable

- Soporte para cálculo directo e inverso de saldos

- Generación de reportes fiscales (Art. 177 ISLR)

## 🔧 Instalación y Ejecución

### **Requisitos**

- Python 3.14.4 (32 bits)

- Windows 10/11

- DBISAM 4 ODBC Driver instalado

### **Dependencias**

```
pip install pyodbc pillow
```

### **Ejecución**

```
python src/main.py
```

### **Compilación a .exe**

```
pyinstaller --onefile --windowed --add-data "assets;assets" src/main.py
```

## 📝 Directivas de Desarrollo

1. **Paso a paso, comando a comando** - Sin saltar verificaciones

2. **VS Code** - Gestión exclusiva del código en este entorno

3. **Python 32 bits** - Compatibilidad estricta con driver ODBC

4. **Código limpio** - Sin comentarios que estorben

5. **Seguimiento por tickets** - Formato: `ACI` + `Año` + `Mes` + `Día` + `Correlativo`

## 🎬 Capturas de Pantalla

### Importación Exitosa

- Mensajes con conteo de registros: *"Importación de Inventario completada. Registros importados: 4314"*

### Maestro de Inventario

- Visualización con 4,314 registros

- Códigos preservados con ceros a la izquierda (00000005, 00000006, etc.)

- Contador en tiempo real: *"Total de registros: 4314"*

## 📅 Roadmap

- [x] Configuración de conexiones ODBC

- [x] Importación de Categorías

- [x] Importación de Depósitos

- [x] Importación de Inventario

- [x] Visualización de maestros con contadores

- [ ] Importación de Movimientos

- [ ] Cálculo de Existencias

- [ ] Reporte Art. 177 ISLR

- [ ] Empaquetado distributable (.exe)

## 📄 Licencia

Proyecto privado desarrollado por JUEPAE - Junio 2026


**Última actualización**: 14 de junio de 2026  
**Estado**: Desarrollo activo - Versión Beta

