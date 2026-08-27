# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""IA 4 APAGADA (24/08/2026, a petición del master). Y por qué no era un motor.

La IA 4 se anunciaba en pantalla como «Gemini Flash — rápido». No lo era. En
`_render_dispatch` hacía:

    model_override="gemini-2.5-flash-image"

que es EXACTAMENTE el modelo que la IA 1 usa por defecto (está escrito en
CLAUDE.md, regla 10). Mismo modelo, mismo encargo, misma imagen y el mismo
tiempo. Un botón que el master pulsaba creyendo que cambiaba de motor, igual
que pasó con la IA 2 — solo que la IA 2 al menos hacía algo distinto (y por eso
se apagó: tardaba cinco minutos).

Lo que NO se hace, igual que con la IA 2: borrar el camino. Hay proyectos
guardados con `motor: 'ia4'` y al abrirlos tienen que seguir dando el render de
siempre. Lo que se quita es el botón: lo que no puede seguir es ofrecerle al
master una elección que no elige nada.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PANTALLA = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")
DESPACHO = os.path.join(RAIZ, "backend", "services", "luiggi_ai", "render_3d.py")


def _pantalla():
    with open(PANTALLA, encoding="utf-8") as f:
        return f.read()


def test_la_ia4_ya_no_se_ofrece_en_pantalla():
    """CANDADO: el botón no vuelve solo."""
    pantalla = _pantalla()
    assert "'IA 4'" not in pantalla, \
        "la IA 4 ha vuelto a la pantalla: se apagó el 24/08 a petición del master"
    assert "Gemini Flash — rápido" not in pantalla, (
        "vuelve la etiqueta que prometía una velocidad que no existe: la IA 4 "
        "usaba el MISMO modelo que la IA 1.")


def test_los_proyectos_guardados_con_ia4_siguen_abriendo():
    """Apagar no es romper: quien guardó un proyecto con IA 4 tiene que poder
    abrirlo y que le salga el render de siempre."""
    pantalla = _pantalla()
    assert "if (motor === 'ia4') return 'gemini_flash';" in pantalla, \
        "se ha borrado la correspondencia de 'ia4': los proyectos guardados con ese motor se quedan sin motor"


def test_la_razon_de_apagarla_sigue_siendo_cierta():
    """Si algún día la IA 4 pasa a usar un modelo DISTINTO al de la IA 1, deja
    de ser un duplicado y esta prueba avisa de que hay que revisar la decisión."""
    with open(DESPACHO, encoding="utf-8") as f:
        codigo = f.read()
    i = codigo.index('if provider == "gemini_flash"')
    bloque = codigo[i:i + 500]
    modelo = re.search(r'model_override="([^"]+)"', bloque)
    assert modelo, "el despacho de gemini_flash ya no fija un modelo"
    assert modelo.group(1) == "gemini-2.5-flash-image", (
        f"gemini_flash usa ahora «{modelo.group(1)}», que ya NO es el modelo de "
        "la IA 1: deja de ser un duplicado y hay que decidir de nuevo si se "
        "vuelve a ofrecer en pantalla. Habla con el master.")
