# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
DESHACER EN LA DISTRIBUCIÓN, Y EL TOTAL A LA VISTA MIENTRAS DISEÑAS.

Las dos «menores» de la lista de mejoras del 25/08/2026. Menores de tamaño, no
de fastidio:

  · No había vuelta atrás. Corriges doce módulos a mano, te equivocas en uno, y
    no hay forma de volver. Y peor: volver a pulsar «Detectar» —UNA TECLA— se
    llevaba los doce por delante.

  · El precio no se veía hasta el final. Había que bajar hasta la relación MV
    para saber por dónde iba la cocina, y al corregir cualquier módulo la
    relación se cerraba: para volver a verlo, otra vez a pulsar.

QUÉ SE HIZO. Una pila con las distribuciones anteriores —incluida la de justo
antes de volver a detectar— y un botón «Deshacer». Y el total se queda vivo: al
corregir un módulo se vuelve a pedir la relación en vez de cerrarla, así que el
número se actualiza solo.

OJO CON EL TOTAL: solo se pinta si hay total. A quien no puede ver la tarifa MV
el servidor le manda `totalPvp` en nulo (CLAUDE.md, regla 8b), y esta pantalla
no puede convertirse en la puerta de atrás para verlo.
"""
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ESTUDIO = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")


def _codigo():
    with open(ESTUDIO, "r", encoding="utf-8") as f:
        return f.read()


# ── Deshacer ─────────────────────────────────────────────────────────────────
def test_hay_deshacer_en_el_panel_de_distribucion():
    cuerpo = _codigo()
    assert "deshacerDistribucion" in cuerpo, "no hay deshacer en la distribución"
    assert "Deshacer" in cuerpo, "el botón de deshacer no se pinta"


def test_se_guarda_el_estado_ANTES_de_cada_correccion():
    cuerpo = _codigo()
    trozo = cuerpo[cuerpo.index("const corregirDistribucion"):]
    trozo = trozo[:trozo.index("const olvidarRelacionMV")] if "const olvidarRelacionMV" in trozo else trozo[:4000]
    assert "apilarDistribucion(base)" in trozo, (
        "corregir un módulo ya no guarda el estado anterior: no habría a dónde "
        "volver")


def test_volver_a_DETECTAR_tambien_se_puede_deshacer():
    """El caso que más duele y el que pidió el master.

    Una detección nueva es una tecla. Si se lleva por delante las correcciones
    de una tarde sin vuelta atrás, la tecla es una trampa.
    """
    cuerpo = _codigo()
    trozo = cuerpo[cuerpo.index("const detectarDistribucion"):]
    trozo = trozo[:trozo.index("const olvidarDistribucion")]
    assert "apilarDistribucion(distAceptada.current)" in trozo, (
        "volver a «Detectar» vuelve a tirar la distribución corregida sin "
        "guardarla: se pierden todas las correcciones y no hay deshacer")


def test_deshacer_tira_lo_dibujado_y_lo_tarifado_con_la_version_vieja():
    """Volver atrás y dejar el alzado y el precio de la versión nueva sería peor
    que no volver: enseñaría un plano que no corresponde a la distribución."""
    cuerpo = _codigo()
    trozo = cuerpo[cuerpo.index("const deshacerDistribucion"):]
    trozo = trozo[:trozo.index("// MUEBLES MV:")]
    assert "alzadoGuardado.current = null" in trozo, (
        "al deshacer se queda el alzado de la versión que acabamos de tirar")
    assert "setRelacionMV(null)" in trozo, (
        "al deshacer se queda la relación MV de la versión que acabamos de tirar")


def test_la_pila_de_deshacer_tiene_tope():
    cuerpo = _codigo()
    assert "pilaDist.current.shift()" in cuerpo, (
        "la pila de deshacer crece sin límite; cada copia lleva todos los módulos "
        "dentro")


# ── Total en euros ───────────────────────────────────────────────────────────
def test_el_total_se_ve_junto_a_la_distribucion():
    cuerpo = _codigo()
    assert "relacionMV?.totalPvp != null &&" in cuerpo, (
        "ya no se enseña el total junto a la distribución: hay que bajar otra vez "
        "hasta la relación MV para saber por dónde va el precio")


def test_el_total_NO_se_pinta_a_quien_no_puede_ver_la_tarifa():
    """El candado del candado (CLAUDE.md, regla 8b).

    Se comprueba `!= null` a propósito: con `!` un total de 0 € tampoco saldría,
    pero lo importante es que a quien no ve precios el servidor le manda `null` y
    aquí no se pinta nada. Si esto pasara a ser `{relacionMV && <span>...}`, se
    pintaría «null €» o peor, y la pantalla se convertiría en la puerta de atrás.
    """
    cuerpo = _codigo()
    i = cuerpo.index("relacionMV?.totalPvp != null &&")
    # El guardia tiene que seguir siendo una comprobación de NULO, no de verdad.
    assert "!= null" in cuerpo[i:i + 60], (
        "el total se pinta sin comprobar que exista: a quien no puede ver la "
        "tarifa MV el servidor le manda `totalPvp` en nulo")


def test_corregir_un_modulo_actualiza_el_total_en_vez_de_cerrarlo():
    cuerpo = _codigo()
    trozo = cuerpo[cuerpo.index("const corregirDistribucion"):]
    trozo = trozo[:trozo.index("const olvidarRelacionMV")] if "const olvidarRelacionMV" in trozo else trozo[:4000]
    assert "if (teniaRelacion) pedirMueblesMV()" in trozo, (
        "al corregir un módulo la relación se cierra y ya no se vuelve a pedir: "
        "para ver el precio otra vez habría que pulsar «Muebles MV» después de "
        "CADA corrección")
