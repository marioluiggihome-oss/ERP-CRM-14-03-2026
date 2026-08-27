# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: lo que se copia del Estudio 3D SE PEGA de verdad en el presupuesto.

DE DÓNDE SALE
-------------
El master, 18/08: «el texto que sale en la parte de abajo que identifica
muebles por debajo del diseño, haz que eso se pueda copiar para poder pegar en
pegado masivo de presupuesto de cocina montada 3 y cocina desmontada».

El recuadro que se pinta bajo el render es para LEERLO —«Bajos: 4 → 60(1p)…»—
y el pegado masivo no entiende eso: habla la notación MV, «1 bf60 (altura 80)».
Así que la relación se genera aparte, de la MISMA lectura del dibujo.

LA PRUEBA QUE IMPORTA ES DE IDA Y VUELTA
----------------------------------------
Comprobar que el texto «tiene buena pinta» no vale para nada. Lo que se
comprueba aquí es que el texto generado, pasado por el INTÉRPRETE DE VERDAD
del presupuesto (`services/mv_relacion.parse_relacion`, el mismo que hay
detrás de /cascos/mv/detectar-relacion), devuelve TODOS los muebles y no deja
ni una línea sin leer.

Un botón de copiar que produce texto que luego no pega es peor que no tener
botón: el que lo usa cree que ha volcado la cocina y se encuentra medio
presupuesto.

LO QUE ADEMÁS SE PROTEGE, Y CUESTA DINERO
-----------------------------------------
· NO SE RELLENA UN ANCHO QUE NO ESTÁ. Un módulo sin cota sale con «?» y no se
  pega. Poner un 60 por defecto sería meter una medida inventada en un
  presupuesto — la regla de oro de la casa, aquí pagada en euros.
· LA CAJONERA SE ELIGE POR SUS FRENTES. En la tarifa, BC son CINCO cajones y
  BGC son TRES: 612,72 € contra 412,92 € en un bajo de 60. Mandar toda
  cajonera al de cinco son 200 € de más por mueble en el papel que se firma.
"""
import importlib.util
import json
import os

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _carga(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(BACKEND, ruta))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


LC = _carga("lectura_cocina", "services/luiggi_ai/lectura_cocina.py")
MVR = _carga("mv_relacion", "services/mv_relacion.py")


def _cocina(bajos=None, altos=None, altillos=None, columnas=None, ancho=330):
    return LC.parsear_lectura(json.dumps({
        "forma": "lineal", "ancho_total_cm": ancho,
        "filas": {
            "bajos": bajos or [], "altos": altos or [],
            "altillos": altillos or [], "columnas": columnas or [],
        },
        "huecos_altos": [],
    }))


def _cocina_del_master():
    """La LL: 5 bajos (fregadero, cajonera, placa y dos puertas), 5 altos con
    la campana en medio, 5 altillos y 2 columnas (una de horno y micro)."""
    return _cocina(
        bajos=[{"orden": 1, "ancho_cm": 60, "contiene": "fregadero", "frentes": ["fregadero", "puerta"]},
               {"orden": 2, "ancho_cm": 60, "frentes": ["cajon", "cajon", "cajon"]},
               {"orden": 3, "ancho_cm": 60, "contiene": "placa", "frentes": ["placa", "puerta"]},
               {"orden": 4, "ancho_cm": 60, "frentes": ["puerta"]},
               {"orden": 5, "ancho_cm": 60, "frentes": ["puerta"]}],
        altos=[{"orden": 1, "ancho_cm": 60, "frentes": ["puerta"]},
               {"orden": 2, "ancho_cm": 60, "frentes": ["puerta"]},
               {"orden": 3, "ancho_cm": 90, "contiene": "campana", "frentes": ["hueco"]},
               {"orden": 4, "ancho_cm": 60, "frentes": ["puerta"]},
               {"orden": 5, "ancho_cm": 60, "frentes": ["puerta"]}],
        altillos=[{"orden": i, "ancho_cm": 60, "frentes": ["puerta"]} for i in range(1, 6)],
        columnas=[{"orden": 1, "ancho_cm": 60, "contiene": "horno y microondas",
                   "frentes": ["microondas", "horno", "puerta"]},
                  {"orden": 2, "ancho_cm": 60, "frentes": ["puerta", "puerta"]}],
    )


# ─── 1. La prueba de ida y vuelta ──────────────────────────────────────────

def test_lo_copiado_lo_entiende_entero_el_presupuesto():
    """LA PRUEBA. Si esto se pone en rojo, el boton de copiar esta entregando
    texto que el presupuesto no sabe leer."""
    rel = LC.relacion_mv(_cocina_del_master())
    assert rel["lineas"] == 17, f"se esperaban 17 muebles y salen {rel['lineas']}"
    leido = MVR.parse_relacion(rel["texto"], "T1")
    assert not leido.get("noLeidas"), (
        f"el presupuesto NO ha sabido leer estas lineas: {leido.get('noLeidas')}. "
        f"El boton de copiar entrega texto que no se pega.")
    assert len(leido["muebles"]) == rel["lineas"], (
        f"se copiaron {rel['lineas']} muebles y el presupuesto ha leido "
        f"{len(leido['muebles'])}: por el camino se pierde alguno")
    sin_codigo = [m for m in leido["muebles"] if not m.get("encontrado")]
    assert not sin_codigo, (
        f"estos codigos no existen en la tarifa: {[m['raw'] for m in sin_codigo]}. "
        f"Entrarian en el presupuesto valiendo 0 EUR")
    sin_precio = [m for m in leido["muebles"] if not m.get("pvp")]
    assert not sin_precio, (
        f"estos muebles entran sin precio: {[m['cod'] for m in sin_precio]}. "
        f"Un mueble a 0 EUR en un presupuesto no lo ve nadie hasta que se fabrica")


def test_cada_familia_va_a_su_codigo():
    """Que se pegue no basta: tiene que pegarse EL MUEBLE QUE ES."""
    leido = MVR.parse_relacion(LC.relacion_mv(_cocina_del_master())["texto"], "T1")
    cods = [m["cod"] for m in leido["muebles"]]
    assert cods[0].startswith("BF"), f"el bajo de fregadero no va a BF: {cods[0]}"
    assert cods[1].startswith("BGC"), f"la cajonera de 3 frentes no va a BGC: {cods[1]}"
    assert any(c.startswith("ASC") for c in cods), "el alto de campana no va a ASC"
    assert "CHM60" in cods, "la columna de horno y microondas no va a CHM"
    assert any(c.startswith("L") for c in cods), "los altillos no van a la familia ALTILLO"


# ─── 2. Lo que no se sabe, no se rellena ───────────────────────────────────

def test_un_mueble_sin_ancho_no_se_inventa_un_60():
    """Regla de oro, y aqui se paga en euros: un ancho que el dibujo no traia
    NO puede entrar en un presupuesto como si fuera un dato."""
    d = _cocina(bajos=[{"orden": 1, "contiene": "fregadero", "frentes": ["fregadero"]},
                       {"orden": 2, "ancho_cm": 60, "frentes": ["puerta"]}], ancho=None)
    rel = LC.relacion_mv(d)
    assert rel["sin_ancho"] == 1, "no se esta contando el mueble sin ancho"
    assert "bf?" in rel["texto"], (
        "un mueble sin cota ha salido con un ancho concreto: se acaba de "
        "inventar una medida y va derecha al presupuesto")
    assert " bf60" not in rel["texto"], "se ha rellenado el ancho que faltaba con un 60"
    # Y el presupuesto lo rechaza, que es lo correcto: mejor que avise a que lo cuele.
    leido = MVR.parse_relacion(rel["texto"], "T1")
    assert leido.get("noLeidas"), (
        "una linea sin ancho tendria que quedarse sin leer en el presupuesto, "
        "para que se vea que falta; si se cuela, entra un mueble equivocado")


def test_la_cajonera_se_elige_por_cuantos_frentes_tiene():
    """BC son CINCO cajones y BGC son TRES: 200 EUR de diferencia en un 60."""
    d = _cocina(bajos=[{"orden": 1, "ancho_cm": 60, "frentes": ["cajon", "cajon", "cajon"]},
                       {"orden": 2, "ancho_cm": 60,
                        "frentes": ["cajon", "cajon", "cajon", "cajon", "cajon"]}])
    leido = MVR.parse_relacion(LC.relacion_mv(d)["texto"], "T1")
    cods = [m["cod"] for m in leido["muebles"]]
    assert cods == ["BGC60", "BC60"], (
        f"las cajoneras no van a su familia por numero de frentes: {cods}. "
        f"Mandar una de tres frentes a la de cinco son 200 EUR de mas")
    precios = [m["pvp"] for m in leido["muebles"]]
    assert precios[0] < precios[1], "la de tres frentes no puede costar mas que la de cinco"


def test_se_avisa_de_lo_deducido():
    """La familia de cajonera es una DEDUCCION —el dibujo enseña frentes, no
    familias—. Si no se dice, se firma sin repasarlo."""
    d = _cocina(bajos=[{"orden": 1, "ancho_cm": 60, "frentes": ["cajon", "cajon", "cajon"]}])
    assert LC.relacion_mv(d)["cajoneras"] == 1, \
        "ya no se cuentan las cajoneras deducidas, asi que la pantalla no puede avisar"


# ─── 3. Enchufado y a la vista ─────────────────────────────────────────────

def test_la_relacion_viaja_con_el_render():
    with open(os.path.join(BACKEND, "services", "luiggi_ai", "render_3d.py"), encoding="utf-8") as f:
        src = f.read()
    assert 'parsed_params["relacionMV"]' in src, \
        "la relacion para el presupuesto ya no viaja con el render"
    assert "relacion_mv(lectura)" in src, (
        "la relacion se genera de otra cosa y no de la lectura del dibujo: dos "
        "interpretaciones distintas del mismo plano acaban no coincidiendo")


def test_la_pantalla_deja_copiarla():
    ruta = os.path.join(os.path.dirname(BACKEND), "frontend", "src", "components", "AIRenderStudio.jsx")
    with open(ruta, encoding="utf-8") as f:
        src = f.read()
    codigo = "\n".join(l.split("//")[0] for l in src.splitlines())
    assert "copiarRelacionMV" in codigo, "no hay forma de copiar la relacion"
    assert "execCommand" in codigo, (
        "se ha quitado el respaldo de copiado: fuera de HTTPS y en moviles "
        "viejos `navigator.clipboard` no existe y el boton no haria nada")
    assert "relacionMVSinAncho" in codigo, \
        "la pantalla ya no avisa de los muebles sin ancho, que NO se pegan"


# ─── 4. El volcado de un clic ──────────────────────────────────────────────
#
# El master: «prueba el boton de volcar a presupuesto, haz funcionar ese
# boton». Lo que hacia era mandar la IMAGEN del render al analizador para que
# adivinara los muebles mirandola. Es decir:
#
#     dibujo -> lectura -> render -> volver a leer el render -> presupuesto
#
# DOS interpretaciones de IA en serie, y la segunda mirando una cocina que la
# primera ya se habia inventado. De ahi que el precio no cuadrara con MV ni con
# ZC. La lectura del plano YA tiene los muebles, con su codigo de tarifa.
#
# Ahora se vuelca ESO. Y no se procesa solo: llega al cuadro de pegado masivo y
# se abre, para repasarlo antes de meterlo. Esto acaba en un presupuesto que
# firma un cliente y la relacion trae cosas deducidas.


def _jsx(nombre):
    ruta = os.path.join(os.path.dirname(BACKEND), "frontend", "src", "components", nombre)
    with open(ruta, encoding="utf-8") as f:
        src = f.read()
    return "\n".join(l.split("//")[0] for l in src.splitlines())


def test_el_estudio_puede_volcar_la_relacion_de_un_clic():
    codigo = _jsx("AIRenderStudio.jsx")
    assert "volcarRelacionA" in codigo, "no hay forma de volcar la relacion al presupuesto"
    assert "'cocinaMontada3'" in codigo, "el volcado no apunta a Cocina Montada 3"
    assert "relacionMVPendiente" in codigo, \
        "la relacion no viaja al presupuestador: el boton navegara y no llevara nada"


def test_cocina_montada_3_recibe_la_relacion():
    codigo = _jsx("CocinaMontada3.jsx")
    assert "relacionMVPendiente" in codigo, (
        "Cocina Montada 3 no recoge la relacion que le manda el Estudio 3D: el "
        "boton de volcar navegaria a una pantalla vacia")
    assert "setTextoMasivo" in codigo and "setShowPegadoMasivo(true)" in codigo, \
        "la relacion llega pero no se ve: no sirve de nada"


def test_la_relacion_no_se_mete_sola_en_el_presupuesto():
    """Trae cosas DEDUCIDAS —la familia de cajonera sale de contar frentes— y
    esto acaba en un papel que firma un cliente. Se repasa antes."""
    codigo = _jsx("CocinaMontada3.jsx")
    i = codigo.index("relacionMVPendiente")
    bloque = codigo[max(0, i - 400):i + 500]
    assert "procesarPegadoMasivo()" not in bloque, (
        "la relacion se procesa sola al llegar: entraria en el presupuesto sin "
        "que nadie la haya mirado, con las familias deducidas incluidas")
