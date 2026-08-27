# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
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

Y los tres tramos de arriba, que fue añadiendo el mismo día: **«9000 euros, 50
euros por mueble»**, **«el bloque de 12000 y 60 euros de prima»** y **«el último
bloque de 15000 euros y 70 euros de prima»**.

Esos dos últimos pasaron por encima del tope de 50 € que había, así que el tope
subió a 70 en el mismo cambio. Si no, `min(euros, TOPE)` habría recortado los 60
y los 70 a 50 EN SILENCIO —sin error, sin aviso— y el comercial cobraría de
menos. Hay una prueba solo para eso.

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
    (8999.99, 40),
    (9000.01, 50),
    (10000, 50),
    (11999.99, 50),
    (12000.01, 60),
    (14999.99, 60),
    (15000.01, 70),
    (250000, 70),
])
def test_los_tramos_son_los_que_dijo_el_master(valoracion, esperado):
    real = C.euros_por_mueble_comercial(valoracion)
    assert real == esperado, (
        f"con una valoración de {valoracion} € el comercial debería llevarse "
        f"{esperado} € por mueble y se lleva {real}. Los tramos los dictó el "
        "master: 20 por debajo de 2.500, 30 hasta 6.000, 40 hasta 9.000, 50 "
        "hasta 12.000, 60 hasta 15.000 y 70 por encima.")


def test_en_el_borde_exacto_se_paga_el_tramo_de_ARRIBA():
    """CONFIRMADO por el master el 25/08: «en 6.000 euros exactos, 40 euros».

    Al describir los tramos dijo «inferiores a 2.500» (20) y «superiores a
    2.500» (30), así que el valor clavado quedaba sin definir. Se implementó al
    alza —en la duda no se le quita dinero a quien vende— y él lo confirmó
    después. Por simetría, en 2.500 y en 9.000 exactos se paga el de arriba.
    """
    assert C.BORDE_AL_ALZA is True
    assert C.euros_por_mueble_comercial(2500) == 30
    assert C.euros_por_mueble_comercial(6000) == 40
    assert C.euros_por_mueble_comercial(9000) == 50
    assert C.euros_por_mueble_comercial(12000) == 60
    assert C.euros_por_mueble_comercial(15000) == 70


def test_hay_un_tope_por_mueble_y_hoy_son_70_euros():
    """El tope nació en 50 € y subió a 70 el 25/08, con los tramos de 12.000 y
    15.000 €. Sube CON el tramo más alto, nunca por detrás — si no, recortaría
    en silencio (ver la prueba de abajo)."""
    assert C.TOPE_COMERCIAL_POR_MUEBLE == 70, (
        "el tope por mueble ha cambiado sin que lo pidiera el master")


def test_que_el_tope_no_recorte_hoy_es_la_DECISION_y_no_un_descuido():
    """Se le preguntó al master si quería un techo por encima de la escala.

    Dijo que no: «70 tope de momento» (25/08). Hoy tope y tramo más alto valen
    lo mismo, así que `min(euros, TOPE)` no le quita un euro a nadie — y eso es
    exactamente lo que tiene que pasar. Queda escrito aquí para que el siguiente
    que lo vea no lo tome por un cabo suelto y «lo arregle» subiendo el tope,
    que sería tocar nómina por su cuenta.
    """
    mayor = max(e for _, e in C.TRAMOS_COMERCIAL)
    assert C.euros_por_mueble_comercial(10 ** 9) == mayor, (
        "el tope está recortando el tramo más alto: alguien ha bajado el tope o "
        "ha subido un tramo sin mirar el otro")


def test_ningun_tramo_puede_pasar_del_TOPE_sin_que_alguien_se_entere():
    """Desde el tramo de 9.000 € (25/08) el tope y el tramo más alto coinciden
    en 50 €. Eso deja el sistema pegado al techo: si mañana alguien añade un
    tramo de 60 € y no sube el tope, `euros_por_mueble_comercial` lo recortaría
    a 50 EN SILENCIO y el comercial cobraría 10 € menos por mueble sin que
    saltara ningún error. Esta prueba es la que se entera.
    """
    mayor = max(e for _, e in C.TRAMOS_COMERCIAL)
    assert mayor <= C.TOPE_COMERCIAL_POR_MUEBLE, (
        f"hay un tramo de {mayor} € por mueble, por encima del tope de "
        f"{C.TOPE_COMERCIAL_POR_MUEBLE} €: el tope lo recortaría en silencio. "
        "Si el tramo es correcto, hay que subir TOPE_COMERCIAL_POR_MUEBLE a la "
        "vez — pidiéndoselo antes al master, que esto es nómina.")


def test_el_tramo_mas_alto_llega_JUSTO_al_tope():
    """Tramo más alto y tope tienen que valer lo mismo.

    Si el tope se quedara por debajo, recortaría en silencio (la prueba de
    arriba). Si se quedara por encima, sería letra muerta otra vez —que es como
    estuvo hasta el 25/08, con tramos de hasta 40 y un tope de 50 que no mordía
    nunca—. Hoy los dos son 70.
    """
    mayor = max(e for _, e in C.TRAMOS_COMERCIAL)
    assert mayor == C.TOPE_COMERCIAL_POR_MUEBLE == 70


def test_el_tope_recorta_de_verdad_si_alguien_sube_un_tramo(monkeypatch):
    """Que el tope no muerda hoy no puede significar que no funcione."""
    monkeypatch.setattr(C, "TRAMOS_COMERCIAL", ((2500.0, 20.0), (None, 120.0)))
    assert C.euros_por_mueble_comercial(20000) == C.TOPE_COMERCIAL_POR_MUEBLE == 70, (
        "un tramo de 120 € por mueble debería quedarse en el tope de 70")


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
    assert r["comercial"]["tramo"] == "de 6.000 € a 9.000 €"

    # Y el tramo de arriba del todo, el último que dictó el master el 25/08.
    r15 = C.resumen(valoracion=16000, muebles=10, mano_por_mueble=20)
    assert r15["comercial"]["porMueble"] == 70
    assert r15["comercial"]["total"] == 700   # 10 x 70
    assert r15["comercial"]["tramo"] == "más de 15.000 €"


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


def test_la_pantalla_PAGA_Y_ROTULA_igual_que_el_calculo(tmp_path):
    """El candado fuerte: se EJECUTA el código de la pantalla y se compara.

    Los tramos viven en dos sitios —el cálculo cobra, la pantalla avisa— y ya se
    han separado una vez: al añadir el tramo de 9.000 € el importe pasó a 50 € y
    el rótulo se quedó diciendo «más de 6.000 €». Número bien, explicación
    mintiendo, que es peor que no explicar nada porque quien lo lee se fía.

    La prueba de arriba compara las TABLAS. Esta compara el RESULTADO: saca del
    JSX las funciones de verdad, las corre en node y mira, valor a valor, que
    paguen lo mismo y lo rotulen igual. Así también entra lo que la tabla no
    dice —el redondeo, el borde, el formato de los miles, el tope—.
    """
    import json
    import shutil
    import subprocess

    node = shutil.which("node")
    if not node:
        pytest.skip("no hay node en esta máquina")

    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ruta = os.path.join(raiz, "frontend", "src", "components", "RentabilidadMV.jsx")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()

    # Se recortan del JSX los trozos que hacen falta, en orden. Nada de volver a
    # escribirlos aquí: entonces la prueba compararía el backend con una copia
    # mía, no con lo que ve el usuario.
    trozos = []
    for marca, fin in (
        ("export const TRAMOS_COMISION_COMERCIAL = [", "];"),
        ("export const TOPE_COMISION_POR_MUEBLE = ", ";"),
        ("export const comisionPorMueble = ", "\n};"),
        ("const eurosDelTramo = ", ";\n"),
        ("export const nombreDelTramo = ", "\n};"),
    ):
        assert marca in cuerpo, f"ya no está «{marca.strip()}» en la pantalla de Rentabilidad"
        i = cuerpo.index(marca)
        j = cuerpo.index(fin, i) + len(fin)
        trozos.append(cuerpo[i:j].replace("export const", "const", 1))

    # Un valor a cada lado de cada frontera, los bordes clavados, y los extremos.
    fronteras = [t for t, _ in C.TRAMOS_COMERCIAL if t is not None]
    pruebas = [0.0, 1.0]
    for f in fronteras:
        pruebas += [f - 0.01, f, f + 0.01]
    pruebas += [max(fronteras) * 10, 1234.56]

    guion = tmp_path / "tramos.js"
    guion.write_text(
        "\n".join(trozos)
        + "\nconst vs = " + json.dumps(pruebas) + ";\n"
        + "console.log(JSON.stringify(vs.map((v) => "
          "[comisionPorMueble(v), nombreDelTramo(v)])));\n",
        encoding="utf-8")

    salida = subprocess.run([node, str(guion)], capture_output=True, text=True, timeout=60)
    assert salida.returncode == 0, (
        f"el código de tramos de la pantalla no corre: {salida.stderr.strip()}")
    pantalla = json.loads(salida.stdout)

    for v, (euros, rotulo) in zip(pruebas, pantalla):
        assert euros == C.euros_por_mueble_comercial(v), (
            f"con {v} € la pantalla paga {euros} € por mueble y el cálculo "
            f"{C.euros_por_mueble_comercial(v)} €. Esto es nómina.")
        assert rotulo == C._nombre_del_tramo(v), (
            f"con {v} € la pantalla rotula «{rotulo}» y el cálculo dice "
            f"«{C._nombre_del_tramo(v)}». El importe puede estar bien y la "
            "explicación mintiendo, que es peor: quien lo lee se fía.")
