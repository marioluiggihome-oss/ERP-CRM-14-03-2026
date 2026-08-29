# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
PRESUPUESTADOR: LAS DOS FORMAS DE PRESUPUESTAR UNA COCINA, EN UNA SOLA PUERTA.

El master, 28/08: juntar Cocina Montada 3 y Cocina Desmontada en una sección
llamada «Presupuestador», donde «el máster vería todo, pero el resto de usuarios
la pestaña de Cocina Desmontada la verían dependiendo de si está activo o no ese
permiso».

LO QUE VIGILA ESTE CANDADO, Y VIENE DE UN SUSTO DE ESE MISMO DÍA: que un cambio
de NAVEGACIÓN no cambie quién ENTRA. Unas horas antes, apretar la lista del
master dejó al propio master sin ver los precios de su tarifa y toda la relación
salió a 0,00 € — sin un solo error. Mover pantallas de sitio se parece
demasiado a eso: si de paso se movieran los permisos, nadie sabría si un usuario
dejó de ver algo por el rediseño o porque se lo quitamos.

Por eso aquí se comprueban tres cosas:

  1. Que los permisos son los MISMOS de antes, no unos nuevos.
  2. Que los caminos de siempre —«Cocina Montada 3» y «Cocina Desmontada»—
     siguen llevando a su pestaña. Una pantalla a la que se llegaba y ya no se
     llega es una pantalla que se ha perdido.
  3. Que no se desmonta la pestaña que no se ve, o cambiar de pestaña vaciaría
     una relación a medio hacer.
"""
import json
import os
import re
import shutil
import subprocess

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JS = os.path.join(RAIZ, "frontend", "src", "presupuestador.js")
PANEL = os.path.join(RAIZ, "frontend", "src", "components", "PresupuestadorPanel.jsx")
APP = os.path.join(RAIZ, "frontend", "src", "App.js")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


# Los mismos usuarios de siempre, con los permisos tal y como estaban ANTES de
# juntar las dos pantallas.
USUARIOS = [
    ("master", {"isMaster": True}, True, True),
    # `isAdmin` YA NO ES MASTER (29/08). Entra en Cocina Montada porque ahí el
    # permiso es «no estar desactivado», y NO en Desmontada, que pide el suyo.
    ("admin sin marca de master", {"isAdmin": True}, True, False),
    ("admin principal", {"isPrimaryAdmin": True}, True, True),
    ("comercial con las dos", {"canUsePresupuestador3": True, "canUseCascos": True}, True, True),
    ("comercial solo montada", {"canUseCascos": False}, True, False),
    ("comercial sin permiso de montada", {"canUsePresupuestador3": False, "canUseCascos": True}, False, True),
    ("tienda con cascos", {"isTienda": True, "canUseCascos": True}, True, False),
    ("sin nada", {"canUsePresupuestador3": False}, False, False),
]


def test_los_PERMISOS_son_los_de_siempre():
    """Se ejecutan en node las funciones reales y se comparan usuario a usuario.

    Los permisos NO cambian al juntar las pantallas: `canUsePresupuestador3`
    para Montada (donde «no estar desactivado» ya era el criterio) y
    `canUseCascos` explícito para Desmontada, nunca para una tienda.
    """
    node = shutil.which("node")
    if not node:
        pytest.skip("no hay node en esta máquina")

    guion = _lee(JS).replace("export const", "const")
    casos = [u for _n, u, _a, _b in USUARIOS]
    guion += ("\nconst us = " + json.dumps(casos) + ";\n"
              "console.log(JSON.stringify(us.map((u) => "
              "[puedeMontada(u), puedeDesmontada(u), pestanasDe(u), "
              "puedeEntrar(u), hayQueEnseñarPestanas(u)])));\n")
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False, encoding="utf-8") as f:
        f.write(guion); ruta = f.name
    try:
        salida = subprocess.run([node, ruta], capture_output=True, text=True, timeout=60)
    finally:
        os.unlink(ruta)
    assert salida.returncode == 0, f"el módulo no corre: {salida.stderr.strip()}"
    res = json.loads(salida.stdout)

    for (nombre, _u, montada, desmontada), (m, d, pestanas, entra, barra) in zip(USUARIOS, res):
        assert m == montada, f"«{nombre}»: Cocina Montada debería ser {montada} y es {m}"
        assert d == desmontada, f"«{nombre}»: Cocina Desmontada debería ser {desmontada} y es {d}"
        assert entra == (montada or desmontada), (
            f"«{nombre}»: entra={entra} pero sus pestañas son {pestanas}")
        assert barra == (len(pestanas) > 1), (
            f"«{nombre}»: la barra de pestañas se enseña con {len(pestanas)} pestaña(s). "
            "Con una sola es ruido con aspecto de que falta algo.")


def test_una_TIENDA_no_ve_Cocina_Desmontada_ni_con_el_permiso():
    """Estaba así antes (`!isTienda && canUseCascos`) y tiene que seguir igual.

    Es el caso que más fácil se pierde al reescribir una condición: la tienda
    lleva el permiso puesto y aun así no entra.
    """
    cuerpo = _lee(JS)
    assert "isTienda" in cuerpo, (
        "se ha perdido el corte de la tienda: una tienda con `canUseCascos` "
        "vería Cocina Desmontada, y antes no la veía")


def test_los_CAMINOS_DE_SIEMPRE_siguen_llevando_a_su_pestaña():
    """Se entraba por «Cocina Montada 3» y por «Cocina Desmontada». Esos
    identificadores siguen vivos —en la bienvenida, en enlaces guardados, en el
    estado del navegador— y tienen que abrir su pestaña, no quedarse en blanco.
    """
    cuerpo = _lee(APP)
    assert "'cocinaMontada3'" in cuerpo and "'cascos'" in cuerpo, (
        "los identificadores de pestaña de siempre han desaparecido de App.js: "
        "quien entre por el camino viejo se queda sin pantalla")
    m = re.search(r"\['presupuestador', 'cocinaMontada3', 'cascos'\]\.includes\(state\.currentTab\)", cuerpo)
    assert m, "los tres caminos ya no llevan al Presupuestador"
    assert "PRE_DESMONTADA" in cuerpo and "PRE_MONTADA" in cuerpo, (
        "entrar por el camino viejo ya no abre la pestaña que toca")


def test_la_pestaña_QUE_NO_SE_VE_no_se_desmonta():
    """Si se desmontara, cambiar de pestaña vaciaría una relación a medio hacer
    —y en Cocina Montada 3 eso puede ser una cocina entera tecleada a mano."""
    cuerpo = _lee(PANEL)
    assert "hidden" in cuerpo, (
        "las pestañas se están desmontando en vez de ocultarse: al volver, lo "
        "que hubiera a medias se habrá perdido")
    assert "vistas" in cuerpo, (
        "ya no se recuerda qué pestañas se han abierto")


def test_la_SECCION_se_llama_PRESUPUESTADOR():
    """El nombre lo eligió el master. Si cambia, que sea a sabiendas."""
    assert "Presupuestador" in _lee(APP)
    assert "presupuestador-nav-btn" in _lee(APP), "no hay botón en la barra"
    bienvenida = _lee(os.path.join(RAIZ, "frontend", "src", "components", "WelcomeScreen.jsx"))
    assert "'presupuestador'" in bienvenida, (
        "el Presupuestador no está en la pantalla de bienvenida, que es por "
        "donde entra todo el mundo")
