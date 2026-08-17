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


# ─── 5. EL RENDER PIERDE LOS FRENTES ────────────────────────────────────────
#
# El master comparo la pagina de presupuesto de Leroy Merlin que habia pasado
# como referencia con el render que le devolvio el ERP: «no se parecen»,
# «faltan similitudes». Puestas una al lado de la otra, la silueta si estaba —
# la misma fila de bajos, la misma columna a la derecha, el mismo largo—, pero
# se habian ido tres cosas:
#
#   · el HUECO de la campana sobre la placa, relleno con un alto inventado;
#   · los FRENTES DE CAJON bajo el fregadero y a la derecha del horno,
#     convertidos en una puerta lisa;
#   · la COLUMNA partida en dos puertas, renderizada como una sola hoja;
#
# y, cuando volvio a mirar: «y falta un mueble a la derecha del todo».
#
# Ninguna de las cuatro da error. Sale una cocina bonita que no es la del
# cliente. El que la firma cree que ese es su presupuesto, y en fabrica se
# corta otra cosa: un cajon no cuesta lo que una puerta, y un mueble que no
# esta en el render se le olvida a todo el mundo menos al montador.
#
# Se pierde en DOS sitios, y por eso se cierran los dos:
#
#   (a) LO QUE SE LEE del dibujo. La transcripcion se antepone tal cual al
#       encargo; el modelo de imagen ya no vuelve a mirar el croquis con lupa,
#       mira ese resumen. Lo que la transcripcion no pregunta, no existe.
#   (b) LO QUE SE LE PIDE al render. Aunque la transcripcion lo cuente, si el
#       encargo no exige frente a frente, el modelo simplifica: alisa cajones,
#       cierra huecos y encuadra por el centro dejando fuera la ultima puerta.


def _prompt_de_transcripcion():
    """El prompt con el que se LEE el croquis (Vision), pegado igual que el
    del render para leerlo como lo ve el modelo."""
    src = _leer(RENDER)
    i = src.index("async def _transcribe_sketch_with_vision")
    cuerpo = src[src.index("prompt = (", i):src.index("raw = raw_b64", i)]
    return re.sub(r'"\s*\n\s*"', "", cuerpo)


def test_al_leer_el_croquis_se_cuentan_los_frentes_de_cada_mueble():
    """Sin esto la transcripcion dice «modulo de 90, fregadero» y se acabo: el
    render no tiene forma de saber si eran tres cajones o una puerta."""
    p = _prompt_de_transcripcion()
    assert "FRONTS OF EACH MODULE" in p, (
        "la lectura del croquis ha dejado de pedir los frentes de cada mueble: "
        "un banco de cajones volvera a renderizarse como una puerta lisa")
    assert "HOW MANY separate fronts" in p, \
        "ya no se pide CUANTOS frentes tiene cada modulo"
    assert "NEVER merge" in p, \
        "ya no se prohibe fundir varios frentes dibujados en uno solo"


def test_al_leer_el_croquis_se_pregunta_por_el_hueco_de_la_campana():
    """La fila de altos NO siempre es continua. Si no se pregunta, se
    transcribe como continua y el render la cierra."""
    p = _prompt_de_transcripcion()
    assert "GAPS AND RECESSES IN THE WALL-UNIT RUN" in p, (
        "ya no se pregunta si la fila de altos esta interrumpida: el hueco de "
        "la campana se rellenara con un mueble que nadie ha pedido")
    assert "continuous or is INTERRUPTED" in p, \
        "la pregunta ya no obliga a mojarse: continua o interrumpida"


def test_al_leer_el_croquis_se_describen_LOS_DOS_extremos():
    """«y falta un mueble a la derecha del todo». Los extremos se cuentan
    aparte porque son justo lo que se pierde al resumir."""
    p = _prompt_de_transcripcion()
    assert "THE TWO ENDS OF THE RUN" in p, (
        "ya no se describen los extremos de la fila: el ultimo mueble de la "
        "derecha volvera a desaparecer del render")
    assert "FAR RIGHT" in p and "FAR LEFT" in p, \
        "ya no se piden los dos extremos por separado"
    assert "Never leave an end undescribed" in p, \
        "vuelve a poderse dejar un extremo sin describir"


def test_el_render_reproduce_frente_a_frente():
    """Un mueble no es una caja: es sus frentes. Sin esta regla el modelo
    'simplifica' y devuelve puertas lisas donde habia cajones."""
    cuerpo = _prompt_del_croquis()
    assert "FRONT-BY-FRONT FIDELITY" in cuerpo, (
        "el encargo del render ya no exige reproducir frente a frente: los "
        "cajones volveran a salir como una puerta lisa")
    assert "three stacked" in cuerpo and "THREE DRAWERS" in cuerpo, \
        "se ha quitado el caso concreto: tres frentes dibujados son tres cajones"
    assert "NEVER merge two drawn fronts" in cuerpo, \
        "vuelve a permitirse fundir dos frentes dibujados en un panel liso"
    assert "horizontal division is TWO stacked doors" in cuerpo, (
        "la columna partida vuelve a poder renderizarse como una sola hoja")


def test_el_hueco_de_la_campana_no_se_rellena():
    """Un hueco es diseno, no un olvido del dibujante."""
    cuerpo = _prompt_del_croquis()
    assert "A GAP IN THE WALL UNITS IS PART OF THE DESIGN" in cuerpo, (
        "el hueco de la fila de altos vuelve a tratarse como un error a "
        "corregir: el render lo cerrara con un mueble inventado")
    assert "above the hob" in cuerpo, \
        "se ha quitado el caso normal: el hueco de la campana sobre la placa"
    assert "do NOT stretch the neighbouring units" in cuerpo, (
        "ya no se prohibe ensanchar los altos de al lado para cerrar el hueco, "
        "que es la otra forma de comerselo")


def test_el_ultimo_mueble_de_la_derecha_entra_en_la_foto():
    """Lo que dijo el master mirando su render: «falta un mueble a la derecha
    del todo». Son DOS reglas, porque son dos fallos distintos: no dibujarlo,
    y dibujarlo pero dejarlo fuera del encuadre."""
    cuerpo = _prompt_del_croquis()
    assert "BOTH ENDS OF THE RUN MUST BE IN THE PHOTOGRAPH" in cuerpo, (
        "ya no se exige renderizar los dos extremos: el ultimo mueble de la "
        "derecha volvera a faltar")
    assert "LAST MODULE ON THE RIGHT" in cuerpo, \
        "se ha quitado la regla del ultimo mueble de la derecha"
    assert "FRAME THE SHOT SO NOTHING IS CUT OFF" in cuerpo, (
        "ya no se manda encuadrar la cocina entera: el mueble se dibujara pero "
        "quedara fuera de la foto, que para el master es lo mismo que faltar")
    assert "widen the lens" in cuerpo, \
        "ya no se dice que se abra el angulo en vez de quitar un mueble"


# ─── 6. LA REFERENCIA ES UNA PAGINA ENTERA, Y LAS COLUMNAS SON MAS ALTAS ────
#
# Segunda pasada del master sobre lo mismo: «falla». Con la referencia ya a
# tamano completo se ve que NO es un croquis a lapiz, es un PANTALLAZO DEL
# MOVIL de una pagina de presupuesto de Leroy Merlin: titulo «Cocina lineal»,
# recuadro de marca, tres lineas con precios, el total, y arriba y abajo las
# barras del propio movil. El dibujo de la cocina ocupa un tercio de la imagen.
#
# Tres cosas que el prompt no cubria y que se ven en ese dibujo:
#
#  · LA PAGINA NO ES LA COCINA. Al modelo se le decia «lee las etiquetas
#    manuscritas» sin decirle que ahi hay titulos, precios y botones que no son
#    muebles. «Elementos CUBRO» y «TOTAL (IVA incluido)» no son modulos.
#  · LAS COLUMNAS SON MAS ALTAS. En el dibujo las dos columnas de la derecha
#    arrancan del suelo y suben POR ENCIMA de la linea de los altos. El render
#    lo aplanaba todo a la misma altura, y una columna aplanada es una columna
#    que ya no esta: exactamente «falta un mueble a la derecha del todo».
#  · LA CAMARA. El prompt mandaba SIEMPRE «wide-angle corner viewpoint». En una
#    cocina lineal esa vista en tres cuartos escorza el fondo hasta que los
#    ultimos modulos desaparecen. La vista de esquina es para la L y la U.
#
# Y una mentira en pantalla: el pie del render decia «Layout: L-shape» debajo
# de una cocina lineal, porque la pantalla manda 'L-shape' por defecto. No
# cambiaba el render —ese valor no entra en el prompt— pero se cree, y manda a
# buscar el fallo donde no esta.


def test_al_leer_el_croquis_se_preguntan_las_alturas():
    """Una columna aplanada a la altura de un alto es una columna que falta."""
    p = _prompt_de_transcripcion()
    assert "RELATIVE HEIGHTS" in p, (
        "la lectura del croquis ya no pregunta que bloques son columnas de "
        "altura completa: se aplanaran a la altura de los altos")
    assert "rise ABOVE the line of the wall cabinets" in p, \
        "ya no se pregunta si las columnas sobresalen por encima de los altos"
    assert "not a base unit with a wall unit above it" in p, (
        "una columna entera vuelve a poder leerse como bajo + alto, que es "
        "otra forma de perderla")


def test_al_leer_el_croquis_se_ignora_el_resto_de_la_pagina():
    """La referencia del master es un pantallazo entero: titulo, precios,
    total y las barras del movil. Nada de eso es un mueble."""
    p = _prompt_de_transcripcion()
    assert "IS THIS THE WHOLE PAGE?" in p, (
        "ya no se avisa de que la imagen puede ser un pantallazo de una pagina "
        "entera: los precios y el titulo vuelven a competir con el dibujo")
    assert "Cocina lineal" in p, \
        "se ha quitado el unico texto de la pagina que SI vale: la forma"


def test_el_render_sabe_que_le_llega_una_pagina_y_no_solo_un_dibujo():
    cuerpo = _prompt_del_croquis()
    assert "ONLY THE DRAWING COUNTS" in cuerpo, (
        "el encargo ya no distingue el dibujo del resto de la pagina")
    assert "PHONE SCREENSHOT OF A WHOLE PAGE" in cuerpo, \
        "ya no se contempla el caso real: un pantallazo del movil"
    assert "never treat a price line or a brand name as a piece of furniture" in cuerpo, \
        "un precio o una marca vuelven a poder acabar renderizados como mueble"
    # Y el dibujo impreso: la referencia del master NO es a lapiz.
    assert "printed line drawing" in cuerpo, (
        "el encargo vuelve a dar por hecho que el dibujo es a mano; un plano "
        "de catalogo impreso es igual de valido y llega igual de a menudo")


def test_una_columna_dibujada_mas_alta_se_renderiza_mas_alta():
    cuerpo = _prompt_del_croquis()
    assert "HEIGHTS ARE DRAWN TOO" in cuerpo, (
        "el encargo ya no exige respetar las alturas relativas: las columnas "
        "se aplanaran a la altura de los altos y pareceran desaparecer")
    assert "rise ABOVE the top line of the wall cabinets" in cuerpo, \
        "ya no se dice que una columna sobresale por encima de los altos"
    assert "never shrink a full-height column" in cuerpo, \
        "vuelve a poderse encoger una columna entera"
    assert "countertop stops where the column starts" in cuerpo, \
        "la encimera vuelve a poder atravesar la columna"


def test_una_cocina_lineal_no_se_fotografia_en_tres_cuartos():
    """La vista de esquina escorza el fondo y se come los ultimos modulos.
    Es para la L y la U, no para una fila recta."""
    cuerpo = _prompt_del_croquis()
    assert "STRAIGHT SINGLE-WALL RUN — CAMERA" in cuerpo, (
        "no hay regla de camara para la cocina lineal: se seguira usando la "
        "vista de esquina, que esconde el extremo de la fila")
    assert "close to straight-on" in cuerpo, \
        "ya no se pide vista frontal para una fila recta"
    assert "only for L, U and peninsula layouts" in cuerpo, \
        "la vista de esquina vuelve a aplicarse a todo"
    # Y la orden global de camara ya no puede ser «siempre de esquina».
    assert "Use a wide-angle corner viewpoint so the COMPLETE layout" not in cuerpo, (
        "ha vuelto la orden incondicional de fotografiar desde la esquina, que "
        "contradice la regla de la cocina lineal")


def test_el_pie_del_render_no_inventa_la_distribucion():
    """«Layout: L-shape» debajo de una cocina lineal. La pantalla manda
    'L-shape' por defecto; con un croquis delante eso no lo decide ella."""
    src = _leer(RENDER)
    i = src.index('parsed_params["fromSketch"] = True')
    cuerpo = src[i:i + 1200]
    assert 'parsed_params["layout"]' in cuerpo, (
        "el render vuelve a devolver el layout que mando la pantalla por "
        "defecto: el pie dira «L-shape» debajo de una cocina lineal")
    assert "según el dibujo" in cuerpo, \
        "el pie ya no dice de donde sale la distribucion cuando hay croquis"
