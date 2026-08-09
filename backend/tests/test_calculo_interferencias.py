# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO de los choques: LO QUE NO SE PUEDE COMPROBAR NO SE APRUEBA.

Los choques de una cocina no se descubren en el plano: se descubren en obra,
cuando la puerta del horno da con el cajon de al lado o cuando el lavavajillas
abierto corta la cocina entera. Casi todos son geometria, sin ninguna IA de por
medio.

Lo que se protege:

1. «NO SE HA PODIDO COMPROBAR» NO ES «NO HAY CHOQUE». Sin la distancia entre
   paredes, sin el fondo del rincon o sin la mano de la puerta, la respuesta es
   que falta el dato. Un repaso que da por bueno lo que no ha mirado es PEOR
   que no hacer el repaso, porque deja tranquilo.

2. EL REPASO NO SALE LIMPIO SI QUEDA ALGO SIN COMPROBAR. Es la misma regla,
   pero en el resultado global, que es donde de verdad se mira.

3. LOS MINIMOS SON DE LA CASA Y VAN ESCRITOS EN EL AVISO. El paso libre o la
   holgura del rincon son criterios de oficio y cambian de un fabricante a
   otro. Cada aviso dice con que numero se ha juzgado, para poder discutirlo en
   vez de creerselo.

4. NO SE ARREGLA NADA SOLO. Se dice que choca, cuanto y donde; mover un modulo
   lo decide quien firma.
"""
import importlib.util
import os

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def it():
    ruta = os.path.join(BACKEND, "services", "interferencias.py")
    spec = importlib.util.spec_from_file_location("_interferencias", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── 1. Lo que no se puede comprobar no se aprueba ──────────────────────────

def test_sin_la_distancia_entre_paredes_no_se_dice_que_el_paso_esta_bien(it):
    """CANDADO PRINCIPAL. En una cocina lineal esa distancia muchas veces NO
    esta medida, y suponerla es justo lo que este ERP no hace."""
    r = it.revisar_paso(None, 60, 60)
    assert r[0]["nivel"] == "sin_comprobar"
    assert "no se puede comprobar" in r[0]["texto"].lower()


def test_sin_mano_decidida_el_rincon_no_pasa_por_bueno(it):
    """Un codigo que llega al taller con D/I lo decide el taller, con un 50 %
    de acertar."""
    r = it.revisar_rincon({"fondo": 60, "junquillo": 0}, apertura=None)
    assert r[0]["nivel"] == "sin_comprobar"
    assert "D/I" in r[0]["texto"]


def test_sin_fondo_de_rincon_tampoco(it):
    r = it.revisar_rincon({}, apertura="D")
    assert r[0]["nivel"] == "sin_comprobar"


def test_una_instalacion_sin_posicion_no_se_da_por_libre(it):
    """«Esta por ahi» no es una posicion."""
    r = it.revisar_instalaciones([{"id": "M01", "x": 0, "largo": 60}],
                                 [{"tipo": "desague"}])
    assert r[0]["nivel"] == "sin_comprobar"


def test_una_instalacion_sin_zona_definida_se_dice(it):
    r = it.revisar_instalaciones([], [{"tipo": "cosa_rara", "x": 100}])
    assert r[0]["nivel"] == "sin_comprobar"


def test_un_frente_que_no_se_sabe_como_abre_no_se_aprueba(it):
    r = it.revisar_barrido(240, 60, 60, "no_se_sabe")
    assert r[0]["nivel"] == "sin_comprobar"


# ─── 2. El repaso no sale limpio si queda algo sin comprobar ────────────────

def test_el_repaso_NO_sale_limpio_con_cosas_sin_comprobar(it):
    """CANDADO. Es donde de verdad se mira, y es donde mas facil seria colar un
    «todo bien» que no lo es."""
    r = it.revisar({"filas": [{"fondo": 60}, {"fondo": 60}]})  # sin distancia
    assert r["limpio"] is False
    assert r["errores"] == []
    assert len(r["sinComprobar"]) >= 1
    assert "SIN comprobar" in r["resumen"]


def test_limpio_de_verdad_cuando_todo_se_ha_podido_mirar(it):
    r = it.revisar({"distanciaParedes": 300, "filas": [{"fondo": 60}, {"fondo": 60}]})
    assert r["limpio"] is True
    assert "todo lo comprobable" in r["resumen"]


def test_una_cocina_de_una_sola_pared_no_inventa_un_paso(it):
    """No hay nada enfrente: comprobar el paso daria un aviso que no significa
    nada, y los avisos que no significan nada se aprenden a ignorar."""
    r = it.revisar({"filas": [{"fondo": 60}]})
    assert r["avisos"] == []
    assert r["limpio"] is True


# ─── 3. Los minimos van escritos en el aviso ────────────────────────────────

def test_un_pasillo_estrecho_es_un_error_y_dice_el_numero(it):
    r = it.revisar_paso(200, 60, 60)   # quedan 80
    assert r[0]["nivel"] == "error"
    assert "80" in r[0]["texto"] and "90" in r[0]["texto"]


def test_un_pasillo_justo_avisa_pero_no_bloquea(it):
    r = it.revisar_paso(230, 60, 60)   # quedan 110: pasa el minimo, no el comodo
    assert r[0]["nivel"] == "aviso"
    assert "120" in r[0]["texto"]


def test_un_pasillo_holgado_no_dice_nada(it):
    assert it.revisar_paso(300, 60, 60) == []


def test_el_minimo_se_puede_cambiar_porque_es_de_la_casa(it):
    """No es una verdad del programa: cambia de un fabricante a otro."""
    assert it.revisar_paso(200, 60, 60, minimo=70, comodo=70) == []


def test_el_junquillo_del_rincon_dice_con_que_numero_se_juzga(it):
    r = it.revisar_rincon({"fondo": 60, "junquillo": 0}, apertura="D")
    assert r[0]["nivel"] == "error"
    assert "5" in r[0]["texto"]


def test_con_junquillo_suficiente_el_rincon_pasa(it):
    assert it.revisar_rincon({"fondo": 60, "junquillo": 6}, apertura="D") == []


# ─── 4. El barrido de un abatible ───────────────────────────────────────────

def test_el_lavavajillas_abierto_que_choca_de_frente(it):
    """El choque que mas se ve en obra. 160 entre paredes, 120 de fondos: 40 de
    paso, y el abatible barre 60. Da contra el frente de enfrente."""
    r = it.revisar_barrido(160, 60, 60, "abatible")
    assert r[0]["nivel"] == "error"
    assert "choca" in r[0]["texto"]


def test_el_lavavajillas_abierto_que_deja_pasar_de_lado(it):
    """300 − 120 = 180 de paso; abierto barre 60 y quedan 120: se pasa."""
    assert it.revisar_barrido(300, 60, 60, "abatible") == []


def test_abierto_deja_un_hueco_por_el_que_no_se_pasa(it):
    """210 − 120 = 90 de paso; barre 60 y quedan 30. Cabe abrirlo, pero por
    detras no pasa nadie sin cerrarlo, y eso hay que saberlo antes."""
    r = it.revisar_barrido(210, 60, 60, "abatible")
    assert r[0]["nivel"] == "aviso"
    assert "30" in r[0]["texto"]


def test_una_puerta_normal_no_barre_el_paso(it):
    """Una puerta abre a un lado, no hacia delante: no come pasillo."""
    assert it.revisar_barrido(200, 60, 60, "puerta") == []


# ─── 5. Las instalaciones tienen su zona ────────────────────────────────────

def test_un_modulo_encima_del_desague_avisa(it):
    r = it.revisar_instalaciones([{"id": "M03", "x": 90, "largo": 60}],
                                 [{"tipo": "desague", "x": 100}])
    assert len(r) == 1
    assert r[0]["nivel"] == "aviso"
    assert "M03" in r[0]["texto"] and "desague" in r[0]["texto"]
    assert "20" in r[0]["texto"], "no dice con cuantos cm se ha juzgado"


def test_un_modulo_lejos_de_la_instalacion_no_dice_nada(it):
    assert it.revisar_instalaciones([{"id": "M01", "x": 0, "largo": 60}],
                                    [{"tipo": "desague", "x": 300}]) == []


def test_la_zona_se_puede_cambiar_por_fabricante(it):
    r = it.revisar_instalaciones([{"id": "M01", "x": 0, "largo": 60}],
                                 [{"tipo": "desague", "x": 100}],
                                 zonas={"desague": 60})
    assert len(r) == 1, "con 60 cm de zona el modulo si la pisa"


# ─── 6. No se arregla nada solo ─────────────────────────────────────────────

def test_ningun_aviso_propone_mover_el_modulo_por_su_cuenta(it):
    r = it.revisar({"distanciaParedes": 200, "filas": [{"fondo": 60}, {"fondo": 60}]})
    for a in r["avisos"]:
        for prohibido in ("nuevaX", "moverA", "corregido", "sugerido"):
            assert prohibido not in a, (
                f"«{prohibido}»: el programa esta moviendo muebles por su cuenta")


def test_sin_datos_no_revienta(it):
    r = it.revisar({})
    assert r["limpio"] is True and r["avisos"] == []


# ─── 7. Un cero no es una medida ────────────────────────────────────────────

def test_una_distancia_de_cero_no_es_una_cocina_estrechisima(it):
    """CANDADO. Salia «el paso queda en −120 cm», que no significa nada y
    encima parece un calculo. Una distancia de 0 es una medida que nadie ha
    puesto."""
    r = it.revisar_paso(0, 60, 60)
    assert r[0]["nivel"] == "sin_comprobar"


def test_el_junquillo_SI_puede_ser_cero(it):
    """Es justo el caso que hace chocar la puerta: no hay junquillo. La regla
    del cero es para MEDIDAS, no para todo."""
    r = it.revisar_rincon({"fondo": 60, "junquillo": 0}, apertura="D")
    assert r[0]["nivel"] == "error"


def test_la_posicion_de_un_modulo_SI_puede_ser_cero(it):
    """El primer modulo empieza en la esquina, en el 0. Un LARGO de 0, en
    cambio, es un modulo que no existe."""
    r = it.revisar_instalaciones([{"id": "M01", "x": 0, "largo": 60}],
                                 [{"tipo": "desague", "x": 30}])
    assert len(r) == 1 and r[0]["nivel"] == "aviso"
    assert it.revisar_instalaciones([{"id": "M01", "x": 0, "largo": 0}],
                                    [{"tipo": "desague", "x": 30}]) == []
