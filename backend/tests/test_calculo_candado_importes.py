# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO de Rentabilidad: quien entra, y que se ve cuando esta echado.

Dos promesas que pidio el master el 05/08 y que no se cambian sin permiso:

1. **Solo el master entra.** Por Rentabilidad pasan la tarifa del proveedor, el
   descuento y el margen. Un gerente o un director comercial ven Cascos, pero
   NO esto. Si el guardia del backend vuelve a la lista ancha de roles, el
   cierre de la pantalla queda de adorno: basta llamar a la API a mano.

2. **El candado oculta DINERO, no bloquea la edicion.** Antes deshabilitaba las
   casillas, que no servia de nada (quien entra aqui ya es master) y encima
   dejaba los importes a la vista, que es justo lo que hay que tapar cuando se
   ensena la pantalla con alguien delante.

Las comprobaciones del frontend se hacen leyendo el fichero, igual que en
test_calculo_motores_render.py: no hay banco de pruebas de React en el repo y
mas vale una prueba que lee el codigo que ninguna.
"""
import ast
import os
from typing import Optional

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASCOS_PY = os.path.join(RAIZ, "backend", "routes", "cascos.py")
IMPORTADOR = os.path.join(RAIZ, "frontend", "src", "components", "ProformaImporter.jsx")
CASCOS_JSX = os.path.join(RAIZ, "frontend", "src", "components", "Cascos.jsx")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def es_master():
    """Saca `_es_master` de routes/cascos.py sin importar el modulo entero.

    cascos.py arrastra fastapi, fitz, reportlab y la base de datos; aqui solo
    interesa el guardia, asi que se extrae su trozo del arbol y se ejecuta
    suelto.
    """
    arbol = ast.parse(_leer(CASCOS_PY))
    trozos = [n for n in arbol.body
              if (isinstance(n, ast.Assign)
                  and any(getattr(t, "id", "") == "_MASTER_FLAGS" for t in n.targets))
              or (isinstance(n, ast.FunctionDef) and n.name == "_es_master")]
    assert any(isinstance(n, ast.FunctionDef) for n in trozos), \
        "ya no existe _es_master en routes/cascos.py"
    ambito = {"Optional": Optional}
    exec(compile(ast.Module(body=trozos, type_ignores=[]), CASCOS_PY, "exec"), ambito)
    return ambito["_es_master"]


# ── 1. Solo el master entra ──────────────────────────────────────────────────

@pytest.mark.parametrize("ficha", [
    {"isAdmin": True},
    {"isPrimaryAdmin": True},
    {"isMaster": True},
])
def test_el_master_entra_en_rentabilidad(es_master, ficha):
    assert es_master(ficha) is True


@pytest.mark.parametrize("ficha", [
    {"isGerente": True},
    {"isDirectorComercial": True},
    {"isController": True},
    {"canAccessRentabilidad": True},
    {"username": "COMERCIAL"},
    {},
    None,
])
def test_nadie_mas_entra_en_rentabilidad(es_master, ficha):
    assert es_master(ficha) is False, (
        "se ha vuelto a abrir el importador de proformas (tarifa de proveedor, "
        "descuento y margen) a quien no es el master. Si el cambio es a "
        "proposito, pideselo al master y actualiza este fichero.")


def test_la_pantalla_de_cascos_tambien_cierra_rentabilidad_al_master():
    fuente = _leer(CASCOS_JSX)
    assert "esMasterRenta" in fuente, \
        "Cascos.jsx ya no distingue el permiso de Rentabilidad del de Cascos"
    assert "showRenta && esMasterRenta" in fuente, \
        "el panel de Rentabilidad se pinta sin comprobar que es el master"
    assert "esMaster={esMasterRenta}" in fuente, \
        "a RentabilidadUnificada se le vuelve a pasar esMaster fijo en true"


# ── 2. El candado oculta dinero, no bloquea la edicion ───────────────────────

def test_el_candado_ya_no_bloquea_la_edicion():
    fuente = _leer(IMPORTADOR)
    assert "bloqueado" not in fuente, (
        "vuelve a haber un bloqueo de edicion en el importador. El candado que "
        "pidio el master tapa importes; deshabilitar casillas no hace falta.")


def test_el_candado_tapa_precios_costes_y_margen():
    fuente = _leer(IMPORTADOR)
    assert "ocultarImportes" in fuente, "el importador ya no sabe ocultar importes"
    # Lo que NO puede leerse con el candado echado. Cada uno tiene que estar
    # dentro de un bloque guardado por `ocultarImportes`; si alguien lo saca
    # fuera, esta prueba no lo ve, pero si lo BORRA del guardia, si.
    for guardia in ("{!ocultarImportes && <>", "{!ocultarImportes && ("):
        assert guardia in fuente, f"falta el guardia {guardia!r} del candado"
    # El resumen economico (COSTE / Margen / PRECIO DE VENTA) va detras del
    # guardia, no suelto.
    resumen = fuente.index("PRECIO DE VENTA")
    guardado = fuente.rindex("{!ocultarImportes && (", 0, resumen)
    cierre = fuente.index(")}", resumen)
    assert guardado < resumen < cierre, \
        "el precio de venta se pinta fuera del candado"


def test_el_panel_de_costes_no_se_ensena_con_el_candado_echado():
    """Descuento, herraje, mano de obra y margen viven en ese panel."""
    fuente = _leer(IMPORTADOR)
    assert "Precios, costes y margen ocultos" in fuente, \
        "ya no se sustituye el panel de costes por el aviso de candado echado"
