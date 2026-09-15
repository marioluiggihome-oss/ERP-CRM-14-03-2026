# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
«PON ESTE GRIFO» ESTABA PROHIBIDO, Y EL AVISO CULPABA AL QUE ESCRIBÍA.

El master, 14/09/2026, con la foto de un grifo adjunta y escrito «pon este
grifo»:

    Error: La instrucción no identifica con suficiente precisión qué propiedad
    y qué zona deben cambiar. No se aplicó ningún cambio.

`contratoEdicion` existe por un buen motivo: sin él, una orden vaga («hazlo
bonito») deja que el modelo rediseñe la cocina entera y se lleve por delante
todo lo ya aprobado. Lo que estaba mal era CÓMO decidía.

FALLO 1 — EL VOCABULARIO SE QUEDABA CORTO. La lista de palabras que valen tenía
tiradores, puertas, encimera, electrodomésticos… y NO tenía el grifo. Tampoco
el fregadero, la placa, el zócalo, el copete, la isla ni el salpicadero: media
cocina. Y el aviso no decía «no conozco esa palabra», decía que la orden no era
lo bastante precisa — así que se reescribe la frase tres veces y sigue sin
funcionar, porque el problema no era la precisión.

FALLO 2, Y ES EL GRAVE — LA IMAGEN ADJUNTA NO CONTABA SI ADEMÁS ESCRIBÍAS. La
rama que acepta una referencia adicional solo entraba con el texto VACÍO
(`!texto && editRefImage`). O sea que adjuntar la foto del grifo y ESCRIBIR
«pon este grifo» funcionaba PEOR que adjuntarla y callarse: el texto caía al
filtro de vocabulario y bloqueaba el cambio. Justo al revés de como se usa —
la imagen es lo que se pide y las palabras solo afinan dónde va.

CÓMO SE COMPRUEBA: EJECUTANDO el filtro en node contra frases de verdad, no
mirando si la palabra «grifo» está escrita en el fichero — que lo está, en este
mismo comentario y en el texto del aviso. Es la trampa de siempre (reglas 24,
34 y 35).

LAS DOS PANTALLAS: el Estudio 3D y su clon (regla 1).
"""
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsx_limpio import sin_comentarios  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMPONENTES = os.path.join(RAIZ, "frontend", "src", "components")
PANTALLAS = ("AIRenderStudio.jsx", "Estudio3DLab.jsx")

# Lo que un diseñador de cocinas escribe de verdad, y tiene que pasar.
ORDENES_REALES = [
    "pon este grifo", "cambia el grifo por uno negro", "cambia el fregadero",
    "quita el zócalo", "pon una isla", "cambia la placa de inducción",
    "pon taburetes en la barra", "cambia el salpicadero", "quita el altillo",
    "pon el copete a juego", "cambia los tiradores de los bajos",
    "cambia la campana", "pon una columna de horno",
]
# Lo que el filtro existe para parar: sin propiedad no hay contrato, y el
# modelo rediseñaría la cocina entera.
ORDENES_VAGAS = ["hazlo bonito", "mejóralo", "más profesional", "cámbialo"]

# ── Y LA PANTALLA NO SOLO DISEÑA COCINAS ────────────────────────────────────
#
# El master, 15/09/2026, con un armario en pantalla:
#
#     DENTRO DEL ARMARIO PON SÓLO ROPA PARA MUJER, CAMBIALA
#     «OJO LE PIDO ESTA INSTRUCCIÓN Y NO LA APLICA»
#
# `ESTUDIO_3D_TIPOS` dice desde el primer día que aquí se diseñan COCINA,
# ARMARIO/VESTIDOR, BAÑO y otro mueble a medida. `tienePropiedad` solo hablaba
# COCINA: ni «armario» ni «ropa» estaban en la lista, así que la orden ni salía
# del navegador — no es que el motor la ignorara, es que nunca le llegó.
#
# LO QUE MÁS DESPISTA es que no parece un bloqueo: el render se queda como
# estaba, igual que cuando el motor obedece un contrato que prohíbe lo que le
# pides (el caso de mover un módulo). Dos causas distintas, la misma pantalla.
ORDENES_DE_ARMARIO = [
    # La del master, literal.
    "dentro del armario pon sólo ropa para mujer, cambiala",
    "cambia la ropa del armario", "pon perchas de madera",
    "quita el zapatero", "pon una cajonera abajo",
    "cambia las baldas del vestidor", "pon cajas en el altillo",
    "más barras de colgar", "pon bolsos en la balda de arriba",
]
ORDENES_DE_BANO = [
    "cambia el lavabo", "pon una mampara de cristal", "quita el bidé",
    "cambia el espejo por uno redondo", "pon toallas en el toallero",
    "cambia el plato de ducha",
]
# EL ATREZO TAMBIÉN SE PIDE, y es una orden LOCALIZADA: cambiar la planta no es
# rediseñar la cocina. Sin estas palabras, el caso del master seguiría
# bloqueado aunque «armario» sí estuviera — su orden habla de ROPA.
ORDENES_DE_ATREZO = [
    "quita la planta", "cambia la alfombra", "pon un cuadro en la pared",
    "quita los cojines", "cambia las cortinas", "pon un jarrón en la repisa",
]


def _limpio(nombre):
    with open(os.path.join(COMPONENTES, nombre), "r", encoding="utf-8") as f:
        cuerpo = sin_comentarios(f.read())
    assert "const contratoEdicion" in cuerpo, nombre
    return cuerpo


def _bloque_del_contrato(cuerpo):
    """El cuerpo de `contratoEdicion`, medido por la función siguiente."""
    i = cuerpo.index("const contratoEdicion")
    j = cuerpo.index("const colorVariant", i)
    bloque = cuerpo[i:j]
    assert "return {" in bloque, "el recorte se ha comido el cuerpo del contrato"
    return bloque


def _lista_de_tipos(cuerpo):
    """Solo `ESTUDIO_3D_TIPOS`, no las otras listas con `id` del fichero."""
    i = cuerpo.index("const ESTUDIO_3D_TIPOS = [")
    j = cuerpo.index("];", i)
    return cuerpo[i:j]


def _regex_de_propiedad(nombre):
    cuerpo = _limpio(nombre)
    m = re.search(r"const tienePropiedad = (/\(.+?\)/)\.test\(texto\)", cuerpo)
    assert m, "%s ya no decide por `tienePropiedad`" % nombre
    return m.group(1)


def _corre_en_node(nombre, frases):
    node = shutil.which("node")
    if not node:
        pytest.skip("no hay node en esta máquina")
    guion = ("const re = %s;\nconst out = {};\n"
             "for (const f of %s) out[f] = re.test(f.toLowerCase());\n"
             "console.log(JSON.stringify(out));\n"
             % (_regex_de_propiedad(nombre), json.dumps(frases)))
    r = subprocess.run([node, "-e", guion], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_EL_GRIFO_Y_MEDIA_COCINA_MAS_DEJAN_DE_ESTAR_PROHIBIDOS():
    """ESTE es el fallo que vio el master, con su frase exacta la primera."""
    for pantalla in PANTALLAS:
        res = _corre_en_node(pantalla, ORDENES_REALES)
        bloqueadas = [f for f, ok in res.items() if not ok]
        assert not bloqueadas, (
            "%s sigue bloqueando órdenes corrientes de cocina: %s"
            % (pantalla, bloqueadas))


def test_UN_ARMARIO_NO_ES_UNA_COCINA_Y_TAMBIEN_SE_EDITA():
    """La frase del master, literal, la primera de la lista."""
    for pantalla in PANTALLAS:
        res = _corre_en_node(pantalla, ORDENES_DE_ARMARIO)
        bloqueadas = [f for f, ok in res.items() if not ok]
        assert not bloqueadas, (
            "%s bloquea órdenes corrientes de armario o vestidor: %s"
            % (pantalla, bloqueadas))


# CADA PALABRA TIENE QUE VALER POR SÍ SOLA.
#
# Las listas de frases de arriba NO probaban eso, y las mutaciones lo
# destaparon: quitar «armario» del filtro las dejaba a TODAS en verde, porque
# cada frase traía además «ropa», «percha» o «balda», que siguen en la lista. Y
# quitar «ropa» tampoco fallaba, por lo mismo al revés. O sea que se podía
# borrar justo la palabra del caso del master y el candado no se enteraba.
#
# Estas sondas llevan UNA sola palabra del vocabulario cada una. Si se cae
# cualquiera, se ve qué falta y no «alguna de estas nueve frases».
SONDAS = [
    # armario / vestidor
    "armario", "vestidor", "ropero", "zapatero", "perchero", "percha",
    "colgador", "pantalonero", "cajonera", "maletero",
    # baño
    "lavabo", "inodoro", "ducha", "bañera", "bidé", "mampara", "toallero",
    "espejo",
    # atrezo
    "ropa", "prenda", "camisa", "vestido", "chaqueta", "zapatos", "bolso",
    "toalla", "almohada", "cesta", "caja", "maleta", "cojín", "manta",
    "alfombra", "cortina", "planta", "maceta", "cuadro", "jarrón", "libro",
    "butaca", "silla", "mesa", "cama",
]


def test_CADA_PALABRA_NUEVA_VALE_POR_SI_SOLA():
    """Una sonda por palabra: «cambia el <palabra>» y nada más.

    `cambia` no está en el vocabulario —vive en el filtro de mover, que es
    otro—, así que lo único que puede hacer pasar cada sonda es su palabra.
    """
    frases = ["cambia el %s" % w for w in SONDAS]
    for pantalla in PANTALLAS:
        res = _corre_en_node(pantalla, frases)
        faltan = sorted(f.replace("cambia el ", "") for f, ok in res.items() if not ok)
        assert not faltan, (
            "%s no reconoce estas palabras, y cada una es una orden que el "
            "usuario escribe y que se quedaría bloqueada sin decir por qué: %s"
            % (pantalla, faltan))


def test_LA_FRASE_DEL_MASTER_NO_DEPENDE_DE_UNA_SOLA_PALABRA():
    """«Armario» y «ropa» tienen que valer las DOS, por separado.

    Su orden trae las dos, así que basta una para que pase — y por eso el
    candado no notaba que faltara la otra. Se comprueban sueltas.
    """
    for pantalla in PANTALLAS:
        res = _corre_en_node(pantalla, ["cambia el armario", "cambia la ropa"])
        faltan = [f for f, ok in res.items() if not ok]
        assert not faltan, (
            "%s se apoya en una sola de las dos palabras del caso del master: %s"
            % (pantalla, faltan))


def test_UN_BANO_TAMPOCO_ES_UNA_COCINA():
    """`ESTUDIO_3D_TIPOS` lleva el baño desde el principio; el filtro no."""
    for pantalla in PANTALLAS:
        res = _corre_en_node(pantalla, ORDENES_DE_BANO)
        bloqueadas = [f for f, ok in res.items() if not ok]
        assert not bloqueadas, (
            "%s bloquea órdenes corrientes de baño: %s" % (pantalla, bloqueadas))


def test_EL_ATREZO_SE_PUEDE_CAMBIAR_SIN_REDISENARLO_TODO():
    """Lo que se ve dentro y alrededor es lo que mira el cliente."""
    for pantalla in PANTALLAS:
        res = _corre_en_node(pantalla, ORDENES_DE_ATREZO)
        bloqueadas = [f for f, ok in res.items() if not ok]
        assert not bloqueadas, (
            "%s bloquea cambiar el atrezo del render: %s" % (pantalla, bloqueadas))


def test_EL_FILTRO_CONOCE_LOS_CUATRO_TIPOS_QUE_LA_PANTALLA_DISEÑA():
    """El candado que impide que esto vuelva a pasar con el tipo siguiente.

    No comprueba palabras sueltas: le pide a la lista de tipos del propio
    fichero (`ESTUDIO_3D_TIPOS`) cuáles son, y exige que el filtro reconozca
    una orden de cada uno. Si mañana se añade un quinto tipo y nadie toca el
    vocabulario, esto se pone rojo ANTES de que el master se encuentre otra
    pantalla que se queda quieta sin decir por qué.
    """
    ejemplo = {
        "cocina": "cambia la encimera",
        "armario": "cambia la ropa del armario",
        "bano": "cambia el lavabo",
        "otro": "cambia las baldas de la estantería",
    }
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        # SOLO LA LISTA DE TIPOS. Buscar `{ id: '...' }` en el fichero entero
        # recogía los estilos, las cámaras, los electrodomésticos y los
        # colores —cincuenta «tipos» que no lo son—, y el candado fallaba por
        # el motivo equivocado.
        tipos = re.findall(r"\{ id: '([a-z]+)',", _lista_de_tipos(cuerpo))
        assert "armario" in tipos and "bano" in tipos, (
            "%s ya no declara los tipos como se esperaba: %s" % (pantalla, tipos))
        faltan = [t for t in tipos if t not in ejemplo]
        assert not faltan, (
            "%s diseña tipos nuevos (%s) y este candado no sabe qué orden "
            "probarles: añade un ejemplo antes de darlos por buenos"
            % (pantalla, faltan))
        res = _corre_en_node(pantalla, [ejemplo[t] for t in tipos])
        mudos = [f for f, ok in res.items() if not ok]
        assert not mudos, (
            "%s declara diseñar %s pero el filtro de edición no entiende: %s"
            % (pantalla, tipos, mudos))


def test_UNA_ORDEN_VAGA_SIGUE_SIN_PASAR():
    """El filtro no se abre del todo: sin decir QUÉ se cambia, el modelo
    rediseña la cocina y se lleva por delante lo ya aprobado."""
    for pantalla in PANTALLAS:
        res = _corre_en_node(pantalla, ORDENES_VAGAS)
        coladas = [f for f, ok in res.items() if ok]
        assert not coladas, (
            "%s deja pasar órdenes sin propiedad: %s" % (pantalla, coladas))


def test_UNA_IMAGEN_ADJUNTA_NUNCA_SE_BLOQUEA_POR_EL_TEXTO():
    """FALLO 2: la rama de la referencia solo entraba con el texto VACÍO, así
    que adjuntar la foto Y escribir era peor que adjuntarla y callarse."""
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        assert "if (!texto && editRefImage) {" not in cuerpo, (
            "%s vuelve a exigir que el texto esté vacío para aceptar la imagen "
            "adjunta: escribir lo que se quiere hace que se bloquee" % pantalla)
        # LA VENTANA SE MIDE POR LA FUNCIÓN, NO POR UN NÚMERO. Antes eran
        # 3.000 caracteres a bulto, y al ampliar el vocabulario a armarios y
        # baños el filtro creció y `if (!tienePropiedad)` se salió de la
        # ventana: el candado reventó por un cambio HONRADO, que es la forma
        # más rápida de que alguien lo borre para seguir trabajando.
        bloque = _bloque_del_contrato(cuerpo)
        pos_img = bloque.index("if (editRefImage) {")
        pos_bloqueo = bloque.index("if (!tienePropiedad) {")
        assert pos_img < pos_bloqueo, (
            "%s comprueba el vocabulario ANTES que la imagen adjunta: con foto "
            "y texto, el texto vuelve a mandar" % pantalla)


def test_EL_TEXTO_NO_SE_TIRA_CUANDO_HAY_IMAGEN():
    """«Pon este grifo EN EL FREGADERO DE LA ISLA» dice dónde. Quedarse solo
    con la foto pierde esa precisión."""
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        i = cuerpo.index("if (editRefImage) {")
        bloque = cuerpo[i:i + 700]
        assert "objetivo: texto" in bloque, (
            "%s descarta lo que el usuario ha escrito cuando adjunta una foto"
            % pantalla)


# ── Mover un módulo ES cambiar la distribución ───────────────────────────────

ORDENES_DE_MOVER = [
    "cambiar la posición de la columna horno micro vinoteca y ponerla más a la izquierda",
    "mueve la columna a la izquierda",
    "desplaza el frigorífico al otro lado",
    "intercambia el horno y la vinoteca",
    "cambia de sitio la campana",
    "pon la columna junto a la ventana",
]
ORDENES_QUE_NO_MUEVEN = [
    "cambia el color de los frentes", "pon este grifo", "quita el zócalo",
    "cambia los tiradores de los bajos",
]


def _regex_de_mover(nombre):
    cuerpo = _limpio(nombre)
    m = re.search(r"const esMover = (/\(.+?\)/)\.test\(texto\)", cuerpo)
    assert m, "%s ya no reconoce las órdenes de mover" % nombre
    return m.group(1)


def _corre_mover(nombre, frases):
    node = shutil.which("node")
    if not node:
        pytest.skip("no hay node en esta máquina")
    guion = ("const re = %s;\nconst out = {};\n"
             "for (const f of %s) out[f] = re.test(f.toLowerCase());\n"
             "console.log(JSON.stringify(out));\n"
             % (_regex_de_mover(nombre), json.dumps(frases)))
    r = subprocess.run([node, "-e", guion], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_MOVER_UN_MODULO_SE_RECONOCE_COMO_TAL():
    """Master, 14/09: «necesito cambiar la posición de la columna
    horno/micro/vinoteca y ponerla más a la izquierda, pero no lo hace»."""
    for pantalla in PANTALLAS:
        res = _corre_mover(pantalla, ORDENES_DE_MOVER)
        sin_detectar = [f for f, ok in res.items() if not ok]
        assert not sin_detectar, (
            "%s no reconoce estas órdenes como un cambio de posición: %s"
            % (pantalla, sin_detectar))


def test_UN_CAMBIO_DE_COLOR_NO_SE_TOMA_POR_UNA_MUDANZA():
    """Al revés también cuenta: si cualquier orden pasara por «mover», el
    contrato dejaría de proteger la distribución en todas."""
    for pantalla in PANTALLAS:
        res = _corre_mover(pantalla, ORDENES_QUE_NO_MUEVEN)
        coladas = [f for f, ok in res.items() if ok]
        assert not coladas, (
            "%s toma por mudanza órdenes que no lo son: %s" % (pantalla, coladas))


def test_EL_CONTRATO_DE_MOVER_NO_PROHIBE_MOVER():
    """ESTE es el fallo. El contrato genérico manda al motor «Debe
    conservarse: distribución, módulos», y el motor obedece: la orden pedía
    mover y el contrato lo prohibía. No fallaba nada — el render volvía igual,
    que es lo que más desconcierta, y cada reintento gasta un crédito."""
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        i = cuerpo.index("alcance: 'mover_modulo'")
        contrato = cuerpo[i:cuerpo.index("contexto_aprobado", i)]
        assert "distribución, módulos" not in contrato, (
            "%s vuelve a exigir conservar la distribución en una orden que "
            "pide justo cambiarla: el motor no moverá nada" % pantalla)
        # Y lo que SÍ tiene que quedarse clavado.
        for debe in ("mismo ancho", "no cambian de tipo", "cámara"):
            assert debe in contrato, (
                "%s ya no protege «%s» al mover: una mudanza acabaría siendo "
                "una cocina nueva" % (pantalla, debe))


def test_MOVER_SE_DECIDE_ANTES_QUE_EL_CONTRATO_GENERICO():
    """Si el genérico ganara, seguiría mandando «conservar distribución»."""
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        i = cuerpo.index("const contratoEdicion")
        bloque = cuerpo[i:i + 6000]
        assert bloque.index("if (esMover) {") < bloque.index("alcance: 'solo_lo_solicitado'"), (
            "%s evalúa el contrato genérico antes que el de mover" % pantalla)


def test_EL_AVISO_DICE_QUE_HACE_FALTA_Y_NO_SOLO_QUE_NO_VALE():
    """«No identifica con suficiente precisión» no se puede arreglar: no dice
    qué falta."""
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        assert "no identifica con suficiente precisión" not in cuerpo, (
            "%s vuelve al aviso que culpa al que escribe sin decirle qué hacer"
            % pantalla)
        i = cuerpo.index("setError('Di QUÉ hay que cambiar")
        aviso = cuerpo[i:i + 400]
        assert "«" in aviso, "%s ya no da ejemplos" % pantalla
        assert "foto" in aviso, (
            "%s no dice que adjuntar una foto también vale, que es la salida "
            "más rápida" % pantalla)
