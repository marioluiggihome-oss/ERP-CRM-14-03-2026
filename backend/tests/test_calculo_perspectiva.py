# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del boceto en perspectiva.

Un dibujo en perspectiva engana mucho mas que un alzado: en un alzado un ancho
mal salta a la vista porque se compara con el de al lado, y en perspectiva
todo se ve escorzado y cualquier cosa "parece bien". Por eso aqui se protege lo
que no se ve.

Lo que se protege:

1. NADA SE DIBUJA CON UNA MEDIDA INVENTADA. Si un elemento no trae ancho, se
   OMITE y se informa. Pintarlo con un ancho "razonable" seria mentir en un
   dibujo que encima parece hecho a mano, o sea con firma.

2. LO QUE ESTA DETRAS DE LA CAMARA NO SE DIBUJA. Proyectar un punto de detras
   da figuras del reves --- matematicamente sale un numero, y ese numero pinta
   un mueble imposible.

3. LO CERCANO TAPA A LO LEJANO. Sin orden de profundidad el fondo se pinta
   encima y el dibujo se lee al reves.
"""
import importlib.util
import os

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def pe():
    ruta = os.path.join(BACKEND, "services", "perspectiva.py")
    spec = importlib.util.spec_from_file_location("_perspectiva", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def D(tipo="lineal", paredes=None, elementos=None):
    return {"tipo": tipo,
            "paredes": paredes if paredes is not None else [{"nombre": "A", "ancho": 300, "alto": 250}],
            "elementos": elementos or []}


# ─── La perspectiva funciona ────────────────────────────────────────────────

def test_lo_lejano_se_dibuja_mas_pequeno(pe):
    """LA propiedad de una perspectiva: el mismo objeto, mas lejos, mas chico."""
    # Un segmento vertical de 100 cm, a dos profundidades distintas.
    cerca_a, cerca_b = pe.proyectar((100, 0, 100)), pe.proyectar((100, 100, 100))
    lejos_a, lejos_b = pe.proyectar((100, 0, 900)), pe.proyectar((100, 100, 900))
    assert all(p is not None for p in (cerca_a, cerca_b, lejos_a, lejos_b))
    alto_cerca = abs(cerca_b[1] - cerca_a[1])
    alto_lejos = abs(lejos_b[1] - lejos_a[1])
    assert alto_lejos < alto_cerca, "el mismo metro, mas lejos, tiene que verse menor"


def test_las_paralelas_convergen(pe):
    """El punto de fuga: DOS rectas paralelas tienen que juntarse al alejarse.

    (Ojo: dos puntos de UNA sola recta no valen para esto. Su fuga no cae en el
    centro del dibujo salvo que la camara mire justo en esa direccion, asi que
    comprobar que "se acercan al centro" seria matematicamente falso.)
    """
    sep_cerca = abs(pe.proyectar((400, 100, 100))[0] - pe.proyectar((0, 100, 100))[0])
    sep_lejos = abs(pe.proyectar((400, 100, 900))[0] - pe.proyectar((0, 100, 900))[0])
    assert sep_lejos < sep_cerca, "dos paralelas tienen que estrecharse con la distancia"


def test_lo_alto_se_dibuja_arriba(pe):
    """CANDADO: si el eje vertical sale invertido, NADA falla --- los numeros
    salen, las cajas salen --- y la cocina aparece colgada del techo. Es el tipo
    de error que solo se ve mirando el dibujo, asi que se fija aqui.
    """
    suelo = pe.proyectar((150, 0, 200))
    techo = pe.proyectar((150, 240, 200))
    assert suelo and techo
    assert techo[1] > suelo[1], "el techo tiene que quedar por encima del suelo"


def test_el_boceto_no_sale_en_espejo(pe):
    """CANDADO. Lo que esta a la izquierda de la pared tiene que dibujarse a la
    izquierda.

    El vector "derecha" se calculaba al reves (arriba x adelante en vez de
    adelante x arriba) y el boceto ENTERO salia reflejado. No chirriaba nada:
    la cocina se veia perfecta, solo que con el fregadero en el lado contrario.
    La vertical si estaba bien, asi que no habia ni un sintoma que mirar --- y
    un plano en espejo que llega a obra se monta en espejo.
    """
    d = D(paredes=[{"ancho": 400, "alto": 250}])
    cam = pe.camara_para(d)
    izquierda = pe.proyectar((20.0, 90.0, 0.0), cam)
    derecha = pe.proyectar((380.0, 90.0, 0.0), cam)
    assert izquierda and derecha
    assert izquierda[0] < derecha[0], (
        "el extremo izquierdo de la pared se dibuja a la derecha: el boceto "
        "sale en espejo")


def test_el_espejo_tampoco_aparece_mirando_desde_el_otro_lado(pe):
    """La misma comprobacion con la camara al otro lado, por si el signo se
    arreglara solo para un caso."""
    cam = {"ojo": (200.0, 150.0, -400.0), "objetivo": (200.0, 110.0, 0.0),
           "distancia_focal": 420.0}
    # Mirando desde -z hacia +z, el mundo se ve al reves a proposito: lo que
    # esta en x grande cae a la IZQUIERDA. Es geometria, no un fallo.
    a = pe.proyectar((20.0, 90.0, 0.0), cam)
    b = pe.proyectar((380.0, 90.0, 0.0), cam)
    assert a and b and a[0] > b[0]


def test_lo_que_esta_detras_de_la_camara_no_se_dibuja(pe):
    """CANDADO: proyectar un punto de detras da un mueble del reves."""
    detras = pe.proyectar((-260 - 500, 150, -320 - 500))
    assert detras is None


# ─── Nada se dibuja con una medida inventada ────────────────────────────────

def test_un_elemento_sin_ancho_se_OMITE_y_se_dice(pe):
    """CANDADO principal. Dibujarlo con un ancho "razonable" seria mentir en un
    dibujo que parece firmado a mano."""
    cajas, omitidos = pe.montar_escena(D(elementos=[
        {"id": "B60", "label": "B60", "pared_idx": 0, "ancho": 60},
        {"id": "B??", "label": "B??", "pared_idx": 0, "ancho": None},
    ]))
    assert len(cajas) == 1 and cajas[0]["id"] == "B60"
    assert len(omitidos) == 1
    assert omitidos[0]["id"] == "B??" and omitidos[0]["motivo"] == "sin ancho"


def test_un_ancho_de_cero_tampoco_vale(pe):
    _, omitidos = pe.montar_escena(D(elementos=[
        {"id": "X", "pared_idx": 0, "ancho": 0}]))
    assert len(omitidos) == 1


def test_un_elemento_en_una_pared_que_no_existe_se_omite(pe):
    """No se recoloca en otra pared "que quedara bien": se dice que sobra."""
    cajas, omitidos = pe.montar_escena(D(elementos=[
        {"id": "B60", "pared_idx": 7, "ancho": 60}]))
    assert not cajas and "inexistente" in omitidos[0]["motivo"]


def test_los_anchos_reales_se_respetan(pe):
    cajas, _ = pe.montar_escena(D(elementos=[
        {"id": "B60", "pared_idx": 0, "ancho": 60},
        {"id": "B90", "pared_idx": 0, "ancho": 90},
    ]))
    assert [c["ancho"] for c in cajas] == [60, 90]


def test_los_modulos_se_colocan_uno_detras_de_otro_sin_solaparse(pe):
    """La suma de anchos tiene que ir corrida por la pared: si dos se pisan, el
    dibujo ensena una cocina que no cabe."""
    cajas, _ = pe.montar_escena(D(elementos=[
        {"id": "B60", "pared_idx": 0, "ancho": 60},
        {"id": "B90", "pared_idx": 0, "ancho": 90},
    ]))
    x0_primero = cajas[0]["esquinas"][0][0]
    x0_segundo = cajas[1]["esquinas"][0][0]
    assert x0_segundo == pytest.approx(x0_primero + 60)


# ─── Alturas y fondos vienen del criterio de fabricacion ────────────────────

def test_las_alturas_se_inyectan_no_se_adivinan(pe):
    """Se pasan desde kitchen_geometry para no tener dos criterios de
    fabricacion que puedan separarse."""
    cajas, _ = pe.montar_escena(
        D(elementos=[{"id": "B60", "pared_idx": 0, "ancho": 60}]),
        altura_modulo=lambda _id: 80, fondo_modulo=lambda _id: 58)
    assert cajas[0]["alto"] == 80 and cajas[0]["fondo"] == 58


def test_quien_cuelga_lo_decide_el_criterio_de_fabrica(pe):
    """CANDADO. Colgar o apoyar se resolvia aqui mirando si la etiqueta
    empezaba por «A», y ese atajo NO coincide con `kitchen_geometry.es_alto`:
    el `microondas` es un mueble alto y no empieza por A (habria salido en el
    suelo), y cualquier cosa rotulada «Armario…» habria salido colgada. Dos
    criterios para lo mismo acaban separandose, y en perspectiva un mueble a la
    altura equivocada no llama la atencion."""
    d = D(elementos=[{"id": "microondas", "label": "Microondas",
                      "pared_idx": 0, "ancho": 60}])
    # Con el criterio de fabrica inyectado, el microondas cuelga.
    cajas, _ = pe.montar_escena(d, es_alto=lambda eid, label="": eid == "microondas")
    assert cajas[0]["base"] > 100, "el microondas se ha dibujado en el suelo"
    # Y el criterio se RESPETA aunque contradiga a la letra inicial.
    cajas, _ = pe.montar_escena(
        D(elementos=[{"id": "ACB", "label": "Armario columna", "pared_idx": 0, "ancho": 60}]),
        es_alto=lambda eid, label="": False)
    assert cajas[0]["base"] < 100, (
        "ha colgado del techo una columna solo porque su etiqueta empieza por A")


def test_los_altos_van_ENCIMA_de_los_bajos_no_a_continuacion(pe):
    """CANDADO. Los altos y los bajos son DOS filas que corren cada una por su
    cuenta a lo largo del muro. Con un solo contador por pared, una pared con
    330 cm de bajos colocaba el primer alto en el centimetro 330 --- fuera de
    un muro de 360 y sin nada debajo. Y en perspectiva no chirria: se ve una
    cocina larga y ya."""
    d = D(paredes=[{"ancho": 360, "alto": 250}], elementos=[
        {"id": "B60", "label": "Bajo 60", "pared_idx": 0, "ancho": 60},
        {"id": "B90", "label": "Bajo 90", "pared_idx": 0, "ancho": 90},
        {"id": "A60", "label": "Alto 60", "pared_idx": 0, "ancho": 60},
    ])
    cajas, _ = pe.montar_escena(d, es_alto=lambda eid, label="": eid.startswith("A"))
    alto = next(c for c in cajas if c["id"] == "A60")
    primer_bajo = next(c for c in cajas if c["id"] == "B60")
    assert alto["esquinas"][0][0] == pytest.approx(primer_bajo["esquinas"][0][0]), (
        "el alto arranca donde acaban los bajos en vez de encima del primero")


def test_ninguna_fila_se_sale_de_su_pared(pe):
    d = D(paredes=[{"ancho": 300, "alto": 250}], elementos=[
        {"id": "B90", "pared_idx": 0, "ancho": 90},
        {"id": "B90b", "pared_idx": 0, "ancho": 90},
        {"id": "B60", "pared_idx": 0, "ancho": 60},
        {"id": "A90", "pared_idx": 0, "ancho": 90},
        {"id": "A60", "pared_idx": 0, "ancho": 60},
    ])
    cajas, _ = pe.montar_escena(d, es_alto=lambda eid, label="": eid.startswith("A"))
    for c in cajas:
        borde = max(p[0] for p in c["esquinas"])
        assert borde <= 300 + 1e-6, f"{c['id']} se sale de la pared de 300 cm"


def test_un_alto_cuelga_y_un_bajo_se_apoya(pe):
    cajas, _ = pe.montar_escena(D(elementos=[
        {"id": "B60", "label": "B60", "pared_idx": 0, "ancho": 60},
        {"id": "A60", "label": "A60", "pared_idx": 0, "ancho": 60},
    ]))
    bajo = next(c for c in cajas if c["id"] == "B60")
    alto = next(c for c in cajas if c["id"] == "A60")
    assert alto["base"] > bajo["base"], "el alto tiene que ir por encima del bajo"


# ─── En L: la segunda pared gira ────────────────────────────────────────────

def test_en_L_la_segunda_pared_corre_en_otra_direccion(pe):
    d = D(tipo="l", paredes=[{"ancho": 300, "alto": 250}, {"ancho": 200, "alto": 250}],
          elementos=[{"id": "B60", "pared_idx": 0, "ancho": 60},
                     {"id": "B90", "pared_idx": 1, "ancho": 90}])
    cajas, _ = pe.montar_escena(d)
    a, b = cajas[0]["esquinas"][0], cajas[1]["esquinas"][0]
    assert a[2] != b[2] or a[0] != b[0]
    # La segunda arranca al final de la primera pared.
    assert b[0] == pytest.approx(300)


# ─── Orden de profundidad ───────────────────────────────────────────────────

def test_se_dibuja_de_lejos_a_cerca(pe):
    """CANDADO: sin esto, el fondo se pinta encima de lo de delante."""
    cajas, _ = pe.montar_escena(D(elementos=[
        {"id": "CERCA", "pared_idx": 0, "ancho": 60},
        {"id": "LEJOS", "pared_idx": 0, "ancho": 60},
    ]))
    ordenadas = pe.ordenar_por_profundidad(cajas)
    assert [c["id"] for c in ordenadas] == ["LEJOS", "CERCA"]


def test_una_distribucion_vacia_no_revienta(pe):
    cajas, omitidos = pe.montar_escena(None)
    assert cajas == [] and omitidos == []
    assert pe.montar_escena({})[0] == []


# ─── EL PUNTO DE VISTA ──────────────────────────────────────────────────────
#
# Es lo que separa un boceto de interiorismo de una caja vista de lejos. Y es
# la parte que mas silenciosamente puede salir mal: una camara mal puesta no
# da ningun error, solo da un dibujo que no sirve.

def _todas_las_esquinas(pe, d):
    cajas, _ = pe.montar_escena(d)
    return [esq for c in cajas for esq in c["esquinas"]]


def test_el_ojo_mira_los_muebles_por_delante(pe):
    """CANDADO. Los muebles salen de la pared HACIA EL INTERIOR, asi que el ojo
    tiene que estar dentro de la estancia. Mirando desde el otro lado se verian
    por detras --- y el dibujo saldria igual, porque una caja vista por detras
    sigue siendo una caja. Este es exactamente el fallo que no avisa."""
    d = D(elementos=[{"id": "B60", "pared_idx": 0, "ancho": 60}])
    cam = pe.camara_para(d)
    cajas, _ = pe.montar_escena(d)
    fondo = cajas[0]["fondo"]
    assert cam["ojo"][2] > fondo, (
        "el ojo esta al otro lado de la pared o metido dentro de los muebles: "
        "se dibujarian por detras")


def test_nada_de_la_cocina_queda_detras_de_la_camara(pe):
    """Si un modulo cae detras del ojo, se pierde del dibujo sin avisar."""
    for tipo, paredes in (
        ("lineal", [{"ancho": 300, "alto": 250}]),
        ("l", [{"ancho": 360, "alto": 250}, {"ancho": 240, "alto": 250}]),
    ):
        d = D(tipo=tipo, paredes=paredes, elementos=[
            {"id": "B60", "pared_idx": 0, "ancho": 60},
            {"id": "B90", "pared_idx": 0, "ancho": 90},
        ])
        cam = pe.camara_para(d)
        for esquina in _todas_las_esquinas(pe, d):
            assert pe.proyectar(esquina, cam) is not None, (
                f"en «{tipo}» hay parte de la cocina detras de la camara")


def test_una_cocina_mas_grande_se_mira_desde_mas_lejos(pe):
    """Con una distancia fija, la cocina de 6 m no cabe y la de 2,4 m sale
    minuscula. La distancia se saca del ancho REAL de la pared."""
    cerca = pe.camara_para(D(paredes=[{"ancho": 240, "alto": 250}]))
    lejos = pe.camara_para(D(paredes=[{"ancho": 600, "alto": 250}]))
    assert lejos["ojo"][2] > cerca["ojo"][2]


def test_la_camara_esta_descentrada_para_que_haya_dos_fugas(pe):
    """Centrada sale UN punto de fuga y el dibujo se lee casi como un alzado.
    Las referencias del master tienen dos."""
    d = D(paredes=[{"ancho": 400, "alto": 250}])
    cam = pe.camara_para(d)
    assert abs(cam["ojo"][0] - 200) > 20, "la camara esta centrada: sale un alzado"


def test_el_ojo_esta_a_la_altura_de_una_persona_de_pie(pe):
    cam = pe.camara_para(D(paredes=[{"ancho": 400, "alto": 250}]))
    assert 140 <= cam["ojo"][1] <= 170


def test_sin_medidas_de_pared_no_se_inventa_un_encuadre(pe):
    """Sin ancho no hay de donde sacar la distancia: se devuelve la de por
    defecto y quien dibuja decide, en vez de calcular sobre un cero."""
    assert pe.camara_para(D(paredes=[])) == pe.CAMARA_POR_DEFECTO
    assert pe.camara_para(D(paredes=[{"ancho": 0, "alto": 250}])) == pe.CAMARA_POR_DEFECTO
    assert pe.camara_para(None) == pe.CAMARA_POR_DEFECTO


# ─── El cascaron de la estancia ─────────────────────────────────────────────

def test_las_paredes_reales_se_dibujan_con_su_ancho_y_su_alto(pe):
    e = pe.suelo_y_paredes(D(tipo="l",
                             paredes=[{"ancho": 360, "alto": 250},
                                      {"ancho": 240, "alto": 250}]))
    assert len(e["paredes"]) == 2
    p0 = e["paredes"][0]["esquinas"]
    assert p0[1][0] == pytest.approx(360), "la pared no mide su ancho real"
    assert p0[2][1] == pytest.approx(250), "la pared no mide su alto real"


def test_no_se_cierra_la_habitacion_por_detras(pe):
    """CANDADO. El fondo de la estancia NO lo sabe nadie: solo se dan los
    anchos de las paredes con muebles. Poner una pared al fondo "a una
    distancia que quede bien" es inventarse una medida --- y encima la mas
    creible de todas, porque en perspectiva nadie la comprueba."""
    e = pe.suelo_y_paredes(D(paredes=[{"ancho": 300, "alto": 250}]))
    assert len(e["paredes"]) == 1, (
        "se ha dibujado mas de una pared para una cocina lineal: la de enfrente "
        "estaria a una distancia inventada")


def test_sin_altura_de_techo_no_se_dibuja_pared(pe):
    """Una pared sin alto seria una linea que no mide nada, con muebles
    colgando de ella."""
    e = pe.suelo_y_paredes(D(paredes=[{"ancho": 300, "alto": None}]))
    assert e["paredes"] == []


def test_el_suelo_avanza_hacia_el_espectador_pero_no_le_llega_a_los_pies(pe):
    """Las lineas de suelo son las que van al punto de fuga: si se quedan en la
    pared, no hay profundidad que ensenar.

    Pero tampoco pueden llegar hasta el ojo: un punto a un palmo de la camara
    se proyecta practicamente al infinito, y esas lineas no aniaden
    profundidad --- estiran el dibujo hasta dejar la cocina del tamanio de un
    sello en una esquina. Se fijan los DOS extremos porque de los dos se sale
    un boceto inservible, y ninguno da error."""
    d = D(paredes=[{"ancho": 300, "alto": 250}])
    e = pe.suelo_y_paredes(d)
    cam = pe.camara_para(d)
    ojo_z = cam["ojo"][2]
    z_max = max(max(p[2] for p in linea) for linea in e["suelo"])
    assert z_max >= ojo_z * 0.55, "el suelo se queda en la pared: no hay profundidad"
    assert z_max < ojo_z, "el suelo llega al ojo: la proyeccion se dispara ahi"


def test_una_estancia_sin_paredes_no_revienta(pe):
    e = pe.suelo_y_paredes(None)
    assert e["paredes"] == [] and e["suelo"] == []
