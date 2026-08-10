# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO de las cantidades: UNA ENCIMERA SE VENDE POR METROS.

EL FALLO
--------
Al guardar un presupuesto del digitalizador con dos lineas de ENCIMERA salia
esto en rojo, y nada mas:

    [object Object]

Dos fallos encadenados, y el segundo escondia al primero.

EL DE VERDAD: `quantity` estaba declarado como ENTERO. Una encimera se vende
por METROS LINEALES —3,5 ml es una cantidad de lo mas normal— y Pydantic
rechazaba el guardado entero con un error de validacion.

EL QUE LO ESCONDIA: cuando FastAPI rechaza los datos no contesta con una frase,
contesta con una LISTA de objetos, uno por campo mal. La pantalla hacia
`new Error(d.detail)` y JavaScript convierte un objeto en «[object Object]». O
sea que el servidor decia exactamente que linea y que campo estaban mal, y esa
informacion se tiraba por el camino.

LO QUE SE PROTEGE
-----------------
1. LAS LINEAS DE VENTA ADMITEN DECIMALES. Encimera, zocalo y cantos van por
   metros. Redondear habria sido PEOR que el fallo: cobrar 4 metros cuando se
   han pedido 3,5 es cambiarle el pedido al cliente sin decirselo.

2. EL DESPIECE SIGUE SIENDO ENTERO. Alli una pieza es una pieza: media pieza no
   existe, y admitir 1,5 dejaria entrar un dato imposible en la maquina.

3. UN ERROR DE VALIDACION SE LEE. Con el campo y la linea, que es lo que hace
   que se pueda arreglar solo.
"""
import importlib.util
import os

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND = os.path.join(RAIZ, "backend")
ERRORES_JS = os.path.join(RAIZ, "frontend", "src", "services", "errores.js")
DIGI_JSX = os.path.join(RAIZ, "frontend", "src", "components", "Digitalizador.jsx")


@pytest.fixture(scope="module")
def esquemas():
    """`models/schemas.py` sin arrastrar el resto del backend."""
    import sys
    if BACKEND not in sys.path:
        sys.path.insert(0, BACKEND)
    ruta = os.path.join(BACKEND, "models", "schemas.py")
    spec = importlib.util.spec_from_file_location("_schemas", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


# ─── 1. Las lineas de venta admiten decimales ───────────────────────────────

def test_una_encimera_de_tres_metros_y_medio_se_puede_guardar(esquemas):
    """CANDADO PRINCIPAL. Es EXACTAMENTE el presupuesto que fallo."""
    linea = esquemas.DigitalizadorLine(id="l1", quantity=3.5, description="ENCIMERA")
    assert linea.quantity == 3.5


def test_el_presupuesto_entero_con_metros_pasa(esquemas):
    p = esquemas.DigitalizadorSaveRequest(
        projectName="jose manuel vazquez moronta",
        userId="u1",
        lines=[
            esquemas.DigitalizadorLine(id="l1", quantity=3.5, description="ENCIMERA"),
            esquemas.DigitalizadorLine(id="l2", quantity=1.2, description="ENCIMERA"),
        ],
    )
    assert [l.quantity for l in p.lines] == [3.5, 1.2]


def test_la_linea_de_un_presupuesto_principal_tambien(esquemas):
    """El digitalizador tambien vuelca a Presupuestos: si alli fuera entero,
    fallaria el segundo guardado en vez del primero."""
    item = esquemas.BudgetItemModel(productId="p1", productCode="ENC",
                                    productName="Encimera", quantity=3.5)
    assert item.quantity == 3.5


def test_las_cantidades_enteras_siguen_valiendo(esquemas):
    """Lo normal —3 bajos— tiene que seguir funcionando igual."""
    assert esquemas.DigitalizadorLine(id="l", quantity=3, description="BAJO").quantity == 3


def test_no_se_redondea_nunca(esquemas):
    """Redondear seria PEOR que rechazar: cobrar 4 metros de encimera cuando se
    han pedido 3,5 es cambiarle el pedido al cliente sin decirselo, y ademas sin
    que salte nada."""
    for pedido in (3.5, 0.5, 2.25, 1.75):
        assert esquemas.DigitalizadorLine(id="l", quantity=pedido,
                                          description="ENCIMERA").quantity == pedido


# ─── 2. El despiece SIGUE siendo entero ─────────────────────────────────────

def _pieza(esquemas, **cambios):
    base = dict(id="p1", name="Costado", nameShort="COS", material="Melamina",
                length=800, width=580, quantity=2, area=0.46)
    base.update(cambios)
    return esquemas.ComponentPiece(**base)


def test_el_despiece_con_piezas_enteras_pasa(esquemas):
    """Primero se comprueba que la pieza BUENA entra: si no, la prueba de abajo
    daria verde por un motivo que no es el suyo."""
    assert _pieza(esquemas).quantity == 2


def test_una_pieza_de_despiece_no_puede_ser_media(esquemas):
    """CANDADO. Alli una pieza es una pieza. Admitir 1,5 dejaria entrar en la
    maquina un dato que no existe."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError) as e:
        _pieza(esquemas, quantity=1.5)
    # Y que falle POR LA CANTIDAD, no por otra cosa.
    assert any(err["loc"] == ("quantity",) for err in e.value.errors())


# ─── 3. Un error de validacion se lee ───────────────────────────────────────

def test_existe_el_traductor_de_errores():
    assert os.path.exists(ERRORES_JS), (
        "sin esto, cada pantalla vuelve a hacer `new Error(d.detail)` y a "
        "ensenniar «[object Object]»")
    src = _leer(ERRORES_JS)
    assert "Array.isArray(detail)" in src, (
        "no reconoce la LISTA de errores de FastAPI, que es justo el caso que "
        "producia «[object Object]»")
    assert "loc" in src, "no lee el campo que ha fallado, que es lo que sirve"


def test_el_traductor_dice_la_linea_empezando_por_uno():
    """Quien mira la pantalla ve la linea 1, no la 0."""
    src = _leer(ERRORES_JS)
    assert "siguiente + 1" in src


def test_el_guardado_del_digitalizador_ya_no_ensenia_objetos():
    src = _leer(DIGI_JSX)
    assert "errorDeRespuesta" in src, "el guardado no usa el traductor"
    assert "new Error(d.detail" not in src, (
        "vuelve a meter el `detail` crudo en un Error: si es una lista, sale "
        "«[object Object]» otra vez")


def test_el_traductor_entiende_el_formato_de_ESTE_servidor():
    """CANDADO. `server.py` NO manda el formato de FastAPI: tiene su propio
    manejador que reescribe cada error como {campo, msg}. Leyendo solo `loc`, el
    mensaje llegaba sin decir que campo fallaba — la mitad de lo que sirve."""
    src = _leer(ERRORES_JS)
    assert "e?.campo" in src or "campo" in src, (
        "el traductor solo entiende el formato estandar de FastAPI; este "
        "servidor manda {campo, msg} y el aviso saldria sin nombrar el campo")
    manejador = _leer(os.path.join(BACKEND, "server.py"))
    assert '"campo"' in manejador, (
        "el manejador de errores del servidor ha cambiado de formato: revisa "
        "services/errores.js o los avisos dejaran de decir que campo falla")


def test_los_huecos_vacios_no_viajan_como_texto():
    """LO QUE ROMPIA EL GUARDADO. La pantalla usa "" para «casilla en blanco»,
    y eso al servidor no se le puede mandar: espera un numero, recibe "" y
    rechaza el presupuesto entero."""
    src = _leer(DIGI_JSX)
    assert "prepararLineas" in src, (
        "las lineas se mandan tal cual: un INC% en blanco viaja como cadena "
        "vacia y el servidor rechaza el presupuesto entero")
    i = src.index("const prepararLineas")
    cuerpo = src[i:i + 1800]
    assert "lineMarkup" in cuerpo and "null" in cuerpo, (
        "el INC% en blanco no se traduce a `null`, que es lo que significa: "
        "«usa el incremento global»")


def test_una_cantidad_en_blanco_NO_se_rellena_sola():
    """CANDADO. Una cantidad vacia no significa 0 ni 1: significa que falta por
    decidir. Poner un numero ahi seria inventarse el pedido del cliente."""
    src = _leer(DIGI_JSX)
    i = src.index("const prepararLineas")
    cuerpo = src[i:i + 1800]
    assert "sinCantidad" in cuerpo and "throw new Error" in cuerpo, (
        "se rellena sola la cantidad que falta en vez de parar y decir que "
        "linea es")


def test_la_cantidad_admite_decimales_tambien_en_la_pantalla():
    """De nada sirve que el servidor acepte 3,5 si la casilla lo recorta a 3 —
    y encima sin decirlo: medio metro de encimera menos."""
    import re as _re
    # Sin los comentarios: la explicacion de por que NO se usa `parseInt` habla
    # de `parseInt`, y la prueba se disparaba contra su propio comentario.
    src = _re.sub(r"//[^\n]*", "", _leer(DIGI_JSX))
    i = src.index("updateLine(line.id, 'quantity'")
    trozo = src[max(0, i - 700):i + 200]
    assert "parseInt" not in trozo, (
        "la cantidad vuelve a leerse con `parseInt`: una encimera de 3,5 m se "
        "quedaria en 3 sin avisar")
    assert "replace(',', '.')" in trozo, "no admite la coma decimal"


def test_ninguna_pantalla_mete_un_detail_crudo_en_un_Error():
    """Barre todo el frontend: era un patron copiado por muchos sitios."""
    import re
    src_dir = os.path.join(RAIZ, "frontend", "src")
    malos = []
    for raiz, _, ficheros in os.walk(src_dir):
        if "node_modules" in raiz:
            continue
        for f in ficheros:
            # El propio traductor habla de `detail` por definicion.
            if not f.endswith((".jsx", ".js")) or f == "errores.js":
                continue
            texto = _leer(os.path.join(raiz, f))
            # `new Error(algo.detail)` sin traducir: el patron exacto que fallaba.
            if re.search(r"new Error\(\s*\w+\.detail\s*\)", texto):
                malos.append(f)
    assert not malos, (
        "estas pantallas meten el `detail` del servidor en un Error sin "
        "traducirlo: " + ", ".join(sorted(set(malos)))
        + ". Si FastAPI manda una lista, el usuario ve «[object Object]». Usa "
        "`errorDeRespuesta` de services/errores.js.")
