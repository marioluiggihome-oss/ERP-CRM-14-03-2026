# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
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
    caja = {"expand_brief_llamado": False}

    async def falso(task_prompt, prompt, parsed_params=None, **kw):
        caja["task_prompt"] = task_prompt
        caja["parsed_params"] = parsed_params
        caja.update(kw)
        return {"success": True, "result": {"images": ["data:image/png;base64,x"]}}

    async def falso_expand(description, space_type):
        caja["expand_brief_llamado"] = True
        return description

    servicio._render_dispatch = falso
    servicio._expand_brief = falso_expand
    return caja


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
    assert "reference image of an EXISTING kitchen" not in prompt, (
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


def test_el_croquis_no_pasa_por_el_brief_expandido(servicio):
    """CANDADO DURO — la segunda mitad del fallo del 06/08.

    `_expand_brief` le pide a un LLM que redacte la distribución y los módulos
    de izquierda a derecha A PARTIR DEL TEXTO y SIN VER el dibujo. Con un
    croquis delante eso es una cocina INVENTADA, y encima ocupa casi todo el
    prompt: el modelo de imagen obedece al texto largo en vez de al croquis.

    Ya estaba escrito en el render compuesto —«un texto largo de dirección de
    arte compite con las imágenes y el modelo acaba inventando una cocina
    genérica»— pero en esta rama no se había aplicado."""
    caja = _capturar_prompt(servicio)
    asyncio.run(servicio.generate_render(
        description="cocina en L, roble y blanco",
        reference_image=_a_data_url(croquis_a_lapiz()),
        reference_mime="image/jpeg",
        provider="gemini"))
    assert caja["expand_brief_llamado"] is False, (
        "el croquis vuelve a pasar por _expand_brief: se le manda al modelo una "
        "distribución inventada por un LLM que NO ha visto el dibujo.")
    assert caja["parsed_params"].get("fromSketch") is True, (
        "el render ya no se marca como hecho a partir de croquis")


def test_con_croquis_manda_el_dibujo_y_el_texto_solo_pone_acabados(servicio):
    """El reparto de mando: geometría del dibujo, acabados del texto."""
    caja = _capturar_prompt(servicio)
    asyncio.run(servicio.generate_render(
        description="roble y blanco mate",
        reference_image=_a_data_url(croquis_a_lapiz()),
        reference_mime="image/jpeg",
        provider="gemini"))
    prompt = caja.get("task_prompt", "")
    assert "Design brief (follow it precisely)" not in prompt, (
        "el croquis ha vuelto al prompt largo de dirección de arte "
        "(build_render_prompt), que es el que tapa el dibujo.")
    assert "roble y blanco mate" in prompt, "se ha perdido el acabado pedido"
    assert "geometry comes 100% from the drawing" in prompt, (
        "ya no se le dice al modelo que la geometría sale del dibujo")


def test_el_render_compuesto_avisa_de_que_el_plano_va_a_mano(servicio):
    """El botón principal, con plano subido, va por el render COMPUESTO. Ahí el
    prompt daba por hecho que las referencias eran fotos o renders. Si el plano
    va a lápiz hay que decirlo, o el modelo toma el trazo por el acabado —o
    «mejora» una distribución que le parece tosca por estar dibujada a mano."""
    caja = _capturar_prompt(servicio)
    asyncio.run(servicio.generate_render_composed(
        description="roble y blanco",
        floor_plan=_a_data_url(croquis_a_lapiz()),
        provider="gemini"))
    prompt = caja.get("task_prompt", "")
    assert "HAND-DRAWN" in prompt, (
        "al modelo ya no se le dice que el plano va a mano: puede dibujar el "
        "papel y el lápiz, o rehacer la distribución por parecerle tosca.")
    assert "do NOT 'tidy up', simplify or upgrade the layout" in prompt


def test_el_render_compuesto_no_avisa_de_croquis_si_es_una_foto(servicio):
    """Con una foto real no se le puede decir que es un dibujo a mano."""
    caja = _capturar_prompt(servicio)
    asyncio.run(servicio.generate_render_composed(
        description="cambia el color",
        floor_plan=_a_data_url(foto_de_cocina_blanca()),
        provider="gemini"))
    assert "HAND-DRAWN" not in caja.get("task_prompt", "")


def test_una_foto_de_cocina_si_se_edita(servicio):
    """Contrapartida: con una foto real de cocina, el modo edición es el bueno
    y no se puede perder al arreglar lo del croquis."""
    caja = _capturar_prompt(servicio)
    asyncio.run(servicio.generate_render(
        description="cambia las puertas a verde",
        reference_image=_a_data_url(foto_de_cocina_blanca()),
        reference_mime="image/jpeg",
        provider="gemini"))
    assert "reference image of an EXISTING kitchen" in caja.get("task_prompt", ""), (
        "una foto real de cocina ha dejado de ir por el modo edición: ahora se "
        "rediseña entera en vez de aplicar solo el cambio pedido.")


# ── EDITAR UN RENDER NUESTRO NO ES INTERPRETAR UN CROQUIS ────────────────────
# 14/08/2026. El master tiene el render bien —la cocina en L, sus columnas, sus
# puertas— escribe abajo «cierra las puertas de mueble placa», y vuelve OTRA
# cocina: las puertas convertidas en gavetas, los altos movidos, la composicion
# rehecha. No dio ningun error. Devolvio una cocina preciosa que no era la suya.
#
# El motivo: al editar se le pasaba el render al DETECTOR DE CROQUIS. Y su
# cocina es blanca —paredes blancas, muebles blancos, encimera blanca—, o sea
# poco color y mucho claro: exactamente la firma del papel. La tomaba por un
# dibujo a mano y se iba por la rama de «construye lo que esta dibujado», que
# reconstruye la cocina entera.
#
# El arreglo no es afinar el umbral: es no adivinar. Cuando el ERP edita SU
# PROPIO render, lo sabe. Una procedencia conocida gana siempre a una heuristica.


def _render_blanco():
    """Un render nuestro de cocina blanca: poco color y mucho claro, que es lo
    que el detector de croquis confunde con papel."""
    img = Image.new("RGB", (800, 600), (250, 250, 249))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 430, 800, 600), fill=(238, 236, 232))   # suelo claro
    d.rectangle((40, 250, 760, 430), fill=(252, 252, 251))  # muebles bajos
    d.rectangle((40, 235, 760, 252), fill=(246, 246, 245))  # encimera
    d.rectangle((520, 60, 760, 200), fill=(251, 251, 250))  # muebles altos
    return img


def test_editar_el_render_propio_no_pasa_por_el_detector_de_croquis(servicio):
    """CANDADO. `editing_render` dice la PROCEDENCIA: es nuestro, no se adivina."""
    caja = _capturar_prompt(servicio)
    asyncio.run(servicio.generate_render(
        description="cierra las puertas de mueble placa",
        reference_image=_a_data_url(_render_blanco()),
        reference_mime="image/jpeg",
        editing_render=True,
        provider="gemini"))
    prompt = caja.get("task_prompt", "")
    assert "reference image of an EXISTING kitchen" in prompt, (
        "editando un render NUESTRO se ha vuelto a la rama del croquis: en vez "
        "de aplicar el cambio se rehace la cocina entera y vuelve otra")
    assert "TECHNICAL 2D DRAWING" not in prompt, \
        "el render propio se sigue tratando como un dibujo a mano"


def test_cerrar_las_puertas_no_autoriza_a_cambiar_los_frentes(servicio):
    """Lo que le paso al master: pidio CERRAR unas puertas y le devolvieron
    gavetas. Cambiar el estado de algo no autoriza a cambiar el mueble."""
    caja = _capturar_prompt(servicio)
    asyncio.run(servicio.generate_render(
        description="cierra las puertas de mueble placa",
        reference_image=_a_data_url(_render_blanco()),
        reference_mime="image/jpeg",
        editing_render=True,
        provider="gemini"))
    prompt = caja.get("task_prompt", "")
    assert "NEVER swap doors for drawers" in prompt, (
        "el prompt de edicion ya no prohibe cambiar puertas por gavetas: "
        "«cierra las puertas» volvera a devolver cajones")
    # La frase del master, escrita en la REGLA. Se busca la regla ENTERA porque
    # «cierra las puertas» tambien llega por lo que teclea el usuario, y
    # entonces la comprobacion pasaria sin que la regla existiera.
    assert "'cierra las puertas' means render those SAME doors" in prompt, \
        "se ha quitado el ejemplo literal del master, que es el caso probado"
    assert "never authorise changing the furniture itself" in prompt, (
        "ya no se dice que una palabra de ESTADO (abierto/cerrado) no da "
        "permiso para tocar el mueble")


# ── UN DIBUJO DA GEOMETRIA, NUNCA ESTILO ────────────────────────────────────
# 14/08/2026. El master pasa la ILUSTRACION de un armario —plana, con contorno,
# en tonos pastel— y el render sale igual de plano: «queda como si fuera de
# dibujos animados, quiero un render real de un armario real».
#
# El prompt del croquis solo prohibia dibujar «el papel, el lapiz y la letra»,
# que es lo que tiene un croquis a mano. Con una ilustracion en color, el modelo
# tomo su ESTILO por el estilo pedido: copio contornos, colores planos y luz
# uniforme. Y encima el prompt decia «kitchen» escrito a fuego, o sea que a un
# croquis de ARMARIO se le pedia una cocina y a la vez fidelidad al dibujo.


def test_del_dibujo_se_copia_la_geometria_y_no_como_esta_dibujado(servicio):
    caja = _capturar_prompt(servicio)
    asyncio.run(servicio.generate_render(
        description="armario blanco mate",
        reference_image=_a_data_url(croquis_a_lapiz()),
        reference_mime="image/jpeg", project_type="armario", provider="gemini"))
    prompt = caja.get("task_prompt", "")
    assert "IT NEVER GIVES STYLE" in prompt, (
        "el prompt ya no separa geometria de estilo: una ilustracion volvera a "
        "salir renderizada como ilustracion")
    for prohibido in ("cartoon", "flat fills", "illustration palette"):
        assert prohibido in prompt, f"ya no se prohibe copiar «{prohibido}»"
    assert "The colours of the drawing are NOT the materials" in prompt, \
        "los colores del dibujo vuelven a tomarse por el acabado del mueble"


def test_lo_dibujado_dentro_se_fotografia_como_objeto_real(servicio):
    """En el armario del master lo de dentro salio dibujado: camisas de linea,
    cajas planas. Si el continente es foto y el contenido dibujo, no vale."""
    caja = _capturar_prompt(servicio)
    asyncio.run(servicio.generate_render(
        description="armario", reference_image=_a_data_url(croquis_a_lapiz()),
        reference_mime="image/jpeg", project_type="armario", provider="gemini"))
    prompt = caja.get("task_prompt", "")
    assert "Never a drawing of a shirt" in prompt, \
        "lo que va dentro del mueble vuelve a poder salir dibujado"


@pytest.mark.parametrize("tipo,palabra", [
    ("armario", "wardrobe"),
    ("bano", "bathroom"),
    ("cocina", "kitchen"),
    (None, "kitchen"),
])
def test_el_croquis_se_realiza_como_el_mueble_que_es(servicio, tipo, palabra):
    """«kitchen» estaba escrito a fuego: con el croquis de un armario se pedia
    una cocina Y fidelidad al dibujo. Dos ordenes que se contradicen."""
    caja = _capturar_prompt(servicio)
    asyncio.run(servicio.generate_render(
        description="mueble a medida",
        reference_image=_a_data_url(croquis_a_lapiz()),
        reference_mime="image/jpeg", project_type=tipo, provider="gemini"))
    prompt = caja.get("task_prompt", "")
    assert palabra in prompt.split("STRICT RULES")[0], (
        f"con project_type={tipo!r} el croquis no se realiza como «{palabra}»")
    if tipo == "armario":
        assert "TECHNICAL 2D DRAWING of ONE specific kitchen" not in prompt, \
            "a un croquis de armario se le sigue pidiendo una cocina"


# ── AÑADIR UN MUEBLE ES UN CAMBIO, NO UN ATAQUE AL RENDER ───────────────────
# 14/08/2026. El master: «le he dicho que a la derecha del mueble de horno un
# extraible de 15 y no me lo esta haciendo bien».
#
# El prompt de edicion decia CUATRO veces «no cambies nada» —«keeping EVERYTHING
# ELSE strictly identical», «Do NOT add», «los frentes no cambian», y remataba
# con «identical in composition to the reference»— y UNA sola vez el cambio
# pedido. Cuando lo que se pide ES un cambio de composicion, gana el «no cambies
# nada» y el mueble no aparece. Encima la pantalla lo envolvia en «manteniendo
# el mismo diseño […] No cambies nada mas», que empujaba en la misma direccion.
#
# Y hay un segundo motivo por el que un extraible de 15 se pierde: los modelos
# de imagen ensanchan los muebles estrechos «para que quede mas equilibrado», o
# se los comen por parecerles demasiado finos para dibujarlos.


def _prompt_de_edicion(servicio, orden):
    caja = _capturar_prompt(servicio)
    asyncio.run(servicio.generate_render(
        description=orden,
        reference_image=_a_data_url(foto_de_cocina_blanca()),
        reference_mime="image/jpeg", editing_render=True, provider="gemini"))
    return caja.get("task_prompt", "")


def test_el_cambio_pedido_manda_dentro_de_lo_suyo(servicio):
    """CANDADO. Sin esto, pedir un mueble nuevo no lo aniade nunca."""
    p = _prompt_de_edicion(servicio, "a la derecha del mueble de horno un extraible de 15")
    assert "THE CONTRACT HAS TWO HALVES" in p, (
        "el prompt de edicion ha vuelto a decir solo «no cambies nada»: pedir "
        "que se AÑADA un mueble no lo aniadira")
    assert "(A) WINS INSIDE ITS OWN SCOPE" in p, \
        "el cambio pedido ya no manda sobre «mantenlo todo igual»"
    assert "shift or resize the" in p, (
        "no se dice que los muebles de al lado pueden correrse para hacer "
        "sitio: un mueble nuevo no cabe sin mover nada")


def test_ya_no_se_exige_composicion_identica(servicio):
    """Era la contradiccion de raiz: se pedia el cambio y en la misma frase se
    exigia que la composicion fuera identica."""
    p = _prompt_de_edicion(servicio, "aniade un extraible de 15")
    assert "identical in composition to the reference" not in p, (
        "vuelve a exigirse composicion identica: cualquier cambio que aniada o "
        "quite un mueble se quedara sin hacer")


def test_un_mueble_estrecho_no_se_ensancha_ni_se_pierde(servicio):
    """15 cm es 15 cm. Los modelos de imagen los ensanchan «para equilibrar» o
    directamente no los dibujan."""
    p = _prompt_de_edicion(servicio, "un extraible de 15 a la derecha del horno")
    assert "NEVER widen a narrow unit" in p, \
        "se ha quitado la regla que impide ensanchar un mueble estrecho"
    assert "15 cm unit is 15 cm" in p, \
        "la medida en cm ha dejado de ser exacta"
    assert "merge it" in p, \
        "ya no se prohibe fundir el mueble estrecho con el de al lado"


def test_la_pantalla_manda_la_orden_limpia():
    """La pantalla envolvia el cambio en «manteniendo el mismo diseño […] No
    cambies nada mas», o sea que empujaba contra lo que el propio usuario acababa
    de pedir. Lo que se respeta y lo que se cambia lo dice el servidor."""
    ruta = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "frontend", "src", "components", "AIRenderStudio.jsx")
    with open(ruta, encoding="utf-8") as f:
        src = f.read()
    codigo = "\n".join(l.split("//")[0] for l in src.splitlines())
    assert "Modifica el render adjunto manteniendo el mismo" not in codigo, (
        "la pantalla vuelve a envolver la orden en «no cambies nada»: un mueble "
        "pedido no se aniadira")
