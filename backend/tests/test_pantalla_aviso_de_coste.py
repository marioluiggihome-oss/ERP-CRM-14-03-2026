# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL RENDER DICE LO QUE VA A COSTAR, Y NO DICE QUÉ IA LO HACE.

Dos reglas, y la segunda es la importante.

1. ANTES DE PULSAR se ve lo que va a gastar. Desde el 25/08 el coste en
   créditos depende del motor —un render del motor Pro cuesta 3,3 veces más—,
   así que pulsabas y te enterabas después.

2. EL AVISO NO PUEDE NOMBRAR NUNCA EL MOTOR. El master, 25/08: «pero que no
   ponga nunca qué IA se usa». Y no es manía: IA 1 es la única que ve un
   usuario que no sea master (CLAUDE.md, regla 1), así que escribir el nombre
   del motor en pantalla sería enseñar por dónde va la casa a quien no tiene
   por qué saberlo. Se dice el NÚMERO y punto.

Y hay una tercera cosa que vigilar, que es de las que se rompen solas: la tabla
de costes está DOS VECES —en la pantalla, para avisar, y en el servidor, para
cobrar—. Si se separan, el aviso dice una cosa y la factura otra. Esta prueba
las compara.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ESTUDIO = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")


def _codigo():
    with open(ESTUDIO, "r", encoding="utf-8") as f:
        return f.read()


def test_se_avisa_del_coste_antes_de_pulsar():
    cuerpo = _codigo()
    assert "creditosDeEstaTanda" in cuerpo, (
        "ya no se calcula lo que va a costar la tanda de renders")
    assert "Vas a gastar" in cuerpo, (
        "ha desaparecido el aviso de coste de debajo del botón de generar")


def test_el_aviso_cuenta_las_variaciones():
    """Tres variaciones son tres renders, y tres veces el coste."""
    cuerpo = _codigo()
    # El aviso sigue contando las variaciones, PERO con plano o bocetos el
    # camino es otro (`handleGenerateComposed`) y ese genera UNA imagen aunque
    # se pidan tres. Si dijera 3 y se cobrara 1, el aviso y el contador
    # volverían a contar cosas distintas — que es lo que esta prueba impide,
    # en los dos sentidos.
    assert ("<AvisoDeCoste n={(floorPlan || wallSketches.length > 0) "
            "? 1 : variantCount} />") in cuerpo, (
        "el aviso del botón de la descripción no cuadra con lo que se cobra: "
        "o no cuenta las variaciones —diría «1 crédito» y gastaría tres— o "
        "las cuenta también con plano/bocetos, donde solo se genera una")
    assert "creditosDeEstaTanda(n)" in cuerpo, (
        "el aviso ya no multiplica por el número de renders de la tanda")


def test_el_aviso_esta_en_LOS_DOS_botones_de_generar():
    """Hay dos caminos hasta el mismo gasto: el de la descripción y el de
    parámetros. Si solo avisara uno, por el otro se gastaría a ciegas — y así
    estuvo la primera versión."""
    cuerpo = _codigo()
    assert cuerpo.count("<AvisoDeCoste") >= 2, (
        f"el aviso de coste solo se pinta {cuerpo.count('<AvisoDeCoste')} vez: "
        "falta en uno de los dos botones de generar")


def test_el_aviso_sale_TAMBIEN_con_cupo_ilimitado():
    """El fallo que hizo que el master no lo viera.

    La primera versión lo escondía con `!aiCredits.ilimitado`, y con eso se
    quedaba sin aviso justo quien más falta le hace: el que paga la factura del
    proveedor. Que no se te acaben los créditos no hace el render gratis.
    """
    cuerpo = _codigo()
    i = cuerpo.index("const AvisoDeCoste")
    trozo = cuerpo[i:i + 1400]
    assert "aiCredits.ilimitado" in trozo and "cupo ilimitado" in trozo, (
        "el aviso ya no dice nada cuando el cupo es ilimitado")
    assert "!aiCredits.ilimitado &&" not in cuerpo, (
        "ha vuelto la condición que esconde el aviso a quien tiene cupo "
        "ilimitado")


def test_el_aviso_NO_dice_nunca_que_ia_se_usa():
    """La regla que pidió el master, y la que hay que vigilar de verdad."""
    cuerpo = _codigo()
    i = cuerpo.index("Vas a gastar")
    # El bloque del aviso: desde el `<p>` que lo envuelve hasta que se cierra.
    ini = cuerpo.rindex("<p", 0, i)
    fin = cuerpo.index("</p>", i)
    aviso = cuerpo[ini:fin]
    prohibido = ("IA 1", "IA 2", "IA 3", "IA 4", "IA 5", "IA 7",
                 "gemini", "banana", "flux", "manus", "motor", "Motor")
    for palabra in prohibido:
        assert palabra not in aviso, (
            f"el aviso de coste nombra «{palabra}». El master, 25/08: «que no ponga "
            "nunca qué IA se usa». Además IA 1 es la única que debe ver un usuario "
            "que no sea master (CLAUDE.md, regla 1): poner el motor en pantalla "
            "enseña por dónde va la casa.")


def test_la_tabla_de_costes_de_la_pantalla_dice_lo_MISMO_que_la_del_servidor():
    """Están en dos sitios porque una avisa y la otra cobra. No pueden separarse."""
    from services.ai_usage import COSTE_POR_MOTOR

    # La tabla salió de dentro de la pantalla el 09/09/2026, al aparecer una
    # SEGUNDA pantalla que renderiza (el clon de pruebas del Estudio 3D). Con
    # una copia en cada una, añadir un motor obligaba a acordarse de tocar las
    # dos, y la que se olvidara avisaría «1 crédito» de un motor que cobra 7.
    compartida = os.path.join(RAIZ, "frontend", "src", "costeDeRender.js")
    with open(compartida, encoding="utf-8") as f:
        cuerpo = f.read()
    linea = re.search(r"export const COSTE_CREDITOS = \{(.*?)\};", cuerpo, re.S)
    assert linea, "ya no está la tabla de costes compartida (costeDeRender.js)"
    pantalla = {}
    for trozo in linea.group(1).split(","):
        if ":" not in trozo:
            continue
        k, v = trozo.split(":", 1)
        pantalla[k.strip().strip("'\"")] = float(v.strip())

    assert pantalla, "la tabla de costes de la pantalla ha quedado vacía"
    for motor, coste in pantalla.items():
        assert motor in COSTE_POR_MOTOR, (
            f"la pantalla conoce el motor «{motor}» y el servidor no")
        assert abs(COSTE_POR_MOTOR[motor] - coste) < 0.001, (
            f"«{motor}» cuesta {coste} en el aviso y {COSTE_POR_MOTOR[motor]} al "
            "cobrar. El aviso diría una cosa y la factura otra.")
    for motor in COSTE_POR_MOTOR:
        assert motor in pantalla, (
            f"el servidor cobra por el motor «{motor}» y la pantalla no sabe "
            "avisarlo: saldría «1 crédito» y se cobraría otra cosa")


def test_se_avisa_cuando_NO_llegan_los_creditos():
    cuerpo = _codigo()
    assert "Te faltan créditos" in cuerpo, (
        "ya no se avisa de que la tanda no cabe en los créditos que quedan: se "
        "pulsaría para nada")


def test_las_dos_pantallas_usan_la_TABLA_COMPARTIDA_y_no_una_copia():
    """Un fichero compartido que nadie importa no protege de nada.

    La prueba de arriba compara `costeDeRender.js` con el servidor. Si una
    pantalla se dejara su propia tabla dentro, esa comparación seguiría en
    verde y la pantalla seguiría avisando con números viejos."""
    for nombre in ("AIRenderStudio.jsx", "Estudio3DLab.jsx"):
        ruta = os.path.join(RAIZ, "frontend", "src", "components", nombre)
        if not os.path.exists(ruta):
            continue
        with open(ruta, encoding="utf-8") as f:
            pantalla = f.read()
        assert "from '../costeDeRender'" in pantalla, (
            f"{nombre} ya no usa la tabla de costes compartida")
        assert "const COSTE_CREDITOS = {" not in pantalla, (
            f"{nombre} ha vuelto a tener su propia tabla de costes dentro: se "
            f"separará de la del servidor y avisará de un precio que no es")
