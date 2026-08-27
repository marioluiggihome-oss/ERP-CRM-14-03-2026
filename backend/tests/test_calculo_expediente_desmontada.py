# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del expediente de COCINA DESMONTADA.

El master lo pidio asi: «desmontada tiene que tener expediente tambien».

COMO SE HA HECHO, Y POR QUE IMPORTA QUE SE MANTENGA
---------------------------------------------------
NO se convierte un pedido de cascos en un proyecto. Eso duplicaria la obra en
dos sitios y al dia siguiente uno de los dos estaria desactualizado, sin que
nada avisara de cual. Se TRADUCE al vuelo: el pedido sigue siendo el dueno de
sus datos y los motores de siempre —expediente, validacion, medidas— lo leen
con otras gafas.

Lo que se protege:

1. EL NUMERO DE EXPEDIENTE ES EL QUE YA TENIA. El pedido de cascos ya llevaba
   un campo `expediente` para atar la venta con la compra. Inventarle otro
   numero a la misma obra es la forma mas rapida de que dejen de encontrarse.

2. NO SE ABLANDA NINGUNA COMPROBACION. La primera version de esto marcaba
   media validacion como «no aplica», dando por hecho que un casco no tiene
   fondo ni acabado ni codigo. Era FALSO: una linea de casco trae `ancho`,
   `alto`, `fondo`, su color y su firma — solo los llamaba por otros nombres.
   Se traducen los nombres y las comprobaciones se contestan solas, con datos
   de verdad. Apagar un control «porque este modulo es distinto» es como se
   acaba con un semaforo verde que no mira nada.

3. LA FIRMA VALE COMO REFERENCIA. Es lo que identifica fisicamente la pieza:
   dos cascos con la misma firma son el mismo articulo en la estanteria y en el
   pedido al proveedor.

4. LAS MEDIDAS CRITICAS SIGUEN MANDANDO. Si el hueco no esta confirmado, no se
   corta. La traduccion no puede ablandar eso.
"""
import importlib.util
import os

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cargar(nombre, fichero):
    ruta = os.path.join(BACKEND, "services", fichero)
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def eo():
    return _cargar("_expediente_origen", "expediente_origen.py")


@pytest.fixture()
def vf():
    return _cargar("_validacion_desmontada", "validacion_fabricacion.py")


@pytest.fixture()
def ex():
    return _cargar("_expediente_desmontada", "expediente.py")


# Un pedido de cascos tal como lo guarda la pantalla de Cocina Desmontada.
PEDIDO = {
    "id": "casco-7f3a91",
    "kind": "pedido",
    "expediente": "EXP-2026-0042",
    "cliente": "María García",
    "ref": "Cocina piso 3B",
    # Tal cual las guarda la pantalla de Cocina Desmontada.
    "lines": [
        {"sig": "b60|grafito", "tipo": "Bajo Con Balda", "grosor": 19,
         "fondo": 560, "alto": 800, "ancho": 600,
         "color": "grafito", "colorLabel": "Grafito 19", "qty": 2},
        {"sig": "a90|grafito", "tipo": "Alto Con Balda", "grosor": 19,
         "fondo": 330, "alto": 900, "ancho": 900,
         "color": "grafito", "colorLabel": "Grafito 19", "qty": 1},
    ],
}


# ─── 1. Se reconoce y conserva su numero ────────────────────────────────────

def test_se_distingue_un_pedido_de_cascos_de_un_proyecto(eo):
    """Por lo que TIENE, no por una etiqueta: una etiqueta se puede quedar sin
    poner al guardar; la forma del documento, no."""
    assert eo.es_pedido_de_casco(PEDIDO) is True
    assert eo.es_pedido_de_casco({"itemsMontada": [], "lines": []}) is False
    assert eo.es_pedido_de_casco({"itemsMontada": []}) is False


def test_conserva_el_numero_de_expediente_que_ya_tenia(eo):
    """CANDADO. Ese numero ya ataba la venta con la compra. Inventarle otro es
    como se pierde el hilo entre las dos."""
    v = eo.desde_pedido_casco(PEDIDO)
    assert v["budgetNumber"] == "EXP-2026-0042"


def test_sin_numero_de_expediente_cae_a_la_referencia_y_luego_al_id(eo):
    v = eo.desde_pedido_casco({**PEDIDO, "expediente": ""})
    assert v["budgetNumber"] == "Cocina piso 3B"
    v2 = eo.desde_pedido_casco({"id": "casco-1", "lines": []})
    assert v2["budgetNumber"] == "casco-1"


def test_el_cliente_y_las_lineas_llegan_donde_los_motores_los_buscan(eo):
    v = eo.desde_pedido_casco(PEDIDO)
    assert v["customerName"] == "María García"
    assert len(v["itemsDespiece"]) == 2 and v["itemsMontada"] == []


def test_el_tipo_de_pedido_dice_en_que_punto_esta_la_venta(eo):
    assert eo.desde_pedido_casco({**PEDIDO, "kind": "presupuesto"})["status"] == "borrador"
    assert eo.desde_pedido_casco({**PEDIDO, "kind": "pedido"})["status"] == "aceptado"
    assert eo.desde_pedido_casco({**PEDIDO, "kind": "compra"})["status"] == "aceptado"


def test_dice_de_donde_viene_para_que_la_pantalla_no_mienta(eo):
    """Quien lo mire tiene que saber que NO esta viendo un proyecto de Cocina
    Montada."""
    assert eo.desde_pedido_casco(PEDIDO)["origenEtiqueta"] == "Cocina Desmontada"


# ─── 2 y 3. La traduccion es de nombres, no de contenido ────────────────────

def test_un_pedido_de_cascos_CORRECTO_pasa_la_validacion_entera(eo, vf):
    """CANDADO PRINCIPAL. Con los nombres traducidos, las comprobaciones de
    siempre se contestan solas y con datos de verdad: nada que apagar."""
    vista = eo.desde_pedido_casco(PEDIDO)
    r = vf.validar(vista)
    for c in r["checks"]:
        assert c["bloquea"] is False, f"«{c['clave']}» bloquea un pedido correcto: {c['detalle']}"
    assert r["puedeLiberar"] is True


@pytest.mark.parametrize("clave", ["medidas_modulos", "fondos", "acabados", "codigos"])
def test_cada_comprobacion_se_contesta_con_el_dato_de_verdad(eo, vf, clave):
    """Ninguna esta puesta en verde a mano: se contestan porque el dato ESTA,
    solo que el modulo lo llama de otra forma."""
    vista = eo.desde_pedido_casco(PEDIDO)
    c = next(x for x in vf.validar(vista)["checks"] if x["clave"] == clave)
    assert c["estado"] == vf.OK


def test_si_una_linea_de_verdad_NO_trae_el_dato_la_validacion_lo_dice(eo, vf):
    """Es la otra mitad del candado: la traduccion no puede tapar un hueco
    real. Sin alto, la comprobacion tiene que ponerse roja."""
    pedido = {**PEDIDO, "lines": [{"sig": "x|grafito", "tipo": "Bajo", "ancho": 600,
                                   "fondo": 560, "qty": 1}]}
    vista = eo.desde_pedido_casco(pedido)
    c = next(x for x in vf.validar(vista)["checks"] if x["clave"] == "medidas_modulos")
    assert c["estado"] == vf.FALTA and c["bloquea"] is True


def test_la_firma_es_la_referencia_de_la_linea(eo):
    """Dos cascos con la misma firma son el mismo articulo en la estanteria."""
    l = eo.traducir_linea(PEDIDO["lines"][0])
    assert l["referencia"] == "b60|grafito"
    assert l["quantity"] == 2 and l["width"] == 600 and l["height"] == 800 and l["depth"] == 560
    assert l["material"] == "Grafito 19"


def test_la_linea_se_nombra_para_poder_encontrarla(eo, vf):
    """Un aviso que dice «linea 3» obliga a repasar el pedido entero."""
    pedido = {**PEDIDO, "lines": [{"tipo": "Bajo Con Balda", "ancho": 600,
                                   "colorLabel": "Grafito 19", "qty": 1}]}
    vista = eo.desde_pedido_casco(pedido)
    c = next(x for x in vf.validar(vista)["checks"] if x["clave"] == "codigos")
    assert "Bajo Con Balda 600 Grafito 19" in c["detalle"]


def test_traducir_no_pisa_lo_que_la_linea_ya_traiga(eo):
    """Si un dia una linea de casco trae `referencia` propia, manda la suya."""
    l = eo.traducir_linea({"sig": "b60|grafito", "referencia": "ACB-B60-GR"})
    assert l["referencia"] == "ACB-B60-GR"


# ─── 4. Las medidas criticas siguen mandando ────────────────────────────────

def test_una_medida_critica_sin_confirmar_sigue_parando_la_fabricacion(eo, vf):
    """Eso SI aplica a un casco: si el hueco no esta confirmado, no se corta.
    La traduccion no puede ablandar esto."""
    pedido = {**PEDIDO, "medidas": [{"clave": "hueco", "etiqueta": "Hueco",
                                     "introducida": 3200, "tomada": 3147,
                                     "critica": True}]}
    vista = eo.desde_pedido_casco(pedido)
    r = vf.validar(vista)
    assert r["puedeLiberar"] is False
    assert any(c["clave"] == "medidas_obra" and c["bloquea"] for c in r["checks"])


def test_confirmada_la_medida_el_pedido_ya_puede_bajar_al_taller(eo, vf):
    pedido = {**PEDIDO, "medidas": [{"clave": "hueco", "etiqueta": "Hueco",
                                     "introducida": 3200, "tomada": 3147,
                                     "confirmada": 3147, "critica": True}]}
    vista = eo.desde_pedido_casco(pedido)
    assert vf.validar(vista)["puedeLiberar"] is True


def test_la_excepcion_autorizada_tambien_vale_en_desmontada(eo, vf):
    pedido = {**PEDIDO,
              "medidas": [{"clave": "hueco", "etiqueta": "Hueco", "critica": True}],
              "excepcionFabricacion": {"motivo": "hueco de maquina",
                                       "autorizadaPor": "Mario", "riesgo": "recortar en obra"}}
    vista = eo.desde_pedido_casco(pedido)
    r = vf.validar(vista)
    assert r["puedeLiberar"] is True and r["conExcepcion"] is True


# ─── El expediente completo, de punta a punta ───────────────────────────────

def test_el_expediente_de_un_pedido_de_cascos_sale_entero(eo, vf, ex):
    vista = eo.desde_pedido_casco(PEDIDO)
    exp = ex.montar(vista, vf.validar(vista), [], {"isAdmin": True})

    assert exp["cabecera"]["cliente"] == "María García"
    assert exp["cabecera"]["proyecto"] == "EXP-2026-0042"
    assert exp["cabecera"]["referencia"] == "Cocina piso 3B"
    assert exp["lineas"] == 2
    assert exp["etapaActual"] in ex.ETAPAS


def test_a_quien_no_puede_ver_importes_tampoco_aqui(eo, vf, ex):
    """El candado del dinero vale igual venga la obra de donde venga."""
    vista = eo.desde_pedido_casco({**PEDIDO, "totalPvp": 9000})
    exp = ex.montar(vista, vf.validar(vista), [], {"isMontador": True})
    assert "importes" not in exp
