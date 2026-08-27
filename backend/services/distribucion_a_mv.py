# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Puente: la DISTRIBUCIÓN detectada en el Estudio 3D → muebles MV de catálogo.

El Estudio 3D sabe qué módulos hay en cada pared y cuánto mide cada uno. La
tarifa MV sabe qué muebles existen y cuánto valen. Faltaba lo de en medio, y
resulta que encaja casi solo: **el número del código MV ES el ancho en cm**
(`B60D` = bajo de 60, una puerta). Así que traducir es, sobre todo, elegir bien
la FAMILIA y no inventarse nada donde no hay dato.

Lo que este módulo NO hace, a propósito:

· No pone precios. Devuelve la notación («1 b60d + 1 bf90…») y de tarifarla se
  encarga `mv_relacion`, que es el que lee el catálogo oficial y ya está
  probado. Dos caminos hasta el precio serían dos sitios donde equivocarse.
· No se inventa un código que no exista en la tarifa. Cada propuesta se
  comprueba contra el catálogo real; si no está, la línea sale SIN código y
  diciendo por qué.
· No le pone casco a un electrodoméstico. Regla 6 de CLAUDE.md: el lavavajillas
  va en HUECO, sin mueble (su puerta de integración es material nuestro). El
  bajo fregadero y el bajo horno SÍ son muebles. Meterle un casco al
  lavavajillas infla el pedido al proveedor con un mueble que no existe.
· No decide la mano (D/I) en silencio. La PROPONE, y va marcada como propuesta
  para que se revise.
"""
import json
import os
from typing import Optional

_MV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "mv_tarifas_oficiales.json")

# ── De qué familia MV es cada módulo ────────────────────────────────────────
# `seguro=False` significa: la familia es un CRITERIO, no un dato. Sale
# propuesta y marcada para confirmar, porque acertar de familia cambia el
# mueble que se le pide a MV.
#
# (prefijo, familia legible, seguro)
MAPA = {
    "bajo":            ("B",   "Bajo", True),
    "bajo_fregadero":  ("BF",  "Bajo fregadero", True),
    "fregadero":       ("BF",  "Bajo fregadero", True),
    "bajo_horno":      ("BH",  "Bajo horno", True),
    "horno":           ("BH",  "Bajo horno", True),
    "cajonera":        ("BC",  "Bajo 5 cajones", False),
    "bajo_cajones":    ("BC",  "Bajo 5 cajones", False),
    "gavetero":        ("BCG", "Bajo 3 cajones + gaveta", False),
    "placa":           ("B",   "Bajo (bajo la placa)", False),
    "alto":            ("A",   "Alto", True),
    "alacena":         ("A",   "Alto", True),
    "campana":         ("ASC", "Alto campana", True),
    "microondas":      ("AM",  "Alto microondas", True),
    "escurreplatos":   ("AE",  "Alto escurreplatos", True),
    "altillo":         ("L",   "Altillo", True),
    "sobreencimera":   ("S",   "Sobreencimera", True),
    "mediacolumna":    ("M",   "Mediacolumna", True),
    "frigorifico":     ("CF",  "Columna frigorífico", True),
    "columna_hornos":  ("CH",  "Columna horno", True),
    "despensa":        ("CD",  "Columna despensero", True),
    "vinoteca":        ("CD",  "Columna despensero", False),
    "congelador":      ("CF",  "Columna frigorífico", False),
}

# Electrodomésticos que van EN HUECO: no llevan casco (CLAUDE.md, regla 6).
SIN_CASCO = {
    "lavavajillas": "va en hueco, sin casco. Su puerta de integración es material nuestro",
    "lavadora": "va en hueco, sin casco",
    "secadora": "va en hueco, sin casco",
    "nevera": "si no es de columna, va en hueco y sin casco",
}

# El relleno no es un mueble de catálogo: es una pieza a medida.
A_MEDIDA = {"relleno": "es una pieza a medida, no un mueble de catálogo"}

# ─── ALTURAS POR DEFECTO ─────────────────────────────────────────────────────
#
# LA ALTURA MANDA EN EL PRECIO, así que estos tres números no son cosmética: un
# alto de 60 vale 156,51 € a 70 cm y 169,83 € a 90.
#
# Hasta el 25/08/2026 la pantalla NO mandaba ninguna altura y el backend cogía
# 70 para los altos y 200 para las columnas sin decírselo a nadie. O sea que
# TODA relación MV salía tarifada a 70/200 aunque la cocina llevara otra cosa:
# ni aviso, ni error, un número plausible y a correr. El master lo cambió al
# leer la auditoría: «por defecto altos de 90, bajos de 80 y columnas de 220».
#
# Son PROPUESTAS, no dogma: las tres se pueden cambiar en el presupuesto antes
# de pasar a pedido (`alto_altos` / `alto_columnas` en el cuerpo de la
# petición). Lo que no puede volver a pasar es que las elija el código en
# silencio.

# En esta fábrica los bajos SOLO se fabrican a 80 (CLAUDE.md). No es una
# preferencia: es que no hay otra.
ALTO_BAJOS = 80
# Alto: 70 o 90 (CLAUDE.md). Se propone la de 90.
ALTO_ALTOS = 90
# Columna: 200 o 220 (CLAUDE.md). Se propone la de 220.
ALTO_COLUMNAS = 220


def _catalogo(tarifa: str = "T1") -> set:
    """Todos los códigos que EXISTEN en la tarifa, en mayúsculas."""
    with open(_MV_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    codigos = set()
    for _fam, info in (data.get("tariffs", {}).get(tarifa, {}) or {}).items():
        items = info.get("items")
        if isinstance(items, dict):
            codigos.update(c.upper() for c in items)
    return codigos


def _propone_mano(indice: int) -> str:
    """Mano PROPUESTA, alternando a lo largo de la pared.

    No es una deducción: es una propuesta razonable para no dejar quince
    huecos que rellenar a mano. Va marcada como propuesta y se cambia en la
    relación. Lo que no se puede hacer es elegirla en silencio y que parezca un
    dato.
    """
    return "D" if indice % 2 == 0 else "I"


def _altura_de(fila: str, prefijo: str, alto_altos: int = ALTO_ALTOS,
               alto_columnas: int = ALTO_COLUMNAS) -> int:
    """La altura MANDA EN EL PRECIO, así que no puede quedarse en blanco.

    Se vio probándolo: un alto de 60 vale 156,51 € a 70 cm y 169,83 € a 90. Si
    la altura no llega, la tarifa coge la que sea y el precio sale de otro
    mueble.
    """
    if prefijo in ("CF", "CH", "CD"):
        return alto_columnas          # columna: 200 o 220
    if prefijo in ("S", "SV", "SC"):
        return 127                    # sobreencimera: 127 o 147
    if fila == "alto":
        return alto_altos             # alto: 70 o 90
    return ALTO_BAJOS                 # bajo: siempre 80 en esta fábrica


def distribucion_a_relacion(distribucion: dict, tarifa: str = "T1",
                            alto_altos: int = ALTO_ALTOS,
                            alto_columnas: int = ALTO_COLUMNAS) -> dict:
    """Traduce una distribución a líneas de relación MV.

    Devuelve {lineas, sin_codigo, notacion}. `notacion` es el texto que entiende
    `mv_relacion.parse_relacion_text`, que es quien pone los precios.
    """
    codigos = _catalogo(tarifa)
    lineas, sin_codigo = [], []
    elementos = sorted((distribucion or {}).get("elementos") or [],
                       key=lambda e: (e.get("pared_idx", 0), e.get("posicion_cm", 0)))

    # La mano alterna por pared, no por cocina entera.
    contador_por_pared = {}

    for e in elementos:
        eid = str(e.get("id") or "").lower().strip()
        etiqueta = e.get("label") or eid or "Módulo"
        ancho = int(e.get("ancho") or 0)
        pared = int(e.get("pared_idx") or 0)
        fila = e.get("fila") or "bajo"

        motivo_fuera = SIN_CASCO.get(eid) or A_MEDIDA.get(eid)
        if motivo_fuera:
            sin_codigo.append({"label": etiqueta, "id": eid, "ancho": ancho,
                               "pared_idx": pared, "motivo": motivo_fuera})
            continue

        entrada = MAPA.get(eid)
        if not entrada:
            sin_codigo.append({"label": etiqueta, "id": eid, "ancho": ancho,
                               "pared_idx": pared,
                               "motivo": "no sé de qué familia MV es: dilo tú"})
            continue

        prefijo, familia, seguro = entrada
        if not ancho:
            sin_codigo.append({"label": etiqueta, "id": eid, "ancho": 0,
                               "pared_idx": pared,
                               "motivo": "sin ancho no hay código: el número del código ES el ancho"})
            continue

        # ¿Existe con mano (una puerta) o sin ella (dos puertas)?
        con_mano = f"{prefijo}{ancho}D/I".upper() in codigos
        sin_mano = f"{prefijo}{ancho}".upper() in codigos
        if not con_mano and not sin_mano:
            anchos = sorted({int(c[len(prefijo):].split("D")[0])
                             for c in codigos
                             if c.startswith(prefijo) and c[len(prefijo):].split("D")[0].isdigit()})
            sin_codigo.append({
                "label": etiqueta, "id": eid, "ancho": ancho, "pared_idx": pared,
                "motivo": (f"MV no hace «{familia}» de {ancho} cm"
                           + (f" (los hay de {', '.join(str(a) for a in anchos)})" if anchos else ""))})
            continue

        i = contador_por_pared.get(pared, 0)
        if con_mano:
            mano = _propone_mano(i)
            contador_por_pared[pared] = i + 1
            codigo = f"{prefijo}{ancho}{mano}"
        else:
            mano = None                      # dos puertas: no hay mano que elegir
            codigo = f"{prefijo}{ancho}"

        lineas.append({
            "label": etiqueta, "id": eid, "pared_idx": pared,
            "posicion_cm": int(e.get("posicion_cm") or 0),
            "familia": familia, "codigo": codigo, "ancho": ancho,
            "mano": mano, "mano_propuesta": bool(mano),
            "puede_dos_puertas": sin_mano and con_mano,
            "alto": _altura_de(fila, prefijo, alto_altos, alto_columnas),
            "confirmar_familia": not seguro,
        })

    return {"lineas": lineas, "sin_codigo": sin_codigo,
            "notacion": notacion_de(lineas)}


def reaplica_alturas(lineas, alto_altos: int = ALTO_ALTOS,
                     alto_columnas: int = ALTO_COLUMNAS):
    """Vuelve a poner la altura a unas líneas YA HECHAS, sin tocar nada más.

    Hace falta porque cada línea lleva su propia altura dentro (`notacion_de`
    escribe «(altura N)» mueble a mueble), así que cambiar el desplegable de la
    pantalla no serviría de nada si las líneas siguieran con la altura vieja: se
    volvería a tarifar exactamente igual.

    La regla de qué altura le toca a cada uno NO se repite aquí: se le pregunta
    a `_altura_de`, que es quien la sabe. El prefijo se saca del código —«A60D»
    -> «A», «CF60» -> «CF»— quitándole el ancho y la mano.

    Se respeta lo que el usuario haya tocado a mano en otras cosas (la mano, el
    dos puertas): esto SOLO cambia `alto`.
    """
    salida = []
    for ln in lineas or []:
        copia = dict(ln)
        cod = str(copia.get("codigo") or "").upper()
        # El prefijo son las letras del principio, hasta el primer dígito.
        prefijo = ""
        for c in cod:
            if c.isdigit():
                break
            prefijo += c
        if prefijo:
            fila = "alto" if prefijo.startswith("A") else "bajo"
            copia["alto"] = _altura_de(fila, prefijo, alto_altos, alto_columnas)
        salida.append(copia)
    return salida


def notacion_de(lineas) -> str:
    """El texto que entiende `mv_relacion`. UN MUEBLE POR LÍNEA.

    Esto no es cosmética, es el precio. `parse_relacion` busca «altura N» UNA
    VEZ POR RENGLÓN y se la aplica a todo lo que haya en él, además de borrar
    todos los paréntesis antes de trocear. O sea que juntando la cocina entera
    en una línea con «+», la primera altura se la come todo: se probó y los
    siete muebles salieron a 80 cm, incluidos los ALTOS, que a 80 no existen
    —van a 70 o a 90— y que valen distinto en cada altura.

    Con un mueble por línea, cada uno lleva la suya y se tarifa por la que es.
    """
    renglones = []
    for ln in lineas:
        pieza = f"1 {ln['codigo'].lower()}"
        if ln.get("alto"):
            pieza += f" (altura {ln['alto']})"
        renglones.append(pieza)
    return "\n".join(renglones)
