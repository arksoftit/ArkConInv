import pyodbc
import sqlite3
import os
import sys
from datetime import date, datetime, time
# import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.embedded_db import get_db_connection
from core.system_info import get_current_user, get_machine_name

# --------------------IMPORT SOPERATIONINV--------------------
CAMPOS_SOPERACIONINV = [
    'FTI_AUTOINCREMENT', 'FTI_DOCUMENTO', 'FTI_TIPO', 'FTI_STATUS', 'FTI_VISIBLE',
    'FTI_FECHAEMISION', 'FTI_DEPOSITOSOURCE', 'FTI_DEPOSITODESTINO',
    'FTI_TOTALITEMS', 'FTI_TOTALITEMSINICIAL', 'FTI_MONEDA', 'FTI_FACTORCAMBIO',
    'FTI_TOTALCOSTO', 'FTI_TOTALCOSTOREAL', 'FTI_CLASIFICACION', 'FTI_DESCRIPCLASIFY',
    'FTI_USER', 'FTI_AUTORIZADOPOR', 'FTI_PROPOSITO', 'FTI_RESPONSABLE', 'FTI_DETALLE',
    'FTI_TIENELOTES', 'FTI_UPDATEITEMS', 'FTI_TOTALBRUTO', 'FTI_DESCUENTO1PORCENT',
    'FTI_DESCUENTO1MONTO', 'FTI_DESCUENTO1ORIGEN', 'FTI_DESCUENTO2PORCENT',
    'FTI_DESCUENTO2MONTO', 'FTI_DESCUENTO2ORIGEN', 'FTI_DESCUENTOPARCIAL',
    'FTI_FLETEPORCENT', 'FTI_FLETEMONEDA', 'FTI_FLETEORIGEN', 'FTI_BASEIMPONIBLE',
    'FTI_BASEIMPONIBLE2', 'FTI_IMPUESTO1PORCENT', 'FTI_IMPUESTO1MONTO',
    'FTI_IMPUESTO2PORCENT', 'FTI_IMPUESTO2MONTO', 'FTI_DESCUENTOCUADRE',
    'FTI_TOTALNETO', 'FTI_FECHAVENCIDO', 'FTI_DIASVENCIMIENTO', 'FTI_RIFCLIENTE',
    'FTI_NITCLIENTE', 'FTI_PERSONACONTACTO', 'FTI_TELEFONOCONTACTO',
    'FTI_DIRECCIONDESPACHO', 'FTI_DETALLECOMENTARIO', 'FTI_ORDENCOMPRA',
    'FTI_PLANILLAIMPORTACION', 'FTI_EXISTEPLANILLAIMPORTACION',
    'FTI_PORCENTFLETESINASIGNAR', 'FTI_SALDOOPERACION', 'FTI_MONEDAPAGO',
    'FTI_FORMADEPAGO', 'FTI_TOTALPRECIO', 'FTI_VUELTO', 'FTI_AUTORIZADOS',
    'FTI_EXCENTO', 'FTI_COSTODEVENTA', 'FTI_TIPOOPERACIONORIGEN', 'FTI_DOCUMENTOORIGEN',
    'FTI_FROMCOMPUESTOS', 'FTI_VENDEDORASIGNADO', 'FTI_ZONAVENTA',
    'FTI_PENDINGFORPRINT', 'FTI_COBRADORASIGNADO', 'FTI_COMISIONCOBROS',
    'FTI_COMISIONCOBROSBLOQUEADA', 'FTI_FACTURASLOTERANDOM', 'FTI_MULTIPLEVENDEDOR',
    'FTI_MULTIPLEDEPOSITO', 'FTI_TIMESAVED', 'FTI_TIPOPRECIO', 'BASE_AUTOINCREMENT',
    'FTI_SERIE', 'FTI_NAMEFORMATO', 'FTI_MACHINENAME', 'FTI_COMISIONVENTA',
    'FTI_MONTOPAGADO', 'FTI_MONTOPERIODO', 'FTI_PORCENTPERIODO', 'FTI_HORA',
    'FTI_GUIADESPACHO', 'FTI_NORECIBOCAJA', 'FTI_CTOCOSTO', 'FTI_COSTOACTUALNACIONAL',
    'FTI_COSTOACTUALEX', 'FTI_PREFIXINVENTARIO', 'FTI_NUMEROCONTROL',
    'FTI_COSTOAJUSTADO', 'FTI_FACTORREFERENCIA', 'FTI_FINICIAL', 'FTI_FINTERESES',
    'FTI_FINTERESESP', 'FTI_FMANEJO', 'FTI_FMANEJOP', 'FTI_FEXTRAORDINARIA',
    'FTI_FCTDEXTRAORDINARIA', 'FTI_FINTEXTRAORDINARIA', 'FTI_FMTOCUOTA',
    'FTI_FCTDCUOTA', 'FTI_FCOBRANZA', 'FTI_TOTALFINANCIADO', 'FTI_DETALLEGIROS',
    'FTI_SALDOFINANCIAR', 'FTI_PRIMERACUOTA', 'FTI_CAPITALCUOTAEXTRA',
    'FTI_CREDICARD', 'FTI_MAQUINAFISCAL', 'FTI_TOTALPAGINAS', 'FTI_SUCURSALORIGEN',
    'FTI_FECHALIBRO', 'FTI_IVAINTERESES', 'FTI_REIMPRESAFISCAL',
    'FTI_DCTOFISCALORIGEN', 'FTI_FECHAFACTURA', 'FTI_DCTOIVA', 'FTI_MONEDACAMBIO',
    'FTI_TIPOFACTORCAMBIO', 'FTI_ORIGENCAMBIO', 'FTI_FACTORVUELTO', 'FTI_CODECAMBIO',
    'FTI_VUELTOORG', 'FTI_VTANAPAGO', 'FTI_FACTORREFERENCIA2', 'FTI_MULTIVUELTO',
    'FTI_EXTRAFIELD01', 'FTI_EXTRAFIELD02', 'FTI_EXTRAFIELD03', 'FTI_EXTRAFIELD04',
    'FTI_EXTRAFIELD05', 'FTI_BASEIGTF', 'FTI_EXTRAFIELD06', 'FTI_IMPRENTAASIGNACION',
    'FTI_IMPRENTAHORA', 'FTI_STATUSIMPRENTA', 'FTI_IMPRENTADOCORIGEN',
    'FTI_IMPRENTAMOTIVO', 'FTI_IMPRENTAFECHAORIGEN', 'FTI_IMPRENTASERIEORIGEN',
    'FTI_IMPRENTAMTOORIGEN', 'FTI_MTOOTROSCARGOS'
]

CAMPOS_VERSION_H = ['FTI_IMPRENTACORRELATIVO', 'FTI_IMPRENTACONTROLORIGEN']

COLUMNAS_DESTINO = [
    'trn_uo_id', 'trn_uo_Codigo', 'trn_autoincrement', 'trn_documento', 'trn_tipo',
    'trn_status', 'trn_visible', 'trn_fechaemision', 'trn_depositosource',
    'trn_depositodestino', 'trn_totalitems', 'trn_totalitemsinicial', 'trn_moneda',
    'trn_factorcambio', 'trn_totalcosto', 'trn_totalcostoreal', 'trn_clasificacion',
    'trn_descripclasify', 'trn_user', 'trn_autorizadopor', 'trn_proposito',
    'trn_responsable', 'trn_detalle', 'trn_tienelotes', 'trn_updateitems',
    'trn_totalbruto', 'trn_descuento1porcent', 'trn_descuento1monto',
    'trn_descuento1origen', 'trn_descuento2porcent', 'trn_descuento2monto',
    'trn_descuento2origen', 'trn_descuentoparcial', 'trn_fleteporcent',
    'trn_fletemoneda', 'trn_fleteorigen', 'trn_baseimponible', 'trn_baseimponible2',
    'trn_impuesto1porcent', 'trn_impuesto1monto', 'trn_impuesto2porcent',
    'trn_impuesto2monto', 'trn_descuentocuadre', 'trn_totalneto', 'trn_fechavencido',
    'trn_diasvencimiento', 'trn_rifcliente', 'trn_nitcliente', 'trn_personacontacto',
    'trn_telefonocontacto', 'trn_direcciondespacho', 'trn_detallecomentario',
    'trn_ordencompra', 'trn_planillaimportacion', 'trn_existeplanillaimportacion',
    'trn_porcentfletesinasignar', 'trn_saldooperacion', 'trn_monedapago',
    'trn_formadepago', 'trn_totalprecio', 'trn_vuelto', 'trn_autorizados',
    'trn_excento', 'trn_costodeventa', 'trn_tipooperacionorigen', 'trn_documentoorigen',
    'trn_fromcompuestos', 'trn_vendedorasignado', 'trn_zonaventa',
    'trn_pendingforprint', 'trn_cobradorasignado', 'trn_comisioncobros',
    'trn_comisioncobrosbloqueada', 'trn_facturasloterandom', 'trn_multiplevendedor',
    'trn_multipledeposito', 'trn_timesaved', 'trn_tipoprecio', 'base_autoincrement',
    'trn_serie', 'trn_nameformato', 'trn_machinename', 'trn_comisionventa',
    'trn_montopagado', 'trn_montoperiodo', 'trn_porcentperiodo', 'trn_hora',
    'trn_guiadespacho', 'trn_norecibocaja', 'trn_ctocosto', 'trn_costoactualnacional',
    'trn_costoactualex', 'trn_prefixinventario', 'trn_numerocontrol',
    'trn_costoajustado', 'trn_factorreferencia', 'trn_finicial', 'trn_fintereses',
    'trn_finteresesp', 'trn_fmanejo', 'trn_fmanejop', 'trn_fextraordinaria',
    'trn_fctdextraordinaria', 'trn_fintextraordinaria', 'trn_fmtocuota',
    'trn_fctdcuota', 'trn_fcobranza', 'trn_totalfinanciado', 'trn_detallegiros',
    'trn_saldofinanciar', 'trn_primeracuota', 'trn_capitalcuotaextra',
    'trn_credicard', 'trn_maquinafiscal', 'trn_totalpaginas', 'trn_sucursalorigen',
    'trn_fechalibro', 'trn_ivaintereses', 'trn_reimpresafiscal',
    'trn_dctofiscalorigen', 'trn_fechafactura', 'trn_dctoiva', 'trn_monedacambio',
    'trn_tipofactorcambio', 'trn_origencambio', 'trn_factorvuelto', 'trn_codecambio',
    'trn_vueltoorg', 'trn_vtanapago', 'trn_factorreferencia2', 'trn_multivuelto',
    'trn_extrafield01', 'trn_extrafield02', 'trn_extrafield03', 'trn_extrafield04',
    'trn_extrafield05', 'trn_baseigtf', 'trn_extrafield06', 'trn_imprentaasignacion',
    'trn_imprentahora', 'trn_statusimprenta', 'trn_imprentadocorigen',
    'trn_imprentamotivo', 'trn_imprentafechaorigen', 'trn_imprentaserieorigen',
    'trn_imprentamtoorigen', 'trn_mtootroscargos', 'trn_imprentacorrelativo',
    'trn_imprentacontrolorigen', 'trn_SystemDate', 'trn_SystemTime', 'trn_NameMachine',
    'trn_UserCreator', 'trn_LastUpdateDate', 'trn_LastUpdateTime', 'trn_LastMachine',
    'trn_UserLastUpdate'
]

# --------------------IMPORT SDETALLEVENTA--------------------

CAMPOS_SDETALLEVENTA = [
    'FDI_TIPOOPERACION', 'FDI_CODIGO', 'FDI_LINEA', 'FDI_DOCUMENTO',
    'FDI_AUTOINCREMENT', 'FDI_CLIENTEPROVEEDOR', 'FDI_DOCUMENTOORIGEN',
    'FDI_LINEAORIGEN', 'FDI_CLASIFICACION', 'FDI_STATUS', 'FDI_VISIBLE',
    'FDI_COSTO', 'FDI_CANTIDAD', 'FDI_CANTIDADPENDIENTE', 'FDI_LOTE',
    'FDI_LOTERANDOM', 'FDI_NEWLOTE', 'FDI_DEPOSITOSOURCE', 'FDI_DEPOSITOTARGET',
    'FDI_OPERACION_AUTOINCREMENT', 'FDI_DECIMALES', 'FDI_DECIMALESPEN',
    'FDI_SERIALNUMBER', 'FDI_USASERIALES', 'FDI_USADEPOSITOS', 'FDI_COSTOOPERACION',
    'FDI_MEMODETALLE', 'FDI_MONEDA', 'FDI_FACTORCAMBIO',
    'FDI_DETALLECOSTOSIMPORTACION', 'FDI_DETALLEPLANILLAIMPORTACION',
    'FDI_EXISTEDETALLEIMPORTACION', 'FDI_EXISTEDETALLEDECOSTOS',
    'FDI_ALICUOTAFLETEOTROS', 'FDI_IMPUESTO1', 'FDI_PORCENTIMPUESTO1',
    'FDI_MONTOIMPUESTO1', 'FDI_IMPUESTO2', 'FDI_PORCENTIMPUESTO2',
    'FDI_MONTOIMPUESTO2', 'FDI_ORIGENPRICE', 'FDI_PORCENTDESCPARCIAL',
    'FDI_DESCUENTOPARCIAL', 'FDI_PRECIOSINDESCUENTO', 'FDI_PRECIOCONDESCUENTO',
    'FDI_PRECIODEVENTA', 'FDI_ROUNDDESCTPARCIAL', 'FDI_COMISIONFIJA',
    'FDI_COMISIONFIJAP', 'FDI_UNDDESCARGA', 'FDI_UNDCAPACIDAD', 'FDI_UNDDETALLADA',
    'FDI_INDEXPRICES', 'FDI_PARTESUSANSERIALES', 'FDI_COSTODEVENTAS',
    'FDI_DESCRIPCIONOFERTA', 'FDI_VENDEDORASIGNADO', 'FDI_MONTOCOMISION',
    'FDI_PRECIOBASECOMISION', 'FDI_COMISIONBLOQUEADA', 'FDI_COMISIONYAPAGADA',
    'FDI_DOCUMENTOLIBERACION', 'FDI_TIPODECOMISION', 'FDI_PRICEFORCOMISION',
    'FDI_FECHAOPERACION', 'FDI_USER', 'FDI_PORCENTDESCUENTO1',
    'FDI_PORCENTDESCUENTO2', 'FDI_COSTOSUPDATE', 'BASE_AUTOINCREMENT',
    'FDI_TOTALPESO', 'FDI_CTOCOSTO', 'FDI_AUTORIZADO', 'FDI_MARKPERIODO',
    'FDI_CTOCOSTOSTR', 'FDI_COSTOACTUALNACIONAL', 'FDI_COSTOACTUALEXT',
    'FDI_PREFIXINVENTARIO', 'FDI_COSTOAJUSTADO', 'FDI_FECHALIBRO',
    'FDI_MONTOLIQUIDADO', 'FDI_TIPODOCUMENTOORIGEN', 'FDI_STATUSDOCUMENTOORIGEN',
    'FDI_DCTOIVA', 'FDI_MONTOIMPUESTO1DCTO', 'FDI_PRECIODEVENTADCTO'
]

COLUMNAS_DESTINO_DTV = [
    'dtv_Idauto', 'dtv_uo_id', 'dtv_uo_Codigo', 'dtv_tipooperacion', 'dtv_codigo',
    'dtv_linea', 'dtv_documento', 'dtv_autoincrement', 'dtv_clienteproveedor',
    'dtv_documentoorigen', 'dtv_lineaorigen', 'dtv_clasificacion', 'dtv_status',
    'dtv_visible', 'dtv_costo', 'dtv_cantidad', 'dtv_cantidadpendiente', 'dtv_lote',
    'dtv_loterandom', 'dtv_newlote', 'dtv_depositosource', 'dtv_depositotarget',
    'dtv_operacion_autoincrement', 'dtv_decimales', 'dtv_decimalespen',
    'dtv_serialnumber', 'dtv_usaseriales', 'dtv_usadepositos', 'dtv_costooperacion',
    'dtv_memodetalle', 'dtv_moneda', 'dtv_factorcambio',
    'dtv_detallecostosimportacion', 'dtv_detalleplanillaimportacion',
    'dtv_existedetalleimportacion', 'dtv_existedetalledecostos',
    'dtv_alicuotafleteotros', 'dtv_impuesto1', 'dtv_porcentimpuesto1',
    'dtv_montoimpuesto1', 'dtv_impuesto2', 'dtv_porcentimpuesto2', 'dtv_montoimpuesto2',
    'dtv_origenprice', 'dtv_porcentdescparcial', 'dtv_descuentoparcial',
    'dtv_preciosindescuento', 'dtv_preciocondescuento', 'dtv_preciodeventa',
    'dtv_rounddesctparcial', 'dtv_comisionfija', 'dtv_comisionfijap',
    'dtv_unddescarga', 'dtv_undcapacidad', 'dtv_unddetallada', 'dtv_indexprices',
    'dtv_partesusanseriales', 'dtv_costodeventas', 'dtv_descripcionoferta',
    'dtv_vendedorasignado', 'dtv_montocomision', 'dtv_preciobasecomision',
    'dtv_comisionbloqueada', 'dtv_comisionyapagada', 'dtv_documentoliberacion',
    'dtv_tipodecomision', 'dtv_priceforcomision', 'dtv_fechaoperacion', 'dtv_user',
    'dtv_porcentdescuento1', 'dtv_porcentdescuento2', 'dtv_costosupdate',
    'dtv_base_autoincrement', 'dtv_totalpeso', 'dtv_ctocosto', 'dtv_autorizado',
    'dtv_markperiodo', 'dtv_ctocostostr', 'dtv_costoactualnacional',
    'dtv_costoactualext', 'dtv_prefixinventario', 'dtv_costoajustado', 'dtv_fechalibro',
    'dtv_montoliquidado', 'dtv_tipodocumentoorigen', 'dtv_statusdocumentoorigen',
    'dtv_dctoiva', 'dtv_montoimpuesto1dcto', 'dtv_preciodeventadcto',
    'dtv_SystemDate', 'dtv_SystemTime', 'dtv_NameMachine', 'dtv_UserCreator',
    'dtv_LastUpdateDate', 'dtv_LastUpdateTime', 'dtv_LastMachine', 'dtv_UserLastUpdate'
]

# def importar_transacciones(uo_id, uo_codigo, uo_nombre, fecha_desde, fecha_hasta, deposito_id, status_valor, tablas, dsn, usuario, password):
def importar_transacciones(uo_id, uo_codigo, uo_nombre, fecha_desde, fecha_hasta, deposito_id, status_valor, tablas, dsn, usuario, password, callback_progreso=None):
    try:
        conn_str = f"DSN={dsn};UID={usuario};PWD={password};"
        dbisam_conn = pyodbc.connect(conn_str, autocommit=True)
        cursor_dbisam = dbisam_conn.cursor()

        resultados = []
        
        # Procesar SOperacionInv si está en la lista
        if "SOperacionInv" in tablas:
            cursor_dbisam.execute("SELECT * FROM SOperacionInv")
            num_campos = len([desc[0] for desc in cursor_dbisam.description])
            version = "H" if num_campos == 147 else "A"

            campos_origen = list(CAMPOS_SOPERACIONINV)
            if version == "H":
                campos_origen.extend(CAMPOS_VERSION_H)

            query_dbisam = f"SELECT {', '.join(campos_origen)} FROM SOperacionInv WHERE FTI_FECHAEMISION >= '{fecha_desde}' AND FTI_FECHAEMISION <= '{fecha_hasta}'"
            
            if deposito_id != 0:
                query_dbisam += f" AND (FTI_DEPOSITOSOURCE = {deposito_id} OR FTI_DEPOSITODESTINO = {deposito_id})"
            
            if status_valor is not None:
                query_dbisam += f" AND FTI_STATUS = {status_valor}"

            cursor_dbisam.execute(query_dbisam)
            rows = cursor_dbisam.fetchall()
            total = len(rows)

            sqlite_conn = get_db_connection()
            sqlite_cursor = sqlite_conn.cursor()

            placeholders = ', '.join(['?'] * len(COLUMNAS_DESTINO))
            query_sqlite = f"INSERT OR IGNORE INTO ark_transacciones ({', '.join(COLUMNAS_DESTINO)}) VALUES ({placeholders})"

            user_creator = get_current_user()
            machine_name = get_machine_name()
            sys_date = date.today().isoformat()
            sys_time = datetime.now().strftime("%H:%M:%S")
            
            audit_values = [sys_date, sys_time, machine_name, user_creator, sys_date, sys_time, machine_name, user_creator]

            for i, row in enumerate(rows):
                data = [uo_id, uo_codigo]
                
                for value in row:
                    if isinstance(value, (bytes, bytearray)):
                        data.append(value.decode('utf-8', errors='replace'))
                    elif type(value).__name__ == 'Decimal':
                        data.append(float(value) if value is not None else None)
                    elif isinstance(value, datetime):
                        data.append(value.isoformat())
                    elif isinstance(value, date):
                        data.append(value.isoformat())
                    elif isinstance(value, time):
                        data.append(value.strftime("%H:%M:%S"))
                    else:
                        data.append(value)
                
                if version == "A":
                    data.extend(["Ver. A", "Ver. A"])
                
                data.extend(audit_values)
                sqlite_cursor.execute(query_sqlite, data)
                
                if (i + 1) % 50 == 0 or i == total - 1:
                    porcentaje = int(((i + 1) / total) * 100)
                    if callback_progreso:
                        callback_progreso(porcentaje, f"Importando transacciones {i + 1} de {total}...")

            sqlite_conn.commit()
            sqlite_conn.close()
            
            resultados.append(f"Transacciones: {total} registros (Versión {version})")

        # Procesar SDetalleVenta si está en la lista
        if "SDetalleVenta" in tablas:
            resultado_detalle = importar_sdetalleventa(
                uo_id, uo_codigo, uo_nombre,
                fecha_desde, fecha_hasta, deposito_id,
                dsn, usuario, password, callback_progreso
            )
            resultados.append(resultado_detalle)

        dbisam_conn.close()

        return f"Importación completada.\n" + "\n".join(resultados)

    except Exception as e:
        raise e


def importar_sdetalleventa(uo_id, uo_codigo, uo_nombre, fecha_desde, fecha_hasta, deposito_id, dsn, usuario, password, callback_progreso=None):
    try:
        conn_str = f"DSN={dsn};UID={usuario};PWD={password};"
        dbisam_conn = pyodbc.connect(conn_str, autocommit=True)
        cursor_dbisam = dbisam_conn.cursor()

        query_dbisam = f"""
            SELECT {', '.join(CAMPOS_SDETALLEVENTA)}
            FROM SDetalleVenta d
            INNER JOIN SOperacionInv c ON d.FDI_OPERACION_AUTOINCREMENT = c.FTI_AUTOINCREMENT
            WHERE c.FTI_FECHAEMISION >= '{fecha_desde}' AND c.FTI_FECHAEMISION <= '{fecha_hasta}'
        """
        
        if deposito_id != 0:
            query_dbisam += f" AND (d.FDI_DEPOSITOSOURCE = {deposito_id} OR d.FDI_DEPOSITOTARGET = {deposito_id})"

        cursor_dbisam.execute(query_dbisam)
        rows = cursor_dbisam.fetchall()
        total = len(rows)
        dbisam_conn.close()

        sqlite_conn = get_db_connection()
        sqlite_cursor = sqlite_conn.cursor()

        placeholders = ', '.join(['?'] * len(COLUMNAS_DESTINO_DTV))
        query_sqlite = f"INSERT OR IGNORE INTO ark_detalletranvtas ({', '.join(COLUMNAS_DESTINO_DTV)}) VALUES ({placeholders})"

        user_creator = get_current_user()
        machine_name = get_machine_name()
        sys_date = date.today().isoformat()
        sys_time = datetime.now().strftime("%H:%M:%S")
        
        audit_values = [sys_date, sys_time, machine_name, user_creator, sys_date, sys_time, machine_name, user_creator]

        for i, row in enumerate(rows):
            # dtv_Idauto es AUTOINCREMENT, no se inserta
            # dtv_uo_id y dtv_uo_Codigo se agregan manualmente
            data = [uo_id, uo_codigo]
            
            for value in row:
                if isinstance(value, (bytes, bytearray)):
                    # Campos BLOB: FDI_DETALLECOSTOSIMPORTACION, FDI_DETALLEPLANILLAIMPORTACION
                    data.append(value.decode('utf-8', errors='replace'))
                elif type(value).__name__ == 'Decimal':
                    data.append(float(value) if value is not None else None)
                elif isinstance(value, datetime):
                    data.append(value.isoformat())
                elif isinstance(value, date):
                    data.append(value.isoformat())
                elif isinstance(value, time):
                    data.append(value.strftime("%H:%M:%S"))
                else:
                    data.append(value)
            
            data.extend(audit_values)
            sqlite_cursor.execute(query_sqlite, data)
            
            if (i + 1) % 50 == 0 or i == total - 1:
                porcentaje = int(((i + 1) / total) * 100)
                if callback_progreso:
                    callback_progreso(porcentaje, f"Importando detalle de ventas {i + 1} de {total}...")

        sqlite_conn.commit()
        sqlite_conn.close()

        return f"Detalle de Ventas: {total} registros importados"

    except Exception as e:
        raise e
    
