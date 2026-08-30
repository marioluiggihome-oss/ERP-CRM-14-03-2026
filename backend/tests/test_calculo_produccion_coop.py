# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
POR DÓNDE VA CADA PEDIDO EN FÁBRICA (pestaña Producción de COOP).

El master, 30/08: «los pedidos y el estado de los mismos en fábrica, vamos los
procesos de producción y su estado».

LO QUE VIGILA ESTE CANDADO:

  1. QUE EL ESTADO NO SE INVENTE. Sale de `fabrica_orders`, la colección que ya
     lleva el taller. Un pedido del que la fábrica no sabe nada NO está
     «pendiente» ni «en producción»: está `confirmed` —vendido y aún sin entrar
     al taller—, que es lo único que se sabe de verdad.

  2. QUE LA TABLA DE ESTADOS NO SE COPIE. Vivía escrita a mano dentro de
     `routes/orders.py`; ahora la usan también COOP y la pantalla. Es la cuarta
     vez en este proyecto que una regla vive en dos sitios —`es_master` en
     cuatro ficheros, el origen de los pedidos en dos, los tramos de comisión en
     la pantalla y en el cálculo—, y cuando se separan una pantalla dice «En
     producción» y otra «Confirmado» del MISMO pedido, sin que ninguna parezca
     un error.

  3. QUE NO SE ESCAPE UN EURO. Es una ruta nueva, y por las rutas nuevas no
     viaja dinero: aquí se mira por dónde va una cocina, no lo que vale.
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
BACKEND = os.path.join(RAIZ, "backend")
sys.path.insert(0, BACKEND)
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import estado_fabricacion as EF  # noqa: E402

JS = os.path.join(RAIZ, "frontend", "src", "estadosFabricacion.js")
ORDERS = os.path.join(BACKEND, "routes", "orders.py")
COOP = os.path.join(BACKEND, "routes", "cooperativistas.py")

PEDIDO = {
    "id": "ped-1",
    "budgetNumber": "MV-1",
    "customerName": "  Ana ",
    "confirmedAt": "2026-08-10",
    "origenNombre": "Presupuestador · Montada",
    "total": 7000.0,
    "items": [{"code": "B60D", "price": 300.0}],
}


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


# ── 1. El estado sale de la fábrica ─────────────────────────────────────────

def test_EL_ESTADO_SALE_DE_LA_FICHA_DEL_TALLER():
    for status, esperado in EF.DE_FABRICA.items():
        assert EF.estado_de({"status": status}) == esperado


def test_UN_PEDIDO_QUE_NO_HA_ENTRADO_AL_TALLER_NO_SE_INVENTA():
    """Sin ficha en fábrica es «Confirmado»: vendido y aún sin empezar.

    Ponerlo «pendiente» o «en producción» sería adivinar, y en una pantalla que
    se mira para decidir qué empujar, adivinar es peor que no decir nada.
    """
    assert EF.estado_de(None) == "confirmed"
    assert EF.estado_de({}) == "confirmed"
    assert EF.estado_de({"status": "lo_que_sea"}) == "confirmed", (
        "un estado que la fábrica no reconoce se está colando tal cual")


def test_EL_PROGRESO_NO_SE_SALE_DE_LA_BARRA():
    assert EF.progreso_de({"progress": 40}) == 40
    assert EF.progreso_de({"progress": 250}) == 100
    assert EF.progreso_de({"progress": -3}) == 0
    assert EF.progreso_de({"progress": "roto"}) == 0, (
        "un progreso corrupto tiene que ser 0, no una barra rara")
    assert EF.progreso_de(None) == 0


def test_LO_MAS_ATRASADO_PRIMERO():
    """Es lo que hay que empujar. Por fecha saldría lo último que entró, que es
    justo lo que menos corre prisa."""
    filas = EF.lineas(
        [dict(PEDIDO, id="a", budgetNumber="A"),
         dict(PEDIDO, id="b", budgetNumber="B"),
         dict(PEDIDO, id="c", budgetNumber="C")],
        {"A": {"status": "delivered"}, "B": {"status": "draft"},
         "C": {"status": "in_progress"}})
    assert [f["pedidoId"] for f in filas] == ["b", "c", "a"]


def test_EL_RESUMEN_CUENTA_EN_ORDEN_DE_PROCESO():
    filas = EF.lineas([dict(PEDIDO, id="a", budgetNumber="A")], {"A": {"status": "draft"}})
    r = EF.resumen(filas)
    assert r["total"] == 1
    assert [e["estado"] for e in r["porEstado"]] == [c for c, _ in EF.ESTADOS]
    assert next(e for e in r["porEstado"] if e["estado"] == "pending")["pedidos"] == 1


# ── 2. Ni un euro por esta puerta ───────────────────────────────────────────

def test_NO_SALE_NI_UN_EURO():
    f = EF.linea(PEDIDO, {"status": "in_progress", "progress": 50})
    assert set(f) <= set(EF.CAMPOS_DE_LA_LINEA), (
        f"campos de más: {set(f) - set(EF.CAMPOS_DE_LA_LINEA)}")
    for prohibido in ("total", "items", "lines", "pvp", "coste", "margen",
                      "baseImponible", "descuento"):
        assert prohibido not in f, f"«{prohibido}» viaja en la producción"
    assert f["cliente"] == "Ana", "el nombre sale sin recortar"


def test_SERVIDO_Y_COBRADO_SON_COSAS_DISTINTAS():
    """«Entregado» en fábrica no quiere decir cobrado, y esa diferencia es la
    que decide si una comisión se libera (regla 17)."""
    f = EF.linea(dict(PEDIDO, deliveredAt="2026-08-20"), {"status": "delivered"})
    assert f["servido"] is True and f["cobrado"] is False
    f2 = EF.linea(dict(PEDIDO, deliveredAt="2026-08-20", paidAt="2026-08-21"), None)
    assert f2["servido"] is True and f2["cobrado"] is True


# ── 3. Que la tabla no se copie ─────────────────────────────────────────────

def test_ORDERS_YA_NO_TIENE_SU_PROPIA_TABLA():
    cuerpo = _lee(ORDERS)
    assert "fab_status_map" not in cuerpo, (
        "ha vuelto la copia de la tabla de estados en `routes/orders.py`: dos "
        "copias acaban diciendo cosas distintas del mismo pedido")
    assert "estado_fabricacion" in cuerpo, (
        "`routes/orders.py` ya no le pregunta al módulo de estados")


def test_LA_PANTALLA_Y_EL_SERVIDOR_USAN_LAS_MISMAS_CLAVES():
    """Se EJECUTA el JS: comparar los dos ficheros a ojo no probaría nada.

    Si la pantalla se quedara sin una clave, ese pedido saldría con el rótulo
    por defecto —«Confirmado»— estando en producción. Un pedido en el taller
    que en pantalla pone «Confirmado» no parece un fallo: parece un pedido
    parado.
    """
    node = shutil.which("node")
    if not node:
        pytest.skip("no hay node en esta máquina")
    guion = re.sub(r"^import .*$", "", _lee(JS), flags=re.M)
    guion = guion.replace("export const", "const").replace("export ", "")
    guion = re.sub(r"icon:\s*\w+", "icon: null", guion)
    guion += ("\nconsole.log(JSON.stringify({claves: Object.keys(ESTADOS_FABRICACION),"
              " nombres: Object.fromEntries(Object.entries(ESTADOS_FABRICACION)"
              ".map(([k, v]) => [k, v.label])), porDefecto: ESTADO_POR_DEFECTO}));\n")
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False, encoding="utf-8") as f:
        f.write(guion); ruta = f.name
    try:
        salida = subprocess.run([node, ruta], capture_output=True, text=True, timeout=60)
    finally:
        os.unlink(ruta)
    assert salida.returncode == 0, f"el módulo de pantalla no corre: {salida.stderr.strip()}"
    d = json.loads(salida.stdout)

    assert set(d["claves"]) == set(EF.NOMBRES), (
        "la pantalla y el servidor no manejan los mismos estados: "
        f"pantalla={sorted(d['claves'])} servidor={sorted(EF.NOMBRES)}")
    assert d["porDefecto"] == EF.SIN_FICHA_EN_FABRICA
    for clave, nombre in EF.NOMBRES.items():
        assert d["nombres"][clave] == nombre, (
            f"«{clave}» se lee «{d['nombres'][clave]}» en pantalla y «{nombre}» "
            "en el servidor: el mismo pedido diría dos cosas")


# ── 4. La puerta ────────────────────────────────────────────────────────────

def test_LA_PRODUCCION_DE_LA_COOPERATIVA_ES_DEL_MASTER():
    cuerpo = _lee(COOP)
    i = cuerpo.index('@router.get("/produccion")')
    j = cuerpo.index("@router", i + 10)
    trozo = cuerpo[i:j]
    assert "_es_master(current_user)" in trozo and "403" in trozo, (
        "la pestaña de producción no está cerrada al master")
    assert "EF.lineas" in trozo, "la lista no pasa por la lista blanca de campos"


# ── 5. ENTRAR EN UN PEDIDO: qué lleva, y sin un euro ────────────────────────
#
# El master, 30/08: «que podamos entrar en los pedidos, si no no sabemos lo que
# hay en cada uno de ellos». La lista dice POR DÓNDE VA; esto dice QUÉ ES.
#
# Aquí está el riesgo de verdad de esta pantalla. Para enseñar el contenido hay
# que tocar las LÍNEAS del pedido, y dentro de una línea viajan `price`, `pvp` y
# el descuento. Volcarlas tal cual abriría por una ruta nueva justo lo que el
# ERP tiene cerrado en Rentabilidad — y un candado que se rodea por otra puerta
# no es un candado.

PEDIDO_CON_LINEAS = {
    "id": "ped-9",
    "budgetNumber": "MV-9",
    "customerName": " Luis ",
    "origenNombre": "Presupuestador · Montada",
    "items": [
        # Un mueble de verdad, con los nombres que usa el ERP de verdad
        # (`quantity`, `price`), no los de las pruebas.
        {"code": "B60D", "name": "Bajo 60 1 puerta", "quantity": 2,
         "price": 600.0, "pvp": 300.0, "coste": 111.0, "descuento": 28},
        # Un frente: NO cuenta para la comisión (master, 25/08).
        {"code": "PT60", "name": "Puerta 60", "quantity": 4,
         "familia": "PUERTAS", "price": 400.0},
    ],
}


def test_AL_ABRIR_UN_PEDIDO_NO_SALE_NI_UN_EURO():
    """Lo que más importa de esta ruta: son las líneas del pedido en crudo.

    Si se volcara la línea entera saldrían `price`, `pvp`, `coste` y el
    descuento del proveedor — el dinero que el ERP tiene cerrado al master en
    Rentabilidad, servido por una ruta nueva y sin que nadie lo note.
    """
    d = EF.contenido_de(PEDIDO_CON_LINEAS)
    for l in d["lineas"]:
        assert set(l) <= set(EF.CAMPOS_DE_LA_LINEA_DEL_PEDIDO), (
            f"campos de más en la línea: {set(l) - set(EF.CAMPOS_DE_LA_LINEA_DEL_PEDIDO)}")
        for prohibido in ("price", "pvp", "coste", "descuento", "importe",
                          "total", "margen", "puntos"):
            assert prohibido not in l, f"«{prohibido}» viaja al abrir un pedido"
    texto = json.dumps(d)
    for euro in ("600.0", "300.0", "111.0", "400.0"):
        assert euro not in texto, f"el importe {euro} se ha colado en el detalle"


def test_LAS_UNIDADES_SE_LEEN_COMO_LAS_LEE_LA_NOMINA():
    """`quantity` es el nombre que usan los pedidos de VERDAD.

    Esto ya falló en producción el 28/08: las pruebas leían `qty`/`familia` y el
    ERP guarda `quantity`/`code`, así que COOP enseñaba «0 muebles» en todos los
    pedidos y la comisión salía a cero para todo el mundo. Por eso las unidades
    no se leen aquí a mano: se las pide a `comisiones`, que es donde ya está
    escrito qué nombre usa cada pantalla.
    """
    d = EF.contenido_de(PEDIDO_CON_LINEAS)
    assert [l["unidades"] for l in d["lineas"]] == [2, 4]
    assert d["unidades"] == 6, "fábrica monta TODAS las unidades"


def test_MUEBLES_Y_UNIDADES_SON_DOS_NUMEROS_DISTINTOS():
    """Fábrica monta todo; la comisión solo paga los muebles (master, 25/08).

    Y el corte lo hace la MISMA función que la nómina, no una copia: si se
    separaran, esta pantalla explicaría una cosa y la liquidación pagaría otra.
    """
    # Con el catálogo delante, que es como llega de la ruta: `B60D` → «BAJO».
    d = EF.contenido_de(PEDIDO_CON_LINEAS, {"B60D": "BAJO"})
    assert d["muebles"] == 2, "las puertas no incentivan y están contando"
    assert d["unidades"] == 6
    porcodigo = {l["codigo"]: l["esMueble"] for l in d["lineas"]}
    assert porcodigo["B60D"] is True
    assert porcodigo["PT60"] is False, (
        "una puerta se está marcando como mueble: el comercial vería una "
        "comisión que no le van a pagar")


def test_LA_FAMILIA_SE_RESUELVE_POR_CODIGO_COMO_EN_LA_LIQUIDACION():
    """Los pedidos de verdad guardan el CÓDIGO; la familia vive en el catálogo."""
    d = EF.contenido_de({"id": "x", "items": [{"code": "b60d", "quantity": 1}]},
                        {"B60D": "BAJO"})
    assert d["lineas"][0]["familia"] == "BAJO"
    assert d["lineas"][0]["esMueble"] is True
    # Y sin el catálogo no se inventa una familia: se queda sin clasificar, que
    # es la decisión conservadora de siempre (pagar de menos se reclama).
    sin = EF.contenido_de({"id": "x", "items": [{"code": "b60d", "quantity": 1}]})
    assert sin["lineas"][0]["familia"] == ""
    assert sin["lineas"][0]["esMueble"] is False


def test_UN_PEDIDO_SIN_LINEAS_NO_LLEVA_CERO_MUEBLES_SINO_QUE_NO_CONSTA():
    """Regla 7: un 0 parece un dato. «No se sabe» se dice, no se rellena."""
    d = EF.contenido_de({"id": "vacio", "items": []})
    assert d["sinDesglose"] is True
    assert d["muebles"] == 0 and d["lineas"] == []


def test_ENTRAR_EN_UN_PEDIDO_ES_DEL_MASTER():
    cuerpo = _lee(COOP)
    i = cuerpo.index('@router.get("/produccion/{pedido_id}")')
    j = cuerpo.index("@router", i + 10)
    trozo = cuerpo[i:j]
    assert "_es_master(current_user)" in trozo and "403" in trozo, (
        "se puede abrir el contenido de un pedido sin ser master")
    assert "EF.contenido_de" in trozo, (
        "el detalle no pasa por la lista blanca de campos: estaría volcando la "
        "línea del pedido entera, con sus euros dentro")


def test_SOLO_SE_ABREN_PEDIDOS_DE_LA_COOPERATIVA():
    """No se lee la colección a pelo: por aquí no se mira un pedido de fábrica.

    `_pedidos_de_la_cooperativa` es la lista BLANCA (Montada 3 y Desmontada, y
    ni una más). Buscar por `id` directamente en `orders` dejaría ver el
    contenido de cualquier pedido del ERP desde una pantalla de la cooperativa.
    """
    cuerpo = _lee(COOP)
    i = cuerpo.index('@router.get("/produccion/{pedido_id}")')
    j = cuerpo.index("@router", i + 10)
    trozo = cuerpo[i:j]
    assert "_pedidos_de_la_cooperativa()" in trozo, (
        "el detalle no sale de la lista blanca de orígenes")
    assert "find_one" not in trozo, (
        "se está leyendo la colección directamente: se colaría un pedido que no "
        "es de este negocio")
    assert "404" in trozo, "un pedido que no es de la cooperativa tiene que dar 404"


def test_LA_PANTALLA_PIDE_EL_DETALLE_AL_ABRIR_Y_NO_PINTA_EUROS():
    """La pantalla del detalle no puede tener su propia columna de importes."""
    jsx = _lee(os.path.join(RAIZ, "frontend", "src", "components", "CoopProduccion.jsx"))
    assert "/api/cooperativistas/produccion/" in jsx, (
        "la pantalla no llama a la ruta del detalle: el pedido no se abre")
    for prohibido in ("l.price", "l.pvp", "l.coste", "l.importe", "€"):
        assert prohibido not in jsx, (
            f"la pantalla de producción pinta «{prohibido}»: aquí no va dinero")


def test_COOP_ABRE_POR_PRODUCCION():
    """El master, 30/08: «al entrar en COOP que entre en producción primero
    siempre».

    Es lo que se mira a diario —por dónde va cada cocina—; los socios se marcan
    una vez y la liquidación es de fin de mes. Se comprueba el `useState`, que
    es lo que de verdad decide qué pestaña sale: que la pestaña exista en la
    lista no dice nada de cuál se abre.
    """
    jsx = _lee(os.path.join(RAIZ, "frontend", "src", "components", "CoopPanel.jsx"))
    m = re.search(r"useState\(\s*'([a-z]+)'\s*\)", jsx)
    assert m, "no se ha podido leer qué pestaña abre COOP"
    assert m.group(1) == "produccion", (
        f"COOP abre por «{m.group(1)}» y el master pidió que abriera por producción")
    assert "'produccion'" in jsx and "<CoopProduccion" in jsx, (
        "la pestaña de producción no está montada: abriría en blanco")
