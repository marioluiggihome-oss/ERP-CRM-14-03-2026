# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
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
