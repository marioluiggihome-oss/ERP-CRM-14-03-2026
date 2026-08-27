# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del emparejamiento de cascos ACB en la proforma.

De aqui sale el COSTE de cada mueble, y de ahi el margen. Un casco mal
emparejado no da ningun error: da un precio, y el precio es creible.

EL FALLO QUE ESTO IMPIDE (08/08, lo vio el master)
--------------------------------------------------
El ancho se sacaba del numero de delante del codigo (`/^(\\d{2,3})/`). Ese
numero NO es el ancho: en la nomenclatura Alvic es el ALTO.

    90AP/1P-60   -> alto 90 cm, ancho 60 cm
    80BP/1P      -> bajo de 80 de alto
    22A2/2P      -> columna de 220

Asi que un alto de 90x60 se emparejaba con el casco de 900 de ANCHO. En la
tarifa ACB (que va en milimetros):

    Alto Con Balda  600 x 900  ->  43,83 EUR
    Alto Con Balda  900 x 900  ->  55,37 EUR

11,54 EUR de mas POR MUEBLE, en un error que solo se ve si alguien se sabe la
tarifa de memoria. En una cocina entera de altos se multiplica.

Lo que se protege:

1. LOS PRECIOS DE LA TARIFA. Si el catalogo cambia, esto se pone rojo y hay que
   mirarlo a proposito, no descubrirlo en una factura.

2. EL ANCHO SALE DE LA PROFORMA, NO DEL CODIGO. La proforma trae `ancho` en mm;
   el codigo no sirve para eso.

3. SIN ANCHO NO SE EMPAREJA. Antes caia a 600 por defecto: un ancho inventado
   que ademas ponia precio. Ahora la linea sale «sin equivalencia», que es la
   verdad, y se le elige el casco a mano.

4. EL COLOR SE LLAMA COMO EN LA TARIFA. El `grafito` se rotulaba «Antracita»
   —que es un acabado de Alvic, no el nombre del casco—, asi que en pantalla
   ponia una cosa y en la tarifa que hay que consultar ponia otra.
"""
import json
import os
import re

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CATALOGO = os.path.join(RAIZ, "frontend", "src", "data", "cascos.js")
IMPORTER = os.path.join(RAIZ, "frontend", "src", "components", "ProformaImporter.jsx")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def _cascos():
    """Saca la lista de cascos del catalogo JS sin ejecutar JavaScript.

    El fichero es `export const CASCOS = [ {...}, ... ];` con objetos de
    claves sin comillas. Se normalizan a JSON para poder leerlos desde aqui.
    """
    src = _leer(CATALOGO)
    # `export const CASCOS =` EXACTO: buscando solo "export const CASCOS" se
    # enganchaba a `CASCOS_COLORES`, que esta antes en el fichero, y la prueba
    # leia dos colores en vez de mil cascos.
    m = re.search(r"export\s+const\s+CASCOS\s*=", src)
    assert m, "no se encuentra `export const CASCOS =` en el catalogo"
    i = src.index("[", m.end())
    # Recorre equilibrando corchetes para quedarse con el array entero.
    prof, fin = 0, None
    for j in range(i, len(src)):
        if src[j] == "[":
            prof += 1
        elif src[j] == "]":
            prof -= 1
            if prof == 0:
                fin = j + 1
                break
    bruto = src[i:fin]
    bruto = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1"\2":', bruto)
    bruto = bruto.replace("'", '"')
    bruto = re.sub(r",(\s*[}\]])", r"\1", bruto)
    return json.loads(bruto)


def _alto_con_balda(ancho, alto, grosor=19):
    for c in _cascos():
        if (c.get("tipo") == "Alto Con Balda" and c.get("grosor") == grosor
                and c.get("ancho") == ancho and c.get("alto") == alto):
            return c
    return None


# ─── 1. Los precios de la tarifa ────────────────────────────────────────────

def test_el_alto_de_600x900_vale_43_83():
    """El numero que dio el master, con el -50% ya aplicado."""
    c = _alto_con_balda(600, 900)
    assert c is not None, "no esta en el catalogo el Alto Con Balda 600x900"
    assert c["precios"]["grafito"] == 43.83


def test_el_alto_de_900x900_vale_55_37():
    """El que se cogia por error. Se fija para que la diferencia quede escrita."""
    c = _alto_con_balda(900, 900)
    assert c is not None
    assert c["precios"]["grafito"] == 55.37


def test_el_ancho_cambia_el_precio_lo_bastante_como_para_importar():
    de600 = _alto_con_balda(600, 900)["precios"]["grafito"]
    de900 = _alto_con_balda(900, 900)["precios"]["grafito"]
    assert round(de900 - de600, 2) == 11.54, (
        "la diferencia entre el casco de 600 y el de 900 ha cambiado: "
        "revisa si la tarifa se ha actualizado a proposito")


def test_el_alto_de_700x900_tambien_existe():
    """El master dijo que pasaba tambien con el de 90x70."""
    c = _alto_con_balda(700, 900)
    assert c is not None and c["precios"]["grafito"] == 47.54


def test_la_tarifa_va_en_milimetros():
    """Si alguien la pasara a cm, los emparejamientos se irian por un factor 10
    y todos los precios saldrian del casco mas pequenio."""
    c = _alto_con_balda(600, 900)
    assert c["ancho"] == 600 and c["alto"] == 900 and c["fondo"] == 330


# ─── 1-bis. Las columnas: cada gama tiene SUS tipos ─────────────────────────
#
# Segundo numero que dio el master: una COLUMNA HORNO MICRO de 220 salia a
# 139,59 EUR cuando en grafito vale 150,46. Dos fallos encadenados:
#
#   a) TODA columna caia en «Columna Despensa» —horno y micro incluidos—.
#   b) «Columna Despensa» NO EXISTE en 19 mm. Al no encontrar nada, el
#      emparejador se caia al respaldo y cogia un casco de 16 mm en Roble.
#
# Por eso el tipo depende del GROSOR: no es nomenclatura, es que en cada gama
# existen unos cascos y no otros.

def _por_tipo(tipo, grosor, ancho, alto):
    for c in _cascos():
        if (c.get("tipo") == tipo and c.get("grosor") == grosor
                and c.get("ancho") == ancho and c.get("alto") == alto):
            return c
    return None


def test_la_columna_horno_micro_de_220_vale_150_46_en_grafito():
    """El numero del master."""
    c = _por_tipo("Columna Horno-Micro 2000/2200", 19, 600, 2200)
    assert c is not None, "no esta en el catalogo la Columna Horno-Micro 2000/2200"
    assert c["precios"]["grafito"] == 150.46


def test_lo_que_cogia_por_error_era_un_roble_de_16():
    """«Columna Despensa 300 · Roble 16» a 139,59: otro tipo, otra gama y otro
    color. Se fija para que la diferencia quede escrita."""
    c = _por_tipo("Columna Despensa", 16, 300, 2200)
    assert c is not None and c["precios"]["roble"] == 139.59


def test_columna_despensa_no_existe_en_19mm():
    """Es la raiz del fallo: mapear ahi una columna de la gama en kit garantiza
    que el filtro de 19 mm no encuentre nada y se caiga al respaldo."""
    hay = [c for c in _cascos()
           if c.get("tipo") == "Columna Despensa" and c.get("grosor") == 19
           and (c.get("precios") or {}).get("grafito") is not None]
    assert hay == [], (
        "ahora SI existe Columna Despensa en 19 mm: revisa el mapeo de tipos, "
        "puede que ya no haga falta desdoblarlo por gama")


def test_en_19mm_las_columnas_se_llaman_con_sus_nombres_de_gama():
    src = _leer(IMPORTER)
    i = src.index("const _tipo_acb_auto")
    cuerpo = src[i:src.index("\n};", i)]
    for nombre in ("Columna Horno-Micro 2000/2200", "Columna Horno 2000/2200",
                   "Columna Con Baldas"):
        assert nombre in cuerpo, f"falta el tipo de 19 mm «{nombre}»"
    assert "grosor" in cuerpo, (
        "el tipo ya no depende del grosor: en 19 mm y en 16 mm las columnas se "
        "llaman distinto y no existen las mismas")


def test_el_horno_y_el_horno_micro_no_son_el_mismo_casco():
    a = _por_tipo("Columna Horno 2000/2200", 19, 600, 2200)
    b = _por_tipo("Columna Horno-Micro 2000/2200", 19, 600, 2200)
    assert a is not None and b is not None
    # Hoy coinciden en precio, pero son referencias distintas: lo que se
    # protege es que exista cada una, no que valgan lo mismo.
    assert a["tipo"] != b["tipo"]


# ─── 2. El ancho sale de la proforma, no del codigo ─────────────────────────

def _cuerpo_medidas():
    src = _leer(IMPORTER)
    i = src.index("const _medidas_mm")
    return src[i:src.index("\n};", i)]


def test_el_ancho_no_se_saca_del_codigo():
    cuerpo = _cuerpo_medidas()
    assert "it.cod" not in cuerpo, (
        "se esta volviendo a sacar la medida del codigo: el numero de delante "
        "es el ALTO, no el ancho (90AP/1P-60 es 90 de alto y 60 de ancho)")
    assert "it.ancho" in cuerpo, "el ancho tiene que venir de la proforma"


def test_sin_ancho_no_se_inventa_un_600():
    cuerpo = _cuerpo_medidas()
    assert "600" not in cuerpo, (
        "ha vuelto el ancho por defecto de 600 mm: es una medida inventada, y "
        "encima le pone precio")
    assert "null" in cuerpo, "sin ancho hay que devolver null, no un numero"


def test_sin_ancho_la_linea_no_se_empareja():
    src = _leer(IMPORTER)
    i = src.index("const _match_acb")
    cuerpo = src[i:src.index("\n};", i)]
    assert "ancho == null" in cuerpo, (
        "`_match_acb` empareja aunque no haya ancho: elegiria el casco «mas "
        "parecido» sin saber el ancho, que es poner un precio a dedo")


# ─── 3. El color se llama como en la tarifa ─────────────────────────────────

def test_el_grafito_se_llama_grafito():
    src = _leer(IMPORTER)
    i = src.index("const COLOR_LBL")
    cuerpo = src[i:src.index("};", i)]
    assert "grafito: 'Grafito'" in cuerpo, (
        "el grafito vuelve a rotularse «Antracita»: en pantalla pondria una "
        "cosa y en la tarifa que hay que consultar, otra")


def test_el_catalogo_y_la_pantalla_llaman_igual_al_grafito():
    """Una sola verdad para el nombre del color."""
    cat = _leer(CATALOGO)
    assert "{ id: 'grafito', label: 'Grafito' }" in cat
    src = _leer(IMPORTER)
    assert "grafito: 'Grafito'" in src


# ─── 3-bis. El color LLEVA su grosor, y no se eligen por separado ───────────
#
# Cada color existe en UN solo grosor: grafito en 19, aluminio y blanco en 16,
# olmo en 18. Eran dos desplegables sueltos, asi que se podia pedir
# «Grafito 16» —que no esta en tarifa—, el emparejador se caia al respaldo y
# traia OTRO color sin decirlo. Eso es lo que producia proformas con unas
# lineas en Grafito 19 y otras en Roble 16.

def _grosor_por_color():
    """En que grosor existe cada color, sacado del catalogo."""
    m = {}
    for c in _cascos():
        for col, precio in (c.get("precios") or {}).items():
            if precio is not None and col not in m:
                m[col] = c.get("grosor")
    return m


def test_cada_color_existe_en_un_solo_grosor():
    """Es la premisa de atar el grosor al color. Si algun dia un color sale en
    dos grosores, esto se pone rojo y hay que volver a separar los desplegables
    —no descubrirlo por un precio raro."""
    grosores = {}
    for c in _cascos():
        for col, precio in (c.get("precios") or {}).items():
            if precio is not None:
                grosores.setdefault(col, set()).add(c.get("grosor"))
    multiples = {col: sorted(g) for col, g in grosores.items() if len(g) > 1}
    assert multiples == {}, (
        f"estos colores existen en varios grosores: {multiples}. El grosor ya no "
        f"se puede derivar del color solo")


def test_el_grafito_es_de_19_y_el_aluminio_de_16():
    m = _grosor_por_color()
    assert m["grafito"] == 19
    assert m["aluminio"] == 16
    assert m["blanco"] == 16
    assert m["olmo"] == 18


def test_el_grosor_se_deriva_del_catalogo_y_no_a_mano():
    src = _leer(IMPORTER)
    assert "GROSOR_DE_COLOR" in src, "no se deriva el grosor del color"
    i = src.index("const GROSOR_DE_COLOR")
    cuerpo = src[i:src.index("})();", i)]
    assert "CASCOS" in cuerpo, (
        "el grosor de cada color se ha escrito a mano: si ACB cambia la tarifa, "
        "la pantalla dira una cosa y el catalogo otra")


def test_ya_no_hay_un_desplegable_de_grosor_suelto_en_la_linea():
    """Con dos desplegables se podia pedir una combinacion que no existe."""
    src = _leer(IMPORTER)
    assert "<option value={16}>16mm</option>" not in src, (
        "ha vuelto el selector de grosor suelto: se puede volver a pedir "
        "«Grafito 16», que no esta en tarifa")


def test_el_color_se_ensenia_con_su_grosor():
    src = _leer(IMPORTER)
    assert "colorConGrosor" in src, (
        "el color ya no se ensenia con el grosor pegado: en la tarifa hay que "
        "pedir «Grafito 19», no «Grafito»")


# ─── 3-ter. Un costado no es un casco ───────────────────────────────────────

def test_las_piezas_sueltas_no_piden_casco():
    """El lector marca `esMueble: true` en TODAS las filas, asi que un
    COSTADO VISTO, un zocalo o una regleta salian en rojo con «sin
    equivalencia» y un boton pidiendo un casco que no van a tener nunca: son
    tablero.

    La lista de palabras ya no vive dentro de `_es_pieza_suelta`: esta en las
    constantes `_ES_*`, que son las MISMAS que usan el emparejador de cascos y
    el destino del pedido (antes habia cuatro copias y podian separarse). Se
    comprueban ahi, y ademas que el predicado las consulte TODAS: si dejara de
    mirar una, esa familia volveria a pedir casco.
    """
    src = _leer(IMPORTER)
    assert "_es_pieza_suelta" in src, "ha vuelto a tratarse todo como mueble"

    familias = ("_ES_PUERTA", "_ES_COSTADO", "_ES_REGLETA", "_ES_TABLERO")
    constantes = ""
    for fam in familias:
        j = src.index(f"const {fam}")
        constantes += src[j:src.index("\n", j)]

    for pieza in ("COSTADO", "REGLETA", "COPETE", "ZOCALO", "TRASERA"):
        assert pieza in constantes, f"«{pieza}» vuelve a contarse como mueble"

    i = src.index("const _es_pieza_suelta")
    cuerpo = src[i:src.index("\n};", i)]
    for fam in familias:
        assert fam in cuerpo, f"`_es_pieza_suelta` ha dejado de mirar {fam}"


def test_un_mueble_que_no_se_reconoce_SIGUE_pidiendo_casco():
    """CANDADO de matiz. «No es un mueble» y «no lo he sabido leer» son cosas
    distintas: si se confunden, el mueble raro pierde el boton «Elegir casco»
    justo donde hace falta. Por eso la lista es EXPLICITA y no «lo que
    `_tipo_acb_auto` no ha sabido clasificar»."""
    src = _leer(IMPORTER)
    # La condicion ocupa varias lineas: se lee hasta el final de la expresion.
    i = src.index("esMueble: it.esMueble !== false")
    expr = src[i:src.index(",\n", src.index("_es_herraje", i))]
    assert "_es_pieza_suelta" in expr
    assert "_tipo_acb_auto" not in expr, (
        "`esMueble` vuelve a depender de si se ha sabido deducir el tipo: un "
        "mueble no reconocido dejaria de poder elegir casco a mano")


def test_un_herraje_no_pide_que_le_elijan_un_casco():
    """Un «TIRADOR T70 NEGRO MATE» salia en rojo con «sin equivalencia» y un
    boton «Elegir casco». Un tirador no va a tener casco nunca, y encima se
    colaba en la relacion MV tipado como CASCO ACB."""
    src = _leer(IMPORTER)
    i = src.index("esMueble: it.esMueble !== false")
    expr = src[i:src.index(",\n", src.index("_es_herraje", i))]
    assert "_es_herraje" in expr, (
        "un herraje vuelve a contar como mueble: pedira un casco que no existe "
        "y se colara en la lista de cascos del pedido")


# ─── 3 bis. LAS VARIANTES DEL MUEBLE NO DICEN LO QUE EL MUEBLE ES ───────────
#
# 14/08/2026, el master: «ha dejado de detectar bien los cascos de acb».
#
# Alvic escribe el mueble y, pegadas detras, sus variantes:
#
#     «BAJO 2 PUERTAS 1 CAJON SUPERIOR. Tirador T000 - SIN TIRADOR ,»
#
# «SIN TIRADOR» estaba en la lista de TABLEROS y «TIRADOR» en la de HERRAJES.
# Resultado: TODO mueble sin tirador —o sea toda la cocina de gola, que es la
# normal de esta casa— salia como pieza suelta Y como herraje, y se quedaba SIN
# CASCO. Un guion en la columna del casco, cero euros de coste, y ningun error.


def test_un_mueble_sin_tirador_sigue_siendo_un_mueble():
    """CANDADO PRINCIPAL de esto. «SIN TIRADOR» describe el TIRADOR."""
    src = _leer(IMPORTER)
    i = src.index("const _ES_TABLERO")
    linea = src[i:src.index("\n", i)]
    assert "SIN TIRADOR" not in linea, (
        "«SIN TIRADOR» vuelve a estar en la lista de TABLEROS: toda la cocina "
        "de gola se quedara otra vez sin casco y sin coste")


def test_lo_que_una_linea_es_se_decide_por_como_empieza():
    src = _leer(IMPORTER)
    assert "const _ES_MODULO_INI" in src, (
        "ya no se mira el principio de la linea: las palabras de las variantes "
        "(tirador, bisagra) volveran a decidir lo que es el mueble")
    i = src.index("const _ES_MODULO_INI")
    linea = src[i:src.index("\n", i)]
    for palabra in ("BAJO", "ALTO", "COLUMNA", "SEMICOLUMNA"):
        assert palabra in linea, f"«{palabra}» ya no empieza un modulo"


@pytest.mark.parametrize("clasificador", [
    "_es_puerta", "_es_costado", "_es_regleta", "_es_herraje", "_es_pieza_suelta"])
def test_ningun_clasificador_puede_convertir_un_modulo_en_otra_cosa(clasificador):
    """Un mueble es un mueble aunque su descripcion nombre el tirador que lleva
    puesto. Si un solo clasificador se olvida de mirarlo, ese mueble se cae de
    los cascos por ese camino y no se entera nadie."""
    src = _leer(IMPORTER)
    i = src.index(f"const {clasificador} = ")
    fin = src.index("\n};", i) if "\n};" in src[i:i + 400] else i + 400
    assert "_es_modulo" in src[i:fin], (
        f"`{clasificador}` ya no comprueba si la linea es un modulo: un "
        f"«BAJO … Tirador T000 - SIN TIRADOR» volvera a salir sin casco")


def test_el_corte_de_variantes_no_se_come_la_linea_del_tirador():
    """«T000 - SIN TIRADOR» es la linea del TIRADOR entera, no un mueble con
    cola. Cortando por la palabra quedaria «T000 - SIN», que ya no se reconoce
    como nada y acabaria pidiendo casco. Fuera de un modulo solo se corta si hay
    un SEPARADOR de verdad."""
    src = _leer(IMPORTER)
    i = src.index("const _sin_variantes")
    cuerpo = src[i:src.index("\n};", i)]
    assert "[.,;]" in cuerpo, (
        "el corte de variantes ya no exige separador: se comera el nombre de "
        "los articulos que se llaman como su variante")
    assert "_es_modulo" in cuerpo, \
        "el corte sin separador ha dejado de reservarse a los modulos"


# ─── 3 ter. TODOS LOS CAMPOS SE PUEDEN CORREGIR ────────────────────────────


@pytest.mark.parametrize("mapa", [
    "puertasEditadas", "costadosEditados", "regletasEditadas", "cascosEditados"])
def test_cada_categoria_del_editor_se_puede_corregir_a_mano(mapa):
    """Los CASCOS eran los unicos en solo lectura: cantidad, alto y ancho salian
    del lector del PDF y, si venian mal, no habia forma de tocarlos — y son
    justo las lineas que van al proveedor."""
    src = _leer(IMPORTER)
    assert f"const [{mapa}" in src or f"{mapa} = {{}}" in src, \
        f"ya no hay correcciones a mano para {mapa}"
    assert f"{mapa}[rawIndex]" in src, f"{mapa} no se lee al pintar la linea"


def test_las_unidades_tambien_se_corrigen():
    """Si el lector lee 1 donde pone 2, se pide la mitad del material y no lo
    dice nadie."""
    src = _leer(IMPORTER)
    assert "const _uds = (mapa, i, item)" in src, \
        "las unidades vuelven a leerse solo del PDF, sin poder corregirlas"
    assert "'uds', e.target.value" in src, \
        "no hay ningun campo en pantalla para corregir las unidades"


# ─── 4. El descuento no viene puesto ────────────────────────────────────────

def test_los_descuentos_nacen_vacios():
    """Los mete el master a mano (CLAUDE.md, regla 5). Un descuento que aparece
    solo se lee como un dato del sistema cuando no lo ha confirmado nadie."""
    src = _leer(IMPORTER)
    i = src.index("const P_DEFAULT")
    linea = src[i:src.index("\n", i)]
    assert "desc1: ''" in linea and "desc2: ''" in linea, (
        f"los descuentos vuelven a venir rellenos: {linea}")


# ─── 6. EL SOBREMODULO NO ES UN ALTO ───────────────────────────────────────
#
# 14/08/2026. El master, preguntado por que casco monta encima de la columna de
# horno-micro: «depende de la altura pero normalmente es un casco de sesenta por
# 90 x 58 de fondo».
#
# Ese 58 DE FONDO lo cambia todo. Aqui se devolvia «Alto Con Balda», que es un
# mueble COLGADO de 330 de fondo. El sobremodulo va encima de una columna, o sea
# que lleva el fondo de la columna: 580. Son dos muebles distintos.
#
# Y costaba dinero por partida doble, porque «Alto Con Balda» NO EXISTE en
# Blanco Esp.: ademas de coger el casco equivocado, se caia a otro color. En la
# proforma del master salia «Alto Con Balda 600 · Aluminio 16» a 39,12 EUR donde
# el bueno es «Sobre Columna Horno 600x900» en Blanco Esp. a 69,40 EUR.
# 30,28 EUR de menos POR MUEBLE, y el unico aviso era el del color.


def test_el_casco_que_dijo_el_master_existe_y_es_el_de_580_de_fondo():
    """60 x 90 x 58, en su gama. Si el catalogo cambiara, esto se pone rojo."""
    cascos = _cascos()
    iguales = [c for c in cascos
               if c["ancho"] == 600 and c["alto"] == 900 and c["fondo"] == 580]
    assert iguales, "ya no hay ningun casco de 600x900x580 en el catalogo"
    tipos = {c["tipo"] for c in iguales}
    assert tipos == {"Sobre Columna Horno"}, (
        f"el casco de 600x900x580 ha dejado de ser «Sobre Columna Horno»: {tipos}")
    en_blanco = [c for c in iguales if c["precios"].get("blancoEsp") is not None]
    assert en_blanco, "«Sobre Columna Horno» 600x900 ya no existe en Blanco Esp."


def test_un_sobremodulo_no_se_valora_como_un_mueble_alto():
    """CANDADO PRINCIPAL. Un alto tiene 330 de fondo; un sobremodulo, 580."""
    src = _leer(IMPORTER)
    i = src.index("if (/SOBREMODULO|SOBREMÓDULO")
    cuerpo = src[i:i + 700]
    assert "'Alto Con Balda'" not in cuerpo, (
        "el sobremodulo vuelve a valorarse como «Alto Con Balda»: es un casco "
        "de 330 de fondo donde va uno de 580, y en Blanco Esp. ni siquiera "
        "existe — se caeria otra vez a otro color")
    for familia in ("Sobre Columna Horno", "Sobre Columna Horno-Micro"):
        assert f"'{familia}'" in cuerpo, f"ya no se contempla «{familia}»"


def test_el_sobremodulo_se_mira_antes_que_la_columna():
    """«SOBRE COLUMNA HORNO» lleva la palabra COLUMNA dentro: si la regla de la
    columna va primero, un sobremodulo se valora como la columna entera."""
    src = _leer(IMPORTER)
    assert src.index("if (/SOBREMODULO|SOBREMÓDULO") < src.index("if (/COLUMNA/.test(t))"), (
        "la regla de COLUMNA ha vuelto a ir delante: un «SOBRE COLUMNA HORNO» "
        "se valorara como la columna completa")


def test_la_altura_decide_que_sobremodulo_es():
    """«Depende de la altura», dijo el master. Horno-Micro llega a 700; el de
    900 solo existe como «Sobre Columna Horno»."""
    src = _leer(IMPORTER)
    i = src.index("if (/SOBREMODULO|SOBREMÓDULO")
    cuerpo = src[i:i + 700]
    assert "alto >= 800" in cuerpo, (
        "la altura ya no decide: un sobremodulo de 900 acabara en un casco de "
        "700 y a fabrica ira una medida que no es")


def test_antes_de_cambiar_el_color_se_prueba_otra_familia():
    """«Sobre Columna» no existe en la gama en kit. Con un solo tipo, esas
    cocinas se valoraban con un casco de OTRO COLOR — y el color se ve en el
    mueble montado; el nombre de la familia, no."""
    src = _leer(IMPORTER)
    assert "_TIPOS_ALTERNATIVOS" in src, \
        "ya no hay familias alternativas: se volvera a cambiar de color"
    i = src.index("let pool = [];")
    cuerpo = src[i:i + 800]
    assert "_TIPOS_ALTERNATIVOS[tipoAcb]" in cuerpo, \
        "el emparejador ya no prueba familias alternativas antes de degradar el color"


def test_cambiar_de_familia_no_se_hace_en_silencio():
    """Regla de la casa: nada se corrige sin decirlo. Un tipo cambiado sin aviso
    da un precio creible que nadie revisa."""
    src = _leer(IMPORTER)
    assert "_tipoSustituido" in src, \
        "el cambio de familia ha vuelto a hacerse en silencio"
    assert "No hay «" in src, \
        "el aviso de familia sustituida ya no sale en pantalla"


def test_con_el_mismo_ancho_se_coge_el_alto_MAS_PARECIDO():
    """Cogia el primero del catalogo. Con un sobremodulo de 1500 y cascos de 700
    y 900, se llevaba el de 700 solo por estar antes en el fichero."""
    src = _leer(IMPORTER)
    i = src.index("const mismoAncho = pool.filter")
    cuerpo = src[i:i + 500]
    assert "reduce" in cuerpo and "Math.abs" in cuerpo, (
        "vuelve a cogerse el primer casco del mismo ancho en vez del de alto "
        "mas parecido")
