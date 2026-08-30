# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LANZAR A FABRICACIÓN, Y QUE NO SE DUPLIQUE EL PEDIDO.

Los dos hallazgos de la auditoría del 30/08 que el master mandó arreglar.

1. NADIE ESCRIBÍA EN `fabrica_orders`. Es la colección de la que sale el estado
   de producción —la leen el dashboard, el command center, «Mis Pedidos» y la
   pestaña Producción de COOP— y al buscar quién la ESCRIBE no había ni un
   endpoint en todo el backend. Los índices se creaban al arrancar y la tabla se
   quedaba vacía para siempre.

   Y el botón «Fabricar» de Cocina Montada 3 no llegaba al servidor: guardaba en
   `localStorage`, o sea en ESE navegador y en ningún sitio más.

   Resultado: en COOP todos los pedidos salían «Confirmado» para siempre, se
   hubiera lanzado a fabricar o no. La pestaña entera no podía cambiar de estado
   porque su fuente no la alimentaba nadie, y eso no daba ningún error.

2. «CREAR PEDIDO» DUPLICABA. Cada pulsación generaba un id nuevo con la hora, así
   que no actualizaba: creaba otro pedido. Los dos entraban en COOP y los dos
   pagaban comisión — una cocina vendida una vez, pagada dos.
"""
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND = os.path.join(RAIZ, "backend")
sys.path.insert(0, BACKEND)
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import estado_fabricacion as EF  # noqa: E402

FABRICA = os.path.join(BACKEND, "routes", "fabrica.py")
CM3 = os.path.join(RAIZ, "frontend", "src", "components", "CocinaMontada3.jsx")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _funcion(jsx, nombre):
    """El cuerpo de una función del JSX, y SOLO ese.

    Se saca la función entera en vez de mirar N caracteres alrededor: una
    ventana a bulto ya dejó pasar un fallo dos veces en este proyecto.
    """
    i = jsx.index(f"const {nombre} = async")
    return jsx[i:jsx.index("\n  };", i)]


# ── 1. La fabricación llega al servidor y COOP la ve ───────────────────────

def test_LA_TABLA_DE_ESTADOS_ENTIENDE_LO_QUE_ESCRIBE_EL_TALLER():
    """Estaba escrita para un esquema que no existe.

    El Portal Fábrica (`routes/fabrica.py`) escribe `in_production`, `ready` y
    `cancelled`. La tabla solo reconocía `in_progress`, `completed` y `shipped`,
    que NO los escribe nadie: son los nombres de SALIDA de la propia tabla. Una
    orden real en producción no encajaba en ninguna clave y caía en el valor por
    defecto, «Confirmado» — y un pedido en el taller que pone «Confirmado» no
    parece un fallo, parece un pedido parado.
    """
    cuerpo = _lee(FABRICA)
    i = cuerpo.index("valid_statuses = [")
    reales = re.findall(r'"([a-z_]+)"', cuerpo[i:cuerpo.index("]", i)])
    assert reales, "no se han podido leer los estados del Portal Fábrica"
    for estado in reales:
        assert estado in EF.DE_FABRICA, (
            f"el taller escribe «{estado}» y la tabla no lo reconoce: ese pedido "
            "saldría «Confirmado» estando en producción")


def test_ANULADA_SE_DICE_EN_VEZ_DE_DISFRAZARSE():
    assert EF.estado_de({"status": "cancelled"}) == "cancelled"
    assert EF.NOMBRES["cancelled"] == "Anulada"
    assert EF.ESTADOS[-1][0] == "cancelled", (
        "«Anulada» no es una etapa del proceso: va la última para no colarse "
        "entre lo que hay que empujar al ordenar por lo más atrasado")


def test_SE_LEE_LA_COLECCION_QUE_EL_TALLER_ESCRIBE_DE_VERDAD():
    """`fabrica_orders` no la escribe NADIE — se buscó en todo el backend.

    Quien escribe es el Portal Fábrica, en `manufacturing_orders`. Todas las
    pantallas leían la vacía, y por eso COOP daba «Confirmado» siempre.
    """
    assert EF.COLECCIONES_DEL_TALLER[0] == "manufacturing_orders", (
        "se sigue prefiriendo la colección que no escribe nadie")
    assert "fabrica_orders" in EF.COLECCIONES_DEL_TALLER, (
        "se ha dejado de leer la colección vieja: se perderían los datos que "
        "hubiera guardados ahí")
    coop = _lee(os.path.join(BACKEND, "routes", "cooperativistas.py"))
    assert "COLECCIONES_DEL_TALLER" in coop, (
        "COOP sigue leyendo una sola colección a mano")


def test_LA_ORDEN_DEL_TALLER_LLEVA_LA_REFERENCIA_DEL_PEDIDO():
    """Sin `budgetNumber` la orden existe y su pedido nunca sabe que está en el
    taller: `estado_fabricacion` cruza por ese campo y por ningún otro."""
    cuerpo = _lee(FABRICA)
    assert "budgetNumber: str" in cuerpo, (
        "el cuerpo de crear orden no acepta la referencia del pedido")
    i = cuerpo.index('"status": "draft"')
    assert "budgetNumber" in cuerpo[i:i + 400], (
        "la referencia no se guarda en el documento de la orden")


def test_LA_PANTALLA_LANZA_AL_SERVIDOR_Y_NO_SOLO_AL_NAVEGADOR():
    jsx = _lee(CM3)
    trozo = _funcion(jsx, "lanzarAFabricacion")
    assert "/api/fabrica/orders" in trozo, (
        "«Fabricar» ha vuelto a guardar solo en el navegador: la orden no "
        "existiría para nadie más y COOP no se enteraría nunca")
    assert "budgetNumber" in trozo, "no manda la referencia: no cruzaría con el pedido"
    i = trozo.index("/api/fabrica/orders")
    assert "r.ok" in trozo[i:], (
        "no se mira la respuesta: diría «lanzada con éxito» aunque fallara")


# ── 2. El pedido no se duplica ──────────────────────────────────────────────

def test_CREAR_PEDIDO_NO_DUPLICA():
    """Cada pulsación creaba otro pedido, y los dos pagaban comisión."""
    jsx = _lee(CM3)
    trozo = _funcion(jsx, "pasarAPedido")
    assert re.search(r"id:\s*destino\s*\|\|", trozo), (
        "el id del pedido se vuelve a generar siempre: dos pulsaciones son dos "
        "pedidos, y los dos pagan comisión")
    assert "setPedidoId(" in trozo, (
        "no se recuerda el pedido creado: la siguiente pulsación haría otro")
    assert "kind=pedido" in trozo, (
        "no se comprueba en el servidor si esa cocina ya tiene pedido: al "
        "recuperar un presupuesto en otra sesión volvería a duplicar")


def test_NO_SE_FUSIONA_NI_SE_DUPLICA_SIN_PREGUNTAR():
    """Duplicar paga dos comisiones y fusionar pisa un pedido que quizá ya está
    en el taller. Lo elige el master, no la pantalla."""
    jsx = _lee(CM3)
    trozo = _funcion(jsx, "pasarAPedido")
    i = trozo.index("kind=pedido")
    assert "window.confirm" in trozo[i:], (
        "se está decidiendo solo qué hacer con un pedido que ya existe")


def test_EL_PRESUPUESTO_RECUPERADO_NO_ARRASTRA_EL_PEDIDO_DE_OTRO():
    jsx = _lee(CM3)
    i = jsx.index("const recuperar")
    trozo = jsx[i:jsx.index("\n  };", i)]
    assert "setPedidoId(null)" in trozo, (
        "al recuperar un presupuesto se queda el id del pedido anterior: "
        "actualizaría el pedido de OTRA cocina")
