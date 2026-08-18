# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Leer la cocina del dibujo COMO UNA LISTA DE MUEBLES, no como una redacción.

POR QUÉ ESTO
------------
El master ha dicho cuatro veces seguidas lo mismo sobre el mismo render: «no
se parecen», «falla», «sigue sin interpretarlo bien», «igual». Cada vez se
apretó el encargo con más reglas. Cada vez volvió a faltar lo mismo: los altos
partidos en dos filas hasta el techo y el nicho de la campana sobre la placa.

El fallo no está en las reglas. Está en el CAMINO:

    dibujo -> párrafo en prosa -> modelo de imagen

Un párrafo no se cuenta. «Una fila de altos con algunos altillos encima y un
hueco para la campana» es una frase perfectamente correcta con la que se puede
dibujar cualquier cocina. Lo que no sobrevive a la prosa son los NÚMEROS: seis
bajos, cinco altos, cinco altillos, un hueco de 90 después del tercero.

Así que el dibujo se lee a FICHA: una lista de muebles con su fila, su ancho y
sus frentes uno a uno. Y de esa ficha se escribe el encargo NOSOTROS, numerado
y contable. La cuenta deja de depender de que un párrafo la conserve.

Y de paso se puede ENSEÑAR: la misma ficha, en cristiano, debajo del render.
Hasta hoy, cuando salía mal, ni el master ni yo sabíamos si era que se había
leído mal el dibujo o que el render no había obedecido. Se adivinaba. Con la
ficha a la vista se ve de un golpe cuál de las dos cosas ha fallado.

MEDIDAS DE LA CASA
------------------
Las alturas normales están aquí para poder DECIDIR de qué fila es un mueble
cuando el dibujo no lo dice: un mueble de 35-45 cm colgado sobre otro es un
altillo, uno de 210-220 que toca el suelo es una columna. No se usan nunca
para inventar una medida que no está: una cota que no aparece se queda vacía.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Alturas y fondos habituales (cm). Sirven para CLASIFICAR, no para inventar.
ALTO_BAJO = (70, 80)          # bajo sin encimera; con encimera y zócalo, ~90
ALTO_ALTO = (70, 90)          # mueble alto de colgar
ALTO_ALTILLO = (20, 45)       # la segunda fila que remata contra el techo
ALTO_COLUMNA = (200, 240)     # del suelo al techo
FONDO_BAJO = (55, 62)
FONDO_ALTO = (30, 40)

FILAS = ("bajos", "altos", "altillos", "columnas")

# Nombres de fila tal y como se le piden al modelo y tal y como se pintan.
_ETIQUETA_FILA = {
    "bajos": "BASE UNITS",
    "altos": "WALL UNITS",
    "altillos": "SECOND ROW ON TOP (altillos)",
    "columnas": "FULL-HEIGHT TALL COLUMNS",
}
_ETIQUETA_ES = {
    "bajos": "Bajos",
    "altos": "Altos",
    "altillos": "Altillos (2ª fila)",
    "columnas": "Columnas",
}


PROMPT_LECTURA = """You are reading a technical drawing of ONE kitchen (elevation and/or plan).
It may be hand-drawn or a printed line drawing, and it may sit inside a page with a title, prices
and phone bars around it: ignore all of that and read ONLY the drawing.

Answer with a SINGLE JSON object and NOTHING ELSE. No prose, no markdown fences, no explanation.

Use exactly this shape:

{
  "forma": "lineal" | "L" | "U" | "peninsula" | "isla",
  "acabados": {"frentes": "", "encimera": ""},
  "filas": {
    "bajos":    [ {"orden":1, "ancho_cm":null, "contiene":"", "frentes":["puerta"]} ],
    "altos":    [ {"orden":1, "ancho_cm":null, "contiene":"", "frentes":["puerta"]} ],
    "altillos": [ {"orden":1, "ancho_cm":null, "contiene":"", "frentes":["puerta"]} ],
    "columnas": [ {"orden":1, "ancho_cm":null, "contiene":"", "frentes":["puerta","puerta"]} ]
  },
  "huecos_altos": [ {"despues_de":3, "ancho_cm":null, "motivo":"campana"} ],
  "altos_llegan_al_techo": true,
  "notas": ""
}

RULES — read them all before answering:

· "frentes" is the list of the separate fronts of that module, TOP TO BOTTOM as drawn. Count the
  horizontal and vertical dividing lines on its face. Allowed values: "puerta", "cajon", "horno",
  "microondas", "lavavajillas", "lavadora", "frigorifico", "placa", "fregadero", "hueco".
  A module drawn with three stacked fronts is ["cajon","cajon","cajon"], NOT ["puerta"].
  A tall column split by a horizontal line is ["puerta","puerta"].
· "altillos" is the SECOND ROW of shorter units sitting ON TOP of the wall units, the one that
  closes against the ceiling. If the upper band of the drawing is divided by a horizontal line
  into two rows of boxes, that lower row is "altos" and the upper row is "altillos". If there is
  only one row, leave "altillos" as [].
· "columnas" are the full-height units that start at the floor and rise above the wall units.
  A column is ONE module: never split it into a base unit plus a wall unit.
· "huecos_altos" is where the row of wall units is INTERRUPTED — typically over the hob, where
  only the extractor hood goes. "despues_de" is the order number of the wall unit it comes after.
  If the row is continuous, use [].
· Left to right, always, and "orden" starts at 1 in every list.
· NEVER INVENT A MEASUREMENT. If a width is not written on the drawing, put null. Do not estimate.
· Report what is DRAWN, not what a kitchen usually has.
"""


def _numero(valor: Any) -> Optional[float]:
    """Un número o nada. Un «60 cm» escrito a mano llega de mil maneras."""
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        return float(valor) if valor > 0 else None
    m = re.search(r"\d+(?:[.,]\d+)?", str(valor))
    if not m:
        return None
    try:
        n = float(m.group(0).replace(",", "."))
    except ValueError:
        return None
    return n if n > 0 else None


def parsear_lectura(texto: str) -> Optional[Dict[str, Any]]:
    """Saca el JSON de lo que devuelva el modelo, o None.

    Se pide «solo JSON» pero los modelos envuelven en ```json, se disculpan
    antes o añaden una coletilla detrás. Si esto devuelve None no pasa nada
    grave: quien llama se queda con la lectura en prosa de siempre.
    """
    if not texto or not str(texto).strip():
        return None
    t = str(texto).strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t).strip()
    datos = None
    try:
        datos = json.loads(t)
    except Exception:
        i, j = t.find("{"), t.rfind("}")
        if i >= 0 and j > i:
            try:
                datos = json.loads(t[i:j + 1])
            except Exception:
                datos = None
    if not isinstance(datos, dict):
        return None

    filas_in = datos.get("filas") if isinstance(datos.get("filas"), dict) else {}
    filas: Dict[str, List[Dict[str, Any]]] = {}
    for fila in FILAS:
        limpia: List[Dict[str, Any]] = []
        for i, m in enumerate(filas_in.get(fila) or []):
            if not isinstance(m, dict):
                continue
            frentes = [str(f).strip().lower() for f in (m.get("frentes") or []) if str(f).strip()]
            limpia.append({
                "orden": int(_numero(m.get("orden")) or (i + 1)),
                "ancho_cm": _numero(m.get("ancho_cm")),
                "contiene": str(m.get("contiene") or "").strip(),
                "frentes": frentes,
            })
        filas[fila] = limpia

    huecos = []
    for h in (datos.get("huecos_altos") or []):
        if isinstance(h, dict):
            huecos.append({
                "despues_de": _numero(h.get("despues_de")),
                "ancho_cm": _numero(h.get("ancho_cm")),
                "motivo": str(h.get("motivo") or "").strip(),
            })

    if not any(filas[f] for f in FILAS):
        # Ni un solo mueble: esto no es una lectura, es ruido.
        return None

    acabados = datos.get("acabados") if isinstance(datos.get("acabados"), dict) else {}
    return {
        "forma": str(datos.get("forma") or "").strip().lower(),
        "acabados": {
            "frentes": str(acabados.get("frentes") or "").strip(),
            "encimera": str(acabados.get("encimera") or "").strip(),
        },
        "filas": filas,
        "huecos_altos": huecos,
        "altos_llegan_al_techo": bool(datos.get("altos_llegan_al_techo")),
        "notas": str(datos.get("notas") or "").strip(),
    }


# El encargo al modelo de imagen va en inglés entero. Si se cuela «fregadero»
# suelto en medio de una frase inglesa, el modelo lo puede leer como una marca,
# como un color o como nada.
_EN = {
    "puerta": "door", "cajon": "drawer", "hueco": "open gap",
    "horno": "built-in oven", "microondas": "built-in microwave",
    "lavavajillas": "integrated dishwasher", "lavadora": "washing machine",
    "frigorifico": "fridge", "frigorífico": "fridge",
    "placa": "hob on the countertop above", "fregadero": "sink on the countertop above",
    "campana": "extractor hood", "extraible": "pull-out unit", "extraíble": "pull-out unit",
}


def _contiene_en_texto(contiene: str) -> str:
    """Lo que lleva el mueble, en inglés si es vocabulario conocido.

    Si NO lo es, se pasa tal cual pero DICIENDO que es una etiqueta leída del
    dibujo. Un rótulo manuscrito es un dato —«escobero», «7B2P800»— y borrarlo
    por no saber traducirlo sería tirar información del cliente; pero soltarlo
    en medio de una frase inglesa sin avisar hace que el modelo lo lea como una
    marca o como un color.
    """
    t = (contiene or "").strip()
    if not t:
        return ""
    clave = t.lower().translate(str.maketrans("áéíóúü", "aeiouu"))
    if clave in _EN:
        return _EN[clave]
    return f'label written on the drawing: "{t}"'


def _frentes_en_texto(frentes: List[str]) -> str:
    """«3 drawers», «1 door», «built-in oven + drawer»… contando de verdad."""
    if not frentes:
        return "fronts not read from the drawing"
    trozos, actual, veces = [], None, 0
    for f in frentes + [None]:
        if f == actual:
            veces += 1
            continue
        if actual is not None:
            nombre = _EN.get(actual, actual)
            trozos.append(f"{veces} {nombre}" + ("s" if veces > 1 and not nombre.endswith("s") else ""))
        actual, veces = f, 1
    return " + ".join(trozos)


def especificacion_en_texto(datos: Dict[str, Any]) -> str:
    """La ficha convertida en encargo NUMERADO para el modelo de imagen.

    Aquí está el porqué de todo el módulo: la cuenta la escribimos nosotros.
    Si el dibujo tiene cinco altos y cinco altillos, el encargo dice CINCO y
    CINCO, y al final vuelve a decir cuántos hay que poder contar en la foto.
    """
    if not datos:
        return ""
    lineas: List[str] = ["EXACT MODULE LIST READ FROM THE DRAWING — BUILD THIS AND NOTHING ELSE:"]
    forma = datos.get("forma") or ""
    if forma:
        lineas.append(f"· LAYOUT: {forma}.")

    filas = datos.get("filas") or {}
    for fila in FILAS:
        modulos = filas.get(fila) or []
        if not modulos:
            if fila == "altillos":
                lineas.append("· SECOND ROW ON TOP (altillos): NONE. The wall units are a single row.")
            continue
        lineas.append(f"· {_ETIQUETA_FILA[fila]} — {len(modulos)} module(s), left to right:")
        for m in modulos:
            ancho = f"{int(m['ancho_cm'])} cm" if m.get("ancho_cm") else "width not written"
            _que = _contiene_en_texto(m.get("contiene") or "")
            que = f" — {_que}" if _que else ""
            lineas.append(f"    {m['orden']}. {ancho}{que} — {_frentes_en_texto(m.get('frentes') or [])}")

    for h in (datos.get("huecos_altos") or []):
        tras = int(h["despues_de"]) if h.get("despues_de") else None
        ancho = f"{int(h['ancho_cm'])} cm wide" if h.get("ancho_cm") else "as drawn"
        motivo = _contiene_en_texto(h.get("motivo") or "") or "extractor hood"
        donde = f"after wall unit {tras}" if tras else "in the wall run"
        lineas.append(
            f"· OPEN GAP IN THE WALL RUN {donde}, {ancho}, for the {motivo}. "
            "LEAVE IT OPEN: no cabinet there, and do not widen its neighbours to close it.")

    if datos.get("altillos_o_techo_avisado") or datos.get("altos_llegan_al_techo"):
        lineas.append("· The wall cabinets run UP TO THE CEILING. No bare wall strip above them.")

    ac = datos.get("acabados") or {}
    if ac.get("frentes"):
        lineas.append(f"· Fronts finish: {ac['frentes']}.")
    if ac.get("encimera"):
        lineas.append(f"· Countertop: {ac['encimera']}.")
    if datos.get("notas"):
        lineas.append(f"· Notes from the drawing: {datos['notas']}")

    # LA CUENTA, OTRA VEZ Y AL FINAL. Es justo lo que se pierde en la prosa, y
    # por eso se repite en una sola línea corta que se pueda comprobar mirando
    # la foto sin volver a leer nada.
    _CUENTA = {
        "bajos": "base units", "altos": "wall units",
        "altillos": "units in the second row on top", "columnas": "full-height tall columns",
    }
    cuenta = [f"{len(filas.get(f) or [])} {_CUENTA[f]}" for f in FILAS if filas.get(f)]
    huecos = len(datos.get("huecos_altos") or [])
    if huecos:
        cuenta.append(f"{huecos} open gap{'s' if huecos > 1 else ''} in the wall run")
    lineas.append(
        "· COUNT BEFORE YOU FINISH: the photograph must show exactly "
        + ", ".join(cuenta) + ". Not one more, not one less.")
    return "\n".join(lineas)


def resumen_para_pantalla(datos: Dict[str, Any]) -> str:
    """Lo mismo, en cristiano y corto, para enseñárselo al master.

    Sin esto, cuando el render sale mal nadie sabe si se leyó mal el dibujo o
    si el render no obedeció. Con esto se ve de un vistazo.
    """
    if not datos:
        return ""
    partes: List[str] = []
    forma = datos.get("forma")
    if forma:
        partes.append(f"Forma: {forma}")
    filas = datos.get("filas") or {}
    for fila in FILAS:
        modulos = filas.get(fila) or []
        if not modulos:
            continue
        detalle = []
        for m in modulos:
            ancho = f"{int(m['ancho_cm'])}" if m.get("ancho_cm") else "?"
            frentes = m.get("frentes") or []
            cajones = sum(1 for f in frentes if f == "cajon")
            puertas = sum(1 for f in frentes if f == "puerta")
            trozos = []
            if puertas:
                trozos.append(f"{puertas}p")
            if cajones:
                trozos.append(f"{cajones}c")
            otros = [f for f in frentes if f not in ("puerta", "cajon")]
            trozos += otros
            detalle.append(f"{ancho}({'+'.join(trozos) or '?'})")
        partes.append(f"{_ETIQUETA_ES[fila]}: {len(modulos)} → " + ", ".join(detalle))
    for h in (datos.get("huecos_altos") or []):
        ancho = f"{int(h['ancho_cm'])} cm" if h.get("ancho_cm") else "sin cota"
        tras = f" tras el alto {int(h['despues_de'])}" if h.get("despues_de") else ""
        partes.append(f"Hueco en los altos{tras}: {ancho} ({h.get('motivo') or 'campana'})")
    ac = datos.get("acabados") or {}
    if ac.get("frentes"):
        partes.append(f"Frentes: {ac['frentes']}")
    if ac.get("encimera"):
        partes.append(f"Encimera: {ac['encimera']}")
    return " · ".join(partes)
