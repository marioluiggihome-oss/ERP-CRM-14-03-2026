# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL EXPEDIENTE DE OBRA, PARA QUIEN VA A LA OBRA.

El master, 30/08: que el cooperativista vea el Expediente de Obra.

POR QUÉ NO LO VEÍA. El Expediente arma su lista con lo que cada usuario ha
CREADO —sus proyectos y sus pedidos—, y un montador no crea nada: monta lo que
le asignan. Así que la pantalla le salía SIEMPRE vacía, «no hay obras que
coincidan con la búsqueda», aunque tuviera media docena de cocinas encima. Y
resulta que una de las tareas del propio expediente, «medidas de obra», lleva
escrito «Montador» como responsable desde el primer día.

DOS COSAS HACÍAN FALTA, y las dos están vigiladas aquí:

  1. Que la LISTA le traiga las obras que le han asignado.
  2. Que al ABRIR una pueda entrar: `_can_access` solo dejaba pasar al dueño y a
     los roles elevados, así que la lista se llenaba y cada obra daba 403.

Y UNA QUE NO PUEDE PASAR: que por esta puerta nueva se escape un euro. El
montador no ve importes en el expediente (`services/expediente.py` los QUITA,
no los pone a cero), y esta lista tampoco los manda.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import area_cooperativista as AC  # noqa: E402

MONTADOR = {"id": "u-mont", "esCooperativistaMontador": True, "plataforma": "cooperativa"}
COMERCIAL = {"id": "u-com", "esCooperativistaComercial": True, "plataforma": "cooperativa"}
OTRO = {"id": "u-otro"}

PEDIDO = {
    "id": "ped-1",
    "budgetNumber": "MV-2026-1",
    "customerName": "  María García ",
    "confirmedAt": "2026-08-10",
    "origenNombre": "Presupuestador · Montada",
    "kind": "pedido",
    "montadorUserId": "u-mont",
    # Lo que NO puede salir de aquí.
    "total": 7000.0,
    "descuento": 12,
    "lines": [{"code": "B60D", "price": 300.0}],
    "items": [{"code": "B60D", "price": 300.0}],
}


def test_LA_OBRA_SALE_CON_LO_JUSTO_PARA_RECONOCERLA():
    o = AC.obra_publica(PEDIDO)
    assert o["id"] == "ped-1"
    assert o["referencia"] == "MV-2026-1"
    assert o["cliente"] == "María García", "el nombre sale sin recortar espacios"
    assert o["fecha"] == "2026-08-10"
    assert o["origen"] == "Presupuestador · Montada"


def test_NO_SALE_NI_UN_EURO_POR_ESTA_PUERTA():
    """Es una ruta NUEVA, y el dinero no viaja por rutas nuevas «por si acaso».

    El montador no ve importes en el expediente —`services/expediente.py` los
    QUITA, no los pone a cero— y esta lista tiene que ir igual: para saber qué
    cocina hay que montar no hace falta saber lo que vale.
    """
    o = AC.obra_publica(PEDIDO)
    assert set(o) <= set(AC.CAMPOS_DE_LA_OBRA), (
        f"se están mandando campos de más: {set(o) - set(AC.CAMPOS_DE_LA_OBRA)}")
    for prohibido in ("total", "descuento", "lines", "items", "baseImponible",
                      "pvp", "precio", "coste", "margen"):
        assert prohibido not in o, f"«{prohibido}» viaja en la lista de obras"


def test_LAS_MAS_RECIENTES_PRIMERO():
    obras = AC.obras_de([
        dict(PEDIDO, id="a", confirmedAt="2026-06-01"),
        dict(PEDIDO, id="b", confirmedAt="2026-08-20"),
        dict(PEDIDO, id="c", confirmedAt="2026-07-15"),
    ])
    assert [o["id"] for o in obras] == ["b", "c", "a"]


def test_EL_FILTRO_ES_EL_SUYO_Y_SALE_DEL_TOKEN():
    """Si el «de quién son» viajara en la petición, cualquiera cambiaría el
    número y vería las obras del compañero (regla 20)."""
    assert AC.filtro_de(MONTADOR) == {"montadorUserId": "u-mont"}
    assert AC.filtro_de(COMERCIAL) == {"comercialUserId": "u-com"}
    assert AC.filtro_de(OTRO) is None, (
        "quien no es socio tiene que recibir `None`, no un filtro vacío: un "
        "`{}` en Mongo son TODOS los pedidos de la casa")


def test_QUIEN_NO_ES_SOCIO_NO_ENTRA_EN_LA_LISTA():
    """La ruta contesta 403 y no una lista vacía: son cosas distintas."""
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "routes", "cooperativistas.py")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    i = cuerpo.index('@router.get("/mis-obras")')
    j = cuerpo.index("@router", i + 10)
    trozo = cuerpo[i:j]
    assert "AC.filtro_de(current_user)" in trozo, (
        "el filtro no sale del token: por ahí se ven las obras de otro")
    assert "if filtro is None" in trozo and "403" in trozo
    assert "AC.obras_de" in trozo, "la lista no pasa por la lista blanca de campos"


# ─── Y que al abrirla no dé 403 ─────────────────────────────────────────────

def _can_access():
    """`_can_access` de `routes/cascos.py`, sin arrastrar el módulo entero."""
    import ast
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "routes", "cascos.py")
    with open(ruta, "r", encoding="utf-8") as f:
        arbol = ast.parse(f.read())
    fn = next(n for n in arbol.body
              if isinstance(n, ast.FunctionDef) and n.name == "_can_access")
    from typing import Optional as _Opt
    ambito = {"Optional": _Opt, "ADMIN_ROLE_FLAGS": ("isAdmin", "isGerente")}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "cascos.py", "exec"), ambito)
    return ambito["_can_access"]


def test_EL_MONTADOR_ASIGNADO_PUEDE_ABRIR_SU_OBRA():
    """Sin esto la lista se le llenaba y cada obra daba 403 al pulsarla."""
    puede = _can_access()
    assert puede(PEDIDO, MONTADOR) is True, (
        "el montador al que le han asignado la cocina no puede abrir su propio "
        "expediente")
    assert puede(dict(PEDIDO, montadorUserId=None, comercialUserId="u-com"),
                 COMERCIAL) is True, "el comercial que la vendió tampoco entra"


def test_PERO_NO_LA_DE_OTRO():
    """La otra mitad: abrir «mis obras» no puede abrir las de todos."""
    puede = _can_access()
    ajeno = dict(PEDIDO, montadorUserId="u-otro-montador", comercialUserId="u-otro-com")
    assert puede(ajeno, MONTADOR) is False, (
        "un montador está entrando en la obra de otro montador")
    assert puede(ajeno, {"id": ""}) is False
    assert puede(ajeno, None) is False
    # Y un pedido sin asignar no se abre «porque sí».
    assert puede({"id": "x", "userId": "otro"}, MONTADOR) is False
