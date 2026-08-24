# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: ningún camino puede leer un croquis SIN RECORTARLO antes.

24/08/2026. El master sube el pantallazo de una página de presupuesto —barra
de estado, título, el dibujo, tres líneas de precio, el total y la barra de
Android— y pide que se lo describan. La descripción que salió decía:

    «sistema METOD de IKEA … frentes de la marca CUBRO»

Eso NO estaba en el dibujo. Estaba en las líneas de precio de la página
(«Elementos IKEA», «Elementos CUBRO»). El modelo no lo dedujo de la cocina: lo
LEYÓ del presupuesto. Y «METOD» ni siquiera aparecía escrito, o sea que además
bordó encima de lo leído.

En la misma descripción se inventó una «longitud total estimada de 300 cm»
repartida en cinco módulos de 60 —el dibujo no lleva NI UNA COTA— y un
«frigorífico combi» que no está dibujado por ningún lado.

POR QUÉ PASÓ
------------
El recorte existía desde el 18/08 y funcionaba: probado contra ese mismo
pantallazo, deja 1080x2400 en 1055x844 con el dibujo limpio. Pero vivía SOLO en
`render_3d.py`, el camino de RENDERIZAR. El de DESCRIBIR
(`routes/ai_engine.py`) recibía la página entera.

O sea: no era que el recorte fallara. Era que había DOS caminos que leen
croquis y el recorte estaba en uno.

QUÉ SE PROTEGE
--------------
Que los dos sigan recortando. Si mañana aparece un tercer camino que lea
dibujos, esto no lo va a saber — pero al menos los dos que hay no se separan
otra vez sin que nadie se entere, que es exactamente lo que pasó aquí.

Las reglas del prompt NO bastan, y esta es la lección: `describe-project` ya
decía «NO te inventes NINGUNA medida» con todas las letras, y aun así salieron
los 300 cm. Se le pueden dar todas las órdenes del mundo; si en la imagen se
ven las líneas de precio, se leen.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUTAS = os.path.join(RAIZ, "backend", "routes", "ai_engine.py")
RENDER = os.path.join(RAIZ, "backend", "services", "luiggi_ai", "render_3d.py")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def test_el_camino_de_describir_recorta_la_imagen():
    """`describe-reference` no puede mandar la página entera a analizar."""
    fuente = _leer(RUTAS)
    ini = fuente.index('@ai_engine_router.post("/describe-reference")')
    fin = fuente.index('@ai_engine_router.post("/describe-project")', ini)
    cuerpo = fuente[ini:fin]
    assert "_recortar_si_es_una_pagina" in cuerpo, (
        "describe-reference vuelve a analizar la imagen entera. Si lo que sube "
        "el master es el pantallazo de una página de presupuesto, la lectura se "
        "queda con las líneas de precio y sale diciendo marcas que no están en "
        "el dibujo")


def test_el_plano_y_los_alzados_tambien_se_recortan():
    """En el proyecto entero, plano y alzados son dibujos: van recortados."""
    fuente = _leer(RUTAS)
    ini = fuente.index('@ai_engine_router.post("/describe-project")')
    cuerpo = fuente[ini:ini + 4000]
    assert cuerpo.count("_recortar_si_es_una_pagina") >= 2, (
        "en describe-project ya no se recortan el plano Y los alzados: alguno "
        "de los dos vuelve a viajar dentro de su página")


def test_el_camino_de_renderizar_sigue_recortando():
    """El que ya funcionaba desde el 18/08 no se pierde por el camino."""
    fuente = _leer(RENDER)
    assert fuente.count("recortar_dibujo_base64") >= 2, (
        "el render ha dejado de recortar el croquis: el dibujo vuelve a ocupar "
        "un tercio de la imagen y el detalle fino deja de verse")


def test_el_recorte_se_llama_ANTES_de_analizar():
    """Recortar después de mandar la imagen no serviría de nada."""
    fuente = _leer(RUTAS)
    ini = fuente.index('@ai_engine_router.post("/describe-reference")')
    fin = fuente.index('@ai_engine_router.post("/describe-project")', ini)
    cuerpo = fuente[ini:fin]
    pos_recorte = cuerpo.index("_recortar_si_es_una_pagina")
    pos_analisis = cuerpo.index("analyze_image_with_gemini")
    # El import está arriba; se busca la LLAMADA, que va después.
    pos_llamada = cuerpo.index("await analyze_image_with_gemini")
    assert pos_recorte < pos_llamada, (
        "se recorta DESPUÉS de mandar la imagen a analizar, o sea que no sirve "
        "de nada")
    assert pos_analisis >= 0


def test_una_foto_no_se_recorta():
    """CANDADO de seguridad: el recorte no puede estropear una referencia.

    Una referencia de acabado es una FOTO de una cocina real, no un dibujo
    dentro de una página. `recortar_dibujo_base64` solo actúa cuando reconoce
    un dibujo enmarcado en una página; si algún día empezara a recortar fotos,
    estaría tirando el contexto que da el acabado.

    Se comprueba sobre el propio código: la función tiene que seguir
    devolviendo un booleano que diga si recortó, porque de eso depende que
    quien la llama pueda dejar la imagen en paz."""
    fuente = _leer(os.path.join(RAIZ, "backend", "services", "recorte_croquis.py"))
    assert re.search(r"def recortar_dibujo_base64\([^)]*\)\s*->\s*Tuple\[str,\s*bool\]", fuente), (
        "`recortar_dibujo_base64` ya no dice si ha recortado o no. Sin ese "
        "booleano, quien la llama no puede distinguir un croquis dentro de una "
        "página de una foto que hay que dejar intacta")
