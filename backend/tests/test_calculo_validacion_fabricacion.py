# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del expediente de validacion antes de fabricar.

Esta pantalla decide si un proyecto baja al taller. Si se equivoca en la
direccion facil --- decir "listo para fabricar" cuando falta algo --- es peor que
no existir, porque sustituye el criterio de una persona por una luz verde.

Lo que se protege:

1. "NO SE SABE" NO ES "CORRECTO". Si un modulo no trae fondo, eso no se aprueba
   por omision. Abajo, en el taller, alguien tendria que inventarselo --- y ese
   es exactamente el fallo que este ERP existe para evitar.

2. CADA AVISO DICE DONDE. Un "faltan medidas" a secas obliga a repasar el
   proyecto entero, y eso no se hace: se ignora. El aviso tiene que llevar al
   modulo concreto.

3. LO QUE BLOQUEA SE ELIGE. Si todo bloqueara, el circuito se saltaria entero a
   la primera urgencia y no volveria a usarse.
"""
import importlib.util
import os

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def vf():
    ruta = os.path.join(BACKEND, "services", "validacion_fabricacion.py")
    spec = importlib.util.spec_from_file_location("_validacion_fab", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def M(code="B60", w=60, h=80, d=58, finish="roble"):
    return {"code": code, "width": w, "height": h, "depth": d, "finish": finish}


def P(lineas=None):
    return {"itemsMontada": lineas if lineas is not None else [M()],
            "itemsDespiece": []}


def _check(r, clave):
    return next(c for c in r["checks"] if c["clave"] == clave)


# ─── El caso bueno ──────────────────────────────────────────────────────────

def test_un_proyecto_completo_se_libera(vf):
    r = vf.validar(P())
    assert r["puedeLiberar"] is True
    assert r["bloqueos"] == 0
    assert "Listo para fabricar" in r["resumen"]


# ─── "No se sabe" no es "correcto" ──────────────────────────────────────────

def test_un_proyecto_vacio_no_se_libera(vf):
    """CANDADO: sin lineas no hay nada que fabricar. Aprobarlo por no encontrar
    fallos seria el peor de los errores posibles."""
    r = vf.validar({"itemsMontada": [], "itemsDespiece": []})
    assert r["puedeLiberar"] is False
    assert _check(r, "medidas_modulos")["estado"] == vf.SIN_DATOS


def test_falta_una_medida_y_bloquea(vf):
    r = vf.validar(P([M(code="B60"), M(code="A90", h=None)]))
    assert r["puedeLiberar"] is False
    c = _check(r, "medidas_modulos")
    assert c["estado"] == vf.FALTA and c["bloquea"] is True
    assert "A90" in c["detalle"] and "alto" in c["detalle"]


def test_el_aviso_dice_en_que_modulo(vf):
    """CANDADO: sin el 'donde', el aviso obliga a repasar el proyecto entero."""
    r = vf.validar(P([M(code="B60"), M(code="A90", w=None)]))
    motivo = r["motivos"][0]
    assert "A90" in motivo["detalle"]
    assert motivo["donde"] is not None and motivo["donde"]["tipo"] == "linea"


# ─── El sentido de apertura, que es el hallazgo fino ────────────────────────

def test_un_codigo_que_sigue_como_D_I_no_tiene_mano_decidida(vf):
    """En MV, `D/I` es "derecha o izquierda": una referencia de tarifa, no un
    mueble. Si llega asi a fabrica, la mano la decide el taller a cara o cruz.
    """
    r = vf.validar(P([M(code="B60D/I")]))
    c = _check(r, "apertura")
    assert c["estado"] == vf.FALTA and c["bloquea"] is True
    assert "B60D/I" in c["detalle"]
    assert r["puedeLiberar"] is False


def test_una_mano_ya_elegida_pasa(vf):
    for cod in ("B60D", "B60I", "B60"):
        r = vf.validar(P([M(code=cod)]))
        assert _check(r, "apertura")["estado"] == vf.OK, cod


# ─── Distinguir "falta en una" de "no se captura en ninguna" ────────────────

def test_si_NINGUNA_linea_trae_fondo_es_falta_de_dato_no_error(vf):
    """Que ninguna lo traiga no significa que cada una lo haya perdido:
    significa que ese dato no se esta capturando. Bloquear ahi pararia todos
    los proyectos por un asunto de configuracion."""
    r = vf.validar(P([M(d=None), M(code="A90", d=None)]))
    c = _check(r, "fondos")
    assert c["estado"] == vf.SIN_DATOS and c["bloquea"] is False


def test_si_falta_en_UNA_sola_si_bloquea(vf):
    """Aqui si es un olvido concreto y localizable."""
    r = vf.validar(P([M(), M(code="A90", d=None)]))
    c = _check(r, "fondos")
    assert c["estado"] == vf.FALTA and c["bloquea"] is True
    assert "A90" in c["detalle"]


def test_lo_mismo_con_los_acabados(vf):
    todos = vf.validar(P([M(finish=""), M(code="A90", finish="")]))
    assert _check(todos, "acabados")["bloquea"] is False
    una = vf.validar(P([M(), M(code="A90", finish="")]))
    assert _check(una, "acabados")["bloquea"] is True


# ─── Lo que avisa pero no corta ─────────────────────────────────────────────

def test_una_linea_sin_codigo_avisa_pero_no_bloquea(vf):
    """Las lineas manuales (un trabajo a medida, un porte) no llevan codigo de
    tarifa y son legitimas: avisan para que alguien les busque equivalencia,
    pero no pueden parar la fabricacion."""
    r = vf.validar(P([M(), M(code="")]))
    c = _check(r, "codigos")
    assert c["estado"] == vf.FALTA and c["bloquea"] is False
    assert r["puedeLiberar"] is True
    assert r["pendientes"] >= 1


def test_lo_pendiente_no_se_cuenta_como_correcto(vf):
    """CANDADO: el resumen no puede dar por bueno lo que solo esta avisado."""
    r = vf.validar(P([M(), M(code="")]))
    assert _check(r, "codigos")["estado"] != vf.OK
    assert r["correctas"] < len(r["checks"])
    assert "pendiente" in r["resumen"]


# ─── Enganche con el control de cambios ─────────────────────────────────────

def test_un_cambio_sin_aprobar_bloquea_la_liberacion(vf):
    r = vf.validar(P(), pendientes_cambios=2)
    c = _check(r, "cambios")
    assert c["bloquea"] is True and "2 cambio" in c["detalle"]
    assert r["puedeLiberar"] is False


def test_los_checks_van_agrupados_para_la_pantalla(vf):
    r = vf.validar(P())
    assert set(r["grupos"]) == {"MEDIDAS", "DISEÑO", "FABRICACIÓN"}
