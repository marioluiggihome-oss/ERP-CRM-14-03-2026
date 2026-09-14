# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL BOTÓN DE PANTALLA COMPLETA EXPANDE LA PANTALLA, NO EL RENDER.

El master, 25/08/2026: «el botón de pantalla arriba a la derecha al lado de los
créditos lo quiero para que expanda la pantalla completa, no para expandir el
render. El render ya tiene su propio botón».

Y lo tiene: el «Visor interactivo (zoom + pan)», que está en esa misma barra.

QUÉ PASABA. Había DOS botones llamados «Pantalla completa» a la vez en la misma
pantalla, haciendo cosas distintas:

  · el del carril de la izquierda  -> pantalla completa del navegador, el ERP entero
  · el de la barra del render      -> una capa negra con la foto dentro

Y encima se pisaban: cerrar la capa del render llamaba a `exitFullscreen`, así
que te sacaba de la pantalla completa del navegador aunque hubieras entrado con
el otro botón y no hubieras pedido salir.

QUÉ SE HIZO. El del Estudio 3D pasa a ser EL MISMO COMPONENTE que el del carril
(`BotonPantallaCompleta`). Una sola implementación, un solo nombre y un solo
efecto. La capa negra y su estado se borraron enteros.

Esta prueba vigila que no vuelva la capa. Es de PANTALLA (lee el JSX): no hay
manera de montar React aquí, pero un borrado accidental o un «lo dejo otra vez
como estaba» se cazan igual, y en un segundo.
"""
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ESTUDIO = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")
BOTON = os.path.join(RAIZ, "frontend", "src", "components", "BotonPantallaCompleta.jsx")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def test_el_estudio_usa_el_boton_compartido_de_pantalla_completa():
    """El Estudio 3D no tiene su propia pantalla completa: usa la de todos."""
    cuerpo = _lee(ESTUDIO)
    assert "import BotonPantallaCompleta from './BotonPantallaCompleta'" in cuerpo, (
        "el Estudio 3D ya no importa `BotonPantallaCompleta`. Si se ha vuelto a "
        "escribir una pantalla completa propia, vuelven los dos botones con el "
        "mismo nombre y distinto efecto que pidió quitar el master el 25/08.")
    assert "<BotonPantallaCompleta" in cuerpo, (
        "el botón compartido ya no se pinta en la barra del render")


def test_no_vuelve_la_capa_negra_que_expandia_el_render():
    """LO QUE SE PROHIBIÓ EL 25/08 NO ERA LA CAPA: ERA LA CONFUSIÓN.

    Esta prueba prohibía CUALQUIER capa a pantalla completa en el Estudio 3D.
    El 14/09/2026 el master pidió lo contrario: «podemos poner un botón de ver
    a tope de tamaño el dibujo renderizado, ocupando toda la pantalla». No es
    que se arrepintiera de lo del 25/08 — lo que molestaba entonces era otra
    cosa, y está escrito en la petición original: «lo quiero para que expanda
    la pantalla completa, NO para expandir el render; el render ya tiene su
    propio botón». Había DOS botones llamados «Pantalla completa» haciendo
    cosas distintas, y cerrar la capa te sacaba del modo pantalla completa del
    navegador aunque hubieras entrado con el otro.

    O sea que el daño real eran esas dos cosas, no la capa. Se vigilan ellas:
    el botón viejo no vuelve, y el nuevo ni se llama igual ni toca el modo
    pantalla completa del navegador. Lo demás está en
    `test_pantalla_candado_gasto_ia_y_ampliar.py`.

    Prohibir la capa a secas habría obligado a borrar esta prueba para darle al
    master lo que pide — y borrar un candado para ponerlo verde es exactamente
    lo que este repo no hace.
    """
    cuerpo = _lee(ESTUDIO)
    for rastro in ("showFullscreen", "entrarEnPantallaCompleta", "salirDePantallaCompleta"):
        assert rastro not in cuerpo, (
            f"ha vuelto `{rastro}`: ese era el botón que se llamaba «Pantalla "
            "completa» y expandía el RENDER, al lado del que expande la "
            "pantalla. Para ampliar el dibujo está «Ampliar».")
    # La capa nueva SÍ puede existir, pero no puede llamarse como la otra ni
    # tocar el modo pantalla completa del navegador: mezclarlos fue el fallo.
    if 'data-testid="dibujo-ampliado"' in cuerpo:
        i = cuerpo.index('data-testid="btn-ampliar-dibujo"')
        boton = cuerpo[i - 500:i + 600]
        assert "Pantalla completa" not in boton, (
            "vuelve a haber dos botones «Pantalla completa» haciendo cosas "
            "distintas en la misma barra")
        j = cuerpo.index("setDibujoAmpliado(true)")
        assert "requestFullscreen" not in cuerpo[j - 300:j + 300], (
            "ampliar el dibujo vuelve a tocar la pantalla completa del "
            "navegador: cerrar la capa sacaría del modo pantalla completa a "
            "quien hubiera entrado con el otro botón")
    else:
        assert "z-[9999]" not in cuerpo, (
            "hay una capa a pantalla completa nueva en el Estudio 3D que no es "
            "la de «Ampliar»: si es a propósito, hay que decir aquí qué es")


def test_el_render_conserva_su_propio_boton_de_ampliar():
    """Quitar la capa NO puede dejar el render sin forma de verse en grande.

    Es la otra mitad de la petición del master: «el render ya tiene su propio
    botón». Si algún día se borra el visor interactivo, esta prueba avisa de que
    el render se ha quedado sin lupa — y entonces quitar la capa sí sería una
    pérdida.
    """
    cuerpo = _lee(ESTUDIO)
    assert "setInteractiveMode" in cuerpo, "no queda visor interactivo"
    assert "Visor interactivo (zoom + pan)" in cuerpo, (
        "el visor interactivo ya no se ofrece con ese nombre: el render se ha "
        "quedado sin manera de ampliarse")


def test_el_boton_compartido_deja_poner_el_rotulo_de_cada_sitio():
    """Vive en dos sitios con tipografías distintas y tiene que caber en los dos."""
    cuerpo = _lee(BOTON)
    assert "claseTexto" in cuerpo and "textos" in cuerpo, (
        "`BotonPantallaCompleta` ha vuelto a llevar el rótulo escrito a fuego. "
        "En el carril va a 7 px en mayúsculas y en la barra del render a 11 px: "
        "con uno solo, en el Estudio 3D salía «Pantalla» en microscópico.")
    # Y el del Estudio 3D tiene que pedir el rótulo largo, que es el que se lee.
    estudio = _lee(ESTUDIO)
    trozo = estudio[estudio.index("<BotonPantallaCompleta"):]
    trozo = trozo[:trozo.index("/>") + 2]
    assert "Pantalla completa" in trozo, (
        "el botón del Estudio 3D ya no dice «Pantalla completa»")


# La palabra «Créditos» en el móvil la vigila
# `test_pantalla_estudio3d_movil.py::test_los_creditos_van_cortos_en_movil`, que
# es de quien era esa regla desde el principio (allí se guarda además el motivo
# de que no pueda volver la coletilla «restantes»). Dos candados sobre lo mismo
# acaban separándose, y entonces uno de los dos miente.
