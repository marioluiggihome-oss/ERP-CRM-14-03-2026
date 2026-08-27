# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
AL AÑADIR UN MUEBLE NO SE ENSEÑA UN HUECO.

El master, dos veces: «cuando meto un mueble tarda un poco, como un segundo, y
se queda la pantalla en blanco; da mala imagen al meterlo en la barra de
búsqueda».

QUÉ ERA, DESPUÉS DE DESCARTAR DOS COSAS QUE NO ERAN:

  · No era el guardia antimanipulación. `securityGuard.js` tiene un
    `detectDevTools()` que BORRA la página entera con `document.body.innerHTML`
    si la ventana exterior y la interior se diferencian en más de 160 px —lo que
    en una tablet pasaría al salir el teclado—, pero está COMENTADO en el
    arranque. No se ejecuta.
  · No era una excepción al pintar. Hay `ErrorBoundary` en `index.js` y en
    `App.js`, y pintan el error con la pila de componentes: un fallo se ve, no
    deja blanco.

Era un HUECO. `añadirTexto` va al servidor y tarda cerca de un segundo. En ese
rato la pantalla entera decía «No hay muebles añadidos en este presupuesto» —un
vacío del tamaño del monitor— con un girito de 18 px dentro del buscador que en
una tablet de 8,6" no se ve. Fotografiado a mitad de la espera con el servidor
ralentizado a propósito (`e2e/blanco-al-buscar.spec.js`).

No estaba rota: estaba enseñando el mensaje de «esto está vacío» justo cuando
acababas de pedirle que lo llenara.
"""
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSX = os.path.join(RAIZ, "frontend", "src", "components", "CocinaMontada3.jsx")


def _lee():
    with open(JSX, "r", encoding="utf-8") as f:
        return f.read()


def test_mientras_busca_NO_sale_el_mensaje_de_vacio():
    cuerpo = _lee()
    i = cuerpo.index("{buscando && filasFiltradas.length === 0 ?")
    # El ELEMENTO, no el comentario. El comentario que explica este arreglo
    # contiene el mismo texto, y buscándolo a secas la prueba se cazaba a sí
    # misma: la explicación de por qué ya no pasa parecía el fallo.
    j = cuerpo.index('<p className="text-base font-bold text-dato-600">'
                     'No hay muebles añadidos')
    assert i < j, (
        "el mensaje de «no hay muebles» vuelve a salir antes que el aviso de "
        "que se está buscando: la pantalla enseñaría el vacío justo mientras "
        "espera al servidor")


def test_la_espera_DICE_QUE_ESTA_BUSCANDO():
    cuerpo = _lee()
    assert "Buscando {busca.trim()" in cuerpo, (
        "la espera ya no dice qué se está buscando")
    assert 'aria-live="polite"' in cuerpo, (
        "la espera no se anuncia: quien use lector de pantalla no se entera de "
        "que hay algo en marcha")
    assert "animate-pulse" in cuerpo, "no hay nada que se mueva durante la espera"


def test_el_BOTON_tambien_lo_dice():
    """El girito del buscador son 18 px. En una tablet de 8,6" no se ve, y el
    master estaba mirando el botón que acababa de pulsar."""
    cuerpo = _lee()
    i = cuerpo.index("Añadir Mueble")
    trozo = cuerpo[max(0, i - 400):i + 60]
    assert "Añadiendo…" in trozo, (
        "el botón no cambia mientras se añade: se queda igual y parece que no "
        "ha pasado nada")
