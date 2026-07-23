"""
Parser de PROFORMAS de proveedor de cascos (PUBLIOFERTA/ALV y similares).

Extrae la relación de muebles de un PDF de presupuesto/proforma para, después,
calcular NUESTRO coste (casco + herraje BLUM + mano de obra).

Estrategia de lectura:
1) Capa de texto (PyMuPDF) si el PDF la tiene -> parseo determinista y gratis.
2) Si no hay texto (PDF escaneado/imagen) -> visión IA (Gemini) como respaldo.

Multipágina: se procesan TODAS las páginas.
"""
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Cabecera de línea de artículo: "<n> <COD_ARTICULO>" (el código no lleva espacios).
_HEADER = re.compile(r"^(\d+)\s+([A-Z0-9][A-Z0-9./+-]{2,})$")
_NUM = re.compile(r"^-?\d+(?:[.,]\d+)?$")
_CANT = re.compile(r"^(\d+(?:[.,]\d+)?)\s*(UD|MI|ML|M2|M)\b", re.I)


def _to_float(s: str) -> Optional[float]:
    try:
        return float(str(s).replace(".", "").replace(",", ".")) if "," in str(s) and "." in str(s) \
            else float(str(s).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _cuenta_frentes(desc: str) -> Dict[str, int]:
    """Cuenta puertas, cajones y gavetas a partir de la descripción del mueble."""
    t = (desc or "").upper()
    def _n(palabra):
        # "2 PUERTAS", "1 PUERTA", "4 GAVETAS"...
        tot = 0
        for m in re.finditer(r"(\d+)\s+" + palabra, t):
            tot += int(m.group(1))
        # singular sin número explícito ("1 PUERTA" ya cubierto; "PUERTA" suelto = 1)
        if tot == 0 and re.search(r"\b" + palabra[:-1] + r"\b", t):
            tot = 1
        return tot
    puertas = _n("PUERTAS")
    cajones = _n("CAJONES") + _n("CAJON" + "ES") if False else 0
    # 'CAJON'/'CAJONES' y 'GAVETA'/'GAVETAS'
    def _cuenta(base):
        tot = 0
        for m in re.finditer(r"(\d+)\s+" + base + r"S?\b", t):
            tot += int(m.group(1))
        return tot
    puertas = _cuenta("PUERTA")
    cajones = _cuenta("CAJON")
    gavetas = _cuenta("GAVETA")
    return {"puertas": puertas, "cajones": cajones, "gavetas": gavetas}


def _color_y_herraje(material: str):
    """Del texto de material saca color/acabado y si lleva herraje BLUM (Merivobox)."""
    m = (material or "").upper()
    herraje_blum = "MERIVOBOX" in m or "MERIVO" in m or "LEGRABOX" in m or "TANDEMBOX" in m
    color = material.strip(" -") if material else ""
    return color, herraje_blum


def parse_proforma_text(full_text: str) -> List[Dict[str, Any]]:
    """Parseo determinista del texto extraído del PDF (todas las páginas concatenadas)."""
    lines = [l.strip() for l in (full_text or "").split("\n")]
    items: List[Dict[str, Any]] = []
    i = 0
    n = len(lines)
    while i < n:
        h = _HEADER.match(lines[i])
        if not h:
            i += 1
            continue
        idx = int(h.group(1)); cod = h.group(2)
        desc = lines[i + 1] if i + 1 < n else ""
        # Recorre el bloque hasta la siguiente cabecera recogiendo números y material.
        j = i + 2
        nums: List[float] = []
        cantidad = None
        material = ""
        precio = None
        total = None
        seen_ud = False
        while j < n and not _HEADER.match(lines[j]):
            ln = lines[j]
            cm = _CANT.match(ln)
            if cm:
                cantidad = _to_float(cm.group(1)); seen_ud = True
                j += 1
                continue
            if _NUM.match(ln):
                val = _to_float(ln)
                if val is not None:
                    if not seen_ud:
                        nums.append(val)          # largo, ancho, grueso (antes de UD)
                    else:
                        if precio is None:
                            precio = val
                        elif total is None:
                            total = val
                j += 1
                continue
            # línea de texto: material/color (la que lleva letras y guiones)
            if re.search(r"[A-Za-z]", ln) and not material and ln.upper() != "UD":
                material = ln
            j += 1
        largo = nums[0] if len(nums) > 0 else None
        ancho = nums[1] if len(nums) > 1 else None
        grueso = nums[2] if len(nums) > 2 else None
        color, herraje_blum = _color_y_herraje(material)
        frentes = _cuenta_frentes(desc)
        # ¿Es un casco/mueble (tiene estructura y material melamina) o un accesorio
        # (regleta, panel, zócalo…)? Heurística: material con "MELAMINA"/"ZENIT" o
        # descripción con PUERTA/CAJON/GAVETA/COLUMNA/BAJO/ALTO.
        es_mueble = bool(re.search(r"MELAMINA|ZENIT|SUPERMATT", (material or "").upper())) or \
            any(k in desc.upper() for k in ("BAJO", "ALTO", "COLUMNA", "SEMICOLUMNA", "PUERTA", "CAJON", "GAVETA", "SOBREMODULO", "MODULO"))
        items.append({
            "n": idx, "cod": cod, "descripcion": desc, "material": material,
            "color": color, "herrajeBlum": herraje_blum,
            "largo": largo, "ancho": ancho, "grueso": grueso,
            "cantidad": cantidad or 1.0, "pvp": precio, "total": total,
            "puertas": frentes["puertas"], "cajones": frentes["cajones"], "gavetas": frentes["gavetas"],
            "esMueble": es_mueble,
        })
        i = j
    return items


def extract_pdf_text_all_pages(pdf_bytes: bytes) -> str:
    """Texto de TODAS las páginas (PyMuPDF)."""
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def pdf_pages_to_png_b64(pdf_bytes: bytes, max_pages: int = 12) -> List[str]:
    """Renderiza cada página a PNG base64 (para el respaldo por visión IA)."""
    import fitz, base64
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    out = []
    for pg in list(doc)[:max_pages]:
        pix = pg.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        out.append(base64.b64encode(pix.tobytes("png")).decode("utf-8"))
    return out
