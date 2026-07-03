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
    
    # query incluyendo NULL as destino para mantener la unión limpia y compatible
    query = f"""
    WITH movimientos AS (
        SELECT dtv_codigo as codigo, dtv_tipooperacion as tipooperacion, dtv_cantidad as cantidad, dtv_uo_Codigo as uo_codigo, dtv_depositosource as deposito, NULL as deposito_destino
        FROM ark_detalletranvtas WHERE dtv_tipooperacion IN ({placeholders}) AND dtv_fechaoperacion BETWEEN ? AND ?
        UNION ALL
        SELECT dtc_codigo as codigo, dtc_tipooperacion as tipooperacion, dtc_cantidad as cantidad, dtc_uo_Codigo as uo_codigo, dtc_depositosource as deposito, NULL as deposito_destino
        FROM ark_detalletrancomp WHERE dtc_tipooperacion IN ({placeholders}) AND dtc_fechaoperacion BETWEEN ? AND ?
        UNION ALL
        SELECT dti_codigo as codigo, dti_tipooperacion as tipooperacion, dti_cantidad as cantidad, dti_uo_Codigo as uo_codigo, dti_depositosource as deposito, dti_depositotarget as deposito_destino
        FROM ark_detalletraninv WHERE dti_tipooperacion IN ({placeholders}) AND dti_fechaoperacion BETWEEN ? AND ?
    ),
    agregado AS (
        SELECT codigo, tipooperacion, SUM(cantidad) as total_cantidad, uo_codigo, deposito, deposito_destino
        FROM movimientos WHERE 1=1
    """
    
    params = tipos_numeros + [fecha_desde, fecha_hasta] + tipos_numeros + [fecha_desde, fecha_hasta] + tipos_numeros + [fecha_desde, fecha_hasta]
    
    if uo_id != "0":
        query += " AND uo_codigo = (SELECT uo_Codigo FROM ark_unds_operativas WHERE uo_id = ?)"
        params.append(uo_id)
    
    if deposito_id != "0":
        # Si hay filtro de depósito, se evalúa si afectó como origen o como destino en transferencias
        query += " AND (deposito = ? OR (tipooperacion = 1 AND deposito_destino = ?))"
        params.extend([deposito_id, deposito_id])
   
    query += """
        GROUP BY codigo, tipooperacion, uo_codigo, deposito, deposito_destino
    )
    SELECT a.codigo, i.inv_descripcion, a.tipooperacion, a.total_cantidad, a.deposito, a.deposito_destino
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
        dep_origen = str(row[4]) if row[4] else ""
        dep_destino = str(row[5]) if row[5] else ""
        
        if codigo not in productos:
            productos[codigo] = {
                'descripcion': descripcion, 
                'tipos': {}, 
                'trans_detalles': [] # Estructura interna para separar los flujos dobles
            }
            
        if tipo == 1:
            # Almacenamos el par de depósitos junto con la cantidad para procesarla en el bucle visual
            productos[codigo]['trans_detalles'].append({
                'cantidad': cantidad,
                'origen': dep_origen,
                'destino': dep_destino
            })
        else:
            productos[codigo]['tipos'][tipo] = cantidad
    
    elements = []
    elements.append(_crear_encabezado(empresa, fecha_str, hora_str, usar_landscape=True))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("MOVIMIENTO DE INVENTARIO", estilos['title']))
    elements.append(Spacer(1, 5))
    
    filtros_texto = [f"UO: {uo_nombre}", f"Período: {fecha_desde} al {fecha_hasta}", f"Depósito: {deposito_nombre}"]
    if tipos:
        nombres = [t.replace('_', ' ').title() for t in tipos]
        filtros_texto.append(f"Tipos: {', '.join(nombres)}")
    
    elements.append(Paragraph(f"Filtros applied: {', '.join(filtros_texto)}", estilos['filter']))
    elements.append(Spacer(1, 10))
    
    col_widths = [1.0*inch, 2.07*inch, 0.75*inch, 0.75*inch, 0.85*inch, 0.85*inch, 0.75*inch, 0.75*inch, 0.75*inch, 0.75*inch, 0.83*inch]
    table_data = [['Código', 'Descripción', 'Cargos', 'Descargos', 'Trans.(+)', 'Trans. (-)', 'Facturas', 'N/E Vta', 'Compras', 'N/E Comp', 'Total']]
    
    total_cargos = total_descargos = total_trans_pos = total_trans_neg = total_facturas = total_ne_vta = total_compras = total_ne_comp = total_general = 0.0
    total_registros = 0
    
    for codigo, data in sorted(productos.items()):
        t_data = data['tipos']
        
        cargos = abs(t_data.get(2, 0.0))
        compras = abs(t_data.get(6, 0.0))
        ne_comp = abs(t_data.get(8, 0.0))
        descargos = -abs(t_data.get(3, 0.0)) if t_data.get(3, 0.0) != 0 else 0.0
        facturas = -abs(t_data.get(11, 0.0)) if t_data.get(11, 0.0) != 0 else 0.0
        ne_vta = -abs(t_data.get(13, 0.0)) if t_data.get(13, 0.0) != 0 else 0.0
        
        # Calcular Transferencias Positivas y Negativas basado en el rol de los depósitos
        trans_pos = 0.0
        trans_neg = 0.0
        
        for trans in data['trans_detalles']:
            cant = trans['cantidad']
            orig = trans['origen']
            dest = trans['destino']
            
            if deposito_id != "0":
                # Si se filtra por depósito específico:
                if orig == deposito_id:
                    trans_neg -= cant  # Funciona como Origen: RESTA
                if dest == deposito_id:
                    trans_pos += cant  # Funciona como Destino: SUMA
            else:
                # Si se listan Todos los Depósitos, se muestran ambas caras simultáneamente
                trans_pos += cant
                trans_neg -= cant

        total = cargos + descargos + trans_pos + trans_neg + facturas + ne_vta + compras + ne_comp
        
        table_data.append([
            str(codigo)[:15], str(data['descripcion'])[:25],
            f"{cargos:,.2f}", f"{descargos:,.2f}", f"{trans_pos:,.2f}", f"{trans_neg:,.2f}",
            f"{facturas:,.2f}", f"{ne_vta:,.2f}", f"{compras:,.2f}", f"{ne_comp:,.2f}", f"{total:,.2f}"
        ])
        
        total_cargos += cargos
        total_descargos += descargos
        total_trans_pos += trans_pos
        total_trans_neg += trans_neg
        total_facturas += facturas
        total_ne_vta += ne_vta
        total_compras += compras
        total_ne_comp += ne_comp
        total_general += total
        total_registros += 1
    
    table_data.append(['', 'TOTALES:', f"{total_cargos:,.2f}", f"{total_descargos:,.2f}", f"{total_trans_pos:,.2f}", f"{total_trans_neg:,.2f}", f"{total_facturas:,.2f}", f"{total_ne_vta:,.2f}", f"{total_compras:,.2f}", f"{total_ne_comp:,.2f}", f"{total_general:,.2f}"])
    
    data_table = Table(table_data, colWidths=col_widths)
    data_table.setStyle(TableStyle([
        # Fondo Azul base para las columnas de texto y el total final
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#4472C4')),   # Código y Descripción
        ('BACKGROUND', (10, 0), (10, 0), colors.HexColor('#4472C4')), # Total General
        
        # ASIGNACIÓN PRECISA DE COLORES PARA LAS CABECERAS
        ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#008000')),   # Verde para Cargos
        ('BACKGROUND', (3, 0), (3, 0), colors.HexColor('#FFA500')),   # Naranja para Descargos
        ('BACKGROUND', (4, 0), (4, 0), colors.HexColor('#008000')),   # Verde para Trans.(+)
        ('BACKGROUND', (5, 0), (5, 0), colors.HexColor('#FFA500')),   # Naranja para Trans. (-)
        ('BACKGROUND', (6, 0), (7, 0), colors.HexColor('#FFA500')),   # Naranja para Facturas y N/E Vta
        ('BACKGROUND', (8, 0), (9, 0), colors.HexColor('#008000')),   # Verde para Compras y N/E Comp
        
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