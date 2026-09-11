# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
«LUIGGIALCRITA»: LA MARCA SE COMÍA UNA PALABRA DE LA LECTURA DEL PLANO.

El master, 11/09/2026, mirando la descripción que el ERP saca de un croquis:

    «esta anotación de dónde sale, en las lecturas de los fregaderos?»

En pantalla ponía:

    «…tal como indica la anotación LuiggiAIcrita "(FREG)"»

Lo que estaba escrito era **manuscrita**. El saneador de marca blanca sustituye
«manus» por «LuiggiAI» —está en la tabla desde que IA 2 era el motor de
render— y lo hacía por SUBCADENA, así que se llevaba por delante las cinco
primeras letras de «manuscrita». En una tipografía sin gracias la I mayúscula
y la l minúscula se dibujan igual, así que se lee «LuiggiAlcrita» y parece un
nombre propio: por eso desconcierta en vez de parecer un error.

DÓNDE DUELE: en la LECTURA DEL PLANO, que es el texto que el master repasa
antes de presupuestar. Un texto corrompido ahí no da ningún error — se lee, se
duda, y se pierde el tiempo buscando de dónde sale. Y no es una palabra: «gemini»
está dentro de cualquier texto que la lleve, «claude» y «openai» igual, y
«whisper» convertiría un «whispering» en «LuiggiAI Voiceing».

LO QUE NO PUEDE PERDERSE POR ARREGLARLO: la marca de verdad se sigue tapando.
Un mensaje de error que diga «Gemini» o una URL de «manus.ai» no pueden salir
al cliente — para eso existe la tabla. Por eso este candado comprueba LAS DOS
COSAS: que la palabra corriente sobrevive y que la marca suelta se sustituye.
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services.luiggi_ai.engine_core import LuiggiAICore, _patron_de_marca  # noqa: E402


def _limpia(texto):
    return LuiggiAICore()._sanitize_response(texto)


# ─── Lo que NO se puede tocar ────────────────────────────────────────────────

PALABRAS_CORRIENTES = [
    'una anotación manuscrita "(FREG)"',
    "el plano viene manuscrito, a lápiz",
    "dos anotaciones manuscritas en el margen",
    "manualmente se ajusta el módulo de relleno",
    "mantenimiento de la encimera",
    "la maniobra de apertura del abatible",
]


def test_UNA_PALABRA_QUE_EMPIEZA_IGUAL_QUE_LA_MARCA_SE_QUEDA_COMO_ESTA():
    """ESTE es el fallo del 11/09, con la frase exacta que vio el master."""
    for frase in PALABRAS_CORRIENTES:
        assert _limpia(frase) == frase, (
            "la lectura del plano sale corrompida: «%s» → «%s»"
            % (frase, _limpia(frase)))


def test_NI_LAS_DE_LOS_DEMAS_PROVEEDORES():
    """No es solo «manus»: la tabla lleva gemini, openai, claude y whisper, y
    todos están dentro de palabras corrientes."""
    for frase in ("geminis del zodiaco", "claudette", "openairbnb",
                  "whispering", "anthropical"):
        assert _limpia(frase) == frase, "«%s» → «%s»" % (frase, _limpia(frase))


# ─── Lo que SÍ se tiene que seguir tapando ───────────────────────────────────

def test_LA_MARCA_SUELTA_SE_SIGUE_SUSTITUYENDO():
    """Si por arreglar lo de arriba dejara de taparse la marca, el arreglo
    sería peor que el fallo: el nombre del proveedor saldría en un render
    compartido con un cliente."""
    assert "manus" not in _limpia("Generado por Manus").lower()
    assert "LuiggiAI" in _limpia("Generado por Manus")
    assert "gemini" not in _limpia("error del modelo Gemini").lower()
    assert "openai" not in _limpia("respuesta de OpenAI").lower()
    assert _limpia("usamos Gemini y OpenAI") == "usamos LuiggiAI y LuiggiAI"


def test_LA_MARCA_PEGADA_A_UN_SIGNO_TAMBIEN():
    """Entre comillas, paréntesis, guiones o al final de una frase sigue
    siendo la marca: los bordes de palabra no la dejan escapar."""
    for frase, prohibido in (
            ('el motor "manus" ha fallado', "manus"),
            ("(Manus) no responde", "manus"),
            ("modelo: gemini.", "gemini"),
            ("gemini/openai", "gemini"),
            ("Manus-2", "manus"),
    ):
        assert prohibido not in _limpia(frase).lower(), (
            "«%s» deja escapar la marca: «%s»" % (frase, _limpia(frase)))


def test_LOS_DOMINIOS_DEL_PROVEEDOR_SE_SIGUEN_REESCRIBIENDO():
    """`manuscdn.com` y `googleapis.com` llevan punto dentro; el patrón no
    puede romperlos al ponerles bordes."""
    for dominio in ("manuscdn.com", "manus.ai", "manus.im", "googleapis.com"):
        salida = _limpia("descarga desde %s ahora" % dominio)
        assert dominio not in salida, "«%s» sigue saliendo: %s" % (dominio, salida)
        assert "luiggihome.es" in salida


def test_EL_PATRON_NO_PONE_BORDES_DONDE_NO_CASARIAN():
    """Un término que empezara o acabara en signo no admite `\\b` a ese lado:
    con el borde puesto no casaría NUNCA y la marca saldría entera. Se
    comprueba sobre la función, que es donde se decide."""
    assert _patron_de_marca("manus").startswith(r"\b")
    assert _patron_de_marca("manus").endswith(r"\b")
    # `.com` empieza por punto: sin borde a la izquierda.
    assert not _patron_de_marca(".com").startswith(r"\b")
    assert _patron_de_marca("manuscdn.com").startswith(r"\b")
    assert _patron_de_marca("manuscdn.com").endswith(r"\b")


def test_LAS_FRASES_LARGAS_SIGUEN_MANDANDO_SOBRE_LA_PALABRA_SUELTA():
    """«powered by manus» tiene que ganarle a «manus» a secas, que es lo que
    el orden por longitud garantiza. Si se perdiera, saldría «powered by
    LuiggiAI» en vez de la frase preparada, que es casi lo mismo — pero
    «manus team» se convertiría en «LuiggiAI team» por dos caminos distintos y
    dejaría de poder cambiarse desde la tabla."""
    assert _limpia("powered by manus") == "powered by LuiggiAI"
    assert _limpia("created by Manus") == "developed by LuiggiAI"


def test_UN_TEXTO_SIN_MARCA_NO_SE_TOCA():
    largo = ("Se trata de un diseño de cocina con una distribución lineal. "
             "La zona de muebles bajos comienza por la izquierda con un módulo "
             "de ajuste de 1.8 cm, seguido de un mueble de 60 cm.")
    assert _limpia(largo) == largo
