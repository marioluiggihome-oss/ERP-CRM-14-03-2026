# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
UN BOTÓN ENCENDIDO QUE NO HACE NADA, Y OTRO QUE DESAPARECE.

El master, 14/09/2026, desde la tablet, dos cosas del Estudio 3D:

1. «ESTE BOTÓN NO FUNCIONA BIEN» — el visor interactivo (zoom + pan).
   Y no funcionaba por lo más tonto: en TODO `AIRenderStudio.jsx` no había un
   solo manejador táctil. El zoom iba por `onWheel` y el arrastre por
   `onMouseDown`, así que en una tablet —que es donde trabaja el master— se
   pulsaba, el icono se ponía azul y no pasaba nada más. Sin error y sin aviso:
   un botón encendido que no hace nada es peor que uno que falla, porque
   parece que el que lo usa lo está haciendo mal.
   Además el zoom no tenía NINGÚN mando a la vista: aunque hubiera ratón, que
   se hace con la rueda no lo adivina nadie.

2. «¿DÓNDE ESTÁ EL BOTÓN DE COMPARAR?» — estaba dentro de un `if` y
   DESAPARECÍA de la barra cuando el proyecto no traía referencia guardada:
   los generados solo desde la descripción, y los antiguos que no la
   persistían. Un botón que se va de la barra no parece apagado, parece que
   alguien lo ha quitado — y se busca por todos los menús.

LAS DOS PANTALLAS: el Estudio 3D y su clon de pruebas. Un arreglo puesto en una
y no en la otra no es un arreglo (regla 1).

EL ESTUDIO 3D ESTÁ CONGELADO (regla 1) desde el 04/09. Se toca porque lo pide
el master, que es quien lo congeló.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsx_limpio import sin_comentarios  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMPONENTES = os.path.join(RAIZ, "frontend", "src", "components")
PANTALLAS = ("AIRenderStudio.jsx", "Estudio3DLab.jsx")


def _limpio(nombre):
    with open(os.path.join(COMPONENTES, nombre), "r", encoding="utf-8") as f:
        cuerpo = sin_comentarios(f.read())
    # El recorte de comentarios no puede haberse comido lo que se va a mirar:
    # este fichero explica los dos fallos CITANDO el código (reglas 24, 34, 35).
    assert "interactiveMode" in cuerpo, nombre
    assert "setCompareOn" in cuerpo, nombre
    return cuerpo


# ── 1. El visor interactivo se usa con los dedos ─────────────────────────────

def test_EL_VISOR_RESPONDE_AL_TACTO_Y_NO_SOLO_AL_RATON():
    """ESTE es el fallo: cero manejadores táctiles en toda la pantalla."""
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        for manejador in ("onTouchStart", "onTouchMove", "onTouchEnd"):
            assert manejador in cuerpo, (
                "%s no tiene %s: en una tablet el visor interactivo se enciende "
                "y no hace nada" % (pantalla, manejador))


def test_UN_DEDO_ARRASTRA_Y_DOS_HACEN_PINZA():
    """Solo arrastrar deja el zoom sin gesto; solo pinza, sin encuadre."""
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        i = cuerpo.index("onTouchStart")
        bloque = cuerpo[i:i + 1800]
        assert "e.touches" in bloque or "t.length" in bloque, pantalla
        assert "t.length === 1" in bloque, (
            "%s no distingue el gesto de UN dedo (arrastrar)" % pantalla)
        assert "t.length === 2" in bloque, (
            "%s no distingue el gesto de DOS dedos (pinza para el zoom)" % pantalla)
        assert "Math.hypot" in bloque, (
            "%s no mide la separación entre los dos dedos: sin eso no hay pinza"
            % pantalla)


def test_EL_NAVEGADOR_NO_SE_QUEDA_EL_GESTO():
    """Sin `touchAction: none` y sin cortar el evento, el navegador se lleva el
    arrastre para desplazar la página y el render no se mueve — que desde
    fuera es exactamente «no funciona»."""
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        # ATADO A `interactiveMode`, no a cualquier `touchAction` del fichero:
        # el visor 360º tiene el suyo, y buscarlo suelto dejaba pasar la
        # mutación que se lo quitaba al visor interactivo. Es la trampa de
        # siempre —el candado se conforma con encontrar el texto en otro sitio.
        assert re.search(r"interactiveMode \?\s*\{\s*touchAction:\s*'none'", cuerpo), (
            "%s no declara `touchAction: none` en el visor INTERACTIVO: el "
            "navegador se queda el arrastre para desplazar la página y el "
            "render no se mueve" % pantalla)
        i = cuerpo.index("onTouchMove")
        assert "preventDefault" in cuerpo[i:i + 900], (
            "%s no corta el gesto en `onTouchMove`" % pantalla)


def test_EL_GESTO_VA_EN_UN_REF_Y_NO_EN_EL_ESTADO():
    """`touchmove` dispara decenas de veces por segundo: repintar en cada uno
    deja el gesto a trompicones."""
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        assert "const gesto = useRef(" in cuerpo, (
            "%s guarda el gesto en el estado en vez de en un ref" % pantalla)


def test_EL_ZOOM_TIENE_MANDOS_A_LA_VISTA():
    """Solo con rueda, en una tablet no hay zoom y en un portátil no se
    adivina. Y el porcentaje dice que el botón está haciendo algo."""
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        i = cuerpo.index("interactiveMode && (")
        bloque = cuerpo[i:i + 1600]
        assert 'title="Acercar"' in bloque and 'title="Alejar"' in bloque, (
            "%s no tiene botones de zoom visibles" % pantalla)
        assert "Math.round(zoom * 100)" in bloque, (
            "%s no enseña a qué zoom está" % pantalla)
        assert "setPanX(0)" in bloque, (
            "%s no tiene forma de volver al encuadre original: con el render "
            "arrastrado fuera de la caja, no hay manera de recuperarlo"
            % pantalla)


# ── 2. Comparar no se esconde ────────────────────────────────────────────────

def test_COMPARAR_SIGUE_EN_LA_BARRA_AUNQUE_NO_HAYA_REFERENCIA():
    """Un botón que desaparece se busca por todos los menús; uno apagado se
    entiende."""
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        assert "{referenciaInicial && (" not in cuerpo, (
            "%s vuelve a esconder el botón de Comparar cuando el proyecto no "
            "trae referencia" % pantalla)
        i = cuerpo.index("setCompareOn(v => !v)")
        bloque = cuerpo[max(0, i - 400):i + 900]
        assert "disabled={!referenciaInicial}" in bloque, (
            "%s ya no apaga Comparar cuando no hay nada con lo que comparar: "
            "pulsarlo abriría una comparación vacía" % pantalla)


def test_COMPARAR_APAGADO_DICE_POR_QUE():
    """«No se puede» sin decir por qué obliga a preguntar."""
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        i = cuerpo.index("setCompareOn(v => !v)")
        bloque = cuerpo[i:i + 1200]
        j = bloque.find("title={referenciaInicial")
        assert j >= 0, "%s no explica por qué Comparar está apagado" % pantalla
        explicacion = bloque[j:j + 800]
        # La rama del `:` es la que se lee con el botón apagado.
        assert ":" in explicacion and "referencia" in explicacion.lower(), pantalla
        assert "croquis" in explicacion.lower() or "foto" in explicacion.lower(), (
            "%s dice que no se puede comparar pero no dice qué hacer para "
            "poder" % pantalla)
