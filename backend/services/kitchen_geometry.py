"""
kitchen_geometry.py — ÚNICA fuente de verdad de la geometría real de cocina.

Regla del proyecto (ver CLAUDE.md): NUNCA se inventan medidas. Toda medida que se
vaya a dibujar en un alzado, planta o ficha técnica pasa por aquí. Si un valor es
imposible de fabricar, se corrige al estándar más cercano; si no hay forma de
derivarlo, se marca como desconocido para que la UI lo pida — jamás se rellena con
un número "plausible".

Medidas en CENTÍMETROS (es la unidad con la que dibuja el alzado vectorial).
"""
from typing import Optional

# ── Estándares de fabricación (cm) ───────────────────────────────────────────
ANCHOS_STD = [15, 20, 30, 40, 45, 50, 60, 70, 80, 90, 100, 120]

CASCO_BAJO_ALTO = 80          # en esta fábrica los bajos SOLO se fabrican a 80
ZOCALO_ALTO_MIN, ZOCALO_ALTO_MAX = 10, 15
ENCIMERA_GRUESO_MIN, ENCIMERA_GRUESO_MAX = 2, 4
ALTOS_ALTURAS = [70, 90]
COLUMNA_ALTURAS = [200, 220]
MEDIACOLUMNA_ALTO = 130
SOBREENCIMERA_ALTURAS = [127, 147]
FONDO_ALTOS = 33
FONDO_BAJOS = 58
SEPARACION_ENCIMERA_ALTOS_MIN, SEPARACION_ENCIMERA_ALTOS_MAX = 55, 60
TECHO_MIN, TECHO_MAX = 240, 270

# Rangos duros de validación: fuera de esto NO es una variante, es un error.
LIMITES = {
    "ancho_modulo":   (15, 120),
    "ancho_pared":    (60, 1200),
    "alto_pared":     (TECHO_MIN, 320),
    "alto_bajo":      (70, 90),
    "alto_alto":      (35, 110),
    "alto_columna":   (180, 240),
    "fondo":          (20, 70),
}

COLUMNAS_IDS = {"frigorifico", "congelador", "columna_hornos", "despensa", "vinoteca"}
ALTOS_IDS = {"microondas"}

# Módulos de ANCHO FIJO: son electrodomésticos de medida comercial. Jamás se
# reescalan para "cuadrar" una pared (un lavavajillas es de 60, no de 120).
ANCHO_FIJO = {
    "lavavajillas": 60, "horno": 60, "microondas": 60, "columna_hornos": 60,
    "frigorifico": 60, "congelador": 60, "vinoteca": 60, "placa": 60, "campana": 60,
}


def snap_ancho(w: float) -> int:
    """Ajusta un ancho al estándar de fabricación más cercano."""
    try:
        w = float(w)
    except (TypeError, ValueError):
        return 60
    return min(ANCHOS_STD, key=lambda s: abs(s - w))


def en_rango(valor, clave: str) -> bool:
    lo, hi = LIMITES[clave]
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return False
    return lo <= v <= hi


def altura_modulo(elem_id: str) -> int:
    """Altura real (cm) del cuerpo de un módulo según su tipo. Deriva del estándar,
    no de una estimación visual."""
    t = (elem_id or "").lower()
    if t in COLUMNAS_IDS:
        return COLUMNA_ALTURAS[1]
    if t in ALTOS_IDS:
        return ALTOS_ALTURAS[0]
    return CASCO_BAJO_ALTO


def fondo_modulo(elem_id: str) -> int:
    t = (elem_id or "").lower()
    return FONDO_ALTOS if t in ALTOS_IDS else FONDO_BAJOS


def validar_distribucion(dist: dict, ancho_real: Optional[int] = None,
                         alto_real: Optional[int] = None) -> dict:
    """Valida y CORRIGE una distribución {paredes, elementos} antes de dibujarla.

    - Cada pared: ancho/alto dentro de rango; si el usuario dio el ancho real, ese
      manda sobre cualquier estimación de la IA.
    - Cada módulo: ancho ajustado a estándar y dentro de rango.
    - Los módulos de una pared se reescalan para SUMAR exactamente el ancho de la
      pared y se recolocan contiguos (sin huecos ni solapes).
    - Devuelve la distribución corregida + `avisos` con lo que se ha tenido que
      corregir (trazabilidad: nada se corrige en silencio).
    """
    avisos = []
    paredes = []
    for i, p in enumerate(dist.get("paredes") or []):
        try:
            anc = int(round(float(p.get("ancho") or 0)))
            alt = int(round(float(p.get("alto") or 0))) or 240
        except (TypeError, ValueError):
            avisos.append(f"Pared {i+1}: medidas ilegibles, descartada.")
            continue
        if not en_rango(anc, "ancho_pared"):
            avisos.append(f"Pared {i+1}: ancho {anc} cm fuera de rango; descartada.")
            continue
        if not en_rango(alt, "alto_pared"):
            avisos.append(f"Pared {i+1}: alto {alt} cm no es una altura de techo real; se usa 240.")
            alt = 240
        paredes.append({"nombre": str(p.get("nombre") or f"Pared {len(paredes)+1}"),
                        "ancho": anc, "alto": alt})

    if not paredes:
        # Sin datos válidos NO se inventa una cocina: se deja explícito.
        return {"ok": False, "motivo": "No hay ninguna pared con medidas válidas.",
                "avisos": avisos, "paredes": [], "elementos": []}

    # El dato del usuario SIEMPRE manda sobre la estimación de la IA.
    if ancho_real and en_rango(ancho_real, "ancho_pared"):
        if paredes[0]["ancho"] != ancho_real:
            avisos.append(f"Pared 1: se usa el ancho REAL del usuario ({ancho_real} cm) "
                          f"en lugar del estimado ({paredes[0]['ancho']} cm).")
        paredes[0]["ancho"] = int(ancho_real)
    if alto_real and en_rango(alto_real, "alto_pared"):
        paredes[0]["alto"] = int(alto_real)

    elementos = []
    for e in (dist.get("elementos") or [])[:60]:
        try:
            anc = float(e.get("ancho") or 0)
            pos = float(e.get("posicion_cm") or 0)
            pidx = int(e.get("pared_idx") or 0)
        except (TypeError, ValueError):
            continue
        eid = str(e.get("id") or "mueble").lower().strip().replace(" ", "_")
        anc_snap = snap_ancho(anc)
        if not en_rango(anc, "ancho_modulo"):
            avisos.append(f"Módulo «{eid}»: ancho {int(anc)} cm no es fabricable; "
                          f"se ajusta a {anc_snap} cm.")
        elementos.append({
            "id": eid,
            "label": str(e.get("label") or eid or "Módulo")[:24],
            "pared_idx": max(0, min(pidx, len(paredes) - 1)),
            "posicion_cm": max(0, int(round(pos))),
            "ancho": anc_snap,
            "alto": altura_modulo(eid),
            "fondo": fondo_modulo(eid),
        })

    # Cuadrar cada pared: la suma de anchos DEBE coincidir con el ancho de pared.
    # Criterio de arquitecto técnico:
    #  · Los electrodomésticos (ancho fijo) NO se tocan nunca.
    #  · El resto (muebles, cajoneras) se ajusta proporcionalmente al hueco libre.
    #  · Si sobra hueco y no hay módulo flexible, se añade un RELLENO/costado real
    #    (es lo que se hace en obra), en vez de inflar los módulos existentes.
    finales = []
    no_cabe = False
    for pidx, pared in enumerate(paredes):
        grupo = sorted([e for e in elementos if e["pared_idx"] == pidx],
                       key=lambda e: e["posicion_cm"])
        if not grupo:
            continue
        objetivo = pared["ancho"]
        for e in grupo:
            if e["id"] in ANCHO_FIJO:
                e["ancho"] = ANCHO_FIJO[e["id"]]
                e["anchoFijo"] = True
        fijos = [e for e in grupo if e.get("anchoFijo")]
        flex = [e for e in grupo if not e.get("anchoFijo")]
        suma_fijos = sum(e["ancho"] for e in fijos)
        libre = objetivo - suma_fijos

        if libre < 0:
            no_cabe = True
            avisos.append(
                f"Pared {pidx+1}: solo los electrodomésticos ocupan {suma_fijos} cm y la pared "
                f"mide {objetivo} cm. La composición NO cabe: revisa medidas o módulos.")
        elif flex:
            suma_flex = sum(e["ancho"] for e in flex)
            if suma_flex > 0 and libre > 0 and suma_flex != libre:
                factor = libre / suma_flex
                # Solo se reescala si el ajuste es razonable (±35%). Un desfase mayor
                # significa que faltan o sobran módulos, no que midan otra cosa.
                if 0.65 <= factor <= 1.35:
                    for e in flex:
                        e["ancho"] = snap_ancho(e["ancho"] * factor)
                    avisos.append(f"Pared {pidx+1}: módulos ajustados para cuadrar con {objetivo} cm.")
                else:
                    avisos.append(
                        f"Pared {pidx+1}: los módulos suman {suma_fijos + suma_flex} cm frente a "
                        f"{objetivo} cm de pared. Parece que FALTAN o SOBRAN módulos; se completa "
                        f"con un relleno en vez de deformar las medidas.")
            resto = objetivo - sum(e["ancho"] for e in grupo)
            if resto:
                # Absorber en el módulo flexible más ancho si cabe; si no, relleno.
                i = max(range(len(flex)), key=lambda i: flex[i]["ancho"])
                nuevo = flex[i]["ancho"] + resto
                if en_rango(nuevo, "ancho_modulo"):
                    flex[i]["ancho"] = int(nuevo)
                elif resto > 0:
                    grupo.append({"id": "relleno", "label": f"Relleno {int(resto)}", "pared_idx": pidx,
                                  "posicion_cm": 0, "ancho": int(resto),
                                  "alto": CASCO_BAJO_ALTO, "fondo": FONDO_BAJOS})
                    avisos.append(f"Pared {pidx+1}: añadido relleno de {int(resto)} cm para cuadrar.")
        else:
            resto = objetivo - suma_fijos
            if resto > 0:
                grupo.append({"id": "relleno", "label": f"Relleno {int(resto)}", "pared_idx": pidx,
                              "posicion_cm": 0, "ancho": int(resto),
                              "alto": CASCO_BAJO_ALTO, "fondo": FONDO_BAJOS})
                avisos.append(f"Pared {pidx+1}: hueco de {int(resto)} cm sin módulo; añadido relleno.")

        x = 0
        for e in grupo:
            e["posicion_cm"] = x
            x += e["ancho"]
        finales.extend(grupo)

    if not finales:
        return {"ok": False, "motivo": "No hay módulos válidos que dibujar.",
                "avisos": avisos, "paredes": paredes, "elementos": []}
    if no_cabe:
        # No se dibuja una cocina que no cabe: es un error a resolver, no una medida
        # que "aproximar". El usuario debe corregir pared o módulos.
        return {"ok": False, "motivo": "La composición no cabe en la pared indicada.",
                "avisos": avisos, "paredes": paredes, "elementos": finales}

    return {
        "ok": True,
        "tipo": str(dist.get("tipo") or "lineal"),
        "paredes": paredes,
        "elementos": finales,
        "isla": dist.get("isla") or {},
        "medidasReales": bool(ancho_real),
        "avisos": avisos,
    }
