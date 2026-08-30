# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
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

# PIEZAS A MEDIDA: su ancho es el que sea, y NO se ajusta a un estándar de
# catálogo. No son muebles: son tableros.
#
# Lo vio el master el 24/08 con un plano suyo en MILÍMETROS: los costados
# decorativos son de 18 mm, o sea 1,8 cm, y `snap_ancho` los subía al mueble
# más estrecho que existe —15 cm—, que es OCHO VECES más. Con tres costados en
# la cocina, eso son 45 cm de mueble que no existe; el propio validador acabó
# avisando de que «los módulos suman 765 cm» en una pared de 425.
#
# Es el mismo caso que el relleno, que ya estaba exceptuado por lo mismo. Se
# generaliza en vez de añadir un `if` más: la próxima pieza a medida que
# aparezca (una tapa, un remate) tendría el mismo problema.
PIEZAS_A_MEDIDA = ("relleno", "costado", "panel", "lateral", "tapa", "remate",
                   "regleta", "cornisa", "zocalo", "zócalo")


def es_a_medida(elem_id: str) -> bool:
    """¿Es un tablero a medida en vez de un mueble de catálogo?"""
    t = str(elem_id or "").lower()
    return any(p in t for p in PIEZAS_A_MEDIDA)
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
    # LA LAVADORA FALTABA, y una lavadora mide 60 como la que más. Al no estar
    # aquí se trataba como un mueble FLEXIBLE, o sea que se estiraba y se
    # encogía para cuadrar la pared: en la cocina del 30/08 salió dibujada de
    # 50. Un electrodoméstico no cambia de tamaño porque falte sitio.
    "lavadora": 60, "secadora": 60, "lavasecadora": 60,
}

# QUÉ ANCHOS EXISTEN DE VERDAD PARA CADA APARATO.
#
# `ANCHO_FIJO` dice lo que mide uno CUANDO NADIE HA DICHO NADA. Esta tabla dice
# algo distinto y hacía falta: cuáles de los anchos que puede traer un diseño son
# medidas REALES de ese aparato.
#
# Sin ella había que elegir entre dos males, y los dos se han visto:
#   · Hacer caso siempre al diseño → una placa «de 80» (que no existe: son 60 o
#     90) se dibujaba y se pedía.
#   · No hacerle caso nunca → la placa de 90 del master salía de 60, y los 30 cm
#     sobrantes estiraban el mueble de al lado.
#
# Con la tabla: si el ancho del diseño es uno de los que existen, MANDA EL
# DISEÑO; si no, se cae al de catálogo y SE DICE en los avisos. Son medidas de
# fabricación, no una preferencia.
# SOLO LOS ANCHOS QUE NO ADMITEN DUDA. La lista es corta a propósito: cada
# entrada de más es un ancho que se acepta del diseño sin comprobarlo, y una
# estimación floja de la IA («placa de 70») se colaría como si fuera un dato.
# Con la lista corta, esa cae al de catálogo y se avisa; la placa de 90 —que
# existe y es corriente— se respeta. Añadir un ancho aquí es una decisión de
# fabricación: se consulta antes.
ANCHOS_APARATO = {
    "placa": (30, 45, 60, 90),         # domino, la de siempre y la de 90
    "campana": (60, 90, 120),
    "lavavajillas": (45, 60),          # el de 45 es el estrecho de toda la vida
    "lavadora": (60,),
    "secadora": (60,),
    "lavasecadora": (60,),
    "horno": (60,),
    "microondas": (60,),
    "columna_hornos": (60,),
    "frigorifico": (60, 90, 120),      # el de 120 es el side by side
    "congelador": (60,),
    "vinoteca": (15, 30, 60),
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
                        # Ancho corregido a mano: manda sobre todo lo demás y se
                        # dice en pantalla. Implica `ancho_escrito`.
                        "ancho_corregido": bool(p.get("ancho_corregido")),
                        # Si la cota está ESCRITA en el plano, manda sobre la suma
                        # de módulos. La bandera tiene que sobrevivir a la ida y
                        # vuelta (detectar → dibujar), o la regla no sirve de nada.
                        "ancho_escrito": bool(p.get("ancho_escrito") or p.get("ancho_corregido"))})

    if not paredes:
        # Sin datos válidos NO se inventa una cocina: se deja explícito.
        return {"ok": False, "motivo": "No hay ninguna pared con medidas válidas.",
                "avisos": avisos, "paredes": [], "elementos": []}

    # El dato del usuario SIEMPRE manda sobre la estimación de la IA.
    #
    # Salvo que haya corregido esa pared A MANO en el panel de distribución, que
    # es más reciente y más concreto que el ancho de la estancia. Los dos los ha
    # tecleado él: gana el último que ha dicho.
    if paredes and paredes[0].get("ancho_corregido"):
        ancho_real = None
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
        # ¿VIENE SIN ANCHO, o viene con un ancho malo? No es lo mismo y hasta
        # ahora se trataban igual: los dos acababan en 15 cm con un aviso de
        # «no es fabricable». Un módulo del que NADIE sabe el ancho se dibuja
        # —un alzado con un hueco tampoco sirve— pero su cota se rotula «?»,
        # nunca un número (CLAUDE.md, regla 7).
        sin_ancho = e.get("ancho") in (None, "")
        try:
            anc = float(e.get("ancho") or 0)
            pos = float(e.get("posicion_cm") or 0)
            pidx = int(e.get("pared_idx") or 0)
        except (TypeError, ValueError):
            continue
        eid = str(e.get("id") or "mueble").lower().strip().replace(" ", "_")
        if es_a_medida(eid):
            # Un tablero a medida NO se ajusta al catálogo. El relleno ya estaba
            # así —su ancho ES el hueco que sobra—, y un costado decorativo es
            # el mismo caso por el otro extremo: 18 mm subidos a 15 cm.
            #
            # Se guarda con DECIMAL: redondear 1,8 a 2 y luego a entero es como
            # empezó el problema. Un tablero de 18 mm tiene que poder decir que
            # mide 1,8.
            anc_snap = round(max(0.1, anc), 1)
            if anc_snap >= 10:
                # Un costado de 10 cm o más no existe: son 16-19 mm de tablero.
                # Casi seguro que el plano venía en MILÍMETROS y se ha leído
                # como centímetros. NO se convierte a la brava —eso sería
                # inventar una medida—: se dice, y lo corrige quien lo sabe.
                avisos.append(
                    f"«{eid}»: {anc_snap:g} cm de tablero no existe (un costado "
                    f"son 16-19 mm). ¿El plano estaba en milímetros? Serían "
                    f"{anc_snap / 10:g} cm. Corrígelo antes de pedir.")
        else:
            anc_snap = snap_ancho(anc)
            if sin_ancho:
                # Se dice lo que pasa de verdad, que no es que la medida sea
                # mala: es que no hay medida. Antes ponía «ancho 0 cm no es
                # fabricable», que despista a quien lo lee.
                avisos.append(f"Módulo «{eid}»: nadie ha dado su ancho. Se dibuja "
                              f"con {anc_snap} cm para que el alzado cierre, pero "
                              f"su cota sale como «?». Ponle la medida antes de pedir.")
            elif not en_rango(anc, "ancho_modulo"):
                avisos.append(f"Módulo «{eid}»: ancho {int(anc)} cm no es fabricable; "
                              f"se ajusta a {anc_snap} cm.")
        etiqueta = str(e.get("label") or eid or "Módulo")[:24]
        escrita = bool(e.get("medida_escrita"))
        # CORREGIDA A MANO por el usuario. Cuenta como medida escrita —de hecho
        # es la más fiable de todas: no la ha leído nadie, la ha dicho él— pero
        # se distingue para poder decirlo en pantalla. Si esta bandera no
        # sobreviviera a la ida y vuelta, el panel volvería a presentar lo que
        # ha tecleado el master como una estimación de la IA.
        corregida = bool(e.get("corregida"))
        if corregida:
            escrita = True
        # La FILA (suelo o colgado) se decide aquí, una sola vez, y viaja con el
        # módulo. El dibujo ya no tiene que adivinarlo por el id.
        fila = "alto" if es_alto(eid, etiqueta) else "bajo"
        elementos.append({
            "id": eid,
            "label": etiqueta,
            "fila": fila,
            "medida_escrita": escrita,
            "corregida": corregida,
            # Viaja con el módulo hasta el dibujo: es lo que hace que se rotule
            # «?» en vez de un número que no ha medido nadie.
            "ancho_desconocido": sin_ancho,
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
        # SOLO si hay cotas escritas. Sin esta condición el ancho de pared pasaba
        # a ser SIEMPRE la suma de los módulos, y entonces cualquier composición
        # "cabía": la pared se estiraba hasta ella. Así, una pared de 324 cm con
        # 310 cm de muebles se convertía en una pared de 310 (y el hueco de 14 cm
        # desaparecía del plano), y 240 cm de electrodomésticos "cabían" en una
        # pared de 120. El validador dejaba de validar nada.
        if escritos:
            suma = sum(e["ancho"] for e in del_suelo)
            if suma > 0 and en_rango(suma, "ancho_pared") and suma != pared["ancho"]:
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


# HASTA DÓNDE UN RELLENO SIGUE SIENDO UN RELLENO.
#
# Cuando los módulos no llegan al ancho de la pared, el validador mete un relleno
# para cuadrar. Eso está bien y es lo que se hace en obra... hasta cierto punto.
# Un relleno es una tira de tablero de unos pocos centímetros. Si lo que falta
# son 195 cm, eso no es un relleno: es que falta un mueble, o que la lectura del
# croquis salió mal.
#
# Sin este tope, una distribución así salía con `ok: True`, se dibujaba, y ese
# «relleno» podía acabar volcado al presupuesto como una línea de material.
# 60 cm es el ancho de mueble más corriente: si cabe un mueble entero en el
# hueco, es que falta el mueble.
RELLENO_MAXIMO = 60

# Ancho de dibujo cuando un módulo llega sin ancho. NO es una medida: es lo que
# se pinta para que el alzado cierre. Nunca se ROTULA (ver `cota_de_ancho`).
ANCHO_DIBUJO_SIN_DATO = 60


def cota_de_ancho(elemento):
    """Qué ancho se DIBUJA y qué cota se ESCRIBE para un módulo.

    Son dos cosas distintas y confundirlas es como se cuela una medida
    inventada en un plano que va a fábrica. Devuelve `(ancho, cota, origen)`:

    · `medida_escrita` -> ("60", "escrita")   el cliente lo puso en su croquis.
    · ancho derivado   -> ("~60", "estimada") lo cuadró `validar_distribucion`
      contra el ancho REAL de la pared: es una estimación con fundamento, y el
      «~» es la marca de toda la vida para decirlo.
    · sin ancho        -> ("?", "sin_dato")   no lo sabe nadie.

    El tercer caso es el arreglo del 23/08/2026. Antes caía en el segundo y se
    rotulaba «~60»: ese 60 no lo había medido ni deducido nadie —es el valor de
    respaldo del código— y salía impreso como si fuera una estimación leída del
    dibujo. Eso es inventarse una cota (regla 7 de CLAUDE.md) y encima con
    coartada, que es peor que inventarla a pelo: el «~» le daba credibilidad.

    El módulo se sigue dibujando, porque un alzado con un hueco tampoco sirve.
    Lo que no se hace es escribir un número que nadie sabe.
    """
    dado = (elemento or {}).get("ancho")
    ancho = int(dado or ANCHO_DIBUJO_SIN_DATO)
    # `ancho_desconocido` lo pone `validar_distribucion` cuando el módulo llegó
    # SIN ancho. Se mira lo primero porque para entonces el módulo ya lleva un
    # ancho de dibujo puesto —hace falta para cerrar el alzado— y sin esta
    # bandera volveríamos a rotular «~15» de algo que no sabe nadie, que es el
    # fallo que se arregló el 23/08 y que se estaba colando otra vez.
    if (elemento or {}).get("ancho_desconocido"):
        return ancho, "?", "sin_dato"
    if (elemento or {}).get("medida_escrita"):
        return ancho, f"{ancho}", "escrita"
    if dado:
        return ancho, f"~{ancho}", "estimada"
    return ancho, "?", "sin_dato"


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
        if e.get("medida_escrita"):
            # Una medida escrita en el plano es un DATO, no una estimación: no se
            # reescala para cuadrar. Si al final no cuadra, se dice — no se falsea.
            #
            # Y GANA TAMBIÉN A `ANCHO_FIJO`. Antes se miraba la tabla PRIMERO, así
            # que una placa de 90 escrita por el cliente salía dibujada de 60 —y
            # sin marca de estimada, o sea presentando el 60 como dato
            # confirmado—. No es un caso raro: el propio glosario de la casa
            # tiene «Bajo Placa 2 Gavetas: 90 cm», y un side by side de 120 se
            # quedaba igualmente en 60. Se perdían 30 cm de encimera y de
            # frentes en el presupuesto, sin un solo aviso.
            #
            # `ANCHO_FIJO` es lo que mide un electrodoméstico CUANDO NADIE HA
            # DICHO NADA. En cuanto alguien lo dice, manda quien lo dijo.
            e["anchoFijo"] = True
        elif e["id"] in ANCHO_FIJO:
            # `ANCHO_FIJO` es lo que mide un electrodoméstico CUANDO NADIE HA
            # DICHO NADA. Eso estaba escrito aquí arriba... y no era lo que
            # hacía el código: pisaba el ancho AUNQUE VINIERA EN LA
            # DISTRIBUCIÓN, y solo respetaba el que traía la marca
            # `medida_escrita` (una cota leída del plano).
            #
            # Un ancho que llega en el elemento YA ES ALGUIEN DICIÉNDOLO: lo ha
            # leído el detector del diseño del master, o lo ha tecleado él en el
            # panel. Pisarlo hacía que el alzado no fuera su cocina, y por dos
            # sitios a la vez: la placa de 90 salía de 60, y esos 30 cm
            # sobrantes ESTIRABAN el mueble de al lado —una cajonera de 90 se
            # dibujaba de 120—. Dos módulos mal por cada aparato.
            #
            # Ahora el catálogo solo entra cuando de verdad no hay dato. Y si lo
            # que viene no es una medida de catálogo, se DICE en los avisos en
            # vez de corregirlo por detrás: una placa de 90 existe, y si alguien
            # ha escrito 47 hay que enterarse, no taparlo.
            _reales = ANCHOS_APARATO.get(e["id"], ())
            if e.get("ancho_desconocido"):
                e["ancho"] = ANCHO_FIJO[e["id"]]
            elif _reales and e["ancho"] not in _reales:
                # Ese ancho no existe en ese aparato: casi seguro es una lectura
                # floja del diseño. Se cae al de catálogo Y SE DICE — corregir
                # por detrás es como se cuela una medida inventada en un plano
                # que va a fábrica.
                avisos.append(
                    f"«{e['label']}»: {e['ancho']:g} cm no es un ancho real de ese "
                    f"aparato (los hay de {', '.join(str(a) for a in _reales)}). "
                    f"Se dibuja con {ANCHO_FIJO[e['id']]} cm; confírmalo antes de pedir.")
                e["ancho"] = ANCHO_FIJO[e["id"]]
            elif e["ancho"] != ANCHO_FIJO[e["id"]]:
                # Existe, pero no es el corriente (una placa de 90, un side by
                # side de 120). Manda el diseño y se deja constancia.
                avisos.append(
                    f"«{e['label']}»: se dibuja con los {e['ancho']:g} cm del "
                    f"diseño (el más corriente de ese aparato es "
                    f"{ANCHO_FIJO[e['id']]} cm). Confírmalo antes de pedir.")
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
            if resto > RELLENO_MAXIMO:
                no_cabe = True
                avisos.append(
                    f"Pared {pidx+1}: faltan {int(resto)} cm de muebles. Un relleno "
                    f"de ese tamaño no existe (son unos pocos centímetros de "
                    f"tablero): ahí cabe un mueble entero. Revisa la composición.")
            else:
                grupo.append({"id": "relleno", "label": f"Relleno {int(resto)}",
                              "fila": "bajo", "pared_idx": pidx,
                              "posicion_cm": 0, "ancho": int(resto),
                              "alto": CASCO_BAJO_ALTO, "fondo": FONDO_BAJOS})
                avisos.append(f"Pared {pidx+1}: añadido relleno de {int(resto)} cm para cuadrar.")
    elif objetivo - suma_fijos > 0 and fila == "bajo":
        resto = objetivo - suma_fijos
        if resto > RELLENO_MAXIMO:
            no_cabe = True
            avisos.append(
                f"Pared {pidx+1}: hay {int(resto)} cm de pared sin ningún mueble. "
                f"Eso no se tapa con un relleno: falta composición.")
        else:
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
