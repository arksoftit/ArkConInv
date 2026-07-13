import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.embedded_db import get_db_connection
from core.system_info import get_current_user, get_machine_name
from datetime import datetime

def convertir_moneda(costo, moneda_origen, factor):
    """Aplica tabla de conversión: Local↔Referencial"""
    if not costo or costo == 0:
        return 0.0, 0.0
    
    factor = float(factor) if factor else 1.0
    
    if moneda_origen == 1:  # Local
        costo_local = costo
        costo_referencial = costo / factor if factor > 0 else 0.0
    elif moneda_origen == 2:  # Referencial
        costo_local = costo * factor
        costo_referencial = costo
    else:
        costo_local = costo
        costo_referencial = costo
    
    return costo_local, costo_referencial

def obtener_costo_fiscal(cursor, codigo, fecha_periodo):
    """Obtiene costo fiscal de ark_costos para una fecha específica"""
    cursor.execute("""
        SELECT cts_dtc_costo, cts_dtc_moneda, cts_dtc_factorcambio,
               cts_dtv_costo, cts_dtv_moneda, cts_dtv_factorcambio,
               cts_dti_costo, cts_dti_moneda, cts_dti_factorcambio
        FROM ark_costos
        WHERE cts_codigo = ?
          AND cts_periodo_desde <= ?
          AND cts_periodo_hasta >= ?
        ORDER BY cts_periodo_desde DESC
        LIMIT 1
    """, (codigo, fecha_periodo, fecha_periodo))
    
    row = cursor.fetchone()
    if not row:
        return 0.0, 0.0, 1.0
    
    dtc_costo, dtc_moneda, dtc_factor, dtv_costo, dtv_moneda, dtv_factor, dti_costo, dti_moneda, dti_factor = row
    
    # Jerarquía: Compra > Venta > Inventario
    if dtc_costo and dtc_costo > 0:
        return convertir_moneda(dtc_costo, dtc_moneda or 1, dtc_factor)
    elif dtv_costo and dtv_costo > 0:
        return convertir_moneda(dtv_costo, dtv_moneda or 1, dtv_factor)
    elif dti_costo and dti_costo > 0:
        return convertir_moneda(dti_costo, dti_moneda or 1, dti_factor)
    
    return 0.0, 0.0, 1.0

def calcular_movimientos_periodo(cursor, uo_codigo, fecha_ini, fecha_fin):
    """Calcula movimientos de un periodo específico"""
    tipos_entrada = [2, 4, 6, 8, 12]  # Cargos, Ajustes+, Compras, Notas Prov, Dev Ventas
    tipos_salida = [3, 7, 11, 13]  # Descargos, Dev Compras, Ventas, Notas Entrega
    tipos_traslado = [1]
    
    query = """
        SELECT codigo, tipooperacion, cantidad, uo_codigo, deposito, deposito_destino
        FROM (
            SELECT dtv_codigo as codigo, dtv_tipooperacion as tipooperacion, dtv_cantidad as cantidad,
                   dtv_uo_Codigo as uo_codigo, dtv_depositosource as deposito, NULL as deposito_destino
            FROM ark_detalletranvtas
            WHERE dtv_tipooperacion IN (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
              AND dtv_fechaoperacion BETWEEN ? AND ?
            
            UNION ALL
            
            SELECT dtc_codigo, dtc_tipooperacion, dtc_cantidad, dtc_uo_Codigo, dtc_depositosource, NULL
            FROM ark_detalletrancomp
            WHERE dtc_tipooperacion IN (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
              AND dtc_fechaoperacion BETWEEN ? AND ?
            
            UNION ALL
            
            SELECT dti_codigo, dti_tipooperacion, dti_cantidad, dti_uo_Codigo, dti_depositosource, dti_depositotarget
            FROM ark_detalletraninv
            WHERE dti_tipooperacion IN (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
              AND dti_fechaoperacion BETWEEN ? AND ?
        )
        WHERE uo_codigo = ?
    """
    
    params = (tipos_entrada + tipos_salida + tipos_traslado + 
              [fecha_ini, fecha_fin] * 3 + [uo_codigo])
    
    cursor.execute(query, params)
    return cursor.fetchall()

def calcular_existencia_inicial_periodo(periodo_id, uo_id, deposito_id):
    """
    Motor de backcasting escalado por periodos.
    Retrocede desde la existencia actual hasta el periodo objetivo.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Obtener información del periodo objetivo
    cursor.execute("""
        SELECT pdo_fecha_ini, pdo_fecha_fin, pdo_uo_Codigo
        FROM ark_periodos
        WHERE pdo_Idauto = ?
    """, (periodo_id,))
    periodo_objetivo = cursor.fetchone()
    
    if not periodo_objetivo:
        conn.close()
        return []
    
    fecha_objetivo_ini, fecha_objetivo_fin, uo_codigo = periodo_objetivo
    
    # 2. Obtener todos los periodos desde el objetivo hasta el presente (ordenados descendente)
    cursor.execute("""
        SELECT pdo_Idauto, pdo_fecha_ini, pdo_fecha_fin, pdo_anio
        FROM ark_periodos
        WHERE pdo_uo_Codigo = ?
          AND pdo_fecha_fin >= ?
          AND pdo_status = 1
        ORDER BY pdo_fecha_fin DESC
    """, (uo_codigo, fecha_objetivo_ini))
    
    periodos = cursor.fetchall()
    
    if not periodos:
        conn.close()
        return []
    
    # 3. Obtener existencia actual (foto del 26-05-2026)
    cursor.execute("""
        SELECT exa_codigoproducto, exa_codigodeposito, exa_existencia
        FROM ark_existencia_actual
        WHERE exa_uo_Codigo = ?
    """, (uo_codigo,))
    
    existencia_actual = {}
    for row in cursor.fetchall():
        codigo, deposito, cantidad = row
        clave = (codigo, deposito)
        existencia_actual[clave] = cantidad or 0.0
    
    # 4. Procesar periodo por periodo (backcasting)
    resultados_periodos = {}
    saldo_actual = dict(existencia_actual)  # Copia para ir retrocediendo
    
    for periodo in periodos:
        pdo_id, pdo_ini, pdo_fin, pdo_anio = periodo
        movimientos = calcular_movimientos_periodo(cursor, uo_codigo, pdo_ini, pdo_fin)
        
        # Consolidar movimientos por (codigo, deposito)
        movimientos_consolidados = {}
        for mov in movimientos:
            codigo, tipo, cantidad, uo, dep_origen, dep_destino = mov
            cantidad = float(cantidad) if cantidad else 0.0
            
            if tipo == 1:  # Traslado
                if dep_origen:
                    clave = (codigo, dep_origen)
                    if clave not in movimientos_consolidados:
                        movimientos_consolidados[clave] = {'entradas': 0.0, 'salidas': 0.0}
                    movimientos_consolidados[clave]['salidas'] += cantidad
                
                if dep_destino:
                    clave = (codigo, dep_destino)
                    if clave not in movimientos_consolidados:
                        movimientos_consolidados[clave] = {'entradas': 0.0, 'salidas': 0.0}
                    movimientos_consolidados[clave]['entradas'] += cantidad
            else:
                # Determinar si es entrada o salida
                es_entrada = tipo in [2, 4, 6, 8, 12]
                
                if dep_origen:
                    clave = (codigo, dep_origen)
                    if clave not in movimientos_consolidados:
                        movimientos_consolidados[clave] = {'entradas': 0.0, 'salidas': 0.0}
                    
                    if es_entrada:
                        movimientos_consolidados[clave]['entradas'] += cantidad
                    else:
                        movimientos_consolidados[clave]['salidas'] += cantidad
        
        # Calcular saldo inicial para cada producto en este periodo
        for clave, movs in movimientos_consolidados.items():
            codigo, deposito = clave
            
            if deposito_id != "0" and deposito != deposito_id:
                continue
            
            # Fórmula inversa: Inicial = Final - Entradas + Salidas
            final_periodo = saldo_actual.get(clave, 0.0)
            entradas = movs['entradas']
            salidas = movs['salidas']
            inicial_teorico = final_periodo - entradas + salidas
            
            # Aplicar ajuste si es negativo (Opción A: ajuste automático al cero)
            ajuste = 0.0
            if inicial_teorico < 0:
                ajuste = abs(inicial_teorico)
                inicial_teorico = 0.0
            
            # Obtener costo fiscal
            costo_local, costo_referencial, factor = obtener_costo_fiscal(cursor, codigo, pdo_ini)
            
            # Calcular valores monetarios
            valor_inicial_local = inicial_teorico * costo_local
            valor_inicial_referencial = inicial_teorico * costo_referencial
            valor_final_local = final_periodo * costo_local
            valor_final_referencial = final_periodo * costo_referencial
            
            # Guardar resultado
            if pdo_id not in resultados_periodos:
                resultados_periodos[pdo_id] = []
            
            resultados_periodos[pdo_id].append({
                'pdo_id': pdo_id,
                'pdo_anio': pdo_anio,
                'pdo_fecha_ini': pdo_ini,
                'pdo_fecha_fin': pdo_fin,
                'uo_codigo': uo_codigo,
                'deposito_codigo': deposito,
                'codigo_producto': codigo,
                'existencia_final': final_periodo,
                'cant_entradas': entradas,
                'cant_salidas': salidas,
                'inicial_teorico': inicial_teorico,
                'ajuste_requerido': ajuste,
                'inicial_ajustado': inicial_teorico + ajuste,
                'costo_local': costo_local,
                'costo_referencial': costo_referencial,
                'factor': factor,
                'valor_inicial_local': valor_inicial_local,
                'valor_inicial_referencial': valor_inicial_referencial,
                'valor_final_local': valor_final_local,
                'valor_final_referencial': valor_final_referencial
            })
        
        # Actualizar saldo_actual para el siguiente periodo (retroceder)
        for clave, movs in movimientos_consolidados.items():
            codigo, deposito = clave
            final_periodo = saldo_actual.get(clave, 0.0)
            entradas = movs['entradas']
            salidas = movs['salidas']
            inicial_teorico = final_periodo - entradas + salidas
            
            if inicial_teorico < 0:
                inicial_teorico = 0.0
            
            saldo_actual[clave] = inicial_teorico
    
    conn.close()
    
    # Retornar solo los resultados del periodo objetivo
    return resultados_periodos.get(periodo_id, [])