# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LA TARIFA DE MADERA DE ACB — LA TERCERA COLECCIÓN.

El master, 04/09/2026: «también tiene otras colecciones en puertas de madera,
puertas laca». Esta es la madera, páginas 17 a 36 de la tarifa del grupo ACB:
71 modelos, siete grupos, 1.558 precios de matriz.

LA MADERA TIENE UNA VUELTA MÁS QUE LA LACA, y es la que cuesta dinero. En la
laca el GRUESO decidía el grupo; aquí lo decide la CHAPA:

    precio = matriz(GRUPO, acabado, alto, ancho)
             × (1 + recargo del modelo)
             × (1 + recargo de la chapa)

Un MADRID en fresno es GRUPO 1 y en abeto tricapa es GRUPO 7. No es un
porcentaje de diferencia: es OTRA MATRIZ ENTERA. Coger la primera línea del
modelo tarifa el abeto al precio del fresno, y ninguno de los dos números
parece raro.

Cinco formas de equivocarse, todas sin dar un error:

1. LA CHAPA NO CAMBIA EL GRUPO, solo el recargo. Falso en MADRID, PALENCIA,
   PALMA y VEGA — los cuatro tienen una línea de abeto en el grupo 7 y otra de
   chapa en el 1, el 3 o el 2.

2. EL RECARGO DE LA CHAPA SE OLVIDA. NOGAL +10 %, ROBLE NUDOS +15 %, en TODOS
   los grupos (pág. 18 y el pie de las catorce páginas de matriz). Sin él, un
   frente de nogal se cobra al precio del de fresno.

3. AL GRUPO 7 SE LE PIDE LA COLUMNA B O C. No las tiene: el abeto tricapa va
   solo en crudo y sus acabados son recargos (pigmento +20 %, poro arenado
   +10 %, tinte +10 %).

4. LA VITRINA SE COBRA IGUAL EN TODOS. Solo once modelos llevan el +20 %
   (pág. 18), y palillería y celosía van a +50 % en cualquiera. Una vitrina mal
   tarifada se cobra un 20 % o un 50 % por debajo.

5. UN MODELO ANTIGUO SE DA POR IMPOSIBLE, o al revés, se da por confirmado. La
   tarifa les da su GRUPO pero NO dice en qué chapas los fabrica ACB. Se
   tarifan —el precio se sabe— y se marcan `chapaSinConfirmar`, para que se
   pregunte antes de cursar.

Y de los 1.558 números se comprueba la FORMA, que es lo único que una máquina
puede comprobar sin el PDF delante: el precio sube con el ancho, crudo ≤ grupo
B ≤ grupo C, la rejilla es la misma en los siete grupos y el costado de nudos y
nogal cuesta más que el de roble y fresno.
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
DATOS = os.path.join(SRC, "data", "acbMadera.js")
GENERADOR = os.path.join(RAIZ, "herramientas", "tarifa_acb_madera.py")

TOL = 0.011

# LA ÚNICA INVERSIÓN COMPROBADA CONTRA EL PDF, y es de ACB: el ATAMBORADO baja
# de 382,63 € («HASTA 9000») a 376,99 € («HASTA 9500»). Mirado a 400 dpi en la
# pág. 36. Lista CERRADA: una inversión nueva se pone roja, que es el fallo que
# se busca.
INVERSIONES_DE_LA_TARIFA = {("atamborado", "HASTA 9500")}


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _madera():
    """EJECUTA el fichero de datos en node y devuelve lo que exporta.

    EJECUTAR y no leer: una tabla que el generador declara y no vuelca se lee
    igual de bien que una correcta y solo revienta cuando la función que la usa
    se llama. Pasó el 05/09/2026 con `ACB_CANTOS` del canteado, y se llevó por
    delante Cocina Desmontada en producción.
    """
    if not shutil.which("node"):
        pytest.skip("hace falta node para leer la tarifa de verdad")
    src = re.sub(r"^export const", "const", _lee(DATOS), flags=re.M)
    js = src + """
console.log(JSON.stringify({
  chapas: ACB_MADERA_CHAPAS, chapasAntiguo: ACB_MADERA_CHAPAS_DE_UN_ANTIGUO,
  acabados: ACB_MADERA_ACABADOS, acabadosAbeto: ACB_MADERA_ACABADOS_ABETO,
  carta: ACB_MADERA_CARTA, modelos: ACB_MADERA_MODELOS,
  matrices: ACB_MADERA_MATRICES, complementos: ACB_MADERA_COMPLEMENTOS,
  costados: ACB_MADERA_COSTADOS, colsCostado: ACB_MADERA_COSTADOS_ACABADOS,
  pct: {
    vitrina: ACB_MADERA_VITRINA_PCT,
    palilleria: ACB_MADERA_VITRINA_PALILLERIA_PCT,
    pigmentadoFuera: ACB_MADERA_PIGMENTADO_FUERA_DE_CARTA_PCT,
    tinteFuera: ACB_MADERA_TINTE_FUERA_DE_CARTA_PCT,
    veta: ACB_MADERA_VETA_CONSECUTIVA_PCT, xolid: ACB_MADERA_XOLID_PCT,
    tintePatina: ACB_MADERA_TINTE_PATINA_PCT,
    pigmentoPatina: ACB_MADERA_PIGMENTO_PATINA_PCT,
    poro: ACB_MADERA_PORO_ARENADO_PCT, costado30: ACB_MADERA_COSTADO_30MM_PCT,
  },
  vitrinaMas20: ACB_MADERA_VITRINA_MAS_20,
  costadoAbeto: ACB_MADERA_COSTADO_ABETO,
  medidaEspecial: ACB_MADERA_MEDIDA_ESPECIAL,
  // SE LLAMAN TODAS LAS FUNCIONES QUE EL FICHERO EXPORTA.
  fn: {
    chapasMadrid: chapasDeModeloACBMadera('MADRID').map((c) => c.id),
    chapasAsturias: chapasDeModeloACBMadera('ASTURIAS').map((c) => c.id),
    chapasDeUnoQueNoExiste: chapasDeModeloACBMadera('NO_EXISTE'),
    madridFresno: lineaDeModeloACBMadera('MADRID', 'fresno'),
    madridAbeto: lineaDeModeloACBMadera('MADRID', 'abeto'),
    madridAlder: lineaDeModeloACBMadera('MADRID', 'alder'),
    asturiasNogal: lineaDeModeloACBMadera('ASTURIAS', 'nogal'),
    asturiasAbeto: lineaDeModeloACBMadera('ASTURIAS', 'abeto'),
    asturiasAlder: lineaDeModeloACBMadera('ASTURIAS', 'alder'),
    baseG1: precioBaseMaderaACB(1, 'crudo', 558, 248),
    baseG1c: precioBaseMaderaACB(1, 'grupoC', 1598, 598),
    baseG7: precioBaseMaderaACB(7, 'crudo', 138, 248),
    baseG7pidiendoB: precioBaseMaderaACB(7, 'grupoB', 138, 248),
    baseG3reparada: [precioBaseMaderaACB(3, 'crudo', 278, 498),
                     precioBaseMaderaACB(3, 'grupoB', 278, 498),
                     precioBaseMaderaACB(3, 'grupoC', 278, 498)],
    baseG5reparada: [precioBaseMaderaACB(5, 'crudo', 898, 398),
                     precioBaseMaderaACB(5, 'grupoB', 898, 398),
                     precioBaseMaderaACB(5, 'grupoC', 898, 398)],
    baseMedidaQueNoExiste: precioBaseMaderaACB(1, 'crudo', 418, 248),
    baseGrupoQueNoExiste: precioBaseMaderaACB(9, 'crudo', 558, 248),
    madridFresnoCrudo: precioMaderaACB('MADRID', 'fresno', 'crudo', 558, 248),
    madridNogal: precioMaderaACB('MADRID', 'nogal', 'crudo', 558, 248),
    madridNudos: precioMaderaACB('MADRID', 'robleNudos', 'crudo', 558, 248),
    madridAbetoPrecio: precioMaderaACB('MADRID', 'abeto', 'crudo', 558, 248),
    madridAbetoPigmento: precioMaderaACB('MADRID', 'abeto', 'crudo', 558, 248,
                                         { acabadoAbeto: 'pigmento' }),
    madridAbetoPidiendoC: precioMaderaACB('MADRID', 'abeto', 'grupoC', 558, 248),
    madridVitrina: precioMaderaACB('MADRID', 'fresno', 'crudo', 558, 248,
                                   { vitrina: true }),
    androsVitrina: precioMaderaACB('ANDROS', 'fresno', 'crudo', 558, 248,
                                   { vitrina: true }),
    androsSinVitrina: precioMaderaACB('ANDROS', 'fresno', 'crudo', 558, 248),
    madridPalilleria: precioMaderaACB('MADRID', 'fresno', 'crudo', 558, 248,
                                      { vitrinaPalilleria: true }),
    duelasAbeto: precioMaderaACB('DUELAS', 'abeto', 'crudo', 558, 248),
    asturiasPrecio: precioMaderaACB('ASTURIAS', 'fresno', 'crudo', 558, 248),
    asturiasEnAbeto: precioMaderaACB('ASTURIAS', 'abeto', 'crudo', 558, 248),
    modeloQueNoExiste: precioMaderaACB('NO_EXISTE', 'fresno', 'crudo', 558, 248),
    tramoRF: tramoCostadoACBMadera('robleFresno', 2400),
    tramoNN: tramoCostadoACBMadera('nudosNogal', 2400),
    tramoBorde: tramoCostadoACBMadera('robleFresno', 2000),
    tramoEnorme: tramoCostadoACBMadera('robleFresno', 20000),
    tramoTablaQueNoExiste: tramoCostadoACBMadera('caoba', 2400),
  },
}));"""
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8",
                                     delete=False) as fh:
        fh.write(js)
        ruta = fh.name
    try:
        r = subprocess.run(["node", ruta], capture_output=True, text=True, timeout=120)
    finally:
        os.unlink(ruta)
    assert r.returncode == 0, f"la tarifa de madera no se puede leer: {r.stderr[-500:]}"
    return json.loads(r.stdout)


def test_EL_PRECIO_SUBE_CON_EL_ANCHO_EN_LOS_SIETE_GRUPOS():
    """La propiedad que caza casi cualquier dígito mal leído. 1.558 casillas."""
    t = _madera()
    for grupo, bloques in t["matrices"].items():
        for b in bloques:
            for aid, col in b["precios"].items():
                assert len(col) == len(b["anchos"]), (
                    f"grupo {grupo} alto {b['altos']} {aid}: {len(col)} precios "
                    f"para {len(b['anchos'])} anchos")
                for (w1, v1), (w2, v2) in zip(zip(b["anchos"], col),
                                              list(zip(b["anchos"], col))[1:]):
                    assert v1 - v2 <= TOL, (
                        f"grupo {grupo} alto {b['altos']} {aid}: el de {w2} de "
                        f"ancho ({v2} €) cuesta menos que el de {w1} ({v1} €)")


def test_CRUDO_MENOS_QUE_GRUPO_B_MENOS_QUE_GRUPO_C():
    """El orden de las tres columnas es fijo en toda la tarifa. Si una casilla
    lo rompiera, sería que dos columnas están cambiadas — y entonces todo un
    acabado se estaría cobrando al precio de otro."""
    t = _madera()
    for grupo, bloques in t["matrices"].items():
        for b in bloques:
            if "grupoB" not in b["precios"]:
                continue
            for i, w in enumerate(b["anchos"]):
                c = b["precios"]["crudo"][i]
                gb = b["precios"]["grupoB"][i]
                gc = b["precios"]["grupoC"][i]
                assert c - TOL <= gb and gb - TOL <= gc, (
                    f"grupo {grupo} {b['altos']}x{w}: crudo/B/C no van de menos "
                    f"a más ({c}, {gb}, {gc})")


def test_LA_REJILLA_ES_LA_MISMA_EN_LOS_SIETE():
    """Los siete grupos tienen los mismos altos y anchos: 82 casillas, 11
    bloques. La madera NO lleva el bloque de 418 que sí tienen el canteado y la
    laca — pedirle un 418 tiene que dar `null`, no el precio del alto de al
    lado."""
    t = _madera()
    ref = [(b["altos"], b["anchos"]) for b in t["matrices"]["1"]]
    assert len(ref) == 11
    for g in map(str, range(2, 8)):
        assert [(b["altos"], b["anchos"]) for b in t["matrices"][g]] == ref, (
            f"el grupo {g} no tiene la misma rejilla que el grupo 1")
    assert t["fn"]["baseMedidaQueNoExiste"] is None, (
        "la madera no tiene el alto 418 y aquí devuelve un precio")
    assert t["fn"]["baseGrupoQueNoExiste"] is None


def test_LA_CHAPA_PUEDE_CAMBIAR_EL_GRUPO():
    """UN MADRID EN ABETO TRICAPA ES OTRA MATRIZ, no un porcentaje.

    Cuatro modelos tienen dos líneas: MADRID (abeto → 7, chapa → 1), PALENCIA y
    PALMA (abeto → 7 +15 %, chapa → 3) y VEGA (abeto → 7 +10 %, chapa → 2). Si
    la búsqueda cogiera la primera línea que hubiera, el abeto se tarifaría por
    la tabla del fresno y el número seguiría pareciendo normal."""
    t = _madera()
    fn = t["fn"]
    assert fn["madridFresno"]["grupo"] == 1
    assert fn["madridAbeto"]["grupo"] == 7, (
        "el MADRID de abeto tricapa es del grupo 7, no del 1")
    assert fn["madridAlder"] is None, (
        "una chapa que ACB no hace en ese modelo tiene que dar `null`, no la "
        "línea de otra")
    dobles = {m["nombre"] for m in t["modelos"] if len(m["lineas"]) > 1}
    assert dobles == {"MADRID", "PALENCIA", "PALMA", "VEGA"}, (
        f"los modelos que cambian de grupo según la chapa son cuatro y aquí "
        f"salen {sorted(dobles)}")
    # Y el precio sale distinto de verdad, no solo la línea.
    assert fn["madridFresnoCrudo"] == 35.42
    assert fn["madridAbetoPrecio"] == 40.52
    assert fn["duelasAbeto"] == 48.62, "DUELAS es grupo 7 +20 % (40,52 x 1,20)"


def test_EL_RECARGO_DE_LA_CHAPA_NO_SE_OLVIDA():
    """NOGAL +10 %, ROBLE NUDOS +15 %, en TODOS los grupos (pág. 18 y el pie de
    las catorce páginas de matriz). Sin él, un frente de nogal se cobra al
    precio del de fresno — un 10 % de menos en cada puerta."""
    t = _madera()
    fn = t["fn"]
    pct = {c["id"]: c["recargo"] for c in t["chapas"]}
    assert pct["nogal"] == 10 and pct["robleNudos"] == 15
    assert pct["fresno"] == 0 and pct["roble"] == 0
    assert fn["madridNogal"] == 38.96, (
        f"el nogal no lleva su +10 %: sale {fn['madridNogal']} y tocan 38.96 "
        f"(35,42 x 1,10)")
    assert fn["madridNudos"] == 40.73, (
        f"el roble nudos no lleva su +15 %: sale {fn['madridNudos']} y tocan "
        f"40.73 (35,42 x 1,15)")


def test_EL_GRUPO_7_SOLO_TIENE_CRUDO():
    """El abeto tricapa va en una sola columna y sus acabados son RECARGOS
    (pigmento +20 %, poro arenado +10 %, tinte +10 %), no columnas. Pedirle la
    B o la C sería tarifarlo por una tabla que no existe."""
    t = _madera()
    for b in t["matrices"]["7"]:
        assert set(b["precios"]) == {"crudo"}, (
            f"el grupo 7 tiene las columnas {sorted(b['precios'])}")
    for g in map(str, range(1, 7)):
        for b in t["matrices"][g]:
            assert set(b["precios"]) == {"crudo", "grupoB", "grupoC"}
    fn = t["fn"]
    assert fn["baseG7pidiendoB"] is None
    # Al pedir un frente del grupo 7 con acabado B o C cae en el crudo, que es
    # el ÚNICO precio que ese grupo tiene — no es una aproximación.
    assert fn["madridAbetoPidiendoC"] == fn["madridAbetoPrecio"]
    ids = {a["id"]: a["recargo"] for a in t["acabadosAbeto"]}
    assert ids == {"pigmento": 20, "poroArenado": 10, "tinte": 10}
    assert fn["madridAbetoPigmento"] == 48.62, "40,52 x 1,20"


def test_LA_VITRINA_SOLO_LA_PAGAN_LOS_ONCE_DE_LA_LISTA():
    """Pág. 18: «LAS VITRINAS DE LOS MODELOS MADRID, VEGA, PALMA, SALZBURGO,
    TRIPOLI, LAREDO, HANOI, PALENCIA, BARBADOS, NUBE Y CADAQUÉS SE INCREMENTAN
    UN 20% SOBRE EL VALOR DE LA PUERTA».

    La lista es CERRADA: en los demás modelos la vitrina NO lleva ese recargo,
    así que ampliarla «por si acaso» cobraría de más. Palillería y celosía van
    a +50 % en cualquier modelo."""
    t = _madera()
    fn, pct = t["fn"], t["pct"]
    assert len(t["vitrinaMas20"]) == 11
    assert pct["vitrina"] == 20 and pct["palilleria"] == 50
    nombres = {m["nombre"] for m in t["modelos"]}
    for v in t["vitrinaMas20"]:
        assert v in nombres, f"la lista nombra «{v}», que no es un modelo"
    assert fn["madridVitrina"] == 42.50, "35,42 x 1,20 — MADRID está en la lista"
    assert fn["androsVitrina"] == fn["androsSinVitrina"], (
        "ANDROS no está en la lista de la pág. 18 y le están cobrando el +20 % "
        "de la vitrina")
    assert fn["madridPalilleria"] == 53.13, "35,42 x 1,50"


def test_UN_MODELO_ANTIGUO_SE_TARIFA_PERO_SE_AVISA():
    """La tarifa les da su GRUPO pero NO dice en qué chapas los fabrica ACB.

    Devolverlos como `null` dejaría sin presupuestar unos modelos que están en
    tarifa. Devolverlos callando haría creer que la combinación está
    confirmada. Se tarifan y se marcan.

    Y NO se les ofrece el abeto tricapa: eso no es una chapa más, es el GRUPO 7
    entero — dárselo por bueno tarifaría por otra matriz."""
    t = _madera()
    fn = t["fn"]
    antiguos = [m for m in t["modelos"] if m["antiguo"]]
    assert len(antiguos) == 30
    for m in antiguos:
        assert m["lineas"] and not m["lineas"][0]["chapas"], (
            f"{m['nombre']} es antiguo y la tarifa no dice sus chapas: la lista "
            f"tiene que ir vacía, no copiada de otro modelo")
    assert t["chapasAntiguo"] == ["fresno", "roble", "nogal", "robleNudos"]
    assert fn["chapasAsturias"] == ["fresno", "roble", "nogal", "robleNudos"]
    assert fn["asturiasNogal"]["chapaSinConfirmar"] is True, (
        "un antiguo tarifado sin avisar de que su chapa no está confirmada")
    assert fn["asturiasNogal"]["grupo"] == 3
    assert fn["asturiasAbeto"] is None, (
        "a un modelo antiguo no se le puede dar el abeto tricapa: es el grupo 7")
    assert fn["asturiasAlder"] is None, (
        "el alder lo lleva un solo modelo de la tarifa; ofrecerlo aquí es "
        "inventarse en qué maderas se fabrica una puerta")
    assert fn["asturiasPrecio"] == 47.59, "grupo 3, 558x248"
    assert fn["asturiasEnAbeto"] is None
    # Y un modelo actual NUNCA cae por esa puerta.
    assert fn["madridAlder"] is None
    assert fn["modeloQueNoExiste"] is None
    assert fn["chapasDeUnoQueNoExiste"] == []


def test_LOS_COSTADOS_SON_DOS_TARIFAS_Y_NO_UNA_CON_UN_PORCENTAJE():
    """La pág. 36 trae hecha la tabla de ROBLE NUDOS Y NOGAL. Aplicarle el
    +10/+15 % a la de roble y fresno daría otro número — el recargo de la chapa
    es para las PUERTAS, no para los costados.

    Y el de nudos y nogal cuesta más, que es la madera cara: si se cruzaran,
    sería que las dos tablas están intercambiadas."""
    t = _madera()
    cols = t["colsCostado"]
    assert cols == ["crudo", "grupoB", "grupoC", "atamborado"]
    rf, nn = t["costados"]["robleFresno"], t["costados"]["nudosNogal"]
    assert len(rf) == len(nn) == 19
    for etiqueta, tabla in (("robleFresno", rf), ("nudosNogal", nn)):
        for k, col in enumerate(cols):
            for f1, f2 in zip(tabla, tabla[1:]):
                if (col, f2["hasta"]) in INVERSIONES_DE_LA_TARIFA:
                    continue
                assert f1["precios"][k] - f2["precios"][k] <= TOL, (
                    f"costado {etiqueta}/{col}: «{f2['hasta']}» "
                    f"({f2['precios'][k]} €) cuesta menos que «{f1['hasta']}» "
                    f"({f1['precios'][k]} €)")
    for f1, f2 in zip(rf, nn):
        assert f1["hasta"] == f2["hasta"]
        for k in range(3):
            assert f1["precios"][k] - f2["precios"][k] <= TOL, (
                f"«{f1['hasta']}» {cols[k]}: el costado de nudos y nogal "
                f"({f2['precios'][k]} €) cuesta menos que el de roble y fresno "
                f"({f1['precios'][k]} €) — las dos tablas están cambiadas")
    fn = t["fn"]
    assert fn["tramoRF"]["hasta"] == "HASTA 2500"
    assert fn["tramoNN"]["precios"][0] > fn["tramoRF"]["precios"][0]
    assert fn["tramoBorde"]["hasta"] == "HASTA 2000", (
        "en el borde exacto se paga el tramo que llega hasta ahí")
    assert fn["tramoEnorme"] is None, (
        "por encima del último tramo ACB no lo fabrica: estirar el último "
        "precio sería inventarlo")
    assert fn["tramoTablaQueNoExiste"] is None


def test_LAS_REGLAS_DE_LA_PAGINA_18_VIAJAN_CON_LA_TARIFA():
    """Están escritas ahí y en ningún otro sitio: si no viajan con la tarifa no
    las aplica nadie, y todas son dinero."""
    t = _madera()
    p = t["pct"]
    assert p["pigmentadoFuera"] == 25 and p["tinteFuera"] == 25
    assert p["veta"] == 25 and p["xolid"] == 15
    assert p["tintePatina"] == 10 and p["pigmentoPatina"] == 10
    assert p["poro"] == 10 and p["costado30"] == 25
    assert "puerta lisa" in t["costadoAbeto"], (
        "el costado de abeto tricapa se cobra como puerta lisa, y eso no está "
        "en ninguna tabla: si no viaja aquí, se pierde")
    assert "inmediata superior" in t["medidaEspecial"], (
        "sin esta regla, alguien interpolará una medida que no está")


def test_LA_CARTA_DE_ACABADOS_DICE_QUE_COLUMNA_SE_COBRA():
    """Pág. 20. No es decorativa: es lo que dice si el acabado que pide el
    cliente se cobra por la columna B o por la C, que son precios distintos.

    Y en roble nudos la tarifa salta del H03 al H05: el H04 NO existe. Se copia
    el salto — rellenarlo sería inventarse una referencia."""
    t = _madera()
    c = t["carta"]
    assert set(c) == {"grupoB", "grupoC"}
    todos = [x for fam in c.values() for lista in fam.values() for x in lista]
    assert len(todos) == len(set(todos)), "un código de acabado sale dos veces"
    nudos = c["grupoC"]["Roble nudos"]
    assert "H04" not in nudos and "H03" in nudos and "H05" in nudos, (
        "el H04 no está en la tarifa de ACB y aquí se ha rellenado")
    assert len(c["grupoC"]["Fresno"]) == 29


def test_NINGUN_PRECIO_ABSURDO():
    """Ni negativos, ni ceros, ni una puerta de 4.000 €. Lo que ACB no fabrica
    no se escribe como 0 € (CLAUDE.md, regla 7): se omite."""
    t = _madera()
    for grupo, bloques in t["matrices"].items():
        for b in bloques:
            for aid, col in b["precios"].items():
                for w, v in zip(b["anchos"], col):
                    assert isinstance(v, (int, float)) and 1 <= v <= 400, (
                        f"grupo {grupo} {b['altos']}x{w} {aid} a {v} €")
    for c in t["complementos"]:
        assert len(c["precios"]) == 3, f"{c['nombre']}: {len(c['precios'])} precios"
        p = c["precios"]
        assert p[0] - TOL <= p[1] and p[1] - TOL <= p[2], (
            f"complemento {c['nombre']}: crudo/B/C no suben ({p})")
        for v in p:
            assert 1 <= v <= 1000, f"complemento {c['nombre']} a {v} €"


def test_LAS_DOS_CASILLAS_QUE_SE_LEYERON_A_OJO_SIGUEN_AHI():
    """Al extraer el texto del PDF, dos filas salían con sus precios pegados en
    un solo número y se caían enteras. Se leyeron en la página impresa a 400
    dpi, celda a celda.

    Esta prueba las fija: si un día se regenera la tarifa y esas dos filas
    vuelven a caerse, el hueco no pasa desapercibido — que es justo lo que
    pasaría, porque una matriz con una fila de menos sigue pareciendo una
    matriz."""
    t = _madera()
    assert t["fn"]["baseG3reparada"] == [50.04, 59.61, 62.00], (
        "el grupo 3 de 278x498 (pág. 25 del PDF)")
    assert t["fn"]["baseG5reparada"] == [58.32, 71.69, 74.56], (
        "el grupo 5 de 898x398 (pág. 30 del PDF)")
    for g, alto, n in (("3", 278, 11), ("5", 898, 7)):
        b = next(x for x in t["matrices"][g] if alto in x["altos"])
        assert len(b["anchos"]) == n, (
            f"al grupo {g}, alto {alto}, le faltan anchos: {b['anchos']}")


def test_EL_FICHERO_DE_DATOS_ES_EL_QUE_SALE_DEL_GENERADOR():
    """El generador tiene que SER la fuente, no un adorno. Se REGENERA a un
    temporal y se compara byte a byte. Si esto se pone rojo, lo que hay que
    hacer es tocar el GENERADOR y volver a ejecutarlo, nunca editar el fichero
    de datos a mano."""
    assert os.path.exists(GENERADOR), (
        "el generador de la madera no está en el repo, y el fichero de datos lo "
        "cita: nadie podría volver a generarlo")
    with tempfile.TemporaryDirectory() as tmp:
        destino = os.path.join(tmp, "acbMadera.js")
        r = subprocess.run([sys.executable, GENERADOR, destino],
                           capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, (
            f"el generador de la madera no se ejecuta: {r.stderr[-500:]}")
        with open(destino, encoding="utf-8") as f:
            generado = f.read()
    actual = _lee(DATOS)
    if generado != actual:
        import difflib
        dif = list(difflib.unified_diff(
            generado.splitlines(), actual.splitlines(),
            "lo que genera la herramienta", "lo que hay en el repo", lineterm=""))
        raise AssertionError(
            "el fichero de la madera NO es el que sale del generador. Toca el "
            "generador y vuelve a ejecutarlo; no edites el fichero a mano.\n"
            + "\n".join(dif[:40]))


# ── LA PANTALLA ────────────────────────────────────────────────────────────
from jsx_limpio import sin_comentarios  # noqa: E402

PANTALLA = os.path.join(SRC, "components", "Cascos.jsx")


def _bloque(cuerpo, arranque, cierre):
    i = cuerpo.index(arranque)
    return cuerpo[i:cuerpo.index(cierre, i) + len(cierre)]


def test_LA_MADERA_ES_LA_TERCERA_COLECCION():
    """Canteado, laca y madera: tres tarifas del mismo proveedor, el mismo
    pedido y el mismo carrito. Y comparten casi toda la rejilla de altos y
    anchos, así que una tabla que no filtrara por colección las enseñaría
    revueltas con precios que no son."""
    datos = _lee(os.path.join(SRC, "data", "acbPuertas.js"))
    for c in ('"canteado"', '"laca"', '"madera"'):
        assert c in datos, f"falta la colección {c} en ACB_COLECCIONES"
    cuerpo = sin_comentarios(_lee(PANTALLA))
    assert "from '../data/acbMadera'" in cuerpo


def test_LA_MADERA_NO_SE_PINTA_CON_LOS_CONTROLES_DE_OTRA_COLECCION():
    """Aquí no hay serie ni canto ni grueso: hay MODELO, CHAPA y ACABADO.

    Y los del canteado se comprueban pegados al bloque, no buscando la
    condición suelta: esa cadena aparece en varios sitios del fichero, así que
    un ancla que casa en otro lado no es un ancla."""
    cuerpo = sin_comentarios(_lee(PANTALLA))
    for tid in ("acb-madera-controles", "acb-madera-modelo", "acb-madera-chapa",
                "acb-madera-acabado", "acb-madera-vitrina", "acb-madera-grupo"):
        assert f'data-testid="{tid}"' in cuerpo, f"falta el control {tid}"
    assert ("{coleccionPuerta === 'canteado' && (\n            "
            '<div data-testid="acb-puertas-controles"') in _lee(PANTALLA), (
        "los selectores de serie y canto se siguen enseñando en la madera")


def test_LA_CHAPA_VA_DELANTE_Y_MANDA_EN_EL_GRUPO():
    """Es lo que separa la madera de la laca. Si la pantalla dejara pedida una
    chapa que el modelo no fabrica, la matriz saldría vacía sin decir por qué —
    y si peor, cogiera otra línea, tarifaría por la matriz que no es."""
    cuerpo = sin_comentarios(_lee(PANTALLA))
    linea = _bloque(cuerpo, "const chapaActiva =", ";")
    assert "chapasMadera.some" in linea, (
        f"al cambiar de modelo se queda pedida una chapa que ese modelo puede "
        f"no fabricar: {linea.strip()}")
    linea = _bloque(cuerpo, "const lineaMadera =", ";")
    assert "chapaActiva" in linea, (
        "el grupo no se busca por la chapa: un MADRID de abeto se tarifaría "
        "por la matriz del de fresno")


def test_EL_GRUPO_7_NO_OFRECE_COLUMNAS_QUE_NO_TIENE():
    """El abeto tricapa va solo en crudo. Ofrecer «grupo B» o «grupo C» en la
    pantalla sería dejar pedir una columna que esa matriz no tiene, y el precio
    saldría el del crudo sin que nadie viera la diferencia."""
    cuerpo = sin_comentarios(_lee(PANTALLA))
    linea = _bloque(cuerpo, "const acabadoMaderaActivo =", ";")
    assert "esAbeto ? 'crudo'" in linea, (
        f"al grupo 7 se le está pasando la columna que se pida: {linea.strip()}")
    assert 'data-testid="acb-madera-acabado-abeto"' in cuerpo, (
        "no se pueden elegir los acabados del abeto (pigmento, poro arenado, "
        "tinte), que son los únicos que ese grupo tiene")
    assert "{!esAbeto ? (" in cuerpo, (
        "el desplegable de crudo/B/C se sigue enseñando con el abeto")


def test_LA_MATRIZ_DE_MADERA_NO_REPITE_LA_CUENTA():
    """LOS PRECIOS LOS CALCULA `precioMaderaACB`, NO LA PANTALLA.

    Es quien sabe que la chapa cambia el grupo, que el nogal lleva +10 % y que
    la vitrina solo la pagan once modelos. Copiar esa cuenta en el JSX sería
    tener dos, y el día que una cambie la pantalla enseñaría un precio y el
    pedido llevaría otro."""
    cuerpo = sin_comentarios(_lee(PANTALLA))
    matriz = _bloque(cuerpo, "const matrizPuertas = useMemo", "]);")
    assert "precioMaderaACB(" in matriz
    assert "ACB_MADERA_VITRINA_PCT" not in cuerpo and "* 1.15" not in cuerpo, (
        "los recargos de la madera están escritos en la pantalla: acabarían "
        "existiendo dos")
    assert matriz.count("if (v != null) precios[w] = v;") >= 2, (
        "una medida que ACB no fabrica se estaría pintando como 0 €, que en el "
        "escandallo es un frente gratis (CLAUDE.md, regla 7)")


def test_EL_PEDIDO_DE_MADERA_LLEVA_LA_CHAPA():
    """SIN LA CHAPA EL PEDIDO NO SE PUEDE CURSAR: un MADRID de fresno y uno de
    abeto son dos piezas distintas, de dos matrices distintas.

    Y la FIRMA la incluye: si no, dos líneas del mismo modelo en chapas
    distintas se fundirían en una y el pedido saldría con la mitad."""
    cuerpo = sin_comentarios(_lee(PANTALLA))
    add = _bloque(cuerpo, "const addPuertaToCart", "\n  };")
    assert "coleccionPuerta === 'madera'" in add
    assert "chapa: chapaActiva" in add, "la línea no dice la chapa"
    assert "acbm|${modeloMadera}|${chapaActiva}" in add, (
        "la chapa no entra en la firma: dos chapas distintas se fundirían en "
        "una sola línea")
    assert "chapaSinConfirmar:" in add, (
        "la línea de un modelo antiguo no dice que su chapa no está confirmada "
        "en la tarifa, y se cursaría el pedido como si lo estuviera")


def test_EL_MODELO_ANTIGUO_SE_AVISA_EN_PANTALLA():
    """La tarifa da el grupo pero no dice en qué chapas lo fabrica ACB. Sin el
    aviso, el precio parece tan firme como cualquier otro."""
    cuerpo = sin_comentarios(_lee(PANTALLA))
    assert 'data-testid="acb-madera-sin-confirmar"' in cuerpo
    bloque = _bloque(cuerpo, "{lineaMadera && lineaMadera.chapaSinConfirmar && (", "</div>")
    assert "confirmar" in bloque.lower() and "chapa" in bloque.lower(), (
        "el aviso no dice qué hay que confirmar")
