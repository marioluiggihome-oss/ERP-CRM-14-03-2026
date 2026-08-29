# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL USUARIO DEL SERVIDOR SALE DE SU FICHA, NO DE UNA LISTA DE TRECE CAMPOS.

Este candado nace del fallo más caro encontrado en todo el proyecto, y explica
de golpe tres cosas que parecían no tener nada que ver.

`get_current_user` no leía al usuario: lo RECONSTRUÍA a partir del token, con
trece campos escritos a mano en 2025. Todo permiso añadido después no existía
para el backend, por muy marcado que estuviera en la ficha:

  · `esCooperativistaMontador` / `esCooperativistaComercial` no llegaban, así
    que `area_cooperativista.rol_de` devolvía None y «Mi área» le contestaba
    «esta área es de los cooperativistas: montadores y comerciales» AL PROPIO
    MONTADOR. El área entera no funcionó nunca para un socio de verdad — las
    pruebas le pasaban la ficha completa a mano, así que estaban en verde.

  · `canUseCascos` no llegaba, así que el corte del Presupuestador en el
    servidor (29/08) veía a TODO EL MUNDO sin permiso de Cocina Desmontada.

  · `isPrimaryAdmin` e `isMaster` no llegaban, así que `es_master` solo podía
    mirar `isAdmin`. Por eso quitarlo el 28/08 dejó al master fuera de su propia
    tarifa y los presupuestos salieron a 0,00 €: los otros dos flags no
    existían aquí. Y por eso el plan de «marcar `isPrimaryAdmin` y después
    estrechar la lista» habría dejado a la casa entera sin ver un euro, con la
    marca puesta en Mongo y el candado mirando a otro sitio.

Y HAY UNA SEGUNDA COSA, que es la que hace que esto no vuelva: leer la ficha
significa que quitar un permiso surte efecto YA. Antes había que esperar a que
la persona volviera a entrar —hasta 24 horas—, así que el master marcaba una
casilla, comprobaba, no pasaba nada, y no había forma de saber si el permiso
estaba mal o solo tardaba.

LO QUE NO PUEDE PASAR: que un problema de base de datos eche del ERP a todo el
mundo a la vez. Si la ficha no se puede leer, se sigue con lo que trae el token.
"""
import asyncio
import importlib.util
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

import pytest  # noqa: E402,F401


def _jwt_de_verdad():
    """El módulo REAL, leído del disco, pase lo que pase en `sys.modules`.

    `test_calculo_recarga_renders.py` mete un doble de `services.jwt_service` en
    `sys.modules` y —lo dice su propio comentario— lo deja ahí para el resto de
    la sesión de pytest. O sea que quien se importe después hereda el doble.

    Un `from services import jwt_service` normal aquí pasaba en solitario y
    fallaba en la suite entera, según el orden de los ficheros. Y esto es
    justo la prueba que NO puede depender del orden: es la del permiso.
    """
    ruta = os.path.join(RAIZ, "services", "jwt_service.py")
    spec = importlib.util.spec_from_file_location("_jwt_real_para_pruebas", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


J = _jwt_de_verdad()

# Los permisos con los que el ERP decide DINERO o ACCESO y que NO caben en la
# lista de trece campos del token. Si uno de estos no llega al servidor, algo
# se cierra o se abre sin que nadie lo haya decidido.
LOS_QUE_DECIDEN = (
    "esCooperativistaComercial",   # cobra comisión, y ve «Mi área»
    "esCooperativistaMontador",    # ídem
    "plataforma",                  # solo la cooperativa reparte comisiones
    "isPrimaryAdmin",              # la llave del dinero (tarifa MV, margen)
    "isMaster",                    # ídem
    "canUseCascos",                # Cocina Desmontada
    "canUsePresupuestador3",       # Cocina Montada 3
    "montadorId",                  # su ficha en la agenda de montajes
    "manoObraPorMueble",           # lo que cobra por mueble montado
)


class _Coleccion:
    def __init__(self, doc):
        self.doc = doc
        self.proyeccion = None

    async def find_one(self, filtro, proyeccion=None):
        self.proyeccion = proyeccion
        return dict(self.doc) if self.doc else None


class _Db:
    def __init__(self, doc):
        self.users = _Coleccion(doc)


def _con_ficha(monkeypatch, doc):
    db = _Db(doc)
    import services.db_client as dbc
    monkeypatch.setattr(dbc, "get_db", lambda: db)
    return db


FICHA = {
    "id": "u-montador-1",
    "username": "montador1",
    "password": "no-tendria-que-salir-de-aqui",
    "esCooperativistaMontador": True,
    "esCooperativistaComercial": False,
    "plataforma": "cooperativa",
    "canUseCascos": True,
    "canUsePresupuestador3": True,
    "isPrimaryAdmin": True,
    "isMaster": False,
    "montadorId": "m-7",
    "manoObraPorMueble": 20.0,
}


def _token_de(ficha):
    return J.verify_access_token(J.create_access_token(ficha))


def test_EL_USUARIO_TRAE_LOS_PERMISOS_CON_LOS_QUE_SE_DECIDE(monkeypatch):
    """El fallo, en una línea: el token no los lleva y antes no se leía la ficha."""
    _con_ficha(monkeypatch, FICHA)
    user = asyncio.run(J._usuario_del_token(_token_de(FICHA)))
    for clave in LOS_QUE_DECIDEN:
        assert clave in user, (
            f"«{clave}» no llega al servidor. Con eso, el ERP decide con un "
            "permiso que no ve: o cierra a quien debía entrar, o abre a quien no.")
        assert user[clave] == FICHA[clave], f"«{clave}» llega cambiado"


def test_UN_SOCIO_COOPERATIVISTA_ES_RECONOCIDO_COMO_TAL(monkeypatch):
    """La comprobación de arriba, pero con la función que de verdad decide.

    Es la que le contestaba al montador «esta área es de los cooperativistas».
    """
    from services import area_cooperativista as AC
    _con_ficha(monkeypatch, FICHA)
    user = asyncio.run(J._usuario_del_token(_token_de(FICHA)))
    assert AC.rol_de(user) == AC.MONTADOR, (
        "el servidor no reconoce como montador cooperativista a un usuario que "
        "lo es en su ficha: «Mi área» le da 403")
    assert AC.filtro_de(user) == {"montadorUserId": "u-montador-1"}


def test_EL_PRESUPUESTADOR_Y_EL_MASTER_ven_lo_que_hay_en_la_ficha(monkeypatch):
    """Las otras dos consecuencias del mismo fallo."""
    from services import master as M
    from services import presupuestador as P
    _con_ficha(monkeypatch, FICHA)
    user = asyncio.run(J._usuario_del_token(_token_de(FICHA)))
    assert P.puede_desmontada(user), (
        "`canUseCascos` no llega: el corte del Presupuestador en el servidor "
        "deja fuera de Cocina Desmontada a quien SÍ tiene el permiso")
    assert M.es_master(user), (
        "`isPrimaryAdmin` no llega: estrechar la lista del master dejaría a la "
        "casa entera sin ver un euro, con la marca puesta en Mongo")


def test_LA_FICHA_MANDA_TAMBIEN_SOBRE_LO_QUE_SI_VA_EN_EL_TOKEN(monkeypatch):
    """Quitarle `isAdmin` a alguien tiene que surtir efecto YA.

    `isAdmin` sí viaja en el token, así que aquí se juega el orden de la mezcla:
    si el token pisara a la ficha, un administrador al que se le acaba de retirar
    el permiso seguiría entrando al dinero de la casa hasta 24 horas después. Y
    al revés: devolvérselo tampoco funcionaría hasta que volviera a entrar.
    """
    from services import master as M
    _con_ficha(monkeypatch, dict(FICHA, isAdmin=False, isPrimaryAdmin=False,
                                 isMaster=False))
    user = asyncio.run(J._usuario_del_token(_token_de(dict(FICHA, isAdmin=True))))
    assert user["isAdmin"] is False, (
        "el token pisa a la ficha: quitar un permiso no surte efecto hasta que "
        "la persona vuelva a entrar")
    assert not M.es_master(user)


def test_LA_CONTRASENA_NO_SALE_DE_LA_FICHA(monkeypatch):
    """Ahora el usuario viaja por dentro de todas las rutas. Que no lleve el
    hash de la contraseña no es un detalle."""
    _con_ficha(monkeypatch, FICHA)
    user = asyncio.run(J._usuario_del_token(_token_de(FICHA)))
    assert "password" not in user, "el hash de la contraseña viaja en `current_user`"


def test_QUIEN_ERES_lo_dice_el_TOKEN_no_la_ficha(monkeypatch):
    """La ficha manda en los PERMISOS; el token manda en la IDENTIDAD.

    Si el `id` saliera del documento, bastaría con que una ficha trajera otro
    `id` dentro para suplantar a alguien. Se lee POR id y se devuelve ESE id.
    """
    _con_ficha(monkeypatch, dict(FICHA, id="otro-usuario", username="otro"))
    user = asyncio.run(J._usuario_del_token(_token_de(FICHA)))
    assert user["id"] == "u-montador-1"
    assert user["username"] == "montador1"


def test_SI_LA_BASE_DE_DATOS_FALLA_no_se_echa_a_nadie(monkeypatch):
    """Un Mongo caído no puede dejar al ERP entero sin sesión."""
    class _Roto:
        @property
        def users(self):
            raise RuntimeError("mongo caído")
    import services.db_client as dbc
    monkeypatch.setattr(dbc, "get_db", lambda: _Roto())
    user = asyncio.run(J._usuario_del_token(_token_de(FICHA)))
    assert user["id"] == "u-montador-1", "un fallo de base de datos ha echado al usuario"
    assert user["username"] == "montador1"


def test_una_CUENTA_BORRADA_no_se_inventa_permisos(monkeypatch):
    _con_ficha(monkeypatch, None)
    user = asyncio.run(J._usuario_del_token(_token_de(FICHA)))
    assert user["id"] == "u-montador-1"
    assert not user.get("esCooperativistaMontador")


def test_QUITAR_UN_PERMISO_SURTE_EFECTO_YA(monkeypatch):
    """Antes había que esperar a que la persona volviera a entrar: hasta 24
    horas con un permiso que el master creía haber quitado."""
    from services import presupuestador as P
    # Sin los flags de master: al master no se le cierra nada, así que con ellos
    # esta prueba pasaría por el motivo equivocado.
    _con_ficha(monkeypatch, dict(FICHA, canUseCascos=False, isPrimaryAdmin=False))
    user = asyncio.run(J._usuario_del_token(_token_de(FICHA)))   # el token dice que sí
    assert not P.puede_desmontada(user), (
        "quitar un permiso en la ficha no surte efecto hasta que la persona "
        "vuelva a entrar: eso no es un permiso, es una sugerencia con retardo")


def test_las_DOS_PUERTAS_leen_la_ficha():
    """`get_current_user` y `require_auth`. Cerrar una y dejar la otra abierta
    es peor que no cerrar ninguna: el mismo usuario tendría permisos distintos
    según por qué endpoint entre."""
    import inspect
    cuerpo = inspect.getsource(J)
    for puerta in ("async def get_current_user", "async def require_auth"):
        i = cuerpo.index(puerta)
        j = cuerpo.index("\nasync def ", i + 10)
        assert "_usuario_del_token(payload)" in cuerpo[i:j], (
            f"«{puerta.split()[-1]}» sigue reconstruyendo el usuario del token "
            "en vez de leer su ficha")
