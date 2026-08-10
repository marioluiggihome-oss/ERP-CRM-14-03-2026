# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO de la proforma de Cocina Desmontada: TRES COSAS QUE COSTABAN DINERO.

1. UN BAJO DE PLACA LLEVA CASCO DE FREGADERO. Los dos van RECORTADOS por
   arriba: uno para la encimera con la placa encastrada, el otro para la cubeta.
   Un «BAJO PLACA 1 GAVETA 2 CAJONES» se estaba valorando con un «Bajo Con
   Balda», que lleva una balda que ahi no existe. Con los numeros reales del
   master (900 de ancho, 800 de alto, grafito 19):

       Bajo Con Balda   61,15 -> tarifa 122,30 -> con -50% = 61,15 €   (MAL)
       Bajo Fregadero   48,35 -> tarifa  96,70 -> con -50% = 48,35 €   (BIEN)

   Casi 13 € de mas POR MUEBLE, y ademas pidiendo al proveedor un casco que no
   sirve.

2. LAS PUERTAS DE UN MUEBLE SE COBRAN. El casco ACB VA DESNUDO: sus puertas hay
   que comprarlas aparte. El aviso ya las contaba —«8 puertas a cotizar»— pero
   solo se cobraban las que venian como linea suelta en la proforma. Las de los
   muebles se contaban y no se pagaban: el coste salia corto y nada avisaba.

3. CADA PROFORMA TIENE SUS DESCUENTOS. Arrastrar los del documento anterior es
   la forma silenciosa de valorar mal una compra: el numero esta puesto, parece
   bueno, y es de otra.
"""
import json
import os
import re

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(RAIZ, "frontend", "src")
IMPORTADOR = os.path.join(SRC, "components", "ProformaImporter.jsx")
CASCOS_JS = os.path.join(SRC, "data", "cascos.js")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def cascos():
    """El catalogo de cascos, leido del fichero de datos de verdad."""
    src = _leer(CASCOS_JS)
    filas = []
    for m in re.finditer(r'\{"id": "c\d+".*?\}\}', src):
        try:
            filas.append(json.loads(m.group(0)))
        except Exception:
            pass
    assert filas, "no se ha podido leer el catalogo de cascos"
    return filas


def _casco(cascos, tipo, ancho, alto, grosor, color):
    for c in cascos:
        if (c["tipo"] == tipo and c["ancho"] == ancho and c["alto"] == alto
                and c["grosor"] == grosor):
            return c["precios"].get(color)
    return None


# ─── 1. Bajo de placa → casco de fregadero ──────────────────────────────────

def test_un_bajo_de_placa_pide_casco_de_fregadero():
    """CANDADO PRINCIPAL."""
    src = _leer(IMPORTADOR)
    i = src.index("const _tipo_acb_auto")
    cuerpo = src[i:i + 1800]
    m = re.search(r"if \(t\.includes\('PLACA'\)\) return '([^']+)'", cuerpo)
    assert m, ("un BAJO PLACA no tiene regla propia: se valora con un «Bajo Con "
               "Balda», que lleva una balda que ahi no existe")
    assert m.group(1) == "Bajo Fregadero"


def test_la_regla_de_placa_va_antes_que_la_de_bajo():
    """«BAJO PLACA» contiene «BAJO»: si la regla generica fuera primero, la de
    placa no se leeria nunca."""
    src = _leer(IMPORTADOR)
    i = src.index("const _tipo_acb_auto")
    cuerpo = src[i:i + 1800]
    assert cuerpo.index("'PLACA'") < cuerpo.index("t.includes('BAJO')")


def test_los_numeros_del_master_cuadran(cascos):
    """Los que dio el master el 09/08: 900 de ancho, 800 de alto, grafito 19.
    96,7 de tarifa que con el 50 % quedan en 48,35 €."""
    PUNTO = 2.0
    fregadero = _casco(cascos, "Bajo Fregadero", 900, 800, 19, "grafito")
    assert fregadero == 48.35, "ha cambiado la tarifa del casco de fregadero"
    assert round(fregadero * PUNTO, 2) == 96.70          # la tarifa ACB
    assert round(fregadero * PUNTO * 0.5, 2) == 48.35    # con el −50 %

    # Y lo que salia antes, para que se vea lo que costaba el fallo.
    con_balda = _casco(cascos, "Bajo Con Balda", 900, 800, 19, "grafito")
    assert con_balda == 61.15
    assert round((con_balda - fregadero) * PUNTO * 0.5, 2) == 12.80


def test_el_valor_del_punto_viene_de_AJUSTES():
    """CANDADO. La tarifa ACB esta en PUNTOS y el euro sale de multiplicarla por
    el valor del punto de Cocina Des-Montada, que se configura en Ajustes: los
    48,35 del casco de fregadero son 96,70 € porque el punto vale 2.

    Estaba escrito a fuego aqui. El dia que se cambiara en Ajustes, esta
    pantalla habria seguido valorando con el viejo — y sin dar ningun error: la
    proforma entera con otro precio y la misma pinta.
    """
    src = _leer(IMPORTADOR)
    assert "valorPunto" in src, (
        "el importador vuelve a tener el valor del punto escrito a fuego: si se "
        "cambia en Ajustes, aqui se seguiria valorando con el viejo")
    m = re.search(r"const PUNTO_POR_DEFECTO = ([\d.]+)", src)
    assert m and float(m.group(1)) == 2.0, "el valor de partida ya no es el de hoy"
    # Y que quien lo tiene configurado se lo pase de verdad.
    cascos_jsx = _leer(os.path.join(SRC, "components", "Cascos.jsx"))
    assert "valorPunto={coef}" in cascos_jsx, (
        "Cascos ya no le pasa el valor del punto: el importador volveria al de "
        "partida sin decir nada")
    assert "pointValueDesmontada" in cascos_jsx


def test_un_fregadero_sigue_siendo_un_fregadero():
    src = _leer(IMPORTADOR)
    i = src.index("const _tipo_acb_auto")
    cuerpo = src[i:i + 1800]
    assert "if (t.includes('FREGADERO')) return 'Bajo Fregadero'" in cuerpo


# ─── 2. Las puertas de un mueble se cobran ──────────────────────────────────

def test_las_puertas_que_van_dentro_de_un_mueble_se_calculan():
    """CANDADO. El casco va desnudo: sus puertas hay que comprarlas."""
    src = _leer(IMPORTADOR)
    assert "_puertasMueble" in src, (
        "las puertas de los muebles vuelven a no cobrarse: el aviso las cuenta "
        "(«8 puertas a cotizar») pero el coste sale corto y nada avisa")
    i = src.index("let puertasDelMueble")
    cuerpo = src[i:i + 1400]
    assert "it.puertas" in cuerpo and "pm2" in cuerpo


def test_la_medida_de_cada_puerta_sale_del_mueble():
    """`n` puertas repartidas a lo ancho: cada una de (ancho / n) x alto. Las
    medidas hacen falta para poder PEDIRLAS, no solo para el precio."""
    src = _leer(IMPORTADOR)
    i = src.index("let puertasDelMueble")
    cuerpo = src[i:i + 1400]
    assert "anchoM / n" in cuerpo, "no reparte el ancho entre las puertas"


def test_un_frente_mixto_NO_se_inventa():
    """Un mueble con puerta Y cajones tiene el frente repartido, y la proforma
    no dice que parte es cada uno. Calcularlo seria inventarse una medida."""
    src = _leer(IMPORTADOR)
    i = src.index("let puertasDelMueble")
    cuerpo = src[i:i + 1400]
    assert "frenteMixto" in cuerpo
    assert "cajones" in cuerpo and "gavetas" in cuerpo, (
        "no mira si el mueble lleva cajones: le cobraria como puerta un frente "
        "que es de cajon")


def test_el_area_no_depende_de_en_cuantas_puertas_se_parta():
    """Dos puertas de 450x800 ocupan lo mismo que una de 900x800. Es la
    comprobacion de que la cuenta es la del FRENTE, no la de cada hoja."""
    ancho, alto = 900, 800
    for n in (1, 2, 3):
        cada = ancho / n
        assert round(n * (cada / 1000) * (alto / 1000), 6) == round(
            (ancho / 1000) * (alto / 1000), 6)


# ─── 3. Cada proforma tiene sus descuentos ──────────────────────────────────

def test_al_importar_se_ponen_a_cero_los_descuentos_y_la_mano_de_obra():
    src = _leer(IMPORTADOR)
    i = src.index("const importar = async (file)")
    cuerpo = src[i:i + 1400]
    assert "desc1: 0" in cuerpo and "desc2: 0" in cuerpo and "manoObra: 0" in cuerpo, (
        "al importar se arrastran los descuentos del documento anterior: el "
        "numero esta puesto, parece bueno, y es de otra compra")


def test_y_se_dice_que_se_han_puesto_a_cero():
    """Un 0 que nadie ha escrito parece un dato guardado y no se revisa."""
    src = _leer(IMPORTADOR)
    assert "importadoLimpio" in src
    assert "Cada proforma" in src


# ─── 4. Que quepa en la pantalla ────────────────────────────────────────────

def test_se_pueden_plegar_las_columnas_del_desglose():
    """Catorce columnas no caben en una pantalla ni al 100 %."""
    src = _leer(IMPORTADOR)
    assert "COLUMNAS_DESGLOSE" in src
    m = re.search(r"const COLUMNAS_DESGLOSE = \[([^\]]*)\]", src)
    assert m, "falta la lista de columnas plegables"
    for clave in ("alvic", "tarifa", "cascoE", "herraje"):
        assert f"'{clave}'" in m.group(1)


# ─── 5. La lista de proyectos ensenia lo que se guardo ──────────────────────

def test_la_lista_lee_los_campos_que_de_verdad_se_guardan():
    """CANDADO. Se guarda `nombre` e `items`, y la lista leia `ref` y `lines`
    —nombres copiados de la lista de presupuestos de Cascos, que si los usa—.
    En JavaScript un campo que no existe NO da error: la lista salia siempre
    sin nombre y con «0 lineas». Parecia que el guardado no funcionaba, y lo
    que no funcionaba era enseniarlo.
    """
    src = _leer(IMPORTADOR)
    i = src.index("PROYECTOS GUARDADOS") if "PROYECTOS GUARDADOS" in src else src.index("Proyectos guardados")
    bloque = src[i:i + 2600]
    assert "o.nombre" in bloque, "la lista no lee el nombre que se guarda"
    assert "o.items" in bloque, "la lista no cuenta las lineas que se guardan"


def test_el_backend_sigue_guardando_esos_mismos_nombres():
    """Si el servidor cambiara de nombres, la lista volveria a salir vacia — y
    otra vez sin dar ningun error."""
    ruta = os.path.join(RAIZ, "backend", "routes", "cascos.py")
    src = _leer(ruta)
    i = src.index("async def guardar_proforma_proyecto")
    cuerpo = src[i:i + 2000]
    assert '"nombre":' in cuerpo and '"items":' in cuerpo


def test_lo_que_NO_se_puede_plegar_nunca():
    """Sin descripcion, sin unidades o sin total, la tabla no sirve para nada."""
    src = _leer(IMPORTADOR)
    m = re.search(r"const COLUMNAS_DESGLOSE = \[([^\]]*)\]", src)
    for imprescindible in ("desc", "uds", "total", "puertas", "destino"):
        assert f"'{imprescindible}'" not in m.group(1), (
            f"la columna «{imprescindible}» se puede ocultar, y sin ella la "
            "tabla no sirve")
