# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LA ALTURA DE UN MUEBLE MV LA ELIGE EL MASTER, NO EL CÓDIGO.

Y no es cosmética: MANDA EN EL PRECIO. Medido con la tarifa de verdad, un alto
de 60 cm vale **156,51 € a 70 y 169,83 € a 90**. Trece euros por mueble, en una
cocina con ocho altos, por un número que nadie eligió.

QUÉ PASABA (auditoría del 25/08/2026). La pantalla NO mandaba `alto_altos` ni
`alto_columnas` —cero apariciones en todo el `AIRenderStudio.jsx`— y el backend
cogía 70 y 200 por defecto. O sea que TODA relación MV salía tarifada a 70/200
aunque la cocina llevara altos de 90 y columnas de 220: sin aviso, sin error, un
número plausible y a correr. Es el mismo fallo que las cotas inventadas, pero
aterrizando en el dinero.

QUÉ SE HIZO. El master fijó las propuestas: «por defecto altos de 90, bajos de
80 y columnas de 220». Y se pueden cambiar en dos sitios: antes de sacar la
relación, y —lo que de verdad hacía falta— **en el presupuesto ya hecho, antes
de pasar a pedido**, porque es mirando el total cuando uno cae en la altura.

Los BAJOS no se eligen: en esta fábrica solo se fabrican a 80 (CLAUDE.md). No
es una preferencia, es que no hay otra.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services.distribucion_a_mv import (  # noqa: E402
    ALTO_ALTOS, ALTO_BAJOS, ALTO_COLUMNAS,
    distribucion_a_relacion, notacion_de, reaplica_alturas,
)
from services.mv_relacion import parse_relacion_text  # noqa: E402


def _cocina(fila="alto", eid="alto", ancho=60):
    return {"paredes": [{"nombre": "P1", "ancho": 300, "alto": 240, "ancho_escrito": True}],
            "elementos": [{"id": eid, "label": "M", "fila": fila, "ancho": ancho,
                           "pared_idx": 0, "posicion_cm": 0, "medida_escrita": True}]}


def _pvp(lineas, tarifa="T1"):
    t = parse_relacion_text(notacion_de(lineas), tarifa)
    return t[0]["pvp"]


def test_las_alturas_propuestas_son_las_que_dijo_el_master():
    assert ALTO_ALTOS == 90, (
        f"la altura propuesta de los altos ha cambiado a {ALTO_ALTOS}. El master, "
        "25/08: «por defecto altos de 90, bajos de 80 y columnas de 220».")
    assert ALTO_COLUMNAS == 220, (
        f"la altura propuesta de las columnas ha cambiado a {ALTO_COLUMNAS}")
    assert ALTO_BAJOS == 80, (
        "los bajos ya no son de 80. En esta fábrica SOLO se fabrican a 80 "
        "(CLAUDE.md); esto no es una preferencia que se pueda cambiar.")


def test_la_altura_cambia_el_precio_de_verdad():
    """Si esto dejara de ser cierto, todo lo demás daría igual."""
    a70 = _pvp(distribucion_a_relacion(_cocina(), tarifa="T1", alto_altos=70)["lineas"])
    a90 = _pvp(distribucion_a_relacion(_cocina(), tarifa="T1", alto_altos=90)["lineas"])
    assert a70 and a90, "no se ha podido tarifar el alto de 60"
    assert a70 != a90, (
        f"un alto de 60 cuesta lo mismo a 70 que a 90 ({a70} €). O ha cambiado la "
        "tarifa, o la altura ha dejado de llegar al tarificador — y entonces el "
        "desplegable de alturas es de adorno.")
    assert a90 > a70, "un alto de 90 debería costar más que uno de 70"


def test_por_defecto_se_tarifa_a_90_no_a_70():
    """El fallo concreto: antes salía todo a 70 sin pedirlo nadie."""
    porDefecto = _pvp(distribucion_a_relacion(_cocina(), tarifa="T1")["lineas"])
    a90 = _pvp(distribucion_a_relacion(_cocina(), tarifa="T1", alto_altos=90)["lineas"])
    assert porDefecto == a90, (
        f"sin pedir altura se está tarifando a algo que no son 90 ({porDefecto} € "
        f"frente a {a90} €)")


def test_los_bajos_van_a_80_pidas_lo_que_pidas():
    r = distribucion_a_relacion(_cocina(fila="bajo", eid="bajo"), tarifa="T1",
                                alto_altos=70, alto_columnas=200)
    assert r["lineas"], "no se ha traducido el bajo a ningún mueble MV"
    assert r["lineas"][0]["alto"] == 80, (
        f"un bajo ha salido a {r['lineas'][0]['alto']} cm. Los bajos de esta "
        "fábrica son de 80 y no dependen de ningún desplegable.")


def test_cambiar_la_altura_en_el_presupuesto_vuelve_a_tarifar():
    """Lo que hace el desplegable de la relación ya hecha.

    Cada línea lleva su altura DENTRO (`notacion_de` la escribe mueble a
    mueble), así que sin reaplicarla el desplegable no cambiaría ni un céntimo.
    """
    r = distribucion_a_relacion(_cocina(), tarifa="T1", alto_altos=70)
    antes = _pvp(r["lineas"])
    despues = _pvp(reaplica_alturas(r["lineas"], alto_altos=90))
    assert despues != antes, (
        f"cambiar la altura en el presupuesto no ha cambiado el precio ({antes} €). "
        "Las líneas se habrán vuelto a tarifar con la altura vieja.")


def test_cambiar_la_altura_NO_pierde_la_mano_elegida():
    """La otra mitad, y la que costaría dinero de verdad.

    La mano D/I la decide el master a mano. Si al tocar la altura se perdiera,
    el código saldría al taller sin mano decidida y «acierta la mitad de las
    veces; la otra mitad es un frente desmontado y taladrado otra vez en casa
    del cliente».
    """
    r = distribucion_a_relacion(_cocina(), tarifa="T1", alto_altos=70)
    r["lineas"][0]["mano"] = "I"
    r["lineas"][0]["mano_propuesta"] = False
    nuevas = reaplica_alturas(r["lineas"], alto_altos=90)
    assert nuevas[0]["mano"] == "I", "se ha perdido la mano al cambiar la altura"
    assert nuevas[0]["mano_propuesta"] is False, (
        "una mano YA DECIDIDA ha vuelto a marcarse como propuesta")
    assert nuevas[0]["alto"] == 90, "no se ha aplicado la altura nueva"


def test_reaplicar_alturas_no_toca_lo_que_no_es_altura():
    r = distribucion_a_relacion(_cocina(), tarifa="T1", alto_altos=70)
    original = dict(r["lineas"][0])
    nueva = reaplica_alturas(r["lineas"], alto_altos=90)[0]
    for clave in ("codigo", "ancho", "familia", "label", "id", "pared_idx"):
        assert nueva.get(clave) == original.get(clave), (
            f"reaplicar la altura ha cambiado «{clave}», que no es asunto suyo")


def test_la_pantalla_manda_las_alturas():
    """Sin esto, todo lo de arriba funciona y no sirve de nada."""
    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ruta = os.path.join(raiz, "frontend", "src", "components", "AIRenderStudio.jsx")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    assert "alto_altos: altoAltos" in cuerpo, (
        "la pantalla ha vuelto a pedir la relación MV sin mandar la altura de los "
        "altos, así que el servidor la elige en silencio otra vez")
    assert "alto_columnas: altoColumnas" in cuerpo, (
        "la pantalla no manda la altura de las columnas")
    assert "cambiarAlturas" in cuerpo, (
        "ya no se pueden cambiar las alturas con la relación hecha, que es donde "
        "el master pidió poder cambiarlas: «en el presupuesto antes de pasar a pedido»")
