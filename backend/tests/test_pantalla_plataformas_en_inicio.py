# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
PLATAFORMAS: LOS TRES NEGOCIOS, EN LA PUERTA DE ENTRADA.

El master, 30/08: «cada una aporta un negocio distinto y quiero estructurarlo
como tal», y sobre el nombre: «PLATAFORMAS».

Se llama igual que el código (`services/plataformas.py`, `plataformas.js`), y no
«Proyectos»: en este ERP un proyecto es una OBRA —la colección `projects`, el
Expediente, «Referencia / Obra»—, así que esa palabra ya significa otra cosa.
Dos significados para una palabra es justo lo que acabamos de arreglar con
«Cocinas por módulos», que en los permisos se llamaba «Estudio 3D» y por eso no
se podía encontrar.

LO QUE VIGILA ESTE CANDADO, que es lo único que puede costar dinero aquí:

  1. Que juntarlas en el mapa NO les junte la puerta. El master, en la misma
     conversación: «no deben compartir puerta». COOP reparte comisiones y cierra
     el mes; carpinter.io y Studio3K venden suscripciones y —27/08— «no tienen
     nada que ver con el negocio de los cooperativistas».
  2. Que carpinter.io y Studio3K sean SOLO DEL MASTER (30/08: «la puerta de
     carpinter y studio3k, sólo la veo yo»).
  3. Que el cierre esté también en el ENRUTADO, no solo en el menú: esconder un
     botón no cierra ninguna puerta (regla 8).
"""
import os

import permisos_de_pestana as P
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INICIO = os.path.join(RAIZ, "frontend", "src", "components", "WelcomeScreen.jsx")
APP = os.path.join(RAIZ, "frontend", "src", "App.js")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _entrada(tab):
    """La línea del menú de inicio de esa sección."""
    for linea in _lee(INICIO).split("\n"):
        if re.search(r"\{\s*tab:\s*'%s'" % re.escape(tab), linea):
            return linea
    raise AssertionError(f"no hay entrada de menú para «{tab}»")


def test_EL_GRUPO_SE_LLAMA_PLATAFORMAS_Y_NO_PROYECTOS():
    cuerpo = _lee(INICIO)
    assert "id: 'plataformas'" in cuerpo, "no existe el grupo de plataformas"
    assert "label: 'Plataformas'" in cuerpo
    assert "label: 'Proyectos'" not in cuerpo, (
        "el grupo se llama «Proyectos», y en este ERP un proyecto es una OBRA: "
        "la palabra ya significa otra cosa")


def test_LAS_TRES_PLATAFORMAS_ESTAN_Y_SON_LAS_DEL_CODIGO():
    """Las mismas tres de `services/plataformas.py`: cooperativa, carpinter,
    studio3k. Si el menú y el código dijeran negocios distintos, el mapa
    mentiría."""
    for tab in ("coop", "carpinter", "landingStudio"):
        assert "group: 'plataformas'" in _entrada(tab), (
            f"«{tab}» no está en el grupo de plataformas")


def test_CARPINTER_Y_STUDIO3K_SON_SOLO_DEL_MASTER():
    """Master, 30/08: «la puerta de carpinter y studio3k, sólo la veo yo»."""
    for tab in ("carpinter", "landingStudio"):
        linea = _entrada(tab)
        assert "isMaster" in linea and "isPrimaryAdmin" in linea, (
            f"«{tab}» no está cerrado al master")
        for ancho in ("isAdmin", "isGerente", "isDirectorComercial",
                      "isRepresentative", "canAccess"):
            assert ancho not in linea, (
                f"«{tab}» se ha abierto a «{ancho}»: es un negocio del master")


def test_NO_COMPARTEN_PUERTA():
    """Estar en el mismo grupo no puede dar el permiso de al lado.

    COOP la abre también un administrador (es la gestión de la red de siempre);
    carpinter.io y Studio3K, no. Si los tres botones tuvieran la misma
    condición, agrupar habría cambiado quién entra — y mover cosas de sitio no
    puede cambiar permisos.
    """
    coop = _entrada("coop")
    assert "isAdmin" in coop, (
        "COOP ha dejado de abrirse a un administrador: agrupar no puede "
        "estrechar de paso lo que ya funcionaba")
    assert "isAdmin" not in _entrada("carpinter"), (
        "carpinter.io y COOP han acabado con la misma puerta")


def test_EL_CIERRE_ESTA_TAMBIEN_EN_EL_ENRUTADO():
    """Esconder el botón no cierra nada: basta con escribir la pestaña a mano.

    Es la regla 8 del proyecto, y aquí importa porque `landingStudio` no tenía
    NINGUNA comprobación: se pintaba con solo llegar a esa pestaña.
    """
    cuerpo = _lee(APP)
    for tab in ("carpinter", "landingStudio"):
        # Que la pestaña siga ENRUTADA: `landingStudio` no tenía ninguna
        # comprobación y se pintaba con solo llegar, y `carpinter` ni siquiera
        # existía en el enrutado — el botón se habría quedado en blanco.
        assert f"state.currentTab === '{tab}'" in cuerpo, (
            f"la pestaña «{tab}» ha desaparecido del enrutado: su botón lleva a "
            f"una pantalla en blanco")

    # Y QUIÉN ENTRA, ejecutando la regla en vez de buscar su texto. El master,
    # 30/08: «la puerta de carpinter y studio3k, sólo la veo yo».
    abre = P.puertas({
        "master": P.MASTER,
        "admin": P.ADMIN,
        "gerente": P.GERENTE,
        "suscriptor": P.SUSCRIPTOR,
    }, ["carpinter", "landingStudio"])
    assert sorted(abre["master"]) == ["carpinter", "landingStudio"], (
        "el master ha perdido la puerta de sus otras dos plataformas")
    for quien in ("admin", "gerente", "suscriptor"):
        assert abre[quien] == [], (
            f"«{quien}» entra en carpinter.io o Studio3K escribiendo la pestaña "
            f"a mano: son negocios que solo mira el master, y esconder el botón "
            f"no cierra nada")


def test_LA_PUERTA_DE_CARPINTER_LLEVA_A_ALGUN_SITIO():
    """Una pantalla a la que se llega y no existe es peor que no tener botón.

    `carpinter` no estaba en el enrutado: el panel solo se abría solo, para el
    admin de la división. El botón nuevo se habría quedado en blanco.
    """
    cuerpo = _lee(APP)
    i = cuerpo.index("state.currentTab === 'carpinter'")
    assert "<CarpinterPanel" in cuerpo[i:i + 700], (
        "el botón de carpinter.io no pinta nada")


def test_LAS_PLATAFORMAS_VAN_LAS_ULTIMAS():
    """El master, 30/08: «las plataformas ponlas abajo del todo».

    No es un capricho de colocación: es el mapa de los tres negocios, no el
    trabajo del día. Quien entra a currar busca el Presupuestador, y tenerlo
    debajo de tres puertas que casi nadie abre es un clic de más cada mañana.

    Se comprueba el ORDEN DE `GROUPS`, que es lo que decide en qué orden se
    pintan los bloques. Mirar solo que el grupo exista no habría notado nada
    cuando estaba el primero.
    """
    cuerpo = _lee(INICIO)
    i = cuerpo.index("const GROUPS = [")
    bloque = cuerpo[i:cuerpo.index("];", i)]
    ids = re.findall(r"\{\s*id:\s*'([a-zA-Z0-9]+)'", bloque)
    assert ids, "no se han podido leer los grupos de la pantalla de inicio"
    assert ids[-1] == "plataformas", (
        f"«plataformas» ya no va la última: el orden es {ids}")
