# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del reparto de incidencias por CAUSA.

Aqui SI se comprueba un calculo, y uno delicado: el porcentaje que va a
contestar "¿de donde salen nuestros fallos?". De ese numero salen decisiones
—cambiar de proveedor, revisar como se mide, tocar el proceso de fabrica— asi
que tiene que ser honesto o es peor que no tenerlo.

La trampa que se protege: repartir el 100 % entre las incidencias clasificadas
mientras la mayoria esta SIN clasificar. Con 10 tickets y solo 2 con causa,
decir "50 % son de medicion" es una cifra inventada con forma de dato. El
resumen tiene que decir SIEMPRE sobre cuantos se calcula (`clasificados`) y
cuantos se quedan fuera (`sinCausa`).

Y la regla que sostiene todo lo anterior: no se puede CERRAR una incidencia sin
decir de donde vino. Si esa puerta se cae, el campo se queda vacio y la
estadistica no vale nada.
"""
import importlib.util
import os
import sys
import types

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def pv(monkeypatch):
    """Carga postventa.py sustituyendo lo que necesita base de datos."""
    paquete = types.ModuleType("services")
    paquete.__path__ = [os.path.join(BACKEND, "services")]
    monkeypatch.setitem(sys.modules, "services", paquete)

    jwt = types.ModuleType("services.jwt_service")
    jwt.get_current_user = lambda: {}
    jwt.require_auth = lambda: {}
    monkeypatch.setitem(sys.modules, "services.jwt_service", jwt)

    dbc = types.ModuleType("services.db_client")
    dbc.get_db = lambda: None
    monkeypatch.setitem(sys.modules, "services.db_client", dbc)

    spec = importlib.util.spec_from_file_location(
        "routes_postventa", os.path.join(BACKEND, "routes", "postventa.py"))
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "routes_postventa", mod)
    spec.loader.exec_module(mod)
    return mod


def _t(causa=None):
    return {"causa": causa}


def test_cuenta_cada_causa_por_separado(pv):
    r = pv.resumen_causas([
        _t("error_medicion"), _t("error_medicion"), _t("error_medicion"),
        _t("error_fabricacion"),
    ])
    assert r["porCausa"] == {"error_medicion": 3, "error_fabricacion": 1}
    assert r["clasificados"] == 4
    assert r["sinCausa"] == 0
    assert r["principal"] == "error_medicion"


def test_el_porcentaje_es_sobre_las_clasificadas_y_lo_dice(pv):
    """CANDADO: 2 clasificadas de 10 son 50 % de DOS, no de diez.

    Es el caso que convierte un informe en una mentira: el numero es correcto
    y la lectura es falsa si no se ve el denominador.
    """
    tickets = [_t("error_medicion"), _t("error_fabricacion")] + [_t() for _ in range(8)]
    r = pv.resumen_causas(tickets)

    assert r["clasificados"] == 2, "el denominador son las clasificadas"
    assert r["sinCausa"] == 8, "hay que poder ver cuantas quedan fuera del calculo"
    assert r["porCausaPct"]["error_medicion"] == 50.0
    # Y lo que NO puede pasar: que el 50 % se haya calculado sobre los 10.
    assert r["porCausaPct"]["error_medicion"] != 10.0


def test_sin_ninguna_clasificada_no_divide_entre_cero(pv):
    r = pv.resumen_causas([_t(), _t(), _t()])
    assert r["porCausa"] == {}
    assert r["porCausaPct"] == {}
    assert r["clasificados"] == 0
    assert r["sinCausa"] == 3
    assert r["principal"] is None


def test_lista_vacia(pv):
    r = pv.resumen_causas([])
    assert r["clasificados"] == 0 and r["sinCausa"] == 0 and r["principal"] is None


def test_una_causa_inventada_no_cuenta_como_clasificada(pv):
    """Solo valen las causas del catalogo: si no, cada uno escribe la suya y el
    reparto deja de poder sumarse."""
    r = pv.resumen_causas([_t("culpa_de_juan"), _t("error_medicion")])
    assert r["porCausa"] == {"error_medicion": 1}
    assert r["sinCausa"] == 1


def test_no_se_puede_cerrar_sin_causa(pv):
    """CANDADO: es la puerta que hace que el campo se rellene de verdad."""
    assert pv.falta_causa_para_cerrar("cerrado", None) is True
    assert pv.falta_causa_para_cerrar("cerrado", "") is True
    assert pv.falta_causa_para_cerrar("cerrado", "loquesea") is True
    assert pv.falta_causa_para_cerrar("cerrado", "error_medicion") is False


@pytest.mark.parametrize("estado", ["abierto", "en_proceso", "espera_cliente", "resuelto"])
def test_los_demas_estados_no_exigen_causa(pv, estado):
    """Se pide UNA vez, al cerrar. Pedirla al abrir solo consigue que se
    rellene a boleo para pasar de pantalla, y eso envenena el dato."""
    assert pv.falta_causa_para_cerrar(estado, None) is False


def test_el_catalogo_cubre_toda_la_cadena(pv):
    """Las causas tienen que permitir separar de que eslabon viene el fallo:
    si no, todo acaba cayendo en 'error de fabricacion' por descarte."""
    for clave in ("error_medicion", "error_diseno", "error_fabricacion",
                  "error_proveedor", "problema_obra", "cambio_cliente"):
        assert clave in pv.CAUSAS, f"falta la causa {clave}"
