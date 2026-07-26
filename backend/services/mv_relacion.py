"""
mv_relacion.py — Lee una RELACIÓN de muebles MV escrita a mano en el PDF de
nomenclaturas rellenable (o cualquier PDF/texto con esa notación) y devuelve los
muebles detectados, emparejados con la tarifa MV (código canónico, puntos, PVP).

Notación admitida en cada campo/línea (la que usa el usuario):
    "1 b25d + 1b30d +1b60i (altura todos 80)"   -> 3 bajos, altura 80
    "1-bf60i"                                    -> 1 bajo fregadero 60 izq.
    "1a60i + 1a60d"                              -> 2 altos de 60
    "1asc60x90 d"                                -> 1 alto campana 60, alto 90, dcha.
    "1ar65x65x90"                                -> 1 alto rincón 65, alto 90

Se lee tanto la CAPA DE TEXTO como los VALORES DE LOS CAMPOS DE FORMULARIO
(AcroForm) del PDF, así que funciona con el PDF de nomenclaturas rellenado.
"""
import json
import os
import re

_MV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mv_tarifas_oficiales.json")

_FONDO = {"BAJO": 58, "ALTO": 33, "COLUMNA": 58}


def _load_index(tariff: str = "T1"):
    data = json.load(open(_MV_PATH, "r", encoding="utf-8"))
    T = data.get("tariffs", {}).get(tariff, {})
    pv = data.get("_meta", {}).get("pointValue", 3.33)
    idx = {}
    for fam, info in T.items():
        items = info.get("items", {})
        if isinstance(items, dict):
            for cod, e in items.items():
                idx[cod.upper()] = {"fam": fam, "e": e, "t": info.get("type")}
    return idx, pv


def _find_code(idx, letters, width, mano):
    letters = letters.upper()
    for c in (f"{letters}{width}D/I", (f"{letters}{width}{mano}" if mano else None), f"{letters}{width}"):
        if c and c in idx:
            return c
    for k in idx:
        if re.match(rf"^{re.escape(letters)}{width}(D/I|D|I)?$", k):
            return k
    return None


def _tipo_de(letters):
    l = letters.upper()
    if l.startswith("B"):
        return "BAJO"
    if l.startswith("A") or l.startswith(("L", "S")):
        return "ALTO"
    if l.startswith("C") or l.startswith("M"):
        return "COLUMNA"
    return "BAJO"


def _puntos(entry, alto):
    """Puntos según el tipo de familia y (si aplica) la altura."""
    if not entry:
        return None
    t = entry["t"]
    ev = entry["e"]
    if t == "single" and isinstance(ev, (int, float)):
        return ev
    if t == "h7090" and isinstance(ev, list):
        return ev[1] if (alto and alto >= 85) else ev[0]
    if t in ("h127147", "h200220") and isinstance(ev, list):
        umbral = 137 if t == "h127147" else 210
        return ev[1] if (alto and alto > umbral) else ev[0]
    if isinstance(ev, list) and ev:
        return ev[0]
    if isinstance(ev, (int, float)):
        return ev
    return None


def parse_relacion_text(text: str, tariff: str = "T1"):
    """Parsea un bloque de texto con la notación de relación. Devuelve lista de
    muebles: {qty, cod, tipo, ancho, alto, fondo, mano, pts, pvp, raw}."""
    idx, pv = _load_index(tariff)
    out = []
    # Cada renglón (o valor de campo) puede llevar varias piezas separadas por + , ;
    for linea in re.split(r"[\r\n]+", text or ""):
        val = linea.strip().lower()
        if not val:
            continue
        m = re.search(r"altura\D*(\d{2,3})", val)
        alt_g = int(m.group(1)) if m else None
        body = re.sub(r"\([^)]*\)", "", val)
        for tok in re.split(r"[+,;]", body):
            tok = tok.strip().strip("-").strip()
            if not tok:
                continue
            mq = re.match(r"^(\d+)\s*[-]?\s*([a-z].*)$", tok)
            if not mq:
                continue
            qty = int(mq.group(1))
            rest = mq.group(2).strip()
            mc = re.match(r"^([a-z]+)(\d{2,3})(.*)$", rest)
            if not mc:
                continue
            letters, width, tail = mc.group(1), mc.group(2), mc.group(3)
            dims = re.findall(r"x\s*(\d{2,3})", tail)
            alto = int(dims[-1]) if dims else alt_g
            mano = ""
            if re.search(r"d\s*$", tail) or re.search(r"\bd\b", tail):
                mano = "D"
            elif re.search(r"i\s*$", tail) or re.search(r"\bi\b", tail):
                mano = "I"
            cod = _find_code(idx, letters, width, mano)
            entry = idx.get(cod) if cod else None
            tipo = _tipo_de(letters)
            # Regla de fábrica: los BAJOS se fabrican SIEMPRE a altura 80 cm. Si no se
            # ha indicado altura para un bajo, se asume 80 (no hay otras alturas de bajo).
            if tipo == "BAJO" and not alto:
                alto = 80
            pts = _puntos(entry, alto)
            out.append({
                "qty": qty,
                "cod": cod,
                "familia": entry["fam"] if entry else None,
                "tipo": tipo,
                "ancho": int(width),
                "alto": alto,
                "fondo": _FONDO.get(tipo, 58),
                "mano": mano,
                "pts": pts,
                "pvp": round(pts * pv, 2) if pts else None,
                "raw": tok,
                "encontrado": bool(cod),
            })
    return out


def extract_form_and_text(pdf_bytes: bytes) -> str:
    """Devuelve TODO el texto útil del PDF: valores de los campos de formulario
    (AcroForm) + la capa de texto. Los campos van primero, uno por línea."""
    import fitz
    campos = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in doc:
        try:
            for w in page.widgets() or []:
                v = (w.field_value or "").strip()
                if v:
                    campos.append(v)
        except Exception:
            pass
    # Si el PDF es de formulario y tiene campos rellenados, esos SON la relación.
    # La capa de texto de un PDF con AcroForm suele DUPLICAR esos valores, así que
    # solo usamos el texto plano cuando NO hay campos rellenados (relación suelta).
    if campos:
        doc.close()
        return "\n".join(campos)
    texto = []
    for page in doc:
        try:
            texto.append(page.get_text())
        except Exception:
            pass
    doc.close()
    return "\n".join(texto)


def detectar_relacion_pdf(pdf_bytes: bytes, tariff: str = "T1"):
    """Punto de entrada: bytes de PDF -> muebles detectados de la relación."""
    texto = extract_form_and_text(pdf_bytes)
    return parse_relacion_text(texto, tariff)
