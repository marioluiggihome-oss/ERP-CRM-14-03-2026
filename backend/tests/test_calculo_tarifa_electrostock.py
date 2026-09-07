# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LA PUBLIOFERTA DE ELECTROSTOCK: EL CATÁLOGO ES DE TODOS, LA CESIÓN NO.

El master, 07/09/2026: «vuelca estas ofertas a la sección electros y mete una
línea en presupuestador de cocina montada... un artículo para que metiendo el
modelo meta el precio, descripción y precio».

QUÉ VIGILA ESTE CANDADO, Y POR QUÉ CADA COSA
────────────────────────────────────────────

1. QUE EL JSON SEA EL PDF. La tarifa se GENERA (regla de las tarifas ACB): se
   regenera a un fichero temporal y se compara byte a byte con el que está en
   el repo. Editar 169 precios a mano es una cifra mal tecleada garantizada, y
   una cifra mal tecleada da un presupuesto plausible y equivocado.

2. QUE LA CESIÓN NO SE ESCAPE. Es COSTE —lo que le cuesta a la casa cada
   aparato, sin IVA y sin portes—, así que se parte igual que la tarifa MV
   (regla 8b): el modelo, la descripción y la marca los ve cualquiera que
   presupueste; la cesión, solo el master. Y se QUITA la clave, no se pone a
   cero: un 0,00 € es una afirmación.

3. QUE LA MITAD ABIERTA SIGA ABIERTA. Es la otra cara de lo mismo y es el
   error que ya se cometió con el MV el 28/08: cerrar el endpoint entero dejó
   la pantalla MUERTA, sin catálogo y sin nada que añadir. Un presupuestador
   tiene que poder buscar el aparato.

4. QUE UN ELECTRODOMÉSTICO NO PAGUE COMISIÓN DE MUEBLE. Se compra hecho y se
   revende. Sin el corte no daría ningún error: `es_mueble` diría que sí, y el
   aparato contaría como unidad Y empujaría el TRAMO de todos los demás. Una
   campana de isla de 2.198 € sube sola un pedido de tramo sin que la casa
   haya fabricado nada.

5. QUE NO SE INVENTE UN PVP. El papel no trae precio de venta. El margen lo
   pone el master y queda escrito de dónde sale (regla 7).

6. QUE LA MANO NO REESCRIBA UN MODELO. El lavavajillas «EDB6130-I» acaba en
   «I», que es como MV escribe la mano izquierda. Con el botón de girar la
   mano, una pulsación lo convertía en «EDB6130-D» — un aparato que no existe,
   pedido a un proveedor que no lo sirve.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND = os.path.join(RAIZ, "backend")
JSON_TARIFA = os.path.join(BACKEND, "data", "electrostock_publioferta.json")
GENERADOR = os.path.join(RAIZ, "herramientas", "tarifa_electrostock.py")
CASCOS = os.path.join(BACKEND, "routes", "cascos.py")
RENTABILIDAD = os.path.join(BACKEND, "routes", "rentabilidad.py")
CM3 = os.path.join(RAIZ, "frontend", "src", "components", "CocinaMontada3.jsx")

if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
os.environ.setdefault("JWT_SECRET", "test-secret-para-los-candados")


def _tarifa():
    with open(JSON_TARIFA, "r", encoding="utf-8") as f:
        return json.load(f)


def _texto(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


# ─── 1. EL JSON ES EL PDF ────────────────────────────────────────────────────

def test_la_tarifa_se_REGENERA_igual_desde_el_pdf():
    """Regenera desde el PDF del proveedor y compara byte a byte.

    Si alguien edita el JSON a mano —para «corregir» un precio, para añadir un
    artículo— esta prueba se pone roja. La tarifa se genera; el sitio donde se
    cambia una cifra es el papel del proveedor, no el fichero de datos.
    """
    with tempfile.TemporaryDirectory() as tmp:
        destino = os.path.join(tmp, "regenerada.json")
        r = subprocess.run([sys.executable, GENERADOR, destino],
                           capture_output=True, text=True)
        assert r.returncode == 0, f"el generador falló: {r.stderr[-2000:]}"
        with open(destino, "rb") as f:
            nueva = f.read()
    with open(JSON_TARIFA, "rb") as f:
        actual = f.read()
    assert nueva == actual, (
        "el JSON de Electrostock NO coincide con lo que sale del PDF. Si has "
        "editado el fichero a mano, deshazlo; si la tarifa nueva es otra, "
        "cambia el PDF y ejecuta herramientas/tarifa_electrostock.py.")


def test_el_papel_dice_que_la_cesion_NO_lleva_iva_ni_portes():
    """Es lo que convierte la cesión en un COSTE INCOMPLETO.

    Sin esto escrito en los datos, alguien puede tomar los 338 € de una placa
    por lo que cuesta puesta en la obra. No lo es: faltan el IVA y los portes,
    que el propio papel deja «a consultar».
    """
    t = _tarifa()
    assert t["ivaIncluido"] is False
    assert t["transporteIncluido"] is False
    assert "Portes" in t["pie"] or "portes" in t["pie"]


def test_la_oferta_TIENE_FECHA_DE_CADUCIDAD():
    """«Precios válidos para el mes de Tarifa o fin de existencias».

    Un presupuesto sacado tres meses después con estos precios no da ningún
    error: da un pedido que se sirve más caro de lo vendido.
    """
    from services import electrostock as E
    t = _tarifa()
    assert re.fullmatch(r"\d{4}-\d{2}", t["vigencia"])
    assert E.vigencia_de("2026-12")["caducada"] is True
    assert E.vigencia_de(t["vigencia"])["caducada"] is False
    assert E.vigencia_de("2026-08")["caducada"] is False


def test_el_reclamo_comercial_NO_esta_en_la_descripcion():
    """«OFERTA», «ÚLTIMAS UDS» y compañía son el gancho, no el producto.

    Pegados a la descripción acaban impresos en el presupuesto de un cliente:
    «Placa 3EB715LR 3 Fuegos grande doble biselada OFERTA».
    """
    from herramientas.tarifa_electrostock import RECLAMOS
    for a in _tarifa()["articulos"]:
        assert not RECLAMOS.search(a["descripcion"]), a["modelo"]


# ─── 2 y 3. EL CORTE VA EN EL PRECIO, NO EN EL CÓDIGO ────────────────────────

def test_sin_permiso_de_dinero_NO_viaja_la_cesion():
    from services import electrostock as E
    abierto = E.catalogo(cesion=False)
    assert abierto, "el catálogo no puede quedarse vacío"
    for a in abierto:
        assert "cesion" not in a, (
            f"«{a['modelo']}» lleva la cesión a quien no puede verla")
    uno = E.por_modelo("3EB715LR", cesion=False)
    assert uno is not None and "cesion" not in uno


def test_la_cesion_se_QUITA_no_se_pone_a_cero():
    """Un 0,00 € es una afirmación —«esto no cuesta nada»— y encima cuadraría
    márgenes solo. La clave desaparece."""
    from services import electrostock as E
    uno = E.por_modelo("3EB715LR", cesion=False)
    assert uno.get("cesion", "AUSENTE") == "AUSENTE"
    assert E.por_modelo("3EB715LR", cesion=True)["cesion"] == 338.0


def test_el_CATALOGO_sigue_abierto_a_quien_presupuesta():
    """La otra mitad de la regla 8b, y la que se olvidó con el MV el 28/08.

    Sin modelo, descripción y marca, la pantalla no se queda sin euros: se
    queda MUERTA, sin un aparato que buscar.
    """
    from services import electrostock as E
    for a in E.catalogo(cesion=False)[:20]:
        assert a["modelo"] and a["descripcion"] and a["marca"] and a["categoria"]


def test_el_endpoint_del_catalogo_pide_la_puerta_ESTRECHA_para_la_cesion():
    """La cesión es COSTE del proveedor: `_ve_precios_mv` (master), no
    `_precios_para_presupuestar`, que es la que abre el PVP de VENTA."""
    src = _texto(CASCOS)
    i = src.index("async def electros_catalogo")
    cuerpo = src[i:i + 1400]
    assert "_ve_precios_mv(current_user)" in cuerpo, (
        "la cesión tiene que ir por la puerta del master")
    assert "cesion=ve_coste" in cuerpo


def test_el_PVP_que_acompana_al_catalogo_NUNCA_lee_el_coste():
    """Lo que se le pega al artículo es el PVP de Electros. Si de paso viajara
    `costeUnitario`, el corte del catálogo se estaría rodeando por otra puerta
    — y un candado que se rodea por otra puerta no es un candado."""
    src = _texto(CASCOS)
    i = src.index("async def _con_pvp_de_electros")
    cuerpo = src[i:i + 2200]
    # Se mira el CÓDIGO, no el docstring: el propio comentario nombra
    # `costeUnitario` para explicar que no se lee, y buscarlo a bulto haría que
    # esta prueba se pusiera roja por su propia explicación.
    codigo = cuerpo.split('"""')[2] if cuerpo.count('"""') >= 2 else cuerpo
    assert '"pvp": 1' in codigo
    assert "costeUnitario" not in codigo, (
        "el coste del proveedor se está colando por el catálogo del presupuestador")
    assert "_precios_para_presupuestar(current_user)" in codigo


# ─── 4. UN ELECTRODOMÉSTICO NO ES UN MUEBLE ──────────────────────────────────

def test_un_electrodomestico_NO_cuenta_como_mueble():
    from services import comisiones as C
    from services.electrostock import FAMILIA
    assert C.es_mueble({"familia": FAMILIA, "quantity": 1, "pvp": 2198}) is False
    assert C.es_mueble({"familia": "BAJO", "quantity": 1, "pvp": 300}) is True


def test_un_electrodomestico_NO_empuja_el_TRAMO_del_comercial():
    """Es la mitad cara del problema y la que no se ve.

    Diez bajos de 300 € son 3.000 € de base: tramo de 30 €/mueble. Con una
    campana de isla de 2.198 € contando, la base sube a 5.198 € y salta al
    tramo de 40 €: 100 € de más en un pedido en el que la casa no ha fabricado
    el aparato. Sin ningún error por medio.
    """
    from services import comisiones as C
    from services.electrostock import FAMILIA
    lineas = [{"familia": "BAJO", "quantity": 10, "pvp": 300},
              {"familia": FAMILIA, "quantity": 1, "pvp": 2198}]
    base = C.base_de_comision(lineas)
    assert base["muebles"] == 10, "el aparato se ha contado como mueble"
    assert base["baseImponible"] == 3000.0, "el aparato ha entrado en el tramo"
    assert base["sinComision"]["pvp"] == 2198.0, "y tiene que verse por qué"


def test_la_familia_del_electro_es_la_MISMA_en_los_dos_lados():
    """La pantalla escribe la familia y el cálculo la lee. Si se separan, el
    aparato vuelve a contar como mueble sin que nada parezca roto."""
    from services.electrostock import FAMILIA
    from services.comisiones import FAMILIAS_SIN_COMISION
    assert FAMILIA in FAMILIAS_SIN_COMISION
    assert f"familia: '{FAMILIA}'" in _texto(CM3), (
        "la línea del presupuestador ya no manda la familia que corta la comisión")


# ─── 5. EL PVP NO SE INVENTA ─────────────────────────────────────────────────

def test_el_papel_NO_trae_precio_de_venta():
    """Solo cesión. Si algún día apareciera un `pvp` en el JSON, sería un
    margen que nadie ha decidido viajando dentro de la tarifa."""
    for a in _tarifa()["articulos"]:
        assert "pvp" not in a and "precioVenta" not in a


def test_el_margen_llega_de_fuera_y_queda_ESCRITO_en_el_articulo():
    from services import electrostock as E
    assert E.pvp_desde_cesion(338.0, 10) == 371.8
    assert E.pvp_desde_cesion(338.0, 0) == 338.0
    assert E.pvp_desde_cesion(338.0, -5) == 0.0, "no se vende por debajo de coste"
    assert E.pvp_desde_cesion(0, 10) == 0.0
    src = _texto(RENTABILIDAD)
    i = src.index("async def seed_electrostock")
    cuerpo = src[i:i + 3500]
    assert '"pvpOrigen": origen' in cuerpo, (
        "sin dejar escrito de dónde sale el PVP, nadie sabe si es del papel")
    assert 'f"cesion+{margen:g}%"' in cuerpo


def test_volver_a_cargar_la_tarifa_NO_pisa_un_PVP_puesto_a_mano():
    """Actualizar los COSTES de una oferta nueva no puede deshacer en silencio
    los precios de venta que el master haya ajustado uno a uno."""
    src = _texto(RENTABILIDAD)
    i = src.index("async def seed_electrostock")
    cuerpo = src[i:i + 3500]
    assert "if pvp_previo is not None and not recalcular:" in cuerpo


def test_volcar_la_tarifa_del_proveedor_es_SOLO_del_master():
    src = _texto(RENTABILIDAD)
    i = src.index("async def seed_electrostock")
    cuerpo = src[i:i + 1200]
    assert '"isAdmin", "isPrimaryAdmin", "isMaster"' in cuerpo
    assert "status_code=403" in cuerpo


# ─── 6. LA MANO NO REESCRIBE UN MODELO ───────────────────────────────────────

def test_hay_modelos_de_electro_que_acaban_en_I_o_en_D():
    """El peligro es real y está en el papel, no es un supuesto."""
    peligrosos = [a["modelo"] for a in _tarifa()["articulos"]
                  if re.search(r"[DI]$", a["modelo"].upper())]
    assert peligrosos, "si esto falla, revisa el PDF: había EDB6130-I y EDB-4610-I"


def test_la_pantalla_NO_le_gira_la_mano_a_un_electrodomestico():
    """`manoDe` recibe la LÍNEA, no el código suelto, y devuelve «sin mano» para
    un electro. Con el código a secas, «EDB6130-I» tenía mano izquierda y una
    pulsación lo reescribía a «EDB6130-D», que no existe."""
    src = _texto(CM3)
    i = src.index("const manoDe = (")
    cuerpo = src[i:i + 700]
    assert "if (linea && linea.esElectro) return undefined;" in cuerpo
    assert "manoDe(m.cod)" not in src, (
        "queda una llamada con el código suelto: ahí se cuela el giro de mano")


# ─── LA LÍNEA DEL PRESUPUESTADOR, ENTERA ─────────────────────────────────────

def test_la_linea_rellena_DESCRIPCION_y_PRECIO_como_pidio_el_master():
    """«metiendo el modelo meta el precio, descripción y precio».

    `desc` es el campo que PINTA la tabla; estuvo puesto en `etiqueta`, que no
    lo lee nadie, y la línea salía con el hueco vacío.
    """
    src = _texto(CM3)
    i = src.index("const añadirElectro = (a) => {")
    cuerpo = src[i:i + 2200]
    assert "desc: a.descripcion," in cuerpo
    assert "cod: a.modelo," in cuerpo
    assert "pvp: Number.isFinite(pvp) && pvp > 0 ? pvp : null," in cuerpo, (
        "un aparato sin PVP no puede entrar a 0 €: en un presupuesto eso es un "
        "precio, y se firma igual que cualquier otro")


def test_un_electro_NO_se_despieza_ni_sale_con_margen_del_cien_por_cien():
    """Un aparato no tiene casco ni puertas: su coste es la cesión, y si quien
    mira no puede verla la línea sale «sin coste». Con el cero del despiece,
    una placa de 578 € enseñaba 578 € de margen y un 100 %."""
    src = _texto(CM3)
    assert "const coste = m.esElectro" in src
    assert "m.costeElectro != null ? m.costeElectro : null" in src


def test_buscar_un_modelo_no_devuelve_EL_QUE_MAS_SE_PARECE():
    """Con un modelo a medias, «el más parecido» mete otro aparato y otro
    precio en el presupuesto sin que nadie haya elegido nada."""
    from services import electrostock as E
    assert E.por_modelo("3EB715") is None
    assert E.por_modelo("")  is None
    assert E.por_modelo("3EB715LR")["modelo"] == "3EB715LR"
    # Y da igual cómo se teclee: en el papel conviven «TD 3002 BK» y «3EB715LR».
    assert E.por_modelo("td3002bk")["modelo"] == "TD 3002 BK"
    assert E.por_modelo("TD-3002-BK")["modelo"] == "TD 3002 BK"


def test_el_generador_PARA_si_la_tarifa_no_cuadra():
    """La validación es lo que separa «169 artículos» de «medio catálogo con la
    misma pinta de bueno»."""
    from herramientas import tarifa_electrostock as G
    arts = G.leer_pdf()
    G.validar(arts)                                   # el papel real pasa
    with pytest.raises(SystemExit):
        G.validar(arts[:-1])                          # uno de menos, no
    roto = [dict(a) for a in arts]
    roto[0]["marca"] = "MARCA_QUE_NO_EXISTE"
    with pytest.raises(SystemExit):
        G.validar(roto)
    caro = [dict(a) for a in arts]
    caro[0]["cesion"] = 99999.0
    with pytest.raises(SystemExit):
        G.validar(caro)
