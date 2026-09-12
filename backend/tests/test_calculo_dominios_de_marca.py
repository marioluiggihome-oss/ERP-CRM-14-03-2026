# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
UN DOMINIO DE MARCA QUE LA PANTALLA CONOCE Y EL SERVIDOR NO: LOGIN MUERTO.

El master, 12/09/2026: «necesito una web conectada a studio3k.io, que es mi
dominio... necesito la URL de acceso, que nada tenga que ver con el dominio
luiggihome».

Al mirarlo estaba casi todo montado: `platformEntry.js` reconoce
`studio3k.io` y `estudio3k.io` por el nombre del dominio desde hace tiempo, la
landing y el login tienen su marca, y `entrada_permitida` deja pasar al master
por cualquier puerta. Lo que NO estaba era el dominio en los orígenes de CORS
del servidor: allí solo se habían añadido a mano los de carpinter.io.

QUÉ PASA ENTONCES, y por eso esto es un candado y no una nota: el día que se
apunte el DNS, la web de studio3k.io CARGA —es un fichero estático, el
navegador no pregunta a nadie—, se ve con su logotipo… y la primera llamada a
la API la corta el navegador. No sale un error legible: sale un login que no
hace nada, y el motivo escondido en la consola. Desde fuera parece que «la web
no funciona» y no hay forma de saber por qué.

Es el fallo de siempre en este repo: un arreglo aplicado a una marca y no a la
otra (regla 1, el `editingRender`). La forma de que no vuelva no es acordarse:
es que las dos listas no se puedan separar.

CÓMO SE COMPRUEBA: EJECUTANDO las dos. El detector de marca se corre EN NODE
—es JavaScript, y reescribirlo en Python protegería la copia, no el original
(reglas 31 y 34)—, y la lista de CORS se saca ejecutando el trozo REAL de
`server.py`, no copiándolo aquí.
"""
import json
import os
import re
import shutil
import subprocess

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER = os.path.join(RAIZ, "backend", "server.py")
ENTRY = os.path.join(RAIZ, "frontend", "src", "platformEntry.js")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _origenes_de_cors(entorno=None):
    """La lista REAL, ejecutando el trozo de `server.py` que la construye.

    No se copia el cálculo: se recorta desde `_cors_env = ` hasta el final del
    bucle que añade los dominios de marca y se ejecuta tal cual. Si alguien
    cambia cómo se arma, esta prueba cambia con él en vez de quedarse
    protegiendo una versión que ya no existe.
    """
    cuerpo = _lee(SERVER)
    ini = cuerpo.index("_cors_env = os.environ.get('CORS_ORIGINS'")
    fin = cuerpo.index("app.add_middleware(", ini)
    trozo = cuerpo[ini:fin]
    assert "_cors_origins" in trozo and "for " in trozo, (
        "el trozo recortado no arma la lista de CORS; ha cambiado la forma de "
        "escribirla y hay que revisar este candado")
    ambito = {"os": os}
    if entorno is not None:
        ambito["os"] = type("_os", (), {"environ": entorno})()
    exec(compile(trozo, SERVER, "exec"), ambito)
    return ambito["_cors_origins"]


def _dominios_que_reconoce_la_pantalla():
    """Los que el detector compara contra el `hostname`, sacados del JS."""
    fuente = _lee(ENTRY)
    return sorted(set(re.findall(r"host\.includes\('([^']+)'\)", fuente)))


def test_TODO_DOMINIO_QUE_LA_PANTALLA_RECONOCE_ESTA_EN_CORS():
    """ESTE es el fallo: studio3k.io lo reconocía la pantalla y no el servidor."""
    origenes = _origenes_de_cors()
    faltan = []
    for dominio in _dominios_que_reconoce_la_pantalla():
        for origen in ("https://%s" % dominio, "https://www.%s" % dominio):
            if origen not in origenes:
                faltan.append(origen)
    assert not faltan, (
        "la pantalla deja entrar por estos dominios y el servidor no los acepta: "
        "%s. La web cargaría con su marca y el login no haría nada, con el "
        "motivo escondido en la consola del navegador." % faltan)


def test_STUDIO3K_ENTRA_POR_SU_DOMINIO_Y_NO_POR_EL_DE_LUIGGI():
    """Se ejecuta el detector de verdad, en node, con el dominio en la mano."""
    node = shutil.which("node")
    if not node:
        pytest.skip("no hay node en esta máquina")
    fuente = _lee(ENTRY).replace("export ", "")
    casos = {
        "studio3k.io": "studio3k",
        "www.studio3k.io": "studio3k",
        "estudio3k.io": "studio3k",
        "carpinter.io": "carpinter",
        "erp.luiggihome.es": "",
        "localhost": "",
    }
    guion = (fuente + "\nconst out={};\n"
             "for (const h of %s) {\n"
             "  const e = detectPlatformEntry({hostname:h, pathname:'/', search:''});\n"
             "  out[h] = e ? e.key : '';\n}\n"
             "console.log(JSON.stringify(out));\n" % json.dumps(list(casos)))
    r = subprocess.run([node, "-e", guion], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout) == casos, (
        "el detector de marca ya no resuelve los dominios igual: %s" % r.stdout)


def test_EL_DOMINIO_DEL_ERP_NO_DEJA_DE_ESTAR_PERMITIDO():
    """Añadir marcas no puede dejar fuera la intranet de siempre: sería tumbar
    el ERP entero por publicar una web."""
    origenes = _origenes_de_cors()
    assert "https://erp.luiggihome.es" in origenes


def test_LA_VARIABLE_DE_ENTORNO_NO_PUEDE_BORRAR_LAS_MARCAS():
    """En producción `CORS_ORIGINS` viene fijada y no lleva los dominios de
    marca: si estos se añadieran solo cuando la variable no existe, funcionaría
    en local y estaría roto justo en Railway, que es donde importa."""
    origenes = _origenes_de_cors({"CORS_ORIGINS": "https://erp.luiggihome.es"})
    assert "https://studio3k.io" in origenes
    assert "https://carpinter.io" in origenes
    assert "https://erp.luiggihome.es" in origenes


def test_NO_SE_ABRE_A_CUALQUIERA():
    """Lo contrario también importa: CORS con `*` y credenciales deja que
    cualquier web haga peticiones con la sesión del usuario."""
    cuerpo = _lee(SERVER)
    i = cuerpo.index("allow_origins=_cors_origins")
    trozo = cuerpo[i - 400:i + 200]
    assert "allow_origins=['*']" not in trozo and 'allow_origins=["*"]' not in trozo
    origenes = _origenes_de_cors()
    assert "*" not in origenes
    for o in origenes:
        assert o.startswith("https://") or o.startswith("http://localhost"), o
