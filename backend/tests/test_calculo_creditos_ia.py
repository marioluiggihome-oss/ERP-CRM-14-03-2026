"""Créditos de IA: los renders comprados NO caducan.

Protege el fallo que se corrigió el 02/08: los packs se guardaban en la ficha del
mes, así que quien compraba 100 renders el día 28 y usaba 30 perdía los otros 70,
ya pagados. Si alguien vuelve a atar el saldo al mes, estas pruebas fallan.

Mongo se sustituye por un doble en memoria: no hace falta base de datos.
"""
import asyncio
import importlib.util
import os
import sys
import types

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _coincide(doc, filtro):
    return all(doc.get(k) == v for k, v in filtro.items())


class _Coleccion:
    def __init__(self):
        self.docs = []

    async def find_one(self, filtro, proj=None):
        for d in self.docs:
            if _coincide(d, filtro):
                return dict(d)
        return None

    async def update_one(self, filtro, upd, upsert=False):
        for d in self.docs:
            if _coincide(d, filtro):
                for k, v in upd.get("$inc", {}).items():
                    d[k] = d.get(k, 0) + v
                d.update(upd.get("$set", {}))
                return
        if upsert:
            nuevo = dict(filtro)
            nuevo.update(upd.get("$setOnInsert", {}))
            nuevo.update(upd.get("$set", {}))
            for k, v in upd.get("$inc", {}).items():
                nuevo[k] = nuevo.get(k, 0) + v
            self.docs.append(nuevo)


class _BaseDatos:
    def __init__(self):
        self._c = {}

    def __getitem__(self, nombre):
        return self

    def __getattr__(self, nombre):
        return self._c.setdefault(nombre, _Coleccion())


@pytest.fixture()
def ai_usage(monkeypatch):
    """Carga services/ai_usage.py con Mongo simulado y el mes bajo control."""
    motor_ma = types.ModuleType("motor.motor_asyncio")
    motor_ma.AsyncIOMotorClient = lambda *a, **k: _BaseDatos()
    motor = types.ModuleType("motor")
    motor.motor_asyncio = motor_ma
    monkeypatch.setitem(sys.modules, "motor", motor)
    monkeypatch.setitem(sys.modules, "motor.motor_asyncio", motor_ma)
    servicios = types.ModuleType("services")
    servicios.__path__ = [os.path.join(BACKEND, "services")]
    monkeypatch.setitem(sys.modules, "services", servicios)

    spec = importlib.util.spec_from_file_location(
        "services.ai_usage", os.path.join(BACKEND, "services", "ai_usage.py"))
    modulo = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "services.ai_usage", modulo)
    spec.loader.exec_module(modulo)

    modulo.db = _BaseDatos()
    modulo.db.ai_usage_config.docs.append(
        {"_id": "cfg", "default_credits": 0, "credits_per": {"render": 1}})
    modulo._mes_actual = ["2026-08"]
    modulo._month = lambda: modulo._mes_actual[0]
    return modulo


USUARIO = {"id": "u42", "aiCreditsMonthly": 10}  # plan Taller: 10 renders/mes


def _estado(mod):
    c = asyncio.get_event_loop().run_until_complete(mod.get_user_credits(USUARIO))
    return c["asignados"], c["saldo"], c["restantes"]


def test_los_packs_comprados_sobreviven_al_cambio_de_mes(ai_usage):
    async def escenario():
        await ai_usage.añadir_saldo("u42", 20)
        # Se gastan 14: los 10 del plan y 4 del saldo comprado.
        for _ in range(14):
            await ai_usage.consume_credits(USUARIO, "render")
        antes = await ai_usage.get_user_credits(USUARIO)
        assert antes["saldo"] == 16

        ai_usage._mes_actual[0] = "2026-09"  # cambia el mes
        despues = await ai_usage.get_user_credits(USUARIO)
        assert despues["saldo"] == 16, "se han perdido renders PAGADOS al cambiar de mes"
        assert despues["asignados"] == 10, "el cupo del plan sí debe renovarse"
        assert despues["restantes"] == 26
    asyncio.run(escenario())


def test_se_gasta_primero_el_plan_y_no_el_saldo_pagado(ai_usage):
    async def escenario():
        await ai_usage.añadir_saldo("u42", 20)
        for _ in range(6):  # caben de sobra en el plan (10)
            await ai_usage.consume_credits(USUARIO, "render")
        c = await ai_usage.get_user_credits(USUARIO)
        assert c["saldo"] == 20, "ha tocado el saldo comprado teniendo cupo del plan libre"
        assert c["restantes"] == 24
    asyncio.run(escenario())


def test_el_saldo_nunca_queda_negativo_y_la_recarga_llega_entera(ai_usage):
    async def escenario():
        await ai_usage.añadir_saldo("u42", 2)
        for _ in range(20):  # muchos más de los que hay
            await ai_usage.consume_credits(USUARIO, "render")
        guardado = await ai_usage.db.ai_credit_balance.find_one({"user_id": "u42"})
        assert (guardado or {}).get("saldo", 0) >= 0, "saldo negativo en la base de datos"
        # Un saldo en negativo se comería parte de la siguiente recarga pagada.
        await ai_usage.añadir_saldo("u42", 20)
        c = await ai_usage.get_user_credits(USUARIO)
        assert c["saldo"] == 20, "la recarga ha llegado mermada"
    asyncio.run(escenario())


def test_el_master_tiene_cupo_para_poder_medirlo(ai_usage):
    """La cuenta de la casa gasta como una mas: con acceso ilimitado no hay
    forma de saber cuanto da de si una bolsa de renders ni de comprobar que el
    aviso de "sin renders" funciona."""
    c = asyncio.run(ai_usage.get_user_credits({"id": "adm", "isAdmin": True}))
    assert c["ilimitado"] is False
    assert c["asignados"] == ai_usage.CUPO_MASTER_POR_DEFECTO == 40


def test_el_master_vuelve_a_ser_ilimitado_poniendo_el_cupo_a_cero(ai_usage):
    """Se cambia desde la configuracion, sin tocar codigo ni desplegar."""
    ai_usage.db.ai_usage_config.docs[0]["master_credits"] = 0
    c = asyncio.run(ai_usage.get_user_credits({"id": "adm", "isAdmin": True}))
    assert c["ilimitado"] is True


def test_direccion_sigue_sin_limite(ai_usage):
    """El cupo es para la cuenta de la casa, no para gerencia."""
    c = asyncio.run(ai_usage.get_user_credits({"id": "ger", "isGerente": True}))
    assert c["ilimitado"] is True


def test_el_master_gasta_de_verdad_sus_renders(ai_usage):
    async def esc():
        usuario = {"id": "adm", "isAdmin": True}
        for _ in range(3):
            await ai_usage.consume_credits(usuario, "render")
        c = await ai_usage.get_user_credits(usuario)
        assert c["consumidos_mes"] == 3, "al master no se le estaba descontando nada"
        assert c["restantes"] == 37
    asyncio.run(esc())


def test_se_respetan_los_packs_del_formato_antiguo(ai_usage):
    """Los packs concedidos antes del cambio viven en `extra` del mes."""
    ai_usage.db.ai_credits.docs.append(
        {"user_id": "u99", "month": "2026-08", "consumed": 0, "extra": 7})
    c = asyncio.run(ai_usage.get_user_credits({"id": "u99", "aiCreditsMonthly": 10}))
    assert c["restantes"] == 17, "se han perdido packs concedidos con el formato anterior"
