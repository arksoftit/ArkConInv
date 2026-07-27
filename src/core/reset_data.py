import os
import getpass
from datetime import datetime
from db.embedded_db import get_db_connection

TABLAS_RESET = {
    "Transacciones": [
        ("ark_transacciones", "Cabecera de transacciones"),
        ("ark_detalletranvtas", "Detalle de ventas"),
        ("ark_detalletrancomp", "Detalle de compras"),
        ("ark_detalletraninv", "Detalle de movimientos de inventario"),
    ],
    "Existencias": [
        ("ark_existencia_calculadas", "Existencias calculadas"),
        ("ark_existencia_periodo", "Existencias por período"),
        ("ark_existencia_historico", "Existencias histórico"),
        ("ark_existencia_actual", "Existencias actual"),
    ],
    "Costos": [
        ("ark_costos", "Costos de productos"),
    ],
}

ORDEN_ELIMINACION = [
    "ark_detalletranvtas",
    "ark_detalletrancomp",
    "ark_detalletraninv",
    "ark_transacciones",
    "ark_existencia_calculadas",
    "ark_existencia_periodo",
    "ark_existencia_historico",
    "ark_existencia_actual",
    "ark_costos",
]


def obtener_conteo_tablas():
    conteo = {}
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for grupo, tablas in TABLAS_RESET.items():
            for tabla, _ in tablas:
                cursor.execute(f"SELECT COUNT(*) FROM {tabla};")
                conteo[tabla] = cursor.fetchone()[0]
        conn.close()
    except Exception as e:
        raise Exception(f"Error al contar registros: {e}")
    return conteo


def ejecutar_reset(tablas_seleccionadas):
    if not tablas_seleccionadas:
        raise ValueError("No se han seleccionado tablas para limpiar.")

    tablas_ordenadas = [t for t in ORDEN_ELIMINACION if t in tablas_seleccionadas]

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF;")

        datos_eliminados = []
        total_eliminados = 0

        for tabla in tablas_ordenadas:
            cursor.execute(f"DELETE FROM {tabla};")
            eliminados = cursor.rowcount
            total_eliminados += eliminados
            datos_eliminados.append((tabla, eliminados))

        for tabla in tablas_ordenadas:
            try:
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name=?;", (tabla,))
            except Exception:
                pass

        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.commit()
        conn.close()

        log_file = _generar_log(datos_eliminados, total_eliminados)

        return {
            "total": total_eliminados,
            "detalle": datos_eliminados,
            "log_file": log_file,
        }
    except Exception as e:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        raise Exception(f"Error al ejecutar el reset: {e}")


def _generar_log(datos_eliminados, total_eliminados):
    try:
        usuario_windows = getpass.getuser()
        ahora = datetime.now()
        fecha_hora = ahora.strftime("%Y-%m-%d %H:%M:%S")
        fecha_archivo = ahora.strftime("%Y%m%d_%H%M%S")

        from core.path_utils import get_project_root
        log_dir = os.path.join(get_project_root(), "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_file = os.path.join(log_dir, f"reset_data_{fecha_archivo}.log")

        with open(log_file, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write("REGISTRO DE LIMPIEZA DE DATOS\n")
            f.write("=" * 70 + "\n")
            f.write(f"Fecha y hora: {fecha_hora}\n")
            f.write(f"Usuario Windows: {usuario_windows}\n")
            f.write("-" * 70 + "\n")
            f.write("TABLAS LIMPIADAS:\n")
            for tabla, cantidad in datos_eliminados:
                f.write(f"  • {tabla}: {cantidad} registros eliminados\n")
            f.write("-" * 70 + "\n")
            f.write(f"TOTAL DE REGISTROS ELIMINADOS: {total_eliminados}\n")
            f.write("=" * 70 + "\n")

        return log_file
    except Exception as e:
        print(f"Error al generar el log: {e}")
        return None