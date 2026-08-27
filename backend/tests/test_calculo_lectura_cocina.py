# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: el dibujo se lee A FICHA, y la cuenta llega entera al render.

EL FALLO QUE SE PERSIGUE
------------------------
Cuatro veces seguidas el master dijo lo mismo del mismo render: «no se
parecen», «falla», «sigue sin interpretarlo bien», «igual». Cuatro veces la
respuesta fue apretar el encargo con mas reglas. Y cuatro veces volvio a
faltar EXACTAMENTE lo mismo: los altillos —la segunda fila de altos que cierra
contra el techo— y el nicho de la campana sobre la placa.

El fallo no estaba en las reglas. Estaba en el camino:

    dibujo -> parrafo en prosa -> modelo de imagen

Un parrafo no se cuenta. «Una fila de altos con altillos encima y un hueco
para la campana» es una frase impecable con la que se puede dibujar cualquier
cocina: describe igual de bien cinco altos que tres. Lo que NO sobrevive a la
prosa son los numeros.

Ahora el dibujo se lee a lista de muebles —fila, ancho y frentes uno a uno— y
el encargo lo escribe el ERP, numerado. La cuenta deja de depender de que un
parrafo la conserve.

LO QUE SE PROTEGE
-----------------
1. Que la cuenta llegue: si el dibujo tiene 5 altos y 5 altillos, en el encargo
   pone 5 y 5, y ademas se repite al final para poder comprobarlo mirando.
2. Que los altillos y el hueco de la campana viajen SIEMPRE, que son las dos
   cosas que se perdian.
3. Que una lectura fallida NO deje sin render: se cae a la prosa de siempre.
4. Que no se invente ni una medida: una cota que no esta escrita se queda
   vacia, nunca se estima. Es la regla de oro de la casa.
"""
import importlib.util
import json
import os

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lc():
    spec = importlib.util.spec_from_file_location(
        "lectura_cocina", os.path.join(BACKEND, "services", "luiggi_ai", "lectura_cocina.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


LC = _lc()


def _cocina_del_master():
    """La cocina LL del master: 5 bajos, 5 altos, 5 altillos hasta el techo,
    2 columnas (una con horno y micro) y el hueco de la campana."""
    return {
        "forma": "lineal",
        "acabados": {"frentes": "blanco mate", "encimera": "cuarzo blanco"},
        "filas": {
            "bajos": [
                {"orden": 1, "ancho_cm": 60, "contiene": "fregadero", "frentes": ["fregadero", "puerta"]},
                {"orden": 2, "ancho_cm": 60, "frentes": ["cajon", "cajon", "cajon"]},
                {"orden": 3, "ancho_cm": 90, "contiene": "placa", "frentes": ["placa", "cajon", "cajon"]},
                {"orden": 4, "ancho_cm": 60, "frentes": ["puerta"]},
                {"orden": 5, "ancho_cm": 60, "frentes": ["puerta"]},
            ],
            "altos": [{"orden": i, "ancho_cm": 60, "frentes": ["puerta"]} for i in range(1, 6)],
            "altillos": [{"orden": i, "ancho_cm": 60, "frentes": ["puerta"]} for i in range(1, 6)],
            "columnas": [
                {"orden": 1, "ancho_cm": 60, "contiene": "horno y microondas",
                 "frentes": ["microondas", "horno", "puerta"]},
                {"orden": 2, "ancho_cm": 60, "frentes": ["puerta", "puerta"]},
            ],
        },
        "huecos_altos": [{"despues_de": 3, "ancho_cm": 90, "motivo": "campana"}],
        "altos_llegan_al_techo": True,
        "notas": "",
    }


# ─── 1. La lectura sobrevive a como conteste el modelo ─────────────────────

def test_el_json_se_saca_aunque_venga_envuelto():
    """Se pide «solo JSON» y contestan con ```json, una disculpa delante y una
    coletilla detras. Si eso tumba la lectura, no se usa nunca."""
    d = _cocina_del_master()
    crudo = "Aqui tienes:\n```json\n" + json.dumps(d) + "\n```\nEspero que sirva."
    leido = LC.parsear_lectura(crudo)
    assert leido is not None, "el JSON envuelto en ``` ha dejado de leerse"
    assert len(leido["filas"]["altillos"]) == 5, "se han perdido los altillos al leer"
    assert len(leido["filas"]["columnas"]) == 2, "se han perdido las columnas al leer"


def test_una_lectura_que_no_vale_devuelve_nada():
    """None significa «cae al metodo de siempre». Devolver una ficha vacia
    seria peor: el encargo diria «0 muebles» y saldria una cocina desnuda."""
    assert LC.parsear_lectura("una cocina bonita en L") is None, \
        "una respuesta en prosa se esta colando como ficha"
    assert LC.parsear_lectura("") is None
    assert LC.parsear_lectura(None) is None
    assert LC.parsear_lectura('{"forma":"lineal","filas":{}}') is None, (
        "una ficha SIN NI UN MUEBLE se da por buena: el encargo pedira una "
        "cocina vacia en vez de caer a la lectura de siempre")


def test_no_se_inventa_ni_una_medida():
    """Regla de oro de la casa: «no se sabe» no es cero, y no es un numero
    aproximado. Un ancho que no esta escrito se queda vacio."""
    leido = LC.parsear_lectura(json.dumps({
        "forma": "lineal",
        "filas": {"bajos": [{"orden": 1, "ancho_cm": None, "frentes": ["puerta"]},
                            {"orden": 2, "ancho_cm": "unos 60", "frentes": ["puerta"]},
                            {"orden": 3, "ancho_cm": 0, "frentes": ["puerta"]}]},
    }))
    anchos = [m["ancho_cm"] for m in leido["filas"]["bajos"]]
    assert anchos[0] is None, "un ancho ausente se ha convertido en un numero"
    assert anchos[2] is None, "un ancho 0 se ha dado por bueno: 0 no es una medida"
    texto = LC.especificacion_en_texto(leido)
    assert "width not written" in texto, (
        "un ancho que no esta en el dibujo tiene que viajar como «no escrito», "
        "no rellenarse con una estimacion")


# ─── 2. La cuenta llega entera al modelo de imagen ─────────────────────────

def test_la_cuenta_de_cada_fila_va_escrita_en_el_encargo():
    texto = LC.especificacion_en_texto(_cocina_del_master())
    assert "BASE UNITS — 5 module(s)" in texto, "no se dice cuantos bajos hay"
    assert "WALL UNITS — 5 module(s)" in texto, "no se dice cuantos altos hay"
    assert "SECOND ROW ON TOP (altillos) — 5 module(s)" in texto, \
        "no se dice cuantos altillos hay: es justo lo que se perdia"
    assert "FULL-HEIGHT TALL COLUMNS — 2 module(s)" in texto, "no se dicen las columnas"


def test_la_cuenta_se_repite_al_final_para_poder_comprobarla():
    """Una lista larga se lee por encima. La linea final es corta y se puede
    contrastar mirando la foto, sin releer nada."""
    texto = LC.especificacion_en_texto(_cocina_del_master())
    assert "COUNT BEFORE YOU FINISH" in texto, \
        "se ha quitado la cuenta final: nadie comprueba una lista larga"
    final = texto[texto.index("COUNT BEFORE YOU FINISH"):]
    assert "5 base units" in final and "5 wall units" in final, "la cuenta final no cuadra"
    assert "5 units in the second row on top" in final, "los altillos no entran en la cuenta final"
    assert "2 full-height tall columns" in final, "las columnas no entran en la cuenta final"
    assert "1 open gap in the wall run" in final, "el hueco de la campana no entra en la cuenta"
    assert "Not one more, not one less" in final, "ya no se cierra la composicion"


def test_los_frentes_van_uno_a_uno():
    """Tres cajones dibujados son tres cajones. Es lo que el master reclamo
    mirando la pagina de Leroy Merlin."""
    texto = LC.especificacion_en_texto(_cocina_del_master())
    assert "3 drawers" in texto, "un banco de tres cajones ha vuelto a ser una puerta"
    assert "2 doors" in texto, "la columna partida en dos puertas se ha fundido en una"
    assert "built-in oven" in texto and "built-in microwave" in texto, \
        "el horno y el microondas ya no viajan como electrodomesticos"
    # Y EN INGLES: el encargo entero va en ingles. El vocabulario conocido se
    # traduce; una palabra suelta en castellano el modelo la lee como marca.
    # Se miran las palabras SUELTAS: lo que va entrecomillado es una etiqueta
    # del dibujo y viaja a proposito tal cual (ver el candado siguiente).
    import re as _re
    suelto = _re.sub(r'"[^"]*"', "", texto).replace("altillos", "")
    for palabra in ("fregadero", "microondas", "cajon", "placa", "campana"):
        assert palabra not in suelto, \
            f"«{palabra}» se cuela sin traducir en un encargo escrito en ingles"


def test_una_etiqueta_del_dibujo_ni_se_borra_ni_se_suelta_a_pelo():
    """Un rotulo manuscrito —«escobero», un codigo de catalogo— es un DATO del
    cliente: borrarlo por no saber traducirlo seria tirar informacion. Pero
    soltarlo en medio de una frase inglesa hace que se lea como una marca."""
    d = _cocina_del_master()
    d["filas"]["bajos"][3]["contiene"] = "escobero"
    texto = LC.especificacion_en_texto(d)
    assert "escobero" in texto, "una etiqueta manuscrita del dibujo se ha perdido"
    assert 'label written on the drawing: "escobero"' in texto, (
        "la etiqueta viaja suelta en medio del ingles, sin decir que es un "
        "rotulo leido del dibujo")


def test_el_hueco_de_la_campana_viaja_con_su_sitio_y_su_ancho():
    texto = LC.especificacion_en_texto(_cocina_del_master())
    assert "OPEN GAP IN THE WALL RUN after wall unit 3, 90 cm wide" in texto, (
        "el hueco de la campana ya no lleva ni donde va ni cuanto mide: se "
        "volvera a rellenar con un mueble inventado")
    assert "LEAVE IT OPEN" in texto, "ya no se ordena dejarlo abierto"
    assert "do not widen its neighbours" in texto, (
        "ya no se prohibe ensanchar los altos de al lado, que es la otra "
        "forma de comerse el hueco")


def test_sin_altillos_se_dice_expresamente_que_no_los_hay():
    """El silencio no vale: si no se dice nada, el modelo pone lo que le
    parece. Una fila sola tiene que ir dicha."""
    d = _cocina_del_master()
    d["filas"]["altillos"] = []
    texto = LC.especificacion_en_texto(d)
    assert "altillos): NONE" in texto and "single row" in texto, (
        "cuando NO hay altillos ya no se dice: el render podra inventarse una "
        "segunda fila igual que antes se comia la que si estaba")


# ─── 3. Lo que ve el master ────────────────────────────────────────────────

def test_el_resumen_de_pantalla_dice_lo_que_se_ha_leido():
    """Sin esto no hay forma de saber si el fallo es de la lectura o del
    render, y se acaba apretando el prompt a ciegas."""
    r = LC.resumen_para_pantalla(_cocina_del_master())
    assert "Bajos: 5" in r and "Altos: 5" in r, "el resumen no dice cuantos muebles se han leido"
    assert "Altillos (2ª fila): 5" in r, "el resumen no menciona los altillos"
    assert "Columnas: 2" in r, "el resumen no menciona las columnas"
    assert "Hueco en los altos" in r and "90 cm" in r, "el resumen no menciona el hueco"
    assert "3c" in r, "el resumen no dice cuantos cajones tiene cada mueble"


# ─── 4. Está enchufado, y con red ──────────────────────────────────────────

def test_el_render_lee_a_ficha_y_cae_a_la_prosa_si_no_puede():
    ruta = os.path.join(BACKEND, "services", "luiggi_ai", "render_3d.py")
    with open(ruta, encoding="utf-8") as f:
        src = f.read()
    i = src.index('parsed_params["fromSketch"] = True')
    cuerpo = src[i:src.index("task_prompt = (", i)]
    assert "_leer_cocina_del_dibujo" in cuerpo, \
        "la via del croquis ya no lee el dibujo a ficha"
    assert "especificacion_en_texto" in cuerpo, (
        "se lee a ficha pero no se convierte en encargo numerado: la cuenta se "
        "vuelve a perder por el camino")
    assert "_transcribe_sketch_with_vision" in cuerpo, (
        "se ha quitado el respaldo en prosa: si la lectura a ficha falla, el "
        "master se queda sin render")
    assert "resumen_para_pantalla" in cuerpo, \
        "lo leido ya no se devuelve para enseñarlo en pantalla"
    # Y el recorte del dibujo tiene que seguir yendo ANTES de leer.
    assert cuerpo.index("recortar_dibujo_base64") < cuerpo.index("_leer_cocina_del_dibujo"), (
        "se lee el dibujo antes de recortarlo: se vuelve a leer la pagina "
        "entera, con los precios y el total dentro")


def test_la_pantalla_enseña_lo_leido():
    ruta = os.path.join(os.path.dirname(BACKEND), "frontend", "src", "components", "AIRenderStudio.jsx")
    with open(ruta, encoding="utf-8") as f:
        src = f.read()
    codigo = "\n".join(l.split("//")[0] for l in src.splitlines())
    assert "lecturaDelDibujo" in codigo, (
        "la pantalla ya no enseña lo que el ERP ha leido del dibujo: cuando un "
        "render salga mal se volvera a adivinar si fallo la lectura o el render")


# ─── 5. ¿Y SI EL DIBUJO NO TRAE MEDIDAS? ───────────────────────────────────
#
# Pregunta literal del master: «y sino tiene medidas? q hace?». Pasa a menudo:
# un croquis rapido en una servilleta, o un dibujo de catalogo que solo enseña
# la composicion.
#
# Lo que NO puede hacer es rellenar el hueco. Un render sin cotas se ve
# EXACTAMENTE igual de bueno que uno acotado, y esa es la trampa: se firma, se
# presupuesta y se corta sobre proporciones que puso una maquina. Por eso:
#
#  · al modelo se le dice que mande el dibujo (proporciones relativas) y las
#    alturas normales del oficio, y que NO iguale los modulos —igualarlos es
#    como se perdian los muebles de 15—;
#  · al master se le avisa EL PRIMERO y en mayusculas.


def _cocina_sin_una_sola_cota():
    d = _cocina_del_master()
    for fila in d["filas"].values():
        for m in fila:
            m.pop("ancho_cm", None)
    for h in d["huecos_altos"]:
        h.pop("ancho_cm", None)
    return d


def test_sin_cotas_la_composicion_se_lee_igual():
    """Lo que se pierde son los numeros, NO los muebles. La cuenta sigue."""
    texto = LC.especificacion_en_texto(LC.parsear_lectura(json.dumps(_cocina_sin_una_sola_cota())))
    assert "BASE UNITS — 5 module(s)" in texto, "sin cotas se han perdido tambien los muebles"
    assert "3 drawers" in texto, "sin cotas se han perdido los frentes"
    assert "OPEN GAP IN THE WALL RUN" in texto, "sin cotas se ha perdido el hueco de la campana"


def test_sin_cotas_no_se_rellena_ningun_ancho():
    """La regla de oro: «no se sabe» no es un numero."""
    leido = LC.parsear_lectura(json.dumps(_cocina_sin_una_sola_cota()))
    for fila in leido["filas"].values():
        for m in fila:
            assert m["ancho_cm"] is None, "se ha rellenado un ancho que el dibujo no traia"
    texto = LC.especificacion_en_texto(leido)
    assert "width not written" in texto, "un ancho ausente ya no viaja como ausente"
    assert " cm —" not in texto, "ha aparecido una medida en cm que nadie escribio"


def test_sin_cotas_manda_la_proporcion_del_dibujo():
    """Sin numeros y sin instruccion, el modelo iguala los modulos «para que
    quede equilibrado». Asi es como desaparecia un extraible de 15."""
    texto = LC.especificacion_en_texto(LC.parsear_lectura(json.dumps(_cocina_sin_una_sola_cota())))
    assert "NO WIDTHS ARE WRITTEN ANYWHERE" in texto, (
        "no se avisa de que el dibujo viene sin cotas: el modelo repartira los "
        "anchos a su gusto sin que nadie se lo haya dicho")
    assert "keep the RELATIVE PROPORTIONS exactly as drawn" in texto, \
        "ya no manda la proporcion dibujada cuando no hay numeros"
    assert "do not even out the modules" in texto, \
        "vuelve a poderse igualar los modulos, y ahi es donde se pierden los estrechos"


def test_con_cotas_no_aparece_el_aviso():
    """El aviso solo cuando toca: si el dibujo viene acotado, sobra."""
    texto = LC.especificacion_en_texto(_cocina_del_master())
    assert "NO WIDTHS ARE WRITTEN ANYWHERE" not in texto, \
        "se avisa de que no hay cotas en un dibujo que SI las trae"
    assert "SIN COTAS ESCRITAS" not in LC.resumen_para_pantalla(_cocina_del_master())


def test_sin_cotas_el_master_lo_ve_lo_primero():
    """Un render sin cotas se ve igual de bueno que uno acotado. Si el aviso va
    escondido al final, no lo lee nadie."""
    r = LC.resumen_para_pantalla(LC.parsear_lectura(json.dumps(_cocina_sin_una_sola_cota())))
    assert r.startswith("SIN COTAS ESCRITAS"), (
        "el aviso de que no hay cotas ya no va el primero: se firmara un "
        "presupuesto sobre proporciones que puso una maquina")
    assert "no midas sobre el render" in r, \
        "ya no se dice lo unico que hay que saber: que de ahi no se mide"


# ─── 6. LAS COTAS DEL PLANO: MILIMETROS, ANCHO TOTAL Y LAS TRAMPAS ─────────
#
# El master, mirando el recuadro «Leido del dibujo» que se acababa de poner:
# «yo creo que el fallo esta en la lectura de datos». Y tenia razon. Su plano
# —uno acotado de verdad, en milimetros— traia esto:
#
#     altos:  800  800  500  400  300        (mm)
#     total:  2500                            (mm)
#     y en el lateral: 600 (fondo), 850 (altura de encimera), 100 (zocalo)
#
# Y el ERP leyo: «Bajos: 4 → 60(2p), ?(2p), ?(1c+horno), ?(1p)».
#
# Tres fallos, todos de lectura:
#
#  · EL NUMERO MAS GRANDE DEL PLANO NO TENIA DONDE IR. El esquema no pedia el
#    ancho total, asi que el 2500 se tiraba. Es el ancla: sin el, cada modulo
#    sin cota es un agujero; con el, el que falta sale de una resta.
#  · LAS COTAS VERTICALES SE COLABAN COMO ANCHOS. El «600» del lateral es el
#    FONDO de los bajos, no el ancho del primer mueble. Igual el 850 y el 100.
#  · MILIMETROS. Un plano tecnico va en mm y este ERP en cm. 2500 no es una
#    pared de 25 metros.
#
# Y una cuarta cosa que sale sola al cuadrar: los altos de su plano suman
# 280 cm y el total escrito son 250. Una de las dos esta mal. Cuadrarlo por
# dentro y callarse es como un presupuesto sale con 30 cm de mas y nadie sabe
# por que.


def test_un_plano_en_milimetros_se_lee_en_centimetros():
    """2500 no es una pared de 25 metros."""
    d = LC.parsear_lectura(json.dumps({
        "forma": "lineal", "ancho_total_cm": 2500, "fondo_cm": 600,
        "filas": {"bajos": [{"orden": 1, "ancho_cm": 800, "frentes": ["puerta"]},
                            {"orden": 2, "ancho_cm": 600, "frentes": ["puerta"]}]}}))
    assert d["ancho_total_cm"] == 250, \
        f"el ancho total se ha quedado en {d['ancho_total_cm']}: no se ha pasado de mm a cm"
    assert d["fondo_cm"] == 60, "el fondo sigue en milimetros"
    assert [m["ancho_cm"] for m in d["filas"]["bajos"]] == [80, 60], \
        "los anchos de modulo siguen en milimetros"


def test_un_numero_que_ya_esta_en_centimetros_no_se_divide():
    """Dividir por diez lo que ya estaba bien es peor que no convertir nada."""
    d = LC.parsear_lectura(json.dumps({
        "forma": "lineal", "ancho_total_cm": 250,
        "filas": {"bajos": [{"orden": 1, "ancho_cm": 60, "frentes": ["puerta"]},
                            {"orden": 2, "ancho_cm": 120, "frentes": ["puerta"]}]}}))
    assert d["ancho_total_cm"] == 250, "un ancho total que ya venia en cm se ha dividido"
    assert [m["ancho_cm"] for m in d["filas"]["bajos"]] == [60, 120], \
        "un modulo de 120 cm (side by side) se ha convertido en 12"


def test_el_ancho_total_del_plano_llega_al_render():
    """Es el ancla. Sin el, el modelo reparte los modulos a ojo."""
    d = LC.parsear_lectura(json.dumps({
        "forma": "lineal", "ancho_total_cm": 2500,
        "filas": {"bajos": [{"orden": 1, "ancho_cm": 600, "frentes": ["puerta"]}]}}))
    texto = LC.especificacion_en_texto(d)
    assert "TOTAL WIDTH OF THE RUN: 250 cm" in texto, (
        "el ancho total del plano ya no viaja al encargo: cada modulo sin cota "
        "vuelve a ser un agujero que el modelo rellena a su gusto")
    assert "Ancho total: 250 cm" in LC.resumen_para_pantalla(d), \
        "el ancho total no se enseña, asi que no se puede comprobar de un vistazo"


def test_la_lectura_avisa_de_no_usar_una_cota_vertical_como_ancho():
    """El «600» del lateral es el FONDO. Es la trampa que se comio el plano."""
    assert "READING THE DIMENSION LINES" in LC.PROMPT_LECTURA, (
        "se ha quitado la parte que distingue cotas horizontales de verticales: "
        "el fondo y la altura de encimera volveran a colarse como anchos")
    assert "it is NEVER the width of a module" in LC.PROMPT_LECTURA, \
        "ya no se prohibe usar una cota vertical como ancho"
    assert "is the DEPTH of the base units" in LC.PROMPT_LECTURA, \
        "se ha quitado el caso concreto del plano del master (el 600 del lateral)"
    assert "millimetres" in LC.PROMPT_LECTURA, \
        "ya no se avisa de que un plano tecnico va en milimetros"


def test_con_una_sola_incognita_el_ancho_sale_de_una_resta():
    """250 total, 60 + 50 + 80 escritos -> el que falta mide 60. Exacto, no
    estimado. Y marcado como deducido, que no es lo mismo que escrito."""
    d = LC.parsear_lectura(json.dumps({
        "forma": "lineal", "ancho_total_cm": 250,
        "filas": {"bajos": [{"orden": 1, "ancho_cm": 60, "frentes": ["puerta"]},
                            {"orden": 2, "ancho_cm": 50, "frentes": ["puerta"]},
                            {"orden": 3, "ancho_cm": 80, "frentes": ["puerta"]},
                            {"orden": 4, "frentes": ["puerta"]}]}}))
    ultimo = d["filas"]["bajos"][3]
    assert ultimo["ancho_cm"] == 60, (
        f"el ancho que faltaba no se ha deducido del total: {ultimo['ancho_cm']}")
    assert ultimo["ancho_deducido"] is True, (
        "el ancho deducido no va marcado: se presentara como si estuviera "
        "escrito en el plano, que es exactamente lo que no puede pasar")
    assert "derived from the total, not written" in LC.especificacion_en_texto(d), \
        "al modelo no se le dice que ese ancho es deducido"
    assert "~60" in LC.resumen_para_pantalla(d), \
        "en pantalla el ancho deducido no se distingue de uno escrito"


def test_con_dos_incognitas_no_se_inventa_el_reparto():
    """Con dos huecos no se sabe como se reparte. Repartir a partes iguales
    seria inventar DOS medidas. Se dice cuanto sitio queda y ya."""
    d = LC.parsear_lectura(json.dumps({
        "forma": "lineal", "ancho_total_cm": 250,
        "filas": {"bajos": [{"orden": 1, "ancho_cm": 60, "frentes": ["puerta"]},
                            {"orden": 2, "frentes": ["puerta"]},
                            {"orden": 3, "frentes": ["puerta"]}]}}))
    anchos = [m["ancho_cm"] for m in d["filas"]["bajos"]]
    assert anchos[1] is None and anchos[2] is None, \
        f"se han inventado dos medidas repartiendo el hueco a partes iguales: {anchos}"
    texto = LC.especificacion_en_texto(d)
    assert "190 cm of the run are shared between the 2 modules" in texto, (
        "no se dice cuanto sitio libre queda: el modelo repartira a su gusto y "
        "los estrechos volveran a desaparecer")
    assert "do NOT make them all equal" in texto, \
        "ya no se prohibe igualarlos, que es justo lo que hace por defecto"


def test_una_contradiccion_del_plano_se_dice_y_no_se_tapa():
    """El plano del master: los altos suman 280 y el total escrito son 250."""
    d = LC.parsear_lectura(json.dumps({
        "forma": "lineal", "ancho_total_cm": 2500,
        "filas": {"altos": [{"orden": i, "ancho_cm": w, "frentes": ["puerta"]}
                            for i, w in enumerate([800, 800, 500, 400, 300], 1)]}}))
    avisos = d.get("avisos") or []
    assert avisos, (
        "los altos suman 280 cm y el total escrito son 250, y no se dice nada: "
        "se cuadra por dentro y el presupuesto sale descuadrado sin explicacion")
    assert "280" in avisos[0] and "250" in avisos[0], \
        "el aviso no dice las dos cifras que no cuadran"
    assert LC.resumen_para_pantalla(d).startswith("⚠"), \
        "el aviso no sale el primero en pantalla, asi que no se lee"


# ─── 7. UN RESPALDO SILENCIOSO ES UN FALLO SILENCIOSO ──────────────────────
#
# El master mando una pantalla con su render y, debajo, NADA: ni el recuadro
# de «leido del dibujo» ni un aviso. No salia porque la lectura a ficha habia
# fallado y se habia caido a la lectura en prosa — sin decirlo.
#
# Desde fuera eso se ve EXACTAMENTE IGUAL que si la mejora no estuviera
# desplegada. Uno se queda mirando una pantalla muda y saca conclusiones sobre
# la version equivocada, que es peor que no tener el recuadro.
#
# El respaldo esta bien —quedarse sin render seria peor que perder detalle—.
# Lo que no puede es no notarse.


def test_si_la_lectura_a_ficha_falla_se_dice():
    ruta = os.path.join(BACKEND, "services", "luiggi_ai", "render_3d.py")
    with open(ruta, encoding="utf-8") as f:
        src = f.read()
    i = src.index("lectura = await self._leer_cocina_del_dibujo")
    cuerpo = src[i:src.index("task_prompt = (", i)]
    caida = cuerpo[cuerpo.index("else:"):]
    assert '_transcribe_sketch_with_vision' in caida, \
        "se ha quitado el respaldo en prosa: un fallo de lectura deja sin render"
    assert 'parsed_params["lecturaDelDibujo"]' in caida, (
        "cuando la lectura a ficha falla no se dice nada: la pantalla se queda "
        "muda y eso es indistinguible de que la mejora no este desplegada")
    assert "en prosa" in caida, \
        "el aviso no explica que se ha usado el metodo antiguo"


def test_la_pantalla_distingue_el_aviso_de_la_lectura_buena():
    """Pintar el fallo con la misma cara que una lectura correcta seria peor
    que no pintarlo: se leeria como si el plano se hubiera entendido."""
    ruta = os.path.join(os.path.dirname(BACKEND), "frontend", "src", "components",
                        "AIRenderStudio.jsx")
    with open(ruta, encoding="utf-8") as f:
        src = f.read()
    codigo = "\n".join(l.split("//")[0] for l in src.splitlines())
    assert "lecturaEstructurada === false" in codigo, (
        "la pantalla ya no distingue una lectura fallida de una buena: un "
        "respaldo se leera como si el plano se hubiera entendido")
    assert "Lectura del plano incompleta" in codigo, \
        "el aviso de lectura incompleta ha desaparecido de la pantalla"


def test_una_lista_de_medidas_escrita_manda_sobre_las_cotas():
    """La hoja del master lo deja escrito con todas las letras: «BAJOS:
    60+60+60+60+60 cm». Medir las lineas del dibujo pudiendo LEER la lista es
    tirar el dato mas fiable de la hoja."""
    assert "A WRITTEN SCHEDULE BEATS MEASURING THE DRAWING" in LC.PROMPT_LECTURA, (
        "ya no se aprovecha la lista de medidas escrita en la hoja, que es el "
        "dato mas fiable que trae")
    assert "60+60+60+60+60" in LC.PROMPT_LECTURA, \
        "se ha quitado el ejemplo literal de la hoja del master"
    assert "0,6 m" in LC.PROMPT_LECTURA, \
        "ya no se avisa de las medidas escritas en metros"
    assert "ACABADOS" in LC.PROMPT_LECTURA, (
        "el bloque de acabados sugeridos vuelve a poder leerse como si fuera "
        "un modulo mas")
