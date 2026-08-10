# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
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
        # Las puertas no son una lista de códigos sino una matriz alto × ancho.
        # Hay VARIAS familias en matriz (puertas rectas, de rincón…): se guardan
        # todas; con una sola clave, la última pisaba a la anterior y una puerta
        # normal acababa tarifada contra la matriz equivocada.
        if info.get("type") == "matrix" and info.get("rows"):
            idx.setdefault("__MATRICES__", {})[fam] = info
    return idx, pv


def _find_code(idx, letters, width, mano):
    letters = letters.upper()
    for c in (f"{letters}{width}D/I", (f"{letters}{width}{mano}" if mano else None), f"{letters}{width}"):
        if c and c in idx:
            return c
    for k in idx:
        if re.match(rf"^{re.escape(letters)}{width}(D/I|D|I)?$", k):
            return k
    # La variante puede ir DESPUÉS del ancho: se escribe "ASFA 60x30" y en la
    # tarifa es "ASF60A". Se prueba moviendo las últimas letras detrás del ancho,
    # pero SOLO se acepta si el código resultante existe: no se inventa nada.
    for corte in (1, 2):
        if len(letters) > corte:
            base, sufijo = letters[:-corte], letters[-corte:]
            for c in (f"{base}{width}{sufijo}", f"{base}{width}{sufijo}D/I"):
                if c in idx:
                    return c
    return None


def _sugerencia(idx, letters, width):
    """Código PARECIDO que sí existe, para poder avisar sin corregir por cuenta
    propia. Devuelve None si no hay nada razonable."""
    letters = (letters or "").upper()
    if not letters:
        return None
    # Mismas letras, otro ancho.
    mismos = [k for k in idx if re.match(rf"^{re.escape(letters)}\d", k)]
    if mismos:
        return sorted(mismos)[0]
    # Mismo ancho, letras parecidas (una letra de más o de menos).
    for cand in (letters[:-1], letters[:-2], letters + "E"):
        if not cand:
            continue
        exactos = [k for k in idx if re.match(rf"^{re.escape(cand)}{width}(D/I|D|I)?$", k)]
        if exactos:
            return sorted(exactos)[0]
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
    """Compatibilidad: solo los muebles. Para saber además QUÉ no se ha podido
    leer, usa `parse_relacion` (y no dejes nada por el camino en silencio)."""
    return parse_relacion(text, tariff)["muebles"]


def _puerta_suelta(idx, pv, tok, contexto):
    """Nota de PUERTA SUELTA: '2 - 90 x 60' = 2 puertas de 90 alto × 60 ancho.

    Solo se interpreta así cuando el recuadro del PDF es el de puertas (lo dice
    su etiqueta): un '2 - 90 x 60' suelto, sin saber de qué familia es, sería
    adivinar. La tarifa de puertas es una matriz alto × ancho.
    """
    if "PUERTA" not in (contexto or "").upper():
        return None
    m = re.match(r"^(\d+)\s*[-xX]?\s*(\d{2,3})\s*[xX*]\s*(\d{2,3})$", tok.strip())
    if not m:
        return None
    qty, alto, ancho = int(m.group(1)), int(m.group(2)), int(m.group(3))
    matrices = idx.get("__MATRICES__") or {}
    if not matrices:
        return None
    # Se busca en la matriz cuya etiqueta encaja con el recuadro; si no, en la
    # primera que tenga esa medida exacta.
    ctx = (contexto or "").upper().replace(" ", "_")
    orden = sorted(matrices, key=lambda f: (0 if (f in ctx or ctx in f) else 1, f))
    fam = pts = None
    for f in orden:
        fila = (matrices[f].get("rows") or {}).get(str(alto))
        if fila and fila.get(f"P{ancho}") is not None:
            fam, pts = f, fila[f"P{ancho}"]
            break
    if pts is None:
        return None
    return {
        "qty": qty, "cod": f"P{ancho}x{alto}", "familia": fam, "tipo": "PUERTA",
        "ancho": ancho, "alto": alto, "fondo": None, "mano": "",
        "pts": pts, "pvp": round(pts * pv, 2), "raw": tok, "encontrado": True,
    }


def parse_relacion(text: str, tariff: str = "T1", contexto: str = ""):
    """Parsea un bloque de texto con la notación de relación.

    Devuelve {muebles, noLeidas}. `noLeidas` son los trozos escritos que NO se
    han sabido interpretar, con una sugerencia cuando hay un código parecido en
    la tarifa. Antes se descartaban sin decir nada y el total salía corto sin
    que nadie se enterara.
    """
    idx, pv = _load_index(tariff)
    out = []
    no_leidas = []
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
            # Puerta suelta escrita como "2 - 90 x 60" (sin codigo).
            suelta = _puerta_suelta(idx, pv, tok, contexto)
            if suelta:
                out.append(suelta)
                continue
            mq = re.match(r"^(\d+)\s*[-]?\s*([a-z].*)$", tok)
            if mq:
                qty = int(mq.group(1))
                rest = mq.group(2).strip()
            else:
                qty = 1
                rest = tok.strip()

            # Caso 1: Código directo exacto en catálogo (ej: ASC60D/I, B60D/I, COL60)
            rest_upper = rest.upper()
            if rest_upper in idx:
                cod = rest_upper
                entry = idx[cod]
                tipo = _tipo_de(cod)
                # Extraer ancho si existe
                m_w = re.search(r"(\d{2,3})", cod)
                width = int(m_w.group(1)) if m_w else 60
                dims = re.findall(r"x\s*(\d{2,3})", rest)
                alto = int(dims[-1]) if dims else alt_g
                if tipo == "BAJO" and not alto:
                    alto = 80
                pts = _puntos(entry, alto)
                mano = "D" if cod.endswith("D") else "I" if cod.endswith("I") else ""
                out.append({
                    "qty": qty,
                    "cod": cod,
                    "familia": entry["fam"],
                    "tipo": tipo,
                    "ancho": width,
                    "alto": alto,
                    "fondo": _FONDO.get(tipo, 58),
                    "mano": mano,
                    "pts": pts,
                    "pvp": round(pts * pv, 2) if pts else None,
                    "raw": tok,
                    "encontrado": True,
                })
                continue

            # Caso 2: Expresión con letras y ancho (ej: asc60d, b60i, a45, 1 b60i)
            mc = re.match(r"^([a-z]+)[\s.\-]*(\d{2,3})(.*)$", rest)
            if not mc:
                no_leidas.append({"texto": tok, "motivo": "falta el ancho en el código"})
                continue
            letters, width, tail = mc.group(1), mc.group(2), mc.group(3)
            dims = re.findall(r"x\s*(\d{2,3})", tail)
            alto = int(dims[-1]) if dims else alt_g
            mano = ""
            if re.search(r"d/i", tail) or re.search(r"d/i", rest):
                mano = ""
            elif re.search(r"d\s*$", tail) or re.search(r"\bd\b", tail):
                mano = "D"
            elif re.search(r"i\s*$", tail) or re.search(r"\bi\b", tail):
                mano = "I"
            cod = _find_code(idx, letters, width, mano)
            entry = idx.get(cod) if cod else None
            if not cod:
                sug = _sugerencia(idx, letters, width)
                no_leidas.append({
                    "texto": tok,
                    "motivo": f"el código {letters.upper()}{width} no está en la tarifa",
                    "sugerencia": sug,
                })
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
    return {"muebles": out, "noLeidas": no_leidas}


def extract_form_and_text(pdf_bytes: bytes) -> str:
    """Devuelve TODO el texto útil del PDF: valores de los campos de formulario
    (AcroForm) + la capa de texto. Los campos van primero, uno por línea."""
    from services.pdf_utils import campos_de_formulario, texto_de_pdf
    campos = [v for _etiqueta, v in campos_de_formulario(pdf_bytes)]
    # Si el PDF es de formulario y tiene campos rellenados, esos SON la relación.
    # Solo se usa el texto plano cuando NO hay campos rellenados (relación suelta).
    if campos:
        return "\n".join(campos)
    return texto_de_pdf(pdf_bytes)


def extract_campos(pdf_bytes: bytes):
    """Campos rellenados del PDF como [(etiqueta, valor)].

    La etiqueta es la del recuadro (la familia a la que pertenece: "Puerta
    suelta", "Bajo con cajones"…), y hace falta para entender una nota que no
    lleva código, como "2 - 90 x 60" en el recuadro de puertas.
    """
    from services.pdf_utils import campos_de_formulario
    return campos_de_formulario(pdf_bytes)


def detectar_relacion(pdf_bytes: bytes, tariff: str = "T1"):
    """Punto de entrada completo: {muebles, noLeidas}.

    Cada recuadro se lee CON SU ETIQUETA, de modo que una nota sin código se
    puede interpretar dentro de su familia en vez de tirarla.
    """
    campos = extract_campos(pdf_bytes)
    if campos:
        muebles, no_leidas = [], []
        for etiqueta, valor in campos:
            r = parse_relacion(valor, tariff, contexto=etiqueta)
            muebles.extend(r["muebles"])
            for nl in r["noLeidas"]:
                no_leidas.append({**nl, "recuadro": etiqueta})
        return {"muebles": muebles, "noLeidas": no_leidas}
    return parse_relacion(extract_form_and_text(pdf_bytes), tariff)


def detectar_relacion_pdf(pdf_bytes: bytes, tariff: str = "T1"):
    """Compatibilidad: solo la lista de muebles."""
    return detectar_relacion(pdf_bytes, tariff)["muebles"]
