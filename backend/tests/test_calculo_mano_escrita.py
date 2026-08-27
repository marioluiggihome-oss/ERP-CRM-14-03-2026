# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LA MANO QUE SE ESCRIBE ES LA QUE SE PONE.

El master, 25/08/2026, con una captura: pega `10 A60I` en Pegado Masivo y el
mueble sale como `A60D/I` con «⚠️ Sin mano». «No coge las manos, cuando sí
debería ponerlas si están escritas.»

DÓNDE ESTABA EL FALLO, que no era donde parecía. El parser del servidor lee bien
la mano: `10 A60I` devuelve `mano='I'`. Lo que devuelve además es el código de
CATÁLOGO —`A60D/I`, que es como se llama en la tarifa MV el alto de una puerta,
con las dos manos posibles—. Y la pantalla saca la mano del CÓDIGO, no del campo
`mano`. Como el código decía `D/I` («sin decidir»), la I escrita por el master
llegaba al navegador y se tiraba ahí mismo.

Por eso el arreglo va en la pantalla y no en el servidor: el servidor ya hacía
lo correcto.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

import pytest  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSX = os.path.join(RAIZ, "frontend", "src", "components", "CocinaMontada3.jsx")


# ── El servidor: ya estaba bien, y tiene que seguir estándolo ────────────────
@pytest.mark.parametrize("texto,mano", [
    ("10 A60I", "I"),
    ("10 A60D", "D"),
    ("1 b60i", "I"),
    ("2 asc60d", "D"),
    ("10 A60 I", "I"),
    ("10 A60", ""),        # sin escribir mano: se queda sin decidir
])
def test_el_servidor_LEE_la_mano_escrita(texto, mano):
    from services.mv_relacion import parse_relacion
    muebles = parse_relacion(texto, "T1")["muebles"]
    assert muebles, f"«{texto}» no se ha leído"
    assert muebles[0]["mano"] == mano, (
        f"«{texto}» debería dar mano {mano!r} y da {muebles[0]['mano']!r}")


def test_el_servidor_devuelve_el_codigo_de_CATALOGO():
    """Y esto no es un fallo: `A60D/I` es como se llama el mueble en la tarifa.

    Se comprueba a propósito para que quede claro por qué la pantalla tiene que
    hacer el último paso. Si algún día el servidor devolviera ya `A60I`, esta
    prueba avisaría de que el arreglo de la pantalla ha dejado de hacer falta.
    """
    from services.mv_relacion import parse_relacion
    m = parse_relacion("10 A60I", "T1")["muebles"][0]
    assert m["cod"] == "A60D/I" and m["mano"] == "I"


# ── La pantalla: EJECUTANDO su función, no leyendo su texto ──────────────────
def _corre_en_node(valores):
    """Saca `aplicarManoEscrita` del JSX y la corre de verdad con node."""
    import json
    import shutil
    node = shutil.which("node")
    if not node:
        pytest.skip("no hay node en esta máquina")
    with open(JSX, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    i = cuerpo.index("const aplicarManoEscrita = (m) => {")
    j = cuerpo.index("\n  };", i) + len("\n  };")
    guion = (cuerpo[i:j] + "\nconsole.log(JSON.stringify("
             + json.dumps(valores) + ".map(aplicarManoEscrita)));")
    r = subprocess.run([node, "-e", guion], capture_output=True, text=True,
                       timeout=60)
    assert r.returncode == 0, f"la función de la pantalla no corre: {r.stderr}"
    return json.loads(r.stdout)


def test_LA_MANO_ESCRITA_ACABA_EN_EL_CODIGO():
    """El fallo del master, arreglado y comprobado ejecutando su pantalla."""
    fuera = _corre_en_node([
        {"cod": "A60D/I", "mano": "I"},
        {"cod": "A60D/I", "mano": "D"},
        {"cod": "B60D/I", "mano": "i"},      # en minúscula, como se teclea
    ])
    assert [m["cod"] for m in fuera] == ["A60I", "A60D", "B60I"], (
        f"la mano escrita no llega al código: {[m['cod'] for m in fuera]}. El "
        "mueble saldría marcado «Sin mano» habiéndola escrito el master.")
    assert [m["mano"] for m in fuera] == ["I", "D", "I"]


def test_SIN_MANO_ESCRITA_no_se_inventa_ninguna():
    """La otra mitad. Si no la escribes, el mueble tiene que seguir pidiéndola:
    poner una por defecto sería fabricar diez altos abriendo al revés."""
    fuera = _corre_en_node([
        {"cod": "A60D/I", "mano": ""},
        {"cod": "A60D/I"},
        {"cod": "A60D/I", "mano": "X"},
    ])
    assert all(m["cod"] == "A60D/I" for m in fuera), (
        f"se ha inventado una mano: {[m['cod'] for m in fuera]}")


def test_un_codigo_que_YA_TRAE_MANO_no_se_toca():
    fuera = _corre_en_node([
        {"cod": "A60D", "mano": "I"},        # contradictorio: manda el código
        {"cod": "BF60", "mano": "D"},        # no lleva mano en su familia
    ])
    assert [m["cod"] for m in fuera] == ["A60D", "BF60"]


def test_la_pantalla_SIGUE_sacando_la_mano_del_codigo():
    """El arreglo no puede convertirse en una segunda fuente de la verdad.

    `rotarMano` y `fijarTodasManos` reescriben el CÓDIGO. Si el rótulo empezara
    a leer `m.mano`, en cuanto alguien pulsara el botón el código diría una cosa
    y la etiqueta otra.
    """
    with open(JSX, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    i = cuerpo.index("const manoDe = (cod) =>")
    trozo = cuerpo[i:i + 260]
    assert "_MANO_SUFIJO.exec" in trozo, (
        "`manoDe` ya no saca la mano del código")
    assert ".mano" not in trozo, (
        "`manoDe` ha empezado a leer el campo `mano`: eso son dos fuentes para "
        "el mismo dato y se separarán en cuanto se pulse «cambiar mano»")
