# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
UN PROYECTO QUE SE ABRE VACÍO NO DA ERROR: PARECE QUE SE HA PERDIDO.

Dos cosas que el master vio el 14/09/2026 en el Estudio 3D, y las dos son del
mismo tipo — nada falla, solo enseñan otra cosa:

1. «HAY PROYECTOS ANTIGUOS QUE NO LOS PUEDO ABRIR.»
   Hasta que el historial de fotos se separó a la colección `render3d_images`,
   cada proyecto guardaba su render DENTRO del documento, en `images`. Al abrir
   solo se leía la colección nueva, así que todo proyecto anterior a ese cambio
   se abría en blanco: el nombre, el cliente y las medidas sí, y ni una foto.
   Los de julio de 2026 son justo esos.

   Ahora, y SOLO cuando el historial nuevo viene vacío, se usa la copia
   heredada. Ese «solo» es la mitad importante: si se rehidratara siempre, una
   foto borrada a propósito reaparecería al reabrir el proyecto. El otro hueco
   —que alguien borre TODAS las fotos y vuelva la heredada— lo cierra el
   servidor, que al borrar la última vacía también esa copia.

2. «QUE AL COMPARAR SALGAN LAS IMÁGENES PRIMITIVAS DEL PROYECTO, NO LAS FOTOS
   POSTERIORES DE ACABADOS, ENCIMERAS O CAMBIOS.»
   Comparar usaba `originalRef || refImage`. Ese `|| refImage` es el fallo: en
   cuanto el proyecto no traía guardada la primera referencia —los antiguos no
   la traen—, el lado «Referencia» enseñaba la ÚLTIMA imagen subida, que es
   justo la foto del acabado. Comparar un render con la imagen que acaba de
   cambiarlo no compara nada, y como sale una foto de verdad no parece un
   error.

CÓMO SE COMPRUEBA: sobre el JSX recortado de comentarios, porque este fichero
explica los dos fallos CITANDO el código malo (`originalRef || refImage` está
escrito ahí arriba). Es la trampa en la que este repo ha caído cuatro veces
—reglas 24, 34 y 35—, y aquí estaba servida.

Y las dos pantallas: el Estudio 3D y su clon de pruebas. Un arreglo puesto en
una y no en la otra no es un arreglo (regla 1).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsx_limpio import sin_comentarios  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMPONENTES = os.path.join(RAIZ, "frontend", "src", "components")
PANTALLAS = ("AIRenderStudio.jsx", "Estudio3DLab.jsx")
AI_ENGINE = os.path.join(RAIZ, "backend", "routes", "ai_engine.py")


def _limpio(nombre):
    with open(os.path.join(COMPONENTES, nombre), "r", encoding="utf-8") as f:
        crudo = f.read()
    cuerpo = sin_comentarios(crudo)
    # El recorte no puede haberse comido el código que se va a mirar.
    assert "const loadDesign" in cuerpo, nombre
    assert "referenciasIniciales" in cuerpo, nombre
    return cuerpo


# ── 1. Los proyectos antiguos se abren ───────────────────────────────────────

def test_UN_PROYECTO_ANTIGUO_RECUPERA_LA_FOTO_DEL_DOCUMENTO():
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        i = cuerpo.index("const loadDesign")
        bloque = cuerpo[i:cuerpo.index("const deleteDesign", i)]
        assert "docGuardado" in bloque, (
            "%s ya no guarda el documento para poder rescatar las fotos "
            "heredadas: los proyectos de antes del cambio se abren en blanco"
            % pantalla)
        assert re.search(r"docGuardado\?\.images", bloque), (
            "%s no lee `images` del documento: es donde viven las fotos de los "
            "proyectos antiguos" % pantalla)


def test_LA_COPIA_HEREDADA_SOLO_SE_USA_CON_EL_HISTORIAL_VACIO():
    """Si se usara siempre, una foto borrada a propósito volvería al reabrir."""
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        i = cuerpo.index("const fotosValidas = await cargarHistorialGuardado")
        bloque = cuerpo[i:i + 2000]
        pos_si = bloque.index("if (fotosValidas.length)")
        pos_heredadas = bloque.index("docGuardado?.images")
        pos_else = bloque.index("} else {")
        assert pos_si < pos_else < pos_heredadas, (
            "%s usa las fotos heredadas fuera de la rama del historial vacío: "
            "una foto borrada reaparecería al reabrir" % pantalla)


def test_AL_BORRAR_LA_ULTIMA_FOTO_EL_SERVIDOR_VACIA_LA_COPIA_HEREDADA():
    """La otra mitad: sin esto, borrar la última foto de un proyecto antiguo no
    la borra de verdad — vuelve sola al reabrir, por el rescate de arriba."""
    with open(AI_ENGINE, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    i = cuerpo.index("async def delete_design_image")
    bloque = cuerpo[i:cuerpo.index("@ai_engine_router.delete(\"/designs/{design_id}\")", i)]
    sin_com = "\n".join(l for l in bloque.splitlines() if not l.strip().startswith("#"))
    assert "total == 0" in sin_com and '"images"' in sin_com, (
        "al borrar la última imagen ya no se vacía `images` del documento: la "
        "foto borrada volvería al reabrir el proyecto")


# ── 2. Comparar enseña lo del principio ──────────────────────────────────────

def test_COMPARAR_NO_CAE_EN_LA_ULTIMA_IMAGEN_SUBIDA():
    """ESTE es el fallo: `originalRef || refImage` ponía la foto del acabado en
    el lado «Referencia»."""
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        assert "const referenciaInicial = originalRef || refImage" not in cuerpo, (
            "%s vuelve a comparar contra la ÚLTIMA imagen subida: si el "
            "proyecto no trae la primera, el lado «Referencia» enseña la foto "
            "del acabado o de la encimera" % pantalla)
        assert "const referenciasIniciales" in cuerpo, pantalla


def test_LO_SUBIDO_DESPUES_DEL_PRIMER_RENDER_NO_ENTRA_EN_COMPARAR():
    """Antes del render, lo que se sube es el encargo; después son cambios
    sobre un render que ya existe."""
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        i = cuerpo.index("const addReference")
        bloque = cuerpo[i:i + 900]
        assert "setRefsIniciales" in bloque, pantalla
        assert re.search(r"if \(!renderResult && renderHistory\.length === 0\)", bloque), (
            "%s mete en Comparar cualquier imagen que se suba, también las de "
            "acabados y encimeras posteriores al render" % pantalla)


def test_LAS_REFERENCIAS_DEL_PRINCIPIO_SE_GUARDAN_Y_VUELVEN():
    """Sin guardarlas, al reabrir el proyecto Comparar se queda otra vez sin
    ellas y vuelve a caer en la última subida — el fallo de siempre."""
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        assert "referenceImages: await Promise.all(" in cuerpo, (
            "%s no guarda las referencias del principio con el proyecto" % pantalla)
        i = cuerpo.index("const loadDesign")
        bloque = cuerpo[i:cuerpo.index("const deleteDesign", i)]
        assert "full.referenceImages" in bloque, (
            "%s no las recupera al abrir" % pantalla)


def test_UN_PROYECTO_NUEVO_NO_HEREDA_LAS_REFERENCIAS_DEL_ANTERIOR():
    """Comparar el render de una cocina contra el croquis de otra es peor que
    no comparar."""
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        assert cuerpo.count("setRefsIniciales([])") >= 3, (
            "%s no limpia las referencias del principio en todos los sitios "
            "donde se empieza de cero (proyecto nuevo, abrir otro, limpiar)"
            % pantalla)


def test_SI_EL_ENCARGO_TRAIA_VARIAS_SE_PUEDEN_VER_TODAS():
    """Guardar varias y enseñar solo la primera deja fuera el resto del encargo
    sin decirlo."""
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        assert "setIdxComparar" in cuerpo, pantalla
        assert "referenciasIniciales.length > 1" in cuerpo, (
            "%s no ofrece pasar de una referencia a otra en Comparar" % pantalla)
