# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
«A60D/I» ACABA EN «I», Y ESO NO ES UNA MANO IZQUIERDA.

El master, 07/09/2026: «ten en cuenta que HAY muchos muebles que aparecen como
D/I».

Y tiene razón en el número: en la tarifa T4, 125 de los 366 códigos llevan el
sufijo `D/I` — un tercio del catálogo. `D/I` quiere decir «UNA puerta, y la
mano está SIN DECIDIR», que es como MV imprime casi todo.

EL FALLO, Y POR QUÉ NADIE LO VEÍA
─────────────────────────────────
Tres sitios del Presupuestador leían la mano con
`cod.endsWith('D') ? 'D' : cod.endsWith('I') ? 'I' : ''`. Y «A60D/I» acaba en
«I». O sea que un mueble sin mano decidida salía como IZQUIERDA:

  · Al añadirlo desde el desplegable, la línea nacía con `mano: 'I'`.
  · En el PDF —el papel que se firma y que luego es el pedido— ponía «Izq».
  · En el copiado a WhatsApp, «[Izq]».

Lo peor es que NO SE VEÍA: el código seguía siendo «A60D/I», así que la
pantalla pintaba «⚠️ Sin Mano» —correcto, porque ese rótulo sale del CÓDIGO—
mientras el pedido viajaba con `hand: 'I'`. La pantalla decía «falta decidir» y
la fábrica recibía «izquierda». Nadie lo había decidido y no saltaba nada; se
ve con el montador, en la obra, con la puerta abriendo al revés.

`manoDe` distingue las TRES situaciones y ya existía: `undefined` (el mueble no
lleva mano), `null` (lleva, sin decidir) y `'D'`/`'I'` (decidida). El arreglo
estaba hecho en `RelacionReview.jsx`, que lo tiene comentado desde antes, y no
se había traído a esta pantalla.
"""
import json
import os
import re
import shutil
import subprocess

import pytest

from jsx_limpio import sin_comentarios

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CM3 = os.path.join(RAIZ, "frontend", "src", "components", "CocinaMontada3.jsx")
REVIEW = os.path.join(RAIZ, "frontend", "src", "components", "RelacionReview.jsx")
TARIFAS = os.path.join(RAIZ, "backend", "data", "mv_tarifas_oficiales.json")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _manoDe(codigos):
    """EJECUTA `manoDe` en node, la de verdad, sacada del fichero."""
    if not shutil.which("node"):
        pytest.skip("hace falta node para ejecutar la función de verdad")
    src = _lee(CM3)
    i = src.index("  const _MANO_SUFIJO")
    fin = src.index("\n  const rotarMano", i)
    fn = src[i:fin]
    js = (fn + f"\nconst CASOS = {json.dumps(codigos)};\n"
          + "console.log(JSON.stringify(CASOS.map(c => {\n"
          + "  const r = manoDe(c);\n"
          + "  return r === undefined ? 'SIN_MANO' : r === null ? 'SIN_DECIDIR' : r;\n"
          + "})));")
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"node falló:\n{r.stderr[-2000:]}"
    return json.loads(r.stdout.strip().splitlines()[-1])


# ─── EL NÚMERO QUE LO HACE GRAVE ─────────────────────────────────────────────

def test_UN_TERCIO_del_catalogo_esta_sin_mano_decidir():
    """«Hay MUCHOS muebles que aparecen como D/I» — con la cifra delante."""
    with open(TARIFAS, "r", encoding="utf-8") as f:
        t4 = json.load(f)["tariffs"]["T4"]
    todos = [k for v in t4.values() for k in (v.get("items") or {})]
    di = [k for k in todos if k.endswith("D/I")]
    assert len(di) > 100 and len(di) / len(todos) > 0.25, (
        f"solo {len(di)} de {len(todos)} llevan D/I; si el catálogo ha cambiado "
        "de forma, revisa que esto siga significando lo mismo")


# ─── LAS TRES SITUACIONES ────────────────────────────────────────────────────

def test_manoDe_distingue_SIN_DECIDIR_de_IZQUIERDA():
    assert _manoDe(["A60D/I", "A60I", "A60D", "BF60", "ARC63D/I"]) == [
        "SIN_DECIDIR", "I", "D", "SIN_MANO", "SIN_DECIDIR"]


def test_TODOS_los_codigos_D_BARRA_I_de_la_tarifa_salen_SIN_DECIDIR():
    """No un puñado: los 125 de la T4, uno a uno."""
    with open(TARIFAS, "r", encoding="utf-8") as f:
        t4 = json.load(f)["tariffs"]["T4"]
    di = sorted({k for v in t4.values() for k in (v.get("items") or {})
                 if k.endswith("D/I")})
    assert len(di) > 100
    salida = _manoDe(di)
    malos = [c for c, r in zip(di, salida) if r != "SIN_DECIDIR"]
    assert not malos, (
        f"{len(malos)} códigos sin decidir se leen como una mano concreta; el "
        f"primero: {malos[0]}. Cada uno de esos se fabricaría con esa mano sin "
        "que nadie lo hubiera decidido")


# ─── DONDE ESTABA EL FALLO ───────────────────────────────────────────────────

def test_NADIE_lee_la_mano_con_endsWith():
    """Es el patrón exacto que fallaba. Si vuelve a aparecer, vuelve el fallo."""
    for ruta in (CM3, REVIEW):
        # SIN COMENTARIOS, y con el limpiador del proyecto: los dos ficheros
        # explican este fallo CITANDO el patrón que lo causaba, y un troceo por
        # «//» no quita los bloques `/* … */`. Con esa cita dentro, la prueba
        # se pondría roja por su propia explicación.
        codigo = sin_comentarios(_lee(ruta))
        sobra = re.findall(r"endsWith\('[DI]'\)", codigo)
        assert not sobra, (
            f"{os.path.basename(ruta)} vuelve a sacar la mano del final del "
            f"código: «A60D/I» acaba en «I» y saldría como izquierda ({sobra})")


def test_anadir_desde_el_desplegable_NO_decide_la_mano():
    """Era el peor de los tres: no mentía en un rótulo, ESCRIBÍA una mano que
    nadie había elegido, y encima la pantalla seguía diciendo «Sin Mano»."""
    src = _lee(CM3)
    i = src.index("const añadirSugerencia = (c) =>")
    cuerpo = src[i:src.index("\n  };", i)]
    assert "manoDe(c.cod) || ''" in cuerpo, (
        "la sugerencia vuelve a decidir la mano por su cuenta")


def test_el_PDF_dice_SIN_DECIDIR_en_vez_de_inventarse_una_mano():
    """El papel que se firma y que luego es el pedido."""
    src = _lee(CM3)
    i = src.index("const tableBody = muebles.map")
    cuerpo = src[i:i + 2500]
    assert "SIN DECIDIR" in cuerpo, (
        "el PDF vuelve a imprimir una mano concreta para un mueble sin decidir")
    assert "manoDe(m)" in cuerpo


def test_el_whatsapp_tampoco_se_la_inventa():
    src = _lee(CM3)
    assert "[MANO SIN DECIDIR]" in src


def test_a_la_FABRICA_la_mano_sale_del_CODIGO_no_de_un_campo_suelto():
    """`m.mano` es un campo de apoyo y podía contradecir al código: un «A60D/I»
    llegaba con `hand: 'I'` mientras la pantalla decía «Sin Mano». Sin decidir
    se manda VACÍO: mejor que el taller pregunte a que fabrique la que no es."""
    src = _lee(CM3)
    assert "hand: manoDe(m) || ''" in src
    assert "hand: m.mano" not in src


def test_la_MEDIDA_DEFINITIVA_tambien_llega_a_la_fabrica():
    """De paso: el taller recibía el ancho del escalón de tarifa, no el que se
    había escrito para cortar."""
    src = _lee(CM3)
    assert "width: m.anchoReal ?? m.ancho" in src
    assert "height: m.altoReal ?? m.alto" in src


# ─── Y EL MISMO FALLO ESTABA EN EL SERVIDOR ──────────────────────────────────

def test_el_SERVIDOR_tampoco_convierte_un_D_BARRA_I_en_izquierda():
    """El cuarto sitio, encontrado barriendo el repo entero después del aviso.

    `mv_relacion.py` lee la relación escrita a mano y tenía, en el camino del
    CÓDIGO EXACTO —cuyo propio ejemplo dice «ASC60D/I, B60D/I»—:

        mano = "D" if cod.endswith("D") else "I" if cod.endswith("I") else ""

    Así que escribir o pegar «1 b60d/i» devolvía `mano: "I"`. La pantalla
    seguía pintando «⚠️ Sin Mano» —ese rótulo sale del CÓDIGO— mientras el dato
    decía izquierda: la misma partida en dos que en el frontend, y en la fuente.

    El otro camino, el de «b60i» escrito suelto, sí lo distinguía desde el
    principio; por eso el fallo solo salía al pegar códigos de catálogo.
    """
    from services.mv_relacion import parse_relacion_text as P

    def _mano(texto):
        muebles = P(texto, "T1")
        assert muebles, f"«{texto}» no se ha leído"
        return muebles[0]["cod"], muebles[0]["mano"]

    assert _mano("1 b60d/i") == ("B60D/I", ""), "un D/I vuelve a salir con mano"
    assert _mano("1 asc60d/i") == ("ASC60D/I", "")
    assert _mano("1 a60d/i") == ("A60D/I", "")
    # Y lo que SÍ trae mano escrita se sigue leyendo: no se puede arreglar una
    # mitad rompiendo la otra.
    assert _mano("1 b60i")[1] == "I"
    assert _mano("1 b60d")[1] == "D"


def test_NINGUN_codigo_de_catalogo_trae_la_mano_decidida():
    """La premisa de la que depende el arreglo del servidor.

    En la tarifa, un mueble de una puerta se escribe «B60D/I» —las dos manos,
    sin elegir—. Si algún día MV imprimiera un «B60I» como código de catálogo,
    el camino del código exacto tendría que volver a mirar el final, y esta
    prueba es la que lo diría. Se comprueban las 21 tarifas.
    """
    with open(TARIFAS, "r", encoding="utf-8") as f:
        tfs = json.load(f)["tariffs"]
    raros = sorted({k for fams in tfs.values() for v in fams.values()
                    for k in (v.get("items") or {})
                    if not k.upper().endswith("D/I")
                    and k.upper().endswith(("D", "I"))})
    assert not raros, (
        f"hay códigos de catálogo con la mano ya decidida ({raros[:5]}): el "
        "camino del código exacto de `mv_relacion` los daría por «sin decidir»")


def test_TODOS_los_codigos_D_BARRA_I_pegados_salen_SIN_MANO_del_servidor():
    """Los 125 de la tarifa, uno a uno, por el camino del código exacto."""
    from services.mv_relacion import parse_relacion_text as P
    with open(TARIFAS, "r", encoding="utf-8") as f:
        t1 = json.load(f)["tariffs"]["T1"]
    di = sorted({k for v in t1.values() for k in (v.get("items") or {})
                 if k.endswith("D/I")})
    assert len(di) > 100
    malos = []
    for cod in di:
        muebles = P(f"1 {cod.lower()}", "T1")
        if muebles and muebles[0].get("mano"):
            malos.append((cod, muebles[0]["mano"]))
    assert not malos, (
        f"{len(malos)} códigos sin decidir vuelven del servidor con una mano "
        f"puesta; el primero: {malos[0]}")


def test_el_AVISO_de_sin_mano_sigue_contando_los_que_faltan():
    """La red de seguridad: mientras queden líneas sin decidir, la pantalla lo
    dice y ofrece fijarlas de golpe."""
    src = _lee(CM3)
    assert "const sinMano = muebles.filter(m => manoDe(m) === null).length;" in src
    assert "sin mano · Fijar Dcha" in src
