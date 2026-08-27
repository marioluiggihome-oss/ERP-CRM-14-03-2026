# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
planta_cocina.py — LA PLANTA DE VERDAD: la cocina vista DESDE ARRIBA.

El master lo dijo con estas palabras: «donde pone planta, no está bien, lo que
dibuja es un alzado; el alzado es visto de frente y la planta vista desde
arriba, con cotas y medidas». Tenía razón, y por dos motivos distintos.

QUÉ ESTABA MAL
--------------
1. La planta vectorial **no usaba los anchos reales**. Pintaba módulos
   genéricos de 55 cm en un bucle (`while x + mod_w <= …`) y DESPUÉS colocaba
   los elementos aparte, con un espaciado propio (`elem_x += ew + 10`) que no
   tenía nada que ver con dónde están de verdad. Los rectángulos eran
   decoración y las etiquetas se amontonaban unas encima de otras.

2. **Se inventaba el fondo de la estancia.** En lineal salía
   `max(250, ancho*0.6)`; en L, un suelo de 250 que pisaba el ancho real de la
   segunda pared. Un número inventado, en un plano rotulado «ESCALA 1:20».

QUÉ HACE ESTO
-------------
Coloca cada módulo en su sitio, con SU ancho y SU fondo, corridos a lo largo
de la pared, y devuelve las cotas. Cálculo puro, sin matplotlib, para poder
probarlo.

DE DÓNDE SALE LA GEOMETRÍA
--------------------------
De `perspectiva.origen_de_pared`, que ya sabía dónde empieza cada pared y hacia
dónde corre. Es la MISMA función, a propósito: si la planta y el boceto en
perspectiva colocaran las paredes cada uno a su manera, enseñarían dos cocinas
distintas del mismo proyecto y nadie sabría cuál mirar.

LO QUE NO SE INVENTA
--------------------
El fondo de la estancia. De una cocina lineal solo se conoce el ancho de SU
pared; lo que hay enfrente no lo ha medido nadie. Así que la planta se dibuja
alrededor de los muebles y no se cierra una habitación imaginaria. En una L o
una U sí se conocen los dos lados, y entonces sí se acota el rincón.
"""
from services.perspectiva import origen_de_pared

# Fondos por defecto SOLO como respaldo si no se inyecta el criterio de
# fábrica. El bueno viene de kitchen_geometry, igual que en el alzado.
FONDO_BAJO = 58.0
FONDO_ALTO = 33.0


def _num(v):
    if v in (None, ""):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def montar(distribucion, fondo_modulo=None, es_alto=None):
    """Coloca los módulos en planta, cada uno con su ancho REAL.

    Devuelve:
      modulos  — cada uno con su rectángulo en cm: (x, y) de la esquina, `largo`
                 a lo ancho de la pared, `fondo` hacia el interior, y el vector
                 de la pared para poder rotularlo en su dirección.
      cotas    — las cadenas de cota por pared, en el orden en que van dibujadas.
      muros    — el segmento de cada pared, con su longitud real.
      omitidos — lo que NO se ha podido dibujar, con el motivo. Se informa; no
                 se rellena con un ancho «razonable».
      rincon   — {ancho, fondo} solo cuando los DOS lados son datos reales.
    """
    d = distribucion or {}
    paredes = d.get("paredes") or []
    elementos = d.get("elementos") or []
    tipo = str(d.get("tipo") or "lineal").lower()

    fondo_de = fondo_modulo or (lambda _id: FONDO_BAJO)
    cuelga = es_alto or (lambda eid, label="": False)

    modulos, omitidos = [], []
    # Dos filas por pared, como en el alzado y en la perspectiva: los altos
    # corren por su cuenta. En planta el alto se dibuja a trazos POR ENCIMA del
    # bajo, que es como se representa en un plano de cocina.
    avance = {}

    for el in elementos:
        ancho = _num(el.get("ancho"))
        if ancho is None or ancho <= 0:
            omitidos.append({"id": el.get("id"), "label": el.get("label"),
                             "motivo": "sin ancho"})
            continue

        pidx = int(el.get("pared_idx") or 0)
        if pidx >= len(paredes):
            omitidos.append({"id": el.get("id"), "label": el.get("label"),
                             "motivo": f"pared {pidx} inexistente"})
            continue

        eid = str(el.get("id") or "")
        label = el.get("label") or eid
        alto = bool(cuelga(eid, label))
        fondo = float(fondo_de(eid))

        fila = (pidx, alto)
        recorrido = avance.get(fila, 0.0)
        avance[fila] = recorrido + ancho

        (ox, oy), (dx, dy) = origen_de_pared(pidx, tipo, paredes)
        # El fondo sale perpendicular a la pared, hacia el interior.
        nx, ny = -dy, dx

        modulos.append({
            "id": eid, "label": label, "pared": pidx, "alto": alto,
            "desde": recorrido, "hasta": recorrido + ancho,
            "ancho": ancho, "fondo": fondo,
            # Las cuatro esquinas del rectángulo en planta, en cm.
            "esquinas": [
                (ox + dx * recorrido, oy + dy * recorrido),
                (ox + dx * (recorrido + ancho), oy + dy * (recorrido + ancho)),
                (ox + dx * (recorrido + ancho) + nx * fondo,
                 oy + dy * (recorrido + ancho) + ny * fondo),
                (ox + dx * recorrido + nx * fondo, oy + dy * recorrido + ny * fondo),
            ],
            "direccion": (dx, dy),
            "normal": (nx, ny),
        })

    muros = []
    for i, p in enumerate(paredes):
        largo = _num(p.get("ancho"))
        if largo is None or largo <= 0:
            continue
        (ox, oy), (dx, dy) = origen_de_pared(i, tipo, paredes)
        muros.append({
            "indice": i,
            "nombre": p.get("nombre") or f"Pared {i + 1}",
            "largo": largo,
            "desde": (ox, oy),
            "hasta": (ox + dx * largo, oy + dy * largo),
            "direccion": (dx, dy),
            "normal": (-dy, dx),
        })

    return {
        "modulos": modulos,
        "muros": muros,
        "cotas": cadenas_de_cota(modulos, muros),
        "omitidos": omitidos,
        "rincon": rincon_real(paredes, tipo),
    }


def cadenas_de_cota(modulos, muros):
    """La cadena de cotas de cada pared: módulo a módulo, y el total.

    Solo de la fila de BAJOS. La de altos va aparte en el alzado; encadenar las
    dos en la misma línea daría una cadena que no suma el largo de la pared y
    quien la lea pensará que falta un mueble.
    """
    cadenas = []
    for muro in muros:
        de_esta = sorted([m for m in modulos
                          if m["pared"] == muro["indice"] and not m["alto"]],
                         key=lambda m: m["desde"])
        if not de_esta:
            continue
        cadenas.append({
            "pared": muro["indice"],
            "nombre": muro["nombre"],
            "tramos": [{"desde": m["desde"], "hasta": m["hasta"],
                        "medida": m["ancho"], "label": m["label"]}
                       for m in de_esta],
            "total": muro["largo"],
            # Lo que ocupan los muebles frente a lo que mide la pared. Si no
            # cuadra, se dice: es la comprobación de la regla de oro («la suma
            # de anchos de una pared coincide con el ancho real de esa pared»).
            "ocupado": sum(m["ancho"] for m in de_esta),
        })
    return cadenas


def rincon_real(paredes, tipo):
    """Las dos medidas del rincón, SOLO si las dos son datos reales.

    En una L o una U se conocen los dos lados y el rincón se puede acotar. En
    una cocina lineal solo se conoce el ancho de su pared: lo que hay enfrente
    no lo ha medido nadie, así que aquí se devuelve None y el dibujo no cierra
    una habitación imaginaria. Antes se rellenaba con `max(250, ancho*0,6)`.
    """
    t = (tipo or "lineal").lower()
    anchos = [(_num(p.get("ancho")) or 0.0) for p in (paredes or [])]
    if t not in ("l", "u", "g") or len(anchos) < 2:
        return None
    if anchos[0] <= 0 or anchos[1] <= 0:
        return None
    return {"ancho": anchos[0], "fondo": anchos[1]}


def descuadres(cotas, tolerancia=1.0):
    """Paredes donde la suma de los muebles no da el largo de la pared.

    No se corrige nada aquí: se DICE. Cuadrarlo por nuestra cuenta —estirando
    un módulo o metiendo un relleno que nadie ha pedido— es exactamente cómo se
    cuela una medida inventada en un plano que parece bueno.
    """
    fuera = []
    for c in cotas:
        dif = c["ocupado"] - c["total"]
        if abs(dif) > tolerancia:
            fuera.append({
                "pared": c["pared"], "nombre": c["nombre"],
                "diferencia": dif,
                "motivo": (f"Los muebles suman {c['ocupado']:.0f} cm y la pared "
                           f"mide {c['total']:.0f} cm: "
                           f"{'sobran' if dif > 0 else 'faltan'} "
                           f"{abs(dif):.0f} cm."),
            })
    return fuera
