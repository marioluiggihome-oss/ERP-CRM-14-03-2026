# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Volcar la relación MV al presupuesto: quién puede, y qué se lleva.

Lo pidió el master: «adelante con volcar la relación de MV al presupuesto pero
con permisos para ciertos usuarios».

SON DOS PERMISOS DISTINTOS, y esa es la idea entera:

    ver lo que CUESTA un mueble   → solo el master (`_ve_precios_mv`, regla 8b)
    poder METER muebles en un presupuesto → `canVolcarMV`, por usuario

Un jefe de obra puede necesitar lo segundo sin tener lo primero, y de hecho es
el caso normal: monta el pedido, no negocia con el proveedor. Si el volcado
fuera detrás del permiso de la tarifa, para dejarle volcar habría que enseñarle
el margen de la casa.

El permiso se comprueba EN EL BACKEND, entregando o no los muebles listos para
volcar. Esconder el botón no cierra una API — regla 8 de CLAUDE.md.
"""
import asyncio
import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND = os.path.join(RAIZ, "backend")
os.environ.setdefault("JWT_SECRET", "x" * 64)
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

import routes.estudio_cocinas as ec  # noqa: E402

MASTER = {"isMaster": True, "id": "u-master"}
CON_PERMISO = {"id": "u-jefe", "email": "jefe@luiggihome.es"}
SIN_PERMISO = {"id": "u-comercial", "email": "comercial@luiggihome.es"}


class _ColeccionFalsa:
    """Un doble de la colección de usuarios: `canVolcarMV` solo para uno."""

    def __init__(self, con_permiso=("u-jefe",), revienta=False):
        self.con_permiso = set(con_permiso)
        self.revienta = revienta

    async def find_one(self, filtro, _proj=None):
        if self.revienta:
            raise RuntimeError("base de datos caída")
        uid = filtro.get("id")
        return {ec.PERMISO_VOLCAR_MV: uid in self.con_permiso}


@pytest.fixture()
def usuarios(monkeypatch):
    doble = _ColeccionFalsa()
    import services.jwt_service as jwt_service
    monkeypatch.setattr(jwt_service, "_users_collection", lambda: doble)
    return doble


def _cocina():
    return {"tipo": "lineal",
            "paredes": [{"nombre": "Pared 1", "ancho": 300, "alto": 240}],
            "elementos": [
                {"id": "bajo", "label": "Bajo", "pared_idx": 0, "posicion_cm": 0, "ancho": 60, "fila": "bajo"},
                {"id": "bajo_fregadero", "label": "Bajo fregadero", "pared_idx": 0, "posicion_cm": 60, "ancho": 90, "fila": "bajo"},
            ]}


def _pedir(usuario):
    return asyncio.run(ec.relacion_mv({"distribucion": _cocina()}, usuario))


# ── El permiso ──────────────────────────────────────────────────────────────

def test_sin_permiso_NO_se_entregan_los_muebles_para_volcar(usuarios):
    """CANDADO. El corte va en los datos, no en el botón: quien no puede volcar
    no recibe con qué hacerlo, aunque llame a la API a mano."""
    r = _pedir(SIN_PERMISO)
    assert r["puedeVolcar"] is False
    assert r["muebles"] is None, "se entregan los muebles listos a quien no puede volcar"


def test_con_permiso_SI(usuarios):
    r = _pedir(CON_PERMISO)
    assert r["puedeVolcar"] is True
    assert r["muebles"], "quien tiene el permiso se ha quedado sin poder volcar"


def test_el_master_puede_siempre(usuarios):
    r = _pedir(MASTER)
    assert r["puedeVolcar"] is True and r["muebles"]


def test_sin_usuario_no_se_vuelca(usuarios):
    r = _pedir(None)
    assert r["puedeVolcar"] is False and r["muebles"] is None


def test_si_no_se_puede_COMPROBAR_el_permiso_no_se_concede(monkeypatch):
    """Un permiso que se abre cuando falla la base de datos no es un permiso."""
    import services.jwt_service as jwt_service
    monkeypatch.setattr(jwt_service, "_users_collection",
                        lambda: _ColeccionFalsa(revienta=True))
    r = _pedir(CON_PERMISO)
    assert r["puedeVolcar"] is False, "al fallar la comprobación se ha concedido el permiso"


# ── Volcar y ver precios son cosas DISTINTAS ────────────────────────────────

def test_se_puede_volcar_SIN_ver_la_tarifa(usuarios):
    """La mitad que importa. Si volcar exigiera el permiso de la tarifa, para
    dejar a alguien montar un pedido habría que enseñarle el margen."""
    r = _pedir(CON_PERMISO)
    assert r["puedeVolcar"] is True
    assert r["preciosOcultos"] is True, "se le está enseñando la tarifa MV"
    assert r["totalPvp"] is None
    for m in r["muebles"]:
        assert m.get("pvp") is None and m.get("pts") is None, \
            f"el mueble {m.get('cod')} viaja con su precio de tarifa"
        assert m.get("cod"), "el mueble viaja sin código: así no se puede pedir"


def test_ver_la_tarifa_no_da_permiso_para_volcar(usuarios):
    """Y al revés tampoco: son dos puertas, no una."""
    from routes.cascos import _ve_precios_mv
    assert _ve_precios_mv(MASTER) is True
    assert _ve_precios_mv(CON_PERMISO) is False, \
        "el permiso de volcar ha abierto también la tarifa"


def test_al_master_los_muebles_le_llegan_CON_precio(usuarios):
    r = _pedir(MASTER)
    assert all(m.get("pvp") for m in r["muebles"]), "al master le faltan precios"


# ── Lo que se vuelca ────────────────────────────────────────────────────────

def test_la_MANO_decidida_viaja_en_el_codigo(usuarios):
    """Un código que acaba en «D/I» es una puerta sin mano decidida. Si sale así
    hacia el taller, la decide el taller: acierta la mitad de las veces y la
    otra mitad es un frente desmontado y taladrado otra vez en casa del
    cliente. Aquí la mano ya se sabe, así que se escribe."""
    r = _pedir(MASTER)
    with_hand = [m for m in r["muebles"] if m.get("mano")]
    assert with_hand, "ningún mueble lleva mano: hasta 60 cm todos son de una puerta"
    for m in with_hand:
        assert not m["cod"].endswith("D/I"), (
            f"{m['cod']} sale hacia el taller sin la mano decidida, teniéndola")
        assert m["cod"].endswith(("D", "I"))


def test_se_avisa_de_que_la_mano_es_PROPUESTA(usuarios):
    """No sale del diseño. Si viaja sin marcar, una suposición del programa
    llega al taller como si la hubiera decidido alguien."""
    r = _pedir(MASTER)
    propuestas = [m for m in r["muebles"] if m.get("manoPropuesta")]
    assert propuestas, "se ha perdido el aviso de que la mano la propuso el programa"


def test_los_muebles_van_en_el_MISMO_formato_que_la_pantalla_de_revision(usuarios):
    """Se reutiliza `RelacionReview`, la de Cascos y Cocina Montada 3, con sus
    avisos. Si aquí se inventara otro formato, habría que escribir un segundo
    volcado — y uno de los dos se quedaría sin el aviso de la mano."""
    r = _pedir(MASTER)
    for m in r["muebles"]:
        for clave in ("cod", "familia", "tipo", "ancho", "alto", "qty"):
            assert clave in m, f"al mueble le falta «{clave}», que la revisión espera"
