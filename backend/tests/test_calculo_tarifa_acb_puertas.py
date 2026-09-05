# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LA TARIFA DE PUERTAS DE ACB, Y LA SECCIÓN QUE LA ENSEÑA.

El master, 04/09/2026: «lo quiero poner en la sección de cocina desmontada al
igual que los cascos, pero una sección que ponga ACB PUERTAS».

QUÉ ES. `frontend/src/data/acbPuertas.js` es el hermano de `cascos.js`: mismo
proveedor —Grupo ACB / Canteado Industrial S.L.—, allí los cuerpos de mueble y
aquí los frentes. Se transcribe del PDF oficial de 2026.

POR QUÉ ESTE CANDADO ES DISTINTO DE LOS DEMÁS. Aquí no hay una regla de negocio
que proteger: hay MIL QUINIENTOS NÚMEROS copiados a mano de un PDF ESCANEADO, y
un dígito mal leído no da ningún error. Sale en un presupuesto y se ve cuando
llega la factura del proveedor. Así que lo que se comprueba es la FORMA de la
tarifa, que es lo único que una máquina puede comprobar sin tener el PDF
delante:

1. DENTRO DE UN ALTO, EL PRECIO SUBE CON EL ANCHO. Siempre, en todas las
   series. Es la propiedad que caza casi cualquier dígito mal leído: un 19,81
   escrito 91,81 rompe la subida.

2. Y CON EL ALTO TAMBIÉN, a igual ancho. Misma idea por el otro eje.

3. LO QUE NO SE FABRICA NO ESTÁ. Las casillas que el PDF deja en «----» se
   OMITEN, no se escriben como 0 €. Un cero ahí es un frente gratis en el
   escandallo (CLAUDE.md, regla 7). Por eso `precioFrenteACB` devuelve `null` y
   la pantalla rotula «--».

4. NADA DE PRECIOS RAROS. Ni negativos, ni ceros, ni un frente de 4.000 €.

Y de la pantalla: que la sección exista, que se llame como la pidió el master,
que enseñe la letra pequeña de la tarifa —el tirador gola aparte, los montados
que no lo admiten, los frentes pequeños que salen lisos— y que una casilla sin
precio no se pueda pulsar.
"""
import json
import os
import re
import shutil
import subprocess

import pytest

from jsx_limpio import sin_comentarios

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(RAIZ, "frontend", "src")
DATOS = os.path.join(SRC, "data", "acbPuertas.js")
PANTALLA = os.path.join(SRC, "components", "Cascos.jsx")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _bloque(cuerpo, arranque, cierre):
    i = cuerpo.index(arranque)
    return cuerpo[i:cuerpo.index(cierre, i) + len(cierre)]


def _tarifa():
    """EJECUTA el fichero de datos en node y devuelve lo que exporta."""
    if not shutil.which("node"):
        pytest.skip("hace falta node para leer la tarifa de verdad")
    src = re.sub(r"^export const", "const", _lee(DATOS), flags=re.M)
    js = src + """
console.log(JSON.stringify({
  series: ACB_PUERTAS_SERIES, filas: ACB_PUERTAS,
  tramos: ACB_COMPLEMENTOS_TRAMOS, complementos: ACB_COMPLEMENTOS,
  regletas: ACB_REGLETAS, dtoZocalo: ACB_ZOCALO_SIN_CANTEAR_DTO,
  pruebas: [
    precioFrenteACB('gm20', 558, 248),
    precioFrenteACB('qualita', 1298, 598),
    precioFrenteACB('calabria8', 138, 248),
    precioFrenteACB('gm20', 9999, 248),
  ],
}));"""
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"la tarifa no se puede leer: {r.stderr[-400:]}"
    return json.loads(r.stdout)


def test_EL_PRECIO_SUBE_CON_EL_ANCHO():
    """La propiedad que caza un dígito mal leído: un 19,81 escrito 91,81 rompe
    la subida y esto se pone rojo."""
    t = _tarifa()
    por_alto = {}
    for f in t["filas"]:
        por_alto.setdefault((f["serie"], tuple(f["altos"])), []).append((f["ancho"], f["precio"]))
    fallos = []
    for (serie, altos), piezas in por_alto.items():
        piezas.sort()
        for (w1, p1), (w2, p2) in zip(piezas, piezas[1:]):
            if p2 < p1:
                fallos.append(f"{serie} alto {list(altos)}: {w2}mm cuesta {p2} y {w1}mm cuesta {p1}")
    assert not fallos, (
        "hay precios que BAJAN al crecer el frente. O la tarifa es así —y hay que "
        "dejarlo dicho aquí— o es un dígito mal transcrito del PDF:\n  "
        + "\n  ".join(fallos[:10]))


# UN CÉNTIMO DE TOLERANCIA POR EL EJE DEL ALTO, Y SOLO POR AHÍ.
#
# La propia tarifa de ACB tiene una inversión de un céntimo: el Qualita de
# 598x598 vale 50,10 € y el de 698x598 vale 50,09 €. Comprobado en el PDF (pág.
# 43): no es una errata de la transcripción, es el redondeo del proveedor.
#
# La tolerancia es de UN CÉNTIMO a propósito. Lo que esta prueba caza son
# dígitos mal leídos —un 19,81 escrito 91,81, un 44,56 escrito 4,56—, y eso
# nunca falla por céntimos: falla por decenas. Una tolerancia ancha dejaría
# pasar justo lo que se busca.
TOLERANCIA_REDONDEO = 0.011


def test_EL_PRECIO_SUBE_CON_EL_ALTO():
    """Lo mismo por el otro eje, a igual ancho."""
    t = _tarifa()
    por_ancho = {}
    for f in t["filas"]:
        por_ancho.setdefault((f["serie"], f["ancho"]), []).append((f["altos"][0], f["precio"]))
    fallos = []
    for (serie, ancho), piezas in por_ancho.items():
        piezas.sort()
        for (h1, p1), (h2, p2) in zip(piezas, piezas[1:]):
            if p1 - p2 > TOLERANCIA_REDONDEO:
                fallos.append(f"{serie} ancho {ancho}: alto {h2} cuesta {p2} y alto {h1} cuesta {p1}")
    assert not fallos, (
        "hay precios que BAJAN al crecer el alto del frente:\n  " + "\n  ".join(fallos[:10]))


def test_LO_QUE_NO_SE_FABRICA_NO_VALE_CERO():
    """El «----» del PDF se omite, nunca se escribe 0 € (regla 7)."""
    t = _tarifa()
    ceros = [f for f in t["filas"] if not f["precio"] or f["precio"] <= 0]
    assert not ceros, (
        f"hay frentes a 0 € o menos en la tarifa: {ceros[:5]}. Una casilla «----» "
        "del PDF es que ACB NO FABRICA esa medida, no que salga gratis")
    # Y la búsqueda lo dice: `null`, no cero.
    gm, qual, calabria, inexistente = t["pruebas"]
    assert gm == 19.81, f"el frente GM 2.0 de 558x248 vale {gm} y en la tarifa son 19,81 €"
    assert qual == 85.67, f"el Qualita de 1298x598 vale {qual} y en la tarifa son 85,67 €"
    assert calabria is None, (
        "Calabria 8 no se fabrica en 138x248 —el PDF pone «----»— y la tarifa "
        "está devolviendo un precio")
    assert inexistente is None, "una medida que no existe devuelve un precio"


def test_NINGUN_PRECIO_ABSURDO():
    """Un frente no cuesta 4.000 € ni 20 céntimos. Caza el dígito de más."""
    t = _tarifa()
    raros = [f for f in t["filas"] if not (5 <= f["precio"] <= 400)]
    assert not raros, (
        f"precios fuera de todo rango razonable para un frente: {raros[:5]}")


def test_CADA_FILA_TIENE_SU_SERIE_DECLARADA():
    """Una fila con una serie que no está en el catálogo no se puede pintar ni
    pedir: sería un precio huérfano."""
    t = _tarifa()
    declaradas = {s["id"] for s in t["series"]}
    usadas = {f["serie"] for f in t["filas"]}
    assert usadas <= declaradas, (
        f"hay precios de series que no están en el catálogo: {sorted(usadas - declaradas)}")
    assert declaradas - usadas == set(), (
        f"hay series en el catálogo sin un solo precio: {sorted(declaradas - usadas)}. "
        "Se ofrecería una serie que al elegirla sale vacía")


def test_LA_LETRA_PEQUENA_DE_LA_TARIFA_VIAJA_CON_LA_SERIE():
    """Son las tres cosas que cambian el precio y no están en ninguna casilla."""
    t = _tarifa()
    notas = {s["id"]: s["nota"] for s in t["series"]}
    assert "GOLA" in notas["gm20"].upper(), (
        "GM 2.0 (BERNA) lleva el tirador gola APARTE y la tarifa no lo dice: el "
        "frente saldría más barato de lo que se paga")
    assert "gola" in notas["galdar"].lower(), (
        "los Galdar montados NO pueden llevar tirador gola, y no se avisa")
    for serie in ("calabria8", "auraResto", "auraSense"):
        assert "238" in notas[serie], (
            f"«{serie}»: los frentes de menos de 238 salen LISOS aunque se pidan "
            f"de esta serie, y la tarifa no lo dice")


def test_LA_SECCION_SE_LLAMA_COMO_LA_PIDIO_EL_MASTER():
    cuerpo = sin_comentarios(_lee(PANTALLA))
    secciones = _bloque(cuerpo, "const SECCIONES = [", "\n];")
    assert "id: 'acbPuertas'" in secciones, (
        "no hay sección de puertas ACB en Cocina Desmontada")
    assert "label: 'ACB PUERTAS'" in secciones, (
        "la sección no se llama «ACB PUERTAS», que es como la pidió el master")
    # Pegada a CASCOS: es el mismo proveedor y el mismo albarán.
    ids = re.findall(r"id: '(\w+)'", secciones)
    assert ids[:2] == ["cascos", "acbPuertas"], (
        f"la sección de puertas no va junto a la de cascos: {ids}")


def test_LA_PANTALLA_PINTA_LA_MATRIZ_Y_NO_INVENTA_HUECOS():
    cuerpo = sin_comentarios(_lee(PANTALLA))
    panel = _bloque(cuerpo, 'data-testid="acb-puertas"', "\n          ) : (seccion === 'blum'")
    assert 'data-testid="acb-puertas-serie"' in panel, "no se puede elegir la serie"
    assert 'data-testid="acb-puertas-add"' in panel, "no se puede añadir un frente"
    assert "if (precio == null) {" in panel, (
        "la pantalla no distingue la casilla sin precio")
    # HASTA EL CIERRE DEL `if`, contando llaves. Cortar por el primer `}` se
    # quedaba en el `{w}` de la clave de React y no llegaba a ver el rótulo.
    i = panel.index("if (precio == null) {")
    hondo = 0
    for k in range(i, len(panel)):
        if panel[k] == "{":
            hondo += 1
        elif panel[k] == "}":
            hondo -= 1
            if hondo == 0:
                break
    hueco = panel[i:k + 1]
    assert ">--<" in hueco.replace(" ", "").replace("\n", ""), (
        f"una medida que ACB no fabrica no se rotula «--»: {hueco.strip()[:200]}")
    assert "no fabrica" in hueco, (
        "el hueco no explica por qué está vacío: se leería como un fallo de la pantalla")
    assert "eur(0)" not in panel and "|| 0" not in panel, (
        "hay un cero por defecto en la matriz: un frente que no existe saldría "
        "costando 0,00 €")


def test_LA_PANTALLA_ENSENA_LA_LETRA_PEQUENA():
    cuerpo = sin_comentarios(_lee(PANTALLA))
    panel = _bloque(cuerpo, 'data-testid="acb-puertas"', "\n          ) : (seccion === 'blum'")
    assert 'data-testid="acb-puertas-nota"' in panel, (
        "la nota de la serie no se pinta: el tirador gola aparte y los frentes "
        "que salen lisos no se verían en ninguna parte")
    assert "serieObj.nota &&" in panel, (
        "la nota se pinta siempre, incluso vacía, y deja un aviso en blanco")


def test_UN_FRENTE_VA_AL_MISMO_CARRITO_QUE_LOS_CASCOS():
    """Es el mismo pedido al mismo proveedor. Dos carritos serían dos albaranes
    para una cocina."""
    cuerpo = sin_comentarios(_lee(PANTALLA))
    add = _bloque(cuerpo, "const addPuertaToCart", "\n  };")
    assert "setCart(prev =>" in add, "los frentes no van al carrito de siempre"
    assert "puerta: true" in add, (
        "la línea no se marca como frente: no se podría distinguir de un casco "
        "al mandarle el pedido al proveedor")
    assert "altos," in add, (
        "la línea no guarda las DOS medidas del grupo: un «1198 & 1298» son dos "
        "altos al mismo precio y al proveedor hay que decirle cuál")
    assert "precio: pc(precio)" in add, (
        "el precio del frente no pasa por `pc`, que es quien decide el precio en "
        "Cocina Desmontada — donde NO se multiplica por el valor del punto")
