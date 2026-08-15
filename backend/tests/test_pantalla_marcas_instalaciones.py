# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: los puntos de instalaciones se colocan, se leen y se imprimen.

Este papel se lo lleva el electricista a PICAR PARED. Si un punto esta dos
palmos corrido, o no se ve en el papel, la roza se hace donde no es. Y eso no
da ningun error: da un PDF con pinta de plano.

Tres cosas que reporto el master el 14/08/2026, las tres del mismo dia:

1. «q se puedan mover en el dibujo para posicionar mejor y editar».
   Un punto solo se podia PONER de un clic. La IA los coloca aproximados, asi
   que casi siempre habia que recolocarlos — y la unica forma era borrarlos y
   volver a ponerlos a ojo hasta acertar.

2. «con un tamaño mas grande porque no se ve casi al imprimir».
   Al «quemar» las marcas sobre la imagen se dibujaban con un radio FIJO de
   `8 * scale` px. Sobre un lienzo de 2.500 px eso son 16 px, y el PDF metia
   luego esa imagen en dos tercios de un A4: puntos de menos de un milimetro
   en el papel. Ademas la cota iba en el color de la marca sobre fondo blanco,
   o sea ilegible encima de una cocina blanca.

3. «esto q sale al pulsar esquema gremio, tambien mas grande […] esta mal
   estructurado el espacio».
   Al dibujo se le daban dos tercios de pagina y el tercio restante era una
   columna de texto con cuatro lineas. Un render 16:9 en 184 mm de ancho solo
   ocupa 103 mm de los 168 de alto disponibles: el plano salia pequeño Y encima
   quedaba media pagina en blanco.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ESTUDIO = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def _cuerpo(src, inicio, fin="\n  };"):
    i = src.index(inicio)
    return src[i:src.index(fin, i)]


# ─── 1. Un punto se arrastra ────────────────────────────────────────────────

def test_un_punto_se_puede_arrastrar_para_colocarlo():
    """CANDADO PRINCIPAL. Sin esto solo queda borrar y volver a poner a ojo."""
    src = _leer(ESTUDIO)
    for pieza in ("empezarArrastre", "seguirArrastre", "soltarArrastre"):
        assert pieza in src, f"se ha quitado «{pieza}»: los puntos ya no se mueven"
    assert "onPointerDown={empezarArrastre(i)}" in src, \
        "el punto ya no engancha el arrastre"
    assert "onPointerMove={seguirArrastre}" in src, \
        "el punto se engancha pero no sigue al dedo"


def test_el_arrastre_va_con_el_dedo_y_no_solo_con_el_raton():
    """La obra se revisa en la tablet. Con eventos de RATON el punto no se
    puede mover con el dedo: la funcion existe y no sirve de nada."""
    src = _leer(ESTUDIO)
    cuerpo = _cuerpo(src, "const empezarArrastre", "\n  };")
    assert "onMouseDown" not in cuerpo and "mousemove" not in cuerpo, \
        "el arrastre ha vuelto a eventos de raton: en tablet no funciona"
    assert "setPointerCapture" in cuerpo, (
        "sin capturar el puntero, el punto se suelta en cuanto el dedo se sale "
        "del circulo — que con un circulo de 40 px pasa siempre")


def test_arrastrar_no_abre_el_editor_encima():
    """Al soltar llega tambien un clic. Sin distinguirlo, cada vez que se
    recoloca un punto se abriria el panel de edicion tapando el dibujo."""
    src = _leer(ESTUDIO)
    cuerpo = _cuerpo(src, "const soltarArrastre", "\n  };")
    assert "movido" in cuerpo, \
        "ya no se distingue un toque de un arrastre: al mover se abrira el editor"


def test_el_punto_se_mide_contra_la_capa_del_render():
    """Las marcas van en % del render. Si se miden contra otra caja —la ventana,
    el panel— el punto se guarda donde no es y el PDF sale mal."""
    src = _leer(ESTUDIO)
    assert "capaMarcasRef" in src, "no hay referencia a la capa del render"
    cuerpo = _cuerpo(src, "const seguirArrastre", "\n  };")
    assert "capaMarcasRef" in cuerpo and "getBoundingClientRect" in cuerpo, \
        "el arrastre ya no se mide contra la caja del render"


# ─── 2. Que se vea en el papel ──────────────────────────────────────────────

def test_la_marca_impresa_escala_con_el_dibujo():
    """CANDADO. Un radio en pixeles fijos se vuelve invisible en cuanto el PDF
    encoge la imagen. El tamaño sale del ANCHO DEL LIENZO."""
    src = _leer(ESTUDIO)
    cuerpo = _cuerpo(src, "const renderMarcadoDataUrl", "\n  });")
    m = re.search(r"const R = Math\.max\([^,]+,\s*cw \* ([\d.]+)\)", cuerpo)
    assert m, ("el radio de la marca ya no sale del ancho del lienzo: volvera a "
               "imprimirse un punto de menos de un milimetro")
    assert float(m.group(1)) >= 0.010, \
        f"el punto se ha quedado en {m.group(1)} del ancho: no se ve al imprimir"
    assert re.search(r"const FS = Math\.max\([^,]+,\s*cw \* ([\d.]+)\)", cuerpo), \
        "la cota tampoco escala con el lienzo"
    # Se mira el CODIGO, no los comentarios: «8 * scale» aparece a proposito en
    # la nota que explica por que ya no se usa.
    codigo = "\n".join(l.split("//")[0] for l in cuerpo.splitlines())
    assert "8 * scale" not in codigo, "ha vuelto el radio fijo de 8 px"


def test_la_cota_se_lee_sobre_una_cocina_blanca():
    """Iba en el color de la marca sobre fondo blanco. Encima de una cocina
    blanca con mucha luz, eso no se lee ni en pantalla ni en papel."""
    src = _leer(ESTUDIO)
    cuerpo = _cuerpo(src, "const renderMarcadoDataUrl", "\n  });")
    assert "rgba(255,255,255,.92)" not in cuerpo, \
        "la cota vuelve a ir sobre un recuadro blanco"
    assert "halo" in cuerpo.lower() or "rgba(255,255,255,.95)" in cuerpo, \
        "el punto ha perdido el halo blanco que lo separa del fondo"


# ─── 3. El esquema del gremio reparte bien la pagina ────────────────────────

def test_el_dibujo_ocupa_el_ancho_de_la_pagina():
    """Dos tercios para el dibujo y un tercio para cuatro lineas de texto
    dejaba el plano pequeño y media pagina en blanco."""
    src = _leer(ESTUDIO)
    cuerpo = _cuerpo(src, "const esquemaGremioPDF", "\n  };")
    assert "W * 0.66" not in cuerpo, \
        "el dibujo vuelve a ocupar dos tercios y la leyenda una columna vacia"
    assert "const areaW = W - M * 2" in cuerpo, \
        "el dibujo ya no usa el ancho entero de la pagina"


def test_la_leyenda_va_debajo_y_en_horizontal():
    """Cuatro datos no necesitan una columna entera: caben en una tira."""
    src = _leer(ESTUDIO)
    cuerpo = _cuerpo(src, "const esquemaGremioPDF", "\n  };")
    assert "const colW = (W - M * 2) / 4" in cuerpo, \
        "la leyenda ha vuelto a una columna lateral"
    assert "ALTO_LEY" in cuerpo, (
        "el alto del dibujo ya no descuenta la leyenda: o se solapan o vuelve a "
        "sobrar hueco")


def test_el_alto_del_dibujo_sale_de_lo_que_queda_libre():
    src = _leer(ESTUDIO)
    cuerpo = _cuerpo(src, "const esquemaGremioPDF", "\n  };")
    assert re.search(r"const areaH = H - cabY - ALTO_LEY", cuerpo), \
        "el dibujo ya no se ajusta a la altura que queda libre en la pagina"


# ─── 4. El panel de opciones se abre usable ─────────────────────────────────

def test_el_panel_se_abre_a_media_pantalla():
    """Arrancaba en 280 px: las pestañas «Cocina / Armario / Vestidor / Baño» se
    partian en cuatro lineas y habia que ensancharlo A MANO cada vez."""
    src = _leer(ESTUDIO)
    i = src.index("const [panelW, setPanelW]")
    cuerpo = src[i:src.index("});", i)]
    assert "280" not in cuerpo, "el panel vuelve a abrirse en 280 px"
    m = re.search(r"window\.innerWidth \* ([\d.]+)", cuerpo)
    assert m and float(m.group(1)) >= 0.5, \
        "el panel ya no se abre al menos a media pantalla"


def test_el_panel_se_puede_ensanchar_con_el_dedo():
    """El tirador iba con eventos de raton: en la tablet no se podia mover."""
    src = _leer(ESTUDIO)
    assert "onPointerDown={() => { resizingPanel.current = true" in src, \
        "el tirador del panel ha vuelto a eventos de raton"
    assert "window.addEventListener('pointermove', onMove)" in src, \
        "el redimensionado del panel ya no sigue al dedo"


# ─── 5. El boton de pantalla completa no se queda muerto ────────────────────
#
# 14/08/2026, el master: «el boton de reducir y expandir se ha quedado pillado».
#
# `activa` salia de `document.fullscreenElement`, que es lo correcto. El agujero
# estaba en que, si el navegador salia de pantalla completa POR SU CUENTA y no
# disparaba `fullscreenchange` —el gesto de volver de Android no siempre lo
# hace—, `activa` se quedaba en true. Entonces el boton decia «Reducir», al
# pulsarlo se llamaba a `exitFullscreen` sobre un documento que ya no estaba en
# pantalla completa, la promesa fallaba, el error se tragaba en silencio... y el
# boton no volvia a funcionar NUNCA. Muerto, y encima con la etiqueta cambiada.

BOTON = os.path.join(RAIZ, "frontend", "src", "components", "BotonPantallaCompleta.jsx")


def test_el_estado_se_relee_del_dom_al_pulsar():
    """CANDADO. Fiarse de lo que creiamos tener es lo que lo dejaba pillado."""
    src = _leer(BOTON)
    i = src.index("const alternar")
    cuerpo = src[i:src.index("\n  }, []);", i)]
    assert "enPantallaCompleta()" in cuerpo, (
        "el boton vuelve a decidir por su estado interno en vez de preguntar al "
        "navegador: si se desincroniza, se queda muerto")
    assert cuerpo.count("setActiva") >= 1, (
        "tras intentarlo no se vuelve a sincronizar: si el evento no llega —que "
        "es el caso que lo rompia— el boton se queda mintiendo")


def test_hay_mas_de_una_forma_de_enterarse_de_que_se_salio():
    """`fullscreenchange` no siempre llega en Android. `resize` y
    `visibilitychange` si, y con ellos el estado se recupera solo."""
    src = _leer(BOTON)
    for evento in ("fullscreenchange", "resize", "visibilitychange"):
        # Se exige el ALTA, no que la palabra aparezca: buscando solo «resize»
        # bastaba con el `removeEventListener` para dar el candado por bueno, y
        # entonces no protege de nada.
        assert re.search(rf"addEventListener\(\s*'{evento}'", src), (
            f"ya no se da de alta el aviso por «{evento}»: el boton puede volver "
            f"a quedarse pillado sin forma de recuperarse")
        assert re.search(rf"removeEventListener\(\s*'{evento}'", src), (
            f"«{evento}» se da de alta y no se quita: cada vez que se pinte el "
            f"boton se acumulara otro oyente")


def test_el_boton_nunca_se_queda_sin_salida():
    """Aunque falle, el estado acaba sincronizado: la siguiente pulsacion
    funciona. Antes un `return` temprano dejaba el boton en punto muerto."""
    src = _leer(BOTON)
    i = src.index("const alternar")
    cuerpo = src[i:src.index("\n  }, []);", i)]
    cuerpo_util = cuerpo[cuerpo.index("try {"):]
    assert "return;" not in cuerpo_util, (
        "ha vuelto un `return` dentro del intento: si esa rama falla, el estado "
        "no se sincroniza y el boton se queda pillado")
