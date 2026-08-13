# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Parser de PROFORMAS de proveedor de cascos (PUBLIOFERTA/ALV y similares).

Extrae la relación de muebles de un PDF de presupuesto/proforma para, después,
calcular NUESTRO coste (casco + herraje BLUM + mano de obra).

Estrategia de lectura:
1) Capa de texto (pypdf) si el PDF la tiene -> parseo determinista y gratis.
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


def _tipo_mueble(desc: str) -> str:
    """Clasifica el mueble para saber qué herraje de sujeción lleva:
    - 'bajo'    → lleva PATAS (se apoya en el suelo).
    - 'columna' → lleva PATAS (columna/semicolumna a suelo).
    - 'alto'    → lleva COLGADORES (va colgado a la pared).
    - 'panel'   → regleta/panel/zócalo (accesorio, sin patas ni colgadores).
    """
    t = (desc or "").strip().upper()
    if t.startswith("BAJO") or " BAJO" in t or "FREGADERO" in t or re.match(r"^B\d", t) or re.match(r"^B[A-Z]*\d", t):
        return "bajo"
    if t.startswith("ALTO") or " ALTO" in t or "SOBREMODULO" in t or "COLGADO" in t or re.match(r"^A\d", t) or re.match(r"^A[A-Z]*\d", t):
        return "alto"
    if "SEMICOLUMNA" in t or "COLUMNA" in t or re.match(r"^C[DHSF]?\d", t):
        return "columna"
    if any(k in t for k in ("REG ", "ZOCALO", "ZÓCALO", "COPETE", "REGLETA", "COSTADO", "PANEL", "AZOC")):
        return "panel"
    return "otro"


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
        variantes_text = []
        nums = []
        precio = None
        total = None
        cantidad = 1.0
        material = ""
        seen_ud = False
        j = i + 2
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
            if re.search(r"[A-Za-z]", ln) and ln.upper() != "UD":
                variantes_text.append(ln)
                if not material:
                    material = ln
            j += 1

        full_var_text = " ".join(variantes_text).upper()
        inc_volada = 0.0
        m_vol = re.search(r"PUERTA\s+VOLADA\s*:?\s*(\d+)", full_var_text) or re.search(r"INCREMENTO\s+INFERIOR\s+PUERTA\s+VOLADA\s*:?\s*(\d+)", full_var_text)
        if m_vol:
            try:
                raw_inc = float(m_vol.group(1))
                # 100 en anotación Alvic proforma = 10mm (1 cm)
                inc_volada = raw_inc / 10.0 if raw_inc >= 100 else raw_inc
            except ValueError:
                inc_volada = 0.0

        largo_total = nums[0] if len(nums) > 0 else None
        ancho = nums[1] if len(nums) > 1 else None
        grueso = nums[2] if len(nums) > 2 else None

        # El casco del alto mide exactamente lo que indica la proforma (ej 800mm / 80 cm)
        largo_casco = largo_total
        # La puerta volada suma el incremento inferior (ej 800mm + 10mm = 810mm / 81 cm)
        largo_puerta = (largo_total + inc_volada) if (largo_total is not None and inc_volada > 0) else largo_total

        color, herraje_blum = _color_y_herraje(material)
        frentes = _cuenta_frentes(desc)
        tipo = _tipo_mueble(desc)
        # ¿Es un casco/mueble (tiene estructura y material melamina) o un accesorio
        # (regleta, panel, zócalo…)? Heurística: material con "MELAMINA"/"ZENIT" o
        # descripción con PUERTA/CAJON/GAVETA/COLUMNA/BAJO/ALTO.
        es_mueble = bool(re.search(r"MELAMINA|ZENIT|SUPERMATT", (material or "").upper())) or \
            any(k in desc.upper() for k in ("BAJO", "ALTO", "COLUMNA", "SEMICOLUMNA", "PUERTA", "CAJON", "GAVETA", "SOBREMODULO", "MODULO"))
        items.append({
            "n": idx, "cod": cod, "descripcion": desc, "material": material,
            "color": color, "herrajeBlum": herraje_blum,
            "largo": largo_casco, "ancho": ancho, "grueso": grueso,
            "largoPuerta": largo_puerta, "incVolada": inc_volada,
            "cantidad": cantidad or 1.0, "pvp": precio, "total": total,
            "puertas": frentes["puertas"], "cajones": frentes["cajones"], "gavetas": frentes["gavetas"],
            "tipo": tipo, "esMueble": es_mueble,
        })
        i = j
    return items


def extract_pdf_text_all_pages(pdf_bytes: bytes) -> str:
    """Texto de TODAS las páginas."""
    from services.pdf_utils import texto_de_pdf
    return texto_de_pdf(pdf_bytes)


def pdf_pages_to_png_b64(pdf_bytes: bytes, max_pages: int = 30) -> List[str]:
    """Renderiza a PNG base64 TODAS las páginas del PDF (hasta 30 páginas)."""
    import base64
    from services.pdf_utils import paginas_a_png

    return [base64.b64encode(p).decode("utf-8")
            for p in paginas_a_png(pdf_bytes, dpi=144, paginas=None)]
