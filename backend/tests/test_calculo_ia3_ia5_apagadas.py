# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""IA 3 e IA 5 APAGADAS (09/09/2026, a petición del master: «quita IA3 e IA5»).

Ninguna de las dos era un motor distinto: las dos pintaban con el MISMO modelo
de imagen que la IA 1 (`gemini-2.5-flash-image`). Lo que cambiaba era el
ENCARGO.

  · IA 3 (`gemini_premium`) — Gemini con un prefijo de prompt
    ultra-fotorrealista por delante.
  · IA 5 (`julio`) — el encargo del 22/07/2026, puesto para comparar los dos
    caminos con el mismo croquis en vez de discutirlo. Comparado y visto.

SE APAGA EL BOTÓN, NO EL CAMINO. Es la misma decisión que se tomó con la IA 2
(18/08) y la IA 4 (24/08), y por el mismo motivo: hay proyectos guardados con
`motor: 'ia3'` y con `motor: 'ia5'`, y al abrirlos tienen que seguir dando el
render que dieron. Si se borrara la correspondencia de `providerOf()`, esos
proyectos NO darían un error: caerían al motor por defecto y devolverían una
imagen distinta a la guardada, sin que nada lo dijera. Eso es exactamente lo
que pasó el 03/08 y por lo que existe el candado de motores.

QUEDAN EN PIE, ENTONCES, DOS COSAS QUE HAY QUE VIGILAR A LA VEZ:
  1. Que el botón no vuelva solo.
  2. Que la correspondencia siga estando.
Una prueba que solo mirase la primera dejaría pasar el borrado del camino, que
es el daño de verdad.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PANTALLA = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")
DESPACHO = os.path.join(RAIZ, "backend", "services", "luiggi_ai", "render_3d.py")


def _pantalla():
    with open(PANTALLA, encoding="utf-8") as f:
        return f.read()


def _botonera():
    """El bloque de botones de motor, que es el único sitio que importa.

    Se recorta a propósito: 'IA3' y 'IA5' aparecen también en comentarios que
    EXPLICAN por qué están apagadas, y un candado que mirase el fichero entero
    se pondría rojo por su propia explicación."""
    fuente = _pantalla()
    inicio = fuente.index("{isMaster && (", fuente.index("Acción principal"))
    fin = fuente.index("</div>\n                )}", inicio)
    return fuente[inicio:fin]


def test_ia3_e_ia5_ya_no_se_ofrecen_en_pantalla():
    """CANDADO: los botones no vuelven solos."""
    botonera = _botonera()
    for perfil in ("IA3", "IA5"):
        assert f"'{perfil}'" not in botonera, (
            f"{perfil} ha vuelto a la botonera del Estudio 3D: se apagó el "
            f"09/09/2026 a petición del master («quita IA3 e IA5»)")
    for ident in ("'ia3'", "'ia5'"):
        assert ident not in botonera, (
            f"{ident} ha vuelto a la lista de botones de motor")


def test_los_botones_que_quedan_son_exactamente_tres():
    """Lo que se apaga se nota; lo que se enciende, también.

    Sin este recuento, apagar IA 3 e IA 5 y encender de vuelta IA 2 o IA 4 en
    el mismo sitio dejaría el candado de arriba en verde."""
    botonera = _botonera()
    perfiles = re.findall(r"\['(ia\d)', '(IA\d)'", botonera)
    assert [p[0] for p in perfiles] == ["ia0", "ia1", "ia7"], (
        f"la botonera de motores ofrece ahora {[p[1] for p in perfiles]} y "
        f"debe ofrecer IA0, IA1 e IA7. Si el master ha pedido otro reparto, "
        f"actualiza CLAUDE.md (regla 1) y este fichero.")


def test_los_proyectos_guardados_con_ia3_o_ia5_siguen_abriendo():
    """Apagar no es romper.

    Y ojo con lo que NO daría un error: sin estas dos líneas, un proyecto
    guardado con IA 3 o IA 5 cae al `return 'gemini'` del final y devuelve una
    imagen — otra imagen, con otro encargo, sin decir nada."""
    pantalla = _pantalla()
    assert "if (motor === 'ia3') return 'gemini_premium';" in pantalla, (
        "se ha borrado la correspondencia de 'ia3': los proyectos guardados "
        "con ese motor renderizarían con otro encargo sin avisar")
    assert "if (motor === 'ia5') return 'julio';" in pantalla, (
        "se ha borrado la correspondencia de 'ia5': los proyectos guardados "
        "con ese motor renderizarían con otro encargo sin avisar")


def test_el_camino_de_ia3_sigue_existiendo_en_el_servidor():
    """La pantalla puede seguir mandando `gemini_premium` desde un proyecto
    guardado: el repartidor tiene que saber qué hacer con él."""
    with open(DESPACHO, encoding="utf-8") as f:
        codigo = f.read()
    assert 'if provider == "gemini_premium"' in codigo, (
        "el repartidor ya no reconoce 'gemini_premium': un proyecto guardado "
        "con IA 3 caería al motor por defecto sin dar error")


def test_la_razon_de_apagarlas_sigue_siendo_cierta():
    """Se apagaron porque NO cambian de modelo, solo de encargo.

    Si algún día IA 3 pasara a fijar un `model_override` propio, dejaría de ser
    el caso y habría que volver a decidir si se ofrece. Esta prueba avisa."""
    with open(DESPACHO, encoding="utf-8") as f:
        codigo = f.read()
    i = codigo.index('if provider == "gemini_premium"')
    bloque = codigo[i:i + 500]
    assert "model_override" not in bloque, (
        "IA 3 fija ahora un modelo de imagen propio: ya no es 'el mismo motor "
        "con otro encargo' y hay que decidir de nuevo si se ofrece en "
        "pantalla. Habla con el master.")
    assert "_PREMIUM_PROMPT_PREFIX" in bloque, (
        "IA 3 ya no es Gemini con el prefijo premium: ha cambiado de "
        "naturaleza y la decisión de apagarla se tomó sobre la anterior")
