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
    # Ventana amplia: entre el título y las tres cajas se metió la cadena
    # «PVP − Dto = Base imponible», y una ventana corta dejaba fuera la última.
    trozo = cuerpo[i:i + 6000]
    assert trozo.count("margenVisible") >= 3, (
        "los importes de las comisiones se pintan sin pasar por el candado de "
        "Rentabilidad: enseñar la pantalla dejaría ver lo que cobra cada uno")


def test_el_tramo_NO_sale_del_COSTE_sino_de_la_base_imponible():
    """Las DOS correcciones del master del 25/08, en una sola prueba.

    Primero se implementó sobre el COSTE, porque él dijo «importes de costo …
    de valoración»; lo corrigió al verlo: «es sobre el PVP». Y después preguntó
    por los descuentos y lo zanjó: «siempre va sobre la base imponible, no sobre
    el total con IVA».

    Se vigila desde la pantalla porque es ahí donde se decide con qué número se
    entra al tramo. Y este fallo NO SE VE: si alguien vuelve a pasarle el coste
    —o el PVP sin descontar— el importe sigue saliendo, solo que del tramo
    equivocado.
    """
    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ruta = os.path.join(raiz, "frontend", "src", "components", "RentabilidadMV.jsx")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    i = cuerpo.index("Comisiones de cooperativistas")
    trozo = cuerpo[max(0, i - 2500):i + 500]
    assert "const valoracion = baseImponible" in trozo, (
        "el tramo ya no sale de la base imponible")
    assert "const baseImponible" in trozo and "calc.tot.pvp" in trozo, (
        "la base imponible ha dejado de derivarse del PVP")
    assert "const valoracion = calc.tot.coste" not in trozo, (
        "vuelve a usarse el COSTE para decidir el tramo")
    assert "calc.tot.coste" not in trozo.split("const baseImponible")[-1][:400], (
        "el coste se ha colado en el cálculo de la base imponible")


# ── LA BASE IMPONIBLE: con descuento y SIN IVA ───────────────────────────────
#
# El master, 25/08: «siempre va sobre la base imponible, no sobre el total con
# IVA». Esta es la cadena de un presupuesto:
#
#     Subtotal (PVP)  −  Descuento  =  BASE IMPONIBLE   ← el tramo sale de aquí
#     Base imponible  +  IVA        =  Total
def test_la_base_imponible_descuenta_el_descuento():
    assert C.base_imponible(1888.11, 30) == 1321.68, (
        "no cuadra con el presupuesto real del master: 1.888,11 € con un 30% de "
        "descuento son 1.321,68 € de base imponible")
    assert C.base_imponible(1000, 0) == 1000
    assert C.base_imponible(1000, 100) == 0


def test_un_descuento_absurdo_no_paga_de_mas_ni_negativo():
    assert C.base_imponible(1000, -50) == 1000      # un descuento no es negativo
    assert C.base_imponible(1000, 150) == 0         # ni pasa del 100%
    assert C.base_imponible(-1000, 10) == 0
    assert C.base_imponible(None, None) == 0


def test_el_descuento_puede_BAJAR_de_tramo_y_asi_debe_ser():
    """El caso concreto: comisionar sobre dinero que no ha entrado."""
    bruto = 2700.0
    assert C.euros_por_mueble_comercial(bruto) == 30
    base = C.base_imponible(bruto, 30)              # 1.890 €
    assert C.euros_por_mueble_comercial(base) == 20, (
        f"con un 30% de descuento la base baja a {base} € y el tramo tiene que "
        "bajar con ella; si no, se comisiona sobre dinero que no se ha cobrado")


def test_el_IVA_NO_puede_entrar_en_el_tramo():
    """Si se colara el total con IVA, el tramo se inflaría solo.

    5.500 € de base con el 21% son 6.655 €: saltaría de 30 a 40 € por mueble sin
    que el pedido valga un euro más para la casa. Y además se pagaría comisión
    sobre dinero de Hacienda.
    """
    base = 5500.0
    con_iva = round(base * 1.21, 2)
    assert C.euros_por_mueble_comercial(base) == 30
    assert C.euros_por_mueble_comercial(con_iva) == 40
    assert C.euros_por_mueble_comercial(base) != C.euros_por_mueble_comercial(con_iva), (
        "esta prueba existe para dejar constancia de la diferencia: al tramo hay "
        "que pasarle SIEMPRE la base imponible, nunca el total con IVA")


def test_la_pantalla_calcula_la_base_imponible_antes_del_tramo():
    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ruta = os.path.join(raiz, "frontend", "src", "components", "RentabilidadMV.jsx")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    i = cuerpo.index("Comisiones de cooperativistas")
    trozo = cuerpo[max(0, i - 2000):i + 4000]
    assert "baseImponible" in trozo, (
        "la pantalla ya no calcula la base imponible: estaría metiendo al tramo "
        "el PVP sin descontar")
    assert "1.21" not in trozo and "* 1.21" not in trozo, (
        "hay un IVA metido en el cálculo de la comisión")
