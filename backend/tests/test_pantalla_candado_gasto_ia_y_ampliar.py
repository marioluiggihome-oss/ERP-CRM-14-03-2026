# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL GASTO DE IA DETRÁS DEL CANDADO, Y EL DIBUJO A TOPE DE TAMAÑO.

El master, 14/09/2026: «pon un botón solo para máster para ver estos gastos con
un candado y pulsando shift» y «podemos poner un botón de ver a tope de tamaño
el dibujo renderizado, ocupando toda la pantalla».

1. EL CANDADO DEL GASTO. Por ahí salen los euros que la casa se gasta en IA y
   QUIÉN los gasta, en una pantalla que se enseña con clientes delante. Es la
   misma clase de dato que el coste y el margen de Rentabilidad y se protege
   igual (regla 9): no se bloquea nada, se OCULTA hasta que hay un gesto
   deliberado.
   - SHIFT NO BASTA, Y ESTO NO ES UN DETALLE: **una tablet no tiene tecla
     Shift**, y el master trabaja en una de 8,6". Con solo Shift el candado no
     se abriría NUNCA ahí y el botón parecería roto — que es lo peor, porque no
     da ningún error. Por eso va con `usePulsacionLarga`, que ya resuelve las
     dos formas en un solo sitio.
   - Y EL CIERRE DE VERDAD ESTÁ EN EL SERVIDOR. Si solo se escondiera el botón,
     la URL seguiría contestando a cualquiera con sesión: el fallo del motor de
     render (regla 11), calcado. `require_admin` NO vale — por ahí pasan
     gerente y director comercial (regla 8).

2. VER EL DIBUJO A TOPE DE TAMAÑO. Esto YA EXISTIÓ y se quitó a propósito el
   25/08, cuando se llamaba «Pantalla completa»: había DOS botones con ese
   nombre en la misma pantalla haciendo cosas distintas, y cerrar la capa te
   sacaba de la pantalla completa del navegador aunque hubieras entrado con el
   otro. Vuelve porque el master lo pide, pero se llama «Ampliar» y no toca la
   pantalla completa del navegador. Este candado existe para que no se vuelvan
   a llamar igual.

Las dos, en el Estudio 3D y en su clon (regla 1).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsx_limpio import sin_comentarios  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMPONENTES = os.path.join(RAIZ, "frontend", "src", "components")
PANEL = os.path.join(COMPONENTES, "ConsumoIADelDia.jsx")
ADMIN = os.path.join(RAIZ, "backend", "routes", "admin.py")
PANTALLAS = ("AIRenderStudio.jsx", "Estudio3DLab.jsx")


def _limpio(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return sin_comentarios(f.read())


def _pantalla(nombre):
    cuerpo = _limpio(os.path.join(COMPONENTES, nombre))
    assert "ConsumoIADelDia" in cuerpo, (
        "%s: el recorte de comentarios se ha comido el código" % nombre)
    return cuerpo


# ── 1. El candado del gasto ──────────────────────────────────────────────────

def test_EL_GASTO_SE_ABRE_CON_SHIFT_Y_TAMBIEN_MANTENIENDO_PULSADO():
    """Solo con Shift, en la tablet del master no se abriría nunca."""
    cuerpo = _limpio(PANEL)
    assert "usePulsacionLarga" in cuerpo, (
        "el candado del gasto ya no se abre manteniendo pulsado: en una tablet "
        "no hay tecla Shift y el botón parecería roto")
    assert "e.shiftKey" in cuerpo, "se ha perdido el Shift+clic del ratón"
    assert "largo.consumir()" in cuerpo, (
        "sin `consumir()`, la pulsación larga abre el candado y el clic que "
        "manda el navegador al soltar lo cierra en el mismo gesto")


def test_UN_CLIC_SUELTO_NO_ABRE_EL_CANDADO():
    """Si un toque lo abriera no sería un candado: se abriría por un roce
    delante de un cliente."""
    cuerpo = _limpio(PANEL)
    i = cuerpo.index("onClick={(e) => {")
    bloque = cuerpo[i:i + 700]
    assert "setAbierto(false)" in bloque, (
        "un clic suelto abre el gasto: deja de ser un candado")


def test_EL_BOTON_NO_EXISTE_PARA_QUIEN_NO_ES_MASTER():
    """Enseñarlo apagado sería contarle que hay un sitio con los euros."""
    cuerpo = _limpio(PANEL)
    assert re.search(r"if \(!esMaster\) return null;", cuerpo), (
        "el botón del gasto se pinta también para quien no es master")


def test_EL_SERVIDOR_CIERRA_EL_GASTO_AL_MASTER_Y_NO_SOLO_LA_PANTALLA():
    """Esconder el botón no cierra una URL."""
    with open(ADMIN, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    i = cuerpo.index('@router.get("/ai-usage/por-dia")')
    j = cuerpo.index("async def", i)
    firma = cuerpo[j:cuerpo.index("):", j)]   # hasta cerrar los parámetros
    assert "require_master" in firma, (
        "el consumo diario ya no está cerrado al master: %s" % firma)
    assert "require_admin" not in firma, (
        "se ha abierto a `require_admin`, por donde pasan gerente y director "
        "comercial (regla 8)")


def test_EL_PANEL_ESTA_MONTADO_EN_LAS_DOS_PANTALLAS():
    for pantalla in PANTALLAS:
        cuerpo = _pantalla(pantalla)
        assert "<ConsumoIADelDia" in cuerpo, (
            "%s no monta el panel del gasto" % pantalla)
        assert "esMaster={isMaster}" in cuerpo, (
            "%s monta el panel sin decirle quién es master" % pantalla)


# ── 2. El dibujo a tope de tamaño ────────────────────────────────────────────

def test_SE_PUEDE_VER_EL_DIBUJO_A_TOPE_DE_TAMANO():
    for pantalla in PANTALLAS:
        cuerpo = _pantalla(pantalla)
        assert 'data-testid="btn-ampliar-dibujo"' in cuerpo, (
            "%s no tiene el botón de ampliar" % pantalla)
        assert 'data-testid="dibujo-ampliado"' in cuerpo, (
            "%s tiene el botón pero no la capa que lo agranda" % pantalla)
        i = cuerpo.index('data-testid="dibujo-ampliado"')
        capa = cuerpo[i:i + 900]
        assert "object-contain" in capa, (
            "%s recorta o deforma el render al ampliarlo: en una cocina eso es "
            "el ancho de un mueble, no un detalle estético" % pantalla)


def test_LA_CAPA_AMPLIADA_SE_PUEDE_CERRAR_DE_TRES_FORMAS():
    """Una capa a pantalla completa sin salida clara parece un cuelgue. Y en
    una tablet no hay Escape."""
    for pantalla in PANTALLAS:
        cuerpo = _pantalla(pantalla)
        i = cuerpo.index('data-testid="dibujo-ampliado"')
        capa = cuerpo[i - 200:i + 1400]
        assert "onClick={() => setDibujoAmpliado(false)}" in capa, "falta cerrar tocando el fondo"
        assert "Cerrar" in capa, "falta la X"
        assert "'Escape'" in cuerpo, "falta cerrar con Escape"


def test_AMPLIAR_NO_SE_LLAMA_IGUAL_QUE_LA_PANTALLA_COMPLETA():
    """EL FALLO DEL 25/08: dos botones llamados «Pantalla completa» en la misma
    barra haciendo cosas distintas. Por eso este se quitó entonces."""
    for pantalla in PANTALLAS:
        cuerpo = _pantalla(pantalla)
        i = cuerpo.index('data-testid="btn-ampliar-dibujo"')
        boton = cuerpo[i - 500:i + 600]
        assert "Pantalla completa" not in boton, (
            "%s vuelve a tener dos botones «Pantalla completa» haciendo cosas "
            "distintas" % pantalla)
        assert "Ampliar" in boton


def test_AMPLIAR_NO_TOCA_LA_PANTALLA_COMPLETA_DEL_NAVEGADOR():
    """Mezclarlos era lo que hacía que cerrar la capa te sacara del modo
    pantalla completa aunque hubieras entrado con el otro botón."""
    for pantalla in PANTALLAS:
        cuerpo = _pantalla(pantalla)
        i = cuerpo.index("setDibujoAmpliado(true)")
        bloque = cuerpo[i - 300:i + 300]
        for prohibido in ("requestFullscreen", "exitFullscreen", "BotonPantallaCompleta"):
            assert prohibido not in bloque, (
                "%s mezcla ampliar con la pantalla completa del navegador (%s)"
                % (pantalla, prohibido))
