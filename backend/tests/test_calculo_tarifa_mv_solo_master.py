# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""El COSTE de la tarifa MV es solo del master. El PRECIO DE VENTA, no.

24/08/2026, el master: «quiero que la tarifa MV sea solo mía». Y 29/08, el
mismo: «los usuarios que tengan activo Cocina Montada 3, lo que se va a llamar
ahora Presupuestador, que vean precios para poder presupuestar».

No se contradice: lo que se protege es lo que le CUESTA a la casa cada mueble
—el margen—, y eso vive en la pantalla de Rentabilidad MV, en las proformas del
proveedor y en el PDF de las 126 páginas. El PVP de venta es otra cosa: es lo
que se le dice al cliente, y sin él un presupuestador no presupuesta.

DOS PUERTAS, Y POR ESO HAY DOS FUNCIONES:
  · `_ve_precios_mv`            → master. Todo lo demás (la relación del
                                  Estudio 3D, entre otros).
  · `_precios_para_presupuestar` → master O quien tenga el Presupuestador
                                  activo. Solo los tres endpoints de esa
                                  pantalla.

Ampliar de más un permiso de dinero «ya que estamos» es justo lo que no se
hace: el master abrió el Presupuestador y no dijo nada del resto.

EL CORTE VA EN EL PRECIO, NO EN EL CÓDIGO. Un «B60D» no es información de
coste: es cómo se llama un mueble. Y ojo: hasta el 29/08 este corte dejaba la
pantalla del Presupuestador MUERTA, no sin euros — el endpoint de la tarifa es
el único que da las FAMILIAS, así que el catálogo no cargaba y no había ni
muebles que añadir.

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

# Con el Presupuestador DESACTIVADO a mano. Es el único caso en el que un
# usuario con sesión se queda sin los precios del Presupuestador, y por eso es
# el que hay que probar: si `canUsePresupuestador3: False` no cerrara, el
# permiso no serviría de nada.
SIN_PRESUPUESTADOR = {"canUsePresupuestador3": False, "email": "sin@luiggihome.es"}
FUERA_DEL_PRESUPUESTADOR = [SIN_PRESUPUESTADOR, NADIE]


def _cocina():
    return {"tipo": "lineal",
            "paredes": [{"nombre": "Pared 1", "ancho": 300, "alto": 240}],
            "elementos": [
                {"id": "bajo", "label": "Bajo", "pared_idx": 0, "posicion_cm": 0, "ancho": 60, "fila": "bajo"},
                {"id": "bajo_fregadero", "label": "Bajo fregadero", "pared_idx": 0, "posicion_cm": 60, "ancho": 90, "fila": "bajo"},
            ]}


# ── La tarifa en crudo: cerrada ─────────────────────────────────────────────

@pytest.mark.parametrize("usuario", FUERA_DEL_PRESUPUESTADOR)
def test_la_tarifa_no_la_ve_QUIEN_NO_TIENE_EL_PRESUPUESTADOR(usuario):
    """Quitar el permiso tiene que cerrar de verdad, no solo esconder el botón."""
    from routes.cascos import mv_tarifa
    with pytest.raises(HTTPException) as ex:
        asyncio.run(mv_tarifa("T1", usuario))
    assert ex.value.status_code == 403


@pytest.mark.parametrize("usuario", [GERENTE, COMERCIAL, MONTADOR])
def test_QUIEN_TIENE_EL_PRESUPUESTADOR_SI_VE_LOS_PRECIOS(usuario):
    """El cambio del master del 29/08, y la mitad que más se nota.

    Antes esto daba 403, y no dejaba a la pantalla «sin euros»: la dejaba
    MUERTA. Este endpoint es el único que devuelve las FAMILIAS, así que el
    catálogo no cargaba y no había ni un mueble que añadir a la relación.
    """
    from routes.cascos import mv_tarifa
    r = asyncio.run(mv_tarifa("T1", usuario))
    assert r["familias"], "sin familias no hay catálogo: la pantalla se queda muerta"
    assert r["pointValue"], "sin valor de punto no se puede valorar nada"


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


@pytest.mark.parametrize("usuario", FUERA_DEL_PRESUPUESTADOR)
def test_la_relacion_de_CASCOS_sale_sin_precios_SIN_EL_PERMISO(usuario):
    """La relación escrita a mano es del Presupuestador: sigue el mismo permiso.

    Sin él salen los CÓDIGOS pero no el dinero, que es el corte de siempre:
    quien monta un pedido tiene que poder leer su relación.
    """
    from routes.cascos import mv_detectar_relacion
    r = asyncio.run(mv_detectar_relacion({"texto": "1 b60d (altura 80)"}, usuario))
    assert r["muebles"], "se ha quedado sin muebles"
    assert r["preciosOcultos"] is True
    assert r["totalPvp"] is None
    assert all(m.get("pvp") is None and m.get("pts") is None for m in r["muebles"])
    assert all(m.get("cod") for m in r["muebles"]), "se han perdido los códigos"


@pytest.mark.parametrize("usuario", [GERENTE, COMERCIAL, MONTADOR])
def test_la_relacion_de_CASCOS_SI_trae_precios_CON_el_permiso(usuario):
    """La otra mitad del cambio del 29/08: con el Presupuestador activo, la
    relación se valora. Es lo que se copia a WhatsApp y lo que se pasa a pedido."""
    from routes.cascos import mv_detectar_relacion
    r = asyncio.run(mv_detectar_relacion({"texto": "1 b60d (altura 80)"}, usuario))
    assert not r.get("preciosOcultos")
    assert r["totalPvp"] and r["totalPvp"] > 0, "la relación sale sin valorar"


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
