# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: una FOTO no lleva cotas. Nunca.

24/08/2026, el master: «si paso un diseño con medidas escritas, cuando lo pasa
a render las escribe».

Y era verdad. Lo único que impedía copiar las anotaciones del dibujo era la
regla de «no reproduzcas el papel ni los trazos de lápiz ni la letra
manuscrita»… que SOLO se añadía si `_parece_dibujo_a_mano` decía que sí. Un
plano impreso de CAD —o el pantallazo de un presupuesto— no lo es. Así que con
un dibujo impreso lleno de cotas nadie le decía al modelo que no las copiara.

Y aunque se hubiera añadido, esa regla habla del SOPORTE (papel, lápiz), no de
las ANOTACIONES TÉCNICAS, que salen igual de nítidas en un dibujo impreso.

POR QUÉ IMPORTA MÁS DE LO QUE PARECE
------------------------------------
Es la regla nº1 de CLAUDE.md: un modelo de imagen NUNCA escribe cotas, porque
no sabe. Las que salieran serían números inventados impresos sobre una foto
que alguien puede acabar enseñando a un cliente o mandando a fabricar. Las
cotas de verdad las dibuja el alzado vectorial, con datos reales.

El camino de ARMARIOS ya lo hacía bien desde el principio —«READ the notation.
NEVER RENDER IT»—. El de cocina no. Esto los iguala.
"""
import asyncio
import importlib.util
import os
import sys
import types

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RENDER = os.path.join(RAIZ, "backend", "services", "luiggi_ai", "render_3d.py")
ARMARIO = os.path.join(RAIZ, "backend", "services", "luiggi_ai", "render_armario.py")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def _encargo_del_croquis():
    """El trozo del prompt que se manda cuando hay dibujos de referencia."""
    fuente = _leer(RENDER)
    ini = fuente.index("async def generate_render_composed")
    fin = fuente.index("def _is_sketch_reference", ini)
    return fuente[ini:fin]


def test_al_render_de_cocina_se_le_prohibe_dibujar_cotas():
    cuerpo = _encargo_del_croquis()
    assert "NEVER draw dimension lines" in cuerpo, (
        "se ha perdido la prohibición de dibujar cotas en el render de cocina. "
        "Con un plano impreso acotado, el modelo copia las medidas encima de la "
        "foto — y son números que él no sabe, sobre una imagen que puede acabar "
        "en manos de un cliente")


@pytest.fixture()
def servicio(monkeypatch):
    """Carga el servicio de render con la configuración simulada."""
    paquete = types.ModuleType("services"); paquete.__path__ = [os.path.join(RAIZ, "backend", "services")]
    monkeypatch.setitem(sys.modules, "services", paquete)
    lai = types.ModuleType("services.luiggi_ai")
    lai.__path__ = [os.path.join(RAIZ, "backend", "services", "luiggi_ai")]
    monkeypatch.setitem(sys.modules, "services.luiggi_ai", lai)
    cfg = types.ModuleType("services.luiggi_ai.config")
    cfg.get_ai_config = lambda: types.SimpleNamespace(
        brand_name="Motor 3D", provider_api_key="", render_enabled=True,
        render_default_style="photorealistic")
    monkeypatch.setitem(sys.modules, "services.luiggi_ai.config", cfg)
    core = types.ModuleType("services.luiggi_ai.engine_core")
    core.get_engine = lambda: types.SimpleNamespace(_sanitize_response=lambda t: t)
    monkeypatch.setitem(sys.modules, "services.luiggi_ai.engine_core", core)
    spec = importlib.util.spec_from_file_location("services.luiggi_ai.render_3d", RENDER)
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "services.luiggi_ai.render_3d", mod)
    spec.loader.exec_module(mod)
    return mod.Render3DService()


def test_la_prohibicion_NO_depende_de_que_el_dibujo_sea_a_mano(servicio):
    """ESTA es la que encierra el fallo, y se comprueba EJECUTANDO.

    La regla vieja iba dentro de `if hay_croquis`, o sea que solo se añadía
    cuando `_parece_dibujo_a_mano` decía que sí. Un plano IMPRESO de CAD no lo
    es — y es justo lo que subió el master.

    Aquí se fuerza el caso malo: un dibujo que NO parece hecho a mano. El
    encargo tiene que llevar la prohibición igual."""
    caja = {}

    async def falso(task_prompt, prompt, parsed_params=None, **kw):
        caja["encargo"] = task_prompt
        return {"success": True, "result": {"images": ["data:image/png;base64,x"]}}

    servicio._render_dispatch = falso
    servicio._prepare_reference = lambda img, mime: ("iVBORw0KGgo=", "image/png")
    # EL CASO DEL MASTER: un plano impreso, no un boceto a lápiz.
    servicio._parece_dibujo_a_mano = lambda *a, **k: False

    asyncio.run(servicio.generate_render_composed(
        description="cocina lineal", floor_plan="data:image/png;base64,iVBORw0KGgo="))

    encargo = caja.get("encargo") or ""
    assert encargo, "el encargo no llegó al repartidor"
    assert "NEVER draw dimension lines" in encargo, (
        "con un dibujo que NO es a mano —un plano impreso acotado, el caso del "
        "master— el encargo vuelve a salir SIN la prohibición de dibujar cotas. "
        "Es exactamente el fallo del 24/08: las medidas escritas del plano "
        "acababan pintadas encima de la foto")


def test_se_le_dice_que_las_cotas_del_dibujo_son_PARA_EL():
    """No basta con «no escribas»: hay que decir qué hacer con lo que lee."""
    cuerpo = _encargo_del_croquis()
    assert "INSTRUCTIONS FOR YOU" in cuerpo, (
        "ya no se le explica que las cotas del dibujo son información para él y "
        "no algo que copiar. Sin eso puede entender que las medidas sobran, y "
        "entonces deja de respetarlas")


def test_el_camino_de_armarios_sigue_teniendo_la_suya():
    """El que ya lo hacía bien no se pierde por el camino."""
    fuente = _leer(ARMARIO)
    assert "NEVER RENDER IT" in fuente, (
        "el render de armarios ha perdido su «READ the notation. NEVER RENDER "
        "IT», que es lo que lleva impidiendo desde el principio que las cotas "
        "del croquis acaben pintadas en la foto")
