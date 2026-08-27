# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LO QUE TIENES A TIRO: EL MOTOR DEL PLAN DE ESTIMULACIÓN.

El master, 25/08/2026: «queremos un plan de estimulación continua, que cuando
accedan a su área puedan estar viendo lo que tienen que producir y los
beneficios que van a tener cuando lo produzcan».

No basta con enseñar lo ganado. Hay que enseñar lo que está a un paso: «a este
pedido le faltan 600 € para pasar de 50 a 60 € por mueble, y con sus 14 muebles
son 140 € más para ti».

EL FALLO QUE TUVO ESTO AL NACER, y que enseña cómo está hecha la tabla. Los
tramos son pares `(hasta, euros)`: «hasta ese importe se cobra eso». La primera
versión buscaba el `tope` del tramo SIGUIENTE, y por eso decía que a un pedido de
11.400 € le faltaban 3.600 € cuando le faltaban 600: se saltaba un escalón
entero. Un plan de estimulación que enseña la meta seis veces más lejos de lo
que está desanima, que es lo contrario de para lo que se hizo.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import comisiones as C  # noqa: E402

falta = C.cuanto_falta_para_el_siguiente_tramo


@pytest.mark.parametrize("valoracion,faltan,hasta,nuevo", [
    (0,        2500.0,  2500.0,  30.0),
    (2400,      100.0,  2500.0,  30.0),
    (5900,      100.0,  6000.0,  40.0),
    (8000,     1000.0,  9000.0,  50.0),
    (11400,     600.0, 12000.0,  60.0),
    (11999.99,    0.01, 12000.0, 60.0),
    (14999,       1.0, 15000.0,  70.0),
])
def test_el_salto_es_AL_ESCALON_DE_AL_LADO_y_no_a_dos(valoracion, faltan, hasta, nuevo):
    g = falta(valoracion, 10)
    assert g, f"con {valoracion} € debería haber un tramo por delante"
    assert g["faltan"] == pytest.approx(faltan), (
        f"con {valoracion} € dice que faltan {g['faltan']} y faltan {faltan}. "
        "Se está saltando un escalón: la tabla es (hasta, euros), así que el "
        "umbral es el `hasta` del tramo ACTUAL, no el del siguiente.")
    assert g["hasta"] == hasta
    assert g["porMuebleSiSalta"] == nuevo


def test_EN_EL_TRAMO_MAS_ALTO_no_se_persigue_nada():
    """Enseñar un objetivo inalcanzable desmotiva en vez de estimular."""
    assert falta(15000, 10) is None
    assert falta(50000, 10) is None


def test_lo_que_se_gana_MULTIPLICA_POR_LOS_MUEBLES():
    """Regla 4 de CLAUDE.md: las unidades multiplican. Y es lo que convierte el
    dato en un motivo: «10 € más por mueble» no mueve a nadie; «140 € más», sí."""
    g = falta(11400, 14)
    assert g["extraPorMueble"] == 10.0
    assert g["extraTotal"] == 140.0
    assert falta(11400, 0)["extraTotal"] == 0.0


def test_el_gancho_CUADRA_con_lo_que_se_paga_de_verdad():
    """No puede ser una cuenta aparte: si el gancho promete 60 € y el cálculo
    paga otra cosa, el comercial persigue una cifra que no existe."""
    for v in (0, 2400, 5900, 8000, 11400, 14999):
        g = falta(v, 10)
        assert g["porMuebleAhora"] == C.euros_por_mueble_comercial(v)
        # Justo al llegar al umbral se cobra ya lo prometido.
        assert C.euros_por_mueble_comercial(g["hasta"]) == g["porMuebleSiSalta"]


@pytest.mark.parametrize("basura", [None, "", "x", -100])
def test_una_valoracion_absurda_no_revienta(basura):
    g = falta(basura, 3)
    assert g is None or g["faltan"] >= 0
