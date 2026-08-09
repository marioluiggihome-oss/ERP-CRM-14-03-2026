# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del logo flotante: QUE NO TAPE LA CABECERA DE NINGUN MODULO.

EL FALLO
--------
Con el menu lateral plegado, la aplicacion pinta el logo —que ademas es el boton
de abrir el menu— en `fixed top-3 left-3` con z-[60]. Ocupa los 60 primeros
pixeles de la esquina superior izquierda de la PANTALLA, por encima de todo lo
que haya debajo. Y debajo hay, en casi todos los modulos, el titulo.

Se veia el icono a medias y el titulo empezado por la mitad.

POR QUE NO SE CAZO ANTES
------------------------
Porque el parche que habia era `ml-14 sm:ml-2`: dejar hueco SOLO en pantalla
estrecha. Pero el boton no aparece por ser un movil, aparece por estar el menu
plegado — y en un ordenador con el menu plegado seguia tapando exactamente igual.
La regla buena es una sola y no habla de anchos:

    EL HUECO EXISTE EXACTAMENTE CUANDO EXISTE EL BOTON.

Eso es lo que se protege aqui:

1. La clase `menu-plegado` se pone con la MISMA condicion que pinta el boton. Si
   se separan, o sobra un hueco de 60 px sin boton, o vuelve a taparse el titulo.

2. Cada modulo de la lista deja el hueco. La lista se escribe A MANO: asi,
   aniadir una pantalla nueva es una decision («¿tiene cabecera arriba a la
   izquierda?») y no un olvido.

3. Nadie vuelve al truco por anchos. `ml-14 sm:ml-2` es el fallo original con
   otro nombre.
"""
import os
import re

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(RAIZ, "frontend", "src")
APP = os.path.join(SRC, "App.js")
CSS = os.path.join(SRC, "index.css")

# Los modulos que TIENEN cabecera pegada al borde de arriba a la izquierda y por
# tanto necesitan el hueco. Revisados uno a uno el 09/08 abriendo cada pestania.
#
# No estan aqui —y es a proposito— los que llevan la cabecera CENTRADA y no
# llegan nunca a la esquina: BackupManager (bloque centrado) y LuiggiFloor (logo
# de marca centrado). Si algun dia se les pone un titulo a la izquierda, entran.
CON_HUECO = [
    "PropData.jsx", "Cascos.jsx", "Armarios2.jsx", "CocinasIA.jsx",
    "Expediente.jsx", "Almacen.jsx", "CommandCenter.jsx", "ResumenCocinas.jsx",
    "KitchenDesigner3D.jsx", "RentabilidadPanel.jsx", "GestionGastos.jsx",
    "Invoices.jsx", "Visualizer.jsx", "ProjectLibrary.jsx",
    "AgentesDisenadores.jsx", "MisPedidos.jsx", "ReportGenerator.jsx",
    "CRMLayout.jsx", "WelcomeScreen.jsx", "Digitalizador.jsx", "Armarios.jsx",
    "EstudioCocinas.jsx", "Presupuestador2.jsx", "PrescriptorAgenda.jsx",
    "PortalFabrica.jsx", "AgendaMontajes.jsx", "BudgetTable.jsx",
    "AIRenderStudio.jsx",
]


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


# ─── 1. El hueco existe exactamente cuando existe el boton ──────────────────

def test_el_boton_flotante_solo_se_pinta_con_el_menu_plegado():
    """La premisa de todo lo demas. Si el boton pasara a verse siempre, los
    huecos condicionados dejarian de cuadrar."""
    app = _leer(APP)
    i = app.index('data-testid="sidebar-toggle"')
    trozo = app[max(0, i - 900):i]
    assert "{!sidebarOpen && (" in trozo, (
        "el boton flotante del logo ya no depende de `!sidebarOpen`: revisa el "
        "hueco de las cabeceras, porque estaba atado a esa condicion")
    assert "fixed top-3 left-3" in trozo, (
        "el boton flotante ha cambiado de sitio: el hueco de 3.75rem por la "
        "izquierda puede haber dejado de ser el correcto")


def test_la_clase_menu_plegado_va_en_la_misma_condicion_que_el_boton():
    """CANDADO PRINCIPAL. Van juntas o no valen: un hueco sin boton es un
    titulo descolocado, y un boton sin hueco es el fallo de siempre."""
    app = _leer(APP)
    i = app.index("<main className=")
    linea = app[i:app.index("\n", i)]
    assert "menu-plegado" in linea, (
        "el <main> ha perdido la clase `menu-plegado`: las cabeceras dejan de "
        "hacerle hueco al logo y vuelve a taparlas")
    # Tiene que ir en la rama de MENU PLEGADO del ternario, no suelta.
    m = re.search(r"\$\{!sidebarOpen \? '([^']*)'", linea)
    assert m and "menu-plegado" in m.group(1), (
        "`menu-plegado` no esta en la rama `!sidebarOpen`: o esta siempre "
        "puesta (hueco de 60 px sin boton que lo ocupe) o esta al reves")


def test_la_regla_del_hueco_esta_definida_en_el_css():
    css = _leer(CSS)
    assert ".menu-plegado .hueco-logo" in css, (
        "falta la regla: las clases `hueco-logo` de los modulos no harian nada "
        "y nadie se enteraria, porque una clase que no existe no da error")
    assert ".menu-plegado .hueco-logo-centrado" in css
    # El hueco tiene que tapar el boton entero: 12 px de margen + 48 de boton.
    m = re.search(r"\.menu-plegado \.hueco-logo \{ padding-left: ([\d.]+)rem", css)
    assert m and float(m.group(1)) * 16 >= 60, (
        "el hueco se ha quedado corto: el boton ocupa hasta el pixel 60 "
        "(12 de margen + 48 de ancho) y el titulo volveria a empezar debajo")


# ─── 2. Cada modulo con cabecera deja su hueco ──────────────────────────────

@pytest.mark.parametrize("fichero", CON_HUECO)
def test_el_modulo_le_deja_hueco_al_logo(fichero):
    """CANDADO. Uno a uno, porque el fallo era justo ese: se arreglaba en la
    pantalla que se estaba mirando y las otras veinte seguian igual."""
    src = _leer(os.path.join(SRC, "components", fichero))
    assert "hueco-logo" in src, (
        f"{fichero} no deja hueco al logo flotante: con el menu plegado, el "
        "logo se le come el icono y el principio del titulo")


def test_ningun_modulo_vuelve_al_truco_de_los_anchos():
    """`ml-14 sm:ml-2` es el fallo original: hueco solo en movil. En un
    ordenador con el menu plegado el logo tapaba igual."""
    malos = []
    for raiz, _, ficheros in os.walk(os.path.join(SRC, "components")):
        for f in ficheros:
            if not f.endswith(".jsx"):
                continue
            src = _leer(os.path.join(raiz, f))
            if "ml-14 sm:ml-2" in src:
                malos.append(f)
    assert not malos, (
        "vuelven a dejar el hueco por ancho de pantalla en: " + ", ".join(malos)
        + ". El boton depende del menu, no del ancho.")
