# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
CADA AJUSTE, COLGANDO DE SU PERMISO. Y CADA CASILLA, DICIENDO QUÉ ABRE.

El master, 30/08, mirando los permisos de un usuario: «cocina por módulos aquí
en permisos de usuario, apartado red distribución, es Estudio 3D».

Y tenía razón, aunque el fallo no era el nombre de la casilla. El panel de
«tipos permitidos» colgaba de la casilla EQUIVOCADA:

  · `estudio3dTipos` lo lee `AIRenderStudio.jsx`, o sea la pantalla «Estudio
    3D», que se abre con `canUseAIAnalysis`.
  · Pero el panel solo aparecía al marcar `canUseKitchenDesigner`, que es
    «Cocinas por módulos»: otra sección y otro permiso.

O sea que se configuraba una pantalla desde la casilla de otra. Por eso parecía
que la casilla estaba mal nombrada: lo que estaba mal era de dónde colgaba.

Y DE PASO, LA OTRA MITAD DE LA REGLA 26. «Una sección, un permiso» vigila que
una sección no tenga dos permisos. Aquí pasaba lo contrario: un permiso abre DOS
secciones —`canUseAIAnalysis` abre «IA Lab» y «Estudio 3D»— y la casilla solo
nombraba una, así que quitarle el Estudio 3D a alguien era imposible de
encontrar. Mientras compartan permiso, la casilla tiene que nombrar las dos.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PANEL = os.path.join(RAIZ, "frontend", "src", "components", "SettingsModal.jsx")
INICIO = os.path.join(RAIZ, "frontend", "src", "components", "WelcomeScreen.jsx")
RENDER = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _rotulo_de(clave):
    """El texto VISIBLE de la casilla que escribe ese permiso.

    Se saca el `<span>` y se quitan los comentarios: la primera versión de esta
    prueba miraba 900 caracteres a bulto y ahí dentro caían el `title=` y el
    comentario de encima, que también dicen «Estudio 3D». O sea que pasaba con
    el rótulo cambiado — un candado que no puede fallar no vigila nada.
    """
    cuerpo = _lee(PANEL)
    i = cuerpo.index(f"{clave}: e.target.checked}}")
    trozo = cuerpo[i:i + 1200]
    trozo = re.sub(r"\{/\*.*?\*/\}", "", trozo, flags=re.S)      # fuera comentarios
    m = re.search(r"<span[^>]*>([^<]+)</span>", trozo)
    assert m, f"no se encuentra el rótulo de «{clave}»"
    return m.group(1).strip()


def test_LOS_TIPOS_DEL_ESTUDIO_3D_CUELGAN_DE_SU_PERMISO():
    """El fallo que vio el master, en una línea."""
    cuerpo = _lee(PANEL)
    i = cuerpo.index("Estudio 3D · tipos permitidos")
    # La condición que enseña el panel está justo encima.
    encima = cuerpo[max(0, i - 900):i]
    assert "userForm.canUseAIAnalysis &&" in encima, (
        "el panel de «tipos permitidos del Estudio 3D» no cuelga de "
        "`canUseAIAnalysis`, que es el permiso que abre esa pantalla: se está "
        "configurando una sección desde la casilla de otra")
    assert "userForm.canUseKitchenDesigner &&" not in encima, (
        "vuelve a colgar de «Cocinas por módulos», que es otra sección")


def test_LOS_TIPOS_SON_DE_LA_PANTALLA_QUE_LOS_LEE():
    """Que no se mueva el panel a un permiso que tampoco es el suyo: quien lee
    `estudio3dTipos` es el Estudio 3D."""
    assert "estudio3dTipos" in _lee(RENDER), (
        "`AIRenderStudio.jsx` ya no lee `estudio3dTipos`: si esos tipos los "
        "consume otra pantalla, el panel tiene que mudarse con ella")


def _entrada(tab):
    for linea in _lee(INICIO).split("\n"):
        if re.search(r"\{\s*tab:\s*'%s'" % re.escape(tab), linea):
            return linea
    raise AssertionError(f"no hay entrada de menú para «{tab}»")


def test_UNA_CASILLA_QUE_ABRE_DOS_SECCIONES_LAS_NOMBRA_LAS_DOS():
    """`canUseAIAnalysis` abre «IA Lab» y «Estudio 3D».

    Mientras compartan permiso, la casilla tiene que nombrar los dos: si solo
    dice «IA Lab», quitarle el Estudio 3D a alguien no se puede encontrar — que
    es exactamente lo que ya pasó con «Cocinas por módulos» (regla 26).
    """
    for tab in ("visualizer", "renderStudio"):
        assert "canUseAIAnalysis" in _entrada(tab), (
            f"«{tab}» ha dejado de abrirse con `canUseAIAnalysis`: si ahora "
            "tiene permiso propio, la casilla puede volver a nombrar solo uno")
    rotulo = _rotulo_de("canUseAIAnalysis")
    assert "IA Lab" in rotulo and "Estudio 3D" in rotulo, (
        f"la casilla de `canUseAIAnalysis` se lee «{rotulo}» y abre DOS "
        "secciones: tiene que nombrar las dos, o quitar una es imposible de "
        "encontrar")


def test_COCINAS_POR_MODULOS_NO_PROMETE_EL_ESTUDIO_3D():
    """Su casilla decía que abría también el Estudio 3D, y no lo abre: el
    Estudio 3D se abre con `canUseAIAnalysis`. Una etiqueta que promete de más
    hace que se marque un permiso para conseguir otro."""
    rotulo = _rotulo_de("canUseKitchenDesigner")
    assert rotulo == "Cocinas por módulos", (
        f"la casilla se lee «{rotulo}» y la sección del menú se llama «Cocinas "
        "por módulos»: si no se llaman igual, no se puede encontrar para "
        "quitarla (regla 26)")
    cuerpo = _lee(PANEL)
    i = cuerpo.index("canUseKitchenDesigner: e.target.checked})")
    assert "y el acceso a Estudio 3D" not in cuerpo[i:i + 800], (
        "la casilla de «Cocinas por módulos» vuelve a prometer el Estudio 3D, "
        "que se abre con otro permiso: una etiqueta que promete de más hace "
        "que se marque un permiso para conseguir otro")
