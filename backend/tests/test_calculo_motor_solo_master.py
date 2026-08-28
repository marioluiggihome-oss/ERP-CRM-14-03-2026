# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL MOTOR DE RENDER LO ELIGE EL MASTER, Y SE COMPRUEBA EN EL SERVIDOR.

La pantalla ya lo hacía bien: el desplegable de motores solo se le pinta al
master y a los demás les ofrece «IA 1» a secas (CLAUDE.md, regla 1: «IA 1 es la
de producción y es la única que ve un usuario que no sea master»).

Lo que faltaba es el otro lado. El motor viaja en el CUERPO de la petición y se
pasaba tal cual al servicio de render sin mirar quién lo mandaba, así que
cualquier usuario con la sesión iniciada podía pedir `banana_pro` —la IA 7, que
cuesta 3,3 veces más por render— desde fuera de la pantalla. Lo dice el propio
repositorio a cuenta de la tarifa MV: esconder un botón no cierra una API.

Y había una segunda mitad: el contador de créditos cobraba por TIPO de llamada
(«render»), no por motor, o sea que un render de IA 7 descontaba lo mismo que
uno de IA 1. El contador decía diez y en el proveedor se habían gastado
treinta y tres.

Esta prueba comprueba LAS DOS MITADES, y comprueba también que al master no se
le ha cerrado la puerta de paso — que sería romper sus motores de pruebas.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from routes.ai_engine import MOTOR_DE_PRODUCCION, motor_permitido  # noqa: E402
from services.ai_usage import coste_de_motor  # noqa: E402

MASTER = {"id": "u-1", "username": "master", "isMaster": True}
ADMIN = {"id": "u-2", "username": "jefe", "isAdmin": True}
# OJO CON ESTE: gerente y director comercial NO son master. Si el candado se
# escribiera con `ADMIN_ROLE_FLAGS` en vez de con `_es_master`, este usuario
# pasaría — y los motores de pruebas son del master, no de la dirección.
GERENTE = {"id": "u-3", "username": "gerente", "isGerente": True, "isDirectorComercial": True}
COMERCIAL = {"id": "u-4", "username": "ana"}

MOTORES_DE_PRUEBAS = ("banana_pro", "flux", "manus", "gemini_premium")


@pytest.mark.parametrize("motor", MOTORES_DE_PRUEBAS)
def test_quien_no_es_master_no_puede_pedir_un_motor_de_pruebas(motor):
    for usuario in (COMERCIAL, GERENTE):
        elegido = motor_permitido(usuario, motor)
        assert elegido == MOTOR_DE_PRODUCCION, (
            f"«{usuario['username']}» ha conseguido el motor '{motor}' pidiéndolo "
            f"por API (le ha salido '{elegido}'). La pantalla no se lo ofrece, "
            "pero la API se lo daba: eso es exactamente lo que hay que cerrar.")


@pytest.mark.parametrize("motor", MOTORES_DE_PRUEBAS)
def test_el_master_si_puede_usar_sus_motores_de_pruebas(motor):
    """La otra mitad: cerrar la puerta no puede dejar al master sin sus motores."""
    for usuario in (MASTER, ADMIN):
        assert motor_permitido(usuario, motor) == motor, (
            f"al master se le ha bloqueado el motor '{motor}'. Son SUS motores de "
            "pruebas (CLAUDE.md, regla 1) y los necesita para comparar.")


def test_sin_motor_pedido_no_se_fuerza_ninguno():
    """Sin `provider` manda el de por defecto del servicio, como siempre."""
    assert motor_permitido(COMERCIAL, None) is None
    assert motor_permitido(MASTER, "") is None


def test_la_ia1_le_sigue_valiendo_a_todo_el_mundo():
    for usuario in (COMERCIAL, GERENTE, MASTER):
        assert motor_permitido(usuario, "gemini") == "gemini"


def test_un_render_de_la_ia7_cuesta_mas_creditos_que_uno_de_la_ia1():
    """3,3x de coste real tiene que ser 3,3x de créditos, o el contador miente."""
    ia1 = coste_de_motor("render", 1, "gemini")
    ia7 = coste_de_motor("render", 1, "banana_pro")
    assert ia1 == 1, f"un render normal ha dejado de costar 1 crédito ({ia1})"
    assert ia7 > ia1, (
        f"un render de la IA 7 sigue costando lo mismo que uno de la IA 1 ({ia7} "
        "vs {ia1}). Cuesta 3,3 veces más de verdad: el contador se queda corto y "
        "la factura del proveedor no cuadra con lo que dice el ERP.")
    assert ia7 == 4, (
        f"se esperaba redondear 3,3 hacia arriba (4 créditos), y salen {ia7}. "
        "Se redondea hacia arriba a propósito: nadie regala el trozo suelto.")


def test_lo_que_no_es_un_render_no_se_multiplica():
    """Un análisis de visión no cambia de precio por el motor de imagen."""
    assert coste_de_motor("vision", 0, "banana_pro") == 0
    assert coste_de_motor("vision", 2, "banana_pro") == 2


def test_un_motor_desconocido_no_encarece_ni_abarata():
    assert coste_de_motor("render", 1, "loquesea") == 1
    assert coste_de_motor("render", 1, None) == 1


def test_las_tres_rutas_de_render_pasan_por_el_candado():
    """Nadie puede colar `provider` sin filtrar: se mira el fichero entero."""
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "routes", "ai_engine.py")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    assert "provider=request.provider" not in cuerpo, (
        "hay una ruta que vuelve a pasar el motor pedido SIN comprobar quién lo "
        "pide. Tiene que ir por `motor_permitido(user, ...)`.")
    assert cuerpo.count("provider=motor_permitido(user, request.provider)") == 3, (
        "deberían ser tres rutas de render las que pasan por el candado "
        "(render, render/compose y render/orbit)")
