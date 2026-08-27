# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Interruptor MEDIDAS del Estudio 3D: quién dibuja las cotas.

El master pidió (24/08/2026) «un botón para que se quiten y se pongan las
medidas» sobre el render. La tentación evidente era pedírselo a la IA: «pon las
cotas en esta foto». Eso es exactamente lo que prohíbe la regla de oro del
proyecto — un modelo de imagen no sabe escribir medidas, escribe números
plausibles — y era además el origen del problema que lo motivó: cuando entraba
un croquis con medidas escritas, el render las copiaba a mano alzada sobre la
encimera, con cifras que ya no correspondían a nada.

Así que el botón alterna entre DOS imágenes distintas: el render (la foto) y el
alzado alámbrico acotado, que dibuja el motor vectorial del backend desde la
distribución real. Estas pruebas son el candado de esa decisión: si alguien
reconvierte el interruptor en una llamada a la IA, o deja que el alzado de una
cocina se enseñe encima del render de otra, el CI se pone rojo.
"""
import os
import re

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ESTUDIO_3D = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")


def _fuente():
    with open(ESTUDIO_3D, encoding="utf-8") as f:
        return f.read()


def _cuerpo_de(nombre, fuente=None):
    """El cuerpo de una función flecha del componente, hasta su cierre.

    Las funciones del componente están a dos espacios de sangría y cierran con
    `\n  };`, así que el recorte no depende de dónde esté la función en el
    fichero: el día que se mueva, la prueba la sigue encontrando.
    """
    fuente = fuente or _fuente()
    ini = fuente.index(f"const {nombre} =")
    fin = fuente.index("\n  };", ini)
    return fuente[ini:fin]


def test_el_boton_existe_y_llama_al_interruptor():
    fuente = _fuente()
    assert "const alternarMedidas" in fuente, \
        "ha desaparecido el interruptor de medidas del Estudio 3D"
    assert "onClick={alternarMedidas}" in fuente, \
        "el botón de poner/quitar medidas ya no está enganchado a alternarMedidas"
    assert "Poner medidas" in fuente and "Quitar medidas" in fuente, \
        "el botón ya no dice en qué estado está: un interruptor mudo no se entiende"


def test_las_cotas_las_dibuja_el_backend_vectorial_y_no_la_ia():
    """CANDADO (regla de oro): ni una cota pintada por un modelo de imagen.

    El interruptor tiene que sacar el alzado del motor vectorial —el mismo que
    valida la geometría antes de dibujar— y no de ninguna de las vías de render.
    """
    cuerpo = _cuerpo_de("alternarMedidas")
    assert "generarVistaAlambrica(true" in cuerpo, \
        "el interruptor ya no pide el alzado vectorial acotado"
    for prohibido in ("handleGenerateComposed", "handleGenerateNatural",
                      "handleGenerateParams", "/api/ai/", "motor"):
        assert prohibido not in cuerpo, (
            f"el interruptor de medidas ha pasado por «{prohibido}»: eso es "
            "pedirle a la IA que escriba las cotas sobre la foto, que es "
            "justo lo que este candado impide.")


def test_volver_a_la_foto_devuelve_EL_MISMO_render_y_no_lo_regenera():
    """Un interruptor que regenera la foto no es un interruptor: es otro render
    (otros muebles, otros créditos y otra espera)."""
    cuerpo = _cuerpo_de("alternarMedidas")
    assert "setRenderResult(fotoGuardada.current)" in cuerpo, \
        "al quitar las medidas ya no se recupera el render guardado"
    # La foto se guarda ANTES de generar el alzado: si se guardase después, lo
    # que se guardaría es el propio alzado y no habría vuelta atrás.
    # `rindex`: hay dos guardados (la vía rápida, con el alzado ya en memoria, y
    # la que lo genera). El que importa es el de la vía que genera, el último.
    guardado = cuerpo.rindex("fotoGuardada.current = actual")
    generado = cuerpo.index("generarVistaAlambrica(true")
    assert guardado < generado, \
        "se guarda la foto DESPUÉS de generar el alzado: se pierde el render"


def test_un_render_nuevo_tira_el_alzado_guardado():
    """CANDADO: las medidas de la cocina de antes NO se enseñan sobre la de
    ahora. Sería una cota inventada con todas las letras."""
    fuente = _fuente()
    efectos = re.findall(r"useEffect\(\(\) => \{(.*?)\}, \[renderResult\]\);", fuente, re.S)
    assert efectos, "ya no hay nada que reaccione a un render nuevo"
    limpia = [e for e in efectos if "alzadoGuardado.current = null" in e]
    assert limpia, (
        "un render nuevo ya no invalida el alzado guardado: el botón enseñaría "
        "las medidas del diseño anterior sobre el nuevo.")
    assert "setVistaConCotas(false)" in limpia[0], \
        "el interruptor se queda encendido con un render que no tiene alzado"


def test_el_alzado_del_interruptor_no_se_cuela_en_el_historial():
    """El historial es de renders. Si cada vez que se miran las medidas entra
    una lámina, en tres clics el historial deja de servir para nada."""
    cuerpo = _cuerpo_de("generarVistaAlambrica")
    assert "opciones.silencioso" in cuerpo, \
        "generarVistaAlambrica ya no distingue la llamada del interruptor"
    historial = cuerpo.index("setRenderHistory")
    guarda = cuerpo.index("if (!opciones.silencioso)")
    assert guarda < historial, \
        "el alzado del interruptor vuelve a entrar en el historial de renders"
    assert "return lamina;" in cuerpo, \
        "generarVistaAlambrica ya no devuelve la lámina: el interruptor no puede guardarla"
