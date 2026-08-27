# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del hueco del electrodomestico: SIN FICHA NO SE DICE QUE CABE.

Es de los errores mas caros y mas tontos que hay: la cocina montada y el horno
que no entra por ocho milimetros. El catalogo de electrodomesticos guarda
codigo, nombre, marca y precio — ninguna medida—, asi que hasta ahora la
comprobacion se hacia de memoria o no se hacia.

Lo que se protege:

1. SIN FICHA NO SE AFIRMA NADA. `cabe` vale None, no False y desde luego no
   True. Un aparato sin medidas no es un aparato que quepa: es un aparato del
   que no se sabe nada, y dar por bueno lo que no se ha mirado es como se llega
   al montaje con un hueco de 596 y un horno de 600.

2. MANDA EL HUECO QUE PIDE EL FABRICANTE, no la medida del aparato. Un horno de
   595 puede pedir 600 de hueco; metido en 595 «cabe» y luego no abre la puerta.

3. LA VENTILACION ES MEDIDA. Si pide 50 mm por detras, el fondo util es el
   fondo menos 50. No contarlos es como el frigorifico entra y no enfria.

4. NO SE AJUSTA NADA SOLO. Si no cabe, se dice CUANTO falta y DONDE. Estirar el
   mueble o comerse la ventilacion lo decide quien firma.

5. «NO CABE» Y «NO SE SABE» SE CUENTAN APARTE. Uno se arregla en el disenio; el
   otro llamando al proveedor por la ficha. Mezclarlos hace que la lista no
   sirva para ninguna de las dos cosas.
"""
import importlib.util
import os

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def eh():
    ruta = os.path.join(BACKEND, "services", "electro_hueco.py")
    spec = importlib.util.spec_from_file_location("_electro_hueco", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Un horno de columna normal: el aparato mide 595 pero pide 600 de hueco.
HORNO = {"marca": "Siemens", "modelo": "HB334A0S0", "codigo": "HB334",
         "anchoHueco": 560, "altoHueco": 590, "fondoHueco": 550,
         "ventilacionFondo": 0, "tipoInstalacion": "integrable"}

FRIGO = {"marca": "Balay", "modelo": "3KFE763XI",
         "anchoHueco": 560, "altoHueco": 1772, "fondoHueco": 550,
         "ventilacionFondo": 50}


# ─── 1. Sin ficha no se afirma nada ─────────────────────────────────────────

def test_sin_ficha_no_se_dice_que_cabe(eh):
    """CANDADO PRINCIPAL."""
    r = eh.comprobar({}, {"ancho": 600, "alto": 600, "fondo": 560})
    assert r["cabe"] is None, "se ha dado por bueno un aparato del que no se sabe nada"
    assert r["estado"] == eh.SIN_FICHA
    assert "pendiente de validación" in r["resumen"].lower()


def test_sin_ficha_tampoco_se_dice_que_NO_cabe(eh):
    """Decir que no cabe manda a rehacer un disenio que a lo mejor esta bien."""
    assert eh.comprobar(None, {"ancho": 600})["cabe"] is not False


def test_una_ficha_a_medias_no_vale(eh):
    r = eh.comprobar({"marca": "X", "anchoHueco": 560}, {"ancho": 600, "alto": 600})
    assert r["cabe"] is None
    assert "altoHueco" in r["faltaEnFicha"]


def test_si_el_disenio_no_da_la_medida_tampoco_se_afirma(eh):
    """El agujero puede estar en el otro lado: ficha completa y hueco sin
    definir. Tampoco se da por bueno."""
    r = eh.comprobar(HORNO, {"ancho": 600})
    assert r["cabe"] is None
    assert "alto" in r["faltaEnHueco"]


# ─── 2. Manda el hueco que pide el fabricante ───────────────────────────────

def test_cabe_cuando_el_hueco_da_lo_que_pide(eh):
    r = eh.comprobar(HORNO, {"ancho": 564, "alto": 596, "fondo": 560})
    assert r["cabe"] is True
    assert r["holguras"] == {"ancho": 4, "alto": 6, "fondo": 10}


def test_no_cabe_y_dice_cuanto_falta_y_donde(eh):
    """«No cabe» a secas obliga a medirlo todo otra vez."""
    r = eh.comprobar(HORNO, {"ancho": 552, "alto": 596, "fondo": 560})
    assert r["cabe"] is False
    assert r["estado"] == eh.NO_CABE
    assert "8 mm de ancho" in r["motivos"][0]
    assert "560" in r["motivos"][0] and "552" in r["motivos"][0]


def test_justo_justo_cabe_pero_se_dice(eh):
    """Cabe segun el fabricante, pero en obra los milimetros aparecen y
    desaparecen."""
    r = eh.comprobar(HORNO, {"ancho": 560, "alto": 590, "fondo": 550})
    assert r["cabe"] is True
    assert any("justo" in a for a in r["avisos"])


def test_una_medida_que_el_aparato_no_declara_no_estorba(eh):
    """Una placa no pide fondo de hueco. Eso no es un fallo."""
    placa = {"marca": "X", "anchoHueco": 560, "altoHueco": 51}
    r = eh.comprobar(placa, {"ancho": 600, "alto": 60})
    assert r["cabe"] is True
    assert "fondo" not in r["holguras"]


# ─── 3. La ventilacion es medida ────────────────────────────────────────────

def test_la_ventilacion_se_resta_del_fondo(eh):
    """CANDADO. 600 de fondo con 50 de ventilacion son 550 utiles."""
    assert eh.fondo_util({"fondo": 600}, FRIGO) == 550


def test_un_frigo_que_entra_pero_no_ventila_NO_cabe(eh):
    """Mirando solo el numero, 560 de fondo contra 550 que pide: cabe. Con los
    50 de ventilacion, no. Es como entra y luego no enfria."""
    r = eh.comprobar(FRIGO, {"ancho": 564, "alto": 1780, "fondo": 560})
    assert r["cabe"] is False
    assert "fondo" in r["motivos"][0]


def test_con_fondo_suficiente_el_mismo_frigo_cabe(eh):
    r = eh.comprobar(FRIGO, {"ancho": 564, "alto": 1780, "fondo": 610})
    assert r["cabe"] is True
    assert any("ventilación" in a for a in r["avisos"])


def test_sin_ventilacion_declarada_no_se_inventa_una(eh):
    """Poner una holgura «por si acaso» seria inventarse una medida."""
    assert eh.fondo_util({"fondo": 600}, {"anchoHueco": 1, "altoHueco": 1}) == 600


# ─── 4. No se ajusta nada solo ──────────────────────────────────────────────

def test_no_hay_ningun_campo_que_proponga_agrandar_el_mueble(eh):
    r = eh.comprobar(HORNO, {"ancho": 552, "alto": 596, "fondo": 560})
    for prohibido in ("anchoSugerido", "corregido", "ajustado", "nuevoAncho"):
        assert prohibido not in r, (
            f"«{prohibido}»: el programa esta proponiendo cambiar el mueble por "
            "su cuenta, y eso lo decide quien firma")


# ─── 5. «No cabe» y «no se sabe» se cuentan aparte ──────────────────────────

def test_la_revision_separa_los_que_no_caben_de_los_que_no_se_saben(eh):
    r = eh.revisar([
        {"ficha": HORNO, "hueco": {"ancho": 564, "alto": 596, "fondo": 560}, "donde": "M06"},
        {"ficha": HORNO, "hueco": {"ancho": 552, "alto": 596, "fondo": 560}, "donde": "M07"},
        {"ficha": {}, "hueco": {"ancho": 600, "alto": 600}, "donde": "M08"},
    ])
    assert r["caben"] == 1
    assert len(r["noCaben"]) == 1 and r["noCaben"][0]["donde"] == "M07"
    assert len(r["sinFicha"]) == 1 and r["sinFicha"][0]["donde"] == "M08"
    assert r["todoComprobado"] is False


def test_un_aparato_sin_ficha_impide_dar_todo_por_comprobado(eh):
    """CANDADO. Si `todoComprobado` se pusiera a True con fichas ausentes, el
    aviso naranja de «pendiente de validacion» no serviria para nada."""
    r = eh.revisar([{"ficha": {}, "hueco": {"ancho": 600, "alto": 600}}])
    assert r["todoComprobado"] is False
    assert "sin ficha" in r["resumen"].lower()


def test_todos_bien_lo_dice_claro(eh):
    r = eh.revisar([{"ficha": HORNO, "hueco": {"ancho": 564, "alto": 596, "fondo": 560}}])
    assert r["todoComprobado"] is True
    assert "caben" in r["resumen"]


def test_sin_aparatos_no_revienta(eh):
    r = eh.revisar([])
    assert r["total"] == 0 and r["todoComprobado"] is True


def test_el_aparato_se_nombra_para_poder_buscarlo(eh):
    assert eh.comprobar(HORNO, {"ancho": 564, "alto": 596})["aparato"] == "Siemens HB334A0S0"
    assert eh.comprobar({"codigo": "X1", "anchoHueco": 1, "altoHueco": 1},
                        {"ancho": 9, "alto": 9})["aparato"] == "X1"


# ─── 6. Un cero no es una medida ────────────────────────────────────────────

def test_una_ficha_con_el_hueco_a_cero_NO_esta_completa(eh):
    """CANDADO. Una ficha a medio rellenar pasaba por completa y contestaba
    «cabe» con una holgura enorme."""
    media = {"marca": "X", "anchoHueco": 0, "altoHueco": 590}
    assert eh.ficha_completa(media) is False
    r = eh.comprobar(media, {"ancho": 600, "alto": 600})
    assert r["cabe"] is None and "anchoHueco" in r["faltaEnFicha"]


def test_un_hueco_disenado_a_cero_tampoco_se_comprueba(eh):
    r = eh.comprobar(HORNO, {"ancho": 0, "alto": 596, "fondo": 560})
    assert r["cabe"] is None and "ancho" in r["faltaEnHueco"]
