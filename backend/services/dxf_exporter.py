# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
"""
dxf_exporter.py — Exportador vectorial DXF (AutoCAD) para Estudio 3D
=====================================================================
Genera planos técnicos en formato DXF (AutoCAD R12/2000 ASCII) directamente
desde la geometría validada de la cocina.

Exporta:
- Planta acotada con paredes, esquinas y profundidad de módulos
- Alzado acotado por pared con bajos, altos, columnas, zócalos y electrodomésticos
- Cotas vectoriales legibles en cm
"""
from typing import Dict, Any, List, Tuple


def _dxf_line(x1: float, y1: float, x2: float, y2: float, layer: str = "0") -> str:
    """Genera una entidad LINE en formato DXF."""
    return (
        f"0\nLINE\n8\n{layer}\n"
        f"10\n{x1:.2f}\n20\n{y1:.2f}\n30\n0.0\n"
        f"11\n{x2:.2f}\n21\n{y2:.2f}\n31\n0.0\n"
    )


def _dxf_rect(x: float, y: float, w: float, h: float, layer: str = "0") -> str:
    """Genera un rectángulo a partir de 4 líneas."""
    return (
        _dxf_line(x, y, x + w, y, layer) +
        _dxf_line(x + w, y, x + w, y + h, layer) +
        _dxf_line(x + w, y + h, x, y + h, layer) +
        _dxf_line(x, y + h, x, y, layer)
    )


def _dxf_text(x: float, y: float, text: str, height: float = 12.0, layer: str = "TEXTO") -> str:
    """Genera una entidad TEXT en formato DXF."""
    clean_text = str(text).replace("\n", " ").strip()
    return (
        f"0\nTEXT\n8\n{layer}\n"
        f"10\n{x:.2f}\n20\n{y:.2f}\n30\n0.0\n"
        f"40\n{height:.2f}\n"
        f"1\n{clean_text}\n"
    )


def generar_dxf_cocina(distribucion: Dict[str, Any], cliente: str = "Cliente") -> str:
    """
    Genera el contenido de un archivo .DXF completo (CAD ASCII R12/2000)
    que contiene la Planta 2D acotada y el Alzado de paredes con muebles.
    """
    tipo = str(distribucion.get("tipo") or "lineal").upper()
    paredes = distribucion.get("paredes") or []
    elementos = distribucion.get("elementos") or []

    entities = []

    # Título principal del plano DXF
    entities.append(_dxf_text(0, 450, f"ESTUDIO 3D — PLANO TÉCNICO CAD (DXF)", height=24, layer="TITULO"))
    entities.append(_dxf_text(0, 420, f"Cliente: {cliente} | Distribución: {tipo}", height=16, layer="TITULO"))

    # 1. PLANTA 2D ACOTADA
    offset_y_planta = 100
    entities.append(_dxf_text(0, offset_y_planta + 260, "PLANTA EN PLANTA (VISTA EN PLANTA)", height=16, layer="CAPA_TITULO"))

    x_curr = 0
    for pidx, p in enumerate(paredes):
        pw = float(p.get("ancho") or 300)
        ph = float(p.get("alto") or 240)
        pname = str(p.get("nombre") or f"Pared {pidx+1}")

        # Pared externa (grosor 15cm)
        entities.append(_dxf_rect(x_curr, offset_y_planta, pw, 15, layer="PAREDES"))
        entities.append(_dxf_text(x_curr + pw/2 - 20, offset_y_planta + 20, f"{pname} ({int(pw)} cm)", height=10, layer="COTAS"))

        # Módulos en planta
        elems_pared = [e for e in elementos if e.get("pared_idx") == pidx]
        for e in elems_pared:
            pos_x = x_curr + float(e.get("posicion_cm") or 0)
            ew = float(e.get("ancho") or 60)
            efondo = float(e.get("fondo") or 58)
            label = str(e.get("label") or e.get("id") or "Módulo")
            fila = str(e.get("fila") or "bajo")

            # Módulo en planta (abajo de la pared)
            y_elem = offset_y_planta - efondo if fila == "bajo" else offset_y_planta - 33
            layer_m = "MUEBLES_BAJOS" if fila == "bajo" else "MUEBLES_ALTOS"

            entities.append(_dxf_rect(pos_x, y_elem, ew, efondo, layer=layer_m))
            entities.append(_dxf_text(pos_x + 2, y_elem + efondo/2, f"{label} ({int(ew)})", height=8, layer="ETIQUETAS"))

        x_curr += pw + 60

    # 2. ALZADO TÉCNICO DE PAREDES
    offset_y_alzado = -300
    entities.append(_dxf_text(0, offset_y_alzado + 280, "ALZADO DE PAREDES (VISTA FRONTAL)", height=16, layer="CAPA_TITULO"))

    x_alzado = 0
    for pidx, p in enumerate(paredes):
        pw = float(p.get("ancho") or 300)
        ph = float(p.get("alto") or 240)
        pname = str(p.get("nombre") or f"Pared {pidx+1}")

        # Marco de la pared (suelo y techo)
        entities.append(_dxf_rect(x_alzado, offset_y_alzado, pw, ph, layer="ESTRUC_PARED"))
        entities.append(_dxf_text(x_alzado + pw/2 - 30, offset_y_alzado + ph + 10, f"ALZADO: {pname} [{int(pw)} x {int(ph)} cm]", height=12, layer="COTAS"))

        # Zócalo (10 cm)
        entities.append(_dxf_rect(x_alzado, offset_y_alzado, pw, 10, layer="ZOCALO"))

        # Módulos en alzado
        elems_pared = [e for e in elementos if e.get("pared_idx") == pidx]
        for e in elems_pared:
            pos_x = x_alzado + float(e.get("posicion_cm") or 0)
            ew = float(e.get("ancho") or 60)
            eh = float(e.get("alto") or 80)
            label = str(e.get("label") or e.get("id") or "Módulo")
            fila = str(e.get("fila") or "bajo")

            if fila == "bajo":
                y_mueble = offset_y_alzado + 10  # sobre zócalo (10cm)
            else:
                y_mueble = offset_y_alzado + 145  # sobre encimera (~145cm)

            layer_m = "MUEBLES_BAJOS" if fila == "bajo" else "MUEBLES_ALTOS"
            entities.append(_dxf_rect(pos_x, y_mueble, ew, eh, layer=layer_m))
            entities.append(_dxf_text(pos_x + 4, y_mueble + eh/2 - 4, label, height=9, layer="ETIQUETAS"))
            entities.append(_dxf_text(pos_x + ew/2 - 10, y_mueble - 12, f"[{int(ew)} cm]", height=8, layer="COTAS"))

        x_alzado += pw + 80

    # Cabecera DXF R12 Estándar
    dxf_content = (
        "0\nSECTION\n2\nHEADER\n0\nENDSEC\n"
        "0\nSECTION\n2\nTABLES\n"
        "0\nTABLE\n2\nLAYER\n"
        "0\nLAYER\n2\n0\n70\n0\n62\n7\n6\nCONTINUOUS\n"
        "0\nLAYER\n2\nPAREDES\n70\n0\n62\n1\n6\nCONTINUOUS\n"
        "0\nLAYER\n2\nMUEBLES_BAJOS\n70\n0\n62\n5\n6\nCONTINUOUS\n"
        "0\nLAYER\n2\nMUEBLES_ALTOS\n70\n0\n62\n3\n6\nCONTINUOUS\n"
        "0\nLAYER\n2\nCOTAS\n70\n0\n62\n2\n6\nCONTINUOUS\n"
        "0\nLAYER\n2\nETIQUETAS\n70\n0\n62\n4\n6\nCONTINUOUS\n"
        "0\nENDTAB\n0\nENDSEC\n"
        "0\nSECTION\n2\nENTITIES\n"
        + "".join(entities) +
        "0\nENDSEC\n"
        "0\nEOF\n"
    )

    return dxf_content
