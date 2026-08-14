# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: EL CROQUIS MANDA SOBRE EL RENDER.

El master paso su croquis a mano —«ESTA ES UNA COCINA»— con las cotas escritas
(60, 100, 70+60+70, alto 70, 15 de pata, alto de 80x30) y dijo dos cosas:
«no cuadra el diseno con el render» y «no cuadra el alzado que genera con el
original pasado».

POR QUE NO CUADRABA
-------------------
La cadena era esta:

    croquis acotado
        -> render            (IA de imagen)
        -> medir el render   (IA de vision)
        -> alzado

Las UNICAS medidas reales —las que el cliente escribio a mano— se perdian en el
primer paso, porque un modelo de imagen no lee numeros: los dibuja «parecidos».
A partir de ahi el alzado media el render, o sea que acotaba una
interpretacion. El alzado NUNCA habia visto el croquis.

Y no fallaba nada: salia un alzado con cotas, con pinta de bueno.

EL DETECTOR YA SABIA HACERLO
----------------------------
El prompt de `detect-distribucion` lleva escrito «REGLA MAS IMPORTANTE — LAS
MEDIDAS ESCRITAS MANDAN». El fallo no era del detector: era que nadie le pasaba
el croquis. Se le daba siempre el render.

Lo que se protege:

1. EL CROQUIS SE LEE PRIMERO. Si vuelve a leerse el render antes, las cotas
   escritas dejan de mandar otra vez.

2. UNA SOLA VIA. Habia CUATRO sitios pidiendo la distribucion por su cuenta;
   arreglar uno dejaba los otros tres midiendo el render. Ahora todos pasan por
   `deducirDistribucion`.

3. EL PROMPT SIGUE DICIENDO QUE LAS MEDIDAS ESCRITAS MANDAN. Si alguien lo
   suaviza, el croquis deja de servir de nada aunque se lea el primero.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ESTUDIO = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")
COCINAS = os.path.join(RAIZ, "backend", "routes", "estudio_cocinas.py")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def _cuerpo_deducir():
    src = _leer(ESTUDIO)
    i = src.index("const deducirDistribucion")
    return src[i:src.index("\n  };", i)]


# ─── 1. El croquis se lee PRIMERO ───────────────────────────────────────────

def test_el_croquis_se_lee_antes_que_el_render():
    cuerpo = _cuerpo_deducir()
    pos_croquis = cuerpo.find("originalRef")
    pos_render = cuerpo.find("currentImage()")
    assert pos_croquis != -1, "ya no se mira el croquis subido por el master"
    assert pos_render != -1, "ya no hay respaldo por el render"
    assert pos_croquis < pos_render, (
        "el render se lee ANTES que el croquis: las cotas escritas a mano "
        "vuelven a perderse y el alzado acotara una interpretacion")


def test_la_descripcion_sigue_siendo_el_ultimo_respaldo():
    cuerpo = _cuerpo_deducir()
    assert "distribucion-desde-texto" in cuerpo, (
        "sin croquis y sin render, la descripcion escrita era la ultima via")
    assert cuerpo.index("currentImage()") < cuerpo.index("distribucion-desde-texto")


# ─── 2. Una sola via ────────────────────────────────────────────────────────

def test_solo_deducirDistribucion_pide_la_distribucion():
    """Habia CUATRO sitios pidiendola por su cuenta. Arreglar uno dejaba los
    otros tres midiendo el render, y desde fuera no se distingue: los cuatro
    botones sacan un alzado con cotas."""
    src = _leer(ESTUDIO)
    llamadas = src.count("estudio-cocinas/detect-distribucion")
    assert llamadas == 2, (
        f"hay {llamadas} llamadas a detect-distribucion y solo deberian estar "
        f"las 2 de `deducirDistribucion` (croquis y render). Barre el fichero "
        f"ENTERO antes de decir cuantas son")
    cuerpo = _cuerpo_deducir()
    assert cuerpo.count("estudio-cocinas/detect-distribucion") == 2, (
        "las dos llamadas que quedan no estan dentro de `deducirDistribucion`")


def test_los_botones_de_plano_usan_la_via_unica():
    src = _leer(ESTUDIO)
    for funcion in ("generarVistaAlambrica", "generarPlanosTecnicos",
                    "generarPerspectiva"):
        i = src.index(f"const {funcion}")
        cuerpo = src[i:i + 2600]
        assert "deducirDistribucion" in cuerpo, (
            f"{funcion} deduce la distribucion por su cuenta")


# ─── 3. El prompt sigue diciendo que las medidas escritas mandan ────────────

def test_el_prompt_da_prioridad_a_las_medidas_escritas():
    src = _leer(COCINAS)
    i = src.index('@router.post("/detect-distribucion")')
    cuerpo = src[i:src.find("\n@router.", i + 10)]
    assert "LAS MEDIDAS ESCRITAS MANDAN" in cuerpo, (
        "se ha suavizado la regla: el croquis dejaria de servir de nada aunque "
        "se lea el primero")
    for exigencia in ("NO los redondees", "NO los ajustes", "medida_escrita"):
        assert exigencia in cuerpo, f"el prompt ya no exige «{exigencia}»"


def test_el_prompt_no_deja_inventar_un_ancho_de_pared_menor_que_la_suma():
    src = _leer(COCINAS)
    i = src.index('@router.post("/detect-distribucion")')
    cuerpo = src[i:src.find("\n@router.", i + 10)]
    assert "nunca inventes un ancho de pared menor que esa suma" in cuerpo


# ─── 5. EL COMBI QUE NADIE DIBUJO ───────────────────────────────────────────
# 13/08/2026. El master manda su croquis de Villaescusa y la descripcion, que
# termina literalmente: «a la derecha de la columna de lavadora, horno compacto
# microondas y puertas, NO VA COMBI NI NADA, solo un costado». Y el render sale
# con una columna de combi a la derecha.
#
# No fallaba nada. Salia un render bonito de una cocina con un mueble de mas.
# Dos agujeros a la vez:
#   · La composicion estaba ABIERTA: nada decia «estos modulos y ni uno mas»,
#     asi que el modelo completaba el hueco con lo que suele ir ahi.
#   · La palabra «combi» estaba en una frase NEGATIVA y se leyo como un encargo.
#     El glosario de etiquetas la lista sin condicion: en cuanto aparece la
#     palabra, hay combi.
#
# Un mueble inventado en un render se presupuesta y se fabrica.

RENDER = os.path.join(RAIZ, "backend", "services", "luiggi_ai", "render_3d.py")


def _prompt_del_croquis():
    """El prompt con el que se renderiza un CROQUIS (no una foto a editar).

    Se pegan los trozos entre comillas para leer el prompt COMO LO VE EL MODELO.
    Si no, una frase partida en dos lineas de Python haria fallar el candado sin
    que nadie haya tocado la regla, y a la tercera vez se borra el candado."""
    src = _leer(RENDER)
    # El mueble ya no va escrito a fuego («kitchen»): sale de `project_type`,
    # porque a un croquis de ARMARIO no se le puede pedir una cocina.
    i = src.index("TECHNICAL 2D DRAWING of ONE specific {_pieza}")
    cuerpo = src[src.rindex("task_prompt = (", 0, i):src.index("return await", i)]
    return re.sub(r'"\s*\n\s*"', "", cuerpo)


def test_la_composicion_del_croquis_esta_cerrada():
    """Si no se dice «estos y ni uno mas», el modelo rellena los huecos solo."""
    cuerpo = _prompt_del_croquis()
    assert "CLOSED COMPOSITION" in cuerpo, (
        "el prompt del croquis ya no cierra la composicion: el render volvera a "
        "anadir el mueble que 'suele ir ahi' (fue un combi que nadie dibujo)")
    assert "IT DOES NOT EXIST" in cuerpo, \
        "ya no se dice que lo que no esta dibujado NO existe"


def test_una_negacion_no_se_lee_como_un_encargo():
    """«no va combi» nombra el combi: sin esta regla, el modelo lo dibuja."""
    cuerpo = _prompt_del_croquis()
    assert "NEGATIONS ARE ORDERS TOO" in cuerpo, (
        "el prompt ya no avisa de las negaciones: nombrar algo para decir que "
        "NO va volvera a dibujarlo")
    assert "no va combi" in cuerpo, \
        "se ha quitado el ejemplo literal del master, que es el caso probado"


def test_a_la_derecha_del_ultimo_mueble_puede_no_haber_nada():
    """Lo que el master pidio: «solo un costado». Un hueco es un resultado
    valido; cerrarlo con un mueble inventado, no."""
    cuerpo = _prompt_del_croquis()
    assert "side panel" in cuerpo, \
        "ya no se contempla que lo ultimo de la fila sea un costado"
    assert "Empty wall is a valid, correct result" in cuerpo, \
        "vuelve a estar prohibido dejar pared vacia, o sea que se rellenara"


def test_el_glosario_de_etiquetas_no_es_una_lista_de_la_compra():
    """El glosario nombra combi, frigo, campana, despensero... Si se lee como
    catalogo en vez de como diccionario, todo lo que nombra acaba dibujado."""
    cuerpo = _prompt_del_croquis()
    i = cuerpo.index("READ HANDWRITTEN SPANISH TECHNICAL LABELS")
    cabecera = cuerpo[i:i + 700]
    assert "DICTIONARY, not a" in cabecera, (
        "el glosario ha vuelto a presentarse como una lista de cosas a "
        "dibujar en vez de como un diccionario de etiquetas")
    assert "not negated" in cabecera, \
        "el glosario vuelve a aplicarse aunque la etiqueta venga negada"


def test_la_composicion_tambien_esta_cerrada_al_medir_el_croquis():
    """El mismo agujero, en el otro extremo: si el que MIDE el croquis anade un
    modulo, el combi vuelve por la puerta del alzado y ademas acotado."""
    src = _leer(COCINAS)
    i = src.index('@router.post("/detect-distribucion")')
    cuerpo = src[i:src.find("\n@router.", i + 10)]
    assert "LA COMPOSICIÓN ESTÁ CERRADA" in cuerpo, (
        "el detector puede volver a anadir modulos que no estan dibujados")
    assert "NO EXISTE" in cuerpo, \
        "ya no se dice que lo que no esta dibujado ni escrito no existe"
    assert "solo hay un costado" in cuerpo, \
        "se ha quitado el caso del master: a la derecha solo va un costado"


# ─── 4. La imagen se valida por sus BYTES, no por lo que diga el servidor ───

def test_la_imagen_se_reconoce_por_su_firma_y_no_por_el_content_type():
    """Un render bueno servido con un mime flojo se rechazaba con «vuelve a
    generar el render», y el render ya estaba bien. La comprobacion sigue
    existiendo —un JSON de error tampoco tiene firma de imagen— pero mira los
    bytes.

    Quien lee los bytes es `tipoImagenPorFirma`; `pareceUnaImagen` solo decide
    con lo que aquella devuelve. El candado mira donde se hace el trabajo: si
    se comprueba la funcion de fuera, se puede vaciar la de dentro sin que el
    candado se entere.
    """
    src = _leer(ESTUDIO)
    assert "pareceUnaImagen" in src, "se ha quitado la comprobacion de la imagen"
    assert "tipoImagenPorFirma" in src, "ya nadie mira los bytes de la imagen"
    # `pareceUnaImagen` puede fiarse del mime, pero NUNCA solo del mime: si el
    # servidor manda un content-type flojo, tiene que quedarle la firma.
    i = src.index("const pareceUnaImagen")
    decision = src[i:src.index(";", i)]
    assert "tipoImagenPorFirma" in decision, (
        "«pareceUnaImagen» ha vuelto a decidir solo por el content-type: un "
        "render bueno con un mime flojo se rechazara otra vez")
    i = src.index("const tipoImagenPorFirma")
    cuerpo = src[i:src.index("\n  };", i)]
    # PNG y JPEG, que son los dos que salen de los motores de render.
    assert "0x89" in cuerpo and "0x50" in cuerpo, "ya no se reconoce el PNG"
    assert "0xFF, 0xD8" in cuerpo, "ya no se reconoce el JPEG"
    # El master fotografia el croquis con el movil: en iPhone sale HEIC.
    assert "heic" in cuerpo.lower(), "ya no se reconoce el HEIC del iPhone"
