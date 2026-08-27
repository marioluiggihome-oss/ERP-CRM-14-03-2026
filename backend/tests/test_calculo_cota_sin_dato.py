# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
UN MÓDULO DEL QUE NADIE SABE EL ANCHO SE ROTULA «?», NO «~60».

`cota_de_ancho` distingue tres casos desde el 23/08/2026, y los distingue bien:

    medida escrita  -> «60»    la puso el cliente en su croquis
    ancho derivado  -> «~60»   lo cuadró el validador contra la pared
    sin ancho       -> «?»     no lo sabe nadie

El tercero es la regla 7 de CLAUDE.md hecha código. Su comentario lo explica:
escribir «~60» de un módulo que nadie ha medido es inventarse una cota CON
COARTADA, porque la virgulilla le da credibilidad a un número que no es más que
el valor de respaldo del código.

LO QUE SE ENCONTRÓ AUDITANDO (25/08/2026): ese tercer caso NO SE PODÍA DAR por
el camino principal. Dos sitios rellenaban el hueco antes de que a nadie le
diera tiempo a preguntar:

  · `/detect-distribucion` hacía `float(e.get("ancho") or 60)`, así que el
    módulo llegaba al validador con un 60 ya puesto.
  · `validar_distribucion` ajustaba ese hueco a 15 cm con un aviso de «ancho
    0 cm no es fabricable», que además despista: no es que la medida sea mala,
    es que no hay medida.

Resultado: por «Detectar distribución» —el botón que usa el master— se imprimía
«~60» o «~15» en planos de taller. Estas pruebas EJECUTAN el camino entero.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import kitchen_geometry as kg  # noqa: E402


def _pared(elementos, ancho=300):
    return {"paredes": [{"nombre": "P1", "ancho": ancho, "alto": 240, "ancho_escrito": True}],
            "elementos": elementos}


def test_los_tres_casos_de_cota_siguen_siendo_tres():
    assert kg.cota_de_ancho({"ancho": 60, "medida_escrita": True}) == (60, "60", "escrita")
    assert kg.cota_de_ancho({"ancho": 60}) == (60, "~60", "estimada")
    assert kg.cota_de_ancho({"label": "sin nada"}) == (60, "?", "sin_dato")


def test_un_modulo_sin_ancho_sale_del_validador_rotulado_con_interrogante():
    """El caso que no se podía dar. Es el corazón del arreglo."""
    v = kg.validar_distribucion(_pared([{"id": "mueble", "label": "sin ancho",
                                         "pared_idx": 0, "posicion_cm": 0}]))
    mueble = [e for e in v["elementos"] if e["id"] == "mueble"][0]
    _, cota, origen = kg.cota_de_ancho(mueble)
    assert origen == "sin_dato", (
        f"un módulo sin ancho ha salido del validador como «{origen}» con la cota "
        f"«{cota}». Eso es un número que no ha medido nadie impreso en un plano "
        "que va a taller (CLAUDE.md, regla 7).")
    assert cota == "?"


def test_el_modulo_sin_ancho_SE_DIBUJA_igual():
    """No rotularlo no puede significar dejar un agujero en el alzado."""
    v = kg.validar_distribucion(_pared([{"id": "mueble", "pared_idx": 0, "posicion_cm": 0}]))
    mueble = [e for e in v["elementos"] if e["id"] == "mueble"][0]
    assert mueble.get("ancho", 0) > 0, (
        "el módulo se ha quedado sin ancho de dibujo: el alzado saldría con un "
        "hueco y tampoco serviría")


def test_se_avisa_de_que_falta_la_medida_y_se_dice_por_que():
    v = kg.validar_distribucion(_pared([{"id": "mueble", "pared_idx": 0, "posicion_cm": 0}]))
    texto = " ".join(v["avisos"])
    assert "nadie ha dado su ancho" in texto, (
        f"no se avisa de que falta la medida. Avisos: {v['avisos']}")
    assert "0 cm no es fabricable" not in texto, (
        "vuelve el aviso que despista: no es que el ancho sea malo, es que no hay "
        "ancho")


def test_la_bandera_sobrevive_al_recuadre_de_la_pared():
    """Donde de verdad se podía perder.

    El validador reparte el ancho sobrante entre los módulos y los recoloca. Si
    en ese viaje se perdiera `ancho_desconocido`, la cota volvería a salir con
    un número y no nos enteraríamos: el módulo saldría dibujado y con su «~».
    """
    v = kg.validar_distribucion(_pared([
        {"id": "mueble", "pared_idx": 0, "posicion_cm": 0},
        {"id": "bajo_fregadero", "ancho": 90, "pared_idx": 0, "posicion_cm": 60,
         "medida_escrita": True},
    ]))
    mueble = [e for e in v["elementos"] if e["id"] == "mueble"][0]
    assert mueble.get("ancho_desconocido") is True, (
        "`ancho_desconocido` se ha perdido al cuadrar la pared")
    assert kg.cota_de_ancho(mueble)[1] == "?"
    # Y el de al lado, que SÍ tenía medida escrita, la conserva tal cual.
    freg = [e for e in v["elementos"] if e["id"] == "bajo_fregadero"][0]
    assert kg.cota_de_ancho(freg) == (90, "90", "escrita")


def test_la_ruta_de_detectar_ya_no_rellena_el_hueco_con_60():
    """El `or 60` que puenteaba todo lo de arriba."""
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "routes", "estudio_cocinas.py")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    trozo = cuerpo[cuerpo.index('@router.post("/detect-distribucion")'):]
    trozo = trozo[:trozo.index('@router.post("/validar-distribucion")')]
    assert 'e.get("ancho") or 60' not in trozo, (
        "ha vuelto el `or 60` en /detect-distribucion. Con él, el módulo llega al "
        "validador con un ancho ya puesto y la cota «?» no puede darse NUNCA por "
        "el camino que usa el botón «Detectar distribución».")
