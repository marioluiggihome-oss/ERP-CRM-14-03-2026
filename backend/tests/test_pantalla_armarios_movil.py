# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del presupuestador de ARMARIOS en el móvil.

QUÉ COMPRUEBA ESTE FICHERO Y QUÉ NO (puesto al día el 23/08/2026)
-----------------------------------------------------------------
Esto lee el JSX y comprueba que estén las clases: `max-lg:flex-col`,
`shrink-0`, `max-lg:overflow-x-auto`. Es barato y caza un borrado accidental
en un segundo, y por eso sigue aquí.

Lo que NO puede hacer es responder a la pregunta de verdad —«¿CABE?»—, porque
un nombre de clase no mide nada. Tampoco lo arreglaría jsdom: no tiene motor
de layout, así que por ahí sólo se pueden mirar los mismos nombres de clase
con otra sintaxis.

Eso se mide ahora en `frontend/e2e/armarios-movil.spec.js`, con un navegador
de verdad y un viewport de 390 px: se le preguntan al navegador los
rectángulos. Ahí está comprobado, con números, que los nueve botones conservan
su ancho, que la tira se desliza y que deslizarla trae el último botón dentro
de la pantalla, y que el armario queda DEBAJO de la configuración y no al lado
—que sin `max-lg:flex-col` acaba en x=410 con una pantalla de 390, o sea fuera
y sin manera de llegar a él—.

Las dos cosas se llevan bien: si alguien borra una clase, salta ésta en un
segundo; si alguien la deja pero rompe el layout de otra manera, salta la otra.

El master trabaja este módulo sobre todo con el teléfono, y en el teléfono no
fallaba nada: sencillamente no se podía usar. Un módulo que no da error pero no
deja trabajar es peor que uno que revienta, porque nadie abre una incidencia —
se deja de usar y se vuelve al papel.

Lo que se protege:

1. LAS TRES COLUMNAS SE APILAN. En escritorio hay tres columnas: configuración
   (320 px), el armario en el centro, y el presupuesto (320 px). En un móvil de
   390 px esas dos laterales se comían casi todo y el armario —lo único que hay
   que mirar— quedaba en una tira estrecha. Por debajo de `lg` van una debajo
   de otra.

   El corte es `lg` (1024 px) y NO `sm` a propósito: el móvil APAISADO mide unos
   850 px de ancho, o sea que se le aplicaban las reglas de escritorio y volvía
   a salir aplastado. Ya pasó una vez en el Estudio 3D.

2. Y SE PUEDEN DESLIZAR. Apilar sin poder desplazar es peor que no apilar: la
   fila de contenido llevaba `overflow-hidden`, así que el presupuesto —que
   ahora queda el último— se quedaba cortado abajo sin manera de llegar a él.

3. NINGÚN BOTÓN SE QUEDA FUERA DE LA PANTALLA. La cabecera tiene nueve botones
   (IA, RENDER, ESTUDIO 3D, PLANOS, PROYECTOS, DESPIECE, GUARDAR, PDF, ENVIAR AL
   PRESUPUESTO). En una fila que ni se envuelve ni se desliza, los últimos
   quedaban fuera: se podía configurar un armario entero y no había forma de
   guardarlo ni de mandarlo al presupuesto. Ahora es una tira que se desliza con
   el dedo y cada botón conserva su tamaño (`shrink-0`); si a alguien se le
   olvida el `shrink-0` en un botón nuevo, ese botón se aplasta hasta ser
   ilegible y esto se pone rojo.

4. LOS ACCESORIOS SE PUEDEN PONER CON EL DEDO. El panel decía «ARRASTRA
   ACCESORIOS AL ARMARIO» y usaba arrastre de HTML5 (`draggable` +
   `onDragStart`), que en una pantalla táctil NO EXISTE. En el móvil se tocaba
   el accesorio y no pasaba absolutamente nada. Ahora un toque lo deja armado y
   el toque siguiente, en el módulo, lo coloca — y los dos caminos (ratón y
   dedo) acaban en la MISMA función, para que no se arregle uno y se quede el
   otro a medias.

5. EL DIBUJO NO SE SALE DE LA PANTALLA. El armario se dibuja en un marco 4:3
   sobre el ancho disponible. En apaisado ese ancho es grande y el alto es
   ridículo: el marco salía más alto que la pantalla entera. Se le pone un tope
   en altura de ventana SIN tocar la proporción — estirar el marco deformaría el
   armario, y un armario dibujado con las proporciones cambiadas es un armario
   que se enseña mal a un cliente.
"""
import os
import re

import pytest

FRONT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend", "src", "components", "Armarios.jsx")


@pytest.fixture(scope="module")
def fuente():
    if not os.path.exists(FRONT):
        pytest.skip("Armarios.jsx no está en este entorno")
    with open(FRONT, encoding="utf-8") as f:
        return f.read()


def _region(fuente, desde, hasta):
    i = fuente.find(desde)
    assert i != -1, f"no se encuentra el trozo que empieza por: {desde[:60]}"
    j = fuente.find(hasta, i)
    assert j != -1, f"no se encuentra el final del trozo: {hasta[:60]}"
    return fuente[i:j]


# ─── 1 y 2. Las tres columnas se apilan y se pueden deslizar ────────────────

def test_las_columnas_se_apilan_en_el_movil(fuente):
    fila = _region(fuente, "{/* Content", "{/* Panel izquierdo")
    assert "max-lg:flex-col" in fila, (
        "la fila de contenido ya no se apila por debajo de lg: en el móvil las "
        "dos columnas laterales vuelven a aplastar el armario")


def test_el_corte_es_lg_y_no_sm(fuente):
    """En apaisado el móvil es ANCHO (unos 850 px) pero muy bajo."""
    fila = _region(fuente, "{/* Content", "{/* Panel izquierdo")
    assert "max-sm:flex-col" not in fila, (
        "el apilado se ha bajado a `sm`; con el móvil girado se pasa de 640 px "
        "y vuelven las tres columnas aplastadas")


@pytest.mark.parametrize("panel,ancla", [
    ("izquierdo (configuración)", "{/* Panel izquierdo"),
    ("derecho (presupuesto)", "{/* Panel derecho"),
])
def test_los_paneles_laterales_ocupan_todo_el_ancho_apilados(fuente, panel, ancla):
    i = fuente.find(ancla)
    assert i != -1, f"no se encuentra el panel {panel}"
    cabecera = fuente[i:i + 400]
    assert "max-lg:w-full" in cabecera, (
        f"el panel {panel} sigue clavado a 320 px cuando la pantalla es "
        "estrecha; apilado tiene que ocupar el ancho entero")


def test_apilado_se_puede_desplazar(fuente):
    fila = _region(fuente, "{/* Content", "{/* Panel izquierdo")
    assert "max-lg:overflow-y-auto" in fila, (
        "la fila de contenido apilada no se puede desplazar: el presupuesto, "
        "que queda el último, se corta y no hay manera de llegar a él")


# ─── 3. La botonera de la cabecera ─────────────────────────────────────────

def _botonera(fuente):
    return _region(fuente, "{/* Botones", "{/* Content")


def test_la_botonera_se_desliza_en_el_movil(fuente):
    b = _botonera(fuente)
    assert "max-lg:overflow-x-auto" in b, (
        "los nueve botones de la cabecera no caben en un móvil y ya no se "
        "pueden deslizar: GUARDAR, PDF y ENVIAR AL PRESUPUESTO quedan fuera")


def test_ningun_boton_de_la_cabecera_se_aplasta(fuente):
    b = _botonera(fuente)
    clases = [c for c in re.findall(r'className="([^"]*)"', b)
              if "px-4 py-2 rounded-lg font-bold text-sm" in c]
    assert len(clases) >= 8, (
        f"solo se han encontrado {len(clases)} botones en la cabecera; si se "
        "han reescrito, hay que revisar este candado, no borrarlo")
    sin_tope = [c for c in clases if "shrink-0" not in c]
    assert not sin_tope, (
        "hay botones de cabecera sin `shrink-0`: dentro de la tira deslizante "
        f"se encogen hasta no leerse. Ejemplo: {sin_tope[0][:80]}")


# ─── 4. Los accesorios se ponen con el dedo ────────────────────────────────

def test_colocar_accesorio_es_una_funcion_aparte(fuente):
    assert "const colocarAccesorio = (moduleIndex)" in fuente, (
        "ha desaparecido `colocarAccesorio`: si la lógica vuelve a vivir dentro "
        "del `handleDrop`, el camino del dedo se queda sin ella")


def test_el_arrastre_y_el_dedo_acaban_en_la_misma_funcion(fuente):
    drop = _region(fuente, "const handleDrop = (e, moduleIndex)", "const tocarModulo")
    assert "colocarAccesorio(moduleIndex)" in drop, (
        "el arrastre de ratón ya no pasa por `colocarAccesorio`: se acaba "
        "arreglando un camino y dejando el otro a medias")
    assert "setModuleConfigs" not in drop, (
        "el `handleDrop` ha vuelto a tener su propia copia de la lógica; dos "
        "copias es exactamente como se desincronizan el ratón y el dedo")


def test_tocar_un_modulo_coloca_el_accesorio_armado(fuente):
    assert "onClick={() => tocarModulo(i)}" in fuente, (
        "el módulo del armario ya no pasa por `tocarModulo`: con el dedo se "
        "vuelve a seleccionar el módulo y el accesorio no se coloca nunca")
    assert "onClick={() => setSelectedModule(i)}" not in fuente, (
        "ha vuelto el `onClick` de antes, que solo seleccionaba el módulo")


def test_tocar_modulo_distingue_los_dos_casos(fuente):
    f = _region(fuente, "const tocarModulo = (moduleIndex)", "// ========== PLANTILLAS")
    assert "colocarAccesorio(moduleIndex)" in f, (
        "tocar el módulo con un accesorio armado ya no lo coloca")
    assert "setSelectedModule(moduleIndex)" in f, (
        "tocar el módulo SIN accesorio armado ya no lo selecciona; se ha "
        "arreglado el móvil rompiendo lo que funcionaba")


def test_el_accesorio_se_arma_con_un_toque(fuente):
    paleta = _region(fuente, "{DRAGGABLE_ACCESSORIES.map((acc)", "))}")
    assert "onClick=" in paleta, (
        "el accesorio de la paleta solo responde a arrastre; en una pantalla "
        "táctil eso no existe y el panel entero vuelve a estar muerto")
    assert "setDraggedAccessory" in paleta, (
        "el toque en el accesorio no lo deja armado, así que el toque "
        "siguiente en el módulo no sabe qué colocar")


# ─── 5. El dibujo cabe en la pantalla y no se deforma ──────────────────────

def test_el_dibujo_del_armario_tiene_tope_de_alto(fuente):
    marco = _region(fuente, 'className="relative w-full', "{/* Pared de fondo")
    assert "vh]" in marco, (
        "el marco del armario ya no tiene tope de alto: con el móvil girado "
        "sale más alto que la pantalla entera y hay que desplazarse para verlo")


def test_el_dibujo_del_armario_no_se_deforma(fuente):
    marco = _region(fuente, 'className="relative w-full', "{/* Pared de fondo")
    assert "aspect-[4/3]" in marco, (
        "se ha quitado la proporción fija del marco. El armario se dibuja en "
        "porcentajes de ese marco: si el marco se estira, el armario sale "
        "achatado, y eso es enseñarle al cliente un armario que no es el suyo")


# ─── 6. Los modales caben en la pantalla del móvil ─────────────────────────
#
# El master abrió RENDER con el móvil: los tres rótulos —«ESTILO DE
# HABITACIÓN», «CONFIGURACIÓN ACTUAL», «IMAGEN DE REFERENCIA»— salían pisados
# unos encima de otros, y el botón GENERAR no aparecía por ninguna parte. La
# caja iba centrada, sin tope de alto y con `overflow-hidden`: más alta que la
# pantalla, se cortaba por arriba Y por abajo. El modal decía «Pulsa Generar» y
# el botón estaba fuera de la pantalla.

def _modales(fuente):
    """Cada caja blanca de un modal, con su clase."""
    trozos = []
    marca = 'className="fixed inset-0 bg-black/70'
    i = fuente.find(marca)
    while i != -1:
        j = fuente.find('className="bg-white rounded-3xl', i)
        if j == -1:
            break
        fin = fuente.find('"', j + len('className="'))
        trozos.append(fuente[j + len('className="'):fin])
        i = fuente.find(marca, j)
    return trozos


def test_ningun_modal_se_sale_de_la_pantalla(fuente):
    cajas = _modales(fuente)
    assert len(cajas) >= 5, (
        f"solo se han encontrado {len(cajas)} modales; si se han reescrito hay "
        "que revisar este candado, no borrarlo")
    sin_tope = [c for c in cajas if "max-h-[" not in c]
    assert not sin_tope, (
        "hay modales sin tope de alto. Centrados y sin tope se cortan por "
        f"arriba y por abajo, y el botón de abajo no se puede pulsar: {sin_tope}")


def test_un_modal_con_tope_tiene_que_poder_desplazarse(fuente):
    """Un tope de alto sin desplazamiento no enseña lo de abajo: lo esconde."""
    cajas = _modales(fuente)
    mudos = [c for c in cajas
             if "max-h-[" in c and "overflow-y-auto" not in c and "flex-col" not in c]
    assert not mudos, (
        "modal con tope de alto que ni se desplaza ni reparte el alto entre "
        f"cabecera/contenido/pie: lo que sobra se pierde. {mudos}")


def test_el_modal_de_render_no_apila_tres_columnas_en_el_movil(fuente):
    bloque = _region(fuente, "{/* Configuración del render", "{/* Toggle por puerta")
    assert "grid-cols-1 sm:grid-cols-3" in bloque, (
        "los tres rótulos vuelven a ir en tres columnas sobre 390 px: "
        "«CONFIGURACIÓN ACTUAL» e «IMAGEN DE REFERENCIA» se salen de su "
        "columna y se pisan")


def test_el_boton_de_generar_queda_dentro(fuente):
    """El pie del modal de render no puede quedarse fuera de la caja.

    Se busca HACIA ATRÁS desde el texto que solo tiene este pie. Buscando hacia
    delante desde «{/* Footer */}» se cogía el pie de OTRO modal —el primero del
    fichero— y la prueba pasaba en verde con este roto: comprobado quitándole el
    `shrink-0` a este pie y viendo que no se enteraba.
    """
    i = fuente.find("Generado con IA • Los renders son aproximaciones visuales")
    assert i != -1, "ha desaparecido el pie del modal de render"
    apertura = fuente.rfind('<div className="bg-slate-50', 0, i)
    assert apertura != -1, "no se encuentra la apertura del pie del modal de render"
    clase = fuente[apertura:fuente.find('"', apertura + len('<div className="'))]
    assert "shrink-0" in clase, (
        "el pie del modal de render puede encogerse hasta desaparecer; ahí "
        f"está el botón GENERAR, que es a lo que se entra. Clase: {clase}")


def test_el_area_del_render_no_empuja_el_boton_fuera(fuente):
    assert "min-h-[220px] sm:min-h-[400px]" in fuente, (
        "el hueco del render vuelve a pedir 400 px de alto en un móvil: entre "
        "la cabecera y ese hueco, el botón de abajo se va de la pantalla")


# ─── 7. El precio privado no se enseña ─────────────────────────────────────
#
# «No debe verse el precio privado con el descuento.» El importe ya se tapaba
# con «•••» hasta pulsar el ojo, pero el rótulo iba diciendo «Precio
# distribución (−45%)» a la vista de todos. Con ese porcentaje y el PVP, que sí
# se ve, el neto de distribución se saca de cabeza: era un candado con la llave
# puesta al lado. Un cliente sentado enfrente de la pantalla no tiene que saber
# a cuánto compra la distribución.

def test_el_descuento_solo_se_ve_con_el_precio_destapado(fuente):
    i = fuente.find("Precio distribución")
    assert i != -1, "ha desaparecido la línea del precio de distribución"
    linea = fuente[fuente.rfind("<span", 0, i):fuente.find("</span>", i)]
    assert "showCost &&" in linea, (
        "el porcentaje de descuento se pinta siempre; tapar el importe y "
        f"enseñar el −45% no tapa nada. Línea: {linea.strip()[:160]}")


def test_el_importe_sigue_tapado_hasta_pulsar(fuente):
    """Lo que ya estaba bien no se rompe al arreglar lo de al lado."""
    assert "{showCost ? `${pricing.distNetTotal.toFixed(2)} €` : '•••'}" in fuente, (
        "el importe del precio de distribución ha dejado de taparse")


def test_el_precio_privado_sigue_bajo_permiso(fuente):
    assert "const canSeeCost = state?.currentUser?.isAdmin === true" in fuente, (
        "quien puede ver el precio de distribución ya no depende del permiso "
        "del usuario")


# ─── 8. Los botones del pie del render caben en el móvil ───────────────────
#
# «Cuando pido el render de todas las puertas en móvil no se ven los botones.»
# El pie tiene CUATRO: DESCARGAR, CERRAR, GENERAR TODAS LAS PUERTAS y GENERAR
# RENDER, en una fila que no se envolvía. Los dos primeros se comían el ancho y
# los otros dos salían cortados por la derecha — entre ellos, justamente el que
# él quería pulsar.

def _pie_del_render(fuente):
    """La botonera del pie del modal de render, por su texto propio."""
    i = fuente.find("Generado con IA • Los renders son aproximaciones visuales")
    assert i != -1, "ha desaparecido el pie del modal de render"
    j = fuente.find("</div>\n          </div>", i)
    return fuente[i:j if j != -1 else i + 4000]


def test_los_botones_del_pie_se_envuelven(fuente):
    pie = _pie_del_render(fuente)
    grupo = pie[pie.find('<div className="'):pie.find('>', pie.find('<div className="'))]
    assert "flex-wrap" in grupo, (
        "los cuatro botones del pie vuelven a ir en una fila que no se "
        f"envuelve: los últimos se salen de la pantalla. Grupo: {grupo}")


def test_cada_boton_del_pie_ocupa_media_fila(fuente):
    pie = _pie_del_render(fuente)
    clases = [c for c in re.findall(r'className="([^"]*)"', pie)
              if "py-2.5 rounded-xl font-bold text-xs uppercase" in c]
    assert len(clases) >= 4, (
        f"se esperaban 4 botones en el pie del render y hay {len(clases)}; si "
        "han cambiado, hay que revisar este candado, no borrarlo")
    sin_ancho = [c for c in clases if "max-sm:basis-" not in c]
    assert not sin_ancho, (
        "hay botones del pie sin ancho de móvil: sin él se reparten a lo ancho "
        f"y el texto largo se sale. Ejemplo: {sin_ancho[0][:90]}")


def test_el_texto_de_los_botones_no_se_estira_en_el_movil(fuente):
    """«GENERAR TODAS LAS PUERTAS» con letra espaciada no cabe en media fila."""
    pie = _pie_del_render(fuente)
    clases = [c for c in re.findall(r'className="([^"]*)"', pie)
              if "py-2.5 rounded-xl font-bold text-xs uppercase" in c]
    sin_compactar = [c for c in clases if "max-sm:tracking-normal" not in c]
    assert not sin_compactar, (
        "el espaciado ancho de letra se mantiene en el móvil; «GENERAR TODAS "
        f"LAS PUERTAS» sale en cuatro líneas. Ejemplo: {sin_compactar[0][:90]}")
