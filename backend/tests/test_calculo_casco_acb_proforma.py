# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
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


# ─── 4. El descuento no viene puesto ────────────────────────────────────────

def test_los_descuentos_nacen_vacios():
    """Los mete el master a mano (CLAUDE.md, regla 5). Un descuento que aparece
    solo se lee como un dato del sistema cuando no lo ha confirmado nadie."""
    src = _leer(IMPORTER)
    i = src.index("const P_DEFAULT")
    linea = src[i:src.index("\n", i)]
    assert "desc1: ''" in linea and "desc2: ''" in linea, (
        f"los descuentos vuelven a venir rellenos: {linea}")
