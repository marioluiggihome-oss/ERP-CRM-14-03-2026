# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del despiece de ARMARIOS 2.

Este despiece se imprime en el PDF que ve el cliente y se exporta en CSV para
cortar. Si miente, se corta madera mal, y eso no se ve hasta que la pieza ya
está cortada.

QUÉ HACÍA ANTES
---------------
Toda balda salía de 400 mm y todo frente de cajón de 400 × 180, dibujaras el
cuerpo que dibujaras. En un armario de 2 m partido en dos, la balda real mide
unos 966 mm: el despiece pedía cortar menos de la mitad. Y Armarios 2 es
justamente el módulo donde se dibujan cuerpos de anchos distintos, o sea donde
más importaba.

LO QUE SE PROTEGE
-----------------
1. NINGUNA MEDIDA FIJA. Cada pieza se corta sobre el HUECO LIBRE del cuerpo
   donde está dibujada. Si alguien vuelve a poner un número fijo, dos armarios
   distintos darían el mismo despiece — y aquí eso se ve.

2. HUECO LIBRE NO ES PASO BRUTO. El reparto incluye el divisor; la balda se
   corta sobre lo que queda. Confundirlos es exactamente por lo que una balda
   no entra.

3. SE REDONDEA HACIA ABAJO. Una balda un milímetro corta entra. Una balda un
   milímetro larga no entra, y es un viaje a fábrica. La suma de los huecos más
   los gruesos NUNCA puede pasarse del ancho del armario.

4. LAS HOLGURAS SON LAS DE LA CASA. Las mismas que el despiece de
   `Armarios.jsx` y que `armario_geometry.py`, que dibuja el alzado acotado. Si
   alguien cambia una sin cambiar la otra, el plano estaría mintiendo sobre la
   pieza que va a existir.

5. NADA DESAPARECE EN SILENCIO. Barra, zapatero, pantalonero y LED se dibujan
   en pantalla y antes no salían en el despiece: quien lo leía creía que ese
   armario no los llevaba.

6. SIN MEDIDAS NO HAY DESPIECE. Si falta el ancho, el alto, el fondo o el
   grueso, se devuelve vacío. Un despiece a medias es peor que ninguno, porque
   el de fábrica se lo cree.

CÓMO SE PRUEBA
--------------
Ejecutando la cuenta de verdad. `armarios2_despiece.js` es JavaScript puro —
sin React, sin imports— así que se le quitan los `export` y se corre con node.
Leer el fichero y comprobar que "pone lo correcto" no es probar una cuenta: es
probar un texto.
"""
import json
import os
import re
import shutil
import subprocess

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JS = os.path.join(RAIZ, "frontend", "src", "components", "armarios2_despiece.js")
JSX = os.path.join(RAIZ, "frontend", "src", "components", "Armarios2.jsx")
GEOMETRIA = os.path.join(RAIZ, "backend", "services", "armario_geometry.py")


@pytest.fixture(scope="module")
def fuente_js():
    if not os.path.exists(JS):
        pytest.skip("armarios2_despiece.js no está en este entorno")
    with open(JS, encoding="utf-8") as f:
        return f.read()


def _correr(fuente_js, cfg, comps, boundaries):
    """Ejecuta el despiece real con node y devuelve las filas."""
    if not shutil.which("node"):
        pytest.skip("node no está disponible en este entorno")
    codigo = re.sub(r"^export ", "", fuente_js, flags=re.MULTILINE)
    guion = (codigo + "\nconsole.log(JSON.stringify(despiece("
             + json.dumps({"cfg": cfg, "comps": comps, "boundaries": boundaries})
             + ")));\n")
    r = subprocess.run(["node", "-e", guion], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"el despiece ha reventado:\n{r.stderr}"
    return json.loads(r.stdout)


def _fila(filas, pieza):
    for f in filas:
        if f["p"] == pieza:
            return f
    return None


def _numeros(medida):
    return [int(n) for n in re.findall(r"-?\d+", str(medida))]


# Armario de 2000 mm partido en dos por un divisor al 50 %, grueso 19.
CFG = {"width": 2000, "height": 2400, "depth": 600, "thickness": 19}
COMPS = [
    {"type": "divider-v", "x": 50},
    {"type": "shelf", "sectionIndex": 0},
    {"type": "shelf", "sectionIndex": 0},
    {"type": "drawer", "sectionIndex": 1},
    {"type": "hanging-rod", "sectionIndex": 1},
]
LIM = [0, 50, 100]


# ─── 1. Ninguna medida fija ────────────────────────────────────────────────

def test_la_balda_mide_el_hueco_de_su_cuerpo(fuente_js):
    filas = _correr(fuente_js, CFG, COMPS, LIM)
    balda = _fila(filas, "Balda")
    assert balda is not None, "el despiece se ha quedado sin baldas"
    largo = _numeros(balda["medida"])[0]
    assert 900 < largo < 1000, (
        f"la balda sale de {largo} mm en un cuerpo de casi un metro. Si vuelve "
        "a ser un número fijo (antes eran 400), se corta menos de la mitad de "
        "lo que hace falta")


def test_cambiar_el_ancho_cambia_la_balda(fuente_js):
    """La prueba de que no hay ningún número fijo escondido."""
    estrecho = _correr(fuente_js, {**CFG, "width": 1200}, COMPS, LIM)
    ancho = _correr(fuente_js, {**CFG, "width": 3000}, COMPS, LIM)
    a = _numeros(_fila(estrecho, "Balda")["medida"])[0]
    b = _numeros(_fila(ancho, "Balda")["medida"])[0]
    assert b > a + 800, (
        f"un armario de 1,20 m y otro de 3 m dan baldas de {a} y {b} mm: el "
        "despiece no está mirando el armario que tiene delante")


def test_mover_el_divisor_cambia_cada_cuerpo(fuente_js):
    """Dos cuerpos desiguales tienen que dar dos baldas distintas."""
    comps = [{"type": "divider-v", "x": 30},
             {"type": "shelf", "sectionIndex": 0},
             {"type": "shelf", "sectionIndex": 1}]
    filas = _correr(fuente_js, CFG, comps, [0, 30, 100])
    baldas = [f for f in filas if f["p"] == "Balda"]
    assert len(baldas) == 2, "las dos baldas se han fundido en una sola línea"
    largos = sorted(_numeros(b["medida"])[0] for b in baldas)
    assert largos[1] - largos[0] > 700, (
        f"un cuerpo al 30 % y otro al 70 % dan baldas de {largos}: el hueco de "
        "cada cuerpo no se está calculando por separado")


# ─── 2 y 3. Hueco libre, y nunca pasarse ───────────────────────────────────

def test_los_huecos_mas_los_gruesos_caben_en_el_armario(fuente_js):
    """Si la suma se pasa del ancho, en fábrica no cierra."""
    for divisores, lim in (([], [0, 100]),
                           ([{"type": "divider-v", "x": 50}], [0, 50, 100]),
                           ([{"type": "divider-v", "x": 33},
                             {"type": "divider-v", "x": 66}], [0, 33, 66, 100])):
        comps = divisores + [{"type": "shelf", "sectionIndex": i}
                             for i in range(len(lim) - 1)]
        filas = _correr(fuente_js, CFG, comps, lim)
        huecos = [_numeros(f["medida"])[0] + 6 for f in filas if f["p"] == "Balda"]
        gruesos = CFG["thickness"] * (2 + len(divisores))
        assert sum(huecos) + gruesos <= CFG["width"], (
            f"con {len(divisores)} divisores los huecos ({huecos}) más los "
            f"gruesos ({gruesos}) suman más que el ancho del armario "
            f"({CFG['width']}): eso es un armario que no cierra")


def test_la_balda_no_es_el_hueco_entero(fuente_js):
    filas = _correr(fuente_js, CFG, COMPS, LIM)
    balda = _fila(filas, "Balda")
    hueco = int(re.search(r"hueco libre (\d+)", balda["nota"]).group(1))
    largo = _numeros(balda["medida"])[0]
    assert largo == hueco - 6, (
        f"la balda ({largo}) se corta a ras del hueco ({hueco}); sin holgura "
        "no entra")


def test_el_cuerpo_del_cajon_descuenta_las_guias(fuente_js):
    filas = _correr(fuente_js, CFG, COMPS, LIM)
    cajon = _fila(filas, "Cajón (cuerpo)")
    assert cajon is not None, "el cajón ha desaparecido del despiece"
    hueco = int(re.search(r"hueco libre (\d+)", cajon["nota"]).group(1))
    assert _numeros(cajon["medida"])[0] == hueco - 26, (
        "el cuerpo del cajón no descuenta las guías: no entra en el hueco")


def test_el_frente_de_cajon_no_es_una_medida_inventada(fuente_js):
    filas = _correr(fuente_js, CFG, COMPS, LIM)
    frente = _fila(filas, "Frente de cajón")
    assert frente is not None, "el frente de cajón ha desaparecido del despiece"
    ancho = _numeros(frente["medida"])[0]
    assert ancho > 900, (
        f"el frente de cajón sale de {ancho} mm; antes eran 400 fijos para "
        "cualquier armario")


# ─── 4. Las holguras son las de la casa ────────────────────────────────────

@pytest.mark.parametrize("constante,nombre_py", [
    ("HOLGURA_BALDA", "HOLGURA_BALDA"),
    ("HOLGURA_CAJON", "HOLGURA_CAJON"),
    ("ALTO_CAJON", "ALTO_CAJON"),
    ("RETRANQUEO_INTERIOR", "RETRANQUEO_INTERIOR"),
    ("RETRANQUEO_CAJON", "RETRANQUEO_CAJON"),
])
def test_las_holguras_coinciden_con_el_alzado_acotado(fuente_js, constante, nombre_py):
    """El plano y el despiece tienen que decir lo mismo."""
    if not os.path.exists(GEOMETRIA):
        pytest.skip("armario_geometry.py no está en este entorno")
    with open(GEOMETRIA, encoding="utf-8") as f:
        py = f.read()
    m_py = re.search(rf"^{nombre_py}\s*=\s*(\d+)", py, re.MULTILINE)
    m_js = re.search(rf"export const {constante} = (\d+)", fuente_js)
    assert m_py and m_js, f"no se encuentra {constante} en los dos ficheros"
    assert m_py.group(1) == m_js.group(1), (
        f"{constante} vale {m_js.group(1)} en el despiece y {m_py.group(1)} en "
        "el alzado acotado. El plano estaría mintiendo sobre la pieza que se va "
        "a cortar")


# ─── 5. Nada desaparece en silencio ────────────────────────────────────────

@pytest.mark.parametrize("tipo,pieza", [
    ("hanging-rod", "Barra de colgar"),
    ("shoe-rack", "Zapatero"),
    ("pant-rack", "Pantalonero"),
    ("led-strip", "Tira LED"),
])
def test_lo_dibujado_sale_en_el_despiece(fuente_js, tipo, pieza):
    filas = _correr(fuente_js, CFG, [{"type": tipo, "sectionIndex": 0}], [0, 100])
    f = _fila(filas, pieza)
    assert f is not None, (
        f"un {pieza.lower()} dibujado en pantalla no aparece en el despiece: "
        "quien lo lee cree que ese armario no lo lleva")
    assert _numeros(f["medida"])[0] > 0, (
        f"el {pieza.lower()} sale sin medida")
    assert f["tablero"] is False, (
        f"el {pieza.lower()} es un herraje, no se corta de un tablero; "
        "listarlo con material manda a fábrica a cortar algo que no existe")


def test_las_piezas_iguales_se_agrupan(fuente_js):
    comps = [{"type": "shelf", "sectionIndex": 0} for _ in range(4)]
    filas = _correr(fuente_js, CFG, comps, [0, 100])
    baldas = [f for f in filas if f["p"] == "Balda"]
    assert len(baldas) == 1 and baldas[0]["q"] == 4, (
        "cuatro baldas iguales salen en cuatro líneas de 1 ud; el de fábrica "
        "tiene que ir sumándolas a mano")


# ─── 6. Sin medidas no hay despiece ────────────────────────────────────────

@pytest.mark.parametrize("falta", ["width", "height", "depth", "thickness"])
def test_sin_una_medida_no_se_despieza(fuente_js, falta):
    filas = _correr(fuente_js, {**CFG, falta: ""}, COMPS, LIM)
    assert filas == [], (
        f"sin {falta} ha sacado un despiece igual; un campo en blanco es «no se "
        "sabe», no «mide 0», y un despiece a medias el de fábrica se lo cree")


# ─── El componente usa esta cuenta y no otra ───────────────────────────────

def test_armarios2_usa_este_despiece():
    if not os.path.exists(JSX):
        pytest.skip("Armarios2.jsx no está en este entorno")
    with open(JSX, encoding="utf-8") as f:
        jsx = f.read()
    assert "from './armarios2_despiece'" in jsx, (
        "Armarios2 ya no usa el despiece probado; si se ha vuelto a copiar la "
        "cuenta dentro del componente, deja de estar protegida")
    assert "h: 400" not in jsx and "w: 400" not in jsx, (
        "han vuelto las medidas fijas de 400 mm al componente")
