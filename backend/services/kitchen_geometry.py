# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
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

# Palabras que delatan un mueble ALTO (va colgado a la pared). Importa mucho más
# de lo que parece: un alzado tiene DOS filas independientes —la de suelo y la
# colgada— y cada una ocupa el ancho de la pared por su cuenta. Si un alto se
# cuela en la fila de suelo, roba sitio a los bajos y la pared "se alarga": es
# justo lo que pasaba el 05/08 (415 cm de módulos en una pared de 324).
_PISTAS_ALTO = ("alto", "alacena", "colgado", "sobreencimera", "sobre_encimera",
                "vitrina", "campana", "extractor", "microondas", "altillo",
                "escurreplatos", "cubretermo")
# ...salvo que la palabra "alto" venga de otra cosa (un "bajo alto" no existe,
# pero "columna" y "bajo" sí mandan sobre la pista).
_PISTAS_NO_ALTO = ("bajo", "columna", "semicolumna", "cajonera", "fregadero",
                   "lavavajillas", "lavadora", "placa", "horno", "encimera",
                   "zocalo", "zócalo", "relleno")


def es_alto(elem_id: str, label: str = "") -> bool:
    """¿Este módulo va COLGADO (fila de altos) o apoyado (fila de suelo)?

    Se mira el id y también la etiqueta, porque la IA devuelve cosas como
    id="mueble_alto" pero también id="mueble" con label="Mueble alto".
    """
    texto = f"{elem_id or ''} {label or ''}".lower()
    if any(p in texto for p in _PISTAS_NO_ALTO):
        # "Columna frigorífico" o "Bajo fregadero" nunca son altos, aunque el
        # texto lleve alguna pista.
        if not any(texto.strip().startswith(p) for p in ("alto", "alacena", "altillo")):
            return False
    return any(p in texto for p in _PISTAS_ALTO)

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
                        "ancho": anc, "alto": alt,
                        # Si la cota está ESCRITA en el plano, manda sobre la suma
                        # de módulos. La bandera tiene que sobrevivir a la ida y
                        # vuelta (detectar → dibujar), o la regla no sirve de nada.
                        "ancho_escrito": bool(p.get("ancho_escrito"))})

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
        paredes[0]["ancho_escrito"] = True
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
        if eid == "relleno":
            # El relleno es una pieza a medida: su ancho ES el hueco que sobra.
            # Ajustarlo a un estándar descuadraba la pared que ya cuadraba (se
            # veía al revalidar: "relleno: 10 cm no es fabricable, se ajusta a 15").
            anc_snap = max(1, int(round(anc)))
        else:
            anc_snap = snap_ancho(anc)
            if not en_rango(anc, "ancho_modulo"):
                avisos.append(f"Módulo «{eid}»: ancho {int(anc)} cm no es fabricable; "
                              f"se ajusta a {anc_snap} cm.")
        etiqueta = str(e.get("label") or eid or "Módulo")[:24]
        escrita = bool(e.get("medida_escrita"))
        # La FILA (suelo o colgado) se decide aquí, una sola vez, y viaja con el
        # módulo. El dibujo ya no tiene que adivinarlo por el id.
        fila = "alto" if es_alto(eid, etiqueta) else "bajo"
        elementos.append({
            "id": eid,
            "label": etiqueta,
            "fila": fila,
            "medida_escrita": escrita,
            "pared_idx": max(0, min(pidx, len(paredes) - 1)),
            "posicion_cm": max(0, int(round(pos))),
            "ancho": anc_snap,
            "alto": ALTOS_ALTURAS[0] if fila == "alto" else altura_modulo(eid),
            "fondo": FONDO_ALTOS if fila == "alto" else fondo_modulo(eid),
        })

    # ── DE DÓNDE SALE EL ANCHO DE LA PARED ──────────────────────────────────
    # Orden de verdad, de más fiable a menos:
    #   1. El que ha tecleado el usuario (ancho_real). Manda siempre.
    #   2. El que está ESCRITO en el plano/croquis (ancho_escrito).
    #   3. La SUMA de los módulos cuyas medidas están escritas.
    #   4. La estimación visual de la IA. Es la última, no la primera.
    # Antes se usaba siempre la 4 y se aplastaban contra ella las medidas
    # escritas: un croquis acotado a mano que sumaba 406 cm acababa metido en
    # una pared "de 280" y todos los muebles encogidos. Al revés.
    for pidx, pared in enumerate(paredes):
        if ancho_real and pidx == 0:
            continue                       # el dato del usuario ya se aplicó
        if pared.get("ancho_escrito"):
            continue                       # la cota del plano manda sobre la suma
        del_suelo = [e for e in elementos
                     if e["pared_idx"] == pidx and e.get("fila") == "bajo"]
        escritos = [e for e in del_suelo if e.get("medida_escrita")]
        if del_suelo:
            suma = sum(e["ancho"] for e in del_suelo)
            if suma > 0 and en_rango(suma, "ancho_pared"):
                if suma != pared["ancho"]:
                    avisos.append(f"Pared {pidx+1}: el ancho se ajusta a la suma real de módulos ({suma} cm).")
                    pared["ancho"] = suma
            avisos.append(
                f"Pared {pidx+1}: el ancho pasa de {pared['ancho']} cm (estimado) a "
                f"{suma} cm, que es lo que suman las medidas escritas en el plano.")
            pared["ancho"] = int(suma)

    # Cuadrar cada pared: la suma de anchos DEBE coincidir con el ancho de pared.
    # Criterio de arquitecto técnico:
    #  · Los electrodomésticos (ancho fijo) NO se tocan nunca.
    #  · El resto (muebles, cajoneras) se ajusta proporcionalmente al hueco libre.
    #  · Si sobra hueco y no hay módulo flexible, se añade un RELLENO/costado real
    #    (es lo que se hace en obra), en vez de inflar los módulos existentes.
    finales = []
    no_cabe = False
    descuadres = []
    # Cada pared tiene DOS filas y cada una se cuadra por separado. Meterlas en
    # el mismo reparto era el fallo: los altos comían ancho de suelo y la suma
    # se disparaba por encima del ancho real de la pared.
    for pidx, pared in enumerate(paredes):
        for fila in ("bajo", "alto"):
            grupo, no_cabe_f, aviso_f = _cuadrar_fila(
                [e for e in elementos if e["pared_idx"] == pidx and e.get("fila") == fila],
                pared, pidx, fila, avisos)
            no_cabe = no_cabe or no_cabe_f
            if aviso_f:
                descuadres.append(aviso_f)
            finales.extend(grupo)

    if not finales:
        return {"ok": False, "motivo": "No hay módulos válidos que dibujar.",
                "avisos": avisos, "paredes": paredes, "elementos": []}
    if no_cabe or descuadres:
        # No se dibuja una pared cuyos módulos no suman su ancho: un alzado con
        # muebles saliéndose de la pared es peor que no tener alzado, porque
        # parece bueno. Regla de CLAUDE.md: la suma CUADRA, exactamente.
        return {"ok": False,
                "motivo": (descuadres[0] if descuadres
                           else "La composición no cabe en la pared indicada."),
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


def _cuadrar_fila(grupo, pared, pidx, fila, avisos):
    """Cuadra UNA fila (suelo o colgada) de UNA pared con el ancho de la pared.

    Devuelve (modulos, no_cabe, descuadre). `descuadre` no es None cuando, después
    de intentarlo todo, la suma sigue sin coincidir: entonces no se dibuja.

    La fila de altos NO se rellena: una cocina puede llevar altos solo en parte
    de la pared, y meter un "relleno colgado" para cuadrar sería inventarse un
    mueble. Lo que sí se exige es que no se pase del ancho.
    """
    # Un RELLENO calculado es una consecuencia, no un dato: se tira y se vuelve a
    # calcular. Si se deja, el reparto proporcional lo trata como un mueble más y
    # `snap_ancho` lo sube al mínimo de catálogo: cuatro rellenos de 1-2 cm se
    # convertían en cuatro de 15, o sea 60 cm de relleno inventado que hacían que
    # la composición dejara de caber. (El relleno ESCRITO en un plano sí es un
    # dato y se respeta.)
    grupo = [e for e in grupo
             if not (e["id"] == "relleno" and not e.get("medida_escrita"))]
    grupo = sorted(grupo, key=lambda e: e["posicion_cm"])
    if not grupo:
        return [], False, None
    no_cabe = False
    objetivo = pared["ancho"]
    etiqueta_fila = "de suelo" if fila == "bajo" else "colgados"

    for e in grupo:
        if e["id"] in ANCHO_FIJO:
            e["ancho"] = ANCHO_FIJO[e["id"]]
            e["anchoFijo"] = True
        elif e.get("medida_escrita"):
            # Una medida escrita en el plano es un DATO, no una estimación: no se
            # reescala para cuadrar. Si al final no cuadra, se dice — no se falsea.
            e["anchoFijo"] = True
    fijos = [e for e in grupo if e.get("anchoFijo")]
    flex = [e for e in grupo if not e.get("anchoFijo")]
    suma_fijos = sum(e["ancho"] for e in fijos)
    libre = objetivo - suma_fijos

    if libre < 0:
        no_cabe = True
        avisos.append(
            f"Pared {pidx+1} ({etiqueta_fila}): solo los electrodomésticos ocupan "
            f"{suma_fijos} cm y la pared mide {objetivo} cm. La composición NO cabe: "
            f"revisa medidas o módulos.")
    elif flex:
        suma_flex = sum(e["ancho"] for e in flex)
        if suma_flex > 0 and suma_flex != libre and (fila == "bajo" or suma_flex > libre):
            factor = libre / suma_flex if suma_flex else 1
            # Solo se reescala si el ajuste es razonable (±35%). Un desfase mayor
            # significa que faltan o sobran módulos, no que midan otra cosa.
            if 0.65 <= factor <= 1.35:
                for e in flex:
                    e["ancho"] = snap_ancho(e["ancho"] * factor)
                avisos.append(f"Pared {pidx+1} ({etiqueta_fila}): módulos ajustados "
                              f"para cuadrar con {objetivo} cm.")
            elif fila == "bajo" or suma_fijos + suma_flex > objetivo:
                # En la fila de suelo un descuadre es un problema. En la de altos
                # NO: es normalísimo que los altos ocupen solo parte de la pared
                # (encima de una columna o de una ventana no van). Solo se avisa
                # si se PASAN del ancho.
                avisos.append(
                    f"Pared {pidx+1} ({etiqueta_fila}): los módulos suman "
                    f"{suma_fijos + suma_flex} cm frente a {objetivo} cm de pared. "
                    f"Faltan o sobran módulos.")
        resto = (objetivo - sum(e["ancho"] for e in grupo)) if fila == "bajo" \
            else min(0, objetivo - sum(e["ancho"] for e in grupo))
        # Un mueble tiene un ancho de CATÁLOGO (15, 20, 30, 40, 45, 50, 60...).
        # El sobrante no se mete estirando un mueble hasta 69 cm —eso no existe—
        # sino en un RELLENO, que es exactamente lo que se hace en obra.
        if resto < 0:
            # Sobra composición: se bajan módulos flexibles al estándar inferior,
            # empezando por el más ancho, hasta que quepa.
            for e in sorted(flex, key=lambda e: -e["ancho"]):
                if resto >= 0:
                    break
                menores = [w for w in ANCHOS_STD if w < e["ancho"]]
                if not menores:
                    continue
                nuevo_ancho = max(menores)
                resto += e["ancho"] - nuevo_ancho
                e["ancho"] = nuevo_ancho
                avisos.append(f"Pared {pidx+1} ({etiqueta_fila}): «{e['label']}» se reduce "
                              f"a {nuevo_ancho} cm para que la composición quepa.")
        if resto > 0 and fila == "bajo":
            grupo.append({"id": "relleno", "label": f"Relleno {int(resto)}",
                          "fila": "bajo", "pared_idx": pidx,
                          "posicion_cm": 0, "ancho": int(resto),
                          "alto": CASCO_BAJO_ALTO, "fondo": FONDO_BAJOS})
            avisos.append(f"Pared {pidx+1}: añadido relleno de {int(resto)} cm para cuadrar.")
    elif objetivo - suma_fijos > 0 and fila == "bajo":
        resto = objetivo - suma_fijos
        grupo.append({"id": "relleno", "label": f"Relleno {int(resto)}",
                      "fila": "bajo", "pared_idx": pidx,
                      "posicion_cm": 0, "ancho": int(resto),
                      "alto": CASCO_BAJO_ALTO, "fondo": FONDO_BAJOS})
        avisos.append(f"Pared {pidx+1}: hueco de {int(resto)} cm sin módulo; añadido relleno.")

    if fila == "bajo":
        # La fila de suelo va contigua de pared a pared: no hay huecos entre
        # muebles apoyados.
        x = 0
        for e in grupo:
            e["posicion_cm"] = x
            x += e["ancho"]
    else:
        # Los altos NO se recolocan desde el origen: van DONDE ESTÁN, encima de
        # su bajo. Empaquetarlos a la izquierda los movía de sitio y el alzado
        # dejaba de parecerse a la cocina. Solo se corrigen solapes y lo que se
        # salga de la pared.
        x_min = 0
        for e in grupo:
            pos = max(int(e.get("posicion_cm") or 0), x_min)
            pos = min(pos, max(0, objetivo - e["ancho"]))
            e["posicion_cm"] = pos
            x_min = pos + e["ancho"]

    # COMPROBACIÓN FINAL, la que faltaba. Antes se avisaba del descuadre y se
    # dibujaba igual: salían muebles fuera de la pared con cotas que no sumaban
    # el total. Un alzado así engaña más que la ausencia de alzado.
    suma = sum(e["ancho"] for e in grupo)
    descuadre = None
    if fila == "bajo" and suma != objetivo:
        descuadre = (f"Los módulos de la pared {pidx+1} suman {suma} cm y la pared mide "
                     f"{objetivo} cm. Sobran o faltan módulos: corrige la composición "
                     f"o el ancho de la pared.")
    elif fila == "alto" and suma > objetivo:
        descuadre = (f"Los muebles altos de la pared {pidx+1} suman {suma} cm y la pared "
                     f"mide {objetivo} cm. No caben: quita alguno o revisa sus anchos.")
    return grupo, no_cabe, descuadre
