# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""ALTOS 90 · BAJOS 80 · COLUMNAS 220, TAMBIÉN AL PEGAR (11/09/2026).

El master, viendo una columna a 200 en el presupuestador: «siempre por defecto
los muebles que detecte que sean los altos de altura 90, y los bajos de 80» y
«las columnas de 220 de alto». Es la regla 13 de CLAUDE.md, escrita desde el
25/08 — y por el camino del PEGADO MASIVO no se cumplía.

CÓMO SE COLABA, Y POR QUÉ NO SALTABA NADA. En `parse_relacion` solo los BAJOS
tenían altura por defecto; altos y columnas se quedaban con `alto = None`. Y
`_puntos` trata la falta de altura como «el escalón de abajo»:

    return ev[1] if (alto and alto > 210) else ev[0]

O sea que una columna pegada sin «altura N» se tarifaba a 200 —el escalón
barato— y salía en pantalla como 200. Un presupuesto 20 cm más bajo de lo que
esta fábrica fabrica, sin un solo error.

Se llega por ahí porque es como se traen los muebles leídos del plano: «he
copiado los muebles detectados y los he pegado en pegado masivo».
"""
import importlib.util
import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND = os.path.join(RAIZ, "backend")
sys.path.insert(0, BACKEND)
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services.mv_relacion import (  # noqa: E402
    ALTURA_POR_DEFECTO, altura_por_defecto, parse_relacion)

PANTALLA = os.path.join(RAIZ, "frontend", "src", "components", "CocinaMontada3.jsx")


def _muebles(texto, tarifa="T4"):
    return {m["cod"]: m for m in parse_relacion(texto, tarifa)["muebles"]}


# ─── Lo que pidió el master, ejecutado ──────────────────────────────────────

@pytest.mark.parametrize("texto,cod,esperado", [
    ("1 chm60", "CHM60", 220),      # columna horno+micro
    ("1 cd60d", "CD60D/I", 220),    # despensero
    ("1 cf60", "CF60", 220),        # columna frigo
    ("1 a60d", "A60D/I", 90),       # alto
    ("1 a90", "A90", 90),
    ("1 b60", "B60", 80),           # bajo
    ("1 bf60", "BF60", 80),         # bajo fregadero
])
def test_sin_altura_escrita_sale_la_DE_LA_FABRICA(texto, cod, esperado):
    """CANDADO PRINCIPAL. Pegar sin «altura N» tiene que dar la de siempre."""
    m = _muebles(texto)
    assert cod in m, f"«{texto}» ya no se reconoce; sale {sorted(m)}"
    assert m[cod].get("alto") == esperado, (
        f"«{texto}» sale a {m[cod].get('alto')} y la fábrica lo hace a "
        f"{esperado} (CLAUDE.md, regla 13)")


def test_una_columna_SIN_altura_NO_se_tarifa_por_el_escalon_barato():
    """Es lo que de verdad costaba dinero: sin altura, `_puntos` devolvía el
    precio de 200. Se compara con la MISMA columna escrita a 200 a propósito;
    si los dos precios coinciden, el defecto no está llegando a la tarifa."""
    sin = _muebles("1 chm60")["CHM60"]
    a200 = _muebles("1 chm60 (altura 200)")["CHM60"]
    a220 = _muebles("1 chm60 (altura 220)")["CHM60"]
    assert sin.get("pvp") == a220.get("pvp"), (
        "una columna sin altura escrita NO se está tarifando como 220")
    assert a200.get("pvp") != a220.get("pvp"), (
        "200 y 220 cuestan lo mismo: esta prueba no puede distinguir nada y "
        "pasaría por el motivo equivocado")


def test_una_altura_ESCRITA_manda_sobre_el_defecto():
    """No se corrige lo que alguien ha puesto a propósito: solo se rellena lo
    que falta. Si el defecto pisara lo escrito, ajustar una altura a mano no
    serviría de nada."""
    assert _muebles("1 chm60 (altura 200)")["CHM60"].get("alto") == 200
    assert _muebles("1 a60d (altura 70)")["A60D/I"].get("alto") == 70


def test_lo_que_no_se_sabe_QUE_ES_no_recibe_altura_inventada():
    """Regla 7: una medida que no se puede derivar se queda vacía."""
    assert altura_por_defecto("LINEAL", None) is None
    assert altura_por_defecto("", None) is None
    assert altura_por_defecto(None, None) is None


def test_los_tres_defectos_estan_en_UN_SOLO_SITIO():
    """Estaban repartidos: el `80` de los bajos escrito a mano en una rama y
    nada en la otra. Con dos caminos que resuelven la altura, arreglar uno deja
    el otro tarifando barato — que es justo lo que pasaba."""
    assert ALTURA_POR_DEFECTO == {"BAJO": 80, "ALTO": 90, "COLUMNA": 220}


def test_LOS_DOS_CAMINOS_del_parser_aplican_el_defecto():
    """`parse_relacion` resuelve la altura en DOS ramas: por código exacto del
    catálogo y por letras+ancho deducidos. Arreglar solo una es el fallo del
    `editingRender` otra vez."""
    src = open(os.path.join(BACKEND, "services", "mv_relacion.py"),
               encoding="utf-8").read()
    codigo = "\n".join(l.split("#")[0] for l in src.splitlines())
    veces = codigo.count("altura_por_defecto(")
    assert veces >= 3, (
        f"`altura_por_defecto` se usa {veces} vece(s): tiene que ser su "
        f"definición MÁS las dos ramas del parser. Si falta una, por ese "
        f"camino las columnas se siguen tarifando a 200.")


# ─── Y la pantalla, que tiene su propia lista ───────────────────────────────

def test_la_pantalla_OFRECE_220_primero_en_las_columnas():
    """El primero de cada lista es el que se asigna al añadir (`opciones[0]`).
    Con `[200, 220]` cada columna nueva nacía a 200."""
    src = open(PANTALLA, encoding="utf-8").read()
    i = src.index("const OPCIONES_ALTURA")
    linea = src[i:src.index("\n", i)]
    assert "h200220: [220, 200]" in linea, (
        f"las columnas ya no salen a 220 por defecto en pantalla: {linea}")
    assert "h7090: [90, 70]" in linea, "los altos ya no salen a 90"
    assert "bajo: [80, 70]" in linea, "los bajos ya no salen a 80"


def test_los_atajos_de_columna_dicen_220():
    """Los botones de «+ CHM60» y compañía escriben la altura en el texto que
    se parsea: si dicen 200, mandan ellos sobre el defecto."""
    src = open(PANTALLA, encoding="utf-8").read()
    assert "(altura 200)" not in src, (
        "algún atajo rápido sigue escribiendo «altura 200»: eso manda sobre el "
        "defecto y la columna vuelve a nacer a 200")
