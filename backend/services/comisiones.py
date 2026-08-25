# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
COMISIONES DE LOS COOPERATIVISTAS: MONTADORES Y COMERCIALES.

Esto es NÓMINA. Aquí no hay ni un número puesto «a ojo»: los tramos los dictó
el master el 25/08/2026 y están escritos tal cual los dijo. Si algún día hay
que cambiarlos, se cambian aquí y en un solo sitio — repartidos por la pantalla
acabarían diciendo cosas distintas, y entonces alguien cobra de menos.

MONTADORES
----------
Su comisión ES la mano de obra que ya se teclea en la casilla de Rentabilidad
MV (`MV_COSTES_DEFAULT.mano`, 20 € por mueble por defecto). No es un concepto
nuevo ni un porcentaje: es ese importe, por mueble fabricado. Lo único que
faltaba era sumarlo y llamarlo por su nombre.

COMERCIALES
-----------
Cantidad FIJA por mueble, y el tramo lo marca el **PVP** del pedido.

OJO CON ESTO, que ya se hizo mal una vez: al describirlo, el master dijo
«importes de costo … de valoración» y se implementó sobre el COSTE. Al verlo en
pantalla lo corrigió: «es sobre el PVP, no sobre el costo». La diferencia no es
menor — el PVP de un pedido es muy superior a su coste, así que con el mismo
pedido el comercial sube de tramo y cobra más.

    valoración < 2.500 €          ->  20 € por mueble
    de 2.500 € a 6.000 €          ->  30 € por mueble
    más de 6.000 €                ->  40 € por mueble

    y un TOPE de 50 € por mueble, pase lo que pase.

UNA COSA QUE EL MASTER TIENE QUE CONFIRMAR, y que queda marcada en el código
para que no se olvide:

  1. Qué pasa EXACTAMENTE en 2.500 € y en 6.000 €. Dijo «inferiores a 2.500»
     (20) y «superiores a 2.500» (30), así que el valor exacto quedó sin
     definir. Aquí el borde va al tramo de ARRIBA —en 2.500 clavados se pagan
     30— porque en la duda no se le quita dinero a quien vende. Cambiar
     `BORDE_AL_ALZA` a False lo pasa al tramo de abajo.

  2. El tope de 50 €. Hoy NO llega a aplicarse nunca: el tramo más alto son
     40 €, así que 50 no muerde. Se deja puesto porque el master lo pidió y
     porque el día que se añada un tramo por encima, el tope ya está.
"""
from __future__ import annotations

from typing import Optional

# ─── Los tramos, tal cual los dictó el master ────────────────────────────────
#
# (hasta_valoracion, euros_por_mueble). `None` = de ahí para arriba.
TRAMOS_COMERCIAL = (
    (2500.0, 20.0),
    (6000.0, 30.0),
    (None, 40.0),
)

# Tope absoluto por mueble. Ver la nota 2 de arriba.
TOPE_COMERCIAL_POR_MUEBLE = 50.0

# En el borde exacto de un tramo (2.500 o 6.000 clavados), ¿se cobra el tramo
# de arriba o el de abajo? Arriba: en la duda no se le quita dinero a quien
# vende. Pendiente de que el master lo confirme.
BORDE_AL_ALZA = True


def euros_por_mueble_comercial(valoracion: float) -> float:
    """Lo que se lleva el comercial POR MUEBLE con esa valoración de pedido."""
    try:
        v = float(valoracion or 0)
    except (TypeError, ValueError):
        v = 0.0
    if v < 0:
        v = 0.0
    for tope, euros in TRAMOS_COMERCIAL:
        if tope is None:
            return min(euros, TOPE_COMERCIAL_POR_MUEBLE)
        cabe = v < tope if BORDE_AL_ALZA else v <= tope
        if cabe:
            return min(euros, TOPE_COMERCIAL_POR_MUEBLE)
    return min(TRAMOS_COMERCIAL[-1][1], TOPE_COMERCIAL_POR_MUEBLE)


def _entero_no_negativo(n) -> int:
    try:
        v = int(n or 0)
    except (TypeError, ValueError):
        return 0
    return max(0, v)


def comision_comercial(valoracion: float, muebles: int) -> dict:
    """Comisión del comercial de un pedido entero.

    `valoracion` es el PVP del pedido (no el coste: lo corrigió el master el
    25/08) con el que se decide el tramo, y
    `muebles` las UNIDADES (no las líneas: una línea de 4 muebles son 4 — regla
    4 de CLAUDE.md, las unidades multiplican).
    """
    uds = _entero_no_negativo(muebles)
    por_mueble = euros_por_mueble_comercial(valoracion)
    return {
        "porMueble": round(por_mueble, 2),
        "muebles": uds,
        "total": round(por_mueble * uds, 2),
        "tramo": _nombre_del_tramo(valoracion),
    }


def comision_montadores(mano_por_mueble: float, muebles: int) -> dict:
    """Comisión de los montadores: la mano de obra que ya se teclea, por mueble.

    No se calcula nada nuevo a propósito. Si esto empezara a tener su propia
    fórmula, habría dos números distintos para lo mismo —el coste de mano de
    obra y la comisión— y en algún momento dejarían de cuadrar.
    """
    try:
        mano = float(mano_por_mueble or 0)
    except (TypeError, ValueError):
        mano = 0.0
    mano = max(0.0, mano)
    uds = _entero_no_negativo(muebles)
    return {
        "porMueble": round(mano, 2),
        "muebles": uds,
        "total": round(mano * uds, 2),
    }


def _nombre_del_tramo(valoracion: float) -> str:
    """Para poder decir en pantalla POR QUÉ sale ese importe."""
    try:
        v = float(valoracion or 0)
    except (TypeError, ValueError):
        v = 0.0
    if (v < 2500.0) if BORDE_AL_ALZA else (v <= 2500.0):
        return "menos de 2.500 €"
    if (v < 6000.0) if BORDE_AL_ALZA else (v <= 6000.0):
        return "de 2.500 € a 6.000 €"
    return "más de 6.000 €"


def resumen(valoracion: float, muebles: int, mano_por_mueble: float,
            unidades: Optional[int] = None) -> dict:
    """Las dos comisiones de un pedido, juntas. Lo que pinta la pantalla."""
    uds = _entero_no_negativo(unidades if unidades is not None else muebles)
    com = comision_comercial(valoracion, uds)
    mon = comision_montadores(mano_por_mueble, uds)
    return {
        "valoracion": round(float(valoracion or 0), 2),
        "muebles": uds,
        "comercial": com,
        "montadores": mon,
        "total": round(com["total"] + mon["total"], 2),
    }
