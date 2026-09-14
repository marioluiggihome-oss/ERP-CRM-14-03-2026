# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
SIN SELLO DE VERSIÓN, «¿ESTÁ DESPLEGADO O ES MI TABLET?» NO SE PUEDE CONTESTAR.

El master, 14/09/2026: «no veo nada de las funciones nuevas en la tablet de 8,6
pulgadas». Y no había forma de saberlo mirando la pantalla: la marca de la
esquina ponía «ERP v4.1» ESCRITA A MANO, así que enseñaba lo mismo en un
despliegue de hoy que en uno de hace tres meses. `APP_VERSION` estaba declarada
en `App.js` y no la leía nadie.

O sea que un aparato con el paquete viejo en la caché y otro recién actualizado
se veían EXACTAMENTE igual. Con un sello de compilación, la pregunta se
contesta en un segundo: se mira la esquina y se compara.

LO QUE DE VERDAD VIGILA ESTE CANDADO, y por lo que existe: que el sello se
SUSTITUYA al compilar. El primer intento ponía `process.env.REACT_APP_BUILD`
desde `craco.config.js`, y eso NO funciona —react-scripts ya ha leído las
variables— pero tampoco da error: el paquete salía con el nombre de la variable
sin sustituir y en pantalla habría puesto «dev» en producción. Un sello que
miente sobre la versión es peor que no tener sello, porque se usa para decidir
si hay que recargar.
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
FRONT = os.path.join(RAIZ, "frontend")
CRACO = os.path.join(FRONT, "craco.config.js")
APP = os.path.join(FRONT, "src", "App.js")


def _app():
    with open(APP, "r", encoding="utf-8") as f:
        cuerpo = sin_comentarios(f.read())
    assert "APP_BUILD" in cuerpo, "el recorte de comentarios se ha comido el código"
    return cuerpo


def test_EL_SELLO_SE_SUSTITUYE_DE_VERDAD_AL_COMPILAR():
    """ESTE es el fallo que se coló y se cazó mirando el paquete compilado.

    Se EJECUTA la configuración en node y se mira el valor que el plugin va a
    inyectar. Leer el fichero y ver que pone «REACT_APP_BUILD» pasaría en verde
    con las dos versiones, la que funciona y la que no.
    """
    node = shutil.which("node")
    if not node:
        pytest.skip("no hay node en esta máquina")
    guion = (
        "const cfg = require(%s);\n"
        "const plugins = (cfg.webpack && cfg.webpack.plugins && cfg.webpack.plugins.add) || [];\n"
        "let valor = null;\n"
        "for (const p of plugins) {\n"
        "  const d = p && p.definitions;\n"
        "  if (d && d['process.env.REACT_APP_BUILD'] !== undefined) valor = d['process.env.REACT_APP_BUILD'];\n"
        "}\n"
        "console.log(JSON.stringify({ valor }));\n" % json.dumps(CRACO)
    )
    r = subprocess.run([node, "-e", guion], capture_output=True, text=True,
                       timeout=90, cwd=FRONT)
    assert r.returncode == 0, r.stderr
    valor = json.loads(r.stdout)["valor"]
    assert valor, (
        "la compilación no inyecta ningún sello de versión: el paquete saldría "
        "con «REACT_APP_BUILD» sin sustituir y la pantalla pondría «dev» en "
        "producción")
    # Es una cadena JSON ya serializada: tiene que traer una fecha de verdad.
    assert re.search(r"\d{2}/\d{2} \d{2}:\d{2}", valor), (
        "el sello no lleva fecha y hora: %s. Sin fecha no se puede comparar "
        "qué aparato tiene qué versión" % valor)


def test_EL_SELLO_NO_DEPENDE_DE_QUE_HAYA_GIT():
    """En Railway la copia puede venir sin `.git`. Una marca que solo funciona
    a veces no sirve para comprobar nada."""
    with open(CRACO, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    i = cuerpo.index("const sello")
    bloque = cuerpo[i:cuerpo.index("module.exports", i)]
    assert "catch" in bloque, (
        "el sello revienta si no hay git en el contenedor de compilación")
    assert "getHours" in bloque or "toISOString" in bloque, (
        "el sello no tiene una parte que funcione siempre (la fecha)")


def test_LA_PANTALLA_ENSENA_EL_SELLO():
    """Un sello que no se ve no lo puede mirar nadie."""
    cuerpo = _app()
    assert "const APP_BUILD = process.env.REACT_APP_BUILD" in cuerpo
    assert "{APP_BUILD}" in cuerpo, (
        "el sello ya no se pinta en pantalla: vuelve a no haber forma de saber "
        "qué versión tiene un aparato")


def test_NO_QUEDA_UNA_VERSION_ESCRITA_A_MANO_AL_LADO():
    """Dos marcas de versión, una fija y otra real, y la que se lee es la que
    miente. Era justo el caso: «ERP v4.1» llevaba meses igual."""
    cuerpo = _app()
    i = cuerpo.index("{APP_BUILD}")
    bloque = cuerpo[max(0, i - 700):i + 100]
    assert not re.search(r"v4\.\d", bloque), (
        "vuelve a haber una versión escrita a mano junto al sello: %s"
        % re.search(r"v4\.\d", bloque).group(0))
