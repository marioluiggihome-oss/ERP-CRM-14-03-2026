# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
UNA IMAGEN QUE NO ESTÁ NO DA ERROR: DEJA UN HUECO EN LA PÁGINA PÚBLICA.

El master, 11/09/2026, pidió el logotipo en alta resolución. El que había era
un PNG de 1578 × 363 px: en una pantalla Retina el navegador lo estira al
doble y el borde de las letras se ve blando; para imprimir no vale. Se
vectorizó y la landing pasó a usar el SVG.

EL RIESGO DE ESTE CAMBIO no es que se vea mal: es que la ruta del fichero y el
fichero viven en dos sitios distintos. `Studio3kLanding.jsx` escribe
`src="/studio3k-logo-white.svg"` y el fichero está en `frontend/public/`. Si
alguien lo renombra, lo mueve o lo borra, **el build sigue en verde**: React no
comprueba las rutas de `public/`, así que la única señal es un recuadro vacío
donde iba la marca, en la página que ven los clientes. Y nadie mira la landing
todos los días.

Se comprueban TODAS las imágenes de esa pantalla, no solo el logo: el fallo es
del tipo de ruta, no de este fichero en concreto.

Y de paso la PROPORCIÓN: el hueco del CSS es fijo (148 × 34) y el SVG trae la
suya dentro. Si se separan, `object-fit: contain` deja el logo pequeño y
descentrado en su caja en vez de dar un error.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsx_limpio import sin_comentarios  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANDING = os.path.join(RAIZ, "frontend", "src", "components", "Studio3kLanding.jsx")
PUBLIC = os.path.join(RAIZ, "frontend", "public")
LOGO = os.path.join(PUBLIC, "studio3k-logo-white.svg")

AZUL = "#4A6AFD"


def _cuerpo():
    with open(LANDING, "r", encoding="utf-8") as f:
        crudo = f.read()
    limpio = sin_comentarios(crudo)
    # El recorte de comentarios no puede haberse comido el código.
    assert "s3k-logo-link" in limpio
    assert "s3k-footer-logo" in limpio
    return limpio


def test_TODAS_LAS_IMAGENES_DE_LA_LANDING_EXISTEN_DE_VERDAD():
    """El build no lo comprueba: una ruta mal escrita deja un hueco blanco en
    la página pública y el CI en verde."""
    cuerpo = _cuerpo()
    rutas = set(re.findall(r'["\'\(](/[A-Za-z0-9_\-./]+\.(?:svg|png|jpe?g|webp|mp4|gif))["\'\)]', cuerpo))
    assert rutas, "la landing ya no referencia ninguna imagen: ¿se ha movido el marcado?"
    faltan = [r for r in sorted(rutas) if not os.path.isfile(os.path.join(PUBLIC, r.lstrip("/")))]
    assert not faltan, (
        "la landing pide ficheros que no están en frontend/public/: %s. "
        "El navegador no da error, deja el hueco vacío." % faltan)


def test_EL_LOGOTIPO_DE_LA_CABECERA_Y_EL_DEL_PIE_SON_EL_MISMO():
    """Dos rutas distintas para la misma marca acaban separándose: se cambia
    una y el pie se queda con el logo viejo."""
    cuerpo = _cuerpo()
    usados = re.findall(r'src="(/studio3k-logo[^"]+)"', cuerpo)
    assert len(usados) >= 2, "faltan usos del logotipo en la landing: %s" % usados
    assert len(set(usados)) == 1, (
        "la cabecera y el pie usan logotipos distintos: %s" % sorted(set(usados)))


def test_LA_LANDING_USA_EL_VECTOR_Y_NO_EL_PNG():
    """Volver al PNG no rompe nada — solo se ve borroso en pantallas buenas y
    pesa ocho veces más en la página que carga primero un cliente."""
    cuerpo = _cuerpo()
    assert 'src="/studio3k-logo-white.svg"' in cuerpo
    assert "studio3k-logo-white.png" not in cuerpo, (
        "la landing ha vuelto al logotipo en PNG")


def test_EL_SVG_DEL_LOGO_ES_UN_SVG_VALIDO_Y_LLEVA_LOS_DOS_COLORES():
    """Un SVG roto tampoco da error: el navegador no pinta nada. Y si se
    perdiera una de las dos capas, saldría «studio k» sin el 3, o el 3 solo."""
    raiz = ET.parse(LOGO).getroot()          # revienta si el XML está mal
    assert raiz.tag.endswith("svg")
    fuente = open(LOGO, "r", encoding="utf-8").read()
    rellenos = {f.upper() for f in re.findall(r'fill="(#[0-9A-Fa-f]{6})"', fuente)}
    assert AZUL in rellenos, (
        "el 3 azul de la marca (%s) no está en el logotipo: %s" % (AZUL, sorted(rellenos)))
    assert "#FFFFFF" in rellenos, (
        "las letras blancas no están en el logotipo: %s" % sorted(rellenos))
    # Dos capas: si alguien fusionara los caminos, el 3 dejaría de ser azul.
    assert fuente.count("<path") >= 2


def test_LA_PROPORCION_DEL_SVG_CUADRA_CON_EL_HUECO_DEL_CSS():
    """El CSS reserva una caja fija. Si el vector trae otra proporción,
    `object-fit: contain` lo encoge dentro de su hueco y queda descentrado —
    sin dar ningún error."""
    fuente = open(LOGO, "r", encoding="utf-8").read()
    w = float(re.search(r'\bwidth="([0-9.]+)"', fuente).group(1))
    h = float(re.search(r'\bheight="([0-9.]+)"', fuente).group(1))
    cuerpo = _cuerpo()
    css = re.search(r"\.s3k-logo-img\s*\{([^}]*)\}", cuerpo)
    assert css, "ya no existe la regla .s3k-logo-img"
    cw = float(re.search(r"width:\s*([0-9.]+)px", css.group(1)).group(1))
    ch = float(re.search(r"height:\s*([0-9.]+)px", css.group(1)).group(1))
    assert abs((w / h) - (cw / ch)) < 0.1, (
        "el logotipo es %.2f:1 y su hueco en el CSS es %.2f:1" % (w / h, cw / ch))
