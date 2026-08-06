# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: un croquis a mano se trata como CROQUIS, no como foto de cocina.

El síntoma que perseguía el master el 06/08: subía su croquis a lápiz de una
cocina en L (dos combis, escobero, despensero, isla con fregadero) y el Estudio
3D devolvía una cocina en línea recta con isla redondeada. Ni la L, ni los
combis, ni el escobero. Se daba por hecho que era cosa del modelo de imagen.

No lo era. `_is_sketch_reference` SOLO miraba si el fichero era un PDF. El
master fotografía el croquis con el móvil, así que llegaba un JPEG, el detector
decía «no es un croquis» y el render se iba por la rama de EDITAR UNA FOTO DE
UNA COCINA EXISTENTE: al modelo se le ordenaba «esta es una cocina real, aplica
solo el cambio pedido y NO reorganices nada». Es decir, se le pedía
fotorrealizar un dibujo a lápiz como si ya fuera una cocina montada. El modelo
hacía lo único que podía hacer con esa orden: inventarse una cocina genérica.

Por eso este candado. Un croquis mal clasificado NO da ningún error: devuelve
una imagen bonita de una cocina que no es la del cliente, y eso solo se ve
cuando el master mira el render. Igual que con el modelo de imagen, lo que no
rompe nada es lo que más tarda en descubrirse.

Las dos direcciones importan, y por eso se prueban las dos:
· Un croquis que pasa por foto  -> el render se inventa la cocina (lo de arriba).
· Una foto que pasa por croquis -> se pierde la referencia real del cliente.
El detector es CONSERVADOR a propósito: ante la duda, foto.
"""
import asyncio
import base64
import importlib.util
import io
import os
import sys
import types

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PIL = pytest.importorskip("PIL", reason="Pillow es necesario para leer el croquis")
from PIL import Image, ImageDraw  # noqa: E402


@pytest.fixture()
def servicio(monkeypatch):
    """Carga el servicio de render con la configuración simulada."""
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
    core.get_engine = lambda: types.SimpleNamespace(_sanitize_response=lambda t: t)
    monkeypatch.setitem(sys.modules, "services.luiggi_ai.engine_core", core)

    spec = importlib.util.spec_from_file_location(
        "services.luiggi_ai.render_3d",
        os.path.join(BACKEND, "services", "luiggi_ai", "render_3d.py"))
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "services.luiggi_ai.render_3d", mod)
    spec.loader.exec_module(mod)
    return mod.Render3DService()


def _a_data_url(img, formato="JPEG"):
    buf = io.BytesIO()
    img.save(buf, format=formato, quality=88) if formato == "JPEG" else img.save(buf, format=formato)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/{formato.lower()};base64,{b64}"


def croquis_a_lapiz():
    """El croquis del master: cocina en L a lápiz sobre papel, fotografiada."""
    img = Image.new("RGB", (800, 600), (252, 251, 247))
    d = ImageDraw.Draw(img)
    # Paredes en L, módulos y la isla, con el trazo repasado como a mano.
    trazos = [(60, 80, 740, 80), (60, 80, 60, 520), (60, 520, 740, 520),
              (740, 80, 740, 520), (60, 300, 420, 300), (420, 80, 420, 520),
              (200, 300, 200, 520), (520, 200, 740, 200)]
    for x1, y1, x2, y2 in trazos:
        for grosor in range(3):
            d.line((x1, y1 + grosor, x2, y2 + grosor), fill=(70, 68, 75), width=2)
    for i in range(14):  # cotas escritas a mano debajo
        d.line((90 + i * 45, 545, 120 + i * 45, 545), fill=(90, 88, 95), width=2)
    # Luz cálida y sombra del móvil al fotografiar el papel.
    return Image.blend(img, Image.new("RGB", (800, 600), (250, 246, 232)), 0.12)


def foto_de_cocina_blanca():
    """El caso ADVERSARIO: foto real de una cocina blanca, lo más parecido a un
    croquis que existe. Si esta se cuela como croquis, el detector no vale."""
    import random
    img = Image.new("RGB", (800, 600))
    d = ImageDraw.Draw(img)
    for y in range(600):  # pared blanca con degradado de luz
        v = 238 - int(y * 0.06)
        d.line((0, y, 800, y), fill=(v, v - 2, v - 6))
    d.rectangle((0, 430, 800, 600), fill=(176, 138, 96))     # suelo de madera
    d.rectangle((40, 250, 760, 430), fill=(246, 246, 244))   # muebles bajos
    d.rectangle((40, 235, 760, 252), fill=(210, 205, 198))   # encimera
    for x in range(60, 760, 90):
        d.rectangle((x, 262, x + 78, 420), fill=(238, 239, 241), outline=(206, 206, 208))
    d.rectangle((520, 60, 760, 200), fill=(232, 233, 236))   # muebles altos
    random.seed(2)
    for _ in range(9000):  # grano de fotografía
        x, y = random.randrange(800), random.randrange(600)
        p = img.getpixel((x, y))
        j = random.randint(-14, 14)
        img.putpixel((x, y), tuple(max(0, min(255, c + j)) for c in p))
    return img


# ── El detector ──────────────────────────────────────────────────────────────

def test_un_croquis_fotografiado_se_detecta_como_croquis(servicio):
    """CANDADO DURO. Esto es exactamente lo que fallaba: el croquis llegaba en
    JPEG (foto del móvil) y el detector solo sabía reconocer PDF."""
    assert servicio._is_sketch_reference(_a_data_url(croquis_a_lapiz()), "image/jpeg"), (
        "un croquis a lápiz fotografiado ha dejado de reconocerse como croquis. "
        "Se irá por la rama de «editar una foto de cocina existente» y el "
        "render devolverá una cocina genérica inventada, sin dar ningún error.")


def test_una_foto_de_cocina_blanca_no_se_confunde_con_un_croquis(servicio):
    """La otra dirección: si una foto real pasa por croquis, se tira la
    referencia del cliente. Ante la duda, foto."""
    assert not servicio._is_sketch_reference(
        _a_data_url(foto_de_cocina_blanca()), "image/jpeg"), (
        "una FOTO de una cocina blanca real se está tomando por un croquis. El "
        "detector se ha vuelto demasiado permisivo y se pierde la referencia.")


def test_el_pdf_escaneado_sigue_siendo_croquis(servicio):
    """Lo que ya funcionaba antes del 06/08 tiene que seguir funcionando."""
    pdf = "data:application/pdf;base64," + base64.b64encode(b"%PDF-1.4 croquis").decode()
    assert servicio._is_sketch_reference(pdf, "application/pdf")
    assert servicio._is_sketch_reference(pdf, None), "ya no se miran los magic bytes %PDF"


def test_el_detector_no_revienta_con_basura(servicio):
    """Una referencia corrupta no puede tumbar el render: se trata como foto."""
    assert servicio._is_sketch_reference("data:image/png;base64,@@@no-es-base64@@@", "image/png") is False
    assert servicio._is_sketch_reference(None, None) is False


# ── La consecuencia: por qué rama se va el render ────────────────────────────

def _capturar_prompt(servicio):
    caja = {}

    async def falso(task_prompt, prompt, parsed_params=None, **kw):
        caja["task_prompt"] = task_prompt
        caja.update(kw)
        return {"success": True, "result": {"images": ["data:image/png;base64,x"]}}

    servicio._render_dispatch = falso
    servicio._expand_brief = lambda *a, **k: _corutina("")
    return caja


async def _corutina(valor):
    return valor


def test_el_croquis_no_se_trata_como_una_cocina_ya_montada(servicio):
    """EL FALLO, de punta a punta.

    Con el croquis del master, al modelo NO se le puede decir «esta es una
    cocina existente, edítala sin reorganizar nada»: no hay ninguna cocina que
    editar todavía, solo un dibujo. Esa orden es la que producía la cocina
    genérica."""
    caja = _capturar_prompt(servicio)
    asyncio.run(servicio.generate_render(
        description="cocina en L, roble y blanco",
        reference_image=_a_data_url(croquis_a_lapiz()),
        reference_mime="image/jpeg",
        provider="gemini"))
    prompt = caja.get("task_prompt", "")
    assert "EDIT that exact image" not in prompt, (
        "el croquis se está tratando como la foto de una cocina ya montada. "
        "Es el fallo del 06/08: el modelo se inventa una cocina genérica.")
    assert "TECHNICAL 2D DRAWING" in prompt, (
        "el croquis ya no entra en modo estructura estricta; se pierde la "
        "distribución dibujada (la L, los combis, el escobero).")


def test_el_croquis_viaja_de_verdad_hasta_el_modelo(servicio):
    """Detectarlo no basta: la imagen tiene que llegar. Si se queda por el
    camino, el modelo diseña a ciegas desde el texto."""
    caja = _capturar_prompt(servicio)
    asyncio.run(servicio.generate_render(
        description="cocina en L",
        reference_image=_a_data_url(croquis_a_lapiz()),
        reference_mime="image/jpeg",
        provider="gemini"))
    assert caja.get("reference_image_base64"), (
        "el croquis se detecta pero NO se le pasa al modelo: renderiza solo "
        "con el texto y no puede seguir el dibujo.")


def test_una_foto_de_cocina_si_se_edita(servicio):
    """Contrapartida: con una foto real de cocina, el modo edición es el bueno
    y no se puede perder al arreglar lo del croquis."""
    caja = _capturar_prompt(servicio)
    asyncio.run(servicio.generate_render(
        description="cambia las puertas a verde",
        reference_image=_a_data_url(foto_de_cocina_blanca()),
        reference_mime="image/jpeg",
        provider="gemini"))
    assert "EDIT that exact image" in caja.get("task_prompt", ""), (
        "una foto real de cocina ha dejado de ir por el modo edición: ahora se "
        "rediseña entera en vez de aplicar solo el cambio pedido.")
