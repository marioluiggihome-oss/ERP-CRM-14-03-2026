# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: el alzado tiene que LEERSE, y no contar muebles que nadie ha pedido.

15/08/2026, el master: «no funciona bien el alzado, no lo lee bien».

Se generó su cocina y se miró el dibujo. Tres cosas, todas comprobadas sobre el
PNG de verdad:

1. EL RÓTULO SE PISABA CON LAS COTAS DE LOS CAJONES. En la cajonera de 90 cm,
   el nombre del módulo iba girado y centrado, y justo ahí van las alturas de
   cada frente (16, 32, 32): se leía «Mueble bajo» encima del «16» y no se
   entendía ninguno de los dos. Además se giraba un rótulo en un módulo de
   90 cm, donde en horizontal cabía de sobra.

2. EL RÓTULO DE LA COLUMNA CRUZABA MEDIO ALZADO. Girado y sin fondo, «Mueble
   horno» pasaba por encima de la línea de encimera y de las diagonales de las
   puertas.

3. SE CONTABA HERRAJE DE MUEBLES QUE NO EXISTEN. Cuando una pared no trae altos
   declarados, el alzado dibuja unos DERIVADOS de los bajos, en línea
   discontinua — como ayuda. Pero iban sin rótulo (una fila de cajas vacías que
   se lee como «aquí van altos») y SUMABAN AL RECUENTO DE HERRAJE. En la cocina
   del master eso eran 13 puertas donde hay 9: cuatro juegos de bisagras y
   cuatro tiradores de más en el pedido. Un pedido de más se paga.
"""
import os

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA = os.path.join(BACKEND, "routes", "estudio_cocinas.py")


def _leer():
    with open(RUTA, encoding="utf-8") as f:
        return f.read()


def _bloque(desde, hasta, margen=3000):
    src = _leer()
    i = src.index(desde)
    return src[i:src.index(hasta, i)] if hasta in src[i:i + margen] else src[i:i + margen]


# ─── 1. Nada se pisa con nada ───────────────────────────────────────────────

def test_la_cota_del_cajon_no_va_donde_va_el_nombre():
    """El nombre del módulo va centrado; si la cota del frente también, chocan."""
    src = _leer()
    i = src.index("for fh in fronts:")
    cuerpo = src[i:i + 1200]
    assert 'ha="left"' in cuerpo, (
        "la altura del frente vuelve al centro del módulo, que es donde va el "
        "nombre: se leerá «16» encima de «Mueble bajo» y no se entenderá ninguno")
    assert 'ax.text(x + w / 2, yy + fh / 2' not in cuerpo, \
        "la cota del frente ha vuelto al centro exacto del módulo"


def test_los_rotulos_llevan_fondo_para_no_leerse_sobre_las_lineas():
    """Girado, el texto cruza la encimera y las diagonales de las puertas."""
    for funcion in ("def _texto_vertical", "def _texto_modulo"):
        cuerpo = _bloque(funcion, "\n        def ")
        assert "bbox=dict(facecolor=C_BG" in cuerpo, (
            f"`{funcion.split()[1]}` ha perdido el fondo opaco: el rótulo se "
            f"leerá encima de las líneas del dibujo")


def test_una_cajonera_ancha_se_rotula_en_horizontal():
    """Girar el nombre en un módulo de 90 cm no lo hace más legible."""
    src = _leer()
    i = src.index("elif tipo in DRAWERS:")
    cuerpo = src[i:i + 1600]
    assert "_texto_modulo(" in cuerpo, (
        "la cajonera vuelve a rotularse siempre girada, incluso a 90 cm de "
        "ancho, donde en horizontal cabe de sobra")


def test_el_nombre_se_parte_por_palabras_antes_de_cortarse():
    """El plano salía lleno de «Bajo frega…», «Lavavaji…». Media palabra no le
    sirve a quien fabrica, y a lo alto del módulo sobra sitio."""
    cuerpo = _bloque("def _texto_modulo", "\n        def ")
    assert "parte.split(\" \")" in cuerpo, (
        "el rótulo vuelve a recortarse a lo bruto en vez de partirse por "
        "palabras")


# ─── 2. El herraje que se pide es el de los muebles que existen ─────────────

def test_los_altos_propuestos_no_se_cuentan_como_herraje():
    """CANDADO DE DINERO. Con este papel se piden bisagras y tiradores."""
    src = _leer()
    i = src.index("for (bx, bw) in (bajos_xy if not altos_xy else []):")
    cuerpo = src[i:i + 1800]
    assert "propuestos += 1" in cuerpo, \
        "los altos propuestos vuelven a contarse como muebles reales"
    assert 'herr["puertas"] += 1' not in cuerpo, (
        "un alto PROPUESTO vuelve a sumar al recuento de herraje: se pedirán "
        "bisagras y tiradores de muebles que no existen")


def test_un_alto_propuesto_dice_que_lo_es():
    """Sin rótulo son una fila de cajas vacías que se leen como muebles."""
    src = _leer()
    i = src.index("for (bx, bw) in (bajos_xy if not altos_xy else []):")
    cuerpo = src[i:i + 1800]
    assert "propuesto" in cuerpo.lower(), \
        "los altos derivados vuelven a dibujarse sin decir que son una propuesta"


def test_el_resumen_avisa_de_los_propuestos():
    """Se dibujan, no se cuentan… y se dice. Callarlo sería esconderlos."""
    src = _leer()
    i = src.index("HERRAJE (aprox.)")
    cuerpo = src[i:i + 900]
    assert "PROPUESTO" in cuerpo, (
        "el resumen ya no avisa de los altos propuestos: se dibujarían sin que "
        "nadie los confirme ni los quite")
