# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del plan de negocio: QUE NO LO VEA NADIE MAS QUE EL MASTER.

QUE HAY AQUI DENTRO
-------------------
El precio de compra del casco, el descuento del proveedor, el coste por hora de
la gente, el margen por canal y la estructura entera de la empresa. Es, con
diferencia, lo mas sensible que guarda el ERP.

QUIEN NO ENTRA
--------------
Un GERENTE y un DIRECTOR COMERCIAL entran a Cascos y a Rentabilidad por
proyecto, pero NO a esto. La lista `ADMIN_ROLE_FLAGS` que se usa en medio ERP los
incluye — por eso aqui NO se usa esa lista, sino una corta y escrita a mano.

Y LA GUARDA VA EN EL BACKEND
----------------------------
Esconder el boton del menu no cierra ninguna puerta: basta con llamar a la API a
mano. Si algun dia la comprobacion se queda solo en la pantalla, el cierre es de
adorno. Eso es lo que vigila este fichero.
"""
import importlib
import os
import re
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND = os.path.join(RAIZ, "backend")
RUTA = os.path.join(BACKEND, "routes", "plan_negocio.py")
PANTALLA = os.path.join(RAIZ, "frontend", "src", "components", "PlanNegocio.jsx")
APP = os.path.join(RAIZ, "frontend", "src", "App.js")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def _sin_comentarios_py(src):
    """El codigo de verdad, sin docstrings ni comentarios.

    Hace falta porque estas pruebas buscan nombres prohibidos —`ADMIN_ROLE_FLAGS`
    y compania— y esos nombres aparecen tambien en las explicaciones de por que
    NO se usan. Sin esto, la prueba se dispara contra su propio comentario.
    """
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    return re.sub(r"#[^\n]*", "", src)


def _sin_comentarios_jsx(src):
    src = re.sub(r"/\*[\s\S]*?\*/", "", src)
    return re.sub(r"^\s*//[^\n]*", "", src, flags=re.M)


# Los paquetes que otras pruebas SUSTITUYEN por modulos de mentira para poder
# probar sin Mongo ni autenticacion.
_A_LIMPIAR = ("services", "routes", "models")


def _apartar_los_falsos():
    """Se lleva de en medio los modulos de mentira antes de importar de verdad.

    Sin esto, esta prueba pasaba o fallaba SEGUN EL ORDEN en que pytest ejecutara
    los ficheros: si antes habia corrido otra que sustituye `services`, el
    `require_auth` de verdad no se podia importar, el router se quedaba sin
    guarda y la prueba cantaba un agujero que no existia. Una prueba que un dia
    dice una cosa y otro la contraria es peor que no tenerla, porque enseinia a
    no hacerle caso.
    """
    guardados = {}
    for nombre in list(sys.modules):
        if nombre in _A_LIMPIAR or any(nombre.startswith(p + ".") for p in _A_LIMPIAR):
            guardados[nombre] = sys.modules.pop(nombre)
    return guardados


@pytest.fixture(scope="module")
def modulo():
    os.environ.setdefault("JWT_SECRET", "solo_para_probar")
    os.environ.setdefault("MONGO_URL", "mongodb://127.0.0.1:27017")
    os.environ.setdefault("DB_NAME", "pruebas")
    if BACKEND not in sys.path:
        sys.path.insert(0, BACKEND)

    guardados = _apartar_los_falsos()
    mod = importlib.import_module("routes.plan_negocio")
    yield mod
    # Y al salir se deja el escenario como estaba para las que vengan detras.
    _apartar_los_falsos()
    sys.modules.update(guardados)


# ─── 1. Quien es master, y quien no ─────────────────────────────────────────

def test_solo_el_master_pasa(modulo):
    """CANDADO PRINCIPAL."""
    for flag in ("isAdmin", "isPrimaryAdmin", "isMaster"):
        assert modulo._es_master({flag: True}) is True, f"{flag} deberia entrar"


def test_un_gerente_NO_pasa(modulo):
    """Un gerente ve Cascos. Aqui no entra: por aqui pasa el coste de compra."""
    for flag in ("isGerente", "isDirectorComercial", "isDirectorFabrica",
                 "isResponsableDelegacion", "isRepresentative", "isController",
                 "isMontador", "isFabrica"):
        assert modulo._es_master({flag: True}) is False, (
            f"{flag} esta entrando al plan de negocio: veria el coste de compra "
            "de los cascos y el margen")


def test_sin_usuario_no_pasa(modulo):
    assert modulo._es_master(None) is False
    assert modulo._es_master({}) is False


def test_no_se_usa_la_lista_ancha_de_roles(modulo):
    """`ADMIN_ROLE_FLAGS` incluye gerente y director comercial. Usarla aqui
    abriria el plan a media empresa sin que nadie se diera cuenta."""
    src = _sin_comentarios_py(_leer(RUTA))
    assert "ADMIN_ROLE_FLAGS" not in src, (
        "el plan de negocio ha pasado a usar la lista ancha de roles: entrarian "
        "gerente y director comercial")
    assert modulo._MASTER_FLAGS == ("isAdmin", "isPrimaryAdmin", "isMaster"), (
        "la lista del master ha cambiado. Si es a proposito, hay que tocarla "
        "tambien en `services/master.py` y en las otras copias — eso lo vigila "
        "`test_calculo_master_unico.py`")


# ─── 2. La guarda esta en TODOS los endpoints ───────────────────────────────

def test_todos_los_endpoints_exigen_master(modulo):
    """No basta con cerrar el que se lee: el de guardar, el de calcular y el de
    descargar el Excel llevan lo mismo dentro."""
    src = _leer(RUTA)
    # Cada funcion decorada con @router.* tiene que llamar a _exigir_master.
    trozos = re.split(r"@router\.(?:get|put|post|delete)\(", src)[1:]
    assert len(trozos) >= 4, "faltan endpoints por revisar"
    for trozo in trozos:
        cuerpo = trozo.split("@router.")[0]
        assert "_exigir_master(current_user)" in cuerpo, (
            "un endpoint del plan de negocio no comprueba que sea el master:\n"
            + cuerpo[:200])


def test_el_router_ademas_exige_estar_identificado(modulo):
    assert getattr(modulo.router, "dependencies", None), (
        "el router ha perdido la guarda de identidad: cualquiera con la URL "
        "llegaria hasta la comprobacion de master con un usuario vacio")


def test_las_rutas_estan_donde_se_espera(modulo):
    caminos = {(tuple(sorted(r.methods - {"HEAD", "OPTIONS"})), r.path)
               for r in modulo.router.routes if getattr(r, "methods", None)}
    assert (("GET",), "/plan-negocio") in caminos
    assert (("PUT",), "/plan-negocio") in caminos
    assert (("POST",), "/plan-negocio/calcular") in caminos
    assert (("GET",), "/plan-negocio/excel") in caminos


def test_el_plan_esta_enchufado_al_servidor():
    """Un modulo de rutas que nadie incluye no existe, y no da ningun error."""
    src = _leer(os.path.join(BACKEND, "server.py"))
    assert "from routes.plan_negocio import router as plan_negocio_router" in src
    assert "api_router.include_router(plan_negocio_router)" in src


# ─── 3. La pantalla tambien, y ademas ───────────────────────────────────────

def test_la_pantalla_comprueba_el_master_por_su_cuenta():
    """Esconder el boton no basta, pero enseniar la pantalla a quien no debe
    tampoco: se veria la estructura de casillas y los rotulos."""
    src = _leer(PANTALLA)
    assert "isPrimaryAdmin" in src and "isMaster" in src
    assert "solo del master" in src


def test_el_boton_del_menu_solo_le_sale_al_master():
    src = _sin_comentarios_jsx(_leer(APP))
    i = src.index("currentTab: 'planNegocio'")
    trozo = src[max(0, i - 600):i]
    assert "isMaster" in trozo and "isPrimaryAdmin" in trozo, (
        "el boton del plan de negocio le sale a mas gente de la que puede entrar")
    for prohibido in ("isGerente", "canAccessRentabilidad"):
        assert prohibido not in trozo, (
            f"el boton usa `{prohibido}`: se lo enseniaria a quien luego recibe "
            "un 403, que es la peor forma de cerrar una puerta")


# ─── 4. Lo calculado no se guarda ───────────────────────────────────────────

def test_solo_se_guarda_lo_que_escribe_el_master():
    """Si se guardara tambien el resultado, un dia quedaria un numero viejo al
    lado de un dato nuevo y nadie sabria cual manda."""
    src = _leer(RUTA)
    i = src.index("async def guardar")
    cuerpo = src[i:src.index("@router.post", i)]
    assert '"datos": datos' in cuerpo
    assert '"resultado":' not in cuerpo.split("return")[0], (
        "se esta guardando el resultado calculado: se quedaria viejo en cuanto "
        "cambie una casilla")


def test_el_plan_nuevo_no_trae_ni_un_precio_inventado(modulo):
    """CANDADO. Una cifra de ejemplo en una casilla acaba viajando al plan final
    sin que nadie recuerde de donde salio."""
    vacio = modulo._vacio()
    for ref in vacio["referencias"]:
        for clave, v in ref.items():
            if clave == "nombre":
                continue
            assert v is None, f"el plan nuevo trae {clave}={v} en {ref['nombre']}"
    assert vacio["capacidad"]["costeHoraPersona"] is None
    assert all(v is None for v in vacio["estructura"].values())
    assert all(v is None for v in vacio["inversion"].values())


def test_el_plan_nuevo_SI_trae_lo_que_ya_decidio_el_master(modulo):
    """2 personas, 3 muebles/hora, 7 h/dia, L-V y 1.600 horas al anio no son
    invenciones: son datos suyos."""
    cap = modulo._vacio()["capacidad"]
    assert (cap["personas"], cap["mueblesHora"], cap["horasDia"],
            cap["diasSemana"], cap["horasAno"]) == (2, 3, 7, 5, 1600)


def test_la_productividad_de_3_y_4_personas_nace_en_blanco(modulo):
    """Es el numero que hunde un plan si se supone en vez de medirse."""
    escenarios = modulo._vacio()["escenarios"]
    assert escenarios[0]["mueblesHora"] == 3
    for e in escenarios[1:]:
        assert e["mueblesHora"] is None, (
            f"el escenario de {e['personas']} personas ya trae una productividad "
            "inventada")
