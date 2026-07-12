import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.embedded_db import get_db_connection
from core.system_info import get_date_audit, get_current_user, get_machine_name, get_app_version

def calcular_existencia_inicial_periodo(periodo_id, uo_id, deposito_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    uo_codigo_filtro = None
    if uo_id != "0":
        cursor.execute("SELECT uo_Codigo FROM ark_unds_operativas WHERE uo_id = ?", (int(uo_id),))
        row = cursor.fetchone()
        if row:
            uo_codigo_filtro = row[0]
        else:
            conn.close()
            return []

    deposito_codigo_filtro = None
    if deposito_id != "0":
         cursor.execute("SELECT dep_codigo FROM ark_depositos WHERE dep_IDauto = ?", (int(deposito_id),))
         row = cursor.fetchone()
         if row:
             deposito_codigo_filtro = row[0]
         else:
             conn.close()
             return []

    query = """
    SELECT
        e_act.exa_codigoproducto,
        COALESCE(inv.inv_descripcion, 'Producto no encontrado') AS descripcion_producto,
        e_act.exa_uo_Codigo,
        d.dep_codigo AS deposito_codigo_texto,
        d.dep_descripcion AS deposito_nombre,
        e_act.exa_existencia AS existencia_actual,
        COALESCE(e_calc.exc_compras, 0) +
        COALESCE(e_calc.exc_nota_entrega_proveedor, 0) +
        COALESCE(e_calc.exc_dev_ventas, 0) +
        COALESCE(e_calc.exc_transferencias_mas, 0) +
        COALESCE(e_calc.exc_cargos, 0) +
        COALESCE(e_calc.exc_ajustes_mas, 0) AS entradas,

        COALESCE(e_calc.exc_ventas, 0) +
        COALESCE(e_calc.exc_nota_entrega_clientes, 0) +
        COALESCE(e_calc.exc_dev_compras, 0) +
        COALESCE(e_calc.exc_transferencias_menos, 0) +
        COALESCE(e_calc.exc_descargos, 0) +
        COALESCE(e_calc.exc_ajustes_menos, 0) AS salidas

    FROM ark_existencia_actual e_act
    LEFT JOIN ark_existencia_calculadas e_calc
        ON e_act.exa_codigoproducto = e_calc.exc_item_codigo
        AND e_act.exa_uo_Codigo = e_calc.exc_uo_Codigo
        AND e_act.exa_codigodeposito = e_calc.exc_dep_codigo
    LEFT JOIN ark_inventario inv
        ON e_act.exa_codigoproducto = inv.inv_codigo
    LEFT JOIN ark_depositos d
        ON e_act.exa_codigodeposito = d.dep_codigo
    WHERE 1=1
    """

    params = []
    if uo_codigo_filtro:
        query += " AND e_act.exa_uo_Codigo = ?"
        params.append(uo_codigo_filtro)
    if deposito_codigo_filtro:
        query += " AND e_act.exa_codigodeposito = ?"
        params.append(deposito_codigo_filtro)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    resultados = []
    for row in rows:
        codigo_producto = row[0]
        descripcion_producto = row[1]
        uo_codigo = row[2]
        deposito_codigo_texto = row[3]
        existencia_actual = row[5] or 0.0
        entradas = row[6] or 0.0
        salidas = row[7] or 0.0

        saldo_inicial = existencia_actual - entradas + salidas

        resultados.append({
            'codigo_producto': codigo_producto,
            'descripcion_producto': descripcion_producto,
            'uo_codigo': uo_codigo,
            'deposito_codigo': deposito_codigo_texto,
            'existencia_actual': existencia_actual,
            'entradas': entradas,
            'salidas': salidas,
            'saldo_inicial_calculado': saldo_inicial
        })

    conn.close()
    return resultados