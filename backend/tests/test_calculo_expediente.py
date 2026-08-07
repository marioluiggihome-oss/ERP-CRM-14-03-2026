# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del expediente unico: el dinero NO VIAJA si no se puede ver.

Esta es la prueba mas importante del fichero, y no es de calculo: es de fuga.

El candado de Rentabilidad OCULTA los importes en pantalla (regla 9) y los
descuentos no salen en nada que vea un cliente (regla 5). Pero ocultar en el
navegador no es proteger: si el importe viaja en la respuesta, se ve abriendo
el inspector del navegador. En una tienda asociada eso es ensenar el margen a
quien no debe verlo, y no hay forma de saber que ha pasado.

Por eso aqui se comprueba que la clave NO ESTA --- no que valga 0. Un 0 es un
dato falso y ademas creible; un campo ausente es la verdad: esa persona no
tiene por que recibirlo.
"""
import importlib.util
import os

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def ex():
    ruta = os.path.join(BACKEND, "services", "expediente.py")
    spec = importlib.util.spec_from_file_location("_expediente", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PROYECTO = {
    "customerName": "María García", "budgetNumber": "P-001", "status": "aceptado",
    "totalPvp": 18500, "totalCoste": 10200, "margen": 44, "totalConIVA": 22385,
    "itemsMontada": [{"code": "B60"}], "itemsDespiece": [],
}

MASTER = {"isAdmin": True}
GERENTE = {"isGerente": True}
MONTADOR = {"isMontador": True}
TIENDA = {"isTienda": True}


# ─── LA FUGA ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("usuario", [MONTADOR, TIENDA, {}, None])
def test_a_quien_no_puede_ver_importes_NO_se_le_mandan(ex, usuario):
    """CANDADO: la clave 'importes' no puede existir siquiera."""
    exp = ex.montar(PROYECTO, usuario=usuario)
    assert "importes" not in exp, (
        "los importes viajan a alguien que no puede verlos: ocultarlos en "
        "pantalla no sirve de nada si estan en la respuesta"
    )
    assert exp["verImportes"] is False


@pytest.mark.parametrize("usuario", [MASTER, GERENTE])
def test_al_mando_si_se_le_mandan(ex, usuario):
    exp = ex.montar(PROYECTO, usuario=usuario)
    assert exp["importes"]["totalPvp"] == 18500
    assert exp["verImportes"] is True


def test_los_importes_no_se_ponen_a_cero_se_quitan(ex):
    """CANDADO: enmascarar con 0 es peor que no mandar nada --- un cero se lee
    como un dato real."""
    exp = ex.montar(PROYECTO, usuario=MONTADOR)
    texto = repr(exp)
    assert "18500" not in texto and "10200" not in texto
    assert "importes" not in exp


def test_las_lineas_tambien_pierden_los_importes(ex):
    lineas = [{"code": "B60", "quantity": 2, "totalPvp": 500, "margen": 30}]
    limpias = ex.limpiar_lineas(lineas, MONTADOR)
    assert limpias[0]["code"] == "B60" and limpias[0]["quantity"] == 2
    assert "totalPvp" not in limpias[0] and "margen" not in limpias[0]


def test_al_mando_las_lineas_van_enteras(ex):
    lineas = [{"code": "B60", "totalPvp": 500}]
    assert ex.limpiar_lineas(lineas, MASTER)[0]["totalPvp"] == 500


def test_el_permiso_usa_los_mismos_flags_que_el_resto_del_ERP(ex):
    """Dos definiciones de "mando" acabarian separandose con el tiempo."""
    for flag in ("isAdmin", "isResponsableDelegacion", "isGerente",
                 "isDirectorComercial", "isDirectorFabrica"):
        assert ex.puede_ver_importes({flag: True}) is True, flag
    assert ex.puede_ver_importes({"isComercial": True}) is False


# ─── Acciones pendientes ────────────────────────────────────────────────────

def _validacion(checks, puede=False):
    return {"checks": checks, "puedeLiberar": puede}


def test_cada_accion_dice_quien_la_resuelve(ex):
    v = _validacion([{"clave": "apertura", "etiqueta": "Sentidos de apertura",
                      "estado": "falta", "bloquea": True, "detalle": "B60D/I", "donde": {}}])
    a = ex.acciones_pendientes(v)[0]
    assert a["responsable"] == "Diseñador"
    assert a["accion"] == "Resolver"


def test_lo_que_bloquea_va_primero(ex):
    v = _validacion([
        {"clave": "codigos", "etiqueta": "Códigos", "estado": "falta", "bloquea": False},
        {"clave": "apertura", "etiqueta": "Apertura", "estado": "falta", "bloquea": True},
    ])
    acciones = ex.acciones_pendientes(v)
    assert acciones[0]["bloquea"] is True


def test_lo_correcto_no_genera_accion(ex):
    v = _validacion([{"clave": "acabados", "etiqueta": "Acabados", "estado": "ok"}])
    assert ex.acciones_pendientes(v) == []


def test_un_cambio_sin_aprobar_es_una_accion_de_gerencia(ex):
    a = ex.acciones_pendientes(_validacion([]),
                               [{"fecha": "2026-08-07T10:00:00", "motivo": ""}])[0]
    assert a["responsable"] == "Gerencia" and a["accion"] == "Revisar"
    assert a["bloquea"] is True


# ─── La etapa se deduce, no se teclea ───────────────────────────────────────

def test_un_borrador_esta_en_venta(ex):
    assert ex.etapa_actual({"status": "borrador"}, None) == "VENTA"


def test_aceptado_y_bloqueado_esta_en_validacion(ex):
    assert ex.etapa_actual({"status": "aceptado"}, {"puedeLiberar": False}) == "VALIDACIÓN"


def test_aceptado_y_liberado_pasa_a_fabricacion(ex):
    assert ex.etapa_actual({"status": "aceptado"}, {"puedeLiberar": True}) == "FABRICACIÓN"


def test_la_cabecera_trae_lo_que_se_lee_de_pie_en_obra(ex):
    exp = ex.montar(PROYECTO, usuario=MONTADOR)
    assert exp["cabecera"]["cliente"] == "María García"
    assert exp["cabecera"]["proyecto"] == "P-001"
    assert exp["etapas"][0] == "VENTA" and exp["etapas"][-1] == "CIERRE"
