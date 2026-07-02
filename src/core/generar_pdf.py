import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.embedded_db import get_db_connection

# =========================================================================
# FUNCIONES AUXILIARES UNIFICADAS (DRY)
# =========================================================================

def _obtener_fecha_hora():
    now = datetime.now()
    return now.strftime("%d/%m/%Y"), now.strftime("%H:%M:%S")

def _obtener_datos_empresa(cursor):
    cursor.execute("SELECT com_Codigo, com_Descripcion, com_IDfiscal, com_DireccionF FROM ark_company LIMIT 1")
    empresa = cursor.fetchone()
    if not empresa:
        empresa = ("", "Sin Empresa Registrada", "Sin RIF", "Sin Dirección")
    return empresa

def _crear_estilos_reporte(styles):
    return {
        'header': ParagraphStyle('Header', parent=styles['Normal'], fontSize=9, leading=12),
        'title': ParagraphStyle('Title', parent=styles['Heading1'], fontSize=14, alignment=TA_CENTER, spaceAfter=12),
        'filter': ParagraphStyle('Filter', parent=styles['Normal'], fontSize=9, alignment=TA_LEFT),
        'footer': ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, alignment=TA_LEFT),
    }

def _crear_encabezado(empresa, fecha_str, hora_str, usar_landscape=False):
    # Calcular ancho útil según orientación (Márgenes de 28pt por lado de forma estandarizada)
    if usar_landscape:
        usable_width = 11 - (28 + 28) / 72  # ≈ 10.22 inches útiles
    else:
        usable_width = 8.5 - (28 + 28) / 72  # ≈ 7.72 inches útiles
    
    col_widths = [usable_width * 0.7 * inch, usable_width * 0.3 * inch]
    
    header_data = [
        [f"Empresa: {empresa[0]} - {empresa[1]}\nRIF: {empresa[2]}\nDirección Fiscal: {empresa[3]}", 
         f"Fecha: {fecha_str}\nHora: {hora_str}"]
    ]
    
    header_table = Table(header_data, colWidths=col_widths)
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (0,-1), 0),
        ('RIGHTPADDING', (1,0), (1,-1), 0),
    ]))
    return header_table

def _generar_pdf(ruta_salida, elements, usar_landscape=False):
    page_size = landscape(letter) if usar_landscape else letter
    # Unificamos márgenes a 28 en todos los reportes para evitar saltos inesperados
    doc = SimpleDocTemplate(ruta_salida, pagesize=page_size,
                            rightMargin=28, leftMargin=28,
                            topMargin=28, bottomMargin=28)
    doc.build(elements)
    return ruta_salida


# =========================================================================
# REPORTES DEL SISTEMA
# =========================================================================

# 1. REPORTE GENERAL DE DEPOSITOS
def generar_reporte_depositos(ruta_salida, uo_id=None, uo_nombre=None, status_filtro="Todos"):
    conn = get_db_connection()
    cursor = conn.cursor()
    empresa = _obtener_datos_empresa(cursor)
    fecha_str, hora_str = _obtener_fecha_hora()
    estilos = _crear_estilos_reporte(getSampleStyleSheet())

    query = "SELECT dep_codigo, dep_descripcion, dep_uo_nombre, dep_status FROM ark_depositos WHERE 1=1"
    params = []
    filtros_aplicados = []

    if uo_id is not None and uo_id != 0:
        query += " AND dep_uo_origen = ?"
        params.append(uo_id)
        filtros_aplicados.append(f"UO: {uo_nombre}")

    if status_filtro == "Activo":
        query += " AND dep_status = 1"
        filtros_aplicados.append("Status: Activo")
    elif status_filtro == "Inactivo":
        query += " AND dep_status = 0"
        filtros_aplicados.append("Status: Inactivo")

    query += " ORDER BY dep_uo_nombre, dep_codigo"
    cursor.execute(query, params)
    depositos = cursor.fetchall()
    conn.close()

    elements = []
    elements.append(_crear_encabezado(empresa, fecha_str, hora_str, usar_landscape=True))
    elements.append(Spacer(1, 14))
    elements.append(Paragraph("GENERAL DE DEPOSITOS", estilos['title']))
    elements.append(Spacer(1, 5))
    
    texto_filtros = "Filtros aplicados: " + (", ".join(filtros_aplicados) if filtros_aplicados else "Todos los registros")
    elements.append(Paragraph(texto_filtros, estilos['filter']))
    elements.append(Spacer(1, 14))

    col_widths = [1.5*inch, 3.5*inch, 3.5*inch, 1.72*inch] # Ajustado a los 10.22" útiles horizontales
    table_data = [['Código', 'Descripción', 'Unidad Operativa', 'Status']]
    total_registros = 0

    for row in depositos:
        status_text = "Activo" if row[3] == 1 else "Inactivo"
        table_data.append([str(row[0]), str(row[1]), str(row[2]), status_text])
        total_registros += 1

    data_table = Table(table_data, colWidths=col_widths)
    data_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
    ]))
    elements.append(data_table)
    elements.append(Spacer(1, 14))
    elements.append(Paragraph(f"TOTAL REGISTROS: {total_registros}", estilos['footer']))

    return _generar_pdf(ruta_salida, elements, usar_landscape=True)


# 2. REPORTE GENERAL DE CATEGORIAS
def generar_reporte_categorias(ruta_salida, status_filtro="Todos", maneja_depositos_filtro="Todos"):
    conn = get_db_connection()
    cursor = conn.cursor()
    empresa = _obtener_datos_empresa(cursor)
    fecha_str, hora_str = _obtener_fecha_hora()
    estilos = _crear_estilos_reporte(getSampleStyleSheet())
        
    query = "SELECT cat_codigo, cat_descripcion, cat_status, cat_depositos FROM ark_categoria WHERE 1=1"
    params = []
    filtros_aplicados = []
    
    if status_filtro == "Activo":
        query += " AND cat_status = 1"
        filtros_aplicados.append("Status: Activo")
    elif status_filtro == "Inactivo":
        query += " AND cat_status = 0"
        filtros_aplicados.append("Status: Inactivo")
        
    if maneja_depositos_filtro == "Si":
        query += " AND cat_depositos = 1"
        filtros_aplicados.append("Maneja Depósitos: Si")
    elif maneja_depositos_filtro == "No":
        query += " AND (cat_depositos = 0 OR cat_depositos IS NULL)"
        filtros_aplicados.append("Maneja Depósitos: No")
        
    query += " ORDER BY cat_codigo"
    cursor.execute(query, params)
    categorias = cursor.fetchall()
    conn.close()
    
    elements = []
    elements.append(_crear_encabezado(empresa, fecha_str, hora_str, usar_landscape=False))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("GENERAL DE CATEGORIAS", estilos['title']))
    elements.append(Spacer(1, 5))
    
    texto_filtros = "Filtros aplicados: " + (", ".join(filtros_aplicados) if filtros_aplicados else "Todos los registros")
    elements.append(Paragraph(texto_filtros, estilos['filter']))
    elements.append(Spacer(1, 10))
    
    col_widths = [1.2*inch, 4.0*inch, 1.2*inch, 1.32*inch] # Ajustado a 7.72" útiles verticales
    table_data = [['Código', 'Descripción', 'Status', 'Maneja Depósitos']]
    
    total_registros = 0
    for row in categorias:
        status_text = "Activo" if row[2] == 1 else "Inactivo"
        depositos_text = "Si" if row[3] == 1 else "No"
        table_data.append([str(row[0]), str(row[1]), status_text, depositos_text])
        total_registros += 1
        
    data_table = Table(table_data, colWidths=col_widths)
    data_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
    ]))
    elements.append(data_table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"TOTAL REGISTROS: {total_registros}", estilos['footer']))
    
    return _generar_pdf(ruta_salida, elements, usar_landscape=False)


# 3. REPORTE GENERAL DE INVENTARIO
def generar_reporte_inventario(ruta_salida, status_filtro="Todos", categoria_filtro="Todas las Categorías"):
    conn = get_db_connection()
    cursor = conn.cursor()
    empresa = _obtener_datos_empresa(cursor)
    fecha_str, hora_str = _obtener_fecha_hora()
    estilos = _crear_estilos_reporte(getSampleStyleSheet())
        
    query = """
        SELECT inv.inv_codigo, inv.inv_descripcion, cat.cat_descripcion, inv.inv_status
        FROM ark_inventario inv
        LEFT JOIN ark_categoria cat ON inv.inv_categoria = cat.cat_codigo
        WHERE 1=1
    """
    params = []
    filtros_aplicados = []
    
    if status_filtro == "Activo":
        query += " AND inv.inv_status = 1"
        filtros_aplicados.append("Status: Activo")
    elif status_filtro == "Inactivo":
        query += " AND inv.inv_status = 0"
        filtros_aplicados.append("Status: Inactivo")
        
    if categoria_filtro != "Todas las Categorías":
        parts = categoria_filtro.split(" - ", 1)
        cat_codigo = parts[0].strip()
        query += " AND inv.inv_categoria = ?"
        params.append(cat_codigo)
        filtros_aplicados.append(f"Categoría: {categoria_filtro}")
        
    query += " ORDER BY inv.inv_codigo"
    cursor.execute(query, params)
    inventario = cursor.fetchall()
    conn.close()
    
    elements = []
    elements.append(_crear_encabezado(empresa, fecha_str, hora_str, usar_landscape=False))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("GENERAL DE INVENTARIO", estilos['title']))
    elements.append(Spacer(1, 5))
    
    texto_filtros = "Filtros aplicados: " + (", ".join(filtros_aplicados) if filtros_aplicados else "Todos los registros")
    elements.append(Paragraph(texto_filtros, estilos['filter']))
    elements.append(Spacer(1, 10))
    
    col_widths = [1.3*inch, 3.4*inch, 2.0*inch, 1.02*inch] # Ajustado a 7.72"
    table_data = [['Código', 'Descripción', 'Categoría', 'Status']]
    
    total_registros = 0
    for row in inventario:
        status_text = "Activo" if row[3] == 1 else "Inactivo"
        cat_nombre = row[2] if row[2] else "Sin Asignar"
        table_data.append([str(row[0]), str(row[1]), cat_nombre, status_text])
        total_registros += 1
        
    data_table = Table(table_data, colWidths=col_widths)
    data_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
    ]))
    elements.append(data_table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"TOTAL REGISTROS: {total_registros}", estilos['footer']))
    
    return _generar_pdf(ruta_salida, elements, usar_landscape=False)


# 4. REPORTE DE MOVIMIENTO DE INVENTARIO (LANDSCAPE)
def generar_pdf_movimiento_inventario(ruta_salida, uo_id="0", fecha_desde=None, fecha_hasta=None, deposito_id="0", tipos=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    empresa = _obtener_datos_empresa(cursor)
    fecha_str, hora_str = _obtener_fecha_hora()
    estilos = _crear_estilos_reporte(getSampleStyleSheet())
    
    cursor.execute("SELECT topo_id, topo_descripcion FROM ark_tipos_operacion")
    tipo_nombres = {row[0]: row[1] for row in cursor.fetchall()}
    
    uo_nombre = "Todas las UO"
    if uo_id != "0":
        cursor.execute("SELECT uo_Codigo, uo_nombre FROM ark_unds_operativas WHERE uo_id = ?", (uo_id,))
        uo_row = cursor.fetchone()
        if uo_row:
            uo_nombre = f"{uo_row[0]} - {uo_row[1]}"
    
    deposito_nombre = "Todos los depósitos"
    if deposito_id != "0":
        cursor.execute("SELECT dep_codigo, dep_descripcion FROM ark_depositos WHERE dep_IDauto = ?", (deposito_id,))
        dep_row = cursor.fetchone()
        if dep_row:
            deposito_nombre = f"{dep_row[0]} - {dep_row[1]}"
    
    tipo_mapping = {
        'cargos': [2], 'descargos': [3], 'transferencias': [1], 'facturas': [11],
        'notas_entrega_vtas': [13], 'compras': [6], 'notas_entrega_comp': [8]
    }
    tipos_numeros = []
    for t in (tipos or []):
        if t in tipo_mapping:
            tipos_numeros.extend(tipo_mapping[t])
    
    if not tipos_numeros:
        tipos_numeros = [1, 2, 3, 6, 8, 11, 13]
 
    placeholders = ','.join(['?'] * len(tipos_numeros))
    
    query = f"""
    WITH movimientos AS (
        SELECT dtv_codigo as codigo, dtv_tipooperacion as tipooperacion, dtv_cantidad as cantidad, dtv_uo_Codigo as uo_codigo, dtv_depositosource as deposito
        FROM ark_detalletranvtas WHERE dtv_tipooperacion IN ({placeholders}) AND dtv_fechaoperacion BETWEEN ? AND ?
        UNION ALL
        SELECT dtc_codigo as codigo, dtc_tipooperacion as tipooperacion, dtc_cantidad as cantidad, dtc_uo_Codigo as uo_codigo, dtc_depositosource as deposito
        FROM ark_detalletrancomp WHERE dtc_tipooperacion IN ({placeholders}) AND dtc_fechaoperacion BETWEEN ? AND ?
        UNION ALL
        SELECT dti_codigo as codigo, dti_tipooperacion as tipooperacion, dti_cantidad as cantidad, dti_uo_Codigo as uo_codigo, dti_depositosource as deposito
        FROM ark_detalletraninv WHERE dti_tipooperacion IN ({placeholders}) AND dti_fechaoperacion BETWEEN ? AND ?
    ),
    agregado AS (
        SELECT codigo, tipooperacion, SUM(cantidad) as total_cantidad, uo_codigo, deposito
        FROM movimientos WHERE 1=1
    """
    
    params = tipos_numeros + [fecha_desde, fecha_hasta] + tipos_numeros + [fecha_desde, fecha_hasta] + tipos_numeros + [fecha_desde, fecha_hasta]
    
    if uo_id != "0":
        query += " AND uo_codigo = (SELECT uo_Codigo FROM ark_unds_operativas WHERE uo_id = ?)"
        params.append(uo_id)
    
    if deposito_id != "0":
        query += " AND deposito = ?"
        params.append(deposito_id)
   
    query += """
        GROUP BY codigo, tipooperacion, uo_codigo, deposito
    )
    SELECT a.codigo, i.inv_descripcion, a.tipooperacion, a.total_cantidad, a.uo_codigo, a.deposito
    FROM agregado a LEFT JOIN ark_inventario i ON a.codigo = i.inv_codigo
    ORDER BY a.codigo, a.tipooperacion
    """
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    productos = {}
    for row in rows:
        codigo = row[0]
        descripcion = row[1] or "Sin descripción"
        tipo = row[2]
        cantidad = float(row[3]) if row[3] else 0.0
        
        if codigo not in productos:
            productos[codigo] = {'descripcion': descripcion, 'tipos': {}}
        productos[codigo]['tipos'][tipo] = cantidad
    
    elements = []
    # Usar landscape=True recalcula dinámicamente los anchos del header a 10.22"
    elements.append(_crear_encabezado(empresa, fecha_str, hora_str, usar_landscape=True))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("MOVIMIENTO DE INVENTARIO", estilos['title']))
    elements.append(Spacer(1, 5))
    
    filtros_texto = [f"UO: {uo_nombre}", f"Período: {fecha_desde} al {fecha_hasta}", f"Depósito: {deposito_nombre}"]
    if tipos:
        nombres = [t.replace('_', ' ').title() for t in tipos]
        filtros_texto.append(f"Tipos: {', '.join(nombres)}")
    
    elements.append(Paragraph(f"Filtros aplicados: {', '.join(filtros_texto)}", estilos['filter']))
    elements.append(Spacer(1, 10))
    
    # Anchos calculados con exactitud para la cuadrícula horizontal (Suma total exacta: 10.22")
    col_widths = [1.0*inch, 2.42*inch, 0.85*inch, 0.85*inch, 0.85*inch, 0.85*inch, 0.85*inch, 0.85*inch, 0.85*inch, 0.9*inch]
    table_data = [['Código', 'Descripción', 'Cargos', 'Descargos', 'Transferencias', 'Facturas', 'N/E Vta', 'Compras', 'N/E Comp', 'Total']]
    
    total_cargos = total_descargos = total_transferencias = total_facturas = total_ne_vta = total_compras = total_ne_comp = total_general = 0.0
    total_registros = 0
    
    for codigo, data in sorted(productos.items()):
        t_data = data['tipos']
        cargos = t_data.get(2, 0.0)
        descargos = t_data.get(3, 0.0)
        transferencias = t_data.get(1, 0.0)
        facturas = t_data.get(11, 0.0)
        ne_vta = t_data.get(13, 0.0)
        compras = t_data.get(6, 0.0)
        ne_comp = t_data.get(8, 0.0)
        total = cargos + descargos + transferencias + facturas + ne_vta + compras + ne_comp
        
        table_data.append([
            str(codigo)[:15], str(data['descripcion'])[:30],
            f"{cargos:,.2f}", f"{descargos:,.2f}", f"{transferencias:,.2f}",
            f"{facturas:,.2f}", f"{ne_vta:,.2f}", f"{compras:,.2f}", f"{ne_comp:,.2f}", f"{total:,.2f}"
        ])
        
        total_cargos += cargos
        total_descargos += descargos
        total_transferencias += transferencias
        total_facturas += facturas
        total_ne_vta += ne_vta
        total_compras += compras
        total_ne_comp += ne_comp
        total_general += total
        total_registros += 1
    
    table_data.append(['', 'TOTALES:', f"{total_cargos:,.2f}", f"{total_descargos:,.2f}", f"{total_transferencias:,.2f}", f"{total_facturas:,.2f}", f"{total_ne_vta:,.2f}", f"{total_compras:,.2f}", f"{total_ne_comp:,.2f}", f"{total_general:,.2f}"])
    
    data_table = Table(table_data, colWidths=col_widths)
    data_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -2), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -2), colors.black),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 7),
        ('ALIGN', (0, 1), (-1, -2), 'LEFT'),
        ('ALIGN', (2, 1), (-1, -2), 'RIGHT'),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F2F2F2')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 8),
        ('ALIGN', (1, -1), (-1, -1), 'RIGHT'),
        ('GRID', (0, -1), (-1, -1), 0.5, colors.grey),
    ]))
    
    elements.append(data_table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"TOTAL PRODUCTOS: {total_registros}", estilos['footer']))
    
    return _generar_pdf(ruta_salida, elements, usar_landscape=True)