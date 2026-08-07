# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
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
