# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del emparejamiento mueble → casco: QUE SEA EL CASCO DE ESA MEDIDA.

EL FALLO, CON EL PRESUPUESTO DEL 09/08 DELANTE
----------------------------------------------
En la relación de muebles había esto:

    BF60D/I    BAJO     60 cm    alto 80
    B90        BAJO     90 cm    alto 80
    A60D/I     ALTO     60 cm    alto 90   (x2)
    A90        ALTO     90 cm    alto 90
    AE60D/I    ALTO     60 cm    alto 90
    BCG60      BAJO     60 cm    alto 80
    CHMCG60D/I COLUMNA  60 cm    alto 220
    ASF60D/I   ALTO     60 cm    alto 90
                                            9 uds · 2.354,31 €

Y el presupuesto salió con esto:

    3  Bajo Con Balda        70x30x58
    5  Alto Con Balda        70x30x33
    1  Columna Con Baldas   200x40x58
                                            9 uds · 669,64 €

Las unidades cuadran. Todo lo demás, no. TODOS los muebles salieron de 30 cm de
ancho — que no había ninguno—, los tres bajos distintos se fundieron en una
sola línea y la columna de 220 se convirtió en una de 200.

POR QUE PASO
------------
El catálogo de cascos está en MILÍMETROS (600) y la relación mandaba
CENTÍMETROS (60). El emparejamiento busca «el casco cuyo ancho se parece más»,
así que comparaba 60 contra 600, 900, 300... y ganaba siempre el más estrecho
del catálogo. No hubo ningún error: hubo un presupuesto con las medidas
cambiadas, con exactamente la misma pinta que uno bueno.

LO QUE SE PROTEGE
-----------------
1. TODO SE PASA A MILÍMETROS ANTES DE COMPARAR, y con UNA sola función. Había
   tres orígenes y cada uno tenía su idea; dos convertían y el tercero no.

2. EL ALTO CUENTA. Un bajo de 80 y uno de 70 no son el mismo mueble, y una
   columna de 220 no es una de 200. Antes solo miraba el ancho.

3. SI NO HAY CASCO DE ESA MEDIDA, SE DICE. Entra a 0 € marcado como estimado,
   con SUS medidas. Una línea que se ve sin precio se corrige; una línea con el
   casco equivocado y un precio de aspecto normal se firma.
"""
import os
import re

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(RAIZ, "frontend", "src")
MEDIDAS = os.path.join(SRC, "utils", "medidas.js")
CASCOS = os.path.join(SRC, "components", "Cascos.jsx")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


# La regla de conversión, traída a Python desde utils/medidas.js para poder
# probarla con números de verdad. Si allí cambia, aquí tiene que cambiar — y esa
# es justo la conversación que hay que tener antes de tocarla.
LIMITE_CM_MM = 320


def a_milimetros(v):
    n = float(v or 0)
    if n <= 0:
        return 0
    return round(n * 10) if n < LIMITE_CM_MM else round(n)


# ─── 1. La conversión, con los números del presupuesto ──────────────────────

def test_los_anchos_de_la_relacion_se_convierten_bien():
    """CANDADO PRINCIPAL. 60 cm son 600 mm, no 60."""
    assert a_milimetros(60) == 600
    assert a_milimetros(90) == 900
    assert a_milimetros(45) == 450


def test_lo_que_ya_viene_en_milimetros_se_queda_como_esta():
    """El analizador de planos y el diseñador 3D ya convierten. Pasar dos veces
    por aquí no puede multiplicar por diez otra vez."""
    assert a_milimetros(600) == 600
    assert a_milimetros(a_milimetros(60)) == 600


def test_las_alturas_altas_tambien(  ):
    """220 cm de columna son 2.200 mm. Está por debajo del límite, así que se
    convierte; 2.200 ya está por encima y se queda."""
    assert a_milimetros(220) == 2200
    assert a_milimetros(2200) == 2200


def test_sin_medida_no_se_inventa_un_ancho():
    """Un 0 aquí significa «no consta», no «un mueble de cero»."""
    for v in (None, "", 0, -5):
        assert a_milimetros(v) == 0


def test_la_conversion_esta_escrita_en_un_solo_sitio():
    assert os.path.exists(MEDIDAS), (
        "falta utils/medidas.js: cada pantalla volvería a tener su propia idea "
        "de en qué unidad manda las medidas, que es como empezó esto")
    m = re.search(r"LIMITE_CM_MM\s*=\s*(\d+)", _leer(MEDIDAS))
    assert m and int(m.group(1)) == LIMITE_CM_MM, (
        "el límite cm/mm ha cambiado en el código y no aquí: esta prueba estaría "
        "comprobando una regla que ya no es la que corre")


def test_ninguna_pantalla_se_hace_su_propia_conversion():
    """Eran tres copias de la misma cuenta. La que se olvidó de aplicarse es la
    que rompió el presupuesto."""
    malos = []
    for raiz, _, ficheros in os.walk(os.path.join(SRC, "components")):
        for f in ficheros:
            if not f.endswith(".jsx"):
                continue
            src = _leer(os.path.join(raiz, f))
            # La firma de la copia: el 320 del límite dentro de un ternario.
            if re.search(r"<\s*320\s*\?", src):
                malos.append(f)
    assert not malos, (
        "vuelven a llevar su propia conversión cm→mm: " + ", ".join(malos)
        + ". Usa `aMilimetros` de utils/medidas.js.")


# ─── 2. El emparejamiento mira el alto, no solo el ancho ────────────────────

def test_el_emparejamiento_convierte_antes_de_comparar():
    src = _leer(CASCOS)
    i = src.index("const famOf = (t) =>")   # el emparejador, no el comentario
    trozo = src[i:i + 4000]
    assert "aMilimetros(det.ancho)" in trozo, (
        "el ancho se compara sin convertir: 60 contra 600 no da error, da el "
        "casco más estrecho del catálogo y el presupuesto sale cambiado")
    assert "aMilimetros(det.alto)" in trozo


def test_el_alto_entra_en_la_decision():
    """Una columna de 220 no es una de 200, y un bajo de 80 no es uno de 70."""
    src = _leer(CASCOS)
    i = src.index("const distancia = (m)")
    trozo = src[i:i + 500]
    assert "altoDet" in trozo, (
        "el alto ha dejado de contar: vuelve a emparejar una columna de 220 con "
        "una de 200 sin decir nada")


# ─── 3. Si no hay casco de esa medida, se dice ──────────────────────────────

def test_un_ancho_que_no_existe_no_se_empareja_a_la_fuerza():
    src = _leer(CASCOS)
    assert "SIN_PARECIDO_MM" in src, (
        "sin un límite de parecido, SIEMPRE hay un «más cercano»: el catálogo "
        "no puede decir nunca que no tiene esa medida")
    m = re.search(r"SIN_PARECIDO_MM\s*=\s*(\d+)", src)
    assert m and 20 <= int(m.group(1)) <= 100, (
        "el límite de parecido se ha ido a un extremo: muy bajo no empareja "
        "nada, muy alto vuelve a colar cualquier casco")


def test_la_linea_sin_casco_conserva_sus_medidas():
    """Si sale a 0 € pero con las medidas del casco equivocado, no hay forma de
    saber qué se pidió de verdad."""
    src = _leer(CASCOS)
    i = src.index("estimado: true")
    linea = src[max(0, i - 700):i]
    for campo in ("ancho: anchoDet", "alto: altoDet", "fondo: fondoDet"):
        assert campo in linea, (
            f"la línea estimada no lleva {campo}: pierde la medida que se pidió")


def test_dos_muebles_distintos_no_se_funden_en_una_linea():
    """Tres bajos distintos salieron como una sola línea de 3 uds porque los
    tres apuntaban al mismo casco. La firma tiene que distinguirlos."""
    src = _leer(CASCOS)
    i = src.index("estimado: true")
    linea = src[max(0, i - 700):i]
    m = re.search(r"sig: `estimado\|\$\{norm\(det\.tipo\)\}\|([^`]*)`", linea)
    assert m and "altoDet" in m.group(1), (
        "la firma de una línea estimada no incluye el alto: un bajo de 80 y uno "
        "de 70 se sumarían en la misma línea")
