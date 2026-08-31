# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
UN CANDADO QUE NO SE ABRE NO PROTEGE NADA: ESTÁ ROTO.

El master, 30/08: «al tocar el candado no veo los costes como antes». No los veía
porque el candado del Presupuestador NO ABRÍA DE NINGUNA MANERA — ni con
pulsación larga ni con Shift+clic, ni en tablet ni en ordenador.

TRES FALLOS A LA VEZ, y ninguno daba un error:

  1. Se esparcía `{...handlersCandado}` en el `<button>`, y el hook NO devuelve
     handlers: devuelve `{ props, consumir }`. Al botón le llegaban dos
     atributos llamados `props` y `consumir` —que no son nada— y NI UN GESTO.
  2. No había `onClick`, así que Shift+clic tampoco hacía nada.
  3. El segundo argumento del hook era una función y el hook espera `{ ms }`:
     la pista de cómo abrirlo no se enseñaba nunca.

El botón se veía perfectamente, se podía pulsar, y no pasaba nada. Es la peor
forma de esconder algo: parece roto, y encima nadie sabe si está protegido o
averiado.

POR QUÉ ESTE CANDADO BARRE TODAS LAS PANTALLAS. El fallo es de una sola letra
—`.props`— y el build no lo ve, ESLint no lo ve y ninguna otra prueba lo ve. La
única forma de que no vuelva es comprobarlo en todas las que usan el gesto.
"""
import os
import re

from jsx_limpio import sin_comentarios as _limpia_jsx

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMPONENTES = os.path.join(RAIZ, "frontend", "src", "components")
HOOK = os.path.join(RAIZ, "frontend", "src", "utils", "pulsacionLarga.js")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _sin_comentarios(cuerpo: str) -> str:
    """El código, sin los comentarios.

    HACE FALTA, y ya es la TERCERA vez en este proyecto: los ficheros EXPLICAN
    el fallo citándolo —aquí `{...handlersCandado}`, en el candado de traducir
    un `lang="en"` de ejemplo, en el de COOP la palabra `isAdmin`— y el
    reconocedor se creía la explicación. Un candado que caza su propia
    documentación acusa al código que acaba de arreglarse.
    """
    return _limpia_jsx(cuerpo)


def _pantallas_con_candado():
    """Las pantallas que usan la pulsación larga, y su código SIN comentarios."""
    fuera = []
    for nombre in sorted(os.listdir(COMPONENTES)):
        if not nombre.endswith(".jsx"):
            continue
        cuerpo = _lee(os.path.join(COMPONENTES, nombre))
        if "usePulsacionLarga(" in cuerpo:
            fuera.append((nombre, _sin_comentarios(cuerpo)))
    return fuera


def test_HAY_PANTALLAS_QUE_LO_USAN():
    """Si esto da cero, el barrido de abajo no comprueba nada y el CI queda en
    verde por vacío — que es como un candado deja de existir sin avisar."""
    assert len(_pantallas_con_candado()) >= 3, (
        "el reconocedor no encuentra las pantallas con candado: la prueba de "
        "abajo estaría pasando sin mirar nada")


def test_EL_HOOK_DEVUELVE_props_Y_HAY_QUE_ESPARCIR_ESO():
    """Se deja escrito lo que devuelve, porque de ahí nace el fallo."""
    hook = _lee(HOOK)
    assert "props: {" in hook and "consumir:" in hook, (
        "ha cambiado lo que devuelve el hook; esta prueba hay que rehacerla")


def test_NINGUNA_PANTALLA_ESPARCE_EL_HOOK_ENTERO():
    """`{...candado}` en vez de `{...candado.props}` deja el botón sin gestos.

    No se busca un nombre concreto de variable: se saca el que use cada
    pantalla, para que renombrarla no despiste al candado.
    """
    for nombre, cuerpo in _pantallas_con_candado():
        for var in set(re.findall(r"const (\w+) = usePulsacionLarga\(", cuerpo)):
            assert f"{{...{var}}}" not in cuerpo, (
                f"{nombre}: se esparce `{{...{var}}}` en vez de "
                f"`{{...{var}.props}}` — el botón se queda SIN los gestos y el "
                "candado no abre de ninguna manera")
            assert f"{{...{var}.props}}" in cuerpo, (
                f"{nombre}: `{var}` no se esparce en ningún botón: el gesto no "
                "está enganchado a nada")


def test_AL_HOOK_NO_SE_LE_PASA_UNA_FUNCION_DE_SEGUNDO_ARGUMENTO():
    """El segundo argumento son OPCIONES (`{ ms }`), no una segunda acción.

    Pasarle una función no rompe nada visible —se lee `ms` de un objeto que no
    lo tiene y se coge el defecto—, así que se queda ahí para siempre haciendo
    creer que hay un aviso que nunca se enseña.
    """
    # NO SE BUSCA HASTA EL PRIMER `);`: el propio callback lleva uno dentro
    # (`setPistaCandado('');`) y el patrón se cortaba ahí, así que el segundo
    # argumento quedaba fuera de la ventana y la prueba no mordía. Se probó
    # rompiéndolo. Ahora se mira un trozo fijo desde la llamada.
    for nombre, cuerpo in _pantallas_con_candado():
        for m in re.finditer(r"usePulsacionLarga\(", cuerpo):
            trozo = cuerpo[m.end():m.end() + 500]
            assert "}, () =>" not in trozo and "}, function" not in trozo, (
                f"{nombre}: se le pasa una función como segundo argumento del "
                "hook, y ahí van las OPCIONES (`{ ms }`): ese callback no se "
                "llama nunca, y quien lo escribió cree que sí")


def test_EL_CANDADO_DEL_PRESUPUESTADOR_ABRE_DE_LAS_DOS_FORMAS():
    """Pulsación larga para tablet, Shift+clic para quien ya lo tiene en los
    dedos. Y un toque corto no abre, pero DICE cómo se abre."""
    cuerpo = _lee(os.path.join(COMPONENTES, "CocinaMontada3.jsx"))
    i = cuerpo.index('data-testid="cm3-candado-coste"')
    boton = cuerpo[max(0, i - 1200):i]
    assert "handlersCandado.props" in boton, "no se enganchan los gestos"
    assert "handlersCandado.consumir()" in boton, (
        "el clic que manda el navegador al soltar deshará lo que abrió la "
        "pulsación larga: el usuario ve un parpadeo y nada más")
    assert "e.shiftKey" in boton, "Shift+clic no abre el candado"
    assert "AYUDA_CANDADO" in boton, (
        "un toque corto no dice cómo se abre: el botón parece roto")
