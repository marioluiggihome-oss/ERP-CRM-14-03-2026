# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
COOP ES LA PLATAFORMA DE LA COOPERATIVA, NO EL PANEL DEL MASTER.

El master, 30/08: «todas esas herramientas de gestión que cuelguen dentro del
área de COOP, no fuera» y «Mi área debería estar dentro de COOP».

LO QUE VIGILA ESTE CANDADO, y es UNA cosa por encima de todas: QUE NADIE PIERDA
ACCESO POR LA MUDANZA. Meter «Mi área» dentro de un COOP que era solo del master
le habría quitado su área al cooperativista — que es literalmente el apagón del
28/08, cuando estrechar una lista dejó al dueño fuera de su propia tarifa. Por
eso la puerta se abre al socio y lo que se recorta son las PESTAÑAS.

Y LOS PERMISOS NO CAMBIAN POR MUDARSE (regla 22, la del Presupuestador): la
facturación sigue pidiendo lo que pedía y la agenda de montajes también. Si de
paso se movieran los permisos, nadie sabría si un usuario dejó de ver algo por
el rediseño o porque se lo quitamos.
"""
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

PANEL = os.path.join(RAIZ, "frontend", "src", "components", "CoopPanel.jsx")
APP = os.path.join(RAIZ, "frontend", "src", "App.js")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _pestanas():
    """Los ids y su condición, sacados de la lista real."""
    cuerpo = _lee(PANEL)
    i = cuerpo.index("const PESTANAS = [")
    bloque = cuerpo[i:cuerpo.index("\n];", i)]
    return bloque, re.findall(r"\{\s*id:\s*'([a-z]+)'", bloque)


def test_LAS_HERRAMIENTAS_DE_GESTION_CUELGAN_DE_COOP():
    _, ids = _pestanas()
    for necesaria in ("miarea", "montajes", "facturacion",
                      "usuarios", "socios", "produccion", "liquidar"):
        assert necesaria in ids, (
            f"«{necesaria}» ya no cuelga de COOP: el master pidió que la gestión "
            "estuviera dentro, no fuera")


def test_MI_AREA_VA_LA_PRIMERA():
    """Es quien más veces entra, y entra a una sola cosa."""
    _, ids = _pestanas()
    assert ids[0] == "miarea", f"el orden de las pestañas es {ids}"


def test_LA_PUERTA_SE_ABRE_AL_SOCIO_O_LE_QUITAMOS_SU_AREA():
    """LO MÁS IMPORTANTE DE ESTE FICHERO.

    Si COOP siguiera siendo solo del master, meter «Mi área» dentro dejaría al
    cooperativista sin ella — y sin un error: simplemente no vería el botón.
    """
    cuerpo = _lee(APP)
    # DONDE SE PINTA, no el primer «'coop'» del fichero — que es la clase CSS
    # del botón del menú. Una ventana anclada a bulto ya dejó pasar un fallo
    # dos veces en este proyecto.
    i = cuerpo.index("['coop', 'miArea']")
    trozo = cuerpo[i:i + 500]
    assert "esCooperativista(state.currentUser)" in trozo, (
        "la puerta de COOP no se abre al cooperativista: acaba de perder «Mi "
        "área», que es lo único suyo que hay en el ERP")


def test_CADA_PESTANA_DICE_QUIEN_LA_VE():
    """Entrar en COOP no puede dar acceso a todo lo de dentro."""
    bloque, ids = _pestanas()
    assert bloque.count("ve:") == len(ids), (
        "hay pestañas sin condición de quién las ve: un socio entraría a "
        "Liquidar el mes")
    # Las del dinero de la casa, cerradas al master y a nadie más.
    for solo_master in ("usuarios", "socios", "produccion", "liquidar"):
        i = bloque.index(f"id: '{solo_master}'")
        assert "ve: esMaster" in bloque[i:i + 220], (
            f"«{solo_master}» se le está enseñando a quien no es master")


def test_LOS_PERMISOS_NO_CAMBIAN_POR_MUDARSE():
    """Regla 22: mover pantallas de sitio no puede cambiar quién entra."""
    bloque, _ = _pestanas()
    i = bloque.index("id: 'montajes'")
    assert "canAccessMontajes" in bloque[i:i + 320], (
        "la agenda de montajes ha perdido su permiso al mudarse")
    j = bloque.index("id: 'facturacion'")
    assert "canAccessInvoices" in bloque[j:j + 320], (
        "la facturación ha perdido su permiso al mudarse")


def test_EL_CAMINO_VIEJO_DE_MI_AREA_SIGUE_VIVO():
    """Hay enlaces y estado de navegador con ese nombre (regla 22)."""
    cuerpo = _lee(APP)
    assert "'miArea'" in cuerpo, (
        "`miArea` ha desaparecido del enrutado: los enlaces que ya existen "
        "llevarían a una pantalla en blanco")
    i = cuerpo.index("['coop', 'miArea']")
    assert "pestanaInicial" in cuerpo[i:i + 700], (
        "entrar por `miArea` no abre la pestaña de Mi área")


def test_MI_AREA_YA_NO_TIENE_BOTON_FUERA():
    """El master: «no fuera»."""
    cuerpo = _lee(APP)
    assert "currentTab: 'miArea'" not in cuerpo, (
        "«Mi área» sigue teniendo su propio botón en el menú lateral")


def test_LA_LISTA_DEL_MASTER_NO_SE_HA_ENSANCHADO_AQUI():
    """`isAdmin` no decide qué pestañas de dinero se ven (regla 8c)."""
    cuerpo = _lee(PANEL)
    i = cuerpo.index("const esMaster =")
    assert "isAdmin" not in cuerpo[i:i + 200], (
        "COOP ha vuelto a mirar `isAdmin` para las pestañas del dinero")
