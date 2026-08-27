# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Permisos de Rentabilidad: quien entra y quien no.

Protege el fallo del 03/08: el guardia de /api/rentabilidad aceptaba
`isController` y `canAccessRentabilidad`, pero esos dos permisos NUNCA viajaban
dentro del token, asi que en la practica solo pasaban los administradores. El
perfil CONTROLLER recibia un 403, el navegador metia ese {"detail": ...} donde
esperaba una lista y la pantalla se caia con "le.filter is not a function".

Si alguien vuelve a quitar esos permisos del token, estas pruebas fallan.

Mongo y jwt se simulan: no hace falta ni base de datos ni libreria de tokens.
"""
import asyncio
import importlib.util
import os
import sys
import types

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONTROLLER = {
    "id": "u-controller", "username": "CONTROLLER", "isController": True,
    "isAdmin": False, "isGerente": False,
}
JEFA = {"id": "u-jefa", "username": "JEFA", "isAdmin": True}
COMERCIAL = {"id": "u-com", "username": "COMERCIAL"}
CON_PERMISO = {"id": "u-per", "username": "PER", "canAccessRentabilidad": True}


class _Usuarios:
    def __init__(self, docs):
        self.docs = docs
        self.consultas = 0

    async def find_one(self, filtro, proj=None):
        self.consultas += 1
        for d in self.docs:
            if all(d.get(k) == v for k, v in filtro.items()):
                return dict(d)
        return None


class _BaseDatos:
    def __init__(self, usuarios):
        self.users = _Usuarios(usuarios)


@pytest.fixture()
def jwt_service(monkeypatch):
    """Carga services/jwt_service.py con un jwt de mentira y Mongo simulado."""
    falso_jwt = types.ModuleType("jwt")
    # El "token" es el propio dict: aqui se comprueba QUE VIAJA, no el cifrado.
    falso_jwt.encode = lambda payload, secreto, algorithm=None: dict(payload)
    falso_jwt.decode = lambda token, secreto, algorithms=None: dict(token)
    falso_jwt.ExpiredSignatureError = type("ExpiredSignatureError", (Exception,), {})
    falso_jwt.InvalidTokenError = type("InvalidTokenError", (Exception,), {})
    monkeypatch.setitem(sys.modules, "jwt", falso_jwt)

    motor_ma = types.ModuleType("motor.motor_asyncio")
    motor_ma.AsyncIOMotorClient = lambda *a, **k: None
    motor = types.ModuleType("motor")
    motor.motor_asyncio = motor_ma
    monkeypatch.setitem(sys.modules, "motor", motor)
    monkeypatch.setitem(sys.modules, "motor.motor_asyncio", motor_ma)

    servicios = types.ModuleType("services")
    servicios.__path__ = [os.path.join(BACKEND, "services")]
    monkeypatch.setitem(sys.modules, "services", servicios)

    base = _BaseDatos([CONTROLLER, JEFA, COMERCIAL, CON_PERMISO])
    dbc = types.ModuleType("services.db_client")
    dbc.get_db = lambda: base
    monkeypatch.setitem(sys.modules, "services.db_client", dbc)

    monkeypatch.setenv("JWT_SECRET", "secreto-de-prueba")
    spec = importlib.util.spec_from_file_location(
        "services.jwt_service", os.path.join(BACKEND, "services", "jwt_service.py"))
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "services.jwt_service", mod)
    spec.loader.exec_module(mod)
    mod._base_de_pruebas = base
    return mod


def _usuario_del_token(mod, ficha):
    """Recorrido completo: ficha de usuario → token → usuario que ve la API."""
    return mod._payload_to_user(mod.create_access_token(ficha))


def test_el_token_lleva_el_permiso_de_controller(jwt_service):
    u = _usuario_del_token(jwt_service, CONTROLLER)
    assert u["isController"] is True, "el permiso de CONTROLLER no viaja en el token"


def test_el_token_lleva_el_permiso_suelto_de_rentabilidad(jwt_service):
    u = _usuario_del_token(jwt_service, CON_PERMISO)
    assert u["canAccessRentabilidad"] is True, "canAccessRentabilidad no viaja en el token"


def test_el_controller_entra_en_rentabilidad(jwt_service):
    u = _usuario_del_token(jwt_service, CONTROLLER)
    assert asyncio.run(jwt_service.tiene_acceso_rentabilidad(u)) is True


def test_un_comercial_cualquiera_no_entra(jwt_service):
    u = _usuario_del_token(jwt_service, COMERCIAL)
    assert asyncio.run(jwt_service.tiene_acceso_rentabilidad(u)) is False, \
        "se ha abierto el informe de margenes a quien no debe verlo"


def test_los_administradores_entran_sin_consultar_la_base_de_datos(jwt_service):
    u = _usuario_del_token(jwt_service, JEFA)
    antes = jwt_service._base_de_pruebas.users.consultas
    assert asyncio.run(jwt_service.tiene_acceso_rentabilidad(u)) is True
    assert jwt_service._base_de_pruebas.users.consultas == antes, \
        "una consulta a la base de datos en cada peticion de un admin"


def test_un_token_antiguo_sin_el_permiso_sigue_funcionando(jwt_service):
    """Quien ya tenia sesion abierta no debe quedarse fuera hasta volver a entrar."""
    antiguo = {"id": "u-controller", "username": "CONTROLLER", "isAdmin": False}
    assert asyncio.run(jwt_service.tiene_acceso_rentabilidad(antiguo)) is True
    # Y queda completado, para el guardia de solo lectura de la misma peticion.
    assert antiguo["isController"] is True


def test_un_token_antiguo_de_quien_no_tiene_permiso_sigue_fuera(jwt_service):
    antiguo = {"id": "u-com", "username": "COMERCIAL"}
    assert asyncio.run(jwt_service.tiene_acceso_rentabilidad(antiguo)) is False


def test_un_usuario_que_ya_no_existe_no_entra(jwt_service):
    assert asyncio.run(jwt_service.tiene_acceso_rentabilidad({"id": "fantasma"})) is False
