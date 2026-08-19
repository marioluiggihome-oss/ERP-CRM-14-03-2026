# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del croquis de ARMARIO en el Estudio 3D.

EL FALLO QUE ESTO IMPIDE
------------------------
El Estudio 3D tenía UN solo camino para los croquis y era el de cocina de punta
a punta: la lectura preguntaba por bajos, altos, altillos y columnas; la
transcripción empezaba por «technical KITCHEN blueprint»; y el encargo del
render llevaba mil palabras de cocina —el hueco de la campana sobre la placa,
la encimera que muere contra la columna, el diccionario de Frigo / Combi /
Lavavajillas / Bajo Fregadero—. Con el croquis de un armario delante, todo eso
seguía puesto, y encima una línea suelta diciendo «esto es un armario».

El master mandó un armario de DOS cuerpos con altillo corrido y una cajonera
abajo a la izquierda. Volvió un frente de SEIS módulos, con la cajonera en el
centro y una columna de seis baldas que no estaba dibujada — o sea, la
composición de una cocina. No era el modelo inventando: era que se le había
pedido una cocina.

LO QUE SE PROTEGE
-----------------
1. UN ARMARIO NO VA POR EL CAMINO DE LA COCINA. Y al revés: la cocina, que es
   el pan de cada día, no puede acabar leyéndose con reglas de armario.

2. SE CUENTAN LOS CUERPOS. Es el número que se perdía. La ficha lo dice y el
   encargo lo repite al final, para que el modelo pueda comprobarlo antes de
   dibujar.

3. EL ALTILLO ES UNA BANDA, NO UN CUERPO. La línea horizontal que cruza todo
   por arriba es el maletero corrido; una que se para en un cuerpo es una balda
   de ese cuerpo. Confundirlos cambia el armario entero.

4. LO DE CADA CUERPO SE QUEDA EN SU CUERPO. La cajonera dibujada abajo a la
   izquierda no se va al centro.

5. NO SE INVENTA NI UNA MEDIDA. Sin cotas se dibujan proporciones, pero se
   avisa de que eso NO sirve para presupuestar. Y un ancho deducido del total
   se marca como deducido: no estaba escrito en el papel.

6. LOS MILÍMETROS NO SE CUELAN. El configurador de armarios va en mm y esta
   ficha en cm. Un 2400 de alto son 240 cm; un 240 ya son centímetros y no se
   toca. Convertir por si acaso es cómo se cuela un armario diez veces mayor
   sin que falle nada.

7. EL NÚMERO VA PEGADO A LA PIEZA QUE CUENTA. «3 bank of drawers» se entiende
   como tres cajoneras; lo que hay que escribir es «a bank of 3 drawers». Este
   texto es el encargo que lee el modelo de imagen, no un adorno.

8. QUE LA FICHA FALLE NO PUEDE SER INVISIBLE. Si no se puede leer, la pantalla
   lo dice; si no, uno mira un render malo sacando conclusiones sobre la
   versión equivocada.
"""
import importlib.util
import json
import os

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cargar(ruta, nombre):
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(BACKEND, ruta))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def la():
    return _cargar("services/luiggi_ai/lectura_armario.py", "_lectura_armario")


@pytest.fixture(scope="module")
def ra():
    return _cargar("services/luiggi_ai/render_armario.py", "_render_armario")


def _ficha(**kw):
    """La lectura del croquis del master: 2 cuerpos, altillo, cajonera abajo izq."""
    base = {
        "ancho_total_cm": None, "alto_total_cm": None, "fondo_cm": None,
        "acabados": {"frentes": "", "interior": ""},
        "altillo": {"hay": True, "alto_cm": None, "divisiones": 2},
        "puertas": {"hay": False, "tipo": "", "n": None},
        "cuerpos": [
            {"orden": 1, "ancho_cm": None, "ancho_relativo": 55,
             "interior": [{"tipo": "barra", "n": 1}, {"tipo": "cajones", "n": 3}]},
            {"orden": 2, "ancho_cm": None, "ancho_relativo": 45,
             "interior": [{"tipo": "baldas", "n": 1}, {"tipo": "barra", "n": 1}]},
        ],
        "notas": "",
    }
    base.update(kw)
    return json.dumps(base)


# ─── 1. Cada mueble por su camino ──────────────────────────────────────────

@pytest.mark.parametrize("tipo", ["armario", "vestidor", "ARMARIO", " Armario "])
def test_un_armario_va_por_el_camino_de_armario(ra, tipo):
    assert ra.es_armario(tipo, None) is True, (
        f"«{tipo}» no se reconoce como armario, así que se le pediría al modelo "
        "una cocina con mil palabras de encimeras y campanas")


def test_tambien_lo_detecta_por_el_texto(ra):
    """Si en la pantalla no se eligió tipo, lo dice el texto del encargo."""
    assert ra.es_armario("otro", "fitted/built-in wardrobe (custom closet)") is True
    assert ra.es_armario(None, "walk-in closet with interior shelving") is True


@pytest.mark.parametrize("tipo,espacio", [
    ("cocina", "modern fitted kitchen"),
    (None, "modern fitted kitchen with island"),
    ("bano", "bathroom vanity"),
    ("", ""),
])
def test_una_cocina_no_se_va_por_el_camino_de_armario(ra, tipo, espacio):
    """El pan de cada día no se rompe arreglando el armario."""
    assert ra.es_armario(tipo, espacio) is False, (
        "una cocina acabaría leída como armario: se perderían los altos, la "
        "campana y el diccionario de electrodomésticos")


# ─── 2. Se cuentan los cuerpos ─────────────────────────────────────────────

def test_la_ficha_cuenta_los_cuerpos(la):
    d = la.parsear_lectura(_ficha())
    assert d is not None and len(d["cuerpos"]) == 2
    texto = la.especificacion_en_texto(d)
    assert "EXACTLY 2 cuerpo" in texto, (
        "el encargo no dice cuántos cuerpos hay; sin ese número el render "
        "vuelve a sacar seis módulos de un armario de dos")
    assert "COUNT BEFORE YOU FINISH: 2 cuerpo" in texto, (
        "falta el recuento final, que es lo único que el modelo puede "
        "comprobar antes de dibujar")


def test_un_cuerpo_de_mas_se_ve_en_pantalla(la):
    d = la.parsear_lectura(_ficha())
    assert "Armario de 2 cuerpo" in la.resumen_para_pantalla(d), (
        "la pantalla no dice cuántos cuerpos se han leído; es lo que le deja "
        "al master ver de un vistazo si el fallo está en la lectura")


def test_sin_cuerpos_no_hay_ficha(la):
    """Mejor la lectura de siempre que una ficha vacía."""
    assert la.parsear_lectura(_ficha(cuerpos=[])) is None
    assert la.parsear_lectura("no soy json") is None
    assert la.parsear_lectura("") is None


def test_se_entiende_aunque_venga_envuelto(la):
    """Los modelos envuelven en ```json y se disculpan antes."""
    d = la.parsear_lectura("Aquí tienes:\n```json\n" + _ficha() + "\n```\nEspero que sirva.")
    assert d is not None and len(d["cuerpos"]) == 2


# ─── 3. El altillo es una banda ────────────────────────────────────────────

def test_el_altillo_no_se_cuenta_como_cuerpo(la):
    d = la.parsear_lectura(_ficha())
    texto = la.especificacion_en_texto(d)
    assert "NOT one of the cuerpos" in texto, (
        "el encargo no aclara que el altillo es una banda; contado como cuerpo "
        "cambia el armario entero")
    assert len(d["cuerpos"]) == 2, "el altillo se ha colado en la lista de cuerpos"


def test_sin_altillo_se_dice_que_no_lo_hay(la):
    d = la.parsear_lectura(_ficha(altillo={"hay": False, "alto_cm": None, "divisiones": None}))
    texto = la.especificacion_en_texto(d)
    assert "NO altillo" in texto, (
        "callarse que no hay altillo es una invitación a añadir uno: casi "
        "todos los armarios de catálogo lo llevan")


# ─── 4. Lo de cada cuerpo se queda en su cuerpo ────────────────────────────

def test_cada_cuerpo_lleva_lo_suyo(la):
    d = la.parsear_lectura(_ficha())
    texto = la.especificacion_en_texto(d)
    # Solo la línea de cada cuerpo: el recuento final también nombra cajoneras,
    # y buscar en todo el texto daría por buena una prueba que no mira nada.
    lineas = {n: [l for l in texto.splitlines() if l.strip().startswith(f"{n}. Cuerpo {n}")]
              for n in (1, 2)}
    assert lineas[1] and lineas[2], "los cuerpos no salen numerados de izquierda a derecha"
    assert texto.find(lineas[1][0]) < texto.find(lineas[2][0]), (
        "los cuerpos no salen en orden de izquierda a derecha")
    assert "drawers" in lineas[1][0], (
        "la cajonera del cuerpo 1 no aparece en el cuerpo 1")
    assert "drawers" not in lineas[2][0], (
        "la cajonera se ha copiado al cuerpo 2; así es como acaba en el centro "
        f"del render. Línea: {lineas[2][0]}")
    assert "THIS bay only" in texto, (
        "no se le dice al modelo que el contenido es de ese cuerpo y de ningún otro")


def test_el_encargo_prohibe_anadir_interior(ra):
    p = ra.prompt_croquis_armario(transcripcion="loquesea", brief="")
    assert "NEVER ADD INTERIOR THAT IS NOT DRAWN" in p, (
        "sin esta orden el modelo rellena los cuerpos vacíos con columnas de "
        "baldas y zapateros que nadie ha dibujado")
    assert "IT DOES NOT EXIST" in p


def test_el_encargo_cuenta_las_divisiones_verticales(ra):
    p = ra.prompt_croquis_armario()
    assert "ONE vertical line means TWO bays" in p, (
        "el encargo no explica cómo se cuentan los cuerpos, que es justo lo "
        "que se equivocaba")
    assert "five or six narrow modules" in p, (
        "no se nombra el fallo concreto que hay que evitar; una regla "
        "abstracta se diluye entre las demás")


def test_el_encargo_de_armario_no_arrastra_la_cocina(ra):
    """Ni una palabra de cocina en el encargo de un armario."""
    p = ra.prompt_croquis_armario(transcripcion="x", brief="roble y blanco").lower()
    for palabra in ("kitchen", "countertop", "worktop", "hob", "cooktop", "extractor hood",
                    "fregadero", "campana", "lavavajillas", "frigo", "island"):
        assert palabra not in p, (
            f"el encargo del armario todavía dice «{palabra}»: son las órdenes "
            "contradictorias que hacían que volviera una cocina")


def test_las_puertas_solo_si_estan_dibujadas(la, ra):
    d = la.parsear_lectura(_ficha())
    texto = la.especificacion_en_texto(d)
    assert "render this wardrobe OPEN" in texto, (
        "el croquis enseña el interior y el encargo no lo dice; el render lo "
        "tapa con puertas y no se ve nada de lo diseñado")
    con_puertas = la.parsear_lectura(_ficha(puertas={"hay": True, "tipo": "corredera", "n": 3}))
    assert "OPEN" not in la.especificacion_en_texto(con_puertas)
    assert "corredera" in la.especificacion_en_texto(con_puertas)


# ─── 5. Ni una medida inventada ────────────────────────────────────────────

def test_sin_cotas_se_avisa(la):
    d = la.parsear_lectura(_ficha())
    assert la.sin_cotas(d) is True
    assert "no para presupuestar" in la.resumen_para_pantalla(d), (
        "un dibujo sin una sola medida sale igual de bonito; si no se avisa, "
        "alguien presupuesta sobre proporciones")
    assert "do not invent numbers" in la.especificacion_en_texto(d)


def test_el_ancho_que_falta_se_deduce_y_se_marca(la):
    d = la.parsear_lectura(_ficha(
        ancho_total_cm=240,
        cuerpos=[{"orden": 1, "ancho_cm": 130, "interior": []},
                 {"orden": 2, "ancho_cm": None, "interior": []}]))
    assert d["cuerpos"][1]["ancho_cm"] == 110
    assert d["cuerpos"][1].get("ancho_deducido") is True, (
        "el ancho deducido no se marca; en pantalla parecería una medida "
        "escrita en el papel")
    assert "deducido" in la.resumen_para_pantalla(d)


def test_con_dos_anchos_que_faltan_no_se_reparte(la):
    """Dos incógnitas y una ecuación: repartir a partes iguales es inventar."""
    d = la.parsear_lectura(_ficha(
        ancho_total_cm=240,
        cuerpos=[{"orden": 1, "ancho_cm": None, "interior": []},
                 {"orden": 2, "ancho_cm": None, "interior": []}]))
    assert all(c["ancho_cm"] is None for c in d["cuerpos"]), (
        "se han repartido los anchos a ojo; eso es dinero viajando sobre una "
        "medida inventada")


def test_con_dos_que_faltan_el_resto_no_se_le_da_al_primero(la):
    """El caso que de verdad hace daño: UNO escrito y DOS sin escribir.

    Es el que se cuela solo, porque hay un ancho conocido y la resta «sale».
    Pero ese resto es de los DOS cuerpos que faltan, no del primero de ellos:
    dárselo entero es inventarle 140 cm a un cuerpo y dejar el otro en blanco.
    """
    d = la.parsear_lectura(_ficha(
        ancho_total_cm=240,
        cuerpos=[{"orden": 1, "ancho_cm": 100, "interior": []},
                 {"orden": 2, "ancho_cm": None, "interior": []},
                 {"orden": 3, "ancho_cm": None, "interior": []}]))
    assert d["cuerpos"][1]["ancho_cm"] is None and d["cuerpos"][2]["ancho_cm"] is None, (
        "se le ha dado a un cuerpo el resto que era de dos: "
        f"{[c['ancho_cm'] for c in d['cuerpos']]}")


def test_si_los_anchos_no_cuadran_se_avisa(la):
    d = la.parsear_lectura(_ficha(
        ancho_total_cm=240,
        cuerpos=[{"orden": 1, "ancho_cm": 200, "interior": []},
                 {"orden": 2, "ancho_cm": 150, "interior": []}]))
    assert d["avisos"], (
        "los cuerpos suman 350 y el total dice 240, y no se dice nada: nada se "
        "corrige en silencio")


# ─── 6. Los milímetros no se cuelan ────────────────────────────────────────

@pytest.mark.parametrize("entra,sale", [(2400, 240.0), (240, 240.0), (2000, 200.0)])
def test_el_alto_en_milimetros_se_pasa_a_centimetros(la, entra, sale):
    d = la.parsear_lectura(_ficha(alto_total_cm=entra))
    assert d["alto_total_cm"] == sale, (
        f"{entra} de alto ha salido como {d['alto_total_cm']}; el "
        "configurador va en mm y esta ficha en cm")


def test_un_alto_normal_no_se_divide(la):
    """220 cm es un armario alto. 22 cm no es nada."""
    d = la.parsear_lectura(_ficha(alto_total_cm=220))
    assert d["alto_total_cm"] == 220.0


# ─── 7. El número va pegado a la pieza ─────────────────────────────────────

def test_tres_cajones_no_son_tres_cajoneras(la):
    d = la.parsear_lectura(_ficha())
    en = la.especificacion_en_texto(d)
    assert "a bank of 3 drawers" in en, (
        "pone «3 bank of drawers», que se entiende como TRES cajoneras y el "
        "modelo dibuja tres")
    es = la.resumen_para_pantalla(d)
    assert "cajonera de 3 cajones" in es, f"en pantalla pone: {es}"


def test_una_sola_balda_no_va_en_plural(la):
    d = la.parsear_lectura(_ficha())
    assert "1 shelf" in la.especificacion_en_texto(d)
    assert "1 balda" in la.resumen_para_pantalla(d)


# ─── 8. Que falle no puede ser invisible ───────────────────────────────────

def test_el_render_avisa_cuando_no_hay_ficha():
    ruta = os.path.join(BACKEND, "services", "luiggi_ai", "render_3d.py")
    with open(ruta, encoding="utf-8") as f:
        codigo = f.read()
    i = codigo.find("_render_croquis_de_armario(self")
    assert i != -1, "ha desaparecido el camino de armario del Estudio 3D"
    trozo = codigo[i:i + 4000]
    assert 'parsed_params["lecturaEstructurada"] = False' in trozo, (
        "si la ficha falla no se marca; desde fuera se ve igual que si la "
        "mejora no estuviera desplegada")
    assert "No se ha podido leer el armario a ficha" in trozo, (
        "el aviso no llega a la pantalla")


def test_el_armario_tambien_recorta_el_dibujo():
    """El master dibuja con el dedo en una app llena de barras y paletas."""
    ruta = os.path.join(BACKEND, "services", "luiggi_ai", "render_3d.py")
    with open(ruta, encoding="utf-8") as f:
        codigo = f.read()
    i = codigo.find("_render_croquis_de_armario(self")
    trozo = codigo[i:i + 4000]
    assert "recortar_dibujo_base64" in trozo, (
        "el croquis de armario ya no se recorta de la página: el armario "
        "vuelve a ocupar un tercio de la imagen y el detalle no se ve")


# ─── 9. Lo que él escribe AYUDA A LEER el dibujo ───────────────────────────
#
# Su descripción decía, sin margen de duda: «altillo de una sola puerta que
# abarca todo el ancho», «dividido en dos módulos asimétricos», «el de la
# izquierda de mayor anchura y 3 cajones», «el de la derecha más estrecho, con
# baldas». Todo eso se archivaba bajo el epígrafe FINISHES del encargo del
# render —o sea, se tiraba— mientras el dibujo se leía a ciegas. Salieron seis
# módulos. Dos pérdidas apiladas: el texto no llegaba a la lectura, y la
# lectura era de cocina.

BRIEF = ("La parte superior es un altillo o maletero de una sola puerta que abarca todo el "
         "ancho. Debajo, dividido en dos módulos asimétricos: uno a la izquierda de mayor "
         "anchura y 3 cajones, y otro a la derecha más estrecho con baldas. Laca blanca mate "
         "sin tiradores visibles.")


def test_lo_escrito_llega_a_quien_lee_el_dibujo(la):
    p = la.prompt_lectura(BRIEF)
    assert BRIEF in p, (
        "lo que el master escribe no le llega a quien lee el dibujo. Un dibujo "
        "hecho con el dedo es ambiguo; quien lo dibujó ya ha contestado por "
        "escrito a esa ambigüedad")
    assert "HELP to read the drawing" in p


def test_sin_texto_el_encargo_de_lectura_no_cambia(la):
    """Nadie está obligado a escribir nada."""
    assert la.prompt_lectura("") == la.PROMPT_LECTURA
    assert la.prompt_lectura(None) == la.PROMPT_LECTURA


def test_el_texto_no_puede_meter_medidas_ni_muebles(la):
    p = la.prompt_lectura(BRIEF)
    assert "NEVER take a measurement from this text that is not on the drawing" in p, (
        "el texto podría colar una medida que no está en el papel: eso es "
        "dinero viajando sobre una medida inventada")
    assert "never add a cuerpo or a piece that is not drawn" in p


def test_si_el_texto_y_el_dibujo_se_pelean_gana_el_dibujo(la):
    p = la.prompt_lectura(BRIEF)
    assert "TRUST THE DRAWING" in p, (
        "sin esta regla, un texto viejo pegado de otro presupuesto mandaría "
        "sobre el croquis que se acaba de dibujar")
    assert "notas" in p.split("TRUST THE DRAWING")[1], (
        "la contradicción se resolvería en silencio; tiene que salir en pantalla")


def test_lo_que_el_escribe_ya_no_se_archiva_como_acabado(ra):
    p = ra.prompt_croquis_armario(transcripcion="(ficha)", brief=BRIEF)
    assert "this is the ONLY thing the text decides" not in p, (
        "la descripción del master vuelve a entrar entera bajo el epígrafe "
        "FINISHES: «dos módulos asimétricos» y «3 cajones» no son acabados")
    assert "CONFIRMS the specification above" in p, (
        "cuando el texto y el dibujo dicen lo mismo hay que decir que "
        "coinciden, no degradar el texto a decoración")
    assert "The GEOMETRY comes 100% from the drawing" in p, (
        "se ha perdido la regla de que manda el dibujo; existe porque la "
        "pantalla mandaba sus valores por defecto («En L», «Cuarzo Blanco») "
        "contradiciendo el croquis")


def test_sin_texto_no_se_promete_un_texto_que_no_hay(ra):
    p = ra.prompt_croquis_armario(transcripcion="(ficha)", brief="")
    assert "No text was written" in p
    assert "The text:" not in p, (
        "se anuncia un texto vacío; una orden en blanco es una invitación a "
        "rellenarla")


def test_el_render_le_pasa_el_texto_a_la_lectura():
    import os
    ruta = os.path.join(BACKEND, "services", "luiggi_ai", "render_3d.py")
    with open(ruta, encoding="utf-8") as f:
        codigo = f.read()
    i = codigo.find("_render_croquis_de_armario(self")
    trozo = codigo[i:i + 4000]
    assert "_leer_armario_del_dibujo(ref_b64, ref_mime, brief_txt)" in trozo, (
        "el Estudio 3D vuelve a leer el dibujo sin lo que el master escribió")
    j = codigo.find("async def _leer_armario_del_dibujo")
    lector = codigo[j:j + 1500]
    assert "prompt_lectura(brief)" in lector, (
        "el lector recibe el texto y no lo usa, que es peor que no recibirlo: "
        "parece arreglado y no lo está")


# ─── 10. El render del CONFIGURADOR: las puertas son todo el frente ────────
#
# El master encargó DOS PUERTAS ABATIBLES en un armario de 1000 mm. Volvió una
# puerta abatible abierta a la izquierda, un panel cerrado en el centro que
# encima parecía corredera, y un tercio del armario a la derecha CON LA
# ESTANTERÍA A LA VISTA Y SIN PUERTA NINGUNA. Por dentro, cuatro o cinco
# columnas de baldas donde había dos módulos.
#
# El encargo decía «EXACTLY 2 doors» y describía el interior, pero en ninguna
# parte decía que esas dos puertas son TODO el frente. Sin esa frase, «dos
# puertas» se cumple poniendo dos puertas donde sea y dejando el resto abierto.

def test_las_puertas_cubren_todo_el_frente(ra):
    r = ra.reglas_de_puertas_y_cuerpos(2, 2, "hinged", 1000)
    assert "1000mm from the left edge to the right edge" in r, (
        "no se dice que las puertas abarcan el ancho entero; «2 puertas» se "
        "cumple poniéndolas donde sea")
    assert "NO part of the front left uncovered" in r
    assert "NEVER render an open, doorless shelving bay" in r, (
        "falta la prohibición del hueco sin puerta, que es literalmente lo que "
        "salió")


def test_abrir_una_puerta_no_la_borra(ra):
    r = ra.reglas_de_puertas_y_cuerpos(3, 3, "sliding", 2400)
    assert "It does not delete the door" in r, (
        "sin esto, la puerta abierta se convierte en un hueco de estantería "
        "permanente y el armario pierde una hoja")


@pytest.mark.parametrize("tipo,no_debe", [
    ("hinged", "sliding panels"),
    ("sliding", "hinged doors"),
    ("folding", "sliding panels"),
])
def test_no_se_mezclan_tipos_de_puerta(ra, tipo, no_debe):
    r = ra.reglas_de_puertas_y_cuerpos(2, 2, tipo, 1000)
    assert "SAME TYPE" in r and no_debe in r, (
        f"con puertas «{tipo}» no se prohíbe meter {no_debe}; salió una "
        "abatible y una corredera en el mismo armario")


@pytest.mark.parametrize("cuerpos,divisores", [(1, 0), (2, 1), (4, 3)])
def test_se_cuentan_los_cuerpos_y_sus_divisores(ra, cuerpos, divisores):
    r = ra.reglas_de_puertas_y_cuerpos(2, cuerpos, "hinged", 1000)
    assert f"EXACTLY {cuerpos} vertical bay" in r
    assert f"{divisores} full-height vertical divider" in r, (
        f"{cuerpos} cuerpos llevan {divisores} divisores; si la cuenta no "
        "cuadra, el modelo mete los que le parezca")
    assert f"Count them before you finish: {cuerpos}" in r, (
        "falta el recuento final, que es lo único comprobable antes de dibujar")


def test_el_render_del_configurador_usa_estas_reglas():
    ruta = os.path.join(BACKEND, "routes", "armarios.py")
    with open(ruta, encoding="utf-8") as f:
        codigo = f.read()
    assert "reglas_de_puertas_y_cuerpos(" in codigo, (
        "el render del configurador de Armarios ya no usa las reglas del "
        "frente; vuelve a poder salir un armario con un lado sin puerta")
    assert "{reglas_frente}" in codigo, (
        "las reglas se calculan y no se meten en el encargo: parece arreglado "
        "y no lo está")
    # El bloque de verdad, no la mención a «DOORS - CRITICAL» que hay dentro
    # del texto del plano: buscando la primera aparición se medía desde el
    # sitio equivocado y la prueba se quejaba de un código que estaba bien.
    i = codigo.find("DOORS - CRITICAL - PAY ATTENTION:")
    j = codigo.find("{reglas_frente}", i)
    assert i != -1, "ha desaparecido el bloque de PUERTAS del encargo"
    assert j != -1 and j - i < 700, (
        "las reglas del frente se han separado del bloque de PUERTAS; juntas "
        "se leen como una sola orden")


# ─── 11. El lápiz del plano no se pinta en la foto ─────────────────────────
#
# El master pidió el armario CERRADO y en la foto salió, pintada encima, una
# línea ROJA DISCONTINUA con el rótulo «Puerta 2» en rojo y una «M2» arriba:
# las anotaciones del plano esquemático que se manda como referencia, copiadas
# literalmente dentro de la fotografía. Y encima media fachada abierta.
#
# No fue el modelo desobedeciendo. Se le da un dibujo técnico y se le dice
# «reprodúcelo EXACTAMENTE»; nadie le había dicho qué parte de ese dibujo es el
# mueble y cuál es el lápiz del delineante.

def test_la_anotacion_no_se_renderiza(ra):
    r = ra.reglas_del_plano_esquematico()
    assert "NEVER RENDER IT" in r, (
        "no se prohíbe pintar la anotación: vuelven las líneas rojas y los "
        "rótulos dentro de la foto")
    for pieza in ("dimension lines", "dashed", "labels", "no text", "no digits"):
        assert pieza in r, f"la anotación «{pieza}» no se nombra, y lo que no se nombra se copia"


def test_se_nombra_el_fallo_concreto(ra):
    r = ra.reglas_del_plano_esquematico()
    assert "'Puerta 1'" in r and "M1" in r, (
        "una regla abstracta sobre «anotaciones» se diluye; hay que nombrar "
        "los rótulos que de verdad salieron pintados")
    assert "red dashed line" in r


def test_los_colores_del_plano_no_son_los_acabados(ra):
    r = ra.reglas_del_plano_esquematico()
    # Se comprueban las DOS mitades de la frase. Mirando solo el final,
    # borrando la primera línea la prueba seguía en verde: la regla estaba
    # medio rota y no se enteraba.
    assert "colours are notation too" in r, (
        "no se dice que los colores del plano también son lápiz")
    assert "never the finishes" in r, (
        "el ámbar del maletero o el rojo de las puertas acabarían siendo el "
        "color del mueble")


def test_con_todo_cerrado_no_se_ve_nada_del_interior(ra):
    r = ra.reglas_de_puertas_y_cuerpos(2, 2, "hinged", 1000, todas_cerradas=True)
    assert "ALL 2 DOORS ARE CLOSED" in r
    assert "exactly what must be HIDDEN" in r, (
        "el plano se dibuja con las puertas transparentes; sin decir que eso "
        "es justo lo que hay que tapar, sale media fachada abierta")
    assert "not one shelf, rail, drawer or garment visible" in r


def test_con_una_puerta_abierta_no_se_manda_cerrar_todo(ra):
    """La orden de cerrar todo solo aparece cuando se ha pedido cerrado."""
    r = ra.reglas_de_puertas_y_cuerpos(2, 2, "hinged", 1000, todas_cerradas=False)
    assert "ALL 2 DOORS ARE CLOSED" not in r, (
        "se manda cerrar todo cuando el master ha pedido una puerta abierta")


def test_el_render_del_configurador_avisa_de_la_anotacion():
    ruta = os.path.join(BACKEND, "routes", "armarios.py")
    with open(ruta, encoding="utf-8") as f:
        codigo = f.read()
    assert "reglas_del_plano_esquematico()" in codigo, (
        "el render del configurador ya no distingue mueble de anotación")
    assert "{reglas_plano}" in codigo, (
        "la regla se calcula y no se mete en el encargo")
    assert "todas_cerradas=not doors_open" in codigo, (
        "el encargo ya no sabe si se han pedido las puertas cerradas")


# El plano que se manda como referencia no puede llevar letras ni rojo: lo que
# no está en el dibujo no se puede copiar. La regla de arriba es el cinturón;
# esto son los tirantes.
def test_el_plano_de_referencia_no_lleva_letras_ni_rojo():
    ruta = os.path.join(
        os.path.dirname(BACKEND), "frontend", "src", "components", "Armarios.jsx")
    if not os.path.exists(ruta):
        pytest.skip("Armarios.jsx no está en este entorno")
    with open(ruta, encoding="utf-8") as f:
        jsx = f.read()
    i = jsx.find("const generateBlueprintDataUrl")
    j = jsx.find("canvas.toDataURL('image/png')", i)
    assert i != -1 and j != -1, "ha desaparecido el plano de referencia para la IA"
    plano = jsx[i:j]
    assert "fillText" not in plano, (
        "el plano que se manda a la IA vuelve a llevar rótulos; el modelo los "
        "pinta dentro de la foto")
    assert "#dc2626" not in plano, (
        "vuelve el rojo al plano: una línea roja discontinua se lee como "
        "anotación y sale pintada encima del mueble")
    assert "setLineDash" not in plano, (
        "vuelven las líneas discontinuas, que es exactamente lo que salió "
        "cruzando la fotografía")
