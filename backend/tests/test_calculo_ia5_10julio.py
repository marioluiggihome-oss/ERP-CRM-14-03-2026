# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: IA 5 es el camino del 10/07/2026, y sigue siéndolo.

POR QUÉ EXISTE ESTE BOTÓN
-------------------------
Trece rondas seguidas de lo mismo: el master mira un render de su cocina, dice
que no se parece, y yo aprieto el encargo con otro párrafo. A la cuarta con la
MISMA cocina dijo lo único que hacía falta decir: «busca lo que hacía el 10 de
julio de 2026, que funcionaba mejor», y después «podías poner un botón de IA 5,
con el prompt del 10 de julio».

Tiene razón en el método. Eso no se zanja con otra teoría mía: se zanja
rindiendo el MISMO croquis por los dos caminos y mirando las dos imágenes.

LO QUE ESTE CANDADO PROTEGE, Y ES RARO
--------------------------------------
Aquí no se protege que algo funcione: se protege que algo NO CAMBIE. IA 5 vale
como medida solo mientras sea julio de verdad. En cuanto alguien —yo el
primero— le añada «una reglita que seguro que ayuda», deja de medir nada y las
dos imágenes ya no comparan lo que creemos que comparan.

Por eso:
 1. El texto de julio tiene que estar LITERAL.
 2. IA 5 NO puede llevar nada de agosto: ni recorte del dibujo dentro de la
    página, ni lectura a ficha, ni lista de módulos numerada. En julio no
    existían.
 3. IA 5 tiene que decidirse ANTES que la rama de edición. Si va después, una
    referencia clasificada como foto se va por el camino de editar y el botón
    no se dispara nunca — un botón que no hace nada es peor que no tenerlo,
    porque el master compararía dos renders del mismo camino creyendo que son
    de caminos distintos y sacaría la conclusión contraria.
 4. IA 1 se queda como está: esto se añade al lado, no encima.

UNA CORRECCIÓN QUE ME DEBO
--------------------------
Le dije al master que julio eran 164 palabras contra 2.262 de hoy, «casi
catorce veces más». Era falso, y decidió con ese número. Medí solo la nota del
croquis y me dejé fuera el andamiaje de `build_render_prompt` —1.146 palabras
más— y que el croquis pasaba además por `_expand_brief`, que le pide a un LLM
que redacte una especificación entera sin haber visto el dibujo.

El total real de julio son 1.310 palabras fijas MÁS lo que escribiera el LLM.
Julio no era un prompt corto: era un prompt DISTINTO. Razón de más para medir
en vez de teorizar.
"""
import os
import re

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(BACKEND)
JULIO = os.path.join(BACKEND, "services", "luiggi_ai", "render_10jul.py")
RENDER = os.path.join(BACKEND, "services", "luiggi_ai", "render_3d.py")
ESTUDIO = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


# ─── 1. El texto de julio, literal ─────────────────────────────────────────

# Frases del commit cbdd742 (10/07/2026 22:55). Si alguna cambia, ya no es
# julio: es «julio mejorado», que es justo lo que no queremos medir.
DE_JULIO = [
    "A HAND-DRAWN FLOOR PLAN / SKETCH has been attached",
    "reproduce the EXACT distribution shown in the sketch",
    "The sketch is NOT decorative — it is a TECHNICAL blueprint",
    "Do NOT add, remove, or rearrange any module",
    "The proportions and widths of each module "
    "must match the sketch",
    "Generate a single high-quality, photorealistic 3D render image based "
    "STRICTLY on the following design brief",
]


def test_el_texto_del_croquis_es_el_de_julio_palabra_por_palabra():
    src = _leer(JULIO)
    plano = re.sub(r'"\s*\n\s*"', "", src)   # se pegan las cadenas partidas
    for frase in DE_JULIO:
        assert frase in plano, (
            f"ha cambiado el texto de julio: falta «{frase[:60]}…». IA 5 solo "
            f"vale como medida mientras sea julio de verdad")


def test_los_principios_de_cocina_de_julio_siguen_ahi():
    """`build_render_prompt` los añadía cuando el mueble era una cocina."""
    plano = re.sub(r'"\s*\n\s*"', "", _leer(JULIO))
    assert "PRO_KITCHEN_DESIGN_PRINCIPLES" in plano, \
        "se han quitado los principios de cocina que julio sí metía"
    assert "Work triangle" in plano, "ya no van los principios completos"


def test_el_camino_de_julio_no_lleva_nada_de_agosto():
    """La tentación es obvia: «le meto la lista de módulos y seguro que sale
    mejor». En cuanto se hace, el botón deja de medir."""
    plano = _leer(JULIO)
    for de_agosto in ("FRONT-BY-FRONT FIDELITY", "CLOSED COMPOSITION",
                      "EXACT MODULE LIST", "HEIGHTS ARE DRAWN TOO",
                      "ONLY THE DRAWING COUNTS", "NO WIDTHS ARE WRITTEN",
                      "recortar_dibujo_base64", "lectura_cocina"):
        assert de_agosto not in plano, (
            f"«{de_agosto}» se ha colado en el camino de julio: ya no compara "
            f"julio contra agosto, compara agosto contra agosto")


# ─── 2. Está enchufado, y en el sitio correcto ─────────────────────────────

def _rama_ia5():
    src = _leer(RENDER)
    i = src.index('if ref_b64 and provider == "julio":')
    return src[i:src.index("\n        if ref_b64", i + 10)]


def test_ia5_se_decide_antes_que_la_rama_de_edicion():
    """SI VA DESPUÉS, NO SE DISPARA NUNCA con una referencia que el detector
    clasifique como foto — y el master compararía dos renders del mismo camino
    creyendo que son de caminos distintos."""
    src = _leer(RENDER)
    assert src.index('if ref_b64 and provider == "julio":') < src.index("if ref_b64 and not is_sketch:"), (
        "la rama de IA 5 ha quedado DESPUÉS de la de edición: con una foto por "
        "referencia el botón no hará nada y la comparación saldrá al revés")
    assert src.index('if ref_b64 and provider == "julio":') < src.index("if ref_b64 and is_sketch:"), \
        "la rama de IA 5 ha quedado después de la del croquis de hoy"


def test_ia5_usa_las_piezas_de_julio_y_el_mismo_motor():
    rama = _rama_ia5()
    assert "from services.luiggi_ai.render_10jul import" in rama, \
        "IA 5 ya no usa el módulo de julio"
    assert "prompt_del_croquis_10jul" in rama, "IA 5 ya no monta el prompt de julio"
    assert 'provider="gemini"' in rama, (
        "IA 5 ha dejado de rendir con Gemini: si cambia el motor, la "
        "comparación mide el motor y no el encargo, que es lo que se quería medir")


def test_ia5_expande_el_brief_porque_julio_lo_hacia():
    """Quitarlo sería otra cosa, no julio: el croquis caía en la rama sin
    referencia, que llamaba a `_expand_brief` con gemini-2.5-pro."""
    rama = _rama_ia5()
    assert "_expand_brief" in rama, \
        "IA 5 ya no expande el brief, y julio lo hacía: deja de ser julio"


def test_ia5_no_recorta_ni_lee_a_ficha():
    rama = _rama_ia5()
    for de_agosto in ("recortar_dibujo_base64", "_leer_cocina_del_dibujo",
                      "especificacion_en_texto"):
        assert de_agosto not in rama, (
            f"IA 5 usa «{de_agosto}», que es de agosto: el botón deja de "
            f"contestar a la pregunta que el master hizo")


def test_ia5_dice_en_pantalla_lo_que_es():
    """Un render de IA 5 y uno de IA 1 se parecen lo bastante como para
    confundirlos al día siguiente. Tiene que ir firmado."""
    rama = _rama_ia5()
    assert 'parsed_params["motor"]' in rama and "10/07/2026" in rama, (
        "el render de IA 5 ya no viene identificado: dentro de dos días nadie "
        "sabrá cuál era de qué camino")


# ─── 3. El botón existe, y IA 1 se queda como estaba ───────────────────────

def test_el_boton_de_ia5_esta_en_la_pantalla():
    codigo = "\n".join(l.split("//")[0] for l in _leer(ESTUDIO).splitlines())
    assert "'ia5'" in codigo, "el botón de IA 5 ha desaparecido de la pantalla"
    assert "return 'julio'" in codigo, (
        "IA 5 ya no manda el motor «julio»: el botón se pintará pero rendirá "
        "por el camino de hoy")
    i = codigo.index("if (motor === 'ia5')")
    assert "'julio'" in codigo[i:i + 120], "IA 5 apunta a otro motor"


def test_el_camino_de_hoy_sigue_intacto():
    """Esto se añade AL LADO, no encima. Si IA 1 pierde sus reglas, se ha
    cambiado lo que había mientras se añadía la forma de compararlo."""
    src = _leer(RENDER)
    i = src.index("if ref_b64 and is_sketch:")
    hoy = src[i:]
    for regla in ("FRONT-BY-FRONT FIDELITY", "CLOSED COMPOSITION",
                  "_leer_cocina_del_dibujo", "recortar_dibujo_base64"):
        assert regla in hoy, f"el camino de hoy ha perdido «{regla}»"
