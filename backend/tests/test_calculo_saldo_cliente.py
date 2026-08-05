# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Saldo de cliente: lo facturado menos lo cobrado.

Protege los dos errores que es facil cometer aqui y que falsean el saldo:
  1. Buscar las facturas SOLO por codigo de cliente. Muchas se guardaron con el
     nombre y sin codigo, y entonces el saldo sale incompleto.
  2. Contar dos veces una entrega a cuenta que encaja por varios caminos a la vez
     (id de ficha, referencia y cliente).

Mongo se sustituye por un doble en memoria: no hace falta base de datos.
"""
import asyncio
import importlib.util
import os
import re
import sys
import types

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _coincide(doc, filtro):
    if "$or" in filtro:
        return any(_coincide(doc, c) for c in filtro["$or"])
    for k, cond in filtro.items():
        v = doc.get(k)
        if isinstance(cond, dict) and "$regex" in cond:
            flags = re.I if "i" in cond.get("$options", "") else 0
            if v is None or not re.search(cond["$regex"], str(v), flags):
                return False
        elif v != cond:
            return False
    return True


class _Cursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *a, **k):
        return self

    async def to_list(self, n):
        return [dict(d) for d in self.docs[:n]]

    def __aiter__(self):
        async def gen():
            for d in self.docs:
                yield dict(d)
        return gen()


class _Coleccion:
    def __init__(self, docs=None):
        self.docs = docs or []

    def find(self, filtro=None, proj=None):
        return _Cursor([d for d in self.docs if _coincide(d, filtro or {})])

    async def find_one(self, filtro, proj=None):
        for d in self.docs:
            if _coincide(d, filtro):
                return dict(d)
        return None

    async def count_documents(self, filtro):
        return len([d for d in self.docs if _coincide(d, filtro)])


class _BaseDatos:
    def __init__(self):
        self._c = {}

    def __getitem__(self, n):
        return self

    def __getattr__(self, n):
        return self._c.setdefault(n, _Coleccion())


L = lambda v: [{"concepto": "x", "venta": v, "coste": 0}]


@pytest.fixture()
def rent(monkeypatch):
    """Carga routes/rentabilidad.py con Mongo simulado y datos de ejemplo."""
    bd = _BaseDatos()
    motor_ma = types.ModuleType("motor.motor_asyncio")
    motor_ma.AsyncIOMotorClient = lambda *a, **k: bd
    motor = types.ModuleType("motor")
    motor.motor_asyncio = motor_ma
    monkeypatch.setitem(sys.modules, "motor", motor)
    monkeypatch.setitem(sys.modules, "motor.motor_asyncio", motor_ma)

    servicios = types.ModuleType("services")
    servicios.__path__ = [os.path.join(BACKEND, "services")]
    monkeypatch.setitem(sys.modules, "services", servicios)
    jwt = types.ModuleType("services.jwt_service")
    jwt.ADMIN_ROLE_FLAGS = ["isAdmin"]

    async def _auth():
        return {"id": "u1", "isAdmin": True}
    jwt.require_auth = _auth
    monkeypatch.setitem(sys.modules, "services.jwt_service", jwt)
    dbc = types.ModuleType("services.db_client")
    dbc.get_db = lambda: bd
    monkeypatch.setitem(sys.modules, "services.db_client", dbc)

    rutas = types.ModuleType("routes")
    rutas.__path__ = [os.path.join(BACKEND, "routes")]
    monkeypatch.setitem(sys.modules, "routes", rutas)
    spec = importlib.util.spec_from_file_location(
        "routes.rentabilidad", os.path.join(BACKEND, "routes", "rentabilidad.py"))
    modulo = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "routes.rentabilidad", modulo)
    spec.loader.exec_module(modulo)

    bd._c["clients"] = _Coleccion([{"id": "c1", "codigo": "2759", "nombre": "MARIA JOSE GARCIA"}])
    bd._c["sale_fichas"] = _Coleccion([
        {"id": "f1", "docType": "factura", "ref": "LG26/101", "fecha": "2026-03-01",
         "cliente": "MARIA JOSE GARCIA", "clienteCodigo": "2759", "lines": L(10000.0)},
        # Guardada con el NOMBRE pero sin codigo: tiene que entrar igual.
        {"id": "f2", "docType": "factura", "ref": "LG26/102", "fecha": "2026-04-01",
         "cliente": "MARIA JOSE GARCIA", "clienteCodigo": "", "lines": L(5000.0)},
        # Abono: resta del facturado.
        {"id": "f3", "docType": "factura", "ref": "LG26/103", "fecha": "2026-05-01",
         "cliente": "MARIA JOSE GARCIA", "clienteCodigo": "2759", "lines": L(-1000.0)},
        # Presupuesto ya convertido en factura: contarlo duplicaria la venta.
        {"id": "f4", "docType": "presupuesto", "ref": "P-900", "fecha": "2026-02-01",
         "cliente": "MARIA JOSE GARCIA", "clienteCodigo": "2759", "lines": L(10000.0),
         "convertidoAId": "f1"},
        {"id": "z1", "docType": "factura", "ref": "LG26/999", "fecha": "2026-03-01",
         "cliente": "OTRO CLIENTE SL", "clienteCodigo": "3333", "lines": L(7777.0)},
    ])
    bd._c["ingresos_cuenta"] = _Coleccion([
        # Enlazada por id de ficha Y por codigo de cliente: UNA sola vez.
        {"id": "i1", "fecha": "2026-03-05", "importe": 4000.0, "cliente": "MARIA JOSE GARCIA",
         "clientCode": "2759", "targetId": "f1", "targetRef": "LG26/101", "targetType": "factura"},
        {"id": "i2", "fecha": "2026-06-01", "importe": 1500.0, "cliente": "MARIA JOSE GARCIA",
         "clientCode": "2759", "targetId": "", "targetRef": "", "targetType": ""},
        # Referencia con otro formato: debe casar con LG26/102.
        {"id": "i3", "fecha": "2026-04-10", "importe": 2000.0, "cliente": "", "clientCode": "",
         "targetId": "", "targetRef": "LG26 / 102", "targetType": "factura"},
        {"id": "z9", "fecha": "2026-03-05", "importe": 999.0, "cliente": "OTRO CLIENTE SL",
         "clientCode": "3333", "targetId": "z1", "targetRef": "LG26/999", "targetType": "factura"},
    ])
    bd._c["project_costs"] = _Coleccion([])
    return modulo


def test_saldo_por_codigo(rent):
    s = asyncio.run(rent.saldo_cliente(q="2759"))
    # 10000 + 5000 - 1000 (abono)
    assert s["facturado"] == 14000.0
    # 4000 (una vez, no dos) + 1500 + 2000
    assert s["cobrado"] == 7500.0, "una entrega se ha contado dos veces"
    assert s["saldo"] == 6500.0
    assert s["aplicadoAFacturas"] == 6000.0
    assert s["sinAplicarAFactura"] == 1500.0


def test_entra_la_factura_guardada_sin_codigo(rent):
    s = asyncio.run(rent.saldo_cliente(q="2759"))
    refs = [f["ref"] for f in s["facturas"]]
    assert "LG26/102" in refs, "se pierde la factura guardada con nombre pero sin codigo"
    assert len(s["facturas"]) == 3


def test_no_se_cuela_otro_cliente(rent):
    s = asyncio.run(rent.saldo_cliente(q="2759"))
    assert all("999" not in str(f["ref"]) for f in s["facturas"])
    assert all(i["importe"] != 999.0 for i in s["ingresos"])


def test_el_documento_convertido_queda_fuera_del_saldo(rent):
    s = asyncio.run(rent.saldo_cliente(q="2759"))
    assert [d["ref"] for d in s["otrosDocumentos"]] == ["P-900"]


def test_casa_la_referencia_con_otro_formato(rent):
    s = asyncio.run(rent.saldo_cliente(q="2759"))
    f2 = next(f for f in s["facturas"] if f["ref"] == "LG26/102")
    assert f2["cobrado"] == 2000.0, "'LG26 / 102' no ha casado con 'LG26/102'"


def test_buscar_por_nombre_da_lo_mismo(rent):
    por_codigo = asyncio.run(rent.saldo_cliente(q="2759"))
    por_nombre = asyncio.run(rent.saldo_cliente(q="MARIA JOSE"))
    assert por_nombre["saldo"] == por_codigo["saldo"]


def test_cliente_inexistente_da_404(rent):
    with pytest.raises(rent.HTTPException) as e:
        asyncio.run(rent.saldo_cliente(q="NO_EXISTE_XYZ"))
    assert e.value.status_code == 404


def test_el_buscador_no_duplica_al_mismo_cliente(rent):
    """Con facturas con y sin codigo, el cliente salia dos veces en la lista."""
    lst = asyncio.run(rent.clientes_con_saldo())
    assert lst["count"] == 2, f"clientes duplicados: {lst['items']}"
