# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: en el móvil, el alto se lo queda el RENDER.

EL CASO
-------
El master, 18/08, mandando dos pantallazos del Estudio 3D desde su móvil:
«estoy con el móvil, optimiza todo bien q se vea todo mejor».

En esos pantallazos, de arriba abajo:

  · «ESTUDIO 3D» partido en DOS líneas,
  · «Créditos: 37 restantes» ocupando media fila,
  · «Clien·» cortado, porque Cliente/Ref habían bajado a otra fila,
  · la barra de acciones (Deco, HD, Render 8K, PDF, CAD DXF…) en TRES filas,
  · y el render, que es lo único que hay que ver, en una franja del medio.

Entre la cabecera y la barra se iba un tercio largo de la pantalla en cosas
que no son el diseño.

LO QUE SE PROTEGE
-----------------
Nada de esto da un error ni rompe un cálculo: simplemente hace el ERP
incómodo en el aparato desde el que más se usa. Y por eso mismo se deshace
solo — cualquiera que añada un botón a esa barra o alargue un rótulo vuelve a
partirla sin enterarse, porque en su pantalla grande se ve bien.

Los cambios son SOLO por debajo del ancho de móvil (`sm:` / `max-sm:`): en
pantalla grande todo se queda como estaba.
"""
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ESTUDIO = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")


def _codigo():
    with open(ESTUDIO, encoding="utf-8") as f:
        src = f.read()
    return "\n".join(l.split("//")[0] for l in src.splitlines())


def test_el_titulo_no_se_parte_en_dos_lineas():
    codigo = _codigo()
    i = codigo.index(">Estudio 3D</h1>")
    linea = codigo[max(0, i - 260):i]
    assert "whitespace-nowrap" in linea, (
        "«ESTUDIO 3D» vuelve a poder partirse en dos lineas en el movil, y esa "
        "segunda linea se la quita al render")


def test_los_creditos_van_cortos_en_movil():
    """«Créditos: 37 restantes» empujaba Cliente/Ref a otra fila, y ahi es
    donde el campo Cliente se quedaba en «Clien·»."""
    codigo = _codigo()
    assert 'className="sm:hidden">{aiCredits.restantes}' in codigo, (
        "el contador de creditos vuelve a salir con su texto largo en el "
        "movil: parte la cabecera en una fila mas")
    assert 'className="hidden sm:inline"' in codigo, \
        "se ha perdido el texto completo de creditos para pantalla grande"


def test_la_barra_de_acciones_no_se_parte_en_movil():
    """Envuelta eran TRES filas de botones. Deslizandose es una."""
    codigo = _codigo()
    assert "max-sm:flex-nowrap" in codigo, (
        "la barra de acciones vuelve a envolverse en el movil: tres filas de "
        "botones comiendose el alto del render")
    assert "max-sm:overflow-x-auto" in codigo, (
        "la barra no se puede deslizar: sin envolver y sin scroll, los botones "
        "del final quedan inalcanzables, que es peor que antes")


def test_el_render_tiene_alto_garantizado_SIEMPRE():
    """EL FALLO QUE COMETI, y merece quedar escrito.

    El primer arreglo puso el alto minimo SOLO en pantallas estrechas
    (`sm:min-h-0`). Pero al GIRAR el movil pasa a ser una pantalla ANCHA —se le
    aplican las reglas de escritorio— y sin embargo tiene MUY POCO ALTO: unos
    430 px. Ahi la cabecera, la barra, el cuadro de edicion y el historial
    sumaban mas que la pantalla, y el render se quedaba en CERO de alto.

    El master, con el movil en horizontal: «se ve todo mejor, LOS DISEÑOS NO SE
    VEN». Efectivamente todo lo demas cabia mejor... porque se habia comido el
    diseño.

    LA ANCHURA NO DICE NADA DEL ALTO. El minimo va sin condicion de ancho."""
    codigo = _codigo()
    assert "min-h-[42vh]" in codigo, (
        "el render vuelve a quedarse sin alto minimo: encajonado entre la "
        "cabecera, la barra y el cuadro de edicion se queda en una franja, y "
        "es lo unico que hay que ver")
    assert "min-h-[42vh] sm:min-h-0" not in codigo, (
        "el alto minimo del render ha vuelto a depender del ANCHO de pantalla: "
        "girando el movil se desactiva y el diseño desaparece, que es "
        "exactamente el fallo que reporto el master")


def test_en_pantalla_baja_el_historial_deja_sitio_al_diseño():
    """Un movil en horizontal tiene ~430 px de alto. La tira del historial se
    encoge por ALTO DE VENTANA —no por ancho, que es lo que no dice nada."""
    codigo = _codigo()
    assert "tira-historial" in codigo,         "la tira del historial ya no se puede encoger en pantallas bajas"
    ruta = os.path.join(RAIZ, "frontend", "src", "index.css")
    with open(ruta, encoding="utf-8") as f:
        css = f.read()
    assert "max-height: 560px" in css, (
        "se ha quitado la regla de pantalla baja: en el movil en horizontal el "
        "historial vuelve a comerse el alto del render")
    i = css.index("max-height: 560px")
    assert ".tira-historial" in css[i:i + 400],         "la regla de pantalla baja ya no encoge la tira del historial"


def test_en_pantalla_grande_no_se_ha_cambiado_nada():
    """Los arreglos son de movil. Si se cuelan en el escritorio, se arregla una
    pantalla rompiendo la otra."""
    codigo = _codigo()
    # La barra sigue envolviendo por defecto; el `nowrap` es solo `max-sm:`.
    assert "'flex-wrap max-sm:flex-nowrap" in codigo, (
        "el «no envolver» ha dejado de ser solo de movil: en el escritorio la "
        "barra de acciones se saldra por un lado")
    assert 'hidden sm:inline' in codigo, \
        "los rotulos completos han desaparecido tambien de la pantalla grande"


# ─── EL RENDER SE ESCALA, NO SE RECORTA ────────────────────────────────────
#
# Segunda vuelta del master: «sigue viendose mal en horizontal». Y ya NO era
# falta de sitio: el hueco estaba, pero se veia una franja del centro de la
# cocina, cortada arriba y abajo.
#
# El recuadro que envuelve al render ABRAZA a la imagen a proposito: las marcas
# de instalaciones se colocan en % de ese recuadro, asi que si no coincide
# clavado con la foto, cada enchufe cae donde no es (el fallo del «letterbox»,
# que ya costo arreglar una vez).
#
# Pero abrazandola, el `max-h-full` de la imagen NO SE RESUELVE contra nada
# —el padre tiene alto automatico— y en vez de encogerse, la imagen se RECORTA.
#
# Sabiendo la PROPORCION REAL de la foto, el recuadro se dimensiona por CSS y
# hace las dos cosas: entra entero y sigue abrazandola.


def test_el_recuadro_del_render_lleva_la_proporcion_de_la_imagen():
    codigo = _codigo()
    assert "aspectRatio: String(ratioRender)" in codigo, (
        "el recuadro del render ya no lleva la proporcion de la imagen: sin "
        "ella no se puede escalar sin recortar, y en horizontal se vuelve a "
        "ver solo una franja")
    assert "setRatioRender" in codigo, \
        "ya no se lee la proporcion real del render"


def test_la_proporcion_se_lee_de_la_imagen_y_no_se_supone():
    """No todos los renders son 16:9 —los 4K y las laminas tecnicas no— y
    suponerlo devolveria el recorte por otro lado."""
    codigo = _codigo()
    # ACOTADO AL SITIO. `naturalWidth` sale en otros tres puntos del fichero
    # (el marcado de agua, la descarga con marcas), asi que buscarlo suelto
    # daba verde aunque se vaciara justo esta parte: el candado no mordia.
    i = codigo.index("setRatioRender(")
    bloque = codigo[max(0, i - 300):i + 120]
    assert "naturalWidth" in bloque and "naturalHeight" in bloque, (
        "la proporcion vuelve a darse por supuesta en vez de leerse de la "
        "imagen: con un render que no sea 16:9 se recorta otra vez")


def test_colocar_y_arrastrar_una_marca_miden_LO_MISMO():
    """Al colocar se medía sobre la IMAGEN y al arrastrar sobre el RECUADRO.
    Coincidian solo mientras el recuadro abrazase la foto clavada — y eso es
    justo lo que acaba de cambiar. Dos formas de medir lo mismo es un fallo
    esperando a que algo se mueva."""
    codigo = _codigo()
    i = codigo.index("const seguirArrastre")
    cuerpo = codigo[i:i + 700]
    assert "render-annot-img" in cuerpo, (
        "el arrastre de marcas vuelve a medir sobre el recuadro y no sobre la "
        "imagen: los enchufes se moveran a donde no van")
