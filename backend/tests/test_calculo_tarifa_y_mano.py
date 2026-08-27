# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO de la relacion de muebles: TARIFA, MANO Y HOLGURA.

1. LA TARIFA NO PUEDE ESTAR ESCRITA A FUEGO. La pantalla pedia siempre T1, la
   MAS BARATA, aunque la cocina fuera un ZENIT (T4) o un FENIX (T5). No daba
   ningun error: daba un presupuesto barato. Y hay 21 tarifas.

2. UN CODIGO QUE ACABA EN «D/I» ES UNA PUERTA SIN MANO DECIDIDA. Si sale asi
   hacia el taller, la decide el taller: acierta la mitad de las veces, y la
   otra mitad es un frente desmontado y vuelto a taladrar en casa del cliente.
   Se decide donde se sabe, que es delante del plano.

3. UNA PUERTA NO MIDE LO QUE EL HUECO. Se le quita la junta, o roza con la de al
   lado y no cierra. Son los mismos milimetros que en Cocina Montada y los que
   dio el master: 2 mm de alto y 3 de ancho. Pedirla a la medida exacta del
   hueco es pedirla mal, y no se ve hasta que llega.
"""
import json
import os
import re

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(RAIZ, "frontend", "src")
REVIEW = os.path.join(SRC, "components", "RelacionReview.jsx")
IMPORTADOR = os.path.join(SRC, "components", "ProformaImporter.jsx")
CASCOS_PY = os.path.join(RAIZ, "backend", "routes", "cascos.py")
MV_JSON = os.path.join(RAIZ, "backend", "data", "mv_tarifas_oficiales.json")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


# ─── 1. La tarifa se elige ──────────────────────────────────────────────────

def test_la_tarifa_ya_no_esta_escrita_a_fuego():
    """CANDADO PRINCIPAL."""
    src = _leer(REVIEW)
    assert "tariff=T1" not in src, (
        "la relacion de muebles vuelve a pedir SIEMPRE la tarifa T1: se "
        "presupuestaria todo a la mas barata aunque la cocina sea otra cosa, y "
        "sin dar ningun error")
    assert "setTarifa" in src, "no hay forma de elegir el grupo de precios"


def test_al_cambiar_de_tarifa_se_recalcula_lo_ya_metido():
    """Dejar los muebles con el precio de la tarifa anterior daria un
    presupuesto MEZCLADO: unas lineas a un precio y otras a otro."""
    src = _leer(REVIEW)
    assert "puntosLocal(m, m.alto" in src, (
        "al cambiar de tarifa no se recalculan los muebles ya aniadidos")
    # Y se revaloran con la MISMA funcion que todo lo demas. Aqui hubo una copia
    # de la formula del precio y las dos ya se habian separado: una miraba
    # `m.alto` y la otra se inventaba un alto por defecto, o sea que el mismo
    # mueble valia una cosa u otra segun por donde se hubiera valorado.
    i = src.index("setTodasTarifasData(prev =>")   # el efecto, no el useState
    cuerpo = src[i:i + 900]
    assert "puntosLocal(" in cuerpo, (
        "al cambiar de tarifa se vuelve a valorar con una copia de la formula "
        "en vez de con `puntosLocal`: las dos copias acabaran diciendo cosas "
        "distintas del mismo mueble")


def test_hay_endpoint_que_lista_las_tarifas_con_sus_acabados():
    """Nadie dice «esta cocina es una T4», dice «esta cocina es ZENIT»."""
    src = _leer(CASCOS_PY)
    assert '@router.get("/cascos/mv/tarifas")' in src
    i = src.index('@router.get("/cascos/mv/tarifas")')
    cuerpo = src[i:i + 2000]
    assert "acabados" in cuerpo
    assert '_es_master' in cuerpo, "la tarifa es informacion de coste: solo master"


def test_los_incrementos_no_se_cuelan_como_acabados():
    """`_inc` son incrementos (metalizado, difuminado), no acabados: en la
    lista de elegir serian una opcion que no se puede elegir."""
    src = _leer(CASCOS_PY)
    i = src.index('@router.get("/cascos/mv/tarifas")')
    cuerpo = src[i:i + 2000]
    assert 'startswith("_")' in cuerpo


def test_las_21_tarifas_estan_en_el_fichero():
    """Si alguna desapareciera, el desplegable se quedaria corto sin avisar."""
    with open(MV_JSON, encoding="utf-8") as f:
        data = json.load(f)
    tarifas = set(data.get("tariffs", {}))
    assert len(tarifas) == 21, f"hay {len(tarifas)} tarifas, se esperaban 21"
    for n in range(1, 22):
        assert f"T{n}" in tarifas, f"falta la tarifa T{n}"


def test_el_acabado_ZENIT_sigue_siendo_T4():
    """Un ejemplo real: si el mapa de acabados cambiara, el comercial elegiria
    la tarifa equivocada creyendo que acierta."""
    with open(MV_JSON, encoding="utf-8") as f:
        data = json.load(f)
    acabados = data["_meta"]["acabados"]
    assert "ZENIT" in acabados["T4"]
    assert "ECO" in acabados["T1"]


# ─── 2. La mano de la puerta ────────────────────────────────────────────────

def test_se_puede_decidir_la_mano_en_la_linea():
    """CANDADO. Un «AV30D/I» sin decidir llega al taller y lo decide el taller.

    La decision se toma linea a linea (`rotarMano`, que va girando D -> I ->
    D/I con un toque, que es lo que se puede hacer en una tablet) o de golpe
    para las que queden sin decidir (`fijarTodasManos`)."""
    src = _leer(REVIEW)
    assert "manoDe" in src, "ya no se sabe si una linea lleva mano o no"
    assert "rotarMano" in src and "fijarTodasManos" in src, (
        "no se puede decidir la mano: los codigos salen como D/I y la mano la "
        "acaba eligiendo quien fabrica")


@pytest.mark.parametrize("funcion", ["const rotarMano", "const fijarTodasManos"])
def test_la_mano_cambia_SOLO_el_sufijo_del_codigo(funcion):
    """El resto del codigo es el mueble. Tocarlo seria cambiar de mueble."""
    src = _leer(REVIEW)
    i = src.index(funcion)
    cuerpo = src[i:i + 500]
    assert "replace(/(D\\/I|D|I)$/i" in cuerpo or "replace(/(D\\/I)$/i" in cuerpo, (
        f"«{funcion}» ya no toca solo el sufijo: esta cambiando el codigo del "
        f"mueble, o sea pidiendo otro mueble")


def test_el_precio_no_se_congela_al_decidir_la_mano():
    """CANDADO DE DINERO. En la tarifa el codigo lleva la mano SIN decidir
    («AE60D/I»). En cuanto se decide («AE60D») ese codigo ya no existe en la
    tarifa: buscando solo por el codigo de la linea no se encuentra nada, se
    devuelve el precio anterior y la linea se queda con la tarifa vieja.

    No da ningun error. Da un presupuesto mezclado: unas lineas a una tarifa y
    otras a otra. Salio cuando el master pregunto «de donde sacas este valor»."""
    src = _leer(REVIEW)
    i = src.index("const puntosLocal")
    cuerpo = src[i:i + 900]
    assert "baseCod" in cuerpo, (
        "al valorar se busca solo por el codigo con la mano ya decidida: no se "
        "encuentra en la tarifa y el precio se queda congelado")


def test_se_avisa_antes_de_volcar_con_manos_sin_decidir():
    """Despues de volcarlo ya no se mira; hay que decirlo antes."""
    src = _leer(REVIEW)
    assert "sinMano" in src
    i = src.index("const confirmar")
    cuerpo = src[i:i + 900]
    assert "sinMano" in cuerpo and "confirm" in cuerpo


def test_una_mano_sin_decidir_no_se_imprime_como_izquierda():
    """CANDADO. `'AV30D/I'.endsWith('I')` es CIERTO. Con esa comprobacion, una
    puerta SIN mano decidida salia impresa —y copiada al WhatsApp— como «Izq»:
    el taller la fabricaba a la izquierda sin que nadie lo hubiera decidido, y
    en el papel no habia ni rastro de que estuviera sin decidir.

    La mano se lee con `manoDe`, que distingue las TRES situaciones: sin mano,
    sin decidir y decidida."""
    # Se mira el CODIGO, no los comentarios: «endsWith» aparece a proposito en
    # las notas que explican por que NO se usa.
    codigo = "\n".join(l.split("//")[0] for l in _leer(REVIEW).splitlines())
    for sufijo in ("D", "I"):
        for comilla in ("'", '"'):
            assert f"endsWith({comilla}{sufijo}{comilla})" not in codigo, (
                "se vuelve a leer la mano con `endsWith`: «D/I» acaba en «I» y "
                "una puerta sin decidir se dara por izquierda")


def test_la_observacion_sale_impresa_y_no_solo_en_pantalla():
    """El master la pidio «para que salga al imprimir el presupuesto». Una
    observacion que solo se ve en pantalla no le sirve a quien fabrica."""
    src = _leer(REVIEW)
    i = src.index("const filasHtml")
    cuerpo = src[i:i + 2000]
    assert "m.nota" in cuerpo, (
        "la observacion de la linea no se imprime: se escribe y se queda en la "
        "pantalla, que es justo lo que no se pidio")


def test_la_regla_del_sufijo_reconoce_los_codigos_reales():
    """Con los codigos que salieron en las capturas del master."""
    patron = re.compile(r"(D/I|D|I)$")
    assert patron.search("AV30D/I").group(1) == "D/I"    # sin decidir
    assert patron.search("BF60D/I").group(1) == "D/I"
    assert patron.search("BF60D").group(1) == "D"        # decidida a la derecha
    assert patron.search("BF60I").group(1) == "I"
    assert patron.search("B90") is None                  # no lleva mano
    assert patron.search("BCG60") is None


# ─── 3. La observacion por linea ────────────────────────────────────────────

def test_cada_linea_puede_llevar_una_observacion():
    src = _leer(REVIEW)
    assert "setNota" in src, "no se puede escribir una observacion por linea"
    i = src.index("const confirmar")
    cuerpo = src[i:i + 900]
    assert "nota:" in cuerpo, (
        "la observacion no viaja al presupuesto: se escribe y se pierde al "
        "volcar, que es peor que no poder escribirla")


# ─── 4. La holgura de la puerta ─────────────────────────────────────────────

def test_la_holgura_es_la_de_la_casa_y_se_puede_cambiar():
    src = _leer(IMPORTADOR)
    m_alto = re.search(r"const HOLGURA_ALTO_MM = (\d+)", src)
    m_ancho = re.search(r"const HOLGURA_ANCHO_MM = (\d+)", src)
    assert m_alto and int(m_alto.group(1)) == 2, "el master dijo 2 mm de alto"
    assert m_ancho and int(m_ancho.group(1)) == 3, "el master dijo 3 mm de ancho"
    assert "setHolgura" in src, "no se puede cambiar en pantalla"


def test_la_holgura_se_quita_de_la_medida_de_PEDIDO():
    """Y el area se calcula con la del HUECO, que es lo que se ocupa y se paga.
    Confundirlas hace que la puerta se pida bien y se cobre mal, o al reves."""
    src = _leer(IMPORTADOR)
    i = src.index("puertasDelMueble = {")
    cuerpo = src[i:i + 500]
    assert "holgura.ancho" in cuerpo and "holgura.alto" in cuerpo
    # El area sigue saliendo del hueco, sin holgura.
    j = src.index("puertaDeLinea = (anchoM / 1000)")
    assert "holgura" not in src[j:j + 200], (
        "se esta cobrando el area con la holgura quitada: la puerta ocupa el "
        "hueco entero, y es lo que se paga")


def test_los_mismos_milimetros_que_cocina_montada():
    """Si en un sitio se pide con 2/3 y en el otro con otra cosa, la misma
    cocina sale con puertas de dos medidas."""
    esquemas = _leer(os.path.join(RAIZ, "backend", "models", "schemas.py"))
    assert "doorToleranceHeight: float = 2" in esquemas
    assert "doorToleranceWidth: float = 3" in esquemas
