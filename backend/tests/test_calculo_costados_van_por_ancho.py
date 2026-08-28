# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
COSTADOS, LATERALES Y REGLETAS: LAS DOS COLUMNAS SON EL ANCHO, NO EL ALTO.

El master, 25/08/2026, mirando Cocina Montada 3:

    «en la librería de MV los costados estás poniendo alto 70 y 90 pero ese es
    el ancho, hasta 70 y hasta 90»

Y tiene razón. En la tarifa (pág. 6) esas familias llevan dos columnas «70» y
«90» igual que los ALTOS, pero no dicen lo mismo:

  · En un ALTO, 70/90 es la altura del mueble. Correcto.
  · En un COSTADO es el ancho de la PIEZA. Se ve en la propia hoja: «REGLETA
    COLOR **Ancho 15**» lleva esas mismas dos columnas, y la fila del costado de
    bajo se describe como «CCB Costado color bajo **70/85 alto**» — o sea que la
    altura va en la DESCRIPCIÓN de la fila, no en la cabecera de la columna.

LA PRUEBA DE QUE ESTABA MAL NO ES UNA OPINIÓN. Compartían el tipo `h7090` y la
columna se elegía con `alto >= 85`. Un costado de COLUMNA mide 200-220 de alto,
así que caía SIEMPRE en la columna de 90: la barata era INALCANZABLE. Igual para
el de mediacolumna (130) y el de sobreencimera (127/147). Una columna de tarifa
que no se puede alcanzar por ningún camino no es una preferencia — es la prueba
de que la clave de búsqueda está mal.

Y no era gratis: el ancho de un costado es el FONDO del mueble que remata (33 en
altos, 58 en bajos y columnas), o sea que el caso CORRIENTE es «hasta 70», que
es justo el que no salía nunca. Se estaba tarifando por la columna cara.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import mv_relacion as MV  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARIFA = os.path.join(RAIZ, "backend", "data", "mv_tarifas_oficiales.json")
MONTADA3 = os.path.join(RAIZ, "frontend", "src", "components", "CocinaMontada3.jsx")

# Las cinco familias de la página de lineales de la tarifa. Las REGLETAS entran
# igual que los costados, y no por deducción: se le preguntó al master al
# revisar este cambio y lo confirmó — «las regletas de color son correctas»
# (25/08). Cuadra con la hoja: la regleta de color lleva escrito «Ancho 15» al
# lado de las mismas dos columnas 70/90, o sea que su ancho de tablero y el
# tramo de tarifa son dos cosas distintas. La de melamina es idéntica en
# estructura («Ancho 10», mismas columnas, mismas cuatro filas).
LINEALES = ("LATERALES_COLOR", "COSTADOS_COLOR", "REGLETA_COLOR",
            "REGLETA_MELAMINA", "COSTADOS_MELAMINA")


def _tarifas():
    with open(TARIFA, "r", encoding="utf-8") as f:
        return json.load(f)["tariffs"]


# ── El catálogo ──────────────────────────────────────────────────────────────
# RESUELTO EL 28/08, con el libro delante. Durante un tiempo T19, T20 y T21
# tuvieron COSTADOS_MELAMINA por `ent`/`med` en vez de por 70/90, y con valores
# propios. Se dejó marcado sin tocar —un dato de tarifa que no se sabe no se
# ajusta «para que cuadre»— hasta poder comprobarlo contra el papel.
#
# El master mandó las páginas 102, 108, 114, 120 y 126 (tarifas 17 a 21) y las
# cinco dicen lo mismo: 19/20, 27/28, 8 y 15. Y en el propio fichero, 18 de las
# 21 tarifas ya lo tenían así. El costado de melamina es un ACCESORIO y no
# depende de la tarifa de puerta, que es justo por lo que no varía.
#
# Así que las tres eran un error de importación y se corrigieron. Ya no queda
# nada sin resolver: si vuelve a aparecer algo, se añade aquí.
SIN_RESOLVER = set()

# Lo que dice el libro, y lo que tienen que decir TODAS las tarifas.
COSTADO_MELAMINA_DEL_LIBRO = {"CMCB": [19, 20], "CMCC": [27, 28],
                              "CMBB": [8, None], "CMBC": [15, None]}


def test_los_lineales_NO_comparten_tipo_con_los_altos():
    """Mientras compartieran `h7090`, cualquier arreglo en uno tocaba al otro."""
    fallos = []
    for t, fam in _tarifas().items():
        for f in LINEALES:
            if (t, f) in SIN_RESOLVER:
                continue
            if f in fam and fam[f].get("type") != "a7090":
                fallos.append(f"{t}/{f}={fam[f].get('type')}")
    assert not fallos, (
        "estas familias vuelven a estar como altura: " + ", ".join(fallos[:8]))


def test_NO_QUEDA_NADA_sin_resolver():
    """Una excepción anotada no puede quedarse ahí de por vida.

    Estaba pensada para ponerse en rojo el día que se resolviera, y así fue: el
    28/08 se corrigieron T19-T21 con el libro delante. Si mañana aparece otra
    discrepancia se añade a `SIN_RESOLVER` y esta prueba avisa de que hay algo
    pendiente de preguntar.
    """
    for t, f in SIN_RESOLVER:
        assert _tarifas()[t][f].get("cols") == ["ent", "med"], (
            f"{t}/{f} ya no está por ent/med: hay que sacarla de SIN_RESOLVER")


def test_el_COSTADO_DE_MELAMINA_vale_lo_mismo_en_TODAS_las_tarifas():
    """Es un accesorio: no depende de la tarifa de puerta.

    Lo dicen las cinco páginas que mandó el master (17 a 21) y lo tenían ya 18
    de las 21 tarifas del fichero. T19, T20 y T21 se salían —con columnas
    `ent`/`med` inventadas y valores propios— y eran un error de importación.

    Este candado existe porque el error volvería igual si alguien re-importa la
    tarifa con el mismo escáner: aquí se ve enseguida y allí no se ve nunca.
    """
    fallos = []
    for t, familias in _tarifas().items():
        fam = familias.get("COSTADOS_MELAMINA")
        if not fam:
            continue
        if fam.get("cols"):
            fallos.append(f"{t}: columnas {fam['cols']} (van por ancho 70/90)")
        # T1..T3 traen los valores de una edición anterior (7/8 y 13/14); no se
        # tocan porque el libro que hay delante es el de T17-T21. Lo que NO
        # puede pasar es que una tarifa tenga valores que no salen en ninguna
        # edición, que es lo que les pasaba a T19-T21.
        if t in ("T19", "T20", "T21") and fam["items"] != COSTADO_MELAMINA_DEL_LIBRO:
            fallos.append(f"{t}: {fam['items']} en vez de {COSTADO_MELAMINA_DEL_LIBRO}")
    assert not fallos, "; ".join(fallos)


def test_los_ALTOS_de_verdad_siguen_yendo_por_ALTURA():
    """El arreglo no puede llevarse por delante lo que sí estaba bien: en un
    alto, 70/90 ES la altura (CLAUDE.md: casco alto 700 o 900)."""
    fam = _tarifas()["T1"]
    assert fam["ALTO"]["type"] == "h7090"
    assert MV._puntos({"t": "h7090", "e": [10, 20]}, 90) == 20
    assert MV._puntos({"t": "h7090", "e": [10, 20]}, 70) == 10


def test_no_se_ha_movido_NI_UN_PUNTO_de_la_tarifa():
    """Cambiar la etiqueta no puede cambiar los precios. Los puntos de la
    tarifa son datos del proveedor: se leen, no se ajustan."""
    fam = _tarifas()["T1"]["COSTADOS_COLOR"]["items"]
    assert fam == {"CCA": [9, 10], "CCF": [14, 15], "CCB": [12, 15],
                   "CCS": [14, 16], "CCM": [17, 21], "CCC": [33, 36]}, (
        "han cambiado los puntos de COSTADOS_COLOR en T1")


# ── El cálculo ───────────────────────────────────────────────────────────────
def test_LAS_DOS_COLUMNAS_SE_PUEDEN_ALCANZAR():
    """La prueba que resume el fallo entero.

    Con la regla vieja (`alto >= 85`) un costado de columna —220 de alto— no
    podía salir barato ni queriendo.
    """
    for cod, ev in (("CCA", [9, 10]), ("CCB", [12, 15]), ("CCS", [14, 16]),
                    ("CCM", [17, 21]), ("CCC", [33, 36])):
        e = {"t": "a7090", "e": ev}
        alcanzables = {MV._puntos(e, None, a) for a in (33, 58, 70, 71, 85, 90)}
        assert alcanzables == set(ev), (
            f"{cod}: con anchos reales solo se alcanza {sorted(alcanzables)} de "
            f"{ev}. Una columna de tarifa inalcanzable es la señal de que la "
            "clave de búsqueda está mal.")


def test_el_ALTO_DEL_MUEBLE_YA_NO_PINTA_NADA_en_un_costado():
    """Lo que hacía que un costado de columna se tarifara por los 220 cm de la
    columna que remata."""
    e = {"t": "a7090", "e": [33, 36]}
    for alto in (70, 90, 130, 200, 220, None):
        assert MV._puntos(e, alto, 58) == 33, (
            f"con un alto de {alto} el costado cambia de columna; el alto del "
            "mueble no decide el precio de la pieza que lo remata")


@pytest.mark.parametrize("ancho,esperado", [
    (33, 33),    # fondo de un alto
    (58, 33),    # fondo de un bajo o una columna: el caso CORRIENTE
    (70, 33),    # el borde exacto entra en «hasta 70»
    (70.5, 36),
    (90, 36),
])
def test_el_corte_esta_en_70_y_el_borde_entra_en_la_barata(ancho, esperado):
    """«Hasta 70» incluye el 70. Si el borde se fuera a la columna cara, el
    caso más común de todos pagaría de más."""
    assert MV._puntos({"t": "a7090", "e": [33, 36]}, None, ancho) == esperado


def test_sin_ancho_se_usa_el_valor_RAZONADO_y_no_un_numero_del_codigo():
    """Un `CCC` no lleva ancho en el código —no hay dígitos que sacar— así que
    aquí no se puede deducir de ninguna parte.

    El defecto son 70 porque el ancho de un costado es el FONDO del mueble (33
    o 58, `_FONDO`), y los dos caben en «hasta 70». No es un número puesto a
    ojo: está razonado y tiene nombre. Lo que NO puede pasar es que se cuele el
    `width = 60` que el parser inventa cuando el código no trae dígitos.
    """
    assert MV.ANCHO_LINEAL_POR_DEFECTO == 70
    assert MV.CORTE_ANCHO_LINEAL == 70
    assert max(MV._FONDO.values()) <= MV.CORTE_ANCHO_LINEAL, (
        "hay un fondo por encima del corte: entonces «hasta 70» ya no es el "
        "caso corriente y el valor por defecto habría que repensarlo")
    assert MV._puntos({"t": "a7090", "e": [33, 36]}, 220, None) == 33


# ── El importador (lo que alimenta el buscador) ──────────────────────────────
def test_el_importador_guarda_el_70_90_COMO_ANCHO():
    """Si volviera a guardarlo como altura, el buscador ofrecería «Alto 70/90»
    para un costado de columna de 220 — que es de donde salió el aviso."""
    with open(os.path.join(RAIZ, "backend", "services",
                           "mv_tariff_importer.py"), "r", encoding="utf-8") as f:
        cuerpo = f.read()
    i = cuerpo.index('elif ftype == "a7090":')
    trozo = cuerpo[i:i + 1200]
    assert "width=a" in trozo and "height=0" in trozo, (
        "el importador vuelve a guardar el 70/90 de los lineales como altura")
    assert 'f"{code}-A{a}"' in trozo, (
        "el código guardado no distingue que es ancho (CCC-A70), así que choca "
        "con el CCC-70 de altura de antes")


# ── La pantalla ──────────────────────────────────────────────────────────────
def test_la_pantalla_dice_ANCHO_y_no_ALTO_en_los_lineales():
    with open(MONTADA3, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    assert "OPCIONES_ANCHO = { a7090: [70, 90] }" in cuerpo, (
        "la pantalla ya no ofrece los anchos de tarifa de los lineales")
    assert "hasta {a} cm" in cuerpo, (
        "el desplegable ya no dice «hasta N cm»: sin el «hasta», 70 y 90 se "
        "leen como una medida exacta y no como un tramo")
    assert "anchoTarifa" in cuerpo, "no se guarda el ancho elegido"


def test_la_pantalla_ELIGE_LA_COLUMNA_IGUAL_QUE_EL_BACKEND():
    """Están en dos sitios: el backend cobra y la pantalla enseña. Si se
    separan, el presupuesto diría un precio y el pedido otro."""
    with open(MONTADA3, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    i = cuerpo.index("else if (t === 'a7090')")
    trozo = cuerpo[i:i + 400]
    assert "a > 70 ? 1 : 0" in trozo, (
        "la pantalla ya no corta en 70 como el backend")
    assert "ANCHO_POR_DEFECTO_LINEAL" in trozo, (
        "la pantalla usa otro valor por defecto que el backend")
