# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
PINTAR ENCIMA DEL RENDER PARA SEÑALAR DÓNDE VA EL CAMBIO.

El master, 07/09/2026: «que pueda pulsar un botón de pintar y dibujar encima
del dibujo».

LO ÚNICO QUE DE VERDAD PUEDE SALIR MAL AQUÍ
───────────────────────────────────────────
Que el modelo PINTE LAS MARCAS. Si le llega una imagen con un churro rojo
encima y nadie le dice qué es, hace lo que hacen los modelos de imagen: lo
reproduce. Y entonces el render vuelve con una raya roja atravesando los
muebles. Por eso el encargo dice, lo primero y en mayúsculas, que las marcas de
color son señales del diseñador y que la imagen final no puede contener
ninguna.

Y LOS DOS DE SIEMPRE, que ya costaron un arreglo cada uno:

  · `editingRender: true` DENTRO DEL CUERPO. Una imagen con trazos a mano
    encima es justo lo que el detector de croquis del servidor busca: sin
    declararlo, la tomaría por un dibujo y reharía la cocina entera.
  · `memoriaDeCambios()`, para no perder los acabados ya aplicados — que es
    literalmente lo que el master reclamó el 06/09 con el botón de decorador.

TRES DETALLES DE LA TABLET QUE NO SON ESTÉTICA
──────────────────────────────────────────────
  1. `touch-action: none` en el lienzo. Sin él, en una tablet el navegador
     entiende el trazo como un gesto de arrastrar la página: se mueve la
     pantalla y no se pinta nada.
  2. Eventos `pointer`, no `mouse`. Con eventos de ratón no se dibuja con el
     dedo, que es como se va a usar.
  3. Los trazos, en coordenadas de 0 a 1. En píxeles, girar la tablet los
     dejaría desplazados o los perdería.

Y la composición se hace a la RESOLUCIÓN NATIVA del render, no a la del lienzo
en pantalla: en una tablet el lienzo mide unos cientos de píxeles, así que
mandar eso sería mandarle al modelo una miniatura de su propio render.
(Que lo pintado sale de verdad en la imagen, y en su sitio, se comprobó
ejecutando `componerPintado` en un Chromium: un trazo del 25 % al 75 % de una
imagen de 200×100 sale rojo en el centro y deja limpias las esquinas.)
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSX = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")


def _lee():
    with open(JSX, "r", encoding="utf-8") as f:
        return f.read()


def _funcion(cuerpo, nombre):
    i = cuerpo.index(f"const {nombre} = ")
    m = re.search(r"\n  const \w+ = ", cuerpo[i + 10:])
    return cuerpo[i:i + 10 + m.start()] if m else cuerpo[i:]


def _cuerpo_de_la_peticion(fn):
    """El objeto que va DENTRO de `JSON.stringify(...)`, con un emparejador de
    llaves de verdad. Buscar por texto no distingue «está en la función» de
    «está en el cuerpo», y ese es exactamente el fallo que se vio el 07/09 en
    otros cuatro botones: `editingRender` colocado como opción de `fetch`, que
    `fetch` ignora sin decir nada."""
    i = fn.find("JSON.stringify(")
    if i < 0:
        return ""
    j = i + len("JSON.stringify(")
    prof, comilla, salida = 1, "", []
    while j < len(fn) and prof > 0:
        c = fn[j]
        if comilla:
            if c == "\\":
                salida.append(fn[j:j + 2]); j += 2; continue
            if c == comilla:
                comilla = ""
        elif c in "\"'`":
            comilla = c
        elif c in "({[":
            prof += 1
        elif c in ")}]":
            prof -= 1
            if prof == 0:
                break
        salida.append(c)
        j += 1
    return "".join(salida)


# ─── LO QUE SE LE DICE AL MODELO ─────────────────────────────────────────────

def test_al_modelo_se_le_dice_que_las_MARCAS_NO_SE_PINTAN():
    """Es el fallo que devolvería un render con una raya roja en los muebles."""
    fn = _funcion(_lee(), "aplicarPintado")
    assert "NO PUEDE CONTENER" in fn, (
        "no se le prohíbe al modelo reproducir las marcas: las pintará")
    assert "SEÑALES" in fn or "señales" in fn
    assert "DÓNDE hay que actuar" in fn


def test_se_le_dice_QUE_COLORES_ha_usado_el_disenador():
    """«Borra las marcas de color» es vago; «borra las marcas rojas y azules»
    no. Los colores salen de los trazos, no de una lista escrita a mano."""
    fn = _funcion(_lee(), "aplicarPintado")
    assert "colores" in fn and "trazos.map" in fn


def test_lo_pintado_se_manda_como_referencia_y_DECLARADO():
    """Una imagen con trazos a mano encima es justo lo que el detector de
    croquis del servidor busca. Sin declararlo, rehace la cocina entera."""
    fn = _funcion(_lee(), "aplicarPintado")
    cuerpo = _cuerpo_de_la_peticion(fn)
    assert "referenceImage: pintada" in cuerpo, (
        "se está mandando el render sin las marcas: el modelo no vería nada")
    assert "editingRender: true" in cuerpo, (
        "`editingRender` no está DENTRO del cuerpo de la petición: si está "
        "fuera, `fetch` lo ignora y al servidor no le llega")


def test_pintar_NO_pierde_los_acabados_ya_aplicados():
    """Lo que el master reclamó el 06/09 con el botón de decorador."""
    fn = _funcion(_lee(), "aplicarPintado")
    assert "memoriaDeCambios()" in fn


def test_lo_senalado_se_APUNTA_para_las_vueltas_siguientes():
    """Si no entra en la lista, la vuelta siguiente puede deshacerlo."""
    fn = _funcion(_lee(), "aplicarPintado")
    assert "setEditAppliedChanges" in fn


# ─── LA TABLET ───────────────────────────────────────────────────────────────

def test_el_lienzo_no_deja_que_el_navegador_arrastre_la_pagina():
    cuerpo = _lee()
    i = cuerpo.index("ref={lienzoRef}")
    trozo = cuerpo[i - 400:i + 700]
    assert "touchAction: 'none'" in trozo, (
        "sin `touch-action: none`, en la tablet el dedo mueve la página en vez "
        "de pintar")


def test_se_dibuja_con_POINTER_y_no_con_MOUSE():
    """Con eventos de ratón no se puede pintar con el dedo."""
    cuerpo = _lee()
    i = cuerpo.index("ref={lienzoRef}")
    trozo = cuerpo[i:i + 700]
    for ev in ("onPointerDown", "onPointerMove", "onPointerUp", "onPointerCancel"):
        assert ev in trozo, f"falta {ev}"
    assert "onMouseDown" not in trozo


def test_los_trazos_van_en_PROPORCION_y_no_en_pixeles():
    """Al girar la tablet el lienzo cambia de tamaño; en píxeles, lo pintado se
    quedaría desplazado o se perdería."""
    fn = _funcion(_lee(), "puntoDe")
    assert "(e.clientX - r.left) / r.width" in fn
    assert "(e.clientY - r.top) / r.height" in fn


def test_se_compone_a_la_RESOLUCION_DEL_RENDER_no_a_la_del_lienzo():
    """En una tablet el lienzo mide unos cientos de píxeles: componer ahí sería
    mandarle al modelo una miniatura de su propio render."""
    fn = _funcion(_lee(), "componerPintado")
    assert "c.width = im.naturalWidth" in fn and "c.height = im.naturalHeight" in fn
    assert "lienzoRef" not in fn, (
        "la composición está mirando el lienzo de pantalla en vez de la imagen")


def test_deshacer_REPINTA_en_vez_de_borrar():
    """Un canvas no recuerda lo que hay debajo de un trazo: «deshacer» solo
    puede hacerse repintando desde cero la lista de trazos."""
    cuerpo = _lee()
    assert "const deshacerTrazo = () => setTrazos(prev => prev.slice(0, -1))" in cuerpo
    fn = _funcion(cuerpo, "repintar")
    assert "clearRect" in fn and "for (const t of trazos)" in fn


def test_un_TOQUE_SUELTO_deja_marca_EN_LOS_DOS_SITIOS():
    """Señalar con un toque es lo natural en una tablet, y `stroke` con un solo
    punto no pinta nada.

    SE MIRA EN LOS DOS: el lienzo de pantalla (`repintar`) y la imagen que se
    manda (`componerPintado`). Si solo lo hiciera uno, el toque se vería
    mientras se pinta y NO llegaría al modelo — o al revés. Se probó quitándolo
    de uno solo, y el candado que miraba únicamente `repintar` se quedaba en
    verde con la marca perdiéndose por el camino.
    """
    cuerpo = _lee()
    for nombre in ("repintar", "componerPintado"):
        fn = _funcion(cuerpo, nombre)
        assert "t.puntos.length === 1" in fn and "arc(" in fn, (
            f"«{nombre}» no marca un toque suelto")


# ─── EL BOTÓN EXISTE Y SE PUEDE SALIR ────────────────────────────────────────

def test_el_boton_de_pintar_esta_en_la_pantalla():
    """Una función sin botón no existe: ya pasó con «Mi área» del
    cooperativista, escrita entera y sin un sitio desde el que abrirla."""
    cuerpo = _lee()
    assert "onClick={() => setPintando(v => !v)}" in cuerpo
    assert ">Pintar<" in cuerpo or "Pintar</span>" in cuerpo


def test_el_lienzo_solo_esta_cuando_se_esta_pintando():
    """Si estuviera siempre, se tragaría los clics del render: ni zoom, ni
    marcas de instalaciones, ni el arrastre del 360º."""
    cuerpo = _lee()
    assert "{pintando && (" in cuerpo
    i = cuerpo.index("{pintando && (")
    assert "ref={lienzoRef}" in cuerpo[i:i + 900]


def test_salir_de_pintar_LIMPIA_los_trazos():
    """Si no, al volver a abrir el pincel aparecerían las marcas de la vez
    anterior sobre un render que ya es otro."""
    cuerpo = _lee()
    assert "const salirDePintar = () => { setPintando(false); setTrazos([]);" in cuerpo


def test_no_se_puede_aplicar_sin_haber_pintado_nada():
    """Sería gastar un render (y un crédito) para no decir nada."""
    fn = _funcion(_lee(), "aplicarPintado")
    assert "!trazos.length" in fn
