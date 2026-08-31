# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
UN CASCO SIN PRECIO NO CUESTA CERO: ES QUE NO SE SABE LO QUE CUESTA.

El master, 30/08, mirando una CHM60D/I en Cocina Montada 3:
«mira el precio del casco de la columna». Ponía esto:

    Casco 0,00 €  Puertas 49,95 €  Herrajes 12,92 €  M. obra 17,00 €
    Coste 79,87 €     Margen 226,49 € (73,9 %)

La columna se vendía a 306,36 € con un margen del 73,9 %. El casco de esa
columna vale 168,24 € en la tarifa ACB. El margen de verdad era del 19 %.

POR QUÉ PASABA
--------------
ACB NO FABRICA TODO EN TODAS LAS GAMAS, y eso no es un fallo de datos: es la
tarifa. La «Columna Despensa» y la «Semicolumna Despensa» solo existen en
Diseño Grueso (roble 16 / olmo 18) y Especiales Blanco 16. No hay ni una en la
gama «en kit» ni en 19 mm. Así que pedir una columna en GRAFITO —que es el
acabado por defecto— no encontraba precio.

Y lo que hacía entonces era devolver `{ coste: 0 }`.

La reserva estaba escrita: `COLOR_PRIO`, una lista de colores por prioridad,
llevaba ahí desde el primer día. La función que tenía que recorrerla se quedó
en un `return null` seco, y se la llama SIEMPRE sin color, así que devolvía
null siempre y la lista era decorado. El gemelo de esa función en
`ProformaImporter.jsx` sí la recorre: era una copia a la que se le había caído
el cuerpo. Nació así, en el commit que trajo el fichero — o sea que el casco de
TODA columna ha valido 0,00 € desde el día uno.

EL ALCANCE, MEDIDO ANTES DE TOCAR NADA: de las 5 familias de casco que usan las
reglas por 9 acabados, 18 casillas daban 0,00 €. Toda columna y toda
semicolumna en los 7 acabados normales; y al revés, todo bajo y todo alto si se
elegía roble u olmo.

LO QUE SE PROTEGE, Y POR QUÉ CADA COSA
--------------------------------------
1. NUNCA UN CERO. Un cero no da error, no se ve raro y se suma sin protestar.
   Es la regla 7 de CLAUDE.md por su lado más caro: lo que no se sabe no se
   rellena con un número plausible, y el cero es el más plausible de todos
   porque siempre cuadra. Es también lo que ya decía el candado
   `test_calculo_casco_por_medida.py`: «una línea que se ve sin precio se
   corrige; una línea con un precio de aspecto normal se firma».

2. SI LA FAMILIA NO SE FABRICA EN ESE ACABADO, SE COGE LA GAMA EN LA QUE SÍ, Y
   SE MARCA. El número es tarifa ACB de verdad; lo que no es, es del acabado
   pedido. Se marca porque quien presupuesta tiene que decidirlo, no
   enterarse después.

3. EL ORDEN IMPORTA: primero el acabado pedido, y solo si esa familia no existe
   en él, otro. Al revés, un mueble que SÍ existe en grafito podría acabar
   tarifado con el precio de otra gama sin que nadie lo hubiera pedido.

4. LO QUE YA FUNCIONABA NO SE MUEVE. Los bajos, los altos y los fregaderos en
   los acabados normales tienen que dar EXACTAMENTE lo de siempre. El BF60 del
   pantallazo del master daba 40,48 € y tiene que seguir dando 40,48 €.
"""
import json
import os
import shutil
import subprocess

import pytest

from jsx_limpio import sin_comentarios as _limpia_jsx

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(RAIZ, "frontend", "src")
RENT = os.path.join(SRC, "components", "RentabilidadMV.jsx")
CM3 = os.path.join(SRC, "components", "CocinaMontada3.jsx")
REVIEW = os.path.join(SRC, "components", "RelacionReview.jsx")
CASCOS_JS = os.path.join(SRC, "data", "cascos.js")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _sin_comentarios(cuerpo):
    """Este fichero y los que vigila EXPLICAN el fallo citando lo que se busca
    («0,00 €», «coste: 0»). Sin quitar los comentarios, un candado se aprueba a
    sí mismo con su propia explicación — ya ha pasado cinco veces en este repo."""
    return _limpia_jsx(cuerpo)


# ── EJECUTAR EL CÓDIGO DE VERDAD ──────────────────────────────────────────────
#
# No se reescribe la fórmula aquí: se saca `cascoACB` del JSX y se ejecuta en
# node contra el catálogo ACB REAL. Una copia de la fórmula dentro de la prueba
# se separa del original, y entonces el candado aprueba algo que ya no existe.

def _casco(*llamadas):
    if not shutil.which("node"):
        pytest.skip("hace falta node para ejecutar el cálculo de verdad")
    rent = _lee(RENT)
    ini = rent.index("const MAP_CASCO_COLOR")
    fin = rent.index("// Reglas de descomposición")
    fuente = rent[ini:fin].replace("export const", "const")
    js = """
const fs = require('fs');
const s = fs.readFileSync(%s, 'utf8');
const CASCOS = eval(s.slice(s.indexOf('export const CASCOS ='))
  .replace('export const CASCOS =', '').replace(/;[\\s\\S]*$/, ''));
%s
const out = [];
for (const a of %s) { out.push(cascoACB(a[0], a[1], a[2], 1.30, a[3])); }
console.log(JSON.stringify(out));
""" % (json.dumps(CASCOS_JS), fuente, json.dumps(list(llamadas)))
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, f"el cálculo del casco no se ejecuta: {r.stderr[-500:]}"
    return json.loads(r.stdout)


def test_LA_COLUMNA_DEL_MASTER_YA_NO_VALE_CERO():
    """El caso exacto del pantallazo: CHM60D/I, columna de 60 a 200."""
    (col,) = _casco(["Columna Despensa", 600, 2000, None])
    assert col["coste"] is not None, (
        "el casco de la columna sigue sin precio: volvería el 0,00 €")
    assert col["coste"] > 0, f"el casco de la columna vale {col['coste']}"
    assert col["coste"] == 168.24, (
        f"el casco de esa columna vale 168,24 € en la tarifa ACB y sale "
        f"{col['coste']}. Si la tarifa ha cambiado, hay que rehacer esta cifra "
        "a mano mirando el PDF, no ajustar la prueba a lo que salga")


def test_NINGUNA_FAMILIA_QUE_USAN_LAS_REGLAS_DA_CERO_EN_NINGUN_ACABADO():
    """La medición que destapó el tamaño real: 18 casillas de 45 daban 0,00 €.

    Se recorren todas las familias de casco que piden las reglas MV por todos
    los acabados que ofrece la pantalla. Ninguna combinación puede dar cero ni
    quedarse sin precio: cualquiera de las dos cosas es un mueble que se vende
    creyendo que el casco es gratis.
    """
    rent = _lee(RENT)
    import re
    familias = sorted({m.group(2) for m in
                       re.finditer(r"^  ([A-Z_0-9]+):\s*\{[^}]*casco:\s*'([^']+)'",
                                   rent, re.M)})
    assert len(familias) >= 5, f"no se han encontrado las familias: {familias}"
    acabados = [m.group(1) for m in re.finditer(r"^  '([a-z-]+-\d+)':", rent, re.M)]
    assert len(acabados) >= 8, f"no se han encontrado los acabados: {acabados}"

    llamadas = [[fam, 600, 2000 if "olumna" in fam else 800, ac]
                for fam in familias for ac in acabados]
    ceros = [(llamadas[i][0], llamadas[i][3])
             for i, r in enumerate(_casco(*llamadas))
             if r.get("sinPrecio") or not r.get("coste")]
    assert not ceros, (
        f"{len(ceros)} combinaciones familia/acabado siguen sin coste de casco: "
        f"{ceros[:6]}. Cada una es un mueble que se presupuesta como si el "
        "casco fuera gratis, y el margen sale inflado sin dar ningún error")


def test_LO_QUE_YA_FUNCIONABA_NO_SE_MUEVE():
    """Las cifras del propio pantallazo del master. Arreglar la columna no
    puede cambiarle el precio a un bajo que ya estaba bien: eso movería los
    márgenes de todos los presupuestos de la casa."""
    bf60, bajo, alto = _casco(
        ["Bajo Fregadero", 600, 800, "grafito-19"],
        ["Bajo Con Balda", 600, 800, "grafito-19"],
        ["Alto Con Balda", 600, 900, "grafito-19"],
    )
    assert bf60["coste"] == 40.48, (
        f"el BF60 daba 40,48 € en la pantalla del master y ahora da "
        f"{bf60['coste']}: se ha movido un precio que ya era correcto")
    assert bajo["coste"] == 49.37, f"el bajo de 60x80 ha cambiado: {bajo['coste']}"
    assert alto["coste"] == 43.83, f"el alto de 60x90 ha cambiado: {alto['coste']}"
    for r in (bf60, bajo, alto):
        assert not r.get("otroAcabado"), (
            "un mueble que SÍ se fabrica en grafito se está tarifando con el "
            "precio de otra gama: el acabado pedido tiene que ganar siempre")


def test_EL_ACABADO_PEDIDO_MANDA_SOBRE_LA_RESERVA():
    """Si la familia existe en el acabado elegido, se usa ESE, no el primero de
    la lista de prioridad. Un bajo en blanco 16 no puede salir tarifado en
    grafito solo porque el grafito va antes en `COLOR_PRIO`."""
    grafito, blanco = _casco(
        ["Bajo Con Balda", 600, 800, "grafito-19"],
        ["Bajo Con Balda", 600, 800, "blanco-16"],
    )
    assert grafito["coste"] != blanco["coste"], (
        "el acabado elegido no cambia el precio del casco: la reserva se está "
        "comiendo el acabado pedido y todo sale tarifado igual")
    assert not blanco.get("otroAcabado")


def test_LA_SUSTITUCION_SE_MARCA_Y_NO_SE_HACE_A_ESCONDIDAS():
    """Un precio de otra gama es un precio de verdad, pero no el del acabado
    elegido. Sin marca, quien presupuesta no puede saberlo."""
    (col,) = _casco(["Columna Despensa", 600, 2000, "grafito-19"])
    assert col.get("otroAcabado"), (
        "la columna se tarifa con otra gama y no se marca: el precio cambia y "
        "en pantalla no hay nada que lo explique")
    assert col.get("gamaUsada"), "no se dice de qué gama sale el precio"


def test_UNA_FAMILIA_QUE_NO_ESTA_EN_TARIFA_DEVUELVE_NADA_NO_CERO():
    (nada,) = _casco(["Casco Que No Existe", 600, 800, None])
    assert nada["coste"] is None, (
        f"un casco que no está en la tarifa devuelve {nada['coste']} en vez de "
        "«no se sabe». Un cero se suma; un hueco se ve")
    assert nada["sinPrecio"] is True


# ── QUE EL `null` NO SE VUELVA CERO AL SALIR ─────────────────────────────────

def test_EL_COSTE_TOTAL_NO_SE_INVENTA_SIN_EL_CASCO():
    """El casco es UNO de los cuatro sumandos. Si falta, sumar los otros tres da
    un número con toda la pinta de ser el coste —más bajo que el real— y de ahí
    sale un margen inflado. Era exactamente el 73,9 % de la columna."""
    rent = _sin_comentarios(_lee(RENT))
    i = rent.index("const costeTotal")
    bloque = rent[i:i + 260]
    assert "cascoSinPrecio" in bloque and "null" in bloque, (
        "el coste total se sigue calculando aunque el casco no tenga precio")


@pytest.mark.parametrize("ruta,nombre", [
    (CM3, "CocinaMontada3.jsx"), (REVIEW, "RelacionReview.jsx")])
def test_LAS_PANTALLAS_NO_CONVIERTEN_EL_HUECO_EN_UN_CERO(ruta, nombre):
    """`const coste = desp.costeTotal || 0` era el último eslabón: el cálculo
    podía devolver «no se sabe» y la pantalla lo escribía como «cero euros»,
    que es una afirmación."""
    cuerpo = _sin_comentarios(_lee(ruta))
    assert "desp.costeTotal || 0" not in cuerpo, (
        f"{nombre} convierte un coste desconocido en 0 €: el margen de esa "
        "línea sale inflado y no salta ningún error")
    i = cuerpo.index("const coste = desp.costeTotal")
    assert "!= null" in cuerpo[i:i + 90], (
        f"{nombre} no distingue «no se sabe» de «cero»")
    # Y el margen tampoco puede calcularse sobre un coste que no existe.
    # SOLO LA LÍNEA DEL MARGEN. Una ventana de 120 caracteres se comía la línea
    # siguiente (`margenPct`), que también dice `coste == null`, así que romper
    # el margen se salvaba con la comprobación de al lado. Sexta vez.
    j = cuerpo.index("const margen =", i)
    linea = cuerpo[j:cuerpo.index("\n", j)]
    assert "coste == null" in linea, (
        f"{nombre} calcula el margen sin coste: daría el PVP entero como margen")


def test_LAS_LINEAS_SIN_COSTE_SE_CUENTAN_Y_SE_AVISAN():
    """Marcar la fila con «—» no basta: con veinte líneas nadie va contando
    cuáles la llevan, y quien fija el precio mira el total de abajo.

    EL AVISO SE MUDÓ AL PIE el 31/08, al recuperar el desglose original: va
    pegado al margen total, que es donde se lee antes de poner precio. Antes era
    una franja ámbar aparte; el sitio ha cambiado, la obligación no.
    """
    cuerpo = _sin_comentarios(_lee(CM3))
    for marca, queja in (
        ("cm3-marca-otra-gama", "no se marca la línea cuyo casco se tarifa en otra gama"),
        ("cm3-aviso-casco", "no hay aviso de las líneas sin coste junto al total"),
        ("cm3-total-coste", "no se enseña el coste total"),
    ):
        assert marca in cuerpo, queja

    ini = cuerpo.index("const sinCoste = filas.filter")
    assert "m.coste == null" in cuerpo[ini:ini + 120], (
        "las líneas sin coste no se cuentan mirando el coste")

    i = cuerpo.index('data-testid="cm3-aviso-casco"')
    aviso = " ".join(cuerpo[i:i + 700].split())
    assert "sin coste" in aviso, "el aviso no dice qué les pasa a esas líneas"
    assert "MÁS ALTO que el real" in aviso, (
        "el aviso no advierte de en qué DIRECCIÓN miente el margen: si faltan "
        "costes, el margen sale más alto de lo que es, y eso es lo que hay que "
        "saber antes de fijar un precio")

def test_LA_RESERVA_DE_COLORES_SE_RECORRE_DE_VERDAD():
    """`COLOR_PRIO` estuvo escrita y sin ejecutarse desde el primer commit. Una
    lista que nadie recorre es peor que no tenerla: parece que hay una reserva."""
    rent = _sin_comentarios(_lee(RENT))
    i = rent.index("const precioColor")
    cuerpo = rent[i:rent.index("\n};", i)]
    assert "COLOR_PRIO" in cuerpo, (
        "`precioColor` ha vuelto a quedarse sin recorrer la lista de "
        "prioridad: devolverá null siempre y los cascos volverán a valer 0")
    # LA RESERVA TIENE QUE RECORRERSE ANTES DE RENDIRSE. Contar los `return
    # null` no vale: hay dos legítimos (el guardia de entrada y el final). Lo
    # que importa es el ORDEN — un bucle escrito DESPUÉS del último `return
    # null` es código muerto, que es justo como estaba.
    bucle = cuerpo.index("for (const col of COLOR_PRIO)")
    ultimo = cuerpo.rindex("return null")
    assert bucle < ultimo, (
        "el recorrido de `COLOR_PRIO` está detrás del `return null` final: no "
        "se ejecuta nunca y los cascos vuelven a valer 0")
