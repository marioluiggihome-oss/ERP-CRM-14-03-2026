# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del motor de render. NO se cambia sin permiso del master.

Estas pruebas no comprueban un calculo: comprueban una PROMESA. El motor que se
elige en pantalla (IA 1/2/3/4) es una habilidad ya adquirida del Estudio 3D, y
cambiarla en silencio significa que el usuario cree seguir en su motor y no lo
esta. Paso el 03/08: al enrutar el boton principal por el render compuesto,
este llamaba directamente a Gemini estandar y se saltaba el motor elegido.

Si alguien —persona o IA— toca el reparto de motores o vuelve a saltarse el
repartidor, estas pruebas se ponen en rojo y el CI corta. Para cambiarlo hace
falta pedirselo al master y actualizar tambien este fichero, a proposito y
dejando constancia.

Mapa que se protege (frontend `providerOf()` -> backend `_render_dispatch`):
    IA 1 -> gemini          (Gemini estandar; el de siempre)
    IA 2 -> manus
    IA 3 -> gemini_premium  (prompt ultra-fotorrealista)
    IA 4 -> gemini_flash    (rapido)
"""
import asyncio
import importlib.util
import os
import sys
import types

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MOTORES = {
    "IA 1": "gemini",
    "IA 2": "manus",
    "IA 3": "gemini_premium",
    "IA 4": "gemini_flash",
}


@pytest.fixture()
def servicio(monkeypatch):
    """Carga el servicio de render con la configuracion simulada."""
    paquete = types.ModuleType("services")
    paquete.__path__ = [os.path.join(BACKEND, "services")]
    monkeypatch.setitem(sys.modules, "services", paquete)

    lai = types.ModuleType("services.luiggi_ai")
    lai.__path__ = [os.path.join(BACKEND, "services", "luiggi_ai")]
    monkeypatch.setitem(sys.modules, "services.luiggi_ai", lai)

    cfg = types.ModuleType("services.luiggi_ai.config")
    cfg.get_ai_config = lambda: types.SimpleNamespace(
        brand_name="Motor 3D", provider_api_key="", render_enabled=True,
        render_default_style="photorealistic")
    monkeypatch.setitem(sys.modules, "services.luiggi_ai.config", cfg)

    core = types.ModuleType("services.luiggi_ai.engine_core")
    core.get_engine = lambda: types.SimpleNamespace(
        _sanitize_response=lambda t: t)
    monkeypatch.setitem(sys.modules, "services.luiggi_ai.engine_core", core)

    spec = importlib.util.spec_from_file_location(
        "services.luiggi_ai.render_3d",
        os.path.join(BACKEND, "services", "luiggi_ai", "render_3d.py"))
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "services.luiggi_ai.render_3d", mod)
    spec.loader.exec_module(mod)
    return mod.Render3DService()


def _capturar_dispatch(servicio):
    """Sustituye el repartidor y devuelve una caja con lo que le llega."""
    caja = {}

    async def falso(task_prompt, prompt, parsed_params=None, **kw):
        caja.update(kw)
        caja["parsed_params"] = parsed_params
        return {"success": True, "result": {"images": ["data:image/png;base64,x"]}}

    servicio._render_dispatch = falso
    return caja


def _imagen():
    return "data:image/png;base64,iVBORw0KGgo="


@pytest.mark.parametrize("etiqueta,provider", sorted(MOTORES.items()))
def test_el_render_compuesto_respeta_el_motor_elegido(servicio, etiqueta, provider):
    """CANDADO: generar con plano NO puede cambiarte de motor por su cuenta."""
    caja = _capturar_dispatch(servicio)
    servicio._prepare_reference = lambda img, mime: ("iVBORw0KGgo=", "image/png")
    asyncio.run(servicio.generate_render_composed(
        description="cocina blanca", floor_plan=_imagen(), provider=provider))
    assert caja.get("provider") == provider, (
        f"{etiqueta} deberia renderizar con '{provider}' y se ha ido a "
        f"'{caja.get('provider')}'. Si el cambio es a proposito, pideselo al "
        f"master y actualiza este fichero.")


def test_el_render_compuesto_pasa_por_el_repartidor_de_motores(servicio):
    """Llamar directo a un motor concreto salta el reparto: prohibido."""
    fuente = open(os.path.join(
        BACKEND, "services", "luiggi_ai", "render_3d.py"), encoding="utf-8").read()
    ini = fuente.index("async def generate_render_composed")
    fin = fuente.index("def _is_sketch_reference", ini)
    cuerpo = fuente[ini:fin]
    assert "_render_dispatch" in cuerpo, "el render compuesto ya no reparte por motor"
    assert "_render_with_gemini(" not in cuerpo, (
        "el render compuesto vuelve a llamar directamente a Gemini y se salta "
        "el motor elegido en pantalla")


def test_el_tipo_de_proyecto_lo_manda_la_pantalla(servicio):
    """Con el tipo delante no se adivina del texto: cocina es cocina."""
    caja = _capturar_dispatch(servicio)
    servicio._prepare_reference = lambda img, mime: ("iVBORw0KGgo=", "image/png")
    asyncio.run(servicio.generate_render_composed(
        description="mueble a medida", floor_plan=_imagen(), project_type="bano"))
    tipo = (caja.get("parsed_params") or {}).get("space_type") or ""
    assert "bath" in tipo.lower() or "bano" in tipo.lower() or "baño" in tipo.lower(), \
        f"el tipo de proyecto se ha perdido por el camino (space_type={tipo!r})"


def test_las_referencias_de_acabado_viajan_con_el_plano(servicio):
    """Habilidad adquirida: plano y referencia se usan A LA VEZ."""
    caja = _capturar_dispatch(servicio)
    servicio._prepare_reference = lambda img, mime: ("iVBORw0KGgo=", "image/png")
    asyncio.run(servicio.generate_render_composed(
        description="", floor_plan=_imagen(), wall_sketches=[_imagen()],
        reference_images=[_imagen()]))
    assert len(caja.get("reference_images") or []) == 3, \
        "se ha perdido alguna imagen entre el plano, el alzado y la referencia"


def test_el_tope_de_imagenes_juntas_no_baja_de_siete(servicio):
    """El master lo subio a 7 a proposito: no se recorta sin pedirselo."""
    assert servicio.MAX_IMAGENES_COMPUESTAS >= 7
