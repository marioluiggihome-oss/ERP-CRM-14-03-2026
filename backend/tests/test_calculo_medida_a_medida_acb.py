# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
TECLEAR LA MEDIDA DE UNA PUERTA Y QUE SALGA EL PRECIO.

El master, 06/09/2026: «necesito poder poner la medida de la puerta tanto el
ancho como el alto y que eso quede ya en la línea de presupuesto o línea de
pedido y que calcule automáticamente el precio... cada puerta, cada frente, con
tirador, sin tirador».

EL PROBLEMA DE FONDO. Las tres tarifas de ACB son rejillas de alto × ancho, y
una puerta real casi nunca cae en una casilla: mide 596 × 397, no 598 × 398. La
tarifa lo resuelve en una línea (pág. 7 de la laca): «El precio para medidas
especiales será igual al precio de la medida inmediata superior». NO SE
INTERPOLA — interpolar da una cifra que ACB no factura (CLAUDE.md, regla 7).

LO QUE LA TARIFA NO DICE, Y HUBO QUE DECIDIR. «Subir cada medida por su lado»
parece lo natural y da resultados absurdos, porque LA REJILLA TIENE HUECOS: la
fila de alto 598 solo se fabrica en 598 de ancho, y la de 418 solo en 298 y 598.
Medido sobre las tres tarifas, en el 96 % de las medidas las dos reglas dan lo
mismo; en el 4 % restante subir por ejes COBRA DE MÁS —una pieza de 560 × 200
se iría a 598 × 598 = 61,91 € cuando 698 × 248 = 35,42 € ya la cubre— y en otros
210 casos ni encuentra casilla, dejando sin presupuestar puertas que ACB sí
fabrica.

LA REGLA ES LA CASILLA MÁS BARATA QUE CUBRE LA PIEZA. Lo que este candado
protege son sus cuatro propiedades, que es lo que hace que sea defendible
delante del proveedor:

1. NUNCA INTERPOLA: el precio devuelto es SIEMPRE uno de los que están escritos
   en la tarifa, nunca un número calculado entre dos.
2. SIEMPRE CUBRE: la casilla facturada es igual o mayor que la pieza en las DOS
   medidas. Facturar una casilla más pequeña es cobrar de menos una pieza que
   hay que fabricar más grande.
3. ES LA MÁS BARATA DE LAS QUE CUBREN: ninguna otra casilla que valga cuesta
   menos. Sin esto se cobraría de más y nadie lo vería.
4. Y CUANDO LA MEDIDA ES DE TARIFA, DA LA MISMA CASILLA. O sea que teclear
   59,8 × 39,8 y pulsar esa casilla en el cuadro tienen que dar EL MISMO PRECIO
   — si se separaran, la pantalla enseñaría dos precios distintos para la misma
   puerta según por dónde se entre.

Y la medida real NO se pierde: el escalón decide lo que CUESTA, el alto y el
ancho de verdad son lo que se fabrica y lo que viaja con el pedido. Es la misma
regla que ya rige en los costados de MV (CLAUDE.md: «EL ESCALÓN DE LA TARIFA NO
ES LA MEDIDA»).
"""
import json
import os
import re
import shutil
import subprocess
import tempfile

import pytest

from jsx_limpio import sin_comentarios

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(RAIZ, "frontend", "src")
MEDIDAS = os.path.join(SRC, "data", "acbMedidas.js")
PANTALLA = os.path.join(SRC, "components", "Cascos.jsx")
DATOS = [os.path.join(SRC, "data", f) for f in
         ("acbPuertas.js", "acbLaca.js", "acbMadera.js")]


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _bloque(cuerpo, arranque, cierre):
    i = cuerpo.index(arranque)
    return cuerpo[i:cuerpo.index(cierre, i) + len(cierre)]


def _node(extra):
    """EJECUTA las funciones de verdad, con las tarifas de verdad."""
    if not shutil.which("node"):
        pytest.skip("hace falta node para ejercitar la tarifa")
    src = "".join(re.sub(r"^export const", "const", _lee(f), flags=re.M)
                  for f in DATOS + [MEDIDAS])
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8",
                                     delete=False) as fh:
        fh.write(src + "\n" + extra)
        ruta = fh.name
    try:
        r = subprocess.run(["node", ruta], capture_output=True, text=True, timeout=180)
    finally:
        os.unlink(ruta)
    assert r.returncode == 0, f"no se puede ejercitar: {r.stderr[-600:]}"
    return json.loads(r.stdout)


# Las tres matrices se arman igual que en la pantalla: { grupos: [{altos, precios}] }.
ARMAR = """
const matrizCanteado = (serie, canto) => {
  const filas = ACB_PUERTAS.filter(f => f.serie === serie && f.canto === canto);
  const grupos = [];
  filas.forEach(f => {
    const clave = f.altos.join('&');
    let g = grupos.find(x => x.clave === clave);
    if (!g) { g = { clave, altos: f.altos, precios: {} }; grupos.push(g); }
    g.precios[f.ancho] = f.precio;
  });
  return { grupos };
};
const matrizDe = (bloques, acabado) => ({ grupos: bloques.map(b => {
  const precios = {};
  b.anchos.forEach((w, i) => { const p = b.precios[acabado][i]; if (p != null) precios[w] = p; });
  return { altos: b.altos, precios };
}) });
const MATRICES = [
  ['canteado gm20/pvc', matrizCanteado('gm20', 'pvc')],
  ['canteado lisos/pvc', matrizCanteado('lisos', 'pvc')],
  ['canteado touch22/alma', matrizCanteado('touch22', 'alma')],
  ['laca G1 blancoBrillo', matrizDe(ACB_LACA_MATRICES[1], 'blancoBrillo')],
  ['laca G3 colorUltramatt', matrizDe(ACB_LACA_MATRICES[3], 'colorUltramatt')],
  ['madera G1 crudo', matrizDe(ACB_MADERA_MATRICES[1], 'crudo')],
  ['madera G7 crudo', matrizDe(ACB_MADERA_MATRICES[7], 'crudo')],
];
const celdasDe = (m) => m.grupos.flatMap(g => g.altos.flatMap(
  a => Object.keys(g.precios).map(w => [a, Number(w), g.precios[w]])));
"""


def test_NUNCA_SE_INTERPOLA_UN_PRECIO():
    """El precio de una medida especial es SIEMPRE uno de los que están escritos
    en la tarifa. Un número calculado entre dos casillas no lo factura ACB: es
    inventarse una cifra, y sale en el presupuesto sin dar ningún error."""
    r = _node(ARMAR + """
    let comprobadas = 0, inventados = [];
    for (const [nom, m] of MATRICES) {
      const precios = new Set(celdasDe(m).map(c => c[2]));
      const altos = [...new Set(celdasDe(m).map(c => c[0]))];
      const anchos = [...new Set(celdasDe(m).map(c => c[1]))];
      const maxA = Math.max(...altos), maxW = Math.max(...anchos);
      for (let a = 100; a <= maxA; a += 7) for (let w = 200; w <= maxW; w += 11) {
        const c = casillaFacturableACB(m, a, w);
        if (!c) continue;
        comprobadas++;
        if (!precios.has(c.precio)) inventados.push(`${nom} ${a}x${w} -> ${c.precio}`);
      }
    }
    console.log(JSON.stringify({ comprobadas, inventados: inventados.slice(0, 5) }));
    """)
    assert r["comprobadas"] > 5000, "apenas se ha probado nada"
    assert not r["inventados"], (
        f"hay precios que no están en la tarifa: {r['inventados']}")


def test_LA_CASILLA_FACTURADA_SIEMPRE_CUBRE_LA_PIEZA():
    """Igual o mayor en las DOS medidas. Facturar una casilla más pequeña que la
    pieza es cobrar de menos algo que hay que fabricar más grande — y como el
    número es plausible, no lo ve nadie."""
    r = _node(ARMAR + """
    let comprobadas = 0, cortas = [];
    for (const [nom, m] of MATRICES) {
      const cs = celdasDe(m);
      const maxA = Math.max(...cs.map(c => c[0])), maxW = Math.max(...cs.map(c => c[1]));
      for (let a = 100; a <= maxA; a += 7) for (let w = 200; w <= maxW; w += 11) {
        const c = casillaFacturableACB(m, a, w);
        if (!c) continue;
        comprobadas++;
        if (c.alto < a || c.ancho < w) cortas.push(`${nom} ${a}x${w} -> ${c.alto}x${c.ancho}`);
      }
    }
    console.log(JSON.stringify({ comprobadas, cortas: cortas.slice(0, 5) }));
    """)
    assert r["comprobadas"] > 5000
    assert not r["cortas"], f"casillas que NO cubren la pieza: {r['cortas']}"


def test_ES_LA_MAS_BARATA_DE_LAS_QUE_CUBREN():
    """Ninguna otra casilla que valga cuesta menos. Sin esto se cobraría de más
    —hasta 26 € en una sola puerta por culpa de las filas huecas de la rejilla—
    y el número seguiría pareciendo normal."""
    r = _node(ARMAR + """
    let comprobadas = 0, caras = [];
    for (const [nom, m] of MATRICES) {
      const cs = celdasDe(m);
      const maxA = Math.max(...cs.map(c => c[0])), maxW = Math.max(...cs.map(c => c[1]));
      for (let a = 100; a <= maxA; a += 7) for (let w = 200; w <= maxW; w += 11) {
        const c = casillaFacturableACB(m, a, w);
        const cubren = cs.filter(x => x[0] >= a && x[1] >= w);
        if (!cubren.length) { if (c) caras.push(`${nom} ${a}x${w}: da casilla y no hay ninguna que cubra`); continue; }
        comprobadas++;
        const min = Math.min(...cubren.map(x => x[2]));
        if (!c) { caras.push(`${nom} ${a}x${w}: hay ${cubren.length} casillas que cubren y no devuelve ninguna`); continue; }
        if (c.precio > min + 1e-9) caras.push(`${nom} ${a}x${w} -> ${c.precio} pudiendo ser ${min}`);
      }
    }
    console.log(JSON.stringify({ comprobadas, caras: caras.slice(0, 5) }));
    """)
    assert r["comprobadas"] > 5000
    assert not r["caras"], f"no se está cogiendo la más barata: {r['caras']}"


def test_TECLEAR_LA_MEDIDA_Y_PULSAR_LA_CASILLA_DAN_LO_MISMO():
    """LA PROPIEDAD QUE DE VERDAD IMPORTA.

    Si se teclea una medida que SÍ está en la tarifa, tiene que salir esa misma
    casilla y ese mismo precio que pulsándola en el cuadro. Si se separaran, la
    pantalla enseñaría dos precios distintos para la misma puerta según por
    dónde se entre, y ninguno de los dos parecería un error."""
    r = _node(ARMAR + """
    let comprobadas = 0, total = 0, distintas = [], noExactas = [];
    for (const [nom, m] of MATRICES) {
      const cs = celdasDe(m); total += cs.length;
      for (const [a, w, p] of cs) {
        const c = casillaFacturableACB(m, a, w);
        comprobadas++;
        if (!c) { distintas.push(`${nom} ${a}x${w}: no devuelve nada y la casilla existe`); continue; }
        if (c.precio !== p) distintas.push(`${nom} ${a}x${w}: ${c.precio} en vez de ${p}`);
        if (!c.exacta) noExactas.push(`${nom} ${a}x${w}`);
      }
    }
    console.log(JSON.stringify({ comprobadas, total, distintas: distintas.slice(0,5), noExactas: noExactas.slice(0,5) }));
    """)
    # SE PRUEBAN TODAS LAS CASILLAS de las siete matrices, no una muestra: es
    # barato y no deja ningun hueco donde esconderse.
    assert r["comprobadas"] == r["total"] > 600, (
        f"no se han recorrido todas las casillas: {r['comprobadas']} de {r['total']}")
    assert not r["distintas"], (
        f"teclear la medida da otro precio que pulsar la casilla: {r['distintas']}")
    assert not r["noExactas"], (
        f"una medida que ES de tarifa se está marcando como especial, y la "
        f"línea diría «se factura como…» sin venir a cuento: {r['noExactas']}")


def test_LO_QUE_ACB_NO_FABRICA_NO_SE_TARIFA():
    """Una pieza más ancha que todo lo que hace ACB no tiene precio: devuelve
    `null` y la pantalla lo dice. Estirar la última casilla sería inventarla."""
    r = _node(ARMAR + """
    const m = MATRICES[0][1];
    console.log(JSON.stringify({
      enorme: casillaFacturableACB(m, 9999, 9999),
      anchaDeMas: casillaFacturableACB(m, 558, 9999),
      altaDeMas: casillaFacturableACB(m, 9999, 248),
      cero: casillaFacturableACB(m, 0, 248),
      negativa: casillaFacturableACB(m, -10, 248),
      texto: casillaFacturableACB(m, 'ancho', 248),
      sinMatriz: casillaFacturableACB(null, 558, 248),
      vacia: casillaFacturableACB({ grupos: [] }, 558, 248),
    }));
    """)
    for k, v in r.items():
        assert v is None, f"«{k}» devuelve {v} y tendría que ser null"


def test_LA_COMA_DEL_TECLADO_ESPANOL_NO_PIERDE_LA_MEDIDA():
    """En un teclado español se teclea «59,6», y `Number('59,6')` es `NaN`. Sin
    admitir la coma, la medida se perdería EN SILENCIO: el campo se queda como
    escrito y el precio no sale, o peor, sale el de otra medida.

    Y lo que no es un número devuelve `null`, NO 0. Un 0 aquí sería un ancho de
    cero, y eso sí se cuela en un presupuesto (CLAUDE.md, regla 7)."""
    r = _node("""
    const casos = [['59,6','cm'],['59.6','cm'],['596','mm'],['59,6','mm'],
      [' 59,6 ','cm'],['','cm'],['   ','cm'],['abc','cm'],['0','cm'],['-5','cm'],
      [null,'cm'],[undefined,'cm'],['1198','mm'],['119,8','cm']];
    console.log(JSON.stringify(casos.map(([t,u]) => [String(t), u, aMmTecleado(t,u)])));
    """)
    d = {(t, u): v for t, u, v in r}
    assert d[("59,6", "cm")] == 596, "la coma se pierde: la medida no llega"
    assert d[("59.6", "cm")] == 596
    assert d[("596", "mm")] == 596
    assert d[("59,6", "mm")] == 60, "en mm, 59,6 mm se redondea a 60"
    assert d[(" 59,6 ", "cm")] == 596, "los espacios de sobra rompen la medida"
    assert d[("119,8", "cm")] == 1198
    # En JavaScript `String(null)` es «null» y `String(undefined)` «undefined»:
    # las claves llegan asi, no como en Python.
    for malo in ("", "   ", "abc", "0", "-5", "null", "undefined"):
        assert d[(malo, "cm")] is None, (
            f"«{malo}» devuelve {d[(malo, 'cm')]} y tiene que ser null, nunca 0")


def test_EL_TIRADOR_TAMBIEN_SUBE_AL_ESCALON_INMEDIATO():
    """El tirador se cobra por el ancho del frente y por SU propio escalón: uno
    de 300 se factura al de 348. Y por encima del último, `null` — que ACB no lo
    haga tan ancho no es que sea gratis."""
    r = _node("""
    const gola = ACB_TIRADORES.find(t => t.id === 'gola').precios;
    console.log(JSON.stringify({
      justo: escalonTiradorACB(gola, 298),
      entre: escalonTiradorACB(gola, 300),
      justoArriba: escalonTiradorACB(gola, 348),
      pequeno: escalonTiradorACB(gola, 100),
      pasado: escalonTiradorACB(gola, 1299),
      ultimo: escalonTiradorACB(gola, 1298),
      cero: escalonTiradorACB(gola, 0),
      sinTabla: escalonTiradorACB(null, 300),
    }));
    """)
    assert r["justo"] == {"ancho": 298, "precio": 13.30, "exacta": True}
    assert r["entre"] == {"ancho": 348, "precio": 14.42, "exacta": False}, (
        "un tirador de 300 se factura al escalón de 348, no interpolado")
    assert r["justoArriba"]["ancho"] == 348
    assert r["pequeno"]["ancho"] == 298, "por debajo del primero, el primero"
    assert r["ultimo"]["ancho"] == 1298
    assert r["pasado"] is None, "ACB no hace el gola de 1299: no es gratis, es que no existe"
    assert r["cero"] is None and r["sinTabla"] is None


# ── LA PANTALLA ────────────────────────────────────────────────────────────

def test_LA_PANTALLA_TIENE_EL_PANEL_DE_MEDIDA():
    cuerpo = sin_comentarios(_lee(PANTALLA))
    for tid in ("acb-medida", "acb-medida-alto", "acb-medida-ancho",
                "acb-medida-uds", "acb-medida-tirador", "acb-medida-add",
                "acb-medida-resumen"):
        assert f'data-testid="{tid}"' in cuerpo, f"falta {tid}"
    # Los campos de medida NO pueden ser `type="number"`: el navegador español
    # rechaza la coma y la medida se pierde antes de llegar al código.
    alto = _bloque(cuerpo, 'data-testid="acb-medida-alto"', "/>")
    assert 'type="text"' in cuerpo[cuerpo.index('data-testid="acb-medida-alto"') - 300:
                                   cuerpo.index('data-testid="acb-medida-alto"')], (
        "el campo del alto es `type=number`: el navegador rechaza «59,6» y la "
        "medida no llega")
    assert "step" not in alto, (
        "se ha puesto un `step`: un frente se corta a milímetro y el navegador "
        "rechazaría una medida legítima")


def test_EL_PRECIO_TECLEADO_SALE_DE_LA_MISMA_MATRIZ_QUE_LA_TABLA():
    """SE LE PASA `matrizPuertas`, la misma que pinta el cuadro. Es lo que hace
    imposible que teclear una medida y pulsar una casilla se separen: si aquí se
    armara otra tabla, un día dirían cosas distintas y ninguna parecería mal."""
    cuerpo = sin_comentarios(_lee(PANTALLA))
    linea = _bloque(cuerpo, "const casillaMedida =", ";")
    assert "casillaFacturableACB(matrizPuertas" in linea, (
        f"el precio tecleado no sale de la matriz que se pinta: {linea.strip()}")
    assert "aMmTecleado(medAlto, unidad)" in cuerpo, (
        "la medida no se pasa a milímetros con la unidad de la pantalla")


def test_LA_LINEA_GUARDA_LA_MEDIDA_REAL_Y_EL_ESCALON():
    """LAS DOS. El escalón decide lo que CUESTA; el alto y el ancho de verdad
    son lo que se fabrica y lo que hay que mandarle al proveedor (CLAUDE.md, «EL
    ESCALÓN DE LA TARIFA NO ES LA MEDIDA»). Guardar solo el escalón haría llegar
    a fábrica una puerta con la medida cambiada."""
    cuerpo = sin_comentarios(_lee(PANTALLA))
    add = _bloque(cuerpo, "const addMedidaToCart", "\n  };")
    assert "alto: medAltoMm" in add and "ancho: medAnchoMm" in add, (
        "la línea no guarda la medida REAL")
    assert "altoFacturado: casillaMedida.alto" in add, (
        "la línea no guarda con qué casilla se factura, y no se podría cotejar "
        "con el proveedor")
    assert "medidaExacta: casillaMedida.exacta" in add
    # LA FIRMA VA POR LA MEDIDA REAL: dos puertas de 596 y de 570 se facturan
    # igual y NO son la misma pieza. Fundirlas dejaría el pedido con la mitad
    # de las puertas y con la medida de una sola.
    firma = _bloque(add, "const sig =", ";")
    assert "${medAltoMm}x${medAnchoMm}" in firma, (
        f"la firma no lleva la medida real: dos piezas distintas que se "
        f"facturan igual se fundirían en una línea: {firma.strip()}")
    assert "medTirador" in firma, (
        "la misma puerta con y sin tirador se fundiría en una sola línea")
    # Y el tirador viaja desglosado, que es como se le pide al proveedor.
    for campo in ("tirador:", "tiradorAncho:", "tiradorPrecio:", "precioFrente:"):
        assert campo in add, f"la línea no desglosa «{campo}»"


def test_UNA_PUERTA_NO_TIENE_GROSOR_NI_COLOR_DE_CASCO():
    """`acabadoOf` pintaba `${l.grosor}mm` para toda línea, y una puerta no
    tiene grosor de tablero: TODAS las líneas de ACB salían con un
    «undefinedmm» pegado al nombre. Y el circulito de color es el del casco.

    No es cosmético: lo que tiene que leerse ahí es el acabado, que es lo que
    falta para pedirle la puerta al proveedor."""
    cuerpo = sin_comentarios(_lee(PANTALLA))
    ac = _bloque(cuerpo, "const acabadoOf = (l) =>", "\n  };")
    assert "if (l.puerta)" in ac, (
        "las líneas de puerta siguen cayendo por la rama de los cascos y "
        "escriben «undefinedmm»")
    i = ac.index("if (l.puerta)")
    assert "grosor" not in ac[i:ac.index("if (l.tirador)", i)], (
        "la rama de las puertas sigue pintando el grosor del tablero")
    assert "!l.puerta && !l.tirador && (" in cuerpo, (
        "el circulito del color del casco se sigue pintando en las puertas, y "
        "hace creer que una puerta tiene color de casco")
