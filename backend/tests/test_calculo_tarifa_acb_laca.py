# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LA TARIFA DE LACADOS DE ACB — LA SEGUNDA COLECCIÓN.

El master, 04/09/2026: «todo lo que te estoy pasando de tarifa es un apartado
que se debe de llamar CANTEADO, que son puertas canteadas a cuatro cantos ACB.
TAMBIÉN TIENE OTRAS COLECCIONES EN PUERTAS DE MADERA PUERTAS LACA QUE YA TE
PASARÉ MÁS ADELANTE». Esta es la laca (págs. 5 a 16 de la tarifa del grupo).

LA LACA NO SE TARIFA COMO EL CANTEADO, y ahí está lo que hay que proteger. En
el canteado el precio SALE de la matriz de su serie y ya está. Aquí la matriz
es solo el primer paso:

    precio = matriz(GRUPO, acabado, alto, ancho) × (1 + recargo del modelo)

y encima van, si los hay, el color especial, el XOLID y la decoración. O sea
que un frente mal tarifado aquí no se ve como un número raro: se ve como un
número PLAUSIBLE que no es el que ACB factura. Tres formas de equivocarse, y
las tres cuestan dinero sin dar un solo error:

1. EL GRUESO SE IGNORA. Un ALZIRA de 19 mm es GRUPO 3 a secas y el de 22 mm es
   GRUPO 3 + 5 %. Coger la primera línea del modelo tarifa el de 22 al precio
   del de 19. Por eso `lineaDeModeloACBLaca` devuelve `null` cuando ese grueso
   no se fabrica, en vez de la línea que hubiera.

2. EL COLOR ESPECIAL SE CALCULA SOBRE LA COLUMNA DE COLOR. La pág. 7 dice
   «sobre el precio de blanco en un 25 %». Con el grupo 1 en 18,40 € de blanco
   y 21,23 € de color, hacerlo mal da 26,54 € en vez de 23,00 €: un 15 % de más
   en cada frente, y ni un aviso.

3. LA MEDIDA QUE NO ESTÁ SE INTERPOLA. La pág. 7 dice que una medida especial
   vale lo que la INMEDIATA SUPERIOR. Interpolar da un precio que ACB no
   factura — es exactamente inventarse una cifra (CLAUDE.md, regla 7).

Y como en el canteado, lo que se comprueba de los 1.008 números es la FORMA,
que es lo único que una máquina puede comprobar sin el PDF delante: el precio
sube con el ancho, el brillo cuesta más que el ultramatt, el color más que el
blanco y los grupos van de menos a más en la MISMA casilla.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(RAIZ, "frontend", "src")
DATOS = os.path.join(SRC, "data", "acbLaca.js")
GENERADOR = os.path.join(RAIZ, "herramientas", "tarifa_acb_laca.py")

# Un céntimo, y solo un céntimo. Lo que se caza son dígitos mal leídos, y esos
# fallan por decenas: una tolerancia ancha dejaría pasar justo lo que se busca.
TOL = 0.011

# LA ÚNICA INVERSIÓN COMPROBADA CONTRA EL PDF, y es de ACB, no de la copia:
# el costado a DOS CARAS en blanco mate «HASTA 10500» pone 113,58 € cuando el
# de 10000 vale 133,12 €. Lista CERRADA a propósito: una inversión nueva se
# pone roja, que es el fallo que se busca. Aflojar la tolerancia hasta que deje
# de saltar sería tapar erratas futuras con la excusa de esta.
INVERSIONES_DE_LA_TARIFA = {("dosCaras", "HASTA 10500", "blancoMate")}


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _laca():
    """EJECUTA el fichero de datos en node y devuelve lo que exporta.

    EJECUTAR y no leer: una tabla que el generador declara y no vuelca se LEE
    igual de bien que una correcta, y solo revienta cuando la función que la
    usa se llama. Pasó el 05/09/2026 con `ACB_CANTOS` del canteado — Cocina
    Desmontada abría en «ERROR AL CARGAR EL MÓDULO» con las 23 pruebas de
    aquella tarifa en verde.
    """
    if not shutil.which("node"):
        pytest.skip("hace falta node para leer la tarifa de verdad")
    src = re.sub(r"^export const", "const", _lee(DATOS), flags=re.M)
    js = src + """
console.log(JSON.stringify({
  acabados: ACB_LACA_ACABADOS, acabadosCostado: ACB_LACA_ACABADOS_COSTADO,
  modelos: ACB_LACA_MODELOS, dosGrupos: ACB_LACA_MODELOS_EN_DOS_GRUPOS,
  matrices: ACB_LACA_MATRICES, colores: ACB_LACA_COLORES,
  complementos: ACB_LACA_COMPLEMENTOS, diseno: ACB_LACA_DISENO,
  curvas: ACB_LACA_CURVAS, retro: ACB_LACA_RETRO, costados: ACB_LACA_COSTADOS,
  pct: {
    especial: ACB_LACA_COLOR_ESPECIAL_PCT, xolid: ACB_LACA_XOLID_PCT,
    c22: ACB_LACA_COSTADO_22MM_PCT, c30: ACB_LACA_COSTADO_30MM_PCT,
    aligerado: ACB_LACA_COSTADO_ALIGERADO_PCT,
    atamborado: ACB_LACA_COSTADO_ATAMBORADO_M2,
    junquillos: ACB_LACA_JUNQUILLOS_VITRINA, muestras: ACB_LACA_PANEL_MUESTRAS,
  },
  medidaEspecial: ACB_LACA_MEDIDA_ESPECIAL,
  // SE LLAMAN TODAS LAS FUNCIONES QUE EL FICHERO EXPORTA.
  fn: {
    gruesosAlzira: gruesosDeModeloACBLaca('ALZIRA'),
    gruesosRotterdam: gruesosDeModeloACBLaca('ROTTERDAM'),
    gruesosDeUnoQueNoExiste: gruesosDeModeloACBLaca('NO_EXISTE_ESTE_MODELO'),
    alzira19: lineaDeModeloACBLaca('ALZIRA', 19),
    alzira22: lineaDeModeloACBLaca('ALZIRA', 22),
    alzira25: lineaDeModeloACBLaca('ALZIRA', 25),
    baseG1: precioBaseLacaACB(1, 'blancoBrillo', 138, 248),
    baseG1bis: precioBaseLacaACB(1, 'blancoBrillo', 173, 248),
    baseG3: precioBaseLacaACB(3, 'blancoBrillo', 138, 248),
    baseColorG1: precioBaseLacaACB(1, 'colorBrillo', 138, 248),
    baseMedidaQueNoExiste: precioBaseLacaACB(1, 'blancoBrillo', 598, 248),
    baseGrupoQueNoExiste: precioBaseLacaACB(9, 'blancoBrillo', 138, 248),
    alziraNormal19: precioLacaACB('ALZIRA', 19, 'blancoBrillo', 138, 248),
    alziraNormal22: precioLacaACB('ALZIRA', 22, 'blancoBrillo', 138, 248),
    bombay22: precioLacaACB('BOMBAY', 22, 'blancoBrillo', 138, 248),
    bernaColor: precioLacaACB('BERNA', 22, 'colorBrillo', 138, 248),
    bernaEspecial: precioLacaACB('BERNA', 22, 'colorBrillo', 138, 248,
                                 { colorEspecial: true }),
    bernaXolid: precioLacaACB('BERNA', 22, 'colorBrillo', 138, 248,
                              { xolid: true }),
    bernaAristaViva: precioLacaACB('BERNA', 22, 'colorBrillo', 138, 248,
                                   { decoracionPct: 5 }),
    alziraEnUnGruesoQueNoSeHace: precioLacaACB('ALZIRA', 25, 'blancoBrillo', 138, 248),
    modeloQueNoExiste: precioLacaACB('NO_EXISTE', 22, 'blancoBrillo', 138, 248),
    tramo2400: tramoCostadoACBLaca('unaCara', 2400),
    tramo2000: tramoCostadoACBLaca('unaCara', 2000),
    tramoEnorme: tramoCostadoACBLaca('unaCara', 20000),
    tramoCaraQueNoExiste: tramoCostadoACBLaca('tresCaras', 2400),
  },
}));"""
    # A UN FICHERO, NO A `node -e`: con mil precios el script se pasa del
    # tamaño máximo de la línea de órdenes.
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8",
                                     delete=False) as fh:
        fh.write(js)
        ruta = fh.name
    try:
        r = subprocess.run(["node", ruta], capture_output=True, text=True, timeout=120)
    finally:
        os.unlink(ruta)
    assert r.returncode == 0, f"la tarifa de laca no se puede leer: {r.stderr[-500:]}"
    return json.loads(r.stdout)


def test_EL_PRECIO_SUBE_CON_EL_ANCHO_EN_LOS_TRES_GRUPOS():
    """La propiedad que caza casi cualquier dígito mal leído: un 41,01 escrito
    14,01 rompe la subida. Se comprueba en las tres matrices y en los cuatro
    acabados — 1.008 casillas."""
    t = _laca()
    ids = [a["id"] for a in t["acabados"]]
    for grupo, bloques in t["matrices"].items():
        for b in bloques:
            for aid in ids:
                col = b["precios"][aid]
                assert len(col) == len(b["anchos"]), (
                    f"grupo {grupo} alto {b['altos']} {aid}: {len(col)} precios "
                    f"para {len(b['anchos'])} anchos")
                for (w1, v1), (w2, v2) in zip(zip(b["anchos"], col),
                                              list(zip(b["anchos"], col))[1:]):
                    assert v1 - v2 <= TOL, (
                        f"grupo {grupo} alto {b['altos']} {aid}: el de {w2} de "
                        f"ancho ({v2} €) cuesta menos que el de {w1} ({v1} €)")


def test_EL_GRUPO_SIGNIFICA_ALGO():
    """1 ≤ 2 ≤ 3 en la MISMA casilla, siempre. Es lo único que hace que el
    grupo de un modelo quiera decir algo; si dos matrices se cruzaran, sería
    que una columna está desplazada — y eso no se ve mirando los números."""
    t = _laca()
    ids = [a["id"] for a in t["acabados"]]
    g1, g2, g3 = t["matrices"]["1"], t["matrices"]["2"], t["matrices"]["3"]
    assert len(g1) == len(g2) == len(g3), "las tres matrices no tienen la misma forma"
    for b1, b2, b3 in zip(g1, g2, g3):
        assert b1["altos"] == b2["altos"] == b3["altos"]
        assert b1["anchos"] == b2["anchos"] == b3["anchos"]
        for i, w in enumerate(b1["anchos"]):
            for aid in ids:
                v = [b["precios"][aid][i] for b in (b1, b2, b3)]
                assert v[0] - TOL <= v[1] and v[1] - TOL <= v[2], (
                    f"{b1['altos']}x{w} {aid}: los grupos no van de menos a "
                    f"más ({v})")


def test_EL_BRILLO_CUESTA_MAS_QUE_EL_MATE_Y_EL_COLOR_MAS_QUE_EL_BLANCO():
    """Las cuatro columnas tienen un orden fijo en toda la tarifa. Si una
    casilla lo rompiera, sería que dos columnas están cambiadas — y entonces
    todo un acabado se estaría cobrando al precio del otro."""
    t = _laca()
    for grupo, bloques in t["matrices"].items():
        for b in bloques:
            for i, w in enumerate(b["anchos"]):
                bb = b["precios"]["blancoBrillo"][i]
                bu = b["precios"]["blancoUltramatt"][i]
                cb = b["precios"]["colorBrillo"][i]
                cu = b["precios"]["colorUltramatt"][i]
                sitio = f"grupo {grupo} {b['altos']}x{w}"
                assert bu - bb <= TOL, f"{sitio}: el blanco ultramatt cuesta más que el brillo"
                assert cu - cb <= TOL, f"{sitio}: el color ultramatt cuesta más que el brillo"
                assert bb - cb <= TOL, f"{sitio}: el color cuesta menos que el blanco"


def test_NINGUN_PRECIO_ABSURDO():
    """Ni negativos, ni ceros, ni un frente de 4.000 €. Lo que ACB no fabrica
    no se escribe como 0 € (CLAUDE.md, regla 7): se omite, y la búsqueda
    devuelve `null`."""
    t = _laca()
    for grupo, bloques in t["matrices"].items():
        for b in bloques:
            for aid, col in b["precios"].items():
                for w, v in zip(b["anchos"], col):
                    assert isinstance(v, (int, float)) and 1 <= v <= 400, (
                        f"grupo {grupo} {b['altos']}x{w} {aid} a {v} €, fuera "
                        f"de todo rango razonable para un frente")


def test_EL_GRUESO_MANDA_EN_EL_PRECIO():
    """UN ALZIRA DE 22 MM NO VALE LO QUE EL DE 19.

    El de 19 es GRUPO 3 a secas y el de 22 es GRUPO 3 + 5 %. Si la búsqueda
    cogiera la primera línea del modelo en vez de la del grueso pedido, el de
    22 se tarifaría al precio del de 19 y nadie lo vería: el número es
    plausible, solo que no es el que ACB factura.

    Y un grueso que no se fabrica devuelve `null`, no la línea que hubiera:
    ALZIRA no existe en 25 mm, y pedirlo así no es más barato — es que no
    existe."""
    t = _laca()
    fn = t["fn"]
    assert fn["gruesosAlzira"] == [19, 22]
    assert fn["gruesosRotterdam"] == [19], (
        "ROTTERDAM solo se fabrica en 19 mm según la pág. 6 bis")
    assert fn["gruesosDeUnoQueNoExiste"] == []
    assert fn["alzira19"] == {"grueso": 19, "grupo": 3, "recargo": 0}
    assert fn["alzira22"] == {"grueso": 22, "grupo": 3, "recargo": 5}
    assert fn["alzira25"] is None, (
        "un grueso que ACB no fabrica tiene que dar `null`, no la línea de otro")
    assert fn["alziraEnUnGruesoQueNoSeHace"] is None
    # Y el recargo se aplica de verdad: 21,99 x 1,05 = 23,09.
    assert fn["alziraNormal19"] == 21.99
    assert fn["alziraNormal22"] == 23.09, (
        f"el recargo del grueso no se aplica: {fn['alziraNormal22']} en vez de "
        f"23.09 (21,99 x 1,05)")
    assert fn["bombay22"] == 27.49, "BOMBAY lleva un 25 % (21,99 x 1,25)"


def test_EL_COLOR_ESPECIAL_SE_CALCULA_SOBRE_BLANCO():
    """LA PÁGINA 7 LO DICE: «se incrementarán sobre el precio de blanco en un
    25 %». Sobre BLANCO, no sobre color.

    Con el grupo 1 a 18,40 € de blanco brillo y 21,23 € de color brillo, un
    BERNA de 22 mm (+5 %) especial sale a 18,40 x 1,05 x 1,25 = 24,15 €.
    Hacerlo sobre la columna de color daría 27,86 €: un 15 % de más en cada
    frente, sin un solo aviso.

    Y el XOLID va «sobre tarifa mate», así que fuerza la columna ultramatt:
    20,18 x 1,05 x 1,15 = 24,37 €. Sobre la de brillo daría 25,64 €."""
    t = _laca()
    fn, pct = t["fn"], t["pct"]
    assert pct["especial"] == 0.25
    assert pct["xolid"] == 0.15
    assert fn["baseG1"] == 18.40 and fn["baseColorG1"] == 21.23
    assert fn["bernaColor"] == 22.29, "21,23 x 1,05"
    assert fn["bernaEspecial"] == 24.15, (
        f"el color especial no se está calculando sobre BLANCO: sale "
        f"{fn['bernaEspecial']} y tocan 24.15 (18,40 x 1,05 x 1,25). Sobre la "
        f"columna de color daría 27.86")
    assert fn["bernaXolid"] == 24.37, (
        f"el XOLID no se está calculando sobre la tarifa MATE: sale "
        f"{fn['bernaXolid']} y tocan 24.37 (20,18 x 1,05 x 1,15)")
    # La decoración se suma encima: 22,29 x 1,05 = 23,41.
    assert fn["bernaAristaViva"] == 23.41


def test_LA_MEDIDA_QUE_NO_ESTA_NO_SE_INVENTA():
    """Una medida que no está en la matriz devuelve `null`, no un precio
    interpolado. La pág. 7 dice que una medida especial vale lo que la
    INMEDIATA SUPERIOR, así que interpolar da una cifra que ACB no factura —
    que es exactamente inventarse un número (CLAUDE.md, regla 7).

    El alto 598 solo existe con ancho 598 en toda la tarifa; pedirle un 248 no
    puede devolver el precio del alto de al lado."""
    t = _laca()
    fn = t["fn"]
    assert fn["baseMedidaQueNoExiste"] is None
    assert fn["baseGrupoQueNoExiste"] is None
    assert fn["modeloQueNoExiste"] is None
    # El escalón de costado SUBE al inmediato superior, y en el borde exacto se
    # queda en el suyo. Por encima del último tramo, `null`: estirar el último
    # precio sería inventarlo.
    assert fn["tramo2400"]["hasta"] == "HASTA 2500"
    assert fn["tramo2000"]["hasta"] == "HASTA 2000"
    assert fn["tramoEnorme"] is None
    assert fn["tramoCaraQueNoExiste"] is None


def test_TODOS_LOS_MODELOS_TIENEN_GRUPO_Y_NINGUNO_REPITE_GRUESO():
    """70 modelos. Uno sin grupo no se puede tarifar; uno con el mismo grueso
    dos veces tarifaría por el que apareciera primero, en silencio."""
    t = _laca()
    assert len(t["modelos"]) == 70
    grupos = set(t["matrices"].keys())
    vistos = set()
    for m in t["modelos"]:
        assert m["lineas"], f"{m['nombre']} no dice en qué grupo está"
        assert m["nombre"] not in vistos, f"{m['nombre']} sale dos veces"
        vistos.add(m["nombre"])
        gruesos = [l["grueso"] for l in m["lineas"]]
        assert len(gruesos) == len(set(gruesos)), (
            f"{m['nombre']} repite un grueso: {gruesos}")
        for l in m["lineas"]:
            assert str(l["grupo"]) in grupos, (
                f"{m['nombre']} de {l['grueso']}mm dice grupo {l['grupo']}, "
                f"que no existe")
            assert 0 <= l["recargo"] <= 30
            assert 10 <= l["grueso"] <= 40


def test_EL_MODELO_QUE_SALE_EN_DOS_GRUPOS_ESTA_DECLARADO():
    """LEIDEN sale en dos grupos a la vez en la tarifa de ACB: la pág. 6 y la
    cabecera del GRUPO 1 dicen grupo 1, y la cabecera del GRUPO 3 también lo
    lista. Son 3,59 € por frente en la casilla base.

    Se toma el de la pág. 6, que es la tabla de modelos. Lo que este candado
    protege es que quede DICHO: un dato dudoso sin marcar acaba pareciendo un
    dato firme, y entonces nadie lo va a confirmar con el proveedor."""
    t = _laca()
    assert t["dosGrupos"].get("LEIDEN") == [1, 3], (
        "LEIDEN sale en el grupo 1 y en el 3 de la tarifa de ACB, y eso tiene "
        "que estar escrito en el fichero, no solo en la cabeza de quien lo "
        "transcribió")
    leiden = next(m for m in t["modelos"] if m["nombre"] == "LEIDEN")
    assert [l["grupo"] for l in leiden["lineas"]] == [1], (
        "manda la pág. 6, que es la tabla de modelos")


def test_EL_TIRADOR_APARTE_SOLO_LO_LLEVA_QUIEN_LO_LLEVA():
    """En la pág. 6 el asterisco significa «hay que incluirle el precio del
    tirador (pág. 93)», y solo lo lleva BERNA.

    OJO: el (*) de las cabeceras de las matrices (págs. 8, 10 y 12) es OTRO
    asterisco —dice «consultar grueso e incrementos en pág. 6»— y ahí lo llevan
    casi todos. Confundirlos metería un tirador de 20 € en setenta modelos que
    no lo llevan, o se lo quitaría al único que sí."""
    t = _laca()
    con_tirador = [m["nombre"] for m in t["modelos"] if m["tiradorAparte"]]
    assert con_tirador == ["BERNA"], (
        f"el asterisco de la pág. 6 lo lleva solo BERNA, y aquí salen "
        f"{con_tirador}")


def test_LOS_COLORES_ESPECIALES_ESTAN_SEPARADOS_DE_LOS_ESTANDAR():
    """Un color especial cuesta un 25 % más. Si uno se colara entre los
    estándar se cobraría de menos, y al revés se cobraría de más — las dos
    cosas sin dar ningún error."""
    t = _laca()
    c = t["colores"]
    assert len(c["estandar"]) == 113
    assert len(c["especiales"]) == 8
    assert not (set(c["estandar"]) & set(c["especiales"])), (
        "hay un color en las dos listas")
    for e in c["especiales"]:
        assert e.startswith("MICROARENADO"), (
            f"los especiales de la pág. 7 son los ocho microarenados, y aquí "
            f"sale {e}")
    assert "BLANCO" in c["estandar"]
    # Las decoraciones llevan su porcentaje, y ninguno es cero: una decoración
    # gratis sería una que no se factura.
    nombres = {d["nombre"] for d in c["decoraciones"]}
    assert {"ARISTA VIVA", "FILO CROMADO", "PATINADO"} <= nombres
    for d in c["decoraciones"]:
        assert 1 <= d["pct"] <= 30, f"{d['nombre']} lleva un {d['pct']}%"


def test_EL_COSTADO_SUBE_CON_LA_SUPERFICIE():
    """Los costados van por cm². Una pieza más grande no puede costar menos: es
    la misma propiedad que caza los dígitos en los frentes.

    Con UNA excepción comprobada contra el PDF, y es de ACB: el costado a dos
    caras en blanco mate «HASTA 10500» pone 113,58 € cuando el de 10000 vale
    133,12 €. Se copia lo que el proveedor factura, no lo que debería."""
    t = _laca()
    ids = [a["id"] for a in t["acabadosCostado"]]
    assert len(ids) == 6, (
        "la tabla de costados tiene SEIS columnas: allí el color especial tiene "
        "columna propia, así que sobre un costado no se aplica el 25 %")
    for cara, tabla in t["costados"].items():
        assert len(tabla) == 19
        for aid in ids:
            for f1, f2 in zip(tabla, tabla[1:]):
                v1, v2 = f1["precios"][ids.index(aid)], f2["precios"][ids.index(aid)]
                if (cara, f2["hasta"], aid) in INVERSIONES_DE_LA_TARIFA:
                    continue
                assert v1 - v2 <= TOL, (
                    f"costado {cara}/{aid}: «{f2['hasta']}» ({v2} €) cuesta "
                    f"menos que «{f1['hasta']}» ({v1} €)")


def test_LOS_RECARGOS_DE_LA_TARIFA_VIVEN_EN_UN_SOLO_SITIO():
    """Los porcentajes van en el fichero de datos y no escritos a mano en una
    pantalla, para que no acaben existiendo dos. Es el mismo motivo por el que
    el descuento del zócalo del canteado vive con su tarifa."""
    t = _laca()
    p = t["pct"]
    assert p["c22"] == 0.10 and p["c30"] == 0.25, "costados de 22 y 30 mm, pág. 16"
    assert p["aligerado"] == 0.50, "costados aligerados de 5 cm, pág. 16"
    assert p["atamborado"] == 304.19, "atamborados, € /m², pág. 16"
    assert p["junquillos"] == 10.88 and p["muestras"] == 16.32, "págs. 7 y 14"
    assert "inmediata superior" in t["medidaEspecial"], (
        "la regla de la medida especial tiene que viajar con la tarifa: sin "
        "ella, alguien interpolará")


def test_LAS_PIEZAS_SUELTAS_TIENEN_SUS_CUATRO_PRECIOS():
    """Complementos, curvas y retro llevan las mismas cuatro columnas que los
    frentes. Las regletas y columnas de diseño llevan DOS, porque solo se hacen
    en ultramatt — escribirles cuatro sería inventarse dos precios."""
    t = _laca()
    for c in t["complementos"] + t["retro"]:
        assert len(c["precios"]) == 4, f"{c['nombre']}: {len(c['precios'])} precios"
        for v in c["precios"]:
            assert 1 <= v <= 2000, f"{c['nombre']} a {v} €"
    for d in t["diseno"]:
        assert len(d["precios"]) == 2, (
            f"{d['nombre']} solo se hace en ultramatt: dos precios, no "
            f"{len(d['precios'])}")
    grupos = [c["grupo"] for c in t["curvas"]]
    assert len(grupos) == 3 and all("CURVAS" in g for g in grupos)
    for c in t["curvas"]:
        for f in c["filas"]:
            assert len(f["precios"]) == 4


def test_EL_FICHERO_DE_DATOS_ES_EL_QUE_SALE_DEL_GENERADOR():
    """El generador tiene que SER la fuente, no un adorno.

    Se REGENERA a un temporal y se compara byte a byte. Si esto se pone rojo,
    lo que hay que hacer es tocar el GENERADOR y volver a ejecutarlo, nunca
    editar el fichero de datos a mano.

    Y de paso comprueba que el generador VALIDA: se ejecuta entero, y su
    validación es la que dice que la rejilla es la misma en los tres grupos.
    """
    assert os.path.exists(GENERADOR), (
        "el generador de la laca no está en el repo, y el fichero de datos lo "
        "cita: nadie podría volver a generarlo")
    with tempfile.TemporaryDirectory() as tmp:
        destino = os.path.join(tmp, "acbLaca.js")
        r = subprocess.run([sys.executable, GENERADOR, destino],
                           capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, (
            f"el generador de la laca no se ejecuta: {r.stderr[-500:]}")
        with open(destino, encoding="utf-8") as f:
            generado = f.read()
    actual = _lee(DATOS)
    if generado != actual:
        import difflib
        dif = list(difflib.unified_diff(
            generado.splitlines(), actual.splitlines(),
            "lo que genera la herramienta", "lo que hay en el repo", lineterm=""))
        raise AssertionError(
            "el fichero de la laca NO es el que sale del generador. Toca el "
            "generador y vuelve a ejecutarlo; no edites el fichero a mano.\n"
            + "\n".join(dif[:40]))


# ── LA PANTALLA ────────────────────────────────────────────────────────────
from jsx_limpio import sin_comentarios  # noqa: E402

PANTALLA = os.path.join(SRC, "components", "Cascos.jsx")


def _bloque(cuerpo, arranque, cierre):
    i = cuerpo.index(arranque)
    return cuerpo[i:cuerpo.index(cierre, i) + len(cierre)]


def test_LA_LACA_TIENE_SU_PROPIA_COLECCION_EN_LA_PANTALLA():
    """El master, 04/09/2026: «también tiene otras colecciones en puertas de
    madera, puertas laca, que ya te pasaré más adelante». La laca entra como
    UNA COLECCIÓN MÁS de ACB PUERTAS, no como una sección aparte: es el mismo
    proveedor, el mismo pedido y el mismo carrito."""
    from types import SimpleNamespace  # noqa: F401
    datos = _lee(os.path.join(SRC, "data", "acbPuertas.js"))
    assert '"laca"' in datos and '"LACA"' in datos, (
        "la laca no aparece en ACB_COLECCIONES: la pantalla no tendría de "
        "dónde sacar el desplegable")
    cuerpo = sin_comentarios(_lee(PANTALLA))
    assert "from '../data/acbLaca'" in cuerpo, (
        "la pantalla no lee la tarifa de laca")


def test_LA_LACA_NO_SE_PINTA_CON_LOS_CONTROLES_DEL_CANTEADO():
    """Aquí no hay serie ni canto: hay MODELO, GRUESO y ACABADO.

    Dejar los del canteado no daría un error — daría una pantalla que pide un
    canto que la laca no tiene y una serie que no existe en esa colección, y
    la matriz saldría vacía sin decir por qué."""
    cuerpo = sin_comentarios(_lee(PANTALLA))
    for tid in ("acb-laca-controles", "acb-laca-modelo", "acb-laca-grueso",
                "acb-laca-acabado", "acb-laca-decoracion", "acb-laca-especial",
                "acb-laca-xolid"):
        assert f'data-testid="{tid}"' in cuerpo, f"falta el control {tid}"
    # Y LOS DEL CANTEADO SE ESCONDEN. Se comprueba pegado al bloque, no
    # buscando la condición suelta en el fichero: esa cadena aparece también
    # en el aviso de la serie, así que quitar la guarda del selector dejaba la
    # prueba en verde. Un ancla que casa en otro sitio no es un ancla.
    #
    # La guarda dice «=== canteado» y no «!== laca»: con tres colecciones, una
    # negación se queda corta a la cuarta — al entrar la madera habría dejado
    # los selectores de serie y canto puestos ahí también.
    assert ("{coleccionPuerta === 'canteado' && (\n            "
            '<div data-testid="acb-puertas-controles"') in _lee(PANTALLA), (
        "los selectores de serie y canto se siguen enseñando en la laca: se "
        "pediría un canto que la laca no tiene y una serie que no existe en "
        "esa colección")


def test_EL_GRUPO_Y_EL_RECARGO_SE_VEN():
    """Enseñar «GRUPO 3 + 5 %» al lado del modelo no es un adorno: es lo único
    que deja comprobar un precio contra el PDF sin abrirlo. Sin eso, la única
    forma de saber si un frente está bien tarifado es la factura."""
    cuerpo = sin_comentarios(_lee(PANTALLA))
    assert 'data-testid="acb-laca-grupo"' in cuerpo
    bloque = _bloque(cuerpo, 'data-testid="acb-laca-grupo"', "</span>")
    assert "lineaLaca.grupo" in bloque and "lineaLaca.recargo" in bloque, (
        "no se ve de qué grupo sale el precio ni qué recargo lleva")


def test_LA_MATRIZ_DE_LACA_NO_REPITE_LA_CUENTA():
    """LOS PRECIOS LOS CALCULA `precioLacaACB`, NO LA PANTALLA.

    Es quien sabe que el grueso cambia de grupo, que el color especial va sobre
    BLANCO y que el XOLID va sobre mate. Copiar esa cuenta en el JSX sería
    tener dos, y el día que una cambie la pantalla enseñaría un precio y el
    pedido llevaría otro — sin que ninguno de los dos parezca un error."""
    cuerpo = sin_comentarios(_lee(PANTALLA))
    matriz = _bloque(cuerpo, "const matrizPuertas = useMemo", "]);")
    assert "precioLacaACB(" in matriz, (
        "la matriz de laca no pide el precio a la tarifa")
    assert "ACB_LACA_COLOR_ESPECIAL_PCT" not in cuerpo and "* 1.25" not in cuerpo, (
        "el 25 % del color especial está escrito en la pantalla: acabarían "
        "existiendo dos")
    assert "if (v != null) precios[w] = v;" in matriz, (
        "una medida que ACB no fabrica se estaría pintando como 0 €, que en el "
        "escandallo es un frente gratis (CLAUDE.md, regla 7)")


def test_EL_PEDIDO_DE_LACA_LLEVA_EL_GRUESO():
    """SIN EL GRUESO EL PEDIDO NO SE PUEDE CURSAR. Un ALZIRA de 19 y uno de 22
    son dos piezas distintas y a dos precios.

    Y además la FIRMA de la línea lo incluye: si no, dos líneas del mismo
    modelo en gruesos distintos se fundirían en una sola y el pedido saldría
    con la mitad de las puertas."""
    cuerpo = sin_comentarios(_lee(PANTALLA))
    add = _bloque(cuerpo, "const addPuertaToCart", "\n  };")
    assert "coleccionPuerta === 'laca'" in add, (
        "la laca cae por el camino del canteado y va al pedido sin grueso")
    assert "grueso: gruesoActivo" in add, "la línea no dice el grueso"
    assert "acbl|${modeloLaca}|${gruesoActivo}" in add, (
        "el grueso no entra en la firma: dos gruesos distintos se fundirían en "
        "una sola línea")
    assert "acabado: acabadoLaca" in add, (
        "sin el acabado, a ACB no se le puede pedir: blanco brillo y color "
        "ultramatt no valen lo mismo")
    assert "tiradorAparte: modeloLacaObj.tiradorAparte" in add, (
        "la línea no dice si el modelo lleva tirador aparte, y quien monte el "
        "pedido no tiene forma de saberlo")


def test_EL_GRUESO_SE_VUELVE_AL_QUE_EL_MODELO_FABRICA():
    """ROTTERDAM solo se hace en 19 mm. Si al cambiar de modelo se quedara
    pedido un 22, la matriz saldría vacía sin decir por qué — el mismo fallo
    que tenía el canto en el canteado, y se arregla igual."""
    cuerpo = sin_comentarios(_lee(PANTALLA))
    linea = _bloque(cuerpo, "const gruesoActivo =", ";")
    assert "gruesosLaca.includes(gruesoLaca)" in linea, (
        f"al cambiar de modelo se queda pedido un grueso que ese modelo puede "
        f"no fabricar: {linea.strip()}")


def test_EL_TIRADOR_APARTE_SE_AVISA_EN_PANTALLA():
    """BERNA lleva el tirador aparte (pág. 6). Sin el aviso, el frente sale más
    barato de lo que se paga y eso no se ve hasta la factura. NO se suma solo:
    se avisa, porque sumarlo lo cobraría también cuando el cliente no lo
    quiera."""
    cuerpo = sin_comentarios(_lee(PANTALLA))
    assert 'data-testid="acb-laca-nota"' in cuerpo
    bloque = _bloque(cuerpo, "{modeloLacaObj.tiradorAparte && (", "</div>")
    assert "tirador" in bloque.lower(), "el aviso no dice de qué avisa"
