# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
lectura_armario.py — LEER EL CROQUIS DE UN ARMARIO A FICHA.

POR QUÉ HACÍA FALTA
-------------------
El Estudio 3D tenía UN solo camino para los croquis y era el de cocina, de
punta a punta: la lectura preguntaba por bajos, altos, altillos y columnas; la
transcripción empezaba por «technical KITCHEN blueprint»; y el encargo del
render llevaba mil palabras de cocina —el hueco de la campana sobre la placa,
la encimera que muere contra la columna, el diccionario de Frigo / Combi /
Lavavajillas / Bajo Fregadero—.

Con el croquis de un ARMARIO delante, todo eso seguía puesto. Al modelo se le
daba la ficha de una cocina y una línea suelta diciendo «esto es un armario».
El master mandó un armario de DOS cuerpos con un altillo corrido encima y una
cajonera abajo a la izquierda; volvió un armario de seis módulos, con los
cajones en el centro y una columna de seis baldas que no estaba dibujada. No
era el modelo inventando: era que se le había pedido una cocina.

QUÉ SE LEE DE UN ARMARIO
------------------------
Otras cosas que de una cocina. En un armario no hay filas: hay CUERPOS, uno al
lado de otro, y dentro de cada cuerpo un orden de arriba abajo —barra, baldas,
cajonera, zapatero—. Y hay una pieza que no existe en cocina y que aquí sale
casi siempre: el ALTILLO (maletero) corrido por encima de todo.

LO QUE NO SE HACE
-----------------
No se inventa ni una medida. Si el ancho no está escrito, va null: un armario
sin cotas se puede dibujar en proporciones, pero no se puede presupuestar, y
mezclar las dos cosas es como acaba viajando dinero sobre una medida inventada.
Y no se rellena lo que el dibujo no dice: si un cuerpo está vacío, está vacío.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

# Nombres en castellano de lo que puede haber dentro de un cuerpo. La clave es
# lo que devuelve el modelo; el valor, cómo se le enseña al master.
_INTERIOR_ES = {
    "barra": "barra de colgar",
    "baldas": "baldas",
    "cajones": "cajonera",
    "zapatero": "zapatero",
    "pantalonero": "pantalonero",
    "maletero": "maletero",
    "hueco": "hueco libre",
}
# Y en inglés, que es la lengua del encargo del render.
_INTERIOR_EN = {
    "barra": "hanging rail",
    "baldas": "shelves",
    "cajones": "bank of drawers",
    "zapatero": "shoe rack",
    "pantalonero": "trouser rack",
    "maletero": "top box / suitcase compartment",
    "hueco": "empty open space",
}

PROMPT_LECTURA = """You are reading a technical drawing of ONE fitted wardrobe / closet (front elevation).
It may be hand-drawn on a phone, or a printed line drawing, and it may sit inside a page with a
title, prices or phone bars around it: ignore all of that and read ONLY the drawing.

Answer with a SINGLE JSON object and NOTHING ELSE. No prose, no markdown fences, no explanation.

Use exactly this shape:

{
  "ancho_total_cm": null,
  "alto_total_cm": null,
  "fondo_cm": null,
  "acabados": {"frentes": "", "interior": ""},
  "altillo": {"hay": false, "alto_cm": null, "divisiones": null},
  "puertas": {"hay": false, "tipo": "", "n": null},
  "cuerpos": [
    {"orden": 1, "ancho_cm": null, "ancho_relativo": null,
     "interior": [ {"tipo": "barra", "n": 1} ]}
  ],
  "notas": ""
}

RULES — read them all before answering:

· A WARDROBE IS A ROW OF CUERPOS (bays). Every VERTICAL line that runs from top to bottom of the
  drawing separates one cuerpo from the next. COUNT THOSE LINES: two vertical divisions inside the
  outline means THREE cuerpos, one vertical division means TWO cuerpos, none means ONE. Report
  exactly that many entries in "cuerpos", left to right, "orden" starting at 1.
· "ancho_relativo" is the share of the total width that cuerpo takes, 0-100, measured on the
  drawing. Fill it ALWAYS, even when no dimension is written: it is what keeps a narrow bay narrow.
· THE ALTILLO IS THE BAND ON TOP. A horizontal line that crosses the WHOLE width near the top,
  above the vertical divisions, is the altillo (maletero) running over everything. Set
  "altillo.hay" to true and put in "divisiones" how many doors/sections that band is divided into.
  A horizontal line that only crosses ONE cuerpo is NOT an altillo — it is a shelf of that cuerpo.
· "interior" is what is drawn INSIDE that cuerpo, TOP TO BOTTOM, in that order. Allowed "tipo":
  "barra", "baldas", "cajones", "zapatero", "pantalonero", "maletero", "hueco". "n" is how many
  (3 shelves -> {"tipo":"baldas","n":3}; a stack of 4 drawers -> {"tipo":"cajones","n":4}).
· HOW THE INTERIOR IS DRAWN:
  · A group of several close, parallel horizontal lines, usually low in the cuerpo, is a BANK OF
    DRAWERS ("cajones"), one drawer per gap.
  · Horizontal lines spaced well apart are SHELVES ("baldas").
  · A single line high up with a tall empty space under it is a shelf with a HANGING RAIL below:
    report ["baldas" n=1, "barra"]. A long empty bay with nothing drawn in it is hanging space too.
  · Short diagonal or slanted lines low down are a SHOE RACK ("zapatero").
· LINES DO NOT CROSS CUERPOS. A horizontal line that stops at a vertical division belongs ONLY to
  the cuerpo it is drawn in. Never copy the contents of one cuerpo into its neighbour.
· DOORS. If the drawing shows the INTERIOR (shelves, rails, drawers visible), it is an OPEN
  elevation: "puertas.hay" is false, whatever a wardrobe "usually" has. Only set it to true when
  door leaves are actually drawn as blank panels with their own division lines or handles.
· NEVER INVENT A MEASUREMENT. If a width, height or depth is not written on the drawing, put null.
  Do not estimate it from the paper.
· UNITS: report EVERYTHING in centimetres. These drawings are usually dimensioned in millimetres —
  2400 mm is 240 cm, 600 mm is 60 cm. A wardrobe is 100-600 cm wide, 200-280 cm high and 55-70 cm
  deep; if your numbers come out ten times bigger, they were millimetres.
· A dimension line running HORIZONTALLY along the top or bottom is a WIDTH. One running VERTICALLY
  at the side is a HEIGHT, and one on a plan view is the DEPTH. A height is never a width.
· A WRITTEN SCHEDULE BEATS MEASURING THE DRAWING. If the sheet spells the sizes out in text
  ("ANCHO 2400", "3 cuerpos de 80"), use those numbers instead of measuring.
· Report what is DRAWN, not what a wardrobe usually has. If a cuerpo is empty, it is empty.
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


def _entero(valor: Any) -> Optional[int]:
    n = _numero(valor)
    return int(round(n)) if n is not None else None


def _en_centimetros(valor: Optional[float], que: str) -> Optional[float]:
    """Pasa a cm SOLO cuando no hay duda de que venían milímetros.

    Un armario mide 100-600 cm de ancho y 200-280 de alto. Si llega un 2400 de
    alto, eran milímetros. Si llega un 240, ya eran centímetros. En la zona
    donde las dos lecturas son posibles NO se toca nada: convertir por si acaso
    es exactamente cómo se cuela un armario diez veces mayor sin que falle nada.
    """
    if valor is None:
        return None
    topes = {"ancho": 700.0, "alto": 320.0, "fondo": 120.0}
    if valor > topes.get(que, 700.0):
        return round(valor / 10.0, 1)
    return valor


def parsear_lectura(texto: str) -> Optional[Dict[str, Any]]:
    """Saca el JSON de lo que devuelva el modelo, o None.

    Se pide «solo JSON» pero los modelos envuelven en ```json, se disculpan
    antes o añaden una coletilla detrás. Si esto devuelve None no pasa nada
    grave: quien llama se queda con la lectura en prosa de siempre.
    """
    if not texto or not str(texto).strip():
        return None
    crudo = str(texto).strip()
    crudo = re.sub(r"^```(?:json)?\s*", "", crudo)
    crudo = re.sub(r"\s*```$", "", crudo)
    i, j = crudo.find("{"), crudo.rfind("}")
    if i == -1 or j == -1 or j <= i:
        return None
    try:
        datos = json.loads(crudo[i:j + 1])
    except (ValueError, TypeError):
        return None
    if not isinstance(datos, dict):
        return None

    cuerpos_crudos = datos.get("cuerpos")
    if not isinstance(cuerpos_crudos, list) or not cuerpos_crudos:
        # Sin cuerpos no hay armario que valga: mejor la lectura de siempre.
        return None

    limpio: Dict[str, Any] = {
        "ancho_total_cm": _en_centimetros(_numero(datos.get("ancho_total_cm")), "ancho"),
        "alto_total_cm": _en_centimetros(_numero(datos.get("alto_total_cm")), "alto"),
        "fondo_cm": _en_centimetros(_numero(datos.get("fondo_cm")), "fondo"),
        "acabados": {},
        "notas": str(datos.get("notas") or "").strip(),
        "avisos": [],
    }
    ac = datos.get("acabados")
    if isinstance(ac, dict):
        limpio["acabados"] = {
            "frentes": str(ac.get("frentes") or "").strip(),
            "interior": str(ac.get("interior") or "").strip(),
        }

    alt = datos.get("altillo")
    if isinstance(alt, dict) and alt.get("hay"):
        limpio["altillo"] = {
            "hay": True,
            "alto_cm": _en_centimetros(_numero(alt.get("alto_cm")), "alto"),
            "divisiones": _entero(alt.get("divisiones")),
        }
    else:
        limpio["altillo"] = {"hay": False, "alto_cm": None, "divisiones": None}

    pu = datos.get("puertas")
    if isinstance(pu, dict) and pu.get("hay"):
        limpio["puertas"] = {"hay": True,
                             "tipo": str(pu.get("tipo") or "").strip(),
                             "n": _entero(pu.get("n"))}
    else:
        limpio["puertas"] = {"hay": False, "tipo": "", "n": None}

    cuerpos: List[Dict[str, Any]] = []
    for n, c in enumerate(cuerpos_crudos, start=1):
        if not isinstance(c, dict):
            continue
        interior = []
        for it in (c.get("interior") or []):
            if not isinstance(it, dict):
                continue
            tipo = str(it.get("tipo") or "").strip().lower()
            if tipo not in _INTERIOR_ES:
                continue
            cuantos = _entero(it.get("n")) or 1
            interior.append({"tipo": tipo, "n": max(1, cuantos)})
        cuerpos.append({
            "orden": _entero(c.get("orden")) or n,
            "ancho_cm": _en_centimetros(_numero(c.get("ancho_cm")), "ancho"),
            "ancho_relativo": _numero(c.get("ancho_relativo")),
            "interior": interior,
        })
    if not cuerpos:
        return None
    cuerpos.sort(key=lambda c: c["orden"])
    for n, c in enumerate(cuerpos, start=1):
        c["orden"] = n
    limpio["cuerpos"] = cuerpos

    _deducir_el_ancho_que_falta(limpio)
    return limpio


def _deducir_el_ancho_que_falta(datos: Dict[str, Any]) -> None:
    """Si falta UN solo ancho y está el total, ese se puede deducir.

    Solo uno. Con dos incógnitas y una ecuación no se deduce nada, y repartir
    «a partes iguales» sería inventar. Lo deducido se marca, para que quien lo
    lea sepa que ese número no estaba escrito en el papel.
    """
    total = datos.get("ancho_total_cm")
    cuerpos = datos.get("cuerpos") or []
    if not total or not cuerpos:
        return
    sin_ancho = [c for c in cuerpos if not c.get("ancho_cm")]
    con_ancho = [c for c in cuerpos if c.get("ancho_cm")]
    if len(sin_ancho) == 1 and con_ancho:
        resto = total - sum(c["ancho_cm"] for c in con_ancho)
        if resto > 0:
            sin_ancho[0]["ancho_cm"] = round(resto, 1)
            sin_ancho[0]["ancho_deducido"] = True
        else:
            datos["avisos"].append(
                f"Los anchos escritos ya suman {sum(c['ancho_cm'] for c in con_ancho):.0f} cm "
                f"y el total dice {total:.0f} cm: no cuadran.")
    elif not sin_ancho:
        suma = sum(c["ancho_cm"] for c in con_ancho)
        if abs(suma - total) > max(5.0, total * 0.05):
            datos["avisos"].append(
                f"Los cuerpos suman {suma:.0f} cm y el ancho total dice {total:.0f} cm.")


def sin_cotas(datos: Dict[str, Any]) -> bool:
    """¿Este dibujo viene sin una sola medida?"""
    if datos.get("ancho_total_cm") or datos.get("alto_total_cm"):
        return False
    return not any(c.get("ancho_cm") for c in (datos.get("cuerpos") or []))


def _una_pieza(tipo: str, n: int, idioma: str) -> str:
    """«3 cajones», no «3 cajonera».

    Parece cosmética y no lo es: este texto es el encargo que lee el modelo de
    imagen. «3 bank of drawers» se puede entender como tres cajoneras, y
    entonces dibuja tres. El número tiene que ir pegado a la pieza que se
    cuenta.
    """
    if idioma == "en":
        if tipo == "baldas":
            return "1 shelf" if n == 1 else f"{n} shelves"
        if tipo == "cajones":
            return "1 drawer" if n == 1 else f"a bank of {n} drawers"
        if tipo == "barra":
            return "a hanging rail" if n == 1 else f"{n} hanging rails"
        return _INTERIOR_EN.get(tipo, tipo)
    if tipo == "baldas":
        return "1 balda" if n == 1 else f"{n} baldas"
    if tipo == "cajones":
        return "1 cajón" if n == 1 else f"cajonera de {n} cajones"
    if tipo == "barra":
        return "barra de colgar" if n == 1 else f"{n} barras de colgar"
    return _INTERIOR_ES.get(tipo, tipo)


def _interior_en_texto(interior: List[Dict[str, Any]], idioma: str = "en") -> str:
    if not interior:
        return "empty (nothing drawn inside)" if idioma == "en" else "vacío"
    trozos = [_una_pieza(it["tipo"], it["n"], idioma) for it in interior]
    return ", then ".join(trozos) if idioma == "en" else ", luego ".join(trozos)


def especificacion_en_texto(datos: Dict[str, Any]) -> str:
    """El encargo, numerado y contable, que se le antepone al render.

    En prosa no sobreviven los números: «un armario con cuerpos y un altillo»
    describe igual de bien dos cuerpos que seis. Por eso va numerado y termina
    con un recuento, que es lo que el modelo puede comprobar antes de dibujar.
    """
    if not datos:
        return ""
    L: List[str] = []
    cuerpos = datos.get("cuerpos") or []
    L.append(f"WARDROBE READ FROM THE DRAWING — it has EXACTLY {len(cuerpos)} "
             f"cuerpo(s) (vertical bays) side by side, left to right.")

    med = []
    if datos.get("ancho_total_cm"):
        med.append(f"total width {datos['ancho_total_cm']:.0f} cm")
    if datos.get("alto_total_cm"):
        med.append(f"total height {datos['alto_total_cm']:.0f} cm")
    if datos.get("fondo_cm"):
        med.append(f"depth {datos['fondo_cm']:.0f} cm")
    if med:
        L.append("Overall: " + ", ".join(med) + ".")
    else:
        L.append("No dimensions are written on the drawing: keep the PROPORTIONS "
                 "exactly as drawn and do not invent numbers.")

    alt = datos.get("altillo") or {}
    if alt.get("hay"):
        div = alt.get("divisiones")
        L.append(f"ON TOP, running across the FULL width above every cuerpo, there is a "
                 f"separate ALTILLO band (top boxes / maletero)"
                 + (f", divided into {div} sections" if div else "")
                 + (f", {alt['alto_cm']:.0f} cm high" if alt.get("alto_cm") else "")
                 + ". This band is horizontal and continuous — it is NOT one of the cuerpos.")
    else:
        L.append("There is NO altillo band on top: the cuerpos run to the full height as drawn.")

    L.append("The cuerpos, left to right:")
    for c in cuerpos:
        ancho = ""
        if c.get("ancho_cm"):
            ancho = f", {c['ancho_cm']:.0f} cm wide"
            if c.get("ancho_deducido"):
                ancho += " (deduced from the total, not written)"
        elif c.get("ancho_relativo"):
            ancho = f", about {c['ancho_relativo']:.0f}% of the total width"
        L.append(f"  {c['orden']}. Cuerpo {c['orden']}{ancho}: "
                 f"{_interior_en_texto(c.get('interior') or [], 'en')} — top to bottom, "
                 "and this content belongs to THIS bay only.")

    pu = datos.get("puertas") or {}
    if pu.get("hay"):
        L.append("The drawing shows DOORS: render the wardrobe closed, with "
                 + (f"{pu['n']} " if pu.get("n") else "")
                 + (f"{pu['tipo']} " if pu.get("tipo") else "")
                 + "door leaves, exactly as drawn.")
    else:
        L.append("The drawing shows the INTERIOR, with no door leaves drawn: render this "
                 "wardrobe OPEN, with the interior visible. Do NOT add doors that are not drawn, "
                 "and do NOT close bays that are drawn open.")

    ac = datos.get("acabados") or {}
    if ac.get("frentes"):
        L.append(f"Fronts finish written on the drawing: {ac['frentes']}.")
    if ac.get("interior"):
        L.append(f"Interior finish written on the drawing: {ac['interior']}.")
    if datos.get("notas"):
        L.append(f"Notes on the drawing: {datos['notas']}")

    L.append(f"COUNT BEFORE YOU FINISH: {len(cuerpos)} cuerpo(s)"
             + (" plus the altillo band on top" if alt.get("hay") else "")
             + ". Not one more, not one less. Adding a bay, a column of shelves or a bank of "
               "drawers that is not on this list makes it a DIFFERENT wardrobe.")
    return "\n".join(L)


def resumen_para_pantalla(datos: Dict[str, Any]) -> str:
    """Lo mismo, en castellano, para el recuadro de debajo del render.

    Esto es lo que le deja al master comprobar de un vistazo si el dibujo se ha
    leído bien SIN tener que deducirlo de la imagen. Si aquí pone tres cuerpos
    y él dibujó dos, ya sabe dónde está el fallo.
    """
    if not datos:
        return ""
    cuerpos = datos.get("cuerpos") or []
    L: List[str] = [f"Armario de {len(cuerpos)} cuerpo(s)."]

    med = []
    if datos.get("ancho_total_cm"):
        med.append(f"ancho {datos['ancho_total_cm']:.0f} cm")
    if datos.get("alto_total_cm"):
        med.append(f"alto {datos['alto_total_cm']:.0f} cm")
    if datos.get("fondo_cm"):
        med.append(f"fondo {datos['fondo_cm']:.0f} cm")
    L.append("Medidas: " + (", ".join(med) + "." if med else
                            "ninguna escrita en el dibujo (se han respetado las proporciones)."))

    alt = datos.get("altillo") or {}
    if alt.get("hay"):
        div = alt.get("divisiones")
        L.append("Altillo corrido por encima" + (f", {div} secciones" if div else "") + ".")

    for c in cuerpos:
        ancho = ""
        if c.get("ancho_cm"):
            ancho = f" ({c['ancho_cm']:.0f} cm{' deducido' if c.get('ancho_deducido') else ''})"
        L.append(f"· Cuerpo {c['orden']}{ancho}: "
                 f"{_interior_en_texto(c.get('interior') or [], 'es')}")

    pu = datos.get("puertas") or {}
    L.append("Con puertas dibujadas." if pu.get("hay")
             else "Sin puertas dibujadas: alzado del interior.")

    for aviso in (datos.get("avisos") or []):
        L.append(f"⚠ {aviso}")
    if sin_cotas(datos):
        L.append("⚠ El dibujo no trae ni una medida: sirve para ver el diseño, "
                 "no para presupuestar.")
    return "\n".join(L)
