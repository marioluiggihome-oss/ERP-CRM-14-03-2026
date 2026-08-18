# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: el dibujo se recorta de la pagina, y NUNCA se recorta de mas.

EL CASO REAL
------------
El master no sube un croquis suelto. Sube el PANTALLAZO DEL MOVIL de una
pagina de presupuesto: barra de estado del telefono, «Presupuesto estimado»,
«Cocina lineal», recuadro de marca, EL DIBUJO, tres lineas con precios, el
total y la barra de navegacion de Android. El dibujo ocupa un TERCIO del alto.

Tres veces seguidas dijo lo mismo mirando el render: «no se parecen», «falla»,
«sigue sin interpretarlo bien». Y las tres veces la respuesta habia sido
apretar el prompt. No servia: si en la imagen que recibe el modelo la cocina
es pequeña, el detalle fino —los altos partidos en dos filas, el nicho de la
campana, las divisiones de cada frente— NO SE VE. No hay orden que arregle eso.

Por eso el dibujo se recorta y va a pantalla completa.

LO QUE HAY QUE VIGILAR, Y ES LO CONTRARIO
-----------------------------------------
Un recorte que se pasa es MUCHO peor que no recortar: se lleva media cocina y
NADIE SE ENTERA, porque el render sigue saliendo bonito y ademas ahora tiene
mejor pinta. Es el peor tipo de fallo que hay en esta casa — el que no avisa.

Por eso la mitad de este candado prueba que NO recorta:
 · un croquis que ya llena el papel se queda como esta,
 · una foto de cocina de verdad se queda como esta,
 · una imagen sin nada legible se queda como esta.

Ante la duda, la original. Siempre.
"""
import base64
import importlib.util
import io
import os

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIL = pytest.importorskip("PIL", reason="Pillow es necesario para recortar el dibujo")
from PIL import Image, ImageDraw  # noqa: E402


@pytest.fixture(scope="module")
def recorte():
    """Se carga por fichero para no arrastrar `services/__init__` (que exige
    JWT_SECRET). Lo que se prueba es esta funcion, no el arranque del backend."""
    spec = importlib.util.spec_from_file_location(
        "recorte_croquis", os.path.join(BACKEND, "services", "recorte_croquis.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _b64(img, fmt="JPEG"):
    buf = io.BytesIO()
    img.save(buf, format=fmt, quality=90)
    return base64.b64encode(buf.getvalue()).decode("ascii")


# El dibujo, en la pagina, va de y=430 a y=1060 sobre 1900 de alto: un tercio.
DIBUJO_ARRIBA, DIBUJO_ABAJO, PAGINA_ALTO = 430, 1060, 1900


def pagina_de_presupuesto():
    """El pantallazo del master, reproducido pieza a pieza."""
    im = Image.new("RGB", (900, PAGINA_ALTO), (247, 247, 249))
    d = ImageDraw.Draw(im)
    for x in (760, 800, 840):                       # barra de estado
        d.rectangle([x, 35, x + 22, 60], fill=(30, 30, 30))
    d.rectangle([50, 180, 520, 235], fill=(60, 60, 60))     # «Presupuesto estimado»
    d.rectangle([50, 275, 400, 350], fill=(20, 20, 20))     # «Cocina lineal»
    d.rectangle([712, 265, 852, 358], fill=(225, 225, 228))  # recuadro de marca
    # ── el dibujo ──
    d.rectangle([50, DIBUJO_ARRIBA, 860, DIBUJO_ABAJO], outline="black", width=3)
    for x in range(150, 860, 100):
        d.line([x, DIBUJO_ARRIBA, x, 700], fill="black", width=2)
    for x in range(150, 860, 130):
        d.line([x, 760, x, DIBUJO_ABAJO], fill="black", width=2)
    d.line([50, 700, 640, 700], fill="black", width=3)
    d.line([50, 760, 860, 760], fill="black", width=3)
    d.rectangle([640, DIBUJO_ARRIBA, 860, DIBUJO_ABAJO], outline="black", width=3)
    # ── precios, total y barra de Android ──
    for y in (1180, 1330, 1480):
        d.rectangle([115, y, 430, y + 30], fill=(40, 40, 40))
        d.rectangle([115, y + 45, 570, y + 70], fill=(140, 140, 145))
        d.rectangle([700, y + 5, 855, y + 35], fill=(30, 30, 30))
        d.line([50, y + 110, 855, y + 110], fill=(228, 228, 230), width=2)
    d.rectangle([45, 1650, 855, 1740], fill=(238, 238, 241))
    d.rectangle([75, 1675, 430, 1712], fill=(25, 25, 25))
    d.rectangle([690, 1675, 830, 1712], fill=(20, 20, 20))
    d.rectangle([230, 1830, 275, 1870], fill=(90, 90, 95))
    # UNA MANCHA COMPACTA Y MUY TUPIDA (un banner, una foto de cabecera, un
    # bloque de color). Ocupa MENOS sitio que el dibujo pero tiene MUCHOS más
    # píxeles de tinta, porque el dibujo son cuatro líneas finas y esto es
    # macizo. Está aquí a propósito: obliga a elegir la mancha por el SITIO que
    # ocupa y no por lo tupida que es. Sin este bloque la prueba daba por buenos
    # los dos criterios, y uno de los dos se lleva el recorte a otra parte.
    d.rectangle([60, 1180, 840, 1520], fill=(70, 70, 75))
    return im


def croquis_que_llena_el_papel():
    im = Image.new("RGB", (1200, 800), "white")
    d = ImageDraw.Draw(im)
    d.rectangle([40, 40, 1160, 760], outline=(60, 60, 60), width=4)
    for x in range(140, 1160, 100):
        d.line([x, 40, x, 760], fill=(60, 60, 60), width=3)
    return im


def foto_de_cocina():
    import random
    random.seed(7)
    im = Image.new("RGB", (1200, 800))
    px = im.load()
    for y in range(800):
        for x in range(1200):
            b = 150 + int(60 * (y / 800.0))
            px[x, y] = (b + random.randint(-25, 25), b + random.randint(-25, 25),
                        b + random.randint(-30, 20))
    return im


# ─── 1. SÍ recorta: el dibujo pasa a ocupar la imagen entera ────────────────

def test_el_dibujo_se_saca_de_la_pagina(recorte):
    """Es el caso del master: la cocina ocupa un tercio del pantallazo."""
    salida, hubo = recorte.recortar_dibujo_base64(_b64(pagina_de_presupuesto()), "image/jpeg")
    assert hubo, (
        "el pantallazo de la pagina de presupuesto ya no se recorta: el modelo "
        "vuelve a recibir la cocina a un tercio de tamano y no vera los frentes")
    im = Image.open(io.BytesIO(base64.b64decode(salida)))
    assert im.height < PAGINA_ALTO * 0.55, (
        f"el recorte se ha quedado con casi toda la pagina ({im.height}px de "
        f"{PAGINA_ALTO}): los precios y el total siguen compitiendo con el dibujo")


def test_el_recorte_no_se_come_la_cocina(recorte):
    """LO IMPORTANTE. Un recorte corto se lleva modulos y no avisa: el render
    sale bonito, con una cocina que no es. Tiene que caber el dibujo ENTERO."""
    caja = recorte.recuadro_del_dibujo(pagina_de_presupuesto())
    assert caja is not None, "no se ha localizado el dibujo dentro de la pagina"
    izq, arr, der, aba = caja
    assert arr <= DIBUJO_ARRIBA, (
        f"el recorte empieza en y={arr}, por debajo de donde empieza el dibujo "
        f"(y={DIBUJO_ARRIBA}): se corta la parte de arriba, o sea los altos")
    assert aba >= DIBUJO_ABAJO, (
        f"el recorte acaba en y={aba}, por encima de donde acaba el dibujo "
        f"(y={DIBUJO_ABAJO}): se cortan los bajos")
    assert izq <= 50 and der >= 860, (
        f"el recorte va de x={izq} a x={der} y el dibujo de 50 a 860: se queda "
        f"fuera un extremo de la fila, que es justo lo que el master reclama")


def test_el_texto_de_la_pagina_se_queda_fuera(recorte):
    """Los precios empiezan en y=1180. Si entran en el recorte, no hemos hecho
    nada: el modelo sigue repartiendo la atencion."""
    caja = recorte.recuadro_del_dibujo(pagina_de_presupuesto())
    assert caja[3] < 1180, (
        f"el recorte llega hasta y={caja[3]} y las lineas de precio empiezan en "
        f"1180: «Elementos CUBRO» y «TOTAL» siguen dentro de la referencia")


# ─── 2. NO recorta: ante la duda, la original ──────────────────────────────

def test_un_croquis_que_ya_llena_el_papel_no_se_toca(recorte):
    _, hubo = recorte.recortar_dibujo_base64(_b64(croquis_que_llena_el_papel()), "image/jpeg")
    assert not hubo, (
        "se esta recortando un croquis que ya ocupaba todo el papel: cada "
        "recorte de mas es un trozo de cocina que desaparece sin avisar")


def test_una_foto_de_cocina_no_se_toca(recorte):
    _, hubo = recorte.recortar_dibujo_base64(_b64(foto_de_cocina()), "image/jpeg")
    assert not hubo, (
        "se esta recortando una foto de cocina de verdad: la referencia del "
        "cliente se quedaria a trozos")


def test_una_imagen_ilegible_devuelve_la_original(recorte):
    """Todo blanco: no hay dibujo que encontrar. Se devuelve tal cual, sin
    reventar, porque esto va en medio de un render que el master esta mirando."""
    blanca = Image.new("RGB", (900, 1400), "white")
    entrada = _b64(blanca)
    salida, hubo = recorte.recortar_dibujo_base64(entrada, "image/jpeg")
    assert not hubo and salida == entrada, \
        "una imagen sin dibujo tiene que volver intacta"


def test_una_entrada_rota_no_tumba_el_render(recorte):
    """Un base64 que no es una imagen NO puede romper el render entero."""
    salida, hubo = recorte.recortar_dibujo_base64("esto-no-es-una-imagen", "image/jpeg")
    assert not hubo and salida == "esto-no-es-una-imagen"
    assert recorte.recortar_dibujo_base64("", "image/png") == ("", False)


# ─── 3. Está enchufado de verdad en la vía del croquis ─────────────────────

def test_el_render_recorta_antes_de_leer_el_croquis():
    """Recortar y no usarlo antes de la transcripcion no sirve de nada: quien
    lee las cotas y los frentes es Vision, y tiene que ver el dibujo grande."""
    ruta = os.path.join(BACKEND, "services", "luiggi_ai", "render_3d.py")
    with open(ruta, encoding="utf-8") as f:
        src = f.read()
    i = src.index('parsed_params["fromSketch"] = True')
    cuerpo = src[i:src.index("task_prompt = (", i)]
    assert "recortar_dibujo_base64" in cuerpo, (
        "la via del croquis ya no recorta el dibujo de la pagina")
    assert cuerpo.index("recortar_dibujo_base64") < cuerpo.index("_transcribe_sketch_with_vision"), (
        "se recorta DESPUES de leer el croquis: Vision sigue leyendo la pagina "
        "entera, que es donde se pierden los frentes")
    assert "ref_b64, ref_mime = recortado" in cuerpo, (
        "el recorte se calcula pero no se usa como referencia: al modelo de "
        "imagen le sigue llegando el pantallazo entero")
