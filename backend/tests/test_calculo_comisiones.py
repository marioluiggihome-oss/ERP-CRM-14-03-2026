# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LAS COMISIONES DE LOS COOPERATIVISTAS. ESTO ES NÓMINA.

Los tramos los dictó el master el 25/08/2026:

    «una cantidad fija por mueble, que será en torno a veinte euros por mueble.
    En importes de costo inferiores a dos mil quinientos euros de valoración,
    en importes superiores a dos mil quinientos se llevarán treinta euros, y en
    importes superiores a seis mil euros de valoración de muebles se llevará
    cuarenta euros. Poniendo un tope de valoración de cincuenta euros por
    mueble en pedidos superiores a este importe anterior.»

Y una corrección suya del mismo día, que importa mucho: al describirlo dijo
«importes de COSTO … de valoración» y se implementó sobre el coste. Al verlo en
pantalla lo corrigió: **«es sobre el PVP, no sobre el costo»**. No es un matiz:
el PVP de un pedido es muy superior a su coste, así que con el mismo pedido el
comercial sube de tramo y cobra más.

Y de los montadores: «se llevan una comisión desde la fabricación de los
pedidos a partir de cascos, donde está la casilla esa que ponemos el valor de
mano de obra».

Estas pruebas están escritas con los números EXACTOS que dijo. Si alguien los
cambia sin que él lo pida, se ponen rojas — que es justo lo que tiene que pasar
cuando se toca lo que cobra la gente.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import comisiones as C  # noqa: E402


# ── Los tramos, uno a uno ────────────────────────────────────────────────────
@pytest.mark.parametrize("valoracion,esperado", [
    (0, 20),
    (100, 20),
    (2499.99, 20),
    (2500.01, 30),
    (4000, 30),
    (5999.99, 30),
    (6000.01, 40),
    (10000, 40),
    (250000, 40),
])
def test_los_tramos_son_los_que_dijo_el_master(valoracion, esperado):
    real = C.euros_por_mueble_comercial(valoracion)
    assert real == esperado, (
        f"con una valoración de {valoracion} € el comercial debería llevarse "
        f"{esperado} € por mueble y se lleva {real}. Los tramos los dictó el "
        "master: 20 por debajo de 2.500, 30 hasta 6.000 y 40 por encima.")


def test_en_el_borde_exacto_se_paga_el_tramo_de_ARRIBA():
    """El master dijo «inferiores a 2.500» (20) y «superiores a 2.500» (30), así
    que el valor clavado quedó sin definir. Se decide al alza: en la duda no se
    le quita dinero a quien vende. Está pendiente de que lo confirme, y por eso
    se deja escrito aquí en vez de en la cabeza de nadie."""
    assert C.BORDE_AL_ALZA is True
    assert C.euros_por_mueble_comercial(2500) == 30
    assert C.euros_por_mueble_comercial(6000) == 40


def test_hay_un_tope_de_50_euros_por_mueble():
    assert C.TOPE_COMERCIAL_POR_MUEBLE == 50, (
        "el tope por mueble ha cambiado; el master lo puso en 50 €")


def test_hoy_el_tope_no_llega_a_morder_y_eso_es_correcto():
    """El tramo más alto son 40 €, así que el tope de 50 no se aplica nunca.

    No es un error: el master lo pidió y queda puesto para el día que se añada
    un tramo por encima. Si esta prueba se pone roja es que alguien ha metido un
    tramo de más de 50 — y entonces hay que mirar si el tope debe recortarlo.
    """
    mayor = max(e for _, e in C.TRAMOS_COMERCIAL)
    assert mayor <= C.TOPE_COMERCIAL_POR_MUEBLE, (
        f"hay un tramo de {mayor} € por mueble, por encima del tope de "
        f"{C.TOPE_COMERCIAL_POR_MUEBLE} €")


def test_el_tope_recorta_de_verdad_si_alguien_sube_un_tramo(monkeypatch):
    """Que el tope no muerda hoy no puede significar que no funcione."""
    monkeypatch.setattr(C, "TRAMOS_COMERCIAL", ((2500.0, 20.0), (None, 80.0)))
    assert C.euros_por_mueble_comercial(9000) == 50, (
        "un tramo de 80 € por mueble debería quedarse en el tope de 50")


# ── Las unidades multiplican (CLAUDE.md, regla 4) ────────────────────────────
def test_la_comision_multiplica_por_las_unidades():
    r = C.comision_comercial(4000, 11)
    assert r["porMueble"] == 30
    assert r["muebles"] == 11
    assert r["total"] == 330, (
        f"11 muebles a 30 € son 330 € y salen {r['total']}. Las unidades "
        "multiplican (CLAUDE.md, regla 4).")


def test_un_pedido_sin_muebles_no_paga_comision():
    assert C.comision_comercial(9000, 0)["total"] == 0


# ── Montadores ───────────────────────────────────────────────────────────────
def test_la_comision_del_montador_ES_la_mano_de_obra_tecleada():
    """No se inventa una fórmula: es el importe de la casilla, por mueble."""
    r = C.comision_montadores(20, 11)
    assert r["porMueble"] == 20 and r["total"] == 220, (
        "la comisión de los montadores debe ser la mano de obra por mueble, sin "
        "más cuentas: si tuviera fórmula propia, habría dos números distintos "
        "para lo mismo y acabarían sin cuadrar")


def test_si_se_cambia_la_mano_de_obra_cambia_la_comision():
    assert C.comision_montadores(25, 4)["total"] == 100
    assert C.comision_montadores(0, 4)["total"] == 0


# ── Resumen y basura de entrada ──────────────────────────────────────────────
def test_el_resumen_junta_las_dos_y_suma_bien():
    r = C.resumen(valoracion=7000, muebles=10, mano_por_mueble=20)
    assert r["comercial"]["total"] == 400   # 10 x 40
    assert r["montadores"]["total"] == 200  # 10 x 20
    assert r["total"] == 600
    assert r["comercial"]["tramo"] == "más de 6.000 €"


@pytest.mark.parametrize("basura", [None, "", "abc", -1, float("nan")])
def test_la_basura_no_revienta_ni_paga_de_mas(basura):
    """Un campo vacío en la pantalla no puede convertirse en una nómina rara."""
    try:
        r = C.comision_comercial(basura, 3)
    except Exception as e:  # noqa: BLE001
        pytest.fail(f"con {basura!r} ha reventado: {e}")
    assert r["total"] >= 0
    assert r["porMueble"] <= C.TOPE_COMERCIAL_POR_MUEBLE


@pytest.mark.parametrize("basura", [None, "", "x", -5])
def test_unas_unidades_absurdas_no_pagan_nada(basura):
    assert C.comision_comercial(4000, basura)["total"] == 0


# ── La pantalla tiene que decir LO MISMO que el cálculo ───────────────────────
def test_los_tramos_de_la_pantalla_son_los_mismos_que_los_del_calculo():
    """Están en dos sitios: la pantalla los pinta y este módulo los calcula.

    Si se separan, en Rentabilidad saldría una cifra y en cualquier otro sitio
    otra distinta — y aquí eso significa que alguien cobra de menos. El candado
    lee la tabla del JSX y la compara número a número.
    """
    import re

    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ruta = os.path.join(raiz, "frontend", "src", "components", "RentabilidadMV.jsx")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()

    bloque = re.search(r"TRAMOS_COMISION_COMERCIAL = \[(.*?)\];", cuerpo, re.S)
    assert bloque, "ya no está la tabla de tramos en la pantalla de Rentabilidad"
    pantalla = [(None if h == "null" else float(h), float(e))
                for h, e in re.findall(r"hasta:\s*([0-9]+|null),\s*euros:\s*([0-9.]+)",
                                       bloque.group(1))]
    assert pantalla, "la tabla de tramos de la pantalla ha quedado vacía"
    assert pantalla == list(C.TRAMOS_COMERCIAL), (
        f"los tramos de la pantalla {pantalla} no son los del cálculo "
        f"{list(C.TRAMOS_COMERCIAL)}. Uno de los dos está mintiendo, y esto es "
        "nómina.")

    tope = re.search(r"TOPE_COMISION_POR_MUEBLE = ([0-9.]+)", cuerpo)
    assert tope and float(tope.group(1)) == C.TOPE_COMERCIAL_POR_MUEBLE, (
        "el tope por mueble de la pantalla no coincide con el del cálculo")


def test_las_comisiones_van_dentro_del_candado_de_importes():
    """Son dinero, y Rentabilidad esconde importes con el candado (regla 9).

    Si las comisiones se pintaran siempre, enseñar la pantalla con alguien
    delante dejaría ver lo que cobra cada uno.
    """
    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ruta = os.path.join(raiz, "frontend", "src", "components", "RentabilidadMV.jsx")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    i = cuerpo.index("Comisiones de cooperativistas")
    trozo = cuerpo[i:i + 3000]
    assert trozo.count("margenVisible") >= 3, (
        "los importes de las comisiones se pintan sin pasar por el candado de "
        "Rentabilidad: enseñar la pantalla dejaría ver lo que cobra cada uno")


def test_el_tramo_se_calcula_sobre_el_PVP_y_no_sobre_el_COSTE():
    """La corrección del master del 25/08, clavada.

    Se implementó primero sobre el coste porque él dijo «importes de costo», y
    lo corrigió al verlo. Esta prueba mira la pantalla: si alguien vuelve a
    pasarle el coste, el comercial baja de tramo y cobra menos sin que nadie se
    entere — el número seguiría saliendo, solo que más pequeño.
    """
    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ruta = os.path.join(raiz, "frontend", "src", "components", "RentabilidadMV.jsx")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    i = cuerpo.index("Comisiones de cooperativistas")
    trozo = cuerpo[max(0, i - 1500):i + 500]
    assert "const valoracion = calc.tot.pvp" in trozo, (
        "el tramo de la comisión ha vuelto a calcularse sobre algo que no es el "
        "PVP. El master lo corrigió expresamente: «es sobre el PVP, no sobre el "
        "costo».")
    assert "const valoracion = calc.tot.coste" not in trozo, (
        "vuelve a usarse el COSTE para decidir el tramo")
