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
Cantidad FIJA por mueble, y el tramo lo marca la **BASE IMPONIBLE** del pedido:
el PVP DESPUÉS del descuento y SIN IVA.

Costó dos correcciones llegar aquí, y las dos las hizo el master el 25/08:

  1. Al describirlo dijo «importes de costo … de valoración» y se implementó
     sobre el COSTE. Lo corrigió al verlo: «es sobre el PVP, no sobre el
     costo». No es menor — el PVP es muy superior al coste, así que con el
     mismo pedido el comercial sube de tramo.

  2. Luego preguntó qué pasa con los descuentos y lo zanjó: «siempre va sobre
     la base imponible, no sobre el total con IVA».

O sea, sobre esta cadena:

    Subtotal (PVP)  −  Descuento  =  BASE IMPONIBLE  ← el tramo sale de aquí
    Base imponible  +  IVA        =  Total

DOS COSAS QUE NO PUEDEN PASAR NUNCA, y por eso hay pruebas para las dos:

  · Que el tramo salga del TOTAL CON IVA. Sería pagar comisión sobre dinero de
    Hacienda, y además inflaría el tramo artificialmente: un pedido de 5.500 €
    de base se iría a 6.655 € con el 21% y saltaría de 30 a 40 € por mueble.

  · Que el tramo salga del subtotal SIN descontar. Sería comisionar sobre
    dinero que no ha entrado: con un 30% de descuento, un pedido de 2.700 €
    baja a 1.890 € de base y el tramo cae de 30 a 20.

    valoración < 2.500 €          ->  20 € por mueble
    de 2.500 € a 6.000 €          ->  30 € por mueble
    de 6.000 € a 9.000 €          ->  40 € por mueble
    de 9.000 € en adelante        ->  50 € por mueble   (25/08, el master)

    y un TOPE de 50 € por mueble, pase lo que pase.

EL TRAMO DE 9.000 € (25/08). El master lo añadió después: «9000 euros, 50 euros
por mueble». Con esto el TOPE de 50 € por fin coincide con el tramo más alto —
que era justo lo que faltaba para que el tope significara algo. Ojo: ahora el
tope y el tramo valen lo mismo, así que un tramo nuevo por encima de 50 quedaría
recortado en silencio. Si algún día hace falta, se sube el tope A LA VEZ; hay
una prueba que se pone roja si se separan.

LOS BORDES, YA CONFIRMADOS (25/08). Al describir los tramos el master dijo
«inferiores a 2.500» (20) y «superiores a 2.500» (30), así que el valor clavado
quedaba sin definir. Se implementó al alza —en la duda no se le quita dinero a
quien vende— y él lo confirmó después: «en 6.000 euros exactos, 40 euros». Por
simetría, en 2.500 y en 9.000 exactos se paga también el tramo de arriba.

    2.499,99 -> 20   2.500 -> 30   5.999,99 -> 30   6.000 -> 40
    8.999,99 -> 40   9.000 -> 50

`BORDE_AL_ALZA` sigue existiendo por si algún día se quiere lo contrario, pero
ya no es una duda: es una decisión tomada.
"""
from __future__ import annotations

from typing import Optional

# ─── Los tramos, tal cual los dictó el master ────────────────────────────────
#
# (hasta_valoracion, euros_por_mueble). `None` = de ahí para arriba.
TRAMOS_COMERCIAL = (
    (2500.0, 20.0),
    (6000.0, 30.0),
    (9000.0, 40.0),
    (None, 50.0),
)

# Tope absoluto por mueble. Desde que existe el tramo de 9.000 € coincide con
# el tramo más alto: recorta solo si alguien mete un tramo por encima de 50.
TOPE_COMERCIAL_POR_MUEBLE = 50.0

# En el borde exacto de un tramo (2.500 o 6.000 clavados) se cobra el tramo de
# ARRIBA. Lo confirmó el master el 25/08: «en 6.000 euros exactos, 40 euros».
BORDE_AL_ALZA = True


def base_imponible(pvp: float, descuento_pct: float = 0.0) -> float:
    """El número con el que se decide el tramo: PVP menos descuento, sin IVA.

    Se pone aquí, y no en la pantalla, para que exista UN SOLO sitio donde está
    escrito qué es «la base imponible» a efectos de comisión. Si cada pantalla
    lo calculara a su manera, acabarían pagando cosas distintas.

    El IVA no entra NUNCA: no se suma aquí ni se debe pasar un importe que ya lo
    lleve dentro.
    """
    try:
        bruto = float(pvp or 0)
    except (TypeError, ValueError):
        bruto = 0.0
    try:
        dto = float(descuento_pct or 0)
    except (TypeError, ValueError):
        dto = 0.0
    dto = min(max(dto, 0.0), 100.0)      # un descuento no es negativo ni pasa del 100%
    return round(max(0.0, bruto * (1 - dto / 100.0)), 2)


def euros_por_mueble_comercial(valoracion: float) -> float:
    """Lo que se lleva el comercial POR MUEBLE con esa BASE IMPONIBLE."""
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

    `valoracion` es la BASE IMPONIBLE del pedido —el PVP después del descuento
    y sin IVA— con la que se decide el tramo, y
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
    if (v < 9000.0) if BORDE_AL_ALZA else (v <= 9000.0):
        return "de 6.000 € a 9.000 €"
    return "más de 9.000 €"


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
