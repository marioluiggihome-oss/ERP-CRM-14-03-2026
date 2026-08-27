# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: «cerrar sesiones» tiene que ECHAR A LA GENTE de verdad.

14/08/2026, el master: «cierra sesiones abiertas de usuarios» y «saca a los
usuarios q estén dentro».

LO QUE HABÍA
------------
Se entra con un JWT firmado, válido 24 horas. `require_auth` comprobaba la
FIRMA y la CADUCIDAD, y nada más. Existe una colección `active_sessions`, pero
solo se lee AL ENTRAR, para impedir que un usuario no administrador tenga dos
sesiones a la vez.

O sea que `/auth/logout` —que vacía `active_sessions`— NO echaba a nadie: el
token seguía valiendo hasta 24 horas después. Quien estaba dentro, seguía
dentro. Y lo peor es que PARECÍA que funcionaba: la colección se quedaba vacía,
la pantalla decía «sesión cerrada», y el usuario seguía operando.

La única forma real de echar a todo el mundo era cambiar `JWT_SECRET` en Railway
y reiniciar: un mazazo que obliga a redesplegar y no distingue entre uno y todos.

LO QUE SE PROTEGE
-----------------
1. Que la revocación SE COMPRUEBE en cada petición. Si `require_auth` deja de
   mirarla, cerrar sesiones vuelve a no hacer nada — sin dar ningún error.
2. Que echar a la gente sea cosa del MASTER, y con la guarda en el endpoint.
3. Que una base de datos que no contesta NO eche a todo el mundo, y que además
   no deje el ERP a rastras reintentando en cada petición.
"""
import asyncio
import os
import sys
import types

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICIO = os.path.join(BACKEND, "services", "sesiones.py")
JWT = os.path.join(BACKEND, "services", "jwt_service.py")
RUTAS = os.path.join(BACKEND, "routes", "auth_routes.py")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def _apartar(*nombres):
    """Aparta `services`/`routes` de sys.modules y devuelve lo apartado.

    Hay que apartarlos porque otras pruebas los dejan sustituidos por falsos y
    aquí se necesita el servicio DE VERDAD. Pero hay que DEVOLVERLOS al
    terminar: borrarlos sin más dejaba sin módulos a la prueba siguiente, y
    entonces fallaba una que no tenía nada que ver (la de recarga de renders).
    Un candado que rompe a otro no vale para nada: se borra el que molesta y se
    pierden los dos."""
    apartados = {}
    for n in list(sys.modules):
        if any(n == x or n.startswith(x + ".") for x in nombres):
            apartados[n] = sys.modules.pop(n)
    return apartados


def _devolver(apartados):
    for n in list(sys.modules):
        if any(n == x or n.startswith(x + ".") for x in ("services", "routes")):
            del sys.modules[n]
    sys.modules.update(apartados)


class _Col:
    def __init__(self):
        self.doc = None
        self.borradas = 0

    async def find_one(self, *a, **k):
        return self.doc

    async def update_one(self, q, u, upsert=False):
        self.doc = self.doc or {"_id": "sesiones"}
        for clave, valor in (u.get("$set") or {}).items():
            if "." in clave:
                a1, a2 = clave.split(".", 1)
                self.doc.setdefault(a1, {})[a2] = valor
            else:
                self.doc[clave] = valor

    async def delete_many(self, q):
        self.borradas += 1


class _DB:
    def __init__(self):
        self.cols = {}

    def __getitem__(self, nombre):
        return self.cols.setdefault(nombre, _Col())

    def __getattr__(self, nombre):
        return self[nombre]


@pytest.fixture()
def entorno(monkeypatch):
    """Servicio real, base de datos falsa en memoria."""
    monkeypatch.setenv("JWT_SECRET", "candado-cierre-sesiones-0123456789abcdefghij")
    apartados = _apartar("services", "routes")
    import services.db_client as dbc
    import services.sesiones as ses
    from services.jwt_service import create_access_token, verify_access_token
    db = _DB()
    monkeypatch.setattr(dbc, "get_db", lambda: db)
    ses.invalidar_cache()
    yield types.SimpleNamespace(ses=ses, db=db, crear=create_access_token,
                                leer=verify_access_token)
    ses.invalidar_cache()
    _devolver(apartados)


USUARIO = {"id": "user-master-mario", "username": "MARIO", "isAdmin": True}


# ─── 1. Echar de verdad ─────────────────────────────────────────────────────

def test_cerrar_todas_invalida_los_tokens_ya_emitidos(entorno):
    """CANDADO PRINCIPAL. Este es EL comportamiento que se pidió."""
    async def prueba():
        p = entorno.leer(entorno.crear(USUARIO))
        assert await entorno.ses.token_revocado(p) is False, \
            "un token recien emitido no puede estar revocado"
        # El corte se toma AHORA; el token se emitio en un segundo anterior.
        await asyncio.sleep(1.1)
        await entorno.ses.cerrar_todas(motivo="prueba")
        assert await entorno.ses.token_revocado(p) is True, (
            "el token de antes del cierre SIGUE valiendo: «cerrar sesiones» no "
            "echa a nadie, igual que antes")
    asyncio.run(prueba())


def test_quien_vuelve_a_entrar_pasa_sin_problema(entorno):
    """Si el corte echara también a los que vuelven, nadie podría entrar y el
    ERP quedaria cerrado a cal y canto — master incluido."""
    async def prueba():
        await entorno.ses.cerrar_todas(motivo="prueba")
        await asyncio.sleep(1.1)
        nuevo = entorno.leer(entorno.crear(USUARIO))
        assert await entorno.ses.token_revocado(nuevo) is False, \
            "tras cerrar sesiones ya no se puede volver a entrar: ERP bloqueado"
    asyncio.run(prueba())


def test_cerrar_a_uno_no_echa_a_los_demas(entorno):
    async def prueba():
        mario = entorno.leer(entorno.crear(USUARIO))
        pepe = entorno.leer(entorno.crear({"id": "u-pepe", "username": "PEPE"}))
        await asyncio.sleep(1.1)
        await entorno.ses.cerrar_de("user-master-mario", motivo="prueba")
        assert await entorno.ses.token_revocado(mario) is True, "no se ha echado a quien tocaba"
        assert await entorno.ses.token_revocado(pepe) is False, \
            "cerrar la sesion de UNO ha echado a todos los demas"
    asyncio.run(prueba())


def test_al_cerrar_se_limpia_tambien_la_sesion_unica(entorno):
    """`active_sessions` decide si un usuario puede volver a entrar. Si se queda
    con una sesion fantasma, el usuario echado no puede ni volver."""
    async def prueba():
        await entorno.ses.cerrar_todas(motivo="prueba")
        assert entorno.db["active_sessions"].borradas > 0, \
            "no se limpio active_sessions: quedarian sesiones fantasma"
    asyncio.run(prueba())


# ─── 2. Que alguien lo compruebe en cada peticion ───────────────────────────

@pytest.mark.parametrize("guardia", ["get_current_user", "require_auth"])
def test_el_guardia_comprueba_la_revocacion(guardia):
    """Sin esto, todo lo demas es decorado: el token revocado seguiria entrando
    y la pantalla diria que las sesiones se han cerrado."""
    src = _leer(JWT)
    i = src.index(f"async def {guardia}(")
    cuerpo = src[i:src.index("\nasync def ", i + 10)]
    assert "token_revocado" in cuerpo, (
        f"`{guardia}` ya no mira si el token esta revocado: cerrar sesiones "
        f"vuelve a no echar a nadie, y sin dar ningun error")


def test_el_token_lleva_la_hora_de_emision():
    """Todo esto se apoya en `iat`. Sin el, no hay forma de saber si un token es
    anterior o posterior al cierre."""
    src = _leer(JWT)
    i = src.index("def create_access_token")
    assert '"iat"' in src[i:i + 1600], \
        "el token ya no lleva `iat`: no se puede saber si es anterior al cierre"


# ─── 3. Echar a la gente es cosa del master ─────────────────────────────────

@pytest.mark.parametrize("endpoint", [
    "/auth/sesiones/cerrar-todas",
    "/auth/sesiones/cerrar/{user_id}",
    "/auth/sesiones",
])
def test_solo_el_master_puede_cerrar_sesiones(endpoint):
    """La guarda va en el ENDPOINT. Esconder el boton no cierra ninguna puerta."""
    src = _leer(RUTAS)
    i = src.index(f'"{endpoint}"')
    cuerpo = src[i:i + 1400]
    assert "_exigir_master" in cuerpo, (
        f"{endpoint} ya no exige master: cualquiera con sesion podria echar del "
        f"ERP a toda la plantilla")


# ─── 4. Una base caida no puede echar a nadie (ni frenar el ERP) ────────────

def test_si_no_se_puede_leer_el_corte_no_se_echa_a_nadie(monkeypatch):
    """Esto es una REVOCACION, no la autenticacion: la firma y la caducidad ya
    se comprobaron. Dejar a todo el mundo fuera porque no se puede leer una
    fecha seria un remedio peor que la enfermedad."""
    monkeypatch.setenv("JWT_SECRET", "candado-cierre-sesiones-0123456789abcdefghij")
    apartados = _apartar("services", "routes")
    import services.db_client as dbc
    import services.sesiones as ses
    from services.jwt_service import create_access_token, verify_access_token

    def revienta():
        raise RuntimeError("la base no contesta")

    monkeypatch.setattr(dbc, "get_db", revienta)
    ses.invalidar_cache()
    p = verify_access_token(create_access_token(USUARIO))
    assert asyncio.run(ses.token_revocado(p)) is False, \
        "una base de datos que no contesta esta echando a todo el mundo del ERP"
    ses.invalidar_cache()
    _devolver(apartados)


def test_el_fallo_de_la_base_tambien_se_cachea():
    """Cuando Mongo no contesta, cada intento se come el tiempo de espera
    entero. Sin cachear el fallo, CADA peticion del ERP lo pagaria y la
    aplicacion se arrastraria — un problema mas gordo que el que se resolvia."""
    src = _leer(SERVICIO)
    assert "SEGUNDOS_CACHE_FALLO" in src, (
        "el fallo de lectura ya no se cachea: con la base caida, cada peticion "
        "esperara el tiempo de espera completo y el ERP ira a rastras")
    i = src.index("except Exception")
    cuerpo = src[i:i + 900]
    assert '_cache["datos"] = datos' in cuerpo, \
        "el camino de error ya no guarda nada en la cache"
