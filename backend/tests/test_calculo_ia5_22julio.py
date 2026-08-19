# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: IA 5 es el camino del 22/07/2026, y sigue siéndolo.

POR QUÉ EXISTE ESTE BOTÓN
-------------------------
Trece rondas seguidas de lo mismo: el master mira un render de su cocina, dice
que no se parece, y yo aprieto el encargo con otro párrafo. A la cuarta con la
MISMA cocina dijo lo único que hacía falta decir: «busca lo que hacía el 10 de
julio de 2026, que funcionaba mejor»; después «podías poner un botón de IA 5,
con el prompt del 10 de julio»; y por último «podemos poner en IA 5 lo que hacía
el programa el 22 de julio, y cómo interpretabas los dibujos».

El 22 es mejor que el 10, y se ve poniéndolos uno al lado del otro: añade MODO
ESTRUCTURA ESTRICTA, LOS VANOS —cada ventana y cada puerta en su posición,
ancho y alto— , los anchos de módulo a escala, y la frase que lo cierra todo:
«del texto solo salen acabados, materiales y colores; la geometría viene 100%
del dibujo». Esa frase es la abuela de la regla que hoy sigue en agosto.

Entre el 10 y el 22 SOLO cambió la nota del croquis: `build_render_prompt`,
`_expand_brief` y los principios de cocina son identicos los dos dias.
Comprobado antes de cambiar nada, no supuesto.

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
JULIO = os.path.join(BACKEND, "services", "luiggi_ai", "render_22jul.py")
RENDER = os.path.join(BACKEND, "services", "luiggi_ai", "render_3d.py")
ESTUDIO = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


# ─── 1. El texto de julio, literal ─────────────────────────────────────────

# Frases del commit 8a48da5 (22/07/2026 22:39). Si alguna cambia, ya no es
# julio: es «julio mejorado», que es justo lo que no queremos medir.
DE_JULIO = [
    "A TECHNICAL 2D DRAWING (hand-drawn floor plan, elevation or blueprint)",
    "Treat it in STRICT STRUCTURE / PRECISE MODE",
    "it is the ground truth for GEOMETRY, not decoration",
    "reproduce the EXACT distribution drawn",
    "Do NOT add, remove, resize or rearrange any module or opening",
    "the geometry comes 100% from the drawing",
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


def test_los_vanos_son_lo_que_el_22_añadio_y_no_se_pueden_perder():
    """Es la diferencia de verdad entre el 10 y el 22: una cocina con una
    ventana sobre el fregadero sale con la ventana donde va, y no donde le
    parezca al modelo. Si esto se cae, IA 5 vuelve a ser el 10 de julio."""
    plano = re.sub(r'"\s*\n\s*"', "", _leer(JULIO))
    assert "the OPENINGS: every window and door" in plano, \
        "se han perdido los vanos, que es justo lo que el 22 anadia sobre el 10"
    assert "(vano)" in plano, "se ha quitado la palabra de casa"
    assert "SAME position, width and height as in the drawing" in plano, \
        "los vanos ya no tienen que ir en su sitio exacto"


def test_del_texto_solo_salen_acabados():
    """La frase que lo cierra todo, y la abuela de la regla de agosto."""
    plano = re.sub(r'"\s*\n\s*"', "", _leer(JULIO))
    assert "Only the FINISHES, MATERIALS and COLORS come from the written brief" in plano, \
        "el texto vuelve a poder mandar sobre la geometria del dibujo"


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
    i = src.index('if ref_b64 and is_sketch and provider == "julio":')
    return src[i:src.index("\n        if ref_b64", i + 10)]


def test_ia5_NO_se_traga_las_ediciones():
    """EL FALLO QUE METI CON ESTE BOTON, y merece quedar escrito.

    Puse la rama de IA 5 antes que la de edicion para que se disparase pasara
    lo que pasara. Con eso se trago TODAS las ediciones. El master: «cuando le
    doy al boton de decorador/a, cambia el diseño totalmente con la IA 5».

    Y era exacto. Decorador manda el render con la orden «NO cambies NADA del
    mobiliario, solo el ambiente». Con IA 5 puesta, esa orden ni se leia: la
    imagen entraba por el camino de julio, que trata lo que le llega como UN
    PLANO QUE HAY QUE REALIZAR DESDE CERO. Salia otra cocina. Lo mismo le
    pasaba a HD, a «aplicar cambio» y a los planos tecnicos.

    `is_sketch` es la pregunta que faltaba: ¿esto es un dibujo, o es una foto
    que hay que retocar?"""
    src = _leer(RENDER)
    assert 'if ref_b64 and is_sketch and provider == "julio":' in src, (
        "IA 5 vuelve a dispararse con CUALQUIER referencia: se tragara otra vez "
        "el boton de Decorador, el HD y «aplicar cambio», y devolvera una cocina "
        "distinta en vez de la del cliente retocada")
    # Y sigue por delante de la rama de croquis de hoy, que es lo que compara.
    assert src.index('if ref_b64 and is_sketch and provider == "julio":') < src.index("\n        if ref_b64 and is_sketch:"), \
        "la rama de IA 5 ha quedado despues de la del croquis de hoy: no se dispararia nunca"


def test_una_edicion_sigue_siendo_una_edicion_con_ia5_puesta():
    """La rama de edicion tiene que quedar ALCANZABLE con provider=julio: es
    donde vive el contrato de «lo que no se pide, no se toca»."""
    src = _leer(RENDER)
    i = src.index('if ref_b64 and is_sketch and provider == "julio":')
    j = src.index("if ref_b64 and not is_sketch:")
    entre = src[i:j]
    # Entre una y otra no puede haber un `return` incondicional que se coma la
    # edicion: el `return` de IA 5 vive DENTRO de su `if`.
    assert entre.count("if ref_b64") >= 1, "estructura inesperada entre las dos ramas"
    assert "is_sketch" in src[i:i + 120], \
        "la rama de IA 5 ya no comprueba que la referencia sea un dibujo"


def test_ia5_usa_las_piezas_de_julio_y_el_mismo_motor():
    rama = _rama_ia5()
    assert "from services.luiggi_ai.render_22jul import" in rama, \
        "IA 5 ya no usa el módulo de julio"
    assert "prompt_del_croquis_22jul" in rama, "IA 5 ya no monta el prompt de julio"
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
    assert 'parsed_params["motor"]' in rama and "22/07/2026" in rama, (
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
