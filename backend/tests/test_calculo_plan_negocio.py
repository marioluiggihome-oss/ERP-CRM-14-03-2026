# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del plan de negocio: QUE UN PLAN A MEDIAS NO PAREZCA UN PLAN BUENO.

Un plan de negocio con las casillas a medio rellenar es el documento mas
peligroso que puede salir de este ERP. No falla, no avisa, y se ensenia a un
banco o a un socio. Por eso todo lo que se protege aqui va en la misma
direccion: que lo que no se sabe SE NOTE.

1. UN HUECO NO ES UN CERO. Un casco a 0 € no es un casco regalado, es una
   casilla vacia — y colada en el coste da un margen del 100 %, un punto de
   equilibrio de cero muebles y un plan precioso que es mentira. Lo que no se
   sabe vale None, y todo lo que dependa de ello vale None.

2. NO SE SUMA «LO QUE HAY». Un coste con tres partidas de ocho no es un coste
   bajo: es un coste desconocido. Sumarlo da un margen que no existe.

3. EL MARGEN VA SOBRE EL PRECIO DE VENTA, no sobre el coste. Un mueble que
   cuesta 100 y se vende a 150 deja un 33 %, no un 50 %. Confundirlos infla el
   plan entero.

4. LA CAPACIDAD DE 3 Y 4 PERSONAS ES UN DATO QUE SE MIDE. Suponer que tres
   rinden un 50 % mas que dos es justo el numero inventado que hunde un plan.

5. EL PLAN DICE LO QUE LE FALTA. Un plan que no lo dice se lee como si
   estuviera terminado.

6. SI NO SE SOSTIENE, SE DICE. Cuando hay que vender mas de lo que se puede
   fabricar, la respuesta no es un numero grande: es que asi NO sale.
"""
import importlib.util
import os

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def pn():
    ruta = os.path.join(BACKEND, "services", "plan_negocio.py")
    spec = importlib.util.spec_from_file_location("_plan_negocio", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# La fabrica que describio el master: 2 personas, 3 muebles/hora conjuntos,
# 7 h/dia, L-V, 1.600 horas productivas al anio.
CAPACIDAD = {"personas": 2, "mueblesHora": 3, "horasDia": 7, "diasSemana": 5,
             "horasAno": 1600, "costeHoraPersona": 18}

# Una referencia con TODAS sus partidas. Los importes son de prueba, no de
# Alemar: aqui se comprueban las cuentas, no los precios.
def _ref(nombre="Bajo 60", **cambios):
    base = {"nombre": nombre, "casco": 40, "bisagras": 3, "guias": 8,
            "patasZocalo": 4, "otrosHerrajes": 2, "componentes": 6,
            "embalaje": 2, "otrosDirectos": 1,
            "precioB2B": 120, "precioB2C": 180}
    base.update(cambios)
    return base


# ─── 0. El coste se puede dar de dos formas ─────────────────────────────────

def test_un_solo_numero_por_mueble_basta(pn):
    """Es como se empieza de verdad: se sabe lo que cuesta el mueble entero y
    todavia no como se reparte. Pedir ocho partidas para poder calcular nada es
    la forma segura de que el plan se quede vacio."""
    r = pn.coste_referencia({"nombre": "Bajo 60", "costeMaterialesMueble": 66}, mano_obra=12)
    assert r["materiales"] == 66
    assert r["costeDirecto"] == 78
    assert r["fuente"] == "por_mueble"
    assert r["faltan"] == []


def test_el_numero_por_mueble_MANDA_sobre_el_desglose(pn):
    """CANDADO. Sumar los dos contaria el material dos veces. Y mezclar en
    silencio dos fuentes que no cuadran es peor que no tener ninguna."""
    r = pn.coste_referencia(_ref(costeMaterialesMueble=80), mano_obra=12)
    assert r["materiales"] == 80, "el desglose suma 66; tiene que ganar el 80 escrito a mano"
    assert r["costeDirecto"] == 92
    assert r["fuente"] == "por_mueble"


def test_el_desglose_se_guarda_aunque_no_se_use(pn):
    """Lo escrito no se pierde por cambiar de forma de contar."""
    r = pn.coste_referencia(_ref(costeMaterialesMueble=80), mano_obra=12)
    assert r["partidas"]["casco"] == 40


def test_el_coste_por_mueble_NO_lleva_mano_de_obra_dentro(pn):
    """Si la llevara, se contaria dos veces: la fabrica ya la calcula sola."""
    r = pn.coste_referencia({"nombre": "X", "costeMaterialesMueble": 66}, mano_obra=12)
    assert r["materiales"] == 66 and r["manoObra"] == 12 and r["costeDirecto"] == 78


def test_sin_ninguna_de_las_dos_formas_se_pide_UNA_cosa_no_ocho(pn):
    """Decir «faltan ocho partidas» cuando no se ha empezado a rellenar es
    ruido: lo que falta es el coste."""
    r = pn.coste_referencia({"nombre": "Bajo 60"}, mano_obra=12)
    assert r["costeDirecto"] is None
    assert r["faltan"] == ["costeMaterialesMueble"]


# ─── 1. Un hueco no es un cero ──────────────────────────────────────────────

def test_un_coste_por_mueble_a_cero_no_es_un_mueble_gratis(pn):
    """CANDADO PRINCIPAL. Con `_num` a secas, un 0 pasaba por precio y el
    margen salia del 100 %."""
    r = pn.coste_referencia({"nombre": "X", "costeMaterialesMueble": 0}, mano_obra=12)
    assert r["costeDirecto"] is None


def test_un_casco_a_cero_no_es_un_casco_gratis(pn):
    """Lo mismo, yendo por el desglose."""
    r = pn.coste_referencia(_ref(casco=0), mano_obra=12)
    assert r["costeDirecto"] is None
    assert "casco" in r["faltan"]


def test_una_casilla_vacia_tampoco(pn):
    for vacio in (None, ""):
        r = pn.coste_referencia(_ref(bisagras=vacio), mano_obra=12)
        assert r["costeDirecto"] is None and "bisagras" in r["faltan"]


def test_sin_coste_por_hora_no_hay_mano_de_obra(pn):
    c = pn.capacidad({**CAPACIDAD, "costeHoraPersona": None})
    assert c["manoObraPorMueble"] is None
    assert c["capacidadAnual"] == 4800, "la capacidad SI se sabe: no depende del sueldo"


def test_un_gasto_de_estructura_a_CERO_si_vale(pn):
    """La regla del cero es para PRECIOS. Un alquiler de 0 € es un dato: la nave
    es propia. Tratarlo como hueco impediria cerrar un plan correcto."""
    r = pn.calcular({"capacidad": CAPACIDAD, "referencias": [_ref()],
                     "estructura": {"alquiler": 0, "salarios": 60000},
                     "b2c": {c: 0 for c in pn.COSTES_B2C}, "repartoB2B": 1})
    assert r["estructura"]["total"] == 60000


# ─── 2. No se suma «lo que hay» ─────────────────────────────────────────────

def test_un_coste_a_medias_no_es_un_coste_bajo(pn):
    """CANDADO. Sumar solo las partidas rellenas da un coste pequenio y un
    margen enorme: el error mas caro que puede tener un plan."""
    a_medias = {"nombre": "Bajo 60", "casco": 40, "bisagras": 3}
    r = pn.coste_referencia(a_medias, mano_obra=12)
    assert r["materiales"] is None and r["costeDirecto"] is None
    assert len(r["faltan"]) == 6


def test_una_estructura_a_medias_no_da_total(pn):
    b = pn._suma_bloque({"alquiler": 12000, "salarios": None})
    assert b["total"] is None and b["faltan"] == ["salarios"]


def test_sin_estructura_no_hay_punto_de_equilibrio(pn):
    r = pn.calcular({"capacidad": CAPACIDAD, "referencias": [_ref()],
                     "b2c": {c: 0 for c in pn.COSTES_B2C}, "repartoB2B": 1})
    assert r["puntoEquilibrio"] is None, (
        "un punto de equilibrio sin conocer la estructura es un numero inventado")


# ─── 3. El margen va sobre el precio de venta ───────────────────────────────

def test_el_margen_es_sobre_el_precio_no_sobre_el_coste(pn):
    """100 de coste y 150 de venta son un 33 % de margen, no un 50 %."""
    m = pn.margen(150, 100)
    assert m["euros"] == 50
    assert m["porcentaje"] == 0.3333


def test_un_mueble_que_se_vende_a_perdida_lo_dice_con_signo(pn):
    m = pn.margen(80, 100)
    assert m["euros"] == -20 and m["porcentaje"] < 0


def test_sin_precio_no_hay_margen(pn):
    assert pn.margen(None, 100)["euros"] is None
    assert pn.margen(0, 100)["euros"] is None, "un precio de 0 no es un regalo, es un hueco"


# ─── 4. Las cuentas de la fabrica del master ────────────────────────────────

def test_la_capacidad_sale_de_las_personas_y_las_horas(pn):
    c = pn.capacidad(CAPACIDAD)
    assert c["capacidadAnual"] == 4800      # 3 muebles/h x 1.600 h
    assert c["capacidadSemanal"] == 105     # 3 x 7 h x 5 dias


def test_la_mano_de_obra_por_mueble_es_la_del_EQUIPO(pn):
    """2 personas a 18 €/h son 36 €/h de equipo; a 3 muebles/h, 12 € por mueble.
    Repartir el coste de UNA persona seria contar la mitad."""
    c = pn.capacidad(CAPACIDAD)
    assert c["costeEquipoHora"] == 36
    assert c["manoObraPorMueble"] == 12


def test_el_coste_directo_suma_materiales_y_mano_de_obra(pn):
    r = pn.coste_referencia(_ref(), mano_obra=12)
    assert r["materiales"] == 66 and r["costeDirecto"] == 78


def test_el_punto_de_equilibrio_con_todo_puesto(pn):
    """Margen B2B de 42 € (120 − 78) y 84.000 € de estructura: 2.000 muebles."""
    r = pn.calcular({
        "capacidad": CAPACIDAD,
        "referencias": [_ref()],
        "b2c": {c: 0 for c in pn.COSTES_B2C},
        "repartoB2B": 1,
        "estructura": {"todo": 84000},
        "plazoEntregaSemanas": 4,
    })
    assert r["margenMedioPonderado"] == 42
    assert r["puntoEquilibrio"] == 2000
    assert r["parteDeLaCapacidad"] == 0.4167   # 2.000 de 4.800
    assert r["sostenible"] is True
    assert r["carteraParaContratar"] == 420    # 4 semanas x 105 muebles


def test_el_margen_b2c_descuenta_la_venta_y_el_montaje(pn):
    """180 − 78 = 102 de margen bruto; menos 40 de comercial, montaje y
    transporte quedan 62. Comparar el bruto con el B2B es enganiarse."""
    r = pn.calcular({
        "capacidad": CAPACIDAD, "referencias": [_ref()],
        "b2c": {"comisionComercial": 15, "montaje": 15, "transporte": 8, "postventa": 2},
        "repartoB2B": 0,
        "estructura": {"todo": 62000},
    })
    assert r["margenB2CMedio"] == 62
    assert r["margenMedioPonderado"] == 62     # todo B2C
    assert r["puntoEquilibrio"] == 1000


def test_el_reparto_entre_canales_pondera(pn):
    r = pn.calcular({
        "capacidad": CAPACIDAD, "referencias": [_ref()],
        "b2c": {"comisionComercial": 15, "montaje": 15, "transporte": 8, "postventa": 2},
        "repartoB2B": 0.5, "estructura": {"todo": 52000},
    })
    assert r["margenMedioPonderado"] == 52      # (42 + 62) / 2
    assert r["puntoEquilibrio"] == 1000


def test_un_reparto_imposible_no_se_usa(pn):
    """Un 150 % de ventas en B2B no es un reparto: es una casilla mal escrita."""
    r = pn.calcular({"capacidad": CAPACIDAD, "referencias": [_ref()],
                     "b2c": {c: 0 for c in pn.COSTES_B2C}, "repartoB2B": 1.5})
    assert r["repartoB2B"] is None and r["margenMedioPonderado"] is None


# ─── 5. La productividad de 3 y 4 personas se mide, no se supone ────────────

def test_un_escenario_sin_productividad_medida_no_inventa_capacidad(pn):
    """CANDADO. Aqui es donde un plan se vuelve humo: dar por hecho que mas
    personas rinden proporcionalmente."""
    r = pn.calcular({
        "capacidad": CAPACIDAD, "referencias": [_ref()],
        "escenarios": [{"nombre": "Inicial", "personas": 2, "mueblesHora": 3},
                       {"nombre": "Crecimiento", "personas": 3, "mueblesHora": None}],
    })
    inicial, crecimiento = r["escenarios"]
    assert inicial["capacidadAnual"] == 4800
    assert crecimiento["capacidadAnual"] is None
    assert crecimiento["facturacion"] is None and crecimiento["ebitda"] is None


def test_el_escenario_grande_avisa_de_que_la_estructura_sube(pn):
    r = pn.calcular({"capacidad": CAPACIDAD, "referencias": [_ref()],
                     "escenarios": [{"nombre": "Escalado", "personas": 4, "mueblesHora": 5}]})
    assert "estructura actual" in r["escenarios"][0]["aviso"]


# ─── 6. El plan dice lo que le falta ────────────────────────────────────────

def test_un_plan_vacio_dice_todo_lo_que_le_falta(pn):
    r = pn.calcular({})
    assert len(r["faltan"]) >= 4
    for f in r["faltan"]:
        assert f["que"] and f["donde"] and f["porque"], (
            "no basta con decir que falta: hay que decir donde va y por que bloquea")


def test_el_coste_sale_el_primero_de_la_lista(pn):
    """Es el dato que desbloquea todo lo demas: sin coste no hay margen."""
    r = pn.calcular({"capacidad": CAPACIDAD, "referencias": [_ref(casco=None)]})
    textos = [f["que"] for f in r["faltan"]]
    assert any("Coste del material por mueble" in t for t in textos)
    assert any("Bajo 60" in t for t in textos), "y dice de QUE referencia falta"


def test_un_plan_completo_no_tiene_nada_pendiente(pn):
    r = pn.calcular({
        "capacidad": CAPACIDAD, "referencias": [_ref()],
        "b2c": {c: 5 for c in pn.COSTES_B2C}, "repartoB2B": 0.6,
        "estructura": {"todo": 80000}, "plazoEntregaSemanas": 4,
    })
    assert r["faltan"] == []


# ─── 7. Si no se sostiene, se dice ──────────────────────────────────────────

def test_una_estructura_que_no_cabe_en_la_fabrica_se_denuncia(pn):
    """CANDADO. Con 42 € de margen y 4.800 muebles de techo, lo maximo que se
    puede cubrir son 201.600 € al anio. Con 300.000 € de estructura NO SALE, y
    no es cuestion de apretar: hay que bajar coste o subir precio."""
    r = pn.calcular({
        "capacidad": CAPACIDAD, "referencias": [_ref()],
        "b2c": {c: 0 for c in pn.COSTES_B2C}, "repartoB2B": 1,
        "estructura": {"todo": 300000},
    })
    assert r["parteDeLaCapacidad"] > 1
    assert r["sostenible"] is False
    assert r["ebitdaPlenaCapacidad"] < 0


def test_sin_saberlo_no_se_dice_ni_que_si_ni_que_no(pn):
    r = pn.calcular({"capacidad": CAPACIDAD, "referencias": [_ref()]})
    assert r["sostenible"] is None, (
        "un plan del que no se sabe si se sostiene no puede contestar que si")


def test_un_margen_negativo_no_da_punto_de_equilibrio(pn):
    """Vendiendo por debajo del coste no hay cantidad que arregle nada: no es un
    numero grandisimo de muebles, es que no existe."""
    r = pn.calcular({
        "capacidad": CAPACIDAD, "referencias": [_ref(precioB2B=50)],
        "b2c": {c: 0 for c in pn.COSTES_B2C}, "repartoB2B": 1,
        "estructura": {"todo": 84000},
    })
    assert r["margenMedioPonderado"] < 0
    assert r["puntoEquilibrio"] is None


# ─── 8. La amortizacion ─────────────────────────────────────────────────────

def test_la_maquinaria_se_reparte_entre_sus_anios(pn):
    assert pn._amortizacion({"maquinaria": 60000, "anosAmortizacion": 10}) == 6000


def test_sin_anios_no_se_amortiza_a_ojo(pn):
    assert pn._amortizacion({"maquinaria": 60000}) is None
    assert pn._amortizacion({"maquinaria": 60000, "anosAmortizacion": 0}) is None
