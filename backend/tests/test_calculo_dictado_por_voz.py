# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del dictado: QUE SALGA LO QUE SE DICE, NO TRES VECES.

EL FALLO, CON LO QUE SALIO EN LA TABLET
---------------------------------------
Dictando «el bajo fregadero» en el cuadro de Estudio 3D salia:

    «elelelel bajoel bajoel bajoel bajo fre»

No es que el micro oyera mal. Es que el navegador va mandando la frase A MEDIAS
mientras piensa —«el», «el bajo», «el bajo fre»— y el codigo las sumaba TODAS,
una detras de otra. Cada version intermedia quedaba pegada a la anterior.

Esto ya se habia arreglado una vez, y solo a medias: entonces se quito el
`+=` sobre los resultados FINALES (que en Android se reentregan), pero se
siguio sumando los PROVISIONALES, que es peor porque son muchos mas.

LA REGLA, LA DE VERDAD
----------------------
· LOS FINALES SE SUMAN, rehaciendolos enteros en cada evento. Asi da igual
  cuantas veces reentregue el navegador lo mismo: el resultado es el mismo.
· DEL PROVISIONAL SOLO VALE EL ULTIMO, Y NO SE SUMA NUNCA. Se ensenia detras
  para que se vea que el micro esta oyendo, y en cuanto llega el final lo
  sustituye.

Aqui se prueba esa regla con la MISMA secuencia que produjo el churro.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOOK = os.path.join(RAIZ, "frontend", "src", "hooks", "useSpeechRecognition.js")


def _leer():
    with open(HOOK, encoding="utf-8") as f:
        return f.read()


# La regla de `leerResultados`, traida a Python para poder probarla con la
# secuencia real. Si alli cambia, aqui tiene que cambiar — y esa es exactamente
# la conversacion que hay que tener antes de tocar el dictado otra vez.
def _unir(a, b):
    x, y = (a or "").strip(), (b or "").strip()
    if not x:
        return y
    if not y:
        return x
    return f"{x} {y}"


def leer_resultados(resultados):
    firme, provisional = "", ""
    for r in resultados:
        texto, es_final = r
        if es_final:
            firme = _unir(firme, texto)
        else:
            provisional = texto   # asignacion, NUNCA suma
    return firme, provisional


# ─── 1. La secuencia que rompio el dictado ──────────────────────────────────

def test_los_provisionales_no_se_amontonan():
    """CANDADO PRINCIPAL. Esta es la secuencia que da «elelelel bajoel bajo…»."""
    eventos = [
        [("el", False)],
        [("el", False)],
        [("el bajo", False)],
        [("el bajo fre", False)],
        [("el bajo fregadero", True)],
    ]
    salida = [_unir(*leer_resultados(e)) for e in eventos]
    assert salida[-1] == "el bajo fregadero"
    for texto in salida:
        assert "elel" not in texto.replace(" ", ""), (
            f"vuelve a amontonar los provisionales: «{texto}»")


def test_un_final_reentregado_no_se_duplica():
    """En Android el mismo resultado final llega varias veces. Rehacerlo entero
    en cada evento lo hace inofensivo."""
    uno = [("el bajo fregadero", True)]
    assert _unir(*leer_resultados(uno)) == "el bajo fregadero"
    assert _unir(*leer_resultados(uno)) == "el bajo fregadero"   # idempotente


def test_lo_firme_de_varias_frases_se_encadena():
    resultados = [("el bajo fregadero", True), ("de sesenta", True)]
    firme, _ = leer_resultados(resultados)
    assert firme == "el bajo fregadero de sesenta"


def test_el_provisional_se_ve_pero_detras_de_lo_firme():
    """Se ensenia para saber que el micro oye; si no, parece colgado."""
    firme, prov = leer_resultados([("el bajo", True), ("fregade", False)])
    assert firme == "el bajo" and prov == "fregade"
    assert _unir(firme, prov) == "el bajo fregade"


def test_el_provisional_no_se_queda_cuando_llega_el_final():
    firme, prov = leer_resultados([("el bajo", True), ("fregadero", True)])
    assert prov == "" and firme == "el bajo fregadero"


def test_sin_nada_dicho_no_revienta():
    assert leer_resultados([]) == ("", "")


# ─── 2. Que el codigo siga siendo el que se ha probado ──────────────────────

def test_el_codigo_separa_finales_de_provisionales():
    src = _leer()
    i = src.index("export function leerResultados")
    cuerpo = src[i:src.index("export default", i)]
    assert "isFinal" in cuerpo, (
        "`leerResultados` ya no distingue lo final de lo provisional: vuelve a "
        "sumar las frases a medias y sale el churro de antes")
    assert re.search(r"provisional\s*=\s*texto", cuerpo), (
        "el provisional se ha vuelto a acumular: tiene que ser una ASIGNACION, "
        "solo vale el ultimo")
    assert not re.search(r"provisional\s*\+=", cuerpo), (
        "`provisional +=` es exactamente el fallo: cada version intermedia "
        "pegada detras de la anterior")


def test_el_dictado_no_se_para_solo_a_media_frase():
    """Android corta la sesion cada pocos segundos. Si no se vuelve a abrir, hay
    que tocar el micro otra vez en mitad de la frase."""
    src = _leer()
    assert "quiereEscuchar" in src, (
        "sin la intencion del usuario guardada, el corte automatico de Android "
        "deja el micro parado a media frase")
    i = src.index("recognition.onend")
    cuerpo = src[i:i + 700]
    assert "quiereEscuchar.current" in cuerpo and "recognition.start()" in cuerpo


def test_parar_de_verdad_para():
    """Si `stop()` fuera antes de quitar la intencion, el `onend` de despues
    volveria a arrancarlo: el micro no se apagaria nunca."""
    src = _leer()
    i = src.index("const stopListening")
    cuerpo = src[i:i + 500]
    pos_intencion = cuerpo.index("quiereEscuchar.current = false")
    pos_stop = cuerpo.index(".stop()")
    assert pos_intencion < pos_stop, (
        "se para el micro antes de quitar la intencion de escuchar: el `onend` "
        "lo volveria a arrancar y no habria forma de apagarlo")


def test_no_se_insiste_contra_un_permiso_denegado():
    """Reintentar en bucle no concede el permiso; solo gasta bateria."""
    src = _leer()
    i = src.index("recognition.onerror")
    cuerpo = src[i:i + 500]
    assert "not-allowed" in cuerpo and "quiereEscuchar.current = false" in cuerpo


def test_el_hook_sigue_siendo_el_unico_sitio_con_dictado():
    """Estaba copiado en dos pantallas y las dos arrastraban el mismo fallo."""
    comp = os.path.join(RAIZ, "frontend", "src", "components")
    malos = []
    for raiz, _, ficheros in os.walk(comp):
        for f in ficheros:
            if not f.endswith(".jsx"):
                continue
            with open(os.path.join(raiz, f), encoding="utf-8") as fh:
                src = fh.read()
            if "webkitSpeechRecognition" in src and "useSpeechRecognition" not in src:
                malos.append(f)
    assert not malos, (
        "vuelven a montarse su propio dictado: " + ", ".join(malos)
        + ". El fallo se arregla en el hook o no se arregla.")
