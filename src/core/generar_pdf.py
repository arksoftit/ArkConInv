import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.embedded_db import get_db_connection

# REPORTE GENERAL DE DEPOSITOS

# def generar_reporte_depositos(ruta_salida, uo_id=None, status_filtro="Todos"):
def generar_reporte_depositos(ruta_salida, uo_id=None, uo_nombre=None, status_filtro="Todos"):
    doc = SimpleDocTemplate(ruta_salida, pagesize=letter,
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT com_Codigo, com_Descripcion, com_IDfiscal, com_DireccionF FROM ark_company LIMIT 1")
    empresa = cursor.fetchone()
    if not empresa:
        empresa = ("", "Sin Empresa Registrada", "Sin RIF", "Sin Dirección")
        
    # Construcción de la consulta con filtros
    query = "SELECT dep_codigo, dep_descripcion, dep_uo_nombre, dep_status FROM ark_depositos WHERE 1=1"
    params = []
    filtros_aplicados = []
    
    if uo_id is not None and uo_id != 0:
        query += " AND dep_uo_origen = ?"
        params.append(uo_id)
        # filtros_aplicados.append(f"UO: {uo_id}")
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
    
    now = datetime.now()
    fecha_str = now.strftime("%d/%m/%Y")
    hora_str = now.strftime("%H:%M:%S")
    
    # Estilos
    header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=9, leading=12)
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=14, alignment=TA_CENTER, spaceAfter=12)
    filter_style = ParagraphStyle('Filter', parent=styles['Normal'], fontSize=9, alignment=TA_LEFT)
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, alignment=TA_LEFT)
    
    # ENCABEZADO: Tabla de 2 columnas para alinear izquierda/derecha
    header_data = [
        [f"Empresa: {empresa[0]} - {empresa[1]}", f"Fecha: {fecha_str}"],
        [f"RIF: {empresa[2]}", f"Hora: {hora_str}"],
        [f"Dirección Fiscal: {empresa[3]}", ""]
    ]
    
    header_table = Table(header_data, colWidths=[4.5*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 15))
    
    # TÍTULO
    elements.append(Paragraph("GENERAL DE DEPOSITOS", title_style))
    elements.append(Spacer(1, 5))
    
    # FILTROS (alineados a la izquierda)
    texto_filtros = "Filtros aplicados: " + (", ".join(filtros_aplicados) if filtros_aplicados else "Todos los registros")
    elements.append(Paragraph(texto_filtros, filter_style))
    elements.append(Spacer(1, 10))
    
    # TABLA DE DETALLES
    col_widths = [1.2*inch, 2.5*inch, 2.0*inch, 1.0*inch]
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
    elements.append(Spacer(1, 20))
    
    # PIE DE PÁGINA (alineado a la izquierda)
    elements.append(Paragraph(f"TOTAL REGISTROS: {total_registros}", footer_style))
    
    doc.build(elements)
    return ruta_salida

# REPORTE GENERAL DE CATEGORIAS

def generar_reporte_categorias(ruta_salida, status_filtro="Todos", maneja_depositos_filtro="Todos"):
    doc = SimpleDocTemplate(ruta_salida, pagesize=letter,
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT com_Codigo, com_Descripcion, com_IDfiscal, com_DireccionF FROM ark_company LIMIT 1")
    empresa = cursor.fetchone()
    if not empresa:
        empresa = ("", "Sin Empresa Registrada", "Sin RIF", "Sin Dirección")
        
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
    
    now = datetime.now()
    fecha_str = now.strftime("%d/%m/%Y")
    hora_str = now.strftime("%H:%M:%S")
    
    header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=9, leading=12)
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=14, alignment=TA_CENTER, spaceAfter=12)
    filter_style = ParagraphStyle('Filter', parent=styles['Normal'], fontSize=9, alignment=TA_LEFT)
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, alignment=TA_LEFT)
    
    header_data = [
        [f"Empresa: {empresa[0]} - {empresa[1]}", f"Fecha: {fecha_str}"],
        [f"RIF: {empresa[2]}", f"Hora: {hora_str}"],
        [f"Dirección Fiscal: {empresa[3]}", ""]
    ]
    
    header_table = Table(header_data, colWidths=[4.5*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("GENERAL DE CATEGORIAS", title_style))
    elements.append(Spacer(1, 5))
    
    texto_filtros = "Filtros aplicados: " + (", ".join(filtros_aplicados) if filtros_aplicados else "Todos los registros")
    elements.append(Paragraph(texto_filtros, filter_style))
    elements.append(Spacer(1, 10))
    
    col_widths = [1.0*inch, 3.5*inch, 1.0*inch, 1.2*inch]
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
    
    elements.append(Paragraph(f"TOTAL REGISTROS: {total_registros}", footer_style))
    
    doc.build(elements)
    return ruta_salida

# REPORTE GENERAL DE INVENTARIO
def generar_reporte_inventario(ruta_salida, status_filtro="Todos", categoria_filtro="Todas las Categorías"):
    doc = SimpleDocTemplate(ruta_salida, pagesize=letter,
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT com_Codigo, com_Descripcion, com_IDfiscal, com_DireccionF FROM ark_company LIMIT 1")
    empresa = cursor.fetchone()
    if not empresa:
        empresa = ("", "Sin Empresa Registrada", "Sin RIF", "Sin Dirección")
        
    # JOIN para obtener el nombre de la categoría
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
        
    # Extraer el código de la categoría del string concatenado (ej: "00009 - MAQUINAS" -> "00009")
    cat_codigo = None
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
    
    now = datetime.now()
    fecha_str = now.strftime("%d/%m/%Y")
    hora_str = now.strftime("%H:%M:%S")
    
    header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=9, leading=12)
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=14, alignment=TA_CENTER, spaceAfter=12)
    filter_style = ParagraphStyle('Filter', parent=styles['Normal'], fontSize=9, alignment=TA_LEFT)
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, alignment=TA_LEFT)
    
    header_data = [
        [f"Empresa: {empresa[0]} - {empresa[1]}", f"Fecha: {fecha_str}"],
        [f"RIF: {empresa[2]}", f"Hora: {hora_str}"],
        [f"Dirección Fiscal: {empresa[3]}", ""]
    ]
    
    header_table = Table(header_data, colWidths=[4.5*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("GENERAL DE INVENTARIO", title_style))
    elements.append(Spacer(1, 5))
    
    texto_filtros = "Filtros aplicados: " + (", ".join(filtros_aplicados) if filtros_aplicados else "Todos los registros")
    elements.append(Paragraph(texto_filtros, filter_style))
    elements.append(Spacer(1, 10))
    
    col_widths = [1.2*inch, 3.0*inch, 2.0*inch, 1.0*inch]
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
    
    elements.append(Paragraph(f"TOTAL REGISTROS: {total_registros}", footer_style))
    
    doc.build(elements)
    return ruta_salida