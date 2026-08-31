# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL DESPIECE DE FRENTES: PIEZA A PIEZA, PARA PODER PEDIR.

El master, 31/08: «en algún sitio debo de poder meter el descuento o los precios
de cada puerta, haciendo un desglose de puertas, frentes, costados, etc., para
luego comprobar y ver si están bien de cara a poder pedir a proveedor».

QUÉ FALTABA. El «Escandallo» que ya había da TOTALES —metros de tablero,
bisagras, horas de taller— y con eso no se pide: al proveedor no se le piden
4,2 m² de puerta, se le piden CINCO puertas de 80×45 y TRES cajones de 14×60. El
dato existía —`despiece` ya devolvía `puertasDetalle` con cada frente y sus
puntos— y no se enseñaba en ninguna parte: vivía dentro del texto de ayuda de
una celda.

LO QUE HACE QUE ESTA LISTA SIRVA PARA PEDIR, Y NO SEA UN ADORNO
---------------------------------------------------------------
1. LAS UNIDADES MULTIPLICAN. Dos muebles B90 iguales son CUATRO puertas
   (CLAUDE.md, regla 4). Pedir de menos no da ningún error: se ve en la obra,
   con el montador delante y la cocina a medio montar.

2. EL COSTE SE REPARTE POR PUNTOS, no a partes iguales. En un BCG60 el cajón de
   14 y la gaveta de 35 no valen lo mismo; repartir a medias daría un precio
   bonito y falso en las dos, y es el precio que se usa para comprobar la
   factura del proveedor.

3. UN FRENTE SIN TARIFA NO VALE CERO. La matriz MV no tiene todas las casillas.
   Se marca y se cuenta aparte: una pieza que sale gratis en la lista se pide
   igual y llega la factura.

4. LOS LINEALES ENTRAN. Costados, laterales y regletas no son frentes y no
   tienen despiece, pero SE PIDEN. Una lista a la que le faltan los costados hay
   que completarla a mano, y entonces no se usa.
"""
import json
import os
import shutil
import subprocess

import pytest

from jsx_limpio import sin_comentarios

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(RAIZ, "frontend", "src")
MODULO = os.path.join(SRC, "utils", "despieceFrentes.js")
CM3 = os.path.join(SRC, "components", "CocinaMontada3.jsx")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _despieza(filas, lineales=()):
    """Ejecuta el módulo REAL en node."""
    if not shutil.which("node"):
        pytest.skip("hace falta node para ejecutar el cálculo de verdad")
    src = _lee(MODULO).replace("export const", "const")
    js = """
%s
const LINEALES = %s;
const filas = %s;
const piezas = despieceDeFrentes(filas, { esLineal: (m) => LINEALES.includes(m.familia) });
console.log(JSON.stringify({ piezas, total: totalesDelDespiece(piezas) }));
""" % (src, json.dumps(list(lineales)), json.dumps(filas))
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"el despiece no se ejecuta: {r.stderr[-400:]}"
    return json.loads(r.stdout)


# Cada frente YA TRAE su coste: lo reparte `despiece`, no la lista (ver
# `test_EL_REPARTO_ESTA_EN_UN_SOLO_SITIO`). Estos datos son la forma que
# devuelve el cálculo de verdad, comprobada ejecutándolo.
B90 = {
    "cod": "B90D/I", "_k": "a", "qty": 2, "pvp": 276, "coste": 225.01,
    "despiece": {"puertaPvp": 612.72, "puerta": 306.36, "puertasDetalle": [
        {"h": 80, "w": 45, "desc": "Puerta 1 (80x45)", "puntos": 92,
         "pvpUd": 306.36, "coste": 153.18},
        {"h": 80, "w": 45, "desc": "Puerta 2 (80x45)", "puntos": 92,
         "pvpUd": 306.36, "coste": 153.18}]},
}
BCG60 = {
    "cod": "BCG60", "_k": "b", "qty": 1, "pvp": 340, "coste": 280,
    "despiece": {"puertaPvp": 200, "puerta": 100, "puertasDetalle": [
        {"h": 14, "w": 60, "desc": "Cajón 1 (14x60)", "puntos": 10,
         "pvpUd": 40.0, "coste": 20.0},
        {"h": 14, "w": 60, "desc": "Cajón 2 (14x60)", "puntos": 10,
         "pvpUd": 40.0, "coste": 20.0},
        {"h": 14, "w": 60, "desc": "Cajón 3 (14x60)", "puntos": 10,
         "pvpUd": 40.0, "coste": 20.0},
        {"h": 35, "w": 60, "desc": "Gaveta inferior (35x60)", "puntos": 20,
         "pvpUd": 80.0, "coste": 40.0}]},
}
COSTADO = {"cod": "CV", "qty": 3, "familia": "COSTADO", "pvp": 39, "coste": 25.5,
           "anchoReal": 61.5, "altoReal": 85, "despiece": {}}


def test_SALE_UNA_LINEA_POR_PIEZA_CON_SUS_MEDIDAS():
    out = _despieza([B90])
    p = out["piezas"]
    assert len(p) == 2, f"un B90 son DOS puertas, y salen {len(p)}"
    assert [x["pieza"] for x in p] == ["Puerta 1", "Puerta 2"]
    assert all(x["alto"] == 80 and x["ancho"] == 45 for x in p), (
        "las puertas de un B90 miden 80×45 cm; sin la medida no se puede pedir")


def test_LAS_UNIDADES_MULTIPLICAN():
    """Dos muebles iguales son cuatro puertas (CLAUDE.md, regla 4). Pedir de
    menos se descubre en la obra, no en la pantalla."""
    out = _despieza([B90])
    assert all(x["uds"] == 2 for x in out["piezas"])
    assert out["total"]["uds"] == 4, (
        f"dos B90 llevan 4 puertas y la lista pide {out['total']['uds']}")
    p = out["piezas"][0]
    assert p["coste"] == round(p["costeUd"] * 2, 2), (
        "el total de la línea no multiplica por las unidades")


def test_EL_COSTE_SE_REPARTE_POR_PUNTOS_Y_NO_A_PARTES_IGUALES():
    """En un BCG60 la gaveta vale el doble que un cajón. A partes iguales
    saldrían los cuatro a 25 €, que es un número bonito y falso — y es el que se
    usaría para comprobar la factura del proveedor."""
    out = _despieza([BCG60])
    por_pieza = {x["pieza"]: x["costeUd"] for x in out["piezas"]}
    assert por_pieza["Cajón 1"] == 20.0, f"el cajón sale a {por_pieza['Cajón 1']}"
    assert por_pieza["Gaveta inferior"] == 40.0, (
        f"la gaveta de 20 puntos tiene que costar el doble que un cajón de 10, "
        f"y sale a {por_pieza['Gaveta inferior']}")
    assert round(sum(por_pieza.values()), 2) == 100.0, (
        "la suma de las piezas no cuadra con el coste de puertas del mueble: la "
        "lista diría una cosa y el presupuesto otra")


def test_LOS_LINEALES_ENTRAN_CON_SU_MEDIDA_DE_VERDAD():
    """Un costado se pide igual que una puerta. Y su medida es la REAL, no el
    escalón de tarifa: el escalón dice lo que cuesta, la medida es lo que se
    corta."""
    out = _despieza([COSTADO], lineales=["COSTADO"])
    p = out["piezas"][0]
    assert p["esLineal"] is True
    assert p["alto"] == 85 and p["ancho"] == 61.5, (
        f"el costado sale a {p['alto']}×{p['ancho']} en vez de 85×61,5: se "
        "cortaría con la medida del escalón de tarifa")
    assert p["uds"] == 3 and p["coste"] == 76.5


def test_UNA_PIEZA_SIN_TARIFA_NO_VALE_CERO_Y_SE_CUENTA_APARTE():
    """La matriz MV no tiene todas las casillas. Una pieza a cero se pide igual
    y llega la factura."""
    raro = {"cod": "AX", "qty": 1, "despiece": {"puertaPvp": 0, "puerta": 0,
            "puertasDetalle": [{"h": 999, "w": 999, "desc": "Puerta rara",
                                "puntos": None, "pvpUd": None, "coste": None,
                                "sinTarifa": True}]}}
    out = _despieza([raro])
    p = out["piezas"][0]
    assert p["sinTarifa"] is True and p["coste"] is None, (
        f"una pieza sin tarifa sale costando {p['coste']} en vez de «no se sabe»")
    assert out["total"]["sinTarifa"] == 1, (
        "las piezas sin tarifa no se cuentan: el total saldría más barato que "
        "la factura que llega después")
    assert out["total"]["coste"] == 0.0


def test_LOS_TOTALES_NO_SE_TRAGAN_LO_QUE_NO_SE_SABE():
    out = _despieza([B90, BCG60, COSTADO], lineales=["COSTADO"])
    t = out["total"]
    assert t["uds"] == 4 + 4 + 3
    assert t["puntos"] == 92 * 2 * 2 + (10 * 3 + 20)
    assert t["coste"] == round(306.36 * 2 + 100 + 25.5 * 3, 2), (
        f"el coste total de la lista no cuadra: {t['coste']}")
    assert t["m2"] > 0, "no se calculan los metros de tablero"


# ── LA PANTALLA ──────────────────────────────────────────────────────────────

def test_LA_LISTA_TIENE_PUERTA_Y_SE_PUEDE_EXPORTAR():
    """Una pantalla sin puerta no existe — ya ha pasado dos veces este mes."""
    cuerpo = sin_comentarios(_lee(CM3))
    assert 'data-testid="cm3-boton-frentes"' in cuerpo, (
        "no hay botón que abra el despiece de frentes")
    assert 'data-testid="cm3-panel-frentes"' in cuerpo, "no existe el panel"
    assert "exportarFrentes" in cuerpo and 'data-testid="frentes-exportar"' in cuerpo, (
        "la lista no se puede exportar: para pedirle al proveedor habría que "
        "copiarla a mano de la pantalla")
    i = cuerpo.index('data-testid="cm3-boton-frentes"')
    boton = cuerpo[cuerpo.rindex("<button", 0, i):i]
    assert "setShowFrentes" in boton, "el botón no abre el panel"


def test_EL_DESCUENTO_DE_PUERTAS_SE_TOCA_DESDE_LA_LISTA():
    """Es el dato que decide si la lista sirve para pedir. Tenerlo en otro modal
    obliga a ir y volver comprobando de memoria."""
    cuerpo = sin_comentarios(_lee(CM3))
    for testid in ("frentes-dto1", "frentes-dto2"):
        assert testid in cuerpo, f"falta el campo «{testid}» en el despiece"


def test_EL_COSTE_DE_COMPRA_SE_VA_CON_EL_CANDADO():
    """La lista se puede estar enseñando con alguien delante. Las medidas y las
    unidades salen siempre —son lo que se pide—; los euros, no (reglas 5 y 9)."""
    cuerpo = sin_comentarios(_lee(CM3))
    i = cuerpo.index('data-testid="cm3-panel-frentes"')
    fin = cuerpo.index("})()}", i)
    panel = cuerpo[i:fin]

    # CADA COLUMNA DE DINERO, UNA A UNA. Comprobar que «{verCoste &&» aparece
    # en el panel no vale: hay varios, y quitar uno solo dejaba la prueba en
    # verde con el coste a la vista. Se comprobó rompiéndolo.
    def dentro_del_candado(pos):
        """¿Está `pos` dentro de algún bloque `{verCoste && ...}`?"""
        k = panel.find("{verCoste &&")
        while k != -1:
            prof = 0
            for j in range(k, len(panel)):
                if panel[j] == "{":
                    prof += 1
                elif panel[j] == "}":
                    prof -= 1
                    if prof == 0:
                        if k < pos < j:
                            return True
                        break
            k = panel.find("{verCoste &&", k + 1)
        return False

    import re as _re
    # `(?<!ver)` para no cazar el propio `verCoste`, que es la condición.
    for m in _re.finditer(r"(?<!ver)Coste|costeUd|p\.coste|T\.coste|Puntos|p\.puntos", panel):
        assert dentro_del_candado(m.start()), (
            f"«{m.group(0)}» se enseña fuera del candado (posición {m.start()}): "
            "esta lista se puede estar mirando con alguien delante, y ahí va lo "
            "que le cuesta a la casa (CLAUDE.md, reglas 5 y 9)")
    # Y LAS MEDIDAS, AL REVÉS: no pueden depender del candado. Con el mismo
    # detector, porque mirar hacia atrás hasta el `<th` no valía: envolver la
    # columna en `{verCoste && <th ...>}` dejaba la prueba en verde, y sin las
    # medidas la lista no sirve para pedir. Se comprobó rompiéndolo.
    for medida in ("Alto</th>", "Ancho</th>", "Uds</th>"):
        j = panel.index(medida)
        assert not dentro_del_candado(j), (
            f"la columna «{medida.replace('</th>', '')}» desaparece con el "
            "candado, y es justo lo que hace falta para pedirle al proveedor")


def test_LA_EXPORTACION_TAMPOCO_SE_LLEVA_LOS_EUROS_A_ESCONDIDAS():
    cuerpo = sin_comentarios(_lee(CM3))
    i = cuerpo.index("const exportarFrentes")
    fn = cuerpo[i:cuerpo.index("\n  };", i)]
    assert "verCoste ?" in fn, (
        "el fichero exportado lleva el coste de compra aunque el candado esté "
        "echado: se manda por correo y ahí va lo que le cuesta a la casa")
    assert "sep=;" in fn and "\\uFEFF" in fn, (
        "el CSV no se abre bien en un Excel español (falta el separador o el BOM)")


# ── EL PRECIO DE UNA PIEZA CONCRETA ──────────────────────────────────────────
#
# El master, 31/08, primero: «en algún sitio debo de poder meter el descuento o
# los precios de cada puerta». Se hizo el descuento; después: «móntalo».
#
# EL RIESGO NO ES EL CAMPO, ES QUE HAYA DOS CÁLCULOS. Antes el coste de puertas
# se calculaba de golpe (`pvpPuertas × dto`) y la lista de frentes lo repartía
# DESPUÉS por su cuenta. Con eso, un precio escrito en la lista habría cambiado
# la lista y NO el presupuesto: dos números del mismo mueble, y el que se firma
# es el que no se tocó. Por eso el reparto se mudó dentro de `despiece` y el
# coste del mueble es LA SUMA DE SUS PIEZAS — son el mismo número mirado de dos
# formas, y no se pueden separar.

RENT = os.path.join(SRC, "components", "RentabilidadMV.jsx")


def _mueble(frentes_precio=None):
    """Ejecuta `despiece` DE VERDAD sobre un BCG60 (3 cajones + 1 gaveta)."""
    if not shutil.which("node"):
        pytest.skip("hace falta node para ejecutar el cálculo de verdad")
    cascos = os.path.join(SRC, "data", "cascos.js")
    vp = os.path.join(SRC, "utils", "valorPuntoCascos.js")
    rent = _lee(RENT)
    ini = rent.index("const MAP_CASCO_COLOR")
    fin = rent.index("export default function RentabilidadMV")
    js = """
const fs = require('fs');
const s = fs.readFileSync(%s, 'utf8');
const CASCOS = eval(s.slice(s.indexOf('export const CASCOS ='))
  .replace('export const CASCOS =', '').replace(/;[\\s\\S]*$/, ''));
globalThis.localStorage = { getItem: () => null };
%s
%s
const p = { bisagra: 1.9, pata4: 3.2, colgador: 2.1, cajon: 41.34, gaveta: 54.37,
            soporte: 0.3, mano: 17, dtoPuertas1: 50, dtoPuertas2: 0, dtoCascos: 28 };
const d = despiece({ cod: 'BCG60', altura: '80', familia: 'BAJO_3CAJ_1GAV',
                     frentesPrecio: %s }, p, 'T1', 3.33, 'grafito-19');
console.log(JSON.stringify({ frentes: d.puertasDetalle, puerta: d.puerta, total: d.costeTotal }));
""" % (json.dumps(cascos),
       _lee(vp).replace("export const", "const"),
       rent[ini:fin].replace("export const", "const"),
       json.dumps(frentes_precio or {}))
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=90)
    assert r.returncode == 0, f"`despiece` no se ejecuta: {r.stderr[-500:]}"
    return json.loads(r.stdout)


def test_EL_COSTE_DEL_MUEBLE_ES_LA_SUMA_DE_SUS_PIEZAS():
    """LA PROPIEDAD QUE LO SOSTIENE TODO. Si esto se rompe, la lista de frentes
    y el presupuesto cuentan cosas distintas del mismo mueble — y el que se
    firma es el presupuesto."""
    d = _mueble()
    suma = round(sum(f["coste"] for f in d["frentes"] if f["coste"] is not None), 2)
    assert suma == d["puerta"], (
        f"las piezas suman {suma} y el mueble dice {d['puerta']}: la lista de "
        "frentes y el presupuesto se han separado")


def test_UN_PRECIO_PACTADO_MANDA_Y_LLEGA_AL_COSTE_DEL_MUEBLE():
    """Lo que pidió el master. Si el precio solo cambiara la lista y no el
    presupuesto, el campo sería un adorno peligroso."""
    base = _mueble()
    con = _mueble({"3": "12"})
    assert con["frentes"][3]["coste"] == 12.0, "el precio escrito no se aplica"
    assert con["frentes"][3]["costeManual"] is True, "no se marca como escrito a mano"
    assert con["frentes"][0]["coste"] == base["frentes"][0]["coste"], (
        "escribir el precio de una pieza ha movido el de las demás")
    assert con["puerta"] == round(base["puerta"] - base["frentes"][3]["coste"] + 12.0, 2), (
        f"el coste del mueble no recoge el precio pactado: {con['puerta']}")
    assert con["total"] < base["total"], (
        "el coste total del mueble no se ha movido: el presupuesto seguiría "
        "saliendo con el precio de tarifa")


def test_UN_CERO_A_PROPOSITO_SE_RESPETA():
    """Una puerta que regala el proveedor vale 0, y ese 0 es una decisión. Un
    `|| 0` lo tomaría por «vacío» y volvería a la tarifa — el mismo fallo que
    tuvo la mano de obra del montador (CLAUDE.md, regla 16)."""
    d = _mueble({"3": "0"})
    assert d["frentes"][3]["coste"] == 0 and d["frentes"][3]["costeManual"] is True, (
        "un 0 escrito a propósito se está tomando por «sin escribir»")


def test_UN_PRECIO_IMPOSIBLE_NO_ENTRA_Y_VUELVE_A_TARIFA():
    base = _mueble()
    for malo in ("abc", "-5", "   "):
        d = _mueble({"3": malo})
        assert d["frentes"][3]["coste"] == base["frentes"][3]["coste"], (
            f"«{malo}» se está tomando por un precio")
        assert d["frentes"][3]["costeManual"] is False


def test_SE_PUEDE_VOLVER_A_LA_TARIFA_SIN_BORRAR_LA_LINEA():
    cuerpo = sin_comentarios(_lee(CM3))
    i = cuerpo.index("const setPrecioFrente")
    fn = cuerpo[i:cuerpo.index("\n  }));", i)]
    assert "delete actual[indice]" in fn, (
        "vaciar el precio no lo quita: no habría forma de volver a la tarifa "
        "salvo borrando la línea entera, y con ella el código y el despiece")


def test_EL_REPARTO_ESTA_EN_UN_SOLO_SITIO():
    """El despiece de pantalla NO puede volver a repartir el coste: sería el
    mismo cálculo en dos sitios, y ya sabemos cómo acaba eso."""
    modulo = sin_comentarios(_lee(MODULO))
    # CON LÍMITE DE PALABRA: `d.puertasDetalle` CONTIENE `d.puerta`, así que la
    # comprobación a secas se disparaba contra la línea que sí es correcta.
    import re as _re
    reparte = bool(_re.search(r"d\.puerta\b", modulo)) or "puertaPvp" in modulo
    assert not reparte, (
        "la lista de frentes vuelve a repartir el coste por su cuenta en vez de "
        "leer el que ya trae cada frente: dos cálculos para el mismo número")
    assert "f.coste" in modulo and "f.pvpUd" in modulo


def test_EL_CAMPO_ESTA_EN_LA_LISTA_Y_SOLO_CON_EL_CANDADO():
    cuerpo = sin_comentarios(_lee(CM3))
    assert 'data-testid="frentes-precio-pieza"' in cuerpo, (
        "no hay dónde escribir el precio de una pieza")
    i = cuerpo.index('data-testid="frentes-precio-pieza"')
    assert "setPrecioFrente" in cuerpo[cuerpo.rindex("<input", 0, i):i], (
        "el campo no guarda lo que se escribe")


def test_EL_CABLE_ENTRE_LA_PANTALLA_Y_EL_CALCULO():
    """El eslabón que las pruebas de arriba NO tocan.

    Todas llaman a `despiece` directamente pasándole `frentesPrecio`, así que
    seguirían en verde con el cable cortado: el master escribiría el precio, se
    guardaría en el mueble, y NUNCA llegaría al cálculo. El campo funcionando y
    el presupuesto sin enterarse. Se comprobó rompiéndolo.
    """
    cuerpo = sin_comentarios(_lee(CM3))
    i = cuerpo.index("const costeDetalladoDe")
    fn = cuerpo[i:cuerpo.index("\n};", i)]
    assert "frentesPrecio: m.frentesPrecio" in fn, (
        "los precios escritos a mano no llegan al cálculo: el campo se rellena, "
        "se guarda en el mueble y el presupuesto sigue saliendo con la tarifa")
