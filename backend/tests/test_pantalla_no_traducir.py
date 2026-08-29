# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL ERP ES ESPAÑOL Y NO SE TRADUCE. LAS DOS COSAS, Y LAS DOS SON DINERO.

`index.html` decía `<html lang="en">` con el ERP entero escrito en castellano.
En un Chrome de móvil en español, con «traducir siempre las páginas en inglés»
activado —que es lo que tiene medio mundo—, Chrome se cree la etiqueta y traduce
la página SOLO, sin preguntar. Y para traducir reescribe todos los nodos de
texto metiéndolos en `<font>`: le cambia el DOM a React por debajo.

La siguiente vez que React va a mover algo, el nodo ya no está donde lo dejó:

    NotFoundError: Failed to execute 'insertBefore' on 'Node'

y eso no rompe una pantalla, tumba la aplicación ENTERA. Pasa en el móvil y no
en el portátil porque en el portátil Chrome pregunta antes de traducir.

Y AUNQUE NO TUMBARA NADA, TRADUCIR ESTE ERP SERÍA UN DESTROZO. Por estas
pantallas pasan códigos de mueble (`B60D/I`, `ASC60`, `CMCB`), medidas y euros.
Un traductor automático se los lleva por delante —«BAJO» no es una palabra que
traducir, es una familia de la tarifa MV— y nadie se entera de que el número que
está mirando ya no es el que puso el ERP.

Por eso van las tres marcas, que se refuerzan entre ellas:
  · `lang="es"`   — lo que la página ES. Además es lo que leen los lectores de
                    pantalla, así que estaba mal por dos motivos.
  · `translate="no"` en el `<html>` — el estándar.
  · `<meta name="google" content="notranslate">` — lo que de verdad respeta
    Chrome, que es el navegador del master.
"""
import os
import re

INDEX = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend", "public", "index.html")


def _html():
    with open(INDEX, "r", encoding="utf-8") as f:
        return f.read()


def _etiqueta_html(texto):
    """La etiqueta `<html ...>` de verdad, no la que aparezca en un comentario."""
    sin_comentarios = re.sub(r"<!--.*?-->", "", texto, flags=re.S)
    m = re.search(r"<html\b[^>]*>", sin_comentarios)
    assert m, "no está la etiqueta <html> en index.html"
    return m.group(0)


def test_la_pagina_se_declara_EN_ESPANOL():
    etiqueta = _etiqueta_html(_html())
    assert re.search(r'lang\s*=\s*"es"', etiqueta), (
        f"el `<html>` no se declara en español: {etiqueta!r}. Con `lang=\"en\"` "
        "Chrome traduce el ERP solo en un móvil configurado en español, "
        "reescribe el DOM por debajo de React y la aplicación se cae entera con "
        "un `insertBefore`.")


def test_NADIE_TRADUCE_este_ERP():
    texto = _html()
    etiqueta = _etiqueta_html(texto)
    assert re.search(r'translate\s*=\s*"no"', etiqueta), (
        "falta `translate=\"no\"` en el `<html>`: aquí se ven códigos de mueble, "
        "medidas y euros, y un traductor automático se los lleva por delante")
    sin_comentarios = re.sub(r"<!--.*?-->", "", texto, flags=re.S)
    assert re.search(r'<meta\s+name="google"\s+content="notranslate"', sin_comentarios), (
        "falta `<meta name=\"google\" content=\"notranslate\">`. Es la marca que "
        "de verdad respeta Chrome, que es el navegador desde el que se usa esto")


def test_el_RECONOCEDOR_no_se_traga_un_comentario():
    """Este fichero explica el fallo en un comentario de HTML, y ahí dentro
    aparece un `lang="en"` de ejemplo. Si la prueba mirase el texto en crudo, ese
    ejemplo la engañaría en las dos direcciones."""
    falso = '<!doctype html>\n<!-- antes ponía <html lang="en"> -->\n<html lang="en">\n'
    assert _etiqueta_html(falso) == '<html lang="en">'
    bueno = '<!doctype html>\n<!-- antes ponía <html lang="en"> -->\n<html lang="es" translate="no">\n'
    assert _etiqueta_html(bueno) == '<html lang="es" translate="no">'
