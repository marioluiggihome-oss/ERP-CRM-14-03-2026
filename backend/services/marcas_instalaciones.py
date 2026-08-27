# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""COLOCAR LAS TOMAS SOBRE EL RENDER: lo que la IA no puede garantizar.

El master, 14/08/2026: «coloca mucho mejor todas las tomas y enchufes». En su
captura salían siete marcas amontonadas en el lado izquierdo, dos de ellas
pisándose una encima de otra, todas con la misma cota de 110 cm, y media cocina
sin un solo punto.

POR QUÉ NO SE ARREGLA PIDIÉNDOSELO MEJOR AL MODELO
--------------------------------------------------
Al modelo de visión se le puede pedir DÓNDE está cada cosa, y eso lo hace
razonablemente. Lo que no se le puede pedir es que garantice que dos etiquetas
no se solapen: eso no es ver, es geometría, y la geometría se calcula.

Un modelo devolverá tarde o temprano dos puntos casi en el mismo píxel —porque
el horno y el microondas están uno encima del otro, o porque ha visto el mismo
enchufe dos veces—. Con las etiquetas encima, ese plano no se puede leer, y es
el papel que se lleva el electricista.

QUÉ SE HACE AQUÍ, Y EN ESTE ORDEN
---------------------------------
1. Se tiran los duplicados: dos puntos DEL MISMO TIPO muy juntos son el mismo
   punto visto dos veces.
2. Se separan los que siguen chocando, moviéndolos en horizontal —que es donde
   hay sitio en una cocina— y sin sacarlos de su banda de altura.
3. Se los aparta del borde, para que la etiqueta no se salga de la imagen.

Nada de esto inventa un punto ni lo cambia de sitio de forma apreciable: son
empujones de unos pocos por ciento del ancho. Un punto movido cinco centímetros
sigue siendo el mismo punto; dos etiquetas ilegibles no son ningún punto.
"""
from typing import Any, Dict, List, Optional

# Distancias en % de la imagen. La marca son 40 px de círculo más la etiqueta
# debajo; sobre un render de 1000 px de ancho, eso es un 4 % largo.
SEPARACION_MIN = 7.0        # entre dos marcas cualesquiera
DUPLICADO_MAX = 4.0         # mismo tipo y más cerca que esto = el mismo punto
MARGEN_BORDE = 3.0          # para que la etiqueta no se salga
PASOS_MAXIMOS = 60

# Altura por defecto de cada tipo (cm desde el suelo acabado), por si la IA no
# la dice. No son cifras inventadas: son las que usa el plan de instalaciones.
ALTURA_POR_TIPO = {
    "enchufe": 110, "agua": 50, "desague": 40, "gas": 50,
    "luz": 220, "datos": 40, "tv": 40, "lavadora": 80, "toallero": 120,
}


def _dist(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    dx = float(a.get("x", 0)) - float(b.get("x", 0))
    dy = float(a.get("y", 0)) - float(b.get("y", 0))
    return (dx * dx + dy * dy) ** 0.5


def quitar_duplicados(marcas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Dos marcas DEL MISMO TIPO casi en el mismo sitio son la misma."""
    limpias: List[Dict[str, Any]] = []
    for m in marcas:
        gemela = next((o for o in limpias
                       if o.get("type") == m.get("type") and _dist(o, m) < DUPLICADO_MAX), None)
        if gemela is None:
            limpias.append(dict(m))
    return limpias


def separar(marcas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aparta las marcas que se pisan, en horizontal, sin salirse de la imagen.

    Se mueven las dos del par, mitad y mitad, para no arrastrar siempre a la
    misma hacia un lado. Se hace en pasadas: mover una puede acercarla a otra.
    """
    ms = [dict(m) for m in marcas]
    for _ in range(PASOS_MAXIMOS):
        movido = False
        for i in range(len(ms)):
            for j in range(i + 1, len(ms)):
                a, b = ms[i], ms[j]
                d = _dist(a, b)
                if d >= SEPARACION_MIN:
                    continue
                falta = (SEPARACION_MIN - d) / 2 + 0.1
                # Si están exactamente encima, se decide por el orden para que el
                # resultado sea el mismo siempre (si no, dependería del azar).
                izq, der = (a, b) if float(a.get("x", 0)) <= float(b.get("x", 0)) else (b, a)
                izq["x"] = max(MARGEN_BORDE, float(izq.get("x", 0)) - falta)
                der["x"] = min(100 - MARGEN_BORDE, float(der.get("x", 0)) + falta)
                movido = True
        if not movido:
            break
    return ms


def _altura(m: Dict[str, Any]) -> Optional[int]:
    bruto = m.get("h", m.get("alto_cm"))
    try:
        v = int(round(float(bruto)))
    except (TypeError, ValueError):
        return ALTURA_POR_TIPO.get(m.get("type"))
    # Fuera de rango no es una variante, es un error: se usa la de la casa.
    if not (0 <= v <= 300):
        return ALTURA_POR_TIPO.get(m.get("type"))
    return v


def ordenar_marcas(marcas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Duplicados fuera, separadas, dentro de la imagen y con su altura.

    Es lo único que se llama desde fuera; el orden de los pasos importa (separar
    antes de quitar duplicados dejaría los duplicados separados, o sea dos
    marcas para el mismo punto).
    """
    limpias = quitar_duplicados([m for m in (marcas or []) if m.get("type")])
    for m in limpias:
        m["x"] = max(MARGEN_BORDE, min(100 - MARGEN_BORDE, float(m.get("x", 50))))
        m["y"] = max(MARGEN_BORDE, min(100 - MARGEN_BORDE, float(m.get("y", 50))))
        alt = _altura(m)
        if alt is not None:
            m["h"] = alt
    separadas = separar(limpias)
    for m in separadas:
        m["x"] = round(float(m["x"]), 2)
        m["y"] = round(float(m["y"]), 2)
    # De izquierda a derecha: es como se lee el plano y como se pica la pared.
    separadas.sort(key=lambda m: (float(m["x"]), float(m["y"])))
    return separadas
