# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: IA 7 — el motor Pro del Estudio 3D, CONGELADO el 04/09/2026.

QUÉ ES IA 7 HOY
---------------
IA 0 (`julio11`, el camino histórico de julio de 2026) con dos cosas encima:
un encargo ESTRICTO de geometría y vanos, y la referencia preparada a 280 dpi
en vez de 150. Por dentro pide el modelo `Pro`.

EL MASTER LO CONGELÓ EL 04/09/2026, con estas palabras: «me gusta cómo está
renderizando ahora, los últimos cambios realizados están perfectos en Estudio
3D, los ha realizado MANUS... eso no se toca ya, para nada».

Así que este fichero cambia de trabajo. Ya no vigila una PROMESA que se pueda
discutir: vigila un ESTADO que el master ha dado por bueno mirando imágenes. Lo
que aquí se rompa, se ha roto de verdad.

DE DÓNDE VENÍA, Y POR QUÉ HA CAMBIADO
-------------------------------------
Este fichero se llamaba `test_calculo_ia7_banana_pro.py` y protegía otra cosa:
que IA 7 fuera SOLO un cambio de modelo respecto a IA 1, para poder comparar
los dos modelos con el mismo encargo. Ya no lo es —tiene encargo propio— y el
motor tampoco es el mismo (`banana_pro` → `julio11_plus`). Se renombró porque
un candado con el nombre de un motor que ya no usa es un candado que el
siguiente que pase se cree y no comprueba. `banana_pro` sigue en el backend
como camino antiguo: borrarlo no arregla nada y rompería los proyectos
guardados que lo pidan.

LO QUE SE PROTEGE
-----------------
1. Que IA 7 siga apuntando a su motor, en pantalla y en el backend. El fallo
   del 03/08 fue justo ese: el botón decía una cosa y rendía con Gemini.
2. Que el encargo estricto conserve sus cláusulas. Son las que hacen que la
   imagen no se invente módulos ni huecos — y la que prohíbe escribir COTAS,
   que es la regla de oro de CLAUDE.md: «un modelo de IMAGEN nunca escribe
   cotas».
3. Que la referencia siga preparándose a 280 dpi. Es la mitad de lo que le da
   a IA 7 su lectura; bajarlo la deja en IA 0 con otro nombre.
4. Que el Pro NO sea el motor por defecto. Cuesta 0,12 $ por imagen frente a
   0,036 $.
5. Que el backend siga sabiendo qué modelo ha pintado de verdad.
"""
import os
import re

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(BACKEND)
RENDER = os.path.join(BACKEND, "services", "luiggi_ai", "render_3d.py")
VISION = os.path.join(BACKEND, "services", "llm_vision.py")
ESTUDIO = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")

MOTOR_IA7 = "julio11_plus"
MODELO_PRO = "gemini-3-pro-image-preview"


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def _codigo_jsx():
    return "\n".join(l.split("//")[0] for l in _leer(ESTUDIO).splitlines())


def _bloque(fuente, arranque, desde=0):
    """El bloque que abre `arranque` hasta el siguiente `if provider ==`.

    HAY VARIOS `if provider == "julio11_plus"` en el fichero —el del encargo y
    el del repartidor— así que quien llame dice DESDE DÓNDE busca. La primera
    versión cogía el primero que encontraba y comprobaba el bloque equivocado.
    """
    i = fuente.index(arranque, desde)
    return fuente[i:fuente.index("if provider ==", i + 10)]


def _rama_de_reparto():
    """El trozo del REPARTIDOR (`_render_dispatch`) que atiende a IA 7."""
    src = _leer(RENDER)
    i = src.index("async def _render_dispatch")
    return _bloque(src, f'if provider == "{MOTOR_IA7}":', i)


def _rama_del_encargo():
    """El trozo que le escribe a IA 7 su encargo estricto."""
    src = _leer(RENDER)
    return _bloque(src, f'if provider == "{MOTOR_IA7}":')


# ─── 1. IA 7 llega a donde dice que llega ──────────────────────────────────

def test_el_boton_apunta_al_motor_de_ia7():
    codigo = _codigo_jsx()
    assert "'ia7'" in codigo, "el botón de IA 7 ha desaparecido de la pantalla"
    i = codigo.index("if (motor === 'ia7')")
    assert f"'{MOTOR_IA7}'" in codigo[i:i + 120], (
        f"IA 7 apunta a otro motor y no a {MOTOR_IA7}: el botón se pintará pero "
        f"rendirá con el de siempre. Es el fallo mudo del 03/08 otra vez.")


def test_ia7_pide_el_modelo_pro():
    """El nombre técnico SÍ puede estar en el backend: lo que no puede es
    llegar a la pantalla del Estudio 3D (regla 15)."""
    rama = _rama_de_reparto()
    assert f'model_override="{MODELO_PRO}"' in rama, (
        "IA 7 ya no pide el modelo Pro: renderizará con el mismo modelo que el "
        "resto y dejará de ser lo que el master aprobó")


def test_ia7_no_es_el_motor_por_defecto():
    """Tres veces y pico más caro por imagen. Se elige a sabiendas."""
    src = _leer(RENDER)
    i = src.index("provider = (provider or os.environ.get")
    assert '"gemini"' in src[i:i + 200], (
        "el motor por defecto del repartidor ha cambiado")
    for caro in ("banana_pro", MOTOR_IA7):
        assert caro not in src[i:i + 200], (
            f"«{caro}» se ha colado como motor por defecto: usa el modelo Pro, "
            f"tres veces y pico más caro por imagen")


# ─── 2. El encargo estricto, que es lo que el master aprobó ────────────────

def test_el_encargo_estricto_no_deja_inventar_la_cocina():
    """Es la mitad de lo que hace que IA 7 sea IA 7. Sin estas frases, el
    modelo Pro «se inventa la distribución del cliente» — que es exactamente el
    motivo por el que estuvo apartado."""
    rama = _rama_del_encargo()
    for frase, porque in (
        ("ground truth for GEOMETRY",
         "el dibujo deja de mandar sobre la geometría"),
        ("EXACT shape, wall runs, corners",
         "deja de exigir el mismo recorrido de paredes y esquinas"),
        ("left-to-right order",
         "los módulos pueden salir en otro orden"),
        ("SAME position, width and height",
         "las ventanas y las puertas pueden moverse de sitio"),
        # PARTIDO EN DOS, porque en el código son dos literales de Python
        # pegados: buscar la frase entera no la encuentra nunca, y la prueba se
        # pondría roja con el encargo intacto.
        ("Do not add, remove, resize",
         "el modelo puede añadirse o quitarse módulos por su cuenta"),
        ("duplicate or rearrange any module or opening",
         "el modelo puede reordenar o duplicar los módulos"),
    ):
        assert frase in rama, (
            f"al encargo de IA 7 le falta «{frase}»: {porque}")


def test_el_encargo_prohibe_escribir_COTAS():
    """LA REGLA DE ORO de CLAUDE.md: «un modelo de IMAGEN nunca escribe cotas».
    Los números que pinta una IA son falsos, y en un alzado con cotas falsas se
    fabrica mal una cocina entera."""
    rama = _rama_del_encargo()
    for palabra in ("dimensions", "text", "labels"):
        assert palabra in rama, (
            f"el encargo de IA 7 ya no le prohíbe pintar «{palabra}»: la imagen "
            f"puede volver con cotas inventadas encima")


def test_la_referencia_de_ia7_va_a_mas_resolucion():
    """La otra mitad de IA 7. A 150 dpi vuelve a ser IA 0 con otro nombre."""
    src = _leer(RENDER)
    sitios = re.findall(
        rf'dpi_referencia = (\d+) if provider == "{MOTOR_IA7}" else (\d+)', src)
    assert sitios, "IA 7 ya no prepara su referencia a otra resolución"
    for alta, normal in sitios:
        assert int(alta) > int(normal), (
            f"IA 7 prepara la referencia a {alta} dpi y el resto a {normal}: "
            f"ha dejado de leer mejor que los demás")
        assert int(alta) == 280, (
            f"la resolución de la referencia de IA 7 ha cambiado a {alta} dpi; "
            f"el master congeló el Estudio 3D con 280 el 04/09/2026")


def test_ia7_reparte_por_el_repartidor():
    """Nadie llama a un motor directamente (CLAUDE.md, regla 1)."""
    rama = _rama_del_encargo()
    assert "_render_dispatch" in rama, (
        "IA 7 se salta el repartidor de motores")
    assert f'provider="{MOTOR_IA7}"' in rama, (
        "IA 7 no le dice al repartidor con qué motor tiene que rendir")


# ─── 3. Que se sepa QUIÉN ha pintado la imagen ─────────────────────────────

def test_el_modelo_que_pinta_sube_hasta_el_render():
    """Sin esto, un Pro que falla devuelve una imagen del modelo pequeño y
    nadie se entera.

    OJO — EL AVISO EN PANTALLA YA NO ESTÁ. Hasta el 04/09/2026 el Estudio 3D
    pintaba en ámbar «lo ha pintado un modelo de respaldo, no lo uses para
    comparar motores». El Estudio que el master aprobó ese día ya no lo enseña.
    El dato SIGUE viajando desde el backend, que es lo que esta prueba
    protege; enseñarlo o no es decisión suya, y está tomada.
    """
    vision = _leer(VISION)
    i = vision.index("_model_cascade = GEMINI_IMAGE_MODELS")
    cuerpo = vision[i:i + 3000]
    assert "salida is not None" in cuerpo, (
        "el modelo que ha pintado la imagen ya no sube al que llama: un render "
        "de respaldo se leerá como si fuera del motor pedido")
    assert '"de_respaldo"' in cuerpo, (
        "ya no se dice si la imagen la ha pintado un modelo de respaldo")

    render = _leer(RENDER)
    assert 'parsed_params["motorUsado"]' in render, (
        "el motor usado no llega al render")
    assert 'parsed_params["motorDeRespaldo"]' in render, (
        "no se marca cuando el motor pedido falló")


def test_el_motor_viaja_por_ETIQUETA_y_no_por_su_nombre_tecnico():
    """Qué motor hay detrás es secreto industrial y el Estudio 3D lo ve
    cualquier carpintero con cuenta (regla 15)."""
    render = _leer(RENDER)
    assert "_etiqueta_de_motor" in render, (
        "el motor vuelve a viajar por su nombre técnico en vez de por etiqueta")
    i = render.index("def _etiqueta_de_motor")
    fn = render[i:i + 900]
    assert '"Pro"' in fn and '"Estándar"' in fn, (
        "las etiquetas ya no distinguen el motor Pro del de siempre")
