def _es_numero(token: str) -> bool:
    try:
        float(token.replace(",", "."))
        return True
    except ValueError:
        return False


# Formato: [placa] monto_total [monto_pendiente]p descripción
def parsear_servicio(texto: str):
    tokens = texto.split()
    if not tokens:
        return None

    idx = 0
    placa = None
    if not _es_numero(tokens[0]):
        placa = tokens[0].upper()
        idx = 1

    if idx >= len(tokens) or not _es_numero(tokens[idx]):
        return None
    total_amount = float(tokens[idx].replace(",", "."))
    idx += 1

    pending_amount = 0.0
    if idx < len(tokens):
        tok = tokens[idx]
        if tok.lower().endswith("p") and _es_numero(tok[:-1]):
            pending_amount = float(tok[:-1].replace(",", "."))
            idx += 1

    descripcion = " ".join(tokens[idx:]).strip()
    if not descripcion or pending_amount > total_amount:
        return None

    return {
        "placa": placa,
        "total_amount": total_amount,
        "pending_amount": pending_amount,
        "descripcion": descripcion,
    }


# 3.7 — Igual que parsear_servicio pero sin placa (el vehículo ya está fijado en el servicio existente)
def parsear_edicion(texto: str):
    tokens = texto.split()
    if not tokens or not _es_numero(tokens[0]):
        return None

    total_amount = float(tokens[0].replace(",", "."))
    idx = 1

    pending_amount = 0.0
    if idx < len(tokens):
        tok = tokens[idx]
        if tok.lower().endswith("p") and _es_numero(tok[:-1]):
            pending_amount = float(tok[:-1].replace(",", "."))
            idx += 1

    descripcion = " ".join(tokens[idx:]).strip()
    if not descripcion or pending_amount > total_amount:
        return None

    return {
        "total_amount": total_amount,
        "pending_amount": pending_amount,
        "descripcion": descripcion,
    }