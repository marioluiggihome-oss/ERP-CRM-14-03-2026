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


def _limpio(nombre):
    with open(os.path.join(COMPONENTES, nombre), "r", encoding="utf-8") as f:
        cuerpo = sin_comentarios(f.read())
    assert "const contratoEdicion" in cuerpo, nombre
    return cuerpo


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
        i = cuerpo.index("const contratoEdicion")
        bloque = cuerpo[i:i + 3000]
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
