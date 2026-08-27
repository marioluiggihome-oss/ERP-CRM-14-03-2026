# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: IA 7 compara MODELOS, no otra cosa. Y dice cuál ha pintado.

DE DÓNDE SALE
-------------
El master preguntó en qué se diferencia el ERP de abrir Google AI Studio con
Nano Banana Pro y darle el dibujo a mano. Se diferencia, entre otras cosas, en
el MODELO: el ERP renderiza con `gemini-2.5-flash-image` —Nano Banana normal—
y Pro es `gemini-3-pro-image`, otro modelo. Dijo: «ponlo en la IA 7 con banana
pro».

En `llm_vision.py` está escrita la decisión de no usarlo:

    «gemini-3-pro-image es más "creativo" e ignora el layout: se inventa la
     distribución del cliente»

Puede ser verdad. Pero es una frase en un comentario y no tiene ni una prueba
detrás, y con este ERP ya hemos visto lo que pasa cuando algo se da por sabido
sin comprobarlo. El botón la pone a prueba.

LO QUE SE PROTEGE, Y ES SUTIL
-----------------------------
1. QUE SOLO CAMBIE EL MODELO. IA 7 usa el MISMO encargo que IA 1 —el recorte
   del dibujo, la lectura a ficha y la lista numerada—. Si alguien le pone
   además otro prompt «para que luzca», las dos imágenes dejan de comparar el
   modelo y la conclusión que saque el master será falsa.

2. QUE SE SEPA QUIÉN HA PINTADO. La cascada de modelos existe para que un
   modelo retirado no deje al ERP sin renders, y está bien. Pero comparando
   motores es una trampa: se pide Pro, falla, pinta el pequeño, y sale una
   imagen con toda la pinta de ser la buena. Es el mismo fallo mudo que ya nos
   costó cuatro rondas con la lectura del plano. Ahora el modelo que ha pintado
   sube hasta la pantalla, y si no es el pedido se dice en naranja.

3. QUE NO SE PONGA DE MOTOR POR DEFECTO. Cuesta 0,12 $ por imagen frente a
   0,036 $ —tres veces y pico—. Se elige a sabiendas o no se elige.
"""
import os
import re

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(BACKEND)
RENDER = os.path.join(BACKEND, "services", "luiggi_ai", "render_3d.py")
VISION = os.path.join(BACKEND, "services", "llm_vision.py")
ESTUDIO = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def _codigo_jsx():
    return "\n".join(l.split("//")[0] for l in _leer(ESTUDIO).splitlines())


def _rama_ia7():
    src = _leer(RENDER)
    i = src.index('if provider == "banana_pro":')
    return src[i:src.index("\n        # IA 4", i)]


# ─── 1. IA 7 es un cambio de MODELO, y nada más ────────────────────────────

def test_ia7_pide_el_modelo_pro():
    """El nombre tecnico SI puede estar en el backend: lo que no puede es
    llegar a la pantalla del Estudio 3D."""
    rama = _rama_ia7()
    assert 'model_override="gemini-3-pro-image-preview"' in rama, (
        "IA 7 ya no pide el modelo Pro: el botón existirá pero renderizará con "
        "el mismo modelo que IA 1, y las dos imágenes serán la misma cosa")


def test_ia7_no_toca_el_encargo():
    """Si además del modelo se le cambia el prompt, lo que se ve en las dos
    imágenes ya no es el modelo, y la conclusión que se saque será falsa."""
    rama = _rama_ia7()
    assert "prompt_prefix" not in rama, (
        "IA 7 lleva un prefijo de prompt propio: deja de comparar modelos y "
        "pasa a comparar modelo+prompt, que no es lo que se preguntó")
    assert "task_prompt, prompt, parsed_params" in rama, \
        "IA 7 ya no manda el mismo encargo que IA 1"


def test_ia7_no_es_el_motor_por_defecto():
    """Tres veces y pico más caro por imagen. Se elige a sabiendas."""
    src = _leer(RENDER)
    i = src.index("provider = (provider or os.environ.get")
    assert '"gemini"' in src[i:i + 200], \
        "el motor por defecto ha cambiado: Banana Pro no puede entrar por la puerta de atrás"
    assert "banana_pro" not in src[i:i + 200], \
        "Banana Pro se ha colado como motor por defecto"


def test_el_boton_existe_y_apunta_a_pro():
    codigo = _codigo_jsx()
    assert "'ia7'" in codigo, "el botón de IA 7 ha desaparecido de la pantalla"
    i = codigo.index("if (motor === 'ia7')")
    assert "'banana_pro'" in codigo[i:i + 120], \
        "IA 7 apunta a otro motor: el botón se pintará pero rendirá con el de siempre"


# ─── 2. Que se sepa QUIÉN ha pintado la imagen ─────────────────────────────

def test_el_modelo_que_pinta_sube_hasta_arriba():
    """Sin esto, un Pro que falla devuelve una imagen del modelo pequeño y
    nadie se entera. Es el mismo fallo mudo de la lectura del plano."""
    vision = _leer(VISION)
    i = vision.index("_model_cascade = GEMINI_IMAGE_MODELS")
    cuerpo = vision[i:i + 3000]
    assert "salida is not None" in cuerpo, (
        "el modelo que ha pintado la imagen ya no sube al que llama: un "
        "render de respaldo se leerá como si fuera del motor pedido")
    assert '"de_respaldo"' in cuerpo, \
        "ya no se dice si la imagen la ha pintado un modelo de respaldo"

    render = _leer(RENDER)
    assert 'parsed_params["motorUsado"]' in render, \
        "el motor usado no llega al render que ve la pantalla"
    assert 'parsed_params["motorDeRespaldo"]' in render, \
        "no se marca cuando el motor pedido fallo"
    # POR ETIQUETA, NO POR NOMBRE DEL MODELO: que motor hay detras es secreto
    # industrial y el Estudio 3D lo ve cualquier carpintero con cuenta. Un
    # candado hermano (`test_calculo_modelos_imagen`) ya lo vigilaba, y me pillo
    # metiendo el nombre tecnico en la pantalla. Aqui se protege la otra mitad:
    # que la etiqueta exista y distinga los motores.
    assert "_etiqueta_de_motor" in render, \
        "el motor vuelve a viajar por su nombre tecnico en vez de por etiqueta"
    i = render.index("def _etiqueta_de_motor")
    fn = render[i:i + 900]
    assert '"Pro"' in fn and '"Estándar"' in fn, \
        "las etiquetas ya no distinguen el motor Pro del de siempre"


def test_la_pantalla_avisa_si_no_es_el_motor_pedido():
    codigo = _codigo_jsx()
    assert "motorDeRespaldo" in codigo, (
        "la pantalla ya no avisa de que el render lo pintó otro modelo: quien "
        "compare dos motores sacará la conclusión al revés")
    assert "No lo uses para comparar motores" in codigo, \
        "el aviso ya no dice lo único que hay que saber al verlo"


def test_el_aviso_no_se_confunde_con_un_render_normal():
    """Pintarlo con la misma cara que un render bueno sería peor que no
    pintarlo: se leería como si todo hubiera ido bien."""
    codigo = _codigo_jsx()
    i = codigo.index("motorDeRespaldo")
    trozo = codigo[i:i + 700]
    assert "amber" in trozo, \
        "el aviso de modelo de respaldo ya no se distingue del texto normal"
