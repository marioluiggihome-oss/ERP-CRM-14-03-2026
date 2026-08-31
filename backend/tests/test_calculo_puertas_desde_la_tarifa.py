# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LAS PUERTAS Y LAS VITRINAS SE COBRAN POR LA TARIFA, NO POR UNA COPIA A MANO.

El master, 25/08/2026, mandó revisar la librería MV: «costados y puertas sobre
todo, para ver cómo lo optimizas, porque yo creo que está mal regulado».

Lo que había en la pantalla:

  · Una matriz de puertas ESCRITA A MANO que solo cubría T1..T5, con un
    `|| PUERTAS_MATRIZ_MV.T1` detrás: **16 tarifas de 21 cobraban precios de T1
    sin decir nada**.
  · En T1, las cuatro filas de abajo (70, 90, 127, 147) coincidían con la tarifa
    en las 26 casillas. Las cuatro de arriba (14, 28, 40, 56) no coincidía
    ninguna, y siempre por encima: una puerta de 14xP60 son 4 puntos en la
    tarifa y se cobraban 10.
  · Las VITRINAS se calculaban como «puerta x 1,3». Un recargo inventado: en T1
    salía el 35% de lo que dice la tarifa (una vitrina de 70x30 son 40 puntos y
    se cobraban 14), en T11 el 79%, y en T21 grande se pasaba al 113%. La tabla
    de VITRINA estaba en el catálogo todo el tiempo, sin usar.
  · Tres redes de seguridad que tapaban los huecos con números: una altura que
    faltaba cobraba como la de 70, y un ancho que faltaba cobraba 16 puntos
    sacados de la nada.

Ahora las dos matrices se GENERAN de la tarifa
(`herramientas/generar_matriz_puertas.py`). Esta prueba las regenera y las
compara con lo que hay en el JSX: si alguien vuelve a editarlas a mano, rojo.
"""
import json
import os
import re
import subprocess
import sys

from jsx_limpio import sin_comentarios as _limpia_jsx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSX = os.path.join(RAIZ, "frontend", "src", "components", "RentabilidadMV.jsx")
TARIFA = os.path.join(RAIZ, "backend", "data", "mv_tarifas_oficiales.json")
GEN = os.path.join(RAIZ, "herramientas", "generar_matriz_puertas.py")


def _jsx():
    with open(JSX, "r", encoding="utf-8") as f:
        return f.read()


def _tarifas():
    with open(TARIFA, "r", encoding="utf-8") as f:
        return json.load(f)["tariffs"]


def _bloque(cuerpo, constante):
    i = cuerpo.index(f"export const {constante} = {{")
    return cuerpo[i:cuerpo.index("\n};", i) + 3]


def test_las_matrices_del_jsx_son_EXACTAMENTE_las_de_la_tarifa():
    """El candado principal: se regenera y se compara carácter a carácter."""
    salida = subprocess.run([sys.executable, GEN], capture_output=True,
                            text=True, timeout=60)
    assert salida.returncode == 0, f"el generador falla: {salida.stderr}"
    cuerpo = _jsx()
    for constante in ("PUERTAS_MATRIZ_MV", "VITRINA_MATRIZ_MV"):
        # el stdout del generador lleva los dos bloques seguidos
        esperado = _bloque(salida.stdout, constante)
        assert _bloque(cuerpo, constante) == esperado, (
            f"{constante} del JSX ya no coincide con la tarifa. Se ha editado a "
            "mano, o se cambió la tarifa sin regenerar: "
            "`python3 herramientas/generar_matriz_puertas.py --escribir`")


def test_estan_LAS_21_TARIFAS_y_no_solo_cinco():
    """El fallo que hacía que 16 tarifas cobraran precios de T1."""
    cuerpo = _jsx()
    for constante in ("PUERTAS_MATRIZ_MV", "VITRINA_MATRIZ_MV"):
        bloque = _bloque(cuerpo, constante)
        hay = set(re.findall(r"^  (T\d+):", bloque, re.M))
        faltan = {t for t in _tarifas() if re.match(r"^T\d+$", t)} - hay
        assert not faltan, (
            f"{constante} no tiene {sorted(faltan)}: esas tarifas volverían a "
            "cobrarse con los precios de otra")


def _sin_comentarios(cuerpo):
    """El JSX sin comentarios.

    Hace falta porque el propio código explica en un comentario cuáles eran los
    apaños viejos, con su texto literal. Sin esto, la prueba de abajo se caza a
    sí misma: el apaño ya no existe, pero la explicación de que no existe sí.
    """
    return _limpia_jsx(cuerpo)


def test_NO_QUEDA_NINGUN_APAÑO_que_tape_un_hueco_con_un_numero():
    """Las tres redes de seguridad que cobraban de más o de menos en silencio.

    Un presupuesto con una casilla vacía se arregla mirándola. Uno con un número
    inventado no se arregla nunca, porque nadie sabe que está mal.
    """
    cuerpo = _sin_comentarios(_jsx())
    prohibido = (
        ("|| PUERTAS_MATRIZ_MV.T1", "16 tarifas cobrando precios de T1"),
        ("tMat['70']", "una altura que falta cobrando como la de 70"),
        ("|| 16)", "un ancho que falta cobrando 16 puntos inventados"),
        ("* 1.3", "la vitrina calculada como puerta x1,3 en vez de por su tabla"),
    )
    for trozo, porque in prohibido:
        assert trozo not in cuerpo, f"ha vuelto el apaño: {porque}"


def test_UN_HUECO_DE_TARIFA_NO_SE_SUMA_COMO_CERO():
    """`null` no puede colarse en el total: sumarlo da 0 y el frente sale gratis
    sin que nadie lo note. Se cuenta aparte para poder decirlo en pantalla."""
    cuerpo = _jsx()
    i = cuerpo.index("let sinTarifa = 0;")
    trozo = cuerpo[i:i + 900]
    assert "if (pts == null)" in trozo, (
        "ya no se comprueba el hueco de tarifa antes de sumar")
    assert "sinTarifa += 1" in trozo, "los frentes sin tarifa no se cuentan"
    assert "sinTarifa }" in cuerpo, (
        "el recuento de frentes sin tarifa no sale del cálculo, así que la "
        "pantalla no puede avisar")


def test_el_ancho_se_redondea_HACIA_ARRIBA():
    """Una puerta de 55 se corta de un tablero de 60, no de uno de 50.

    Antes se cogía el ancho MÁS CERCANO y en los empates ganaba el pequeño (55
    está a 5 de 50 y a 5 de 60), o sea que se cobraba una puerta más estrecha de
    la que hay que fabricar.
    """
    cuerpo = _jsx()
    i = cuerpo.index("const anchosDisp")
    trozo = cuerpo[i:i + 700]
    assert "w >= anchoCm" in trozo, (
        "el ancho ya no se redondea hacia arriba: se cobraría una puerta más "
        "estrecha de la que hay que fabricar")
    assert "Math.abs" not in trozo, "ha vuelto el «ancho más cercano»"


def test_la_vitrina_usa_SU_tabla_y_no_la_de_puertas():
    cuerpo = _jsx()
    assert "getPuntosVitrinaMV" in cuerpo, "no hay tarifa propia de vitrinas"
    i = cuerpo.index("const esVitrina")
    trozo = cuerpo[i:i + 400]
    assert "getPuntosVitrinaMV(fr.h, fr.w, tariff)" in trozo, (
        "el frente de vitrina no se tarifa por la tabla de VITRINA")


def test_una_vitrina_NO_sale_por_el_precio_de_una_puerta():
    """La comprobación con números, no con texto: en T1 una vitrina de 70x30 son
    40 puntos y la puerta equivalente 11. Si alguien volviera al x1,3 saldrían
    14, o sea el 35% de lo que toca."""
    t = _tarifas()["T1"]
    puerta = t["PUERTAS"]["rows"]["70"]["P30"]
    vitrina = t["VITRINA"]["rows"]["70"]["PV30"]
    assert puerta == 11 and vitrina == 40
    assert round(puerta * 1.3) < vitrina / 2, (
        "el viejo x1,3 ya no se queda muy por debajo de la tarifa de vitrina; "
        "revisar si la tarifa ha cambiado")


def test_LA_PUERTA_DE_T11_QUEDA_COMO_LA_MANDO_CAMBIAR_EL_MASTER():
    """La única casilla en la que el fichero NO dice lo que dice la hoja.

    La hoja de MV pone, en T11 alto 90, P45=65 y P50=59 — una puerta más ancha
    y más barata. Comprobado a 900 dpi sobre el escaneo: pone 59, no 69, así que
    la rareza es del impreso y no de la transcripción. El master mandó
    invertirlas: «invierte el precio, cámbialo y ya está» (25/08).

    Se invirtieron y no se inventó un tercer número. Lo que cuadraría del todo
    sería P50=69, pero ese valor no aparece impreso en ninguna parte y una
    tarifa no se completa a ojo.

    Esta prueba existe para que el cambio no se pierda: si alguien vuelve a
    volcar la tarifa desde el escaneo, se llevará la inversión por delante y
    volverán los 65/59 sin que nadie se entere.
    """
    fila = _tarifas()["T11"]["PUERTAS"]["rows"]["90"]
    assert fila["P45"] == 59 and fila["P50"] == 65, (
        f"T11/PUERTAS alto 90 está en P45={fila.get('P45')} y "
        f"P50={fila.get('P50')}. El master mandó invertirlas (59 y 65).")


def test_EL_CAMBIO_DEL_MASTER_ESTA_ESCRITO_EN_LOS_PROPIOS_DATOS():
    """Apartarse de la hoja del proveedor no puede quedar solo en un commit.

    Quien abra el JSON dentro de dos años tiene que poder ver que esa casilla no
    es un dato de MV sino una decisión de la casa, y por qué. Si no, la próxima
    auditoría la dará por buena como si viniera del proveedor.
    """
    with open(TARIFA, "r", encoding="utf-8") as f:
        meta = json.load(f).get("_meta", {})
    cambios = meta.get("cambios_del_master") or []
    assert cambios, (
        "no queda constancia en el JSON de que nos hemos apartado de la hoja")
    uno = [c for c in cambios if "T11" in c.get("donde", "")]
    assert uno, "falta la anotación del cambio de T11/PUERTAS"
    assert uno[0].get("hoja_impresa", {}).get("P45") == 65, (
        "la anotación no dice qué ponía la hoja ANTES; sin eso no se puede "
        "volver atrás ni discutirlo con el proveedor")
    assert uno[0].get("efecto_que_queda"), (
        "la anotación no dice qué queda sin cuadrar después del cambio")
