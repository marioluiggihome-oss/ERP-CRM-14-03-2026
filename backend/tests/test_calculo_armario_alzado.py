# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO de la geometria del alzado de armario.

Este plano baja al taller. Si miente, se corta madera mal, y eso no se ve
hasta que la pieza ya esta cortada.

Lo que se protege:

1. NO SE INVENTA NI UNA COTA. Sin ancho, alto, fondo o numero de modulos NO
   se dibuja un armario "razonable": se dice que falta. Un plano acotado con
   medidas inventadas es peor que no tener plano, porque el de fabrica se lo
   cree.

2. MILIMETROS, SIEMPRE. El presupuestador de armarios va en mm y la cocina en
   cm. Si alguien mete un factor 10 por el camino, el dibujo sale igual de
   bonito y el armario sale diez veces mayor. Aqui entra mm y sale mm.

3. PASO NO ES HUECO LIBRE. El reparto bruto incluye el divisor de 18 mm; la
   balda se corta sobre lo que queda. Confundirlos es exactamente por lo que
   una balda no entra.

4. LO QUE NO CABE NO SE APRIETA. Si el interior pedido se pasa del alto, se
   dice cuanto se pasa. No se encoge el reparto para que quepa en pantalla:
   eso deja un plano correcto y un modulo que en fabrica no cierra.

5. EL PLANO Y EL DESPIECE DICEN LO MISMO. Las constantes de corte son las de
   `Armarios.jsx`. Si alguien cambia una sin cambiar la otra, esto se pone
   rojo — que es justo lo que tiene que pasar.
"""
import importlib.util
import os

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def ag():
    ruta = os.path.join(BACKEND, "services", "armario_geometry.py")
    spec = importlib.util.spec_from_file_location("_armario_geometry", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _config(**kw):
    base = {"width": 2400, "height": 2400, "depth": 600, "modules": 3, "numDoors": 3}
    base.update(kw)
    return base


# ─── 1. No se inventa ninguna cota ──────────────────────────────────────────

@pytest.mark.parametrize("falta", ["width", "height", "depth", "modules"])
def test_sin_una_medida_no_se_dibuja(ag, falta):
    c = _config()
    c[falta] = None
    r = ag.montar(c)
    assert r["ok"] is False, f"ha dibujado un armario sin {falta}"
    assert r["motivo"], "ha dicho que no sin explicar que falta"


@pytest.mark.parametrize("falta", ["width", "height", "depth"])
def test_una_medida_vacia_no_es_cero(ag, falta):
    """Un campo en blanco es "no se sabe", no "mide 0"."""
    c = _config()
    c[falta] = ""
    assert ag.montar(c)["ok"] is False


def test_el_motivo_dice_cual_falta(ag):
    r = ag.montar(_config(width=None))
    assert "ancho" in r["motivo"].lower(), (
        "el aviso no dice que falta el ancho; un aviso que no lleva a ninguna "
        "parte se acaba ignorando")


# ─── 2. Milimetros, siempre ─────────────────────────────────────────────────

def test_las_medidas_salen_en_los_mismos_milimetros_que_entran(ag):
    r = ag.montar(_config(width=2400, height=2400, depth=600))
    assert r["ancho"] == 2400 and r["alto"] == 2400 and r["fondo"] == 600, (
        "se ha convertido de unidad por el camino: entra mm, sale mm")


def test_un_armario_en_cm_por_error_se_rechaza(ag):
    """240 (cm) en vez de 2400 (mm) no da ni para los dos laterales."""
    r = ag.montar(_config(width=30, height=240))
    assert r["ok"] is False
    assert "mm" in r["motivo"] or "cm" in r["motivo"]


# ─── 3. Paso no es hueco libre ──────────────────────────────────────────────

def test_el_hueco_libre_descuenta_el_divisor(ag):
    cols = ag.modulos_alzado(2400, 3)
    assert cols[0]["paso"] == 800
    assert cols[0]["hueco"] == 800 - ag.GRUESO_PANEL, (
        "la balda se cortaria sobre el paso bruto y no entraria en fabrica")


def test_los_modulos_no_se_solapan_ni_dejan_hueco(ag):
    cols = ag.modulos_alzado(2400, 3)
    for a, b in zip(cols, cols[1:]):
        assert a["x"] + a["paso"] == pytest.approx(b["x"])
    assert cols[-1]["x"] + cols[-1]["paso"] == pytest.approx(2400), (
        "la suma de los modulos no da el ancho del armario")


def test_demasiados_modulos_para_el_ancho_no_se_dibujan(ag):
    r = ag.montar(_config(width=400, modules=40))
    assert r["ok"] is False, "ha dibujado modulos de hueco negativo"


# ─── 4. Las puertas son suyas, no las de los modulos ────────────────────────

def test_las_puertas_no_se_dibujan_sobre_los_modulos(ag):
    """En correderas casi nunca coinciden: dibujarlas juntas es otro armario."""
    r = ag.montar(_config(modules=3, numDoors=2))
    assert len(r["puertas"]) == 2
    assert r["puertas"][0]["ancho"] == pytest.approx(1200)
    assert len(r["modulos"]) == 3


def test_las_puertas_suman_el_ancho(ag):
    r = ag.montar(_config(numDoors=4))
    assert sum(p["ancho"] for p in r["puertas"]) == pytest.approx(r["ancho"])


# ─── 5. Lo que no cabe no se aprieta ────────────────────────────────────────

def test_un_interior_que_no_cabe_se_rechaza_diciendo_cuanto(ag):
    rep = ag.reparto_vertical(2000, {"drawers": 20})
    assert rep["error"], "ha metido 3000 mm de cajones en 2000 mm de modulo"
    assert "mm" in rep["error"]


def test_no_se_encoge_el_reparto_para_que_quepa(ag):
    """El fallo tiene que salir aqui, no en el taller."""
    rep = ag.reparto_vertical(2000, {"drawers": 20})
    assert rep["elementos"] == [], (
        "ha devuelto un reparto apretado: en pantalla cuadra y en fabrica no cierra")


def test_baldas_que_se_pisan_entre_si_se_rechazan(ag):
    """Si el reparto deja menos que el grueso de la propia balda, las baldas se
    solapan. Eso no es un armario estrecho: es un armario que no existe."""
    rep = ag.reparto_vertical(2364, {"shelves": 200})
    assert rep["error"], "ha repartido baldas que se pisan unas con otras"
    assert str(ag.GRUESO_PANEL) in rep["error"]


# ─── 5-bis. Bloquear no es avisar ───────────────────────────────────────────

def test_baldas_estrechas_se_dibujan_y_se_avisa(ag):
    """CLAUDE.md: bloquea lo que impide fabricar, avisa lo que conviene mirar.
    Una balda cada 172 mm es incomoda, pero se corta igual."""
    rep = ag.reparto_vertical(2364, {"shelves": 4, "hangingRods": 1, "maletero": True})
    assert rep["error"] is None, "ha bloqueado un reparto que si es fabricable"
    assert rep["avisos"], "lo ha dibujado sin decir que las baldas van justas"
    assert any(e["tipo"] == "balda" for e in rep["elementos"])


def test_la_configuracion_por_defecto_del_configurador_no_se_bloquea(ag):
    """Los tres modulos con los que arranca `Armarios.jsx`. Si el motor tumba
    esto, el alzado nace roto para todo el mundo el primer dia."""
    r = ag.montar(_config(width=2400, height=2400, depth=600, modules=3, numDoors=3), [
        {"shelves": 4, "drawers": 0, "hangingRods": 1, "hangingHeight": 1200},
        {"shelves": 6, "drawers": 2, "hangingRods": 0, "hangingHeight": 0},
        {"shelves": 4, "drawers": 0, "hangingRods": 2, "hangingHeight": 1000},
    ])
    assert r["ok"] is True
    assert r["problemas"] == [], f"bloquea la configuracion de fabrica: {r['problemas']}"


def test_un_aviso_no_cuenta_como_problema(ag):
    """Mezclarlos haria que un armario perfectamente fabricable saliera marcado
    como 'NO CABE' en el plano."""
    r = ag.montar(_config(modules=1), [{"shelves": 4, "hangingRods": 1, "maletero": True}])
    assert r["problemas"] == []
    assert r["avisos"], "el aviso se ha perdido por el camino"


def test_un_modulo_imposible_no_tumba_el_plano_entero(ag):
    r = ag.montar(_config(modules=3), [{"shelves": 4}, {"drawers": 40}, {"shelves": 2}])
    assert r["ok"] is True, "un modulo malo ha dejado sin plano a los otros dos"
    assert len(r["problemas"]) == 1
    assert r["problemas"][0]["modulo"] == 2, "no dice CUAL de los modulos falla"


def test_si_ningun_modulo_cabe_no_se_devuelve_un_plano_vacio(ag):
    r = ag.montar(_config(modules=2), [{"drawers": 40}, {"drawers": 40}])
    assert r["ok"] is False, (
        "un plano vacio se lee como 'el armario esta vacio', no como 'esto falla'")


# ─── 6. El reparto vertical respeta los estandares ──────────────────────────

def test_los_cajones_van_abajo(ag):
    rep = ag.reparto_vertical(2364, {"drawers": 3, "shelves": 2})
    cajones = [e for e in rep["elementos"] if e["tipo"] == "cajon"]
    baldas = [e for e in rep["elementos"] if e["tipo"] == "balda"]
    assert max(c["y"] for c in cajones) < min(b["y"] for b in baldas)


def test_el_maletero_va_arriba_del_todo(ag):
    rep = ag.reparto_vertical(2364, {"shelves": 2, "maletero": True})
    mal = [e for e in rep["elementos"] if e["tipo"] == "maletero"][0]
    otros = [e for e in rep["elementos"] if e["tipo"] != "maletero"]
    assert mal["y"] >= max(o["y"] for o in otros)
    assert mal["y"] + mal["alto"] == pytest.approx(2364)


def test_el_maletero_se_reconoce_lo_llamen_como_lo_llamen(ag):
    """La pantalla lo llama `maletero` y la IA `trunk`. Mirar solo uno lo borra
    del plano segun por donde se haya configurado."""
    for clave in ("maletero", "trunk"):
        rep = ag.reparto_vertical(2364, {clave: True, "shelves": 1})
        assert any(e["tipo"] == "maletero" for e in rep["elementos"]), (
            f"con `{clave}` el maletero no se ha dibujado")


def test_los_cajones_no_se_solapan_entre_si(ag):
    rep = ag.reparto_vertical(2364, {"drawers": 4})
    cajones = sorted([e for e in rep["elementos"] if e["tipo"] == "cajon"],
                     key=lambda e: e["y"])
    for a, b in zip(cajones, cajones[1:]):
        assert a["y"] + a["alto"] <= b["y"] + 1e-6, "dos cajones ocupan el mismo sitio"


def test_nada_se_sale_del_modulo(ag):
    # Modulo realista: zapatero + 3 cajones + barra + 1 balda + maletero.
    rep = ag.reparto_vertical(2364, {"drawers": 3, "shelves": 1, "hangingRods": 1,
                                     "maletero": True})
    assert rep["error"] is None
    for e in rep["elementos"]:
        assert e["y"] >= -1e-6, f"{e['etiqueta']} sale por debajo del modulo"
        assert e["y"] <= 2364 + 1e-6, f"{e['etiqueta']} sale por encima del modulo"


# ─── 7. La altura de colgar: dada o derivada, pero nunca callada ────────────

def test_la_altura_de_colgar_dada_se_respeta(ag):
    h, derivada = ag.altura_colgar({"hangingRods": 1, "hangingHeight": 1350})
    assert h == 1350 and derivada is False


def test_sin_altura_de_colgar_se_deriva_del_estandar_y_se_dice(ag):
    h, derivada = ag.altura_colgar({"hangingRods": 1})
    assert h == ag.COLGAR_ALTURA_SIMPLE
    assert derivada is True, (
        "ha derivado una medida sin marcarla: quien lea el plano creera que la "
        "dio el cliente")


def test_la_doble_altura_usa_su_propio_estandar(ag):
    h, _ = ag.altura_colgar({"hangingRods": 2})
    assert h == ag.COLGAR_ALTURA_DOBLE


def test_lo_derivado_llega_al_plano(ag):
    r = ag.montar(_config(modules=1), [{"hangingRods": 1}])
    assert any("derivad" in d.lower() or "estándar" in d.lower() for d in r["derivados"]), (
        "la medida derivada no se informa; se estaria colando como dato real")


def test_sin_barras_no_hay_altura_de_colgar(ag):
    h, derivada = ag.altura_colgar({"hangingRods": 0})
    assert h == 0 and derivada is False


# ─── 8. El plano y el despiece dicen lo mismo ───────────────────────────────

def test_las_constantes_son_las_del_despiece(ag):
    """Fijadas a proposito: son las de `Armarios.jsx`. Si alguien cambia una
    aqui y no alli, el plano dibuja una pieza y fabrica corta otra."""
    assert ag.GRUESO_PANEL == 18
    assert ag.GRUESO_TRASERA == 8
    assert ag.HOLGURA_BALDA == 6
    assert ag.HOLGURA_CAJON == 26
    assert ag.ALTO_CAJON == 150
    assert ag.RETRANQUEO_INTERIOR == 20
    assert ag.RETRANQUEO_CAJON == 50


def test_las_piezas_del_plano_cuadran_con_el_despiece(ag):
    """Mismas formulas que `generateAccessoriesList`."""
    p = ag.medidas_piezas(2400, 2400, 600, 3)
    hueco = 2400 / 3 - 18
    assert p["tapa"] == (2400 - 36, 600, 18)
    assert p["trasera"] == (2400 - 36, 2400 - 36, 8)
    assert p["divisor"] == (2400 - 36, 600 - 20, 18)
    assert p["balda"] == (hueco - 6, 600 - 20, 18)
    assert p["cajon"] == (hueco - 26, 600 - 50, 150)
    assert p["divisores_uds"] == 2


def test_un_solo_modulo_no_lleva_divisores(ag):
    assert ag.medidas_piezas(1000, 2400, 600, 1)["divisores_uds"] == 0
