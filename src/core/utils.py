def formato_monto(valor):
    """Formatea un valor numérico como monto monetario con 4 decimales."""
    return round(float(valor) if valor is not None else 0.0, 4)

def formato_cantidad(valor):
    """Formatea un valor numérico como cantidad con 3 decimales."""
    return round(float(valor) if valor is not None else 0.0, 3)