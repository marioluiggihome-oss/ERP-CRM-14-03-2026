# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL ESCALÓN DE LA TARIFA Y LA MEDIDA DE VERDAD SON DOS COSAS DISTINTAS.

El master, 28/08: «aunque pongas hasta 70 o hasta 90, esas medidas las puedo
modificar para que queden grabadas las medidas definitivas», y «en los costados
bajos y altos también se debe poder cambiar la medida, tanto de ancho como de
alto, en todos».

    · El ESCALÓN («hasta 70», «hasta 90») decide lo que CUESTA la pieza.
    · El ancho y el alto reales son lo que se FABRICA y lo que va al pedido.

LO QUE VIGILA ESTE CANDADO: que escribir la medida definitiva NO toque el
precio. Si al corregir el alto de un costado se moviera el pvp, el presupuesto
cambiaría solo mientras alguien ajusta cotas — y nadie lo relacionaría con eso.
Si la pieza se sale del escalón, el escalón se cambia a mano al lado, que es una
decisión y no un efecto secundario.

Y la otra mitad: que las medidas VIAJEN. Grabarlas y que se queden en la
pantalla no sirve de nada; tienen que llegar al pedido, que es lo que se
fabrica.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSX = os.path.join(RAIZ, "frontend", "src", "components", "CocinaMontada3.jsx")


def _lee():
    with open(JSX, "r", encoding="utf-8") as f:
        return f.read()


def _cuerpo_de(nombre, cuerpo):
    """El cuerpo de esa función y NADA MÁS.

    La primera versión cortaba a 500 caracteres a ojo y se llevaba por delante
    la función de al lado —`setAnchoTarifa`, que SÍ toca el pvp a propósito—,
    así que la prueba fallaba por el código equivocado. Un candado que lee de
    más acusa a quien no es.
    """
    i = cuerpo.index(f"const {nombre} = ")
    fin = cuerpo.index("}));", i) + 4
    return cuerpo[i:fin]


def test_la_MEDIDA_DEFINITIVA_no_toca_el_precio():
    """`setMedidaReal` no puede escribir `pvp`, ni llamar al cálculo de puntos.

    Compárese con `setAlto`, que SÍ lo hace a propósito: ahí el alto es el que
    manda en la tarifa. En un costado no: su precio lo fija el escalón.
    """
    cuerpo = _lee()
    assert "const setMedidaReal" in cuerpo, (
        "ya no existe `setMedidaReal`: las medidas definitivas no se pueden "
        "escribir")
    fn = _cuerpo_de("setMedidaReal", cuerpo)
    assert "pvp" not in fn, (
        f"escribir la medida definitiva está tocando el precio: {fn[:200]}")
    assert "puntos" not in fn.lower(), (
        "la medida definitiva está entrando en el cálculo de puntos")


def test_se_puede_escribir_ANCHO_Y_ALTO_en_costados_y_laterales():
    """«En todos», dijo el master. Antes el alto de un costado era un guion
    fijo: no había forma de dejar grabada la medida real."""
    cuerpo = _lee()
    for campo in ("anchoReal", "altoReal"):
        assert f"setMedidaReal(m._k, '{campo}'" in cuerpo, (
            f"no se puede escribir «{campo}» en ninguna vista")
    # Y el alto ha dejado de ser un guion inamovible en la tabla.
    assert not re.search(r"opcionesAnc \? \(\s*/\*[^*]*\*/\s*<span className=\"text-slate-400\">—</span>",
                         cuerpo), (
        "el alto de los costados sigue pintado como un guion fijo")


def test_el_ESCALON_de_precio_sigue_estando_y_se_distingue():
    """No se sustituye una cosa por la otra: el escalón tiene que seguir ahí, y
    tiene que verse que es el del precio."""
    cuerpo = _lee()
    assert "hasta {a} cm" in cuerpo, "ha desaparecido el escalón de la tarifa"
    assert "setAnchoTarifa" in cuerpo
    assert "decide el PRECIO" in cuerpo, (
        "nada distingue el escalón de la medida real: quien lo use pensará que "
        "son lo mismo y corregirá el precio sin querer")


def test_las_medidas_VIAJAN_AL_PEDIDO():
    """Grabarlas y que se queden en la pantalla no sirve de nada: son lo que se
    fabrica."""
    cuerpo = _lee()
    i = cuerpo.index("const pasarAPedido")
    trozo = cuerpo[i:cuerpo.index("finally", i)]
    assert "anchoReal" in trozo and "altoReal" in trozo, (
        "las medidas definitivas no llegan al pedido: se quedan en la pantalla")
