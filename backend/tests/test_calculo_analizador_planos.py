# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: el código que propone la IA es una PISTA, no una identidad.

15/08/2026. El master analiza un plano en IA Lab y en su propia pantalla lee:

    «Para el mueble bajo cajonero, se ha interpretado que 'nP' en el código se
     refiere al número de frentes, resultando en 7B2P800».

OJO, QUE ESTO SE ENTENDIÓ MAL LA PRIMERA VEZ: la IA no se inventa el código. Lo
CONSTRUYE con la nomenclatura ZC, y normalmente bien — «7B2P800» es un bajo de
70 de alto, 2 puertas y 800 de ancho, y es un código de catálogo válido; lo
aclaró el master. El problema no es la forma del código, sino qué pasa cuando
ESE código no está en el catálogo de la biblioteca activa: ahí entran los
respaldos, y buscaban con expresiones muy sueltas:

    pattern_simple = f".*{tipo_code}.*{ancho}$"     ->  .*B.*800$

o sea CUALQUIER código que lleve una B y acabe en 800. Un código inventado podía
casar con un producto REAL que no es ese mueble, y entonces salía un nombre de
catálogo y un precio de catálogo —creíbles los dos— para un mueble que no es.

Y de ahí se pulsa «AÑADIR 8 PRODUCTOS AL PRESUPUESTO».

LO QUE SE PROTEGE
-----------------
Lo que se encuentre POR PATRÓN se comprueba contra lo que se vio en el plano:
el ANCHO (que va rotulado y es lo que más mueve el precio) y la FAMILIA (un alto
no se valora con un bajo). Lo que se encuentra por código EXACTO no pasa por esa
comprobación: ahí el código sí identifica.

Vale más una línea en «requieren revisión manual» que una línea con el mueble
equivocado y su precio puesto.
"""
import importlib.util
import os
import sys
import types

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA = os.path.join(BACKEND, "routes", "ia_lab.py")


def _leer():
    with open(RUTA, encoding="utf-8") as f:
        return f.read()


@pytest.fixture()
def ia(monkeypatch):
    """Carga el router de verdad con sus dependencias simuladas."""
    # Se APARTAN, no se borran: otras pruebas dejan `services` sustituido por
    # falsos y aqui hace falta el modulo de verdad, pero hay que DEVOLVERLOS al
    # terminar. Borrarlos sin mas dejaba sin modulos a la prueba siguiente y
    # fallaba una que no tenia nada que ver (la de recarga de renders).
    apartados = {}
    for n in list(sys.modules):
        if n in ("services", "routes") or n.startswith(("services.", "routes.")):
            apartados[n] = sys.modules.pop(n)
    paquete = types.ModuleType("services")
    paquete.__path__ = [os.path.join(BACKEND, "services")]
    monkeypatch.setitem(sys.modules, "services", paquete)

    dbc = types.ModuleType("services.db_client")
    dbc.get_db = lambda: types.SimpleNamespace()
    monkeypatch.setitem(sys.modules, "services.db_client", dbc)

    jwt = types.ModuleType("services.jwt_service")
    jwt.require_auth = lambda: None
    monkeypatch.setitem(sys.modules, "services.jwt_service", jwt)

    spec = importlib.util.spec_from_file_location("routes.ia_lab", RUTA)
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "routes.ia_lab", mod)
    spec.loader.exec_module(mod)
    yield mod
    for n in list(sys.modules):
        if n in ("services", "routes") or n.startswith(("services.", "routes.")):
            del sys.modules[n]
    sys.modules.update(apartados)


# ─── El caso del master: un código deducido que casa con otro mueble ────────

def test_un_bajo_no_se_valora_con_un_alto(ia):
    """CANDADO PRINCIPAL. El patrón `.*B.*800$` casa con cualquier cosa que
    lleve una B y acabe en 800 — un ALTO incluido."""
    alto = {"code": "9AB1P800", "name": "ALTO 1 PUERTA 800MM", "category": "ALTOS"}
    assert ia._es_del_mueble_detectado(alto, width=800, tipo="BAJO") is False, (
        "un mueble ALTO se está aceptando para un BAJO detectado: son cascos "
        "distintos y precios distintos, y no lo dice nadie")


def test_un_mueble_de_otro_ancho_no_vale(ia):
    """El ancho va rotulado en el plano y es lo que más mueve el precio."""
    otro = {"code": "7B2P600", "name": "BAJO 2 PUERTAS 600MM", "category": "BAJOS"}
    assert ia._es_del_mueble_detectado(otro, width=800, tipo="BAJO") is False, (
        "se acepta un mueble de 600 para un hueco de 800: se presupuesta un "
        "mueble que no cabe")


def test_el_mueble_bueno_si_pasa(ia):
    """Y lo que SÍ es, tiene que pasar: si no, todo iría a revisión manual y
    el analizador dejaría de servir para nada."""
    bueno = {"code": "7B2P800", "name": "BAJO 2 PUERTAS 800MM", "category": "BAJOS"}
    assert ia._es_del_mueble_detectado(bueno, width=800, tipo="BAJO") is True


def test_el_redondeo_al_estandar_no_tumba_el_emparejamiento(ia):
    """La IA estima 790 y el mueble es de 800. Eso es el mismo mueble."""
    bueno = {"code": "7B2P800", "name": "BAJO 2 PUERTAS 800MM", "category": "BAJOS"}
    assert ia._es_del_mueble_detectado(bueno, width=790, tipo="BAJO") is True


def test_sin_producto_no_hay_emparejamiento(ia):
    assert ia._es_del_mueble_detectado(None, width=800, tipo="BAJO") is False


def test_sin_tipo_ni_ancho_no_se_bloquea(ia):
    """Si no se sabe ni el ancho ni la familia, esta comprobación no puede
    decidir: que siga el flujo normal en vez de tirarlo todo."""
    algo = {"code": "X", "name": "LO QUE SEA", "category": ""}
    assert ia._es_del_mueble_detectado(algo, width=0, tipo="") is True


# ─── Y que alguien la llame ─────────────────────────────────────────────────

def test_las_busquedas_POR_PATRON_verifican_lo_que_encuentran():
    """El servicio puede estar perfecto y no servir de nada si nadie lo llama.
    Se exige en los pasos heurísticos, que son los que usan el código deducido."""
    src = _leer()
    i = src.index("async def search_product_in_catalog")
    cuerpo = src[i:src.index("\ndef _dim_mm", i)]
    assert cuerpo.count("_es_del_mueble_detectado(") >= 4, (
        "las búsquedas por patrón vuelven a devolver lo primero que casa sin "
        "comprobar que sea el mueble detectado")


def test_la_busqueda_por_codigo_EXACTO_no_se_estorba():
    """Un código que existe TAL CUAL en el catálogo es una identidad: no se le
    aplica la comprobación, o un código bueno acabaría en revisión manual."""
    src = _leer()
    i = src.index("# 1. Búsqueda exacta")
    cuerpo = src[i:i + 420]
    assert "_es_del_mueble_detectado" not in cuerpo, (
        "se está verificando también el código exacto: un código correcto "
        "acabaría en «revisión manual» sin motivo")


def test_un_codigo_ZC_de_verdad_NO_acaba_en_revision_manual(ia):
    """El caso que aclaró el master: «7B2P800» es un bajo de 70, 2 puertas y 800
    de ancho, y es un código de catálogo VÁLIDO. La comprobación está para cazar
    emparejamientos por patrón que no cuadran, no para estorbar a los códigos
    buenos: si esto se pusiera rojo, el analizador mandaría a revisión manual
    justo los muebles que sí sabe cotizar."""
    real = {"code": "7B2P800", "name": "Bajo 2 puertas 800mm", "category": "BAJOS"}
    assert ia._es_del_mueble_detectado(real, width=800, tipo="BAJO") is True


def test_solo_se_rechaza_lo_que_PARECE_de_otra_familia(ia):
    """Conservador a propósito. Si el nombre del producto no dice de qué familia
    es, no se rechaza: se rechaza cuando dice que es de OTRA. Al revés se
    tirarían productos buenos con el nombre mal puesto en el catálogo."""
    sin_pistas = {"code": "X800", "name": "Modulo inferior 800", "category": ""}
    assert ia._es_del_mueble_detectado(sin_pistas, width=800, tipo="BAJO") is True
