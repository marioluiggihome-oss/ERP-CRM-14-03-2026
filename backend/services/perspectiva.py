# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
perspectiva.py — BOCETO EN PERSPECTIVA, dibujado desde los datos.

El master quiere el boceto a mano alzada de sus referencias: con profundidad y
punto de fuga, no el alzado plano. Esto arma la escena en 3D y la proyecta,
para poder dibujarla después con trazo de lápiz.

Cálculo puro, sin base de datos ni matplotlib, para poder probarlo.

POR QUÉ NO SE LE PIDE A UNA IA
------------------------------
Porque una IA redibuja, y al redibujar mueve cosas. Y en un boceto eso es peor
que en un render: un dibujo a lápiz se lee como "esto lo ha hecho el
diseñador", así que un módulo desplazado ahí tiene MÁS autoridad, no menos.
Aquí cada arista sale de un ancho o una altura reales.

LO QUE SE ELIGE Y LO QUE NO
---------------------------
Se elige la CÁMARA — dónde se pone el ojo y cuánto abarca. Eso es un punto de
vista, no una medida de la cocina: cambiarlo no cambia lo que se fabrica.

NO se elige ninguna dimensión. Si un elemento no trae ancho, no se dibuja con
uno "razonable": se deja fuera y se dice. Un mueble pintado con un ancho
inventado es exactamente el fallo que este ERP existe para evitar, y en
perspectiva ni siquiera se nota a simple vista.
"""
import math

# Altura del ojo al dibujar un interior: la de una persona de pie (cm).
# Es un punto de vista, no una medida de la cocina.
CAMARA_POR_DEFECTO = {
    "ojo": (-260.0, 150.0, -320.0),   # x, y (altura), z
    "objetivo": (150.0, 110.0, 100.0),
    "distancia_focal": 420.0,
}

# Altura del ojo de una persona de pie. Es un punto de vista, NO una medida de
# la cocina: cambiarlo no cambia lo que se fabrica.
ALTURA_OJO = 150.0
# A qué altura se mira. Un poco por debajo del ojo, que es como se mira una
# cocina de verdad: si se apunta al horizonte, el suelo desaparece y el dibujo
# pierde la profundidad que es justo lo que se busca aquí.
ALTURA_OBJETIVO = 110.0
# Distancia del ojo a la pared, en proporción al ancho que hay que enseñar.
# Más cerca exagera la fuga (parece un gran angular); más lejos la aplana hasta
# parecer un alzado. 1,15 da el escorzo de un boceto de interiorismo.
DISTANCIA_RELATIVA = 1.15
# Cuánto se desplaza el ojo hacia un lado. Centrado da UN punto de fuga (una
# vista frontal, plana); descentrado da dos, que es como están dibujadas las
# referencias del master.
DESPLAZAMIENTO_LATERAL = 0.18
DISTANCIA_FOCAL = 420.0
# Fondo máximo de un mueble (cm): el ojo nunca puede quedar dentro de los
# muebles. Ver `camara_para`.
FONDO_MAXIMO = 65.0


def _num(v):
    if v in (None, ""):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ─── Proyección ─────────────────────────────────────────────────────────────

def _base_camara(camara):
    """Ejes de la cámara: hacia dónde mira, qué es su derecha y su arriba."""
    ox, oy, oz = camara["ojo"]
    tx, ty, tz = camara["objetivo"]
    fx, fy, fz = tx - ox, ty - oy, tz - oz
    n = math.sqrt(fx * fx + fy * fy + fz * fz) or 1.0
    f = (fx / n, fy / n, fz / n)
    # DERECHA = adelante x arriba-del-mundo, con arriba = (0,1,0). Sale
    # (-f_z, 0, f_x).
    #
    # Esto estaba al reves —se calculaba (f_z, 0, -f_x), que es arriba x
    # adelante— y el boceto entero salia EN ESPEJO. Y no chirriaba: la cocina
    # se veia perfecta, solo que con el fregadero en el lado contrario. La
    # vertical si estaba bien, asi que no habia nada raro que mirar.
    rx, ry, rz = -f[2], 0.0, f[0]
    n = math.sqrt(rx * rx + ry * ry + rz * rz) or 1.0
    r = (rx / n, ry / n, rz / n)
    # ARRIBA = derecha x adelante (en este orden). Al reves sale ABAJO, y el
    # dibujo entero queda del reves sin que nada falle: los numeros salen, las
    # cajas salen, y la cocina aparece colgada del techo.
    u = (r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0])
    return f, r, u


def proyectar(punto, camara=None):
    """Lleva un punto 3D al plano del dibujo.

    Devuelve (x, y, profundidad) o None si el punto queda DETRÁS de la cámara.
    Los puntos de detrás no se "acercan": no se dibujan. Proyectarlos daría
    figuras del revés, que es como se cuelan los dibujos imposibles.
    """
    cam = camara or CAMARA_POR_DEFECTO
    ox, oy, oz = cam["ojo"]
    f, r, u = _base_camara(cam)
    dx, dy, dz = punto[0] - ox, punto[1] - oy, punto[2] - oz

    prof = dx * f[0] + dy * f[1] + dz * f[2]
    if prof <= 1e-6:
        return None

    dcha = dx * r[0] + dy * r[1] + dz * r[2]
    arr = dx * u[0] + dy * u[1] + dz * u[2]
    k = cam["distancia_focal"] / prof
    return (dcha * k, arr * k, prof)


# ─── La escena, armada desde los datos ──────────────────────────────────────

def origen_de_pared(indice, tipo, paredes):
    """Dónde empieza cada pared y hacia dónde corre, según el tipo de cocina.

    Lineal: una pared. En L: la segunda gira 90°. En U: la tercera vuelve.
    Las longitudes son las REALES de cada pared, no un lienzo fijo.
    """
    t = (tipo or "lineal").lower()
    anchos = [(_num(p.get("ancho")) or 0.0) for p in paredes]

    if indice == 0:
        return (0.0, 0.0), (1.0, 0.0)
    if indice == 1 and t in ("l", "u", "g", "paralela"):
        if t == "paralela":
            # Enfrentada, a 240 cm, y corriendo en sentido contrario.
            return (anchos[0], 240.0), (-1.0, 0.0)
        return (anchos[0], 0.0), (0.0, 1.0)
    if indice == 2 and t in ("u", "g"):
        return (anchos[0], anchos[1] if len(anchos) > 1 else 0.0), (-1.0, 0.0)
    # Cualquier pared extra sigue a continuación de la primera.
    return (0.0, 0.0), (1.0, 0.0)


def montar_escena(distribucion, altura_modulo=None, fondo_modulo=None, es_alto=None):
    """Convierte la distribución en cajas 3D con medidas reales.

    `altura_modulo(id)`, `fondo_modulo(id)` y `es_alto(id, label)` se inyectan
    (vienen de kitchen_geometry) para no duplicar aquí el criterio de
    fabricación.

    `es_alto` DECIDE SI EL MUEBLE CUELGA O SE APOYA, y por eso se inyecta como
    los otros dos. Antes se resolvía aquí mirando si la etiqueta empezaba por
    «A», y ese atajo no coincide con el criterio de fábrica: el `microondas`
    es un mueble alto y no empieza por A —se habría dibujado en el suelo—, y
    cualquier cosa rotulada «Armario…» habría salido colgada del techo. Dos
    criterios para lo mismo acaban separándose, y en perspectiva un mueble a
    la altura equivocada no llama la atención.

    Devuelve (cajas, omitidos). En `omitidos` van los elementos que NO se han
    podido dibujar por falta de datos: se informan, no se rellenan.
    """
    d = distribucion or {}
    paredes = d.get("paredes") or []
    elementos = d.get("elementos") or []
    alto_de = altura_modulo or (lambda _id: 80)
    fondo_de = fondo_modulo or (lambda _id: 58)
    # Respaldo mínimo por si se usa el módulo suelto (pruebas): la «A» del
    # código MV. Es peor que el criterio de fábrica, y por eso se inyecta.
    cuelga = es_alto or (lambda eid, label="":
                         str(label or "").upper().startswith("A")
                         or str(eid or "").upper().startswith("A"))

    cajas, omitidos = [], []
    # UN CONTADOR POR FILA, no uno por pared. Los altos y los bajos son DOS
    # filas que corren cada una por su cuenta a lo largo del muro: el alto va
    # ENCIMA del bajo, no a continuación. Con un contador único, una pared con
    # 330 cm de bajos colocaba el primer alto en el centímetro 330 — o sea
    # fuera del muro de 360 y sin nada debajo. En perspectiva eso no chirría:
    # se ve una cocina larga y ya.
    avance = {}

    for el in elementos:
        ancho = _num(el.get("ancho"))
        if ancho is None or ancho <= 0:
            # NO se dibuja con un ancho "razonable". Se deja fuera y se dice.
            omitidos.append({"id": el.get("id"), "label": el.get("label"),
                             "motivo": "sin ancho"})
            continue

        pidx = int(el.get("pared_idx") or 0)
        if pidx >= len(paredes):
            omitidos.append({"id": el.get("id"), "label": el.get("label"),
                             "motivo": f"pared {pidx} inexistente"})
            continue

        (ox, oz), (dx, dz) = origen_de_pared(pidx, d.get("tipo"), paredes)
        eid = str(el.get("id") or "")
        alto = float(alto_de(eid))
        fondo = float(fondo_de(eid))
        # Los altos cuelgan; los bajos se apoyan en el zócalo. Quién es alto lo
        # decide el criterio de fábrica que se inyecta, no un atajo local.
        es_colgado = bool(cuelga(eid, el.get("label") or ""))
        base = 145.0 if es_colgado else 10.0

        # Cada fila avanza por su cuenta: los altos empiezan otra vez desde el
        # principio de la pared, encima de los bajos.
        fila = (pidx, es_colgado)
        recorrido = avance.get(fila, 0.0)
        avance[fila] = recorrido + ancho

        x0, z0 = ox + dx * recorrido, oz + dz * recorrido
        x1, z1 = ox + dx * (recorrido + ancho), oz + dz * (recorrido + ancho)
        # El fondo sale perpendicular a la pared.
        nx, nz = -dz, dx

        cajas.append({
            "id": eid, "label": el.get("label") or eid, "pared": pidx,
            "ancho": ancho, "alto": alto, "fondo": fondo,
            "base": base,
            "esquinas": [
                (x0, base, z0), (x1, base, z1),
                (x1, base + alto, z1), (x0, base + alto, z0),
                (x0 + nx * fondo, base, z0 + nz * fondo),
                (x1 + nx * fondo, base, z1 + nz * fondo),
                (x1 + nx * fondo, base + alto, z1 + nz * fondo),
                (x0 + nx * fondo, base + alto, z0 + nz * fondo),
            ],
        })

    return cajas, omitidos


def camara_para(distribucion):
    """EL PUNTO DE VISTA, derivado de la cocina que hay que enseñar.

    Esto es lo que faltaba para que el boceto en perspectiva pareciera un
    boceto de interiorismo y no una caja vista de lejos.

    Tres decisiones, y las tres son de ENCUADRE, no de medida:

    1. **El ojo va DENTRO de la estancia.** Los muebles salen de la pared hacia
       el interior, así que mirando desde el otro lado se verían por detrás.
       Parece obvio y no lo es: la cámara por defecto miraba desde `z` negativa
       —o sea desde detrás de la pared— y el dibujo salía igualmente, porque una
       caja vista por detrás sigue siendo una caja.

    2. **Descentrado.** Centrado sale UN punto de fuga y el dibujo se lee casi
       como un alzado. Descentrado salen dos, que es como están dibujadas las
       referencias que enseñó el master.

    3. **La distancia se saca del ancho REAL de la pared.** Una cocina de 6 m y
       una de 2,4 m no se dibujan desde la misma distancia: con una fija, la
       grande no cabe y la pequeña sale minúscula.

    NO se inventa ninguna medida de la cocina: sin paredes con ancho se
    devuelve la cámara por defecto, y quien dibuja ya decide si sigue.
    """
    d = distribucion or {}
    paredes = d.get("paredes") or []
    anchos = [(_num(p.get("ancho")) or 0.0) for p in paredes]
    if not anchos or anchos[0] <= 0:
        return dict(CAMARA_POR_DEFECTO)

    tipo = str(d.get("tipo") or "lineal").lower()
    a0 = anchos[0]
    a1 = anchos[1] if len(anchos) > 1 and anchos[1] > 0 else 0.0

    # Distancia de retroceso: proporcional al ancho que hay que encuadrar, y
    # nunca menor que el fondo de un mueble — si no, el ojo quedaría DENTRO de
    # los armarios y la mitad de la cocina se proyectaría detrás de la cámara.
    retroceso = max(a0 * DISTANCIA_RELATIVA, FONDO_MAXIMO * 2.5)

    if tipo in ("l", "u", "g"):
        # En L la segunda pared corre hacia +z desde el final de la primera, y
        # sus muebles salen hacia -x. Así que la esquina de trabajo está en
        # (a0, 0) y el hueco libre queda en x pequeña, z grande: ahí va el ojo,
        # mirando a la esquina. Es el punto desde el que se fotografía una
        # cocina en L.
        ojo = (-a0 * DESPLAZAMIENTO_LATERAL, ALTURA_OJO, retroceso + (a1 * 0.25))
        objetivo = (a0 * 0.55, ALTURA_OBJETIVO, a1 * 0.20)
    else:
        # Lineal y paralela: de frente a la pared, desplazado a un lado.
        ojo = (a0 * (0.5 - DESPLAZAMIENTO_LATERAL), ALTURA_OJO, retroceso)
        objetivo = (a0 * 0.5, ALTURA_OBJETIVO, 0.0)

    return {"ojo": ojo, "objetivo": objetivo, "distancia_focal": DISTANCIA_FOCAL}


def suelo_y_paredes(distribucion):
    """El cascarón de la estancia: las aristas que dan la profundidad.

    Sin esto los muebles flotan en el vacío y el dibujo no se lee como una
    habitación. Con esto aparecen las líneas que van al punto de fuga, que es
    lo que hace que un boceto parezca un boceto.

    LO QUE SE DIBUJA Y LO QUE NO: se dibujan las paredes cuyo ancho y alto son
    DATOS REALES, y una retícula de suelo que se desvanece hacia el
    espectador. NO se cierra la habitación por detrás: el fondo de la estancia
    no lo sabe nadie, y ponerle una pared a una distancia "que quede bien" es
    inventarse una medida —además la más creíble de todas, porque en
    perspectiva nadie la comprueba—.
    """
    d = distribucion or {}
    paredes = d.get("paredes") or []
    if not paredes:
        return {"paredes": [], "suelo": [], "alto": 0.0}

    tipo = str(d.get("tipo") or "lineal").lower()
    alto = _num(paredes[0].get("alto")) or 0.0
    if alto <= 0:
        # Sin altura de techo no se dibuja la pared: se dibujarían muebles
        # colgando de una línea que no mide nada.
        alto = 0.0

    muros, anchos = [], [(_num(p.get("ancho")) or 0.0) for p in paredes]
    for i, ancho in enumerate(anchos):
        if ancho <= 0 or alto <= 0:
            continue
        (ox, oz), (dx, dz) = origen_de_pared(i, tipo, paredes)
        x0, z0 = ox, oz
        x1, z1 = ox + dx * ancho, oz + dz * ancho
        muros.append({
            "indice": i,
            "esquinas": [(x0, 0.0, z0), (x1, 0.0, z1),
                         (x1, alto, z1), (x0, alto, z0)],
        })

    # Retícula de suelo: líneas paralelas a la pared 0, cada 50 cm, hasta la
    # posición del ojo. Son las que van al punto de fuga.
    a0 = anchos[0] if anchos else 0.0
    suelo = []
    if a0 > 0:
        cam = camara_para(distribucion)
        # Hasta CERCA del ojo, no hasta el ojo. Un punto a un palmo de la
        # cámara se proyecta prácticamente al infinito: esas líneas no aportan
        # profundidad, solo estiran el dibujo.
        hasta = max(cam["ojo"][2] * 0.72, 100.0)
        paso = 50.0
        z = 0.0
        while z <= hasta + 1e-6:
            suelo.append([(0.0, 0.0, z), (a0, 0.0, z)])
            z += paso
        # Y las perpendiculares, cada 50 cm a lo ancho.
        x = 0.0
        while x <= a0 + 1e-6:
            suelo.append([(x, 0.0, 0.0), (x, 0.0, hasta)])
            x += paso

    return {"paredes": muros, "suelo": suelo, "alto": alto}


def ordenar_por_profundidad(cajas, camara=None):
    """De lejos a cerca, para que lo cercano tape a lo lejano al dibujar.

    Sin esto los muebles del fondo se pintan encima de los de delante y el
    dibujo se lee al revés.
    """
    cam = camara or CAMARA_POR_DEFECTO
    ox, oy, oz = cam["ojo"]

    def dist(c):
        xs = [p[0] for p in c["esquinas"]]
        ys = [p[1] for p in c["esquinas"]]
        zs = [p[2] for p in c["esquinas"]]
        cx, cy, cz = sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs)
        return (cx - ox) ** 2 + (cy - oy) ** 2 + (cz - oz) ** 2

    return sorted(cajas, key=dist, reverse=True)
