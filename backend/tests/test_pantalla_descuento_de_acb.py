# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL DESCUENTO DE COMPRA DE ACB, Y EL MODAL QUE NO TENÍA PUERTA.

El master, 30/08: «falta el desglose y el descuento de ACB que metía a mano».

Eran dos cosas, y la segunda es la que no se ve mirando el código de lejos:

1. NO HABÍA DÓNDE METERLO. El coste del casco salía directo de la tarifa ACB,
   sin descuento y sin ningún sitio donde teclearlo. La tarifa del proveedor se
   negocia; el catálogo trae el precio de tarifa y el descuento va aparte.

2. EL MODAL DE DESCUENTOS ESTABA ESCRITO ENTERO Y NO SE ABRÍA NUNCA. Cabecera,
   campos, multiplicador neto, botón de aplicar... y `setShowModalDtos(true)`
   NO APARECÍA EN NINGÚN SITIO del fichero. Es el mismo fallo que ya tuvo
   `AreaCooperativista` (regla 21: «una pantalla sin puerta no existe») y no da
   ningún error: el build pasa, el modal existe, y simplemente no se abre.
   Por eso la primera prueba de aquí es la de la PUERTA.

LO QUE NO PUEDE PASAR NUNCA:

- Que el descuento venga con un valor puesto. Por defecto es CERO: sin tocarlo,
  todos los márgenes ya calculados salen exactamente igual que antes. Un
  descuento que aparece solo mueve el margen de toda la casa sin que nadie lo
  haya decidido, y eso no da ningún error — solo un margen distinto.
- Que toque el PVP. Lo que se negocia es lo que PAGA LA CASA. El PVP de Cocina
  Desmontada es lo que paga el CLIENTE y no se mueve (CLAUDE.md, regla 5: los
  descuentos no salen en nada que vea un cliente).
- Que el botón se vea con el candado echado. Con el candado echado esta pantalla
  se enseña con un cliente delante (reglas 5 y 9).
"""
import json
import os
import re
import shutil
import subprocess

from jsx_limpio import sin_comentarios as _limpia_jsx

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CM3 = os.path.join(RAIZ, "frontend", "src", "components", "CocinaMontada3.jsx")
RENT = os.path.join(RAIZ, "frontend", "src", "components", "RentabilidadMV.jsx")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _sin_comentarios(cuerpo):
    """Los comentarios de estos ficheros EXPLICAN el fallo, y al explicarlo
    citan lo mismo que se busca.

    QUINTA VEZ que este proyecto tropieza con esto, y la primera versión de esta
    prueba volvió a caer: solo quitaba las líneas que EMPIEZAN por `//`, y el
    comentario que hay encima del botón es un bloque `{/* ... */}` de JSX que
    cita `setShowModalDtos(true)` para explicar que no aparecía. O sea que
    borrar el botón entero dejaba la prueba EN VERDE, aprobada por su propia
    explicación. Se comprobó rompiéndolo.
    """
    return _limpia_jsx(cuerpo)


# ── 1. LA PUERTA ──────────────────────────────────────────────────────────────

def test_EL_MODAL_DE_DESCUENTOS_TIENE_PUERTA():
    """El fallo de hoy, tal cual. `showModalDtos` se leía para pintar el modal y
    NADIE lo ponía a `true`: descuentos escritos y jamás abiertos."""
    cuerpo = _sin_comentarios(_lee(CM3))
    assert "setShowModalDtos(true)" in cuerpo, (
        "el modal de descuentos no se abre desde ningún sitio: está escrito "
        "entero y no hay forma de llegar a él. Es el fallo que el master "
        "reportó el 30/08 («el descuento de ACB que metía a mano»)")
    assert "cm3-abrir-descuentos" in cuerpo, (
        "el botón que abre los descuentos ha perdido su marca: sin ella este "
        "candado no puede comprobar dónde vive")


def _bloque_de(cuerpo, apertura):
    """De `{verCoste && (` hasta la llave que lo cierra, contando llaves.

    A ojo no vale: la primera versión de esta prueba buscaba un `)}` entre la
    condición y el botón, y `setShowModalDtos(true)}` LLEVA UN `)}` DENTRO —
    así que daba por fuera un botón que estaba dentro. Un candado que se
    equivoca en la dirección contraria es igual de inútil.
    """
    profundidad = 0
    for k in range(apertura, len(cuerpo)):
        if cuerpo[k] == "{":
            profundidad += 1
        elif cuerpo[k] == "}":
            profundidad -= 1
            if profundidad == 0:
                return apertura, k
    raise AssertionError("el bloque del candado no se cierra")


def test_LA_PUERTA_VIVE_DETRAS_DEL_CANDADO():
    """Un descuento de compra es lo que le cuesta a la casa. Con el candado
    echado esta pantalla se enseña con un cliente delante (reglas 5 y 9): el
    botón tiene que irse con los importes, no quedarse suelto en la barra."""
    cuerpo = _sin_comentarios(_lee(CM3))
    i = cuerpo.index("cm3-abrir-descuentos")
    # Se prueban TODOS los bloques `{verCoste && (` del fichero: basta con que
    # uno de ellos contenga el botón. Buscar solo «el más cercano hacia atrás»
    # daría por bueno un bloque ya cerrado que quedara justo encima.
    dentro = False
    k = cuerpo.find("{verCoste && (")
    while k != -1:
        ini, fin = _bloque_de(cuerpo, k)
        if ini < i < fin:
            dentro = True
            break
        k = cuerpo.find("{verCoste && (", k + 1)
    assert dentro, (
        "el botón de descuentos está FUERA del bloque del candado: se vería con "
        "el candado echado, o sea con un cliente delante mirando la pantalla. "
        "Los descuentos no salen en nada que vea un cliente (CLAUDE.md, regla 5)")


# ── 2. EL DESCUENTO LLEGA AL CÁLCULO ──────────────────────────────────────────

def test_EL_CAMPO_LLEGA_AL_CALCULO_Y_NO_SE_QUEDA_DE_ADORNO():
    """Un campo que se teclea y no viaja es peor que no tenerlo: el master lo
    pone al 28%, ve el número puesto y el margen no se mueve."""
    cuerpo = _sin_comentarios(_lee(CM3))
    assert "cm3-dto-cascos" in cuerpo, "no hay campo donde teclear el descuento de ACB"

    i = cuerpo.index("const paramsCostes")
    corte = cuerpo.index("}), [", i)
    # EL CUERPO Y LAS DEPENDENCIAS, POR SEPARADO. La primera versión rebanaba
    # los dos juntos, así que el `dtoCascos` de las dependencias aprobaba el
    # cuerpo: quitar el campo de los parámetros —el fallo de verdad, el que deja
    # el descuento sin efecto— pasaba en verde. Se comprobó rompiéndolo.
    params = cuerpo[i:corte]
    deps = cuerpo[corte:corte + 80]
    assert "dtoCascos," in params, (
        "`dtoCascos` no se mete en los parámetros del cálculo: el campo se "
        "teclea y el coste no cambia")
    assert "dtoCascos" in deps, (
        "`dtoCascos` no está en las dependencias del useMemo: al cambiarlo, "
        "React reutilizaría los parámetros viejos y el coste no se recalcularía "
        "hasta que se tocara otra cosa. Peor que no cambiar nada: cambia tarde")


def test_SE_GUARDA_ENTRE_SESIONES():
    """Se negocia una vez y se usa en todos los presupuestos. Volver a teclearlo
    cada vez acaba en presupuestos calculados con descuentos distintos."""
    cuerpo = _sin_comentarios(_lee(CM3))
    assert "dto_cascos_acb" in cuerpo, (
        "el descuento de ACB no se guarda: se pierde al recargar y cada "
        "presupuesto saldría con lo que hubiera tecleado el último")


# ── 3. LA ARITMÉTICA, EJECUTANDO EL CÓDIGO DE VERDAD ──────────────────────────

def _ejecuta_el_descuento(valores):
    """Extrae del JSX las líneas REALES que aplican el descuento y las ejecuta.

    No se reescribe la fórmula aquí: una copia de la fórmula en la prueba se
    separa del original y entonces el candado aprueba algo que ya no existe.
    """
    if not shutil.which("node"):
        return None
    rent = _lee(RENT)
    i = rent.index("const dtoCascos = Math.min")
    j = rent.index("\n", rent.index("    : ccBruto;", i))
    bloque = rent[i:j]
    js = """
const ccBruto = { coste: 61.15, pvpDesmontada: 203.83, med: '800x900' };
const out = [];
for (const v of %s) {
  const p = { dtoCascos: v };
  %s
  out.push([cc.coste, cc.pvpDesmontada]);
}
console.log(JSON.stringify(out));
""" % (json.dumps(valores), bloque)
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"el bloque del descuento no se ejecuta: {r.stderr[-400:]}"
    return json.loads(r.stdout)


def test_EL_DESCUENTO_SE_APLICA_AL_COSTE_CON_NUMEROS_DE_VERDAD():
    """El caso del master: un casco de 61,15 € de tarifa."""
    salida = _ejecuta_el_descuento([0, 28, 50])
    if salida is None:
        return
    assert salida[0][0] == 61.15, (
        f"sin descuento el coste ya no sale igual que antes: {salida[0][0]} en "
        "vez de 61,15. Poner el campo NO puede mover un margen ya calculado")
    assert salida[1][0] == 44.03, f"un 28% sobre 61,15 son 44,03, no {salida[1][0]}"
    assert salida[2][0] == 30.58, f"un 50% sobre 61,15 son 30,58, no {salida[2][0]}"


def test_EL_PVP_DEL_CLIENTE_NO_SE_TOCA():
    """Lo que se negocia con ACB es lo que PAGA LA CASA. El PVP de Cocina
    Desmontada es lo que paga el cliente (regla 5)."""
    salida = _ejecuta_el_descuento([0, 28, 50, 100])
    if salida is None:
        return
    pvps = {fila[1] for fila in salida}
    assert pvps == {203.83}, (
        f"el descuento de compra le está bajando el PVP al cliente: {pvps}. "
        "Eso es regalar el margen entero de la negociación")


def test_UN_VALOR_IMPOSIBLE_NO_INVENTA_UN_COSTE():
    """El valor sale de localStorage, o sea de algo que se puede corromper. Un
    negativo NO puede subir el coste y un 150% no puede dejarlo en negativo."""
    salida = _ejecuta_el_descuento([-5, 150, "abc", None])
    if salida is None:
        return
    assert salida[0][0] == 61.15, (
        f"un descuento negativo está SUBIENDO el coste: {salida[0][0]}")
    assert salida[1][0] == 0.0, f"un 150% deja el coste en {salida[1][0]}"
    assert salida[2][0] == 61.15, (
        f"un valor que no es un número se está tomando por un descuento: "
        f"{salida[2][0]}")
    assert salida[3][0] == 61.15


def test_POR_DEFECTO_ES_CERO():
    """Lo más importante de todo. Un descuento que aparece con un valor puesto
    mueve el margen de todos los presupuestos de la casa sin que nadie lo haya
    decidido, y no salta ningún error: solo un margen distinto."""
    rent = _sin_comentarios(_lee(RENT))
    i = rent.index("MV_COSTES_DEFAULT")
    bloque = rent[i:rent.index("\n};", i)]
    m = re.search(r"dtoCascos:\s*([\d.]+)", bloque)
    assert m, "`dtoCascos` no está en los parámetros por defecto"
    assert float(m.group(1)) == 0.0, (
        f"el descuento de ACB viene con un {m.group(1)}% puesto de fábrica")

    cm3 = _sin_comentarios(_lee(CM3))
    j = cm3.index("const [dtoCascos, setDtoCascos]")
    inicial = cm3[j:cm3.index("});", j)]
    assert "|| 0" in inicial and "return 0" in inicial, (
        "el estado del descuento no arranca a cero cuando no hay nada guardado")


# ── 4. EL DESGLOSE LO CUENTA ──────────────────────────────────────────────────

def test_EL_DESGLOSE_DICE_QUE_HAY_DESCUENTO():
    """La otra mitad de lo que pidió el master («falta el desglose»).

    Sin esto el casco baja de 61,15 a 44,03 y en pantalla no hay NADA que lo
    explique: el desglose seguiría sumando —así que el candado del desglose
    seguiría verde— pero el número parecería mal leído.
    """
    cuerpo = _sin_comentarios(_lee(CM3))
    assert "cascoTarifa" in cuerpo, (
        "la pantalla no enseña la tarifa de ACB antes del descuento: no hay "
        "forma de saber de dónde sale el coste del casco")
    i = cuerpo.index("`Casco ${eur(m.despiece?.casco)}`")
    titulo = cuerpo.rindex("title=", 0, i)
    ayuda = cuerpo[titulo:i]
    assert "cascoTarifa" in ayuda and "dtoCascos" in ayuda, (
        "el texto de ayuda del casco no cuenta el descuento aplicado: quien lo "
        "mire verá un coste más bajo sin saber por qué")


def test_EL_CALCULO_DEVUELVE_LO_QUE_LA_PANTALLA_NECESITA():
    """`cascoTarifa` y `dtoCascos` tienen que salir de `despiece`. Si la
    pantalla los calculara por su cuenta, se separarían del cálculo — que es
    justo el fallo del rótulo de los tramos de comisión (regla 16)."""
    rent = _sin_comentarios(_lee(RENT))
    i = rent.index("casco: cc.coste,")
    devuelto = rent[i:i + 260]
    assert "cascoTarifa: ccBruto.coste" in devuelto, (
        "`despiece` no devuelve la tarifa antes del descuento")
    assert "dtoCascos," in devuelto, (
        "`despiece` no devuelve el descuento aplicado: la pantalla tendría que "
        "volver a leerlo por su cuenta y las dos cifras podrían separarse")


def test_LOS_DOS_PROVEEDORES_VAN_SEPARADOS():
    """ACB y MV son dos tarifas distintas. Si el descuento de cascos entrara en
    la cascada de puertas, negociar con uno movería el coste de lo que compra el
    otro — y el error saldría en el margen, no en un fallo."""
    rent = _sin_comentarios(_lee(RENT))
    i = rent.index("const costePuertas")
    formula = rent[i:i + 400]
    assert "dtoCascos" not in formula, (
        "el descuento de los cascos ACB se está aplicando también a las puertas "
        "MV: son dos proveedores y dos tarifas distintas")
