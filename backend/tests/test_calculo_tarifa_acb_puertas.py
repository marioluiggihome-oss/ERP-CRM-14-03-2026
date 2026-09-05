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
import sys

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
  series: ACB_PUERTAS_SERIES, filas: ACB_PUERTAS, colecciones: ACB_COLECCIONES,
  complementos: ACB_COMPLEMENTOS, cantosPieza: ACB_COMPLEMENTOS_CANTOS,
  dtoZocalo: ACB_ZOCALO_SIN_CANTEAR_DTO,
  pruebas: [
    precioFrenteACB('gm20', 'pvc', 558, 248),
    precioFrenteACB('qualita', 'pvc', 1298, 598),
    precioFrenteACB('calabria8', 'pvc', 138, 248),
    precioFrenteACB('gm20', 'pvc', 9999, 248),
    precioFrenteACB('touch22', 'alma', 558, 248),
    precioFrenteACB('gm20', 'alma', 558, 248),
  ],
}));"""
    # A UN FICHERO, NO A `node -e`. Con 1.530 precios el script se pasa del
    # tamaño máximo de la línea de órdenes y `node` revienta con «Argument list
    # too long» — un error que no se parece en nada a su causa y que dejó seis
    # pruebas rojas sin que la tarifa tuviera nada malo.
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8",
                                     delete=False) as fh:
        fh.write(js)
        ruta = fh.name
    try:
        r = subprocess.run(["node", ruta], capture_output=True, text=True, timeout=120)
    finally:
        os.unlink(ruta)
    assert r.returncode == 0, f"la tarifa no se puede leer: {r.stderr[-400:]}"
    return json.loads(r.stdout)


# UN CÉNTIMO DE TOLERANCIA, Y SOLO UN CÉNTIMO.
#
# La propia tarifa de ACB tiene inversiones de un céntimo por redondeo: el
# Qualita de 598x598 vale 50,10 € y el de 698x598 vale 50,09 €; el Touch 22 de
# 798x248 vale 30,57 € y el de 798x298 vale 30,56 €. Comprobado en el PDF: no
# son erratas de la transcripción.
#
# La tolerancia es de UN céntimo a propósito. Lo que estas dos pruebas cazan son
# dígitos mal leídos —un 19,81 escrito 91,81, un 44,56 escrito 4,56—, y eso
# nunca falla por céntimos: falla por decenas. Una tolerancia ancha dejaría
# pasar justo lo que se busca.
TOLERANCIA_REDONDEO = 0.011

# INVERSIONES DE LA TARIFA COMPROBADAS UNA A UNA CONTRA EL PDF.
#
# Aquí solo entra lo que se ha mirado con lupa —el PDF re-renderizado a 400 dpi
# y la celda leída otra vez— y ha resultado ser así de verdad. Cada una lleva su
# página. Es una LISTA CERRADA a propósito: una inversión nueva se pone roja,
# que es justo el fallo que se busca. Aflojar la tolerancia hasta que dejen de
# saltar sería tapar erratas futuras con la excusa de estas.
#
# Palma Touch, ancho 398: el frente de 448 de alto cuesta 21 céntimos MENOS que
# el de 348 (34,81 € contra 35,02 € en PVC; 35,51 € contra 35,72 € en ALMA).
# Pág. 48 del PDF. Es la tarifa de ACB, no la transcripción.
#
# Palma Touch, ancho 598: el frente de 1498 de alto cuesta 6,46 € MENOS que el
# de 1298 (117,96 € contra 124,42 € en PVC; 120,32 € contra 126,91 € en ALMA).
# Págs. 49 y 50. Y el 124,42 se sale también de su propia fila —de 498 a 598
# sube 19,75 € cuando en la fila de 1498 sube 9,87 €—, así que lo más probable
# es que el error esté en la tarifa de ACB. Se deja tal cual: aquí se copia lo
# que el proveedor factura, no lo que debería facturar.
INVERSIONES_DE_LA_TARIFA = {
    ("palmaTouch", "pvc", 398, 448, 348),
    ("palmaTouch", "alma", 398, 448, 348),
    ("palmaTouch", "pvc", 598, 1498, 1298),
    ("palmaTouch", "alma", 598, 1498, 1298),
}


def test_EL_PRECIO_SUBE_CON_EL_ANCHO():
    """La propiedad que caza un dígito mal leído: un 19,81 escrito 91,81 rompe
    la subida y esto se pone rojo."""
    t = _tarifa()
    # EL CANTO ENTRA EN EL GRUPO. Sin él se comparaban precios de cantos
    # distintos —el ALMA de 248 contra el PVC de 298— y salían decenas de
    # «bajadas» que no existen: el ALMA cuesta más que el PVC en toda la tarifa.
    por_alto = {}
    for f in t["filas"]:
        clave = (f["serie"], f["canto"], tuple(f["altos"]))
        por_alto.setdefault(clave, []).append((f["ancho"], f["precio"]))
    fallos = []
    for (serie, canto, altos), piezas in por_alto.items():
        piezas.sort()
        for (w1, p1), (w2, p2) in zip(piezas, piezas[1:]):
            if p1 - p2 > TOLERANCIA_REDONDEO:
                fallos.append(f"{serie}/{canto} alto {list(altos)}: {w2}mm cuesta {p2} y {w1}mm cuesta {p1}")
    assert not fallos, (
        "hay precios que BAJAN al crecer el frente. O la tarifa es así —y hay que "
        "dejarlo dicho aquí— o es un dígito mal transcrito del PDF:\n  "
        + "\n  ".join(fallos[:10]))


def test_EL_PRECIO_SUBE_CON_EL_ALTO():
    """Lo mismo por el otro eje, a igual ancho."""
    t = _tarifa()
    por_ancho = {}
    for f in t["filas"]:
        por_ancho.setdefault((f["serie"], f["canto"], f["ancho"]), []).append(
            (f["altos"][0], f["precio"]))
    fallos = []
    for (serie, canto, ancho), piezas in por_ancho.items():
        piezas.sort()
        for (h1, p1), (h2, p2) in zip(piezas, piezas[1:]):
            if (serie, canto, ancho, h2, h1) in INVERSIONES_DE_LA_TARIFA:
                continue
            if p1 - p2 > TOLERANCIA_REDONDEO:
                fallos.append(f"{serie}/{canto} ancho {ancho}: alto {h2} cuesta {p2} y alto {h1} cuesta {p1}")
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
    gm, qual, calabria, inexistente, touchAlma, gmAlma = t["pruebas"]
    assert gm == 19.81, f"el frente GM 2.0 de 558x248 vale {gm} y en la tarifa son 19,81 €"
    assert qual == 85.67, f"el Qualita de 1298x598 vale {qual} y en la tarifa son 85,67 €"
    assert calabria is None, (
        "Calabria 8 no se fabrica en 138x248 —el PDF pone «----»— y la tarifa "
        "está devolviendo un precio")
    assert inexistente is None, "una medida que no existe devuelve un precio"
    # EL CANTO ENTRA EN LA BUSQUEDA. El ALMA cuesta mas que el PVC en toda la
    # tarifa, asi que devolver «el primero que aparezca» seria un precio
    # equivocado sin dar ningun error.
    assert touchAlma == 24.52, (
        f"el Touch 22 de 558x248 con canto ALMA vale {touchAlma} y en la tarifa "
        f"son 24,52 € (el de canto PVC son 23,69 €)")
    assert gmAlma is None, (
        "GM 2.0 no se fabrica con canto ALMA y la tarifa está devolviendo un "
        "precio: se estaría cobrando el del PVC")


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

    # Y LO MISMO CON EL CANTO. Una serie que anuncia un canto que no fabrica
    # deja el desplegable con una opción que vacía la matriz — sin error, sin
    # explicación, y el master pensando que la tarifa está mal cargada.
    reales = {}
    for f in t["filas"]:
        reales.setdefault(f["serie"], set()).add(f["canto"])
    for s2 in t["series"]:
        anunciados = set(s2.get("cantos") or [])
        assert anunciados == reales.get(s2["id"], set()), (
            f"«{s2['id']}» anuncia los cantos {sorted(anunciados)} y en la tarifa "
            f"tiene precios en {sorted(reales.get(s2['id'], set()))}. El que sobre "
            f"sale en el desplegable y deja la matriz vacía; el que falte hace "
            f"invisible media tarifa.")


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


def test_EL_CANTO_ES_PARTE_DEL_PRECIO_EN_LA_PANTALLA():
    """El canto ALMA cuesta más que el PVC en toda la tarifa. Si la pantalla no
    lo dejara elegir, o lo dejara pedido en una serie que no lo fabrica, se
    cobraría un precio que no es y sin dar ningún error."""
    cuerpo = sin_comentarios(_lee(PANTALLA))
    assert 'data-testid="acb-puertas-canto"' in cuerpo, (
        "no se puede elegir el canto: las series Touch se tarifan en dos y el "
        "ALMA cuesta más")
    linea = _bloque(cuerpo, "const cantoActivo =", ";")
    assert "cantosSerie.some" in linea, (
        f"al cambiar de serie se queda pedido un canto que esa serie puede no "
        f"fabricar, y la matriz saldría vacía sin decir por qué: {linea.strip()}")
    matriz = _bloque(cuerpo, "const matrizPuertas = useMemo", "}, [coleccionPuerta, seriePuerta, cantoActivo]);")
    assert "f.canto === cantoActivo" in matriz, (
        "la matriz mezcla los dos cantos: se pintarían dos precios distintos "
        "para la misma medida")
    add = _bloque(cuerpo, "const addPuertaToCart", "\n  };")
    assert "canto: cantoActivo" in add, (
        "el frente va al carrito sin decir de qué canto es: al proveedor no se "
        "le podría pedir")


def test_LOS_COMPLEMENTOS_SUBEN_CON_LA_SUPERFICIE():
    """Costados, zócalos y regletas van por cm². Una pieza más grande no puede
    costar menos: es la misma propiedad que caza los dígitos mal leídos en los
    frentes."""
    t = _tarifa()
    cantos = [c["id"] for c in t["cantosPieza"]]
    fallos = []
    for gid, g in t["complementos"].items():
        for canto in cantos:
            vals = g[canto]
            assert len(vals) == len(g["tramos"]), (
                f"«{gid}/{canto}» tiene {len(vals)} precios para "
                f"{len(g['tramos'])} tramos: sobra o falta una columna entera")
            for tramo, a, b in zip(g["tramos"][1:], vals, vals[1:]):
                if a - b > TOLERANCIA_REDONDEO:
                    fallos.append(f"{gid}/{canto} hasta {tramo} cm²: {b} < {a}")
    assert not fallos, (
        "hay complementos que BAJAN de precio al crecer la pieza:\n  "
        + "\n  ".join(fallos[:10]))


def test_MAS_CANTOS_CUESTA_MAS():
    """Cada canto es más trabajo: 1 largo < 1 largo + 2 cortos < 4 cantos.
    Si se cruzaran, es que se han cambiado dos columnas de sitio — y entonces
    TODOS los precios de ese grupo están mal, no uno."""
    t = _tarifa()
    fallos = []
    for gid, g in t["complementos"].items():
        for tramo, a, b, c in zip(g["tramos"], g["unLargo"],
                                  g["unLargoDosCortos"], g["cuatroCantos"]):
            if a - b > TOLERANCIA_REDONDEO or b - c > TOLERANCIA_REDONDEO:
                fallos.append(f"{gid} hasta {tramo} cm²: {a} / {b} / {c}")
        costado = g.get("costado2440x600")
        if costado:
            if (costado["unLargo"] - costado["unLargoDosCortos"] > TOLERANCIA_REDONDEO
                    or costado["unLargoDosCortos"] - costado["cuatroCantos"] > TOLERANCIA_REDONDEO):
                fallos.append(f"{gid} costado 2440x600: {costado}")
    assert not fallos, (
        "el precio no crece con el número de cantos; lo más probable es que dos "
        "columnas estén cambiadas de sitio:\n  " + "\n  ".join(fallos[:10]))


def test_LO_QUE_EL_PDF_DEJA_EN_BLANCO_NO_ESTA():
    """La regleta de 2440 que el PDF deja en «------» NO la fabrica ACB en esa
    serie. Escribirla a 0 € sería una regleta gratis en un pedido."""
    t = _tarifa()
    for gid, g in t["complementos"].items():
        for alto, precio in g["regletas"].items():
            assert precio and precio > 0, (
                f"«{gid}» tiene la regleta de {alto} a {precio}: si ACB no la "
                f"fabrica, no se escribe; si la fabrica, tiene que costar algo")
    # Las dos que el PDF deja en blanco, comprobadas: no están.
    for gid in ("slateHoriz", "hafaxCasellaHoriz"):
        assert "2440" not in t["complementos"][gid]["regletas"], (
            f"«{gid}» tiene regleta de 2440 y el PDF (pág. 54) la deja en "
            f"«------»: ACB no la fabrica en esa serie")


def test_LAS_TOUCH_LLEGAN_A_UN_TRAMO_MAS_Y_NO_TRAEN_COSTADO():
    """Cada grupo tiene sus propios tramos. Meterlos todos en una lista común
    habría obligado a rellenar huecos, y rellenar huecos en una tarifa es
    inventarse precios."""
    t = _tarifa()
    for gid in ("touch22|pvc", "touch22|alma", "touch19|pvc", "touch19|alma"):
        g = t["complementos"][gid]
        assert g["tramos"][-1] == 14640, (
            f"«{gid}» ya no llega al tramo de 14640 cm² que trae su página")
        assert "costado2440x600" not in g, (
            f"«{gid}» tiene costado suelto y su página no lo trae: sale de otro "
            f"sitio o está inventado")
    for gid in ("gm20", "fenix", "hafaxCasellaVert"):
        g = t["complementos"][gid]
        assert g["tramos"][-1] == 10000, f"«{gid}» ha cambiado de tramos"
        assert g.get("costado2440x600"), (
            f"«{gid}» se ha quedado sin el costado de 2440x600, que su página sí trae")


def test_EL_ZOCALO_SIN_CANTEAR_LLEVA_SU_DESCUENTO():
    """Pág. 44: «al ser sin cantear, se hace un descuento del 10 % sobre el
    precio del costado a 1 largo». Va en la tarifa y no escrito a mano en una
    pantalla, para que no acaben existiendo dos descuentos para lo mismo."""
    t = _tarifa()
    assert abs(t["dtoZocalo"] - 0.10) < 1e-9, (
        f"el descuento del zócalo sin cantear es {t['dtoZocalo']} y la tarifa "
        f"dice 10 %")


def test_EL_FICHERO_DE_DATOS_ES_EL_QUE_SALE_DEL_GENERADOR():
    """El generador tiene que SER la fuente, no un adorno.

    `frontend/src/data/acbPuertas.js` se escribe con
    `herramientas/tarifa_acb_puertas.py`. Si alguien lo edita a mano —o un
    script se lo deja tocado, que ya pasó y se perdió un aviso de la tarifa—,
    el generador y el fichero dicen cosas distintas y nadie se entera: el
    siguiente que regenere borra el cambio, o al revés.

    Se REGENERA a un temporal y se compara byte a byte. Si esto se pone rojo,
    lo que hay que hacer es tocar el GENERADOR y volver a ejecutarlo, nunca
    editar el fichero de datos.
    """
    generador = os.path.join(RAIZ, "herramientas", "tarifa_acb_puertas.py")
    assert os.path.exists(generador), (
        "el generador de la tarifa no está en el repo, y el fichero de datos lo "
        "cita: nadie podría volver a generarlo")
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        destino = os.path.join(tmp, "acbPuertas.js")
        r = subprocess.run([sys.executable, generador, destino],
                           capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, (
            f"el generador de la tarifa no se ejecuta: {r.stderr[-500:]}")
        with open(destino, encoding="utf-8") as f:
            generado = f.read()
    actual = _lee(DATOS)
    if generado != actual:
        import difflib
        dif = list(difflib.unified_diff(
            generado.splitlines(), actual.splitlines(),
            "lo que genera la herramienta", "lo que hay en el repo", lineterm=""))
        raise AssertionError(
            "el fichero de la tarifa NO es el que sale del generador. Toca el "
            "generador y vuelve a ejecutarlo; no edites el fichero a mano.\n"
            + "\n".join(dif[:40]))


def test_LA_COLECCION_SE_LLAMA_CANTEADO():
    """El master, 04/09/2026: «todo lo que te estoy pasando de tarifa es un
    apartado que se debe llamar CANTEADO, que son puertas canteadas a cuatro
    cantos», y «ACB también tiene otras colecciones en puertas de MADERA y
    puertas LACA, que ya te pasaré más adelante».

    Por eso la colección es un CAMPO y no el nombre de la sección: cuando
    lleguen Madera y Laca serán otra entrada y otro bloque de precios, sin
    mover nada de lo que ya funciona."""
    t = _tarifa()
    ids = [c["id"] for c in t["colecciones"]]
    assert "canteado" in ids, "se ha perdido la colección CANTEADO"
    canteado = next(c for c in t["colecciones"] if c["id"] == "canteado")
    assert canteado["label"] == "CANTEADO", (
        f"la colección se llama «{canteado['label']}» y el master la llamó CANTEADO")
    assert "4 cantos" in canteado["desc"] or "cuatro cantos" in canteado["desc"], (
        "la colección no dice qué es: puertas canteadas a cuatro cantos")


def test_NINGUN_PRECIO_SE_QUEDA_SIN_COLECCION():
    """Un precio sin colección no se puede pintar cuando haya más de una: o se
    mezclaría con la tarifa de Madera, o desaparecería."""
    t = _tarifa()
    declaradas = {c["id"] for c in t["colecciones"]}
    sueltas = {f.get("coleccion") for f in t["filas"]} - declaradas
    assert not sueltas, f"hay precios de colecciones que no existen: {sueltas}"
    sin = [f for f in t["filas"] if not f.get("coleccion")]
    assert not sin, f"{len(sin)} precios sin colección: el primero es {sin[:1]}"
    sueltas_s = {s2.get("coleccion") for s2 in t["series"]} - declaradas
    assert not sueltas_s, f"hay series de colecciones que no existen: {sueltas_s}"


def test_LA_PANTALLA_NO_MEZCLA_DOS_COLECCIONES():
    """El día que entren Madera y Laca, una tabla que no filtre por colección
    enseñaría las tres tarifas revueltas — con los mismos altos y anchos, y
    precios que no son."""
    cuerpo = sin_comentarios(_lee(PANTALLA))
    matriz = _bloque(cuerpo, "const matrizPuertas = useMemo", "}, [coleccionPuerta, seriePuerta, cantoActivo]);")
    assert "f.coleccion === coleccionPuerta" in matriz, (
        "la matriz no filtra por colección")
    panel = _bloque(cuerpo, 'data-testid="acb-puertas"', "\n          ) : (seccion === 'blum'")
    assert "s2.coleccion === coleccionPuerta" in panel, (
        "el desplegable de series ofrece las de todas las colecciones")
    assert 'data-testid="acb-puertas-coleccion"' in panel, (
        "la colección no se ve en pantalla, y el master pidió que se llamara CANTEADO")
    add = _bloque(cuerpo, "const addPuertaToCart", "\n  };")
    assert "coleccion: coleccionPuerta" in add, (
        "la línea del carrito no dice de qué colección es el frente: al pedir a "
        "ACB no se sabría si es canteado, madera o laca")


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
