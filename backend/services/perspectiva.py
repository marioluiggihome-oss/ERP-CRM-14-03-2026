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
    # Derecha = adelante x arriba-del-mundo, normalizado.
    rx, ry, rz = f[2] * 1.0 - f[1] * 0.0, f[0] * 0.0 - f[2] * 0.0, f[1] * 0.0 - f[0] * 1.0
    n = math.sqrt(rx * rx + ry * ry + rz * rz) or 1.0
    r = (rx / n, ry / n, rz / n)
    # ARRIBA = adelante x derecha (en este orden). Al reves sale ABAJO, y el
    # dibujo entero queda del reves sin que nada falle: los numeros salen, las
    # cajas salen, y la cocina aparece colgada del techo.
    u = (f[1] * r[2] - f[2] * r[1], f[2] * r[0] - f[0] * r[2], f[0] * r[1] - f[1] * r[0])
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

def _origen_de_pared(indice, tipo, paredes):
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


def montar_escena(distribucion, altura_modulo=None, fondo_modulo=None):
    """Convierte la distribución en cajas 3D con medidas reales.

    `altura_modulo(id)` y `fondo_modulo(id)` se inyectan (vienen de
    kitchen_geometry) para no duplicar aquí el criterio de fabricación.

    Devuelve (cajas, omitidos). En `omitidos` van los elementos que NO se han
    podido dibujar por falta de datos: se informan, no se rellenan.
    """
    d = distribucion or {}
    paredes = d.get("paredes") or []
    elementos = d.get("elementos") or []
    alto_de = altura_modulo or (lambda _id: 80)
    fondo_de = fondo_modulo or (lambda _id: 58)

    cajas, omitidos = [], []
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

        (ox, oz), (dx, dz) = _origen_de_pared(pidx, d.get("tipo"), paredes)
        recorrido = avance.get(pidx, 0.0)
        avance[pidx] = recorrido + ancho

        eid = str(el.get("id") or "")
        alto = float(alto_de(eid))
        fondo = float(fondo_de(eid))
        # Los altos cuelgan; los bajos se apoyan en el zócalo.
        base = 145.0 if str(el.get("label", "")).upper().startswith("A") or eid.upper().startswith("A") else 10.0

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
