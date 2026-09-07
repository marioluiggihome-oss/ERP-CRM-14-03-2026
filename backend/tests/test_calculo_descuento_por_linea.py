# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL DESCUENTO, LÍNEA A LÍNEA — Y EL COSTE, DEBAJO DEL CANDADO.

El master, 07/09/2026: «faltan los pvp's de los artículos y que en ellos pueda
meter un descuento en línea, así como el descuento de los muebles que aparezca
también en línea; el coste que aparece ahora que no aparezca hasta que yo toque
candado, por si saco algún presupuesto con cliente delante, que eso no se vea».

TRES COSAS, Y LAS TRES SON DINERO
─────────────────────────────────

1. EL DE LA CABECERA ES EL DE POR DEFECTO; EL DE LA LÍNEA MANDA SOBRE ÉL.
   No se suman, y esto no es un matiz: sumándolos, un 10 % en una línea dentro
   de una cocina al 20 % la dejaría al 72 % — un 28 % de descuento que nadie ha
   decidido y que no da ningún error.

2. UN 0 ESCRITO A PROPÓSITO SE RESPETA. Un electrodoméstico que se vende sin
   descuento dentro de una cocina al 20 % es lo normal. Se mira si la cifra
   ESTÁ, no si es verdadera: con un `or`, ese 0 se cae al descuento general y
   el aparato sale un 20 % más barato de lo que se ha decidido. Es la misma
   trampa que la mano de obra del montador (CLAUDE.md, regla 16).

3. Y LA COMISIÓN SE PAGA SOBRE LO QUE SE COBRA. `base_de_comision` aplicaba el
   porcentaje del PEDIDO a todas las líneas por igual; con descuentos de línea
   eso paga de más en unas y de menos en otras. Ojo con la trampa de
   arreglarlo a medias: si la línea guardara el importe YA NETO y encima
   llegara el porcentaje del pedido, se descontaría DOS VECES.

Y EL COSTE: con el candado cerrado, las columnas NO EXISTEN. Antes estaban
siempre, con «•••» dentro. Con un cliente mirando por encima del hombro, ese
«•••» es una invitación: dice que ahí hay un número escondido.
"""
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND = os.path.join(RAIZ, "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)
os.environ.setdefault("JWT_SECRET", "test-secret-para-los-candados")

JSX = os.path.join(RAIZ, "frontend", "src", "components", "CocinaMontada3.jsx")


def _pantalla():
    with open(JSX, "r", encoding="utf-8") as f:
        return f.read()


# ─── EL PORCENTAJE QUE SE APLICA DE VERDAD ───────────────────────────────────

def test_el_de_la_LINEA_manda_sobre_el_del_pedido():
    from services.comisiones import dto_de
    assert dto_de({"dtoPct": 10}, 20) == 10
    assert dto_de({}, 20) == 20
    assert dto_de({"dtoPct": 30}, 0) == 30


def test_NO_se_suman_los_dos():
    """Sumándolos, un 10 % dentro de un pedido al 20 % dejaría la línea al
    72 %: un 28 % que nadie ha decidido."""
    from services.comisiones import dto_de, importe_neto_de
    assert dto_de({"dtoPct": 10}, 20) == 10, "se están sumando"
    assert importe_neto_de({"price": 1000, "dtoPct": 10}, 20) == 900.0


def test_un_CERO_escrito_a_proposito_se_respeta():
    """Con un `or`, ese 0 se cae al descuento del pedido y el aparato se vende
    un 20 % más barato de lo decidido."""
    from services.comisiones import dto_de, importe_neto_de
    assert dto_de({"dtoPct": 0}, 20) == 0
    assert importe_neto_de({"price": 1000, "dtoPct": 0}, 20) == 1000.0


def test_una_cifra_ROTA_cae_al_escalon_siguiente_y_no_a_cero():
    """Un «150 %» o un «-3» no son un descuento: son un dato corrupto.
    Tratarlos como «sin descuento» subiría la base y pagaría comisión de MÁS
    sobre un importe que nadie cobró (regla 16)."""
    from services.comisiones import dto_de
    assert dto_de({"dtoPct": 150}, 15) == 15
    assert dto_de({"dtoPct": -3}, 15) == 15
    assert dto_de({"dtoPct": "no es un número"}, 15) == 15
    assert dto_de({}, 999) == 0.0, "un porcentaje de pedido imposible tampoco vale"


# ─── LA BASE DE LA COMISIÓN ──────────────────────────────────────────────────

def test_la_comision_se_paga_sobre_lo_que_se_COBRA():
    from services.comisiones import base_de_comision
    lineas = [{"familia": "BAJO", "quantity": 10, "price": 3000},
              {"familia": "BAJO", "quantity": 1, "price": 1000, "dtoPct": 0}]
    # 3.000 al 20 % = 2.400, más 1.000 sin descuento propio = 3.400.
    assert base_de_comision(lineas, 20)["baseImponible"] == 3400.0


def test_el_descuento_NO_se_aplica_DOS_VECES():
    """La trampa de arreglarlo a medias. Si `base_imponible` volviera a
    descontar el porcentaje del pedido sobre un importe ya neto, un pedido al
    20 % pagaría comisión sobre 6.400 € en vez de 8.000."""
    from services.comisiones import base_de_comision
    lineas = [{"familia": "BAJO", "quantity": 10, "price": 10000}]
    assert base_de_comision(lineas, 20)["baseImponible"] == 8000.0


def test_sin_descuentos_sale_EXACTAMENTE_lo_de_siempre():
    """El cambio no puede mover un euro en los pedidos que ya existen."""
    from services.comisiones import base_de_comision
    lineas = [{"familia": "BAJO", "quantity": 10, "price": 3000},
              {"familia": "PUERTAS", "quantity": 4, "price": 800}]
    b = base_de_comision(lineas, 0)
    assert b["baseImponible"] == 3000.0 and b["muebles"] == 10
    assert b["sinComision"]["pvp"] == 800.0


def test_un_descuento_de_linea_tambien_baja_el_TRAMO():
    """Es la mitad que no se ve: el importe decide el €/mueble de TODOS."""
    from services.comisiones import base_de_comision, euros_por_mueble_comercial
    lineas = [{"familia": "BAJO", "quantity": 10, "price": 6500, "dtoPct": 20}]
    base = base_de_comision(lineas, 0)["baseImponible"]
    assert base == 5200.0
    # 6.500 € cae en el tramo de 40 €/mueble; 5.200 €, en el de 30. Son 100 €
    # de diferencia en un pedido de 10 muebles.
    assert euros_por_mueble_comercial(6500) == 40
    assert euros_por_mueble_comercial(base) == 30


# ─── LA PANTALLA ─────────────────────────────────────────────────────────────

def test_la_pantalla_aplica_la_MISMA_regla_que_la_nomina():
    """`dtoDe` en el JSX y `dto_de` en Python tienen que decir lo mismo: si se
    separan, el presupuesto cobra una cosa y la comisión se calcula sobre
    otra."""
    src = _pantalla()
    i = src.index("const dtoDe = (m)")
    linea = src[i:src.index("\n", i)]
    assert "m.dto != null" in linea, (
        "la pantalla usa un `||` y se comería el 0 escrito a propósito")
    assert "Number(descuento) || 0" in linea, "no cae al descuento general"


def test_el_TOTAL_de_la_linea_lleva_el_descuento_dentro():
    """Si la línea enseñara el bruto y el pie otra cifra, nadie sabría cuál de
    las dos es la buena."""
    src = _pantalla()
    assert "const importeLinea = Math.round(pvpNeto * (Number(m.qty) || 1) * 100) / 100;" in src
    assert "{eur(m.importeLinea)}" in src


def test_los_totales_se_SUMAN_DESDE_LAS_LINEAS():
    """Con un porcentaje único sobre el subtotal, una línea con su propio
    descuento enseñaría una cosa y el total cobraría otra."""
    src = _pantalla()
    assert "const baseImponible = filas.reduce((s, m) => s + m.importeLinea, 0);" in src
    assert "const importeDescuento = subtotalBruto - baseImponible;" in src


def test_el_MARGEN_se_mide_contra_lo_que_se_cobra():
    """Midiéndolo contra el PVP bruto, aplicar un 20 % de descuento no movería
    el margen ni un punto: el semáforo seguiría verde con la línea ya en
    pérdidas. Y el semáforo verde es por lo que alguien rebaja un poco más."""
    src = _pantalla()
    assert "const margen = coste == null ? null : pvpNeto - coste;" in src
    assert "margenSobreCoste(pvpNeto, coste)" in src


def test_el_ROTULO_del_descuento_no_miente():
    """«Dto. (20%)» con una línea al 0 % es una explicación falsa. El número
    bien y la etiqueta mintiendo es peor que no poner etiqueta (regla 16)."""
    src = _pantalla()
    i = src.index("const rotuloDescuento = ()")
    cuerpo = src[i:i + 400]
    assert "new Set(filas.map(m => m.dtoAplicado))" in cuerpo
    assert "usados.length === 1" in cuerpo
    assert "Descuento (${descuento}%)" not in src, (
        "ha vuelto el rótulo que da por hecho que el descuento es uno solo")


def test_el_pedido_guarda_el_BRUTO_y_el_descuento_APARTE():
    """Guardar el neto Y el porcentaje del pedido haría que la comisión
    descontara dos veces."""
    src = _pantalla()
    assert src.count("dtoPct: dtoDe(m),") == 2, (
        "el descuento de la línea no viaja en las DOS rutas (presupuesto y pedido)")
    assert src.count("price: (Number(m.pvp) || 0) * (Number(m.qty) || 1),") == 2, (
        "se está guardando el neto en `price`: la comisión lo descontaría otra vez")


# ─── EL CANDADO DEL COSTE ────────────────────────────────────────────────────

def test_con_el_candado_cerrado_el_coste_NO_SE_LEE():
    """DOS PETICIONES DEL MASTER QUE PARECEN CHOCAR Y NO CHOCAN.

      · 31/08 — las columnas ESTÁN SIEMPRE: cuando aparecían y desaparecían con
        el candado, la tabla se ensanchaba de golpe, la cabecera se salía y el
        PVP quedaba contra el borde.
      · 07/09 — «el coste que aparece ahora que no aparezca hasta que yo toque
        candado, por si saco algún presupuesto con cliente delante».

    Lo que molesta no es el hueco: es que se LEA. Hasta el 07/09, cerrado,
    ponía «•••» debajo de un rótulo que decía «Coste» — o sea que un cliente
    mirando por encima del hombro veía que ahí hay números escondidos.

    Así que la columna se queda (mismo ancho exacto, la tabla no se mueve) y no
    dice nada: ni cifra, ni puntos visibles, ni rótulo, ni `title`.
    """
    src = _pantalla()
    # Los tres puntos siguen ahí —para que la columna mida lo mismo— pero en
    # transparente.
    i = src.index("const OCULTO")
    marcador = src[i:i + 220]
    assert "•••" in marcador and "opacity-0" in marcador, (
        "o se ha perdido el marcador (la tabla se moverá al abrir el candado) "
        "o ha vuelto a ser visible (el cliente ve que hay un coste escondido)")
    # Y el rótulo del margen, apagado con el candado cerrado.
    j = src.index(">Margen s/coste</button>")
    assert "opacity-0" in src[max(0, j - 500):j], (
        "«Margen s/coste» se sigue leyendo con el candado cerrado")


def test_el_desglose_del_coste_no_se_ve_ni_pasando_el_raton():
    """En un portátil, un `title` con el desglose del casco, las puertas y la
    mano de obra se enseña solo con pasar el ratón por encima — con el candado
    cerrado y el cliente delante."""
    src = _pantalla()
    i = src.index("title={!verCoste ? '' : (m.coste == null ?")
    assert i > 0, "el `title` del coste no se calla con el candado cerrado"


def test_el_candado_SIGUE_ESTANDO_cuando_esta_cerrado():
    """Si el botón se fuera con las columnas, no habría forma de volver a
    abrirlas: la pantalla se quedaría sin coste para siempre."""
    src = _pantalla()
    i = src.index('data-testid="cm3-candado-coste"')
    cabecera = src[max(0, i - 900):i + 300]
    assert "{verCoste && (" not in cabecera.split("<th")[-2], (
        "el botón del candado está dentro de una columna que se oculta")
    assert "verCoste ? <><Unlock" in src


# ─── LAS MEDIDAS DEFINITIVAS, EN TODOS LOS MUEBLES ───────────────────────────

def test_se_puede_escribir_el_ALTO_definitivo_de_un_mueble():
    """El master, 07/09: «igual que en costados, que deje cambiar altura de los
    muebles y anchura». Sin esta casilla, un alto de 35 solo se podía apuntar
    como observación —y una medida escrita en un texto libre no la lee el
    pedido: se fabricaba con la altura del desplegable."""
    src = _pantalla()
    assert 'data-testid="cm3-alto-real-mueble"' in src
    i = src.index('data-testid="cm3-alto-real-mueble"')
    assert "setMedidaReal(m._k, 'altoReal'" in src[max(0, i - 600):i]


def test_la_medida_definitiva_NO_toca_el_precio():
    """El escalón dice lo que CUESTA; la medida es lo que se fabrica. Si
    escribir una cota moviera el importe, el presupuesto cambiaría solo
    mientras alguien ajusta medidas."""
    src = _pantalla()
    i = src.index("const setMedidaReal = (k, campo, v)")
    cuerpo = src[i:src.index("}));", i)]
    assert "pvp" not in cuerpo, "escribir la medida definitiva está tocando el precio"
    assert "replace(',', '.')" in cuerpo, (
        "sin admitir la coma, un 61,5 tecleado en español se pierde en silencio")


def test_la_medida_definitiva_SALE_EN_EL_PDF():
    """El master: «cuando pones una observación o una medida especial que la
    plasme en el documento de presupuesto, que luego será el mismo para
    pedidos». El papel que se firma llevaba la medida del desplegable."""
    src = _pantalla()
    assert "m.anchoReal ? `${m.anchoReal} cm *`" in src
    assert "m.altoReal ? `${m.altoReal} cm *`" in src
    assert "Medida definitiva de fabricación" in src, (
        "el asterisco sale sin explicar: en un presupuesto que se firma, eso "
        "es una duda")


def test_las_OBSERVACIONES_siguen_saliendo_en_el_PDF():
    src = _pantalla()
    assert "[Obs: ${m.obs.trim()}]" in src


# ─── LÍNEAS A MANO ───────────────────────────────────────────────────────────

def test_se_puede_meter_una_linea_ESCRITA_A_MANO():
    """El master: «que pueda meter líneas manuales escritas a mano y que pueda
    poner el precio que quiera y el descuento que quiera»."""
    src = _pantalla()
    assert 'data-testid="cm3-linea-manual"' in src
    i = src.index("const añadirLineaManual = ()")
    cuerpo = src[i:i + 1400]
    assert "pvpManual: true" in cuerpo, (
        "sin `pvpManual`, cambiar de tarifa le pisaría el precio escrito")
    assert "esManual: true" in cuerpo


def test_una_linea_a_mano_NO_es_un_mueble_y_no_paga_comision():
    """Regla 16: «las líneas manuales de servicios no llevan compensación de
    ningún tipo». Un transporte de 300 € no puede entrar en la valoración que
    decide el TRAMO del comercial."""
    from services.comisiones import es_mueble, base_de_comision
    src = _pantalla()
    i = src.index("const añadirLineaManual = ()")
    cuerpo = src[i:i + 1400]
    assert "familia: ''," in cuerpo, (
        "la línea a mano nace con familia: entraría en la comisión como mueble")
    assert es_mueble({"familia": "", "quantity": 1, "price": 300}) is False
    b = base_de_comision([{"familia": "BAJO", "quantity": 10, "price": 3000},
                          {"familia": "", "quantity": 1, "price": 300}])
    assert b["muebles"] == 10 and b["baseImponible"] == 3000.0


# ─── EMPEZAR OTRO PRESUPUESTO ────────────────────────────────────────────────

def test_hay_boton_de_NUEVO_presupuesto():
    src = _pantalla()
    assert 'data-testid="cm3-nuevo-presupuesto"' in src


def test_empezar_uno_nuevo_SUELTA_el_presupuesto_anterior():
    """Lo peligroso no son las líneas: es `savedId`. Con él puesto, «Guardar»
    ACTUALIZA el presupuesto del cliente anterior en vez de crear uno — se
    sobrescribe con la cocina del cliente de ahora, sin dar ningún error."""
    src = _pantalla()
    i = src.index("const nuevoPresupuesto = ()")
    cuerpo = src[i:src.index("\n  };", i)]
    for setter in ("setSavedId(null)", "setPedidoId(null)", "setMuebles([])",
                   "setCliente('')", "setRef('')", "setDescuento(0)"):
        assert setter in cuerpo, f"«Nuevo» no hace {setter}"
    assert "window.confirm" in cuerpo, "vaciar la pantalla no tiene deshacer"
    # La tarifa y los acabados son de la casa, no del cliente: no se tocan.
    assert "setTarifa(" not in cuerpo and "setAcabadoPuerta(" not in cuerpo


# ─── EL PDF CABE ─────────────────────────────────────────────────────────────

def test_el_pie_del_PDF_no_se_dibuja_FUERA_DE_LA_HOJA():
    """El master: «el pdf no cabe en una hoja, mira lo que pasa».

    `autoTable` parte la TABLA, pero lo que va después —observaciones y
    totales— se pintaba en `finalY` sin mirar si quedaba sitio: con una cocina
    larga, el cuadro de totales se dibujaba fuera del papel y el presupuesto
    salía SIN TOTAL. jsPDF no da ningún error por pintar fuera de la página.
    """
    src = _pantalla()
    assert "const ALTO_DEL_PIE = 50;" in src
    i = src.index("const ALTO_DEL_PIE")
    cuerpo = src[i:i + 400]
    assert "doc.internal.pageSize.getHeight()" in cuerpo
    # LA CONDICIÓN, no solo la llamada. Con `if (false)` el `doc.addPage()`
    # sigue escrito y no se ejecuta nunca: comprobar que la línea existe deja
    # pasar exactamente el fallo que esto vigila.
    assert "if (finalY + ALTO_DEL_PIE > LIMITE) {" in cuerpo, (
        "el salto de página ya no depende de si queda sitio")
    assert "doc.addPage();" in cuerpo


def test_las_observaciones_largas_no_se_salen_por_el_borde():
    """`doc.text` con un texto largo no lo corta: lo pinta en una línea que se
    sale del papel y se pierde."""
    src = _pantalla()
    assert "doc.splitTextToSize(observacionesGenerales.trim(), 100)" in src


def test_un_presupuesto_de_dos_hojas_va_NUMERADO():
    """La segunda hoja es donde va el total: traspapelarla no puede pasar
    desapercibido."""
    src = _pantalla()
    assert "Página ${i} de ${hojas}" in src
