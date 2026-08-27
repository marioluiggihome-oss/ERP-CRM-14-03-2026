# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""La TARIFA MV es solo del master (24/08/2026, a petición suya).

«Tarifa» es el DINERO: puntos, PVP y valor de punto. Por ahí se lee lo que le
cuesta a la casa cada mueble, o sea el margen entero.

EL CORTE VA EN EL PRECIO, NO EN EL CÓDIGO. Un «B60D» no es información de
coste: es cómo se llama un mueble. Cerrar también los códigos habría dejado
Cocina Montada 3 y la Relación sin funcionar para todo el que no sea el master
— gente que necesita leer su propia relación para montar un pedido, y que con
este cierre la sigue leyendo, pero sin ver un euro.

Estas pruebas LLAMAN A LOS ENDPOINTS con un usuario que no es master. Mirar el
código no vale: la regla 8 de CLAUDE.md ya avisa de que un cierre solo en la
pantalla es de adorno, porque basta llamar a la API a mano.
"""
import asyncio
import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND = os.path.join(RAIZ, "backend")
os.environ.setdefault("JWT_SECRET", "x" * 64)
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from fastapi import HTTPException  # noqa: E402

MASTER = {"isMaster": True, "email": "master@luiggihome.es"}
# La lista ANCHA. Si el cierre usara `require_admin`, estos pasarían — y sería
# de adorno, que es justo lo que advierte la regla 8.
GERENTE = {"isGerente": True, "email": "gerente@luiggihome.es"}
COMERCIAL = {"isDirectorComercial": True, "email": "comercial@luiggihome.es"}
MONTADOR = {"canAccessMontajes": True, "email": "montador@luiggihome.es"}
NADIE = None

NO_MASTER = [GERENTE, COMERCIAL, MONTADOR, NADIE]


def _cocina():
    return {"tipo": "lineal",
            "paredes": [{"nombre": "Pared 1", "ancho": 300, "alto": 240}],
            "elementos": [
                {"id": "bajo", "label": "Bajo", "pared_idx": 0, "posicion_cm": 0, "ancho": 60, "fila": "bajo"},
                {"id": "bajo_fregadero", "label": "Bajo fregadero", "pared_idx": 0, "posicion_cm": 60, "ancho": 90, "fila": "bajo"},
            ]}


# ── La tarifa en crudo: cerrada ─────────────────────────────────────────────

@pytest.mark.parametrize("usuario", NO_MASTER)
def test_la_tarifa_en_crudo_no_la_ve_nadie_mas(usuario):
    from routes.cascos import mv_tarifa
    with pytest.raises(HTTPException) as ex:
        asyncio.run(mv_tarifa("T1", usuario))
    assert ex.value.status_code == 403


def test_el_master_SI_ve_la_tarifa():
    """Un candado que también cierra al master no es un candado: es una avería."""
    from routes.cascos import mv_tarifa
    r = asyncio.run(mv_tarifa("T1", MASTER))
    assert r.get("success") or r.get("tarifa") or r.get("items"), \
        "el master ya no puede ver la tarifa MV"


@pytest.mark.parametrize("usuario", NO_MASTER)
def test_el_PDF_de_la_tarifa_entera_no_se_lo_baja_nadie_mas(usuario):
    """126 páginas con TODOS los precios del proveedor. Era el sitio por donde
    se escapaba más coste: bastaba con tener una sesión cualquiera."""
    from routes.products import export_mv_catalog_pdf
    with pytest.raises(HTTPException) as ex:
        asyncio.run(export_mv_catalog_pdf(usuario))
    assert ex.value.status_code == 403


# ── La relación: los muebles sí, el dinero no ───────────────────────────────

@pytest.mark.parametrize("usuario", [GERENTE, COMERCIAL, MONTADOR])
def test_la_relacion_del_estudio_3d_sale_SIN_precios(usuario):
    from routes.estudio_cocinas import relacion_mv
    r = asyncio.run(relacion_mv({"distribucion": _cocina()}, usuario))
    assert r["success"] and r["lineas"], "se ha quedado sin muebles: el corte iba en el precio"
    assert r["preciosOcultos"] is True
    assert r["totalPvp"] is None, "el total de tarifa se sigue viendo"
    for linea in r["lineas"]:
        assert linea.get("pvp") is None, f"se ve el PVP de {linea['codigo']}"
        assert linea.get("puntos") is None, f"se ven los puntos de {linea['codigo']}"


@pytest.mark.parametrize("usuario", [GERENTE, COMERCIAL, MONTADOR])
def test_pero_los_CODIGOS_y_las_MEDIDAS_se_siguen_viendo(usuario):
    """Esta es la mitad que importa. Sin códigos no se puede montar un pedido, y
    cerrar de más habría roto pantallas que usa gente todos los días."""
    from routes.estudio_cocinas import relacion_mv
    r = asyncio.run(relacion_mv({"distribucion": _cocina()}, usuario))
    for linea in r["lineas"]:
        assert linea["codigo"], "una línea sin código no sirve para pedir nada"
        assert linea["ancho"], "una línea sin ancho tampoco"
        assert linea["familia"], "ni sin saber qué mueble es"


def test_el_master_SI_ve_los_precios_de_la_relacion():
    from routes.estudio_cocinas import relacion_mv
    r = asyncio.run(relacion_mv({"distribucion": _cocina()}, MASTER))
    assert not r.get("preciosOcultos")
    assert r["totalPvp"] and r["totalPvp"] > 0
    assert all(x.get("pvp") for x in r["lineas"]), "al master le faltan precios"


def test_el_aviso_de_sin_precio_no_miente_cuando_estan_ocultos():
    """`sinPrecio` avisa de muebles que la tarifa no sabe valorar. Si se
    calculara DESPUÉS de esconder el dinero, con un usuario normal saldrían
    todos — y el aviso diría que la tarifa está rota cuando lo que pasa es que
    no se tiene permiso."""
    from routes.estudio_cocinas import relacion_mv
    r = asyncio.run(relacion_mv({"distribucion": _cocina()}, GERENTE))
    assert r["sinPrecio"] == [], \
        f"el aviso dice que estos muebles no tienen precio y sí lo tienen: {r['sinPrecio']}"


@pytest.mark.parametrize("usuario", [GERENTE, MONTADOR])
def test_la_relacion_de_CASCOS_tambien_sale_sin_precios(usuario):
    """El mismo criterio por la otra puerta: la relación escrita a mano."""
    from routes.cascos import mv_detectar_relacion
    r = asyncio.run(mv_detectar_relacion({"texto": "1 b60d (altura 80)"}, usuario))
    assert r["muebles"], "se ha quedado sin muebles"
    assert r["preciosOcultos"] is True
    assert r["totalPvp"] is None
    assert all(m.get("pvp") is None and m.get("pts") is None for m in r["muebles"])
    assert all(m.get("cod") for m in r["muebles"]), "se han perdido los códigos"


def test_el_master_SI_ve_los_precios_en_cascos():
    from routes.cascos import mv_detectar_relacion
    r = asyncio.run(mv_detectar_relacion({"texto": "1 b60d (altura 80)"}, MASTER))
    assert not r.get("preciosOcultos")
    assert r["totalPvp"] and r["totalPvp"] > 0


# ── Que el cierre no sea de adorno ──────────────────────────────────────────

def test_el_cierre_NO_usa_la_lista_ancha_de_roles():
    """Regla 8 de CLAUDE.md, al pie de la letra: con `require_admin` pasarían el
    gerente y el director comercial, y el candado no cerraría nada."""
    from routes.cascos import _ve_precios_mv
    assert _ve_precios_mv(MASTER) is True
    for usuario in NO_MASTER:
        assert _ve_precios_mv(usuario) is False, f"pasa {usuario}"


def test_se_vacian_los_precios_pero_no_desaparecen_las_claves():
    """Una clave que desaparece se vuelve «undefined» en la pantalla y acaba
    pintando «NaN €»: parece una avería, no un candado."""
    from routes.cascos import sin_precios
    limpio = sin_precios([{"cod": "B60D/I", "ancho": 60, "pts": 49, "pvp": 163.17}])[0]
    assert "pvp" in limpio and limpio["pvp"] is None
    assert "pts" in limpio and limpio["pts"] is None
    assert limpio["cod"] == "B60D/I" and limpio["ancho"] == 60
