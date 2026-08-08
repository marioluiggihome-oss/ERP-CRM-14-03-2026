# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO de la medicion en obra: EL PROGRAMA NO ELIGE LA MEDIDA.

La regla de oro dice que no se inventa una medida. Este modulo protege la
version dificil de esa regla: cuando hay DOS medidas distintas de la misma
cosa, no elegir tambien es no inventar.

El 3.245 que se tecleo el dia de la venta y el 3.238 que midio el montador no
son la misma cosa. Guardarlos en el mismo hueco hace que el segundo pise al
primero y nadie llegue a saber que habia siete milimetros de diferencia. Siete
milimetros en el hueco de una columna es un mueble que no entra, y el error
aparece con el montador ya en la obra.

Lo que se protege:

1. LOS TRES NIVELES NO SE MEZCLAN. Introducida, tomada y confirmada conviven;
   apuntar una no borra la anterior, porque la diferencia entre ellas es
   justo lo que hay que poder mirar.

2. NO SE CORTA CON LO QUE NO ESTA CONFIRMADO. `valor_para_fabricar` NO cae a
   la tomada «porque es la mas nueva»: confirmar es el acto de dar por buena
   una medida, y saltarselo lo borraria del proceso.

3. CONFIRMAR EXIGE EL VALOR. Un boton que copia la tomada en silencio no
   comprueba nada y ademas parece que si.

4. UNA DIFERENCIA NO SE RESUELVE SOLA. Se ensenia y obliga a revisar; no se
   queda con la mas nueva ni hace una media.

5. SIN MEDIDA NO HAY CERO. Un cero es un numero y se cuela en el despiece.
"""
import importlib.util
import os

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def mo():
    ruta = os.path.join(BACKEND, "services", "medicion_obra.py")
    spec = importlib.util.spec_from_file_location("_medicion_obra", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# El caso que cuenta el master: 3.245 en la venta, 3.238 en la obra.
HUECO = {"clave": "hueco_columna", "etiqueta": "Hueco de la columna",
         "introducida": 3245, "tomada": 3238, "critica": True, "unidad": "mm"}


# ─── 1. Los tres niveles no se mezclan ──────────────────────────────────────

def test_el_nivel_es_el_mas_alto_que_tenga_valor(mo):
    assert mo.nivel({"introducida": 3245}) == mo.INTRODUCIDA
    assert mo.nivel({"introducida": 3245, "tomada": 3238}) == mo.TOMADA
    assert mo.nivel({"introducida": 3245, "tomada": 3238, "confirmada": 3238}) == mo.CONFIRMADA


def test_una_clave_vacia_no_sube_el_nivel(mo):
    """Si contara la clave y no el valor, el nivel subiria solo con abrir el
    formulario."""
    assert mo.nivel({"introducida": 3245, "tomada": None}) == mo.INTRODUCIDA
    assert mo.nivel({"introducida": 3245, "tomada": ""}) == mo.INTRODUCIDA


def test_sin_nada_es_sin_medir_y_no_cero(mo):
    f = mo.revisar_una({"clave": "ancho"})
    assert f["nivel"] == mo.SIN_MEDIR
    assert f["introducida"] is None, "se ha inventado un cero donde no hay medida"


def test_tomar_no_pisa_la_introducida(mo):
    """CANDADO PRINCIPAL. Si la tomada pisara a la introducida, la diferencia
    —que es el dato que importa— desapareceria al apuntarla."""
    m = mo.tomar({"clave": "hueco", "introducida": 3245}, 3238, quien="Montador")
    assert m["introducida"] == 3245
    assert m["tomada"] == 3238


def test_confirmar_no_pisa_ni_la_tomada_ni_la_introducida(mo):
    m = mo.confirmar(dict(HUECO), 3238, quien="Master")
    assert m["introducida"] == 3245 and m["tomada"] == 3238 and m["confirmada"] == 3238


# ─── 2. No se corta con lo que no esta confirmado ───────────────────────────

def test_no_se_fabrica_con_la_tomada_por_ser_la_mas_nueva(mo):
    """CANDADO. Devolver la tomada aqui haria que confirmar no sirviera para
    nada, y confirmar es lo unico que separa un numero apuntado de una medida
    con la que se corta."""
    assert mo.valor_para_fabricar(HUECO) is None


def test_confirmada_si_se_puede_fabricar(mo):
    assert mo.valor_para_fabricar({**HUECO, "confirmada": 3240}) == 3240


def test_una_critica_sin_confirmar_bloquea(mo):
    f = mo.revisar_una(HUECO)
    assert f["bloquea"] is True
    assert mo.revisar([HUECO])["puedeFabricar"] is False


def test_una_medida_secundaria_sin_confirmar_avisa_pero_no_para_la_obra(mo):
    """Parar la fabricacion por el ancho de un zocalo haria que el aviso se
    ignorase tambien cuando importa."""
    f = mo.revisar_una({**HUECO, "critica": False})
    assert f["bloquea"] is False
    assert mo.revisar([{**HUECO, "critica": False}])["puedeFabricar"] is True


# ─── 3. Confirmar exige el valor ────────────────────────────────────────────

def test_confirmar_sin_valor_es_un_error_no_una_copia(mo):
    with pytest.raises(ValueError):
        mo.confirmar(dict(HUECO), None)
    with pytest.raises(ValueError):
        mo.confirmar(dict(HUECO), "")


def test_tomar_sin_valor_tampoco(mo):
    with pytest.raises(ValueError):
        mo.tomar({"clave": "hueco"}, None)


def test_se_puede_confirmar_un_valor_distinto_de_los_dos(mo):
    """Se vuelve a medir y salen 3.240: ni el de la venta ni el primero de
    obra. Es lo normal y tiene que caber."""
    m = mo.confirmar(dict(HUECO), 3240)
    assert mo.valor_para_fabricar(m) == 3240


# ─── 4. Una diferencia no se resuelve sola ──────────────────────────────────

def test_los_siete_milimetros_del_ejemplo(mo):
    assert mo.diferencia(HUECO) == -7
    assert mo.hay_discrepancia(HUECO) is True


def test_cualquier_diferencia_se_seniala(mo):
    """La tolerancia por defecto es 0 A PROPOSITO: cuanta diferencia da igual
    depende de donde este la medida, y eso no lo puede decidir el programa."""
    assert mo.hay_discrepancia({"introducida": 1000, "tomada": 1001}) is True


def test_con_tolerancia_explicita_si_se_puede_dejar_pasar(mo):
    assert mo.hay_discrepancia({"introducida": 1000, "tomada": 1001}, tolerancia=2) is False


def test_sin_una_de_las_dos_no_hay_diferencia_que_calcular(mo):
    assert mo.diferencia({"introducida": 3245}) is None
    assert mo.hay_discrepancia({"introducida": 3245}) is False


def test_la_revision_dice_que_hacer_no_solo_que_pasa(mo):
    f = mo.revisar_una(HUECO)
    assert "revisar" in f["pendiente"].lower()
    assert "-7" in f["pendiente"] or "−7" in f["pendiente"]


def test_comparar_dos_mediciones_no_elige_ninguna(mo):
    """CANDADO. Quedarse con la mas nueva, o con la de quien tiene mas galones,
    es como se acaba cortando con la mala."""
    a = [{"clave": "pared_a", "tomada": 3245}]
    b = [{"clave": "pared_a", "tomada": 3238}]
    r = mo.comparar_mediciones(a, b, "comercial", "montador")
    fila = r["filas"][0]
    assert fila["comercial"] == 3245 and fila["montador"] == 3238
    assert fila["diferencia"] == -7
    assert r["hayQueRevisar"] is True
    assert "no elige" in r["resumen"]
    # Y no hay ningun campo que diga cual vale.
    assert "buena" not in fila and "correcta" not in fila and "gana" not in fila


def test_una_medida_que_solo_esta_en_una_medicion_no_es_una_diferencia_de_cero(mo):
    r = mo.comparar_mediciones([{"clave": "pared_a", "tomada": 3245}],
                               [{"clave": "pared_b", "tomada": 1200}])
    assert len(r["faltan"]) == 2
    assert all(f["diferencia"] is None for f in r["faltan"])


def test_dos_mediciones_iguales_lo_dicen_y_no_mandan_revisar(mo):
    r = mo.comparar_mediciones([{"clave": "p", "tomada": 3245}],
                               [{"clave": "p", "tomada": 3245}])
    assert r["hayQueRevisar"] is False


# ─── 5. El resumen no da por bueno lo que no se ha mirado ───────────────────

def test_el_resumen_cuenta_las_sin_medir_aparte(mo):
    r = mo.revisar([HUECO, {"clave": "otra", "critica": False}])
    assert "1 sin medir" in r["resumen"]
    assert r["confirmadas"] == 0


def test_todo_confirmado_y_sin_diferencias_deja_fabricar(mo):
    m = {"clave": "h", "introducida": 3245, "tomada": 3245, "confirmada": 3245, "critica": True}
    r = mo.revisar([m])
    assert r["puedeFabricar"] is True
    assert r["bloqueos"] == []


def test_una_diferencia_ya_confirmada_se_sigue_diciendo(mo):
    """No es un problema —la obra no siempre mide lo que decia el
    presupuesto— pero explica por que el mueble no es el que se presupuesto."""
    r = mo.revisar([{**HUECO, "confirmada": 3238}])
    assert r["puedeFabricar"] is True
    assert len(r["discrepancias"]) == 1


def test_sin_medidas_no_revienta(mo):
    r = mo.revisar([])
    assert r["puedeFabricar"] is True and r["total"] == 0
    assert mo.comparar_mediciones([], [])["hayQueRevisar"] is False


def test_valor_visible_no_es_valor_para_fabricar(mo):
    """Son dos preguntas distintas: «que numero ensenio» y «con que corto».
    Juntarlas es como se acaba cortando con una medida sin confirmar."""
    assert mo.valor_visible(HUECO) == 3238
    assert mo.valor_para_fabricar(HUECO) is None
