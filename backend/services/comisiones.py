# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
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
MV. No es un concepto nuevo ni un porcentaje: es ese importe, por mueble
montado. Lo único que faltaba era sumarlo y llamarlo por su nombre.

Son 17 € por mueble (master, 28/08) y CADA MONTADOR PUEDE TENER LA SUYA: el
master le pone su cifra a quien haga falta y, si no se la pone, cobra la de la
casa. Ver `mano_de_obra_de()`.

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
    de 9.000 € a 12.000 €         ->  50 € por mueble
    de 12.000 € a 15.000 €        ->  60 € por mueble
    de 15.000 € en adelante       ->  70 € por mueble

    y un TOPE de 70 € por mueble, pase lo que pase.

CÓMO CRECIÓ LA ESCALA (todo el 25/08, y todo dictado por el master). Primero
tres tramos —20 / 30 / 40— y un tope de 50 € que no llegaba a aplicarse nunca.
Después «9000 euros, 50 euros por mueble». Y después los dos de arriba: «el
bloque de 12000 y 60 euros de prima» y «el último bloque de 15000 euros y 70
euros de prima».

EL TOPE SUBE CON LOS TRAMOS, SIEMPRE. Al añadir el de 12.000 € la escala pasó
por encima del tope de 50 que había, y eso NO da error: `min(euros, TOPE)`
habría recortado los 60 y los 70 a 50 en silencio, y el comercial cobraría de
menos sin que nadie se enterase. Por eso el tope subió a 70 en el mismo cambio.
Regla, para el siguiente que pase por aquí: **un tramo nuevo por encima del tope
obliga a subir el tope A LA VEZ**, y a preguntárselo al master antes, que esto
es nómina. Hay una prueba que se pone roja si se separan.

CONFIRMADO: el tope se queda en 70 «de momento» (master, 25/08). Se le preguntó
expresamente si quería un techo POR ENCIMA de la escala —hoy tope y tramo más
alto valen lo mismo, así que el tope no recorta nada— y dijo que no. O sea que
esto no es un descuido ni un cabo suelto: es la decisión. Que no recorte hoy es
lo correcto; lo que hace falta es que siga sin recortar el día que suba un
tramo, y de eso se encarga la prueba de arriba.

LOS BORDES, YA CONFIRMADOS (25/08). Al describir los tramos el master dijo
«inferiores a 2.500» (20) y «superiores a 2.500» (30), así que el valor clavado
quedaba sin definir. Se implementó al alza —en la duda no se le quita dinero a
quien vende— y él lo confirmó después: «en 6.000 euros exactos, 40 euros». Por
simetría, en TODOS los bordes clavados se paga el tramo de arriba.

    2.499,99 -> 20    2.500 -> 30     5.999,99 -> 30    6.000 -> 40
    8.999,99 -> 40    9.000 -> 50    11.999,99 -> 50   12.000 -> 60
   14.999,99 -> 60   15.000 -> 70

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
    (12000.0, 50.0),
    (15000.0, 60.0),
    (None, 70.0),
)

# Tope absoluto por mueble. Sube CON el tramo más alto, nunca por detrás: si se
# quedara en 50 mientras hay tramos de 60 y 70, `euros_por_mueble_comercial` los
# recortaría a 50 en silencio y el comercial cobraría de menos sin que saltara
# ningún error. Hay una prueba que se pone roja si se separan.
TOPE_COMERCIAL_POR_MUEBLE = 70.0

# En el borde exacto de un tramo (2.500, 6.000, 9.000… clavados) se cobra el
# tramo de ARRIBA. Lo confirmó el master el 25/08: «en 6.000 euros exactos, 40
# euros».
BORDE_AL_ALZA = True


# ─── QUÉ CUENTA PARA LA COMISIÓN: SOLO LOS MUEBLES ──────────────────────────
#
# El master, 25/08/2026: «las líneas de muebles siempre incentivarán a los
# comerciales, pero las puertas y los costados y las líneas manuales con los
# distintos servicios que añadamos manualmente no van a llevar compensación de
# ningún tipo. Solo los muebles».
#
# No es un matiz: cambia el DINERO por los dos lados. Contar puertas y costados
# infla el número de unidades (se paga de más por mueble) y además mete su
# importe en la valoración, que es la que decide el TRAMO. Un pedido de 11.000 €
# de muebles con 1.500 € de puertas saltaría a un tramo que no le toca, y
# cobraría más por cada mueble además de por las puertas.
#
# LAS DOS LISTAS SALEN DE DATOS QUE YA ESTABAN EN EL ERP, no de una lista
# escrita a ojo que se quedaría vieja:
#
#   · Categoría «lineal» de `nomenclaturas_pdf.FAMILIAS`: costados, laterales,
#     regletas, techos y elementos lineales.
#   · Tipo «matrix» de la tarifa MV: PUERTAS, VITRINA y REJILLA. Son FRENTES —
#     se tarifan por alto x ancho, no por código de mueble.
#
# OJO con no pasarse: un ALTO_VITRINA o una MEDIACOLUMNA_VITRINA SÍ son muebles
# (un casco con puerta de cristal). Lo que no lo es son las familias de frentes
# sueltos. Por eso el corte va por `matrix`, no por la palabra «vitrina».
def _familias_que_no_son_mueble() -> frozenset:
    fuera = set()
    try:
        from services.nomenclaturas_pdf import FAMILIAS
        fuera |= {k for k, v in FAMILIAS.items()
                  if isinstance(v, (list, tuple)) and len(v) > 1 and v[1] == "lineal"}
    except Exception:                                    # noqa: BLE001
        pass
    try:
        import json as _json
        import os as _os
        ruta = _os.path.join(_os.path.dirname(_os.path.dirname(
            _os.path.abspath(__file__))), "data", "mv_tarifas_oficiales.json")
        with open(ruta, "r", encoding="utf-8") as f:
            t1 = _json.load(f)["tariffs"]["T1"]
        fuera |= {k for k, v in t1.items() if v.get("type") == "matrix"}
    except Exception:                                    # noqa: BLE001
        pass
    # Red de seguridad por si algún día no se pudiera leer ninguna de las dos:
    # mejor de más que de menos, porque de menos se PAGA de más.
    fuera |= {"PUERTAS", "VITRINA", "VITRINA_INGLESA", "REJILLA_CONFESIONARIO",
              "COSTADOS_COLOR", "COSTADOS_MELAMINA", "LATERALES_COLOR",
              "REGLETA_COLOR", "REGLETA_MELAMINA", "TECHO_COLOR",
              "ELEMENTOS_LINEALES"}
    return frozenset(fuera)


FAMILIAS_SIN_COMISION = _familias_que_no_son_mueble()


def es_mueble(linea: dict) -> bool:
    """¿Esta línea de un pedido incentiva al comercial?

    NO incentivan: puertas, vitrinas y rejillas (frentes), costados, laterales,
    regletas, techos y elementos lineales, y las LÍNEAS MANUALES — las que
    alguien teclea a mano para un servicio, que no tienen familia del catálogo.

    Una línea sin familia se trata como servicio y NO cuenta. Es la decisión
    conservadora a propósito: si un día entra una línea rara sin clasificar,
    que no se pague de más. Pagar de menos se reclama; pagar de más no se
    devuelve.
    """
    if not linea:
        return False
    fam = str(linea.get("familia") or "").strip().upper()
    if not fam:
        return False                       # línea manual / servicio
    return fam not in FAMILIAS_SIN_COMISION


def base_de_comision(lineas, descuento_pct: float = 0.0) -> dict:
    """Las unidades y la valoración que entran en la comisión: SOLO muebles.

    Devuelve también lo que se ha dejado fuera, para poder enseñarlo en pantalla:
    un comercial que ve «14 muebles» en un pedido de 20 líneas tiene que poder
    entender por qué, o pensará que le están quitando.
    """
    muebles = uds_fuera = 0
    pvp_muebles = pvp_fuera = 0.0
    for l in (lineas or []):
        try:
            qty = max(0, int(l.get("qty") or l.get("cant") or 1))
        except (TypeError, ValueError):
            qty = 0
        try:
            pvp = float(l.get("pvp") or 0) * qty
        except (TypeError, ValueError):
            pvp = 0.0
        if es_mueble(l):
            muebles += qty
            pvp_muebles += pvp
        else:
            uds_fuera += qty
            pvp_fuera += pvp
    return {
        "muebles": muebles,
        "baseImponible": base_imponible(pvp_muebles, descuento_pct),
        "pvpMuebles": round(pvp_muebles, 2),
        "sinComision": {"unidades": uds_fuera, "pvp": round(pvp_fuera, 2)},
    }


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


# Lo que cobra un montador por mueble montado si nadie le ha puesto otra cosa.
# El master, 28/08/2026: «la rentabilidad por mueble montado va a ser de 17
# euros, no de 20». Vive aquí y no en la pantalla porque este fichero es el que
# dice CUÁNTO se cobra (regla 16); la pantalla y los ajustes leen de aquí.
MANO_DE_OBRA_POR_DEFECTO = 17.0


def mano_de_obra_de(user: Optional[dict], ajustes: Optional[dict] = None) -> float:
    """€ por mueble montado de ESE montador.

    Manda lo que el master le haya puesto a él; si no tiene cifra propia, la de
    la casa; y si tampoco hay ajuste, el valor por defecto.

    OJO CON EL CERO. Se mira si la cifra ESTÁ, no si es verdadera: un 0 tecleado
    a propósito por el master es una decisión suya y se respeta. Con un
    `or` —que es como estaba escrito en las rutas— un 0 se caería al siguiente
    escalón y el montador cobraría sin que nadie lo hubiera decidido, que es el
    error que más caro sale: pagar de más no se devuelve.

    Un valor que no sea un número (una casilla con texto, un `None` guardado
    raro) NO cae en el defecto: cae en el escalón siguiente, para que un dato
    corrupto no invente una nómina.
    """
    for fuente, clave in (((user or {}), "manoObraPorMueble"),
                          ((ajustes or {}), "manoObraPorMueble")):
        if clave not in fuente or fuente[clave] is None:
            continue
        try:
            return max(0.0, float(fuente[clave]))
        except (TypeError, ValueError):
            continue
    return MANO_DE_OBRA_POR_DEFECTO


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


def _euros(v: float) -> str:
    """12000 -> «12.000 €». Con el punto de los miles, como se escribe aquí."""
    return f"{int(round(v)):,}".replace(",", ".") + " €"


def _nombre_del_tramo(valoracion: float) -> str:
    """Para poder decir en pantalla POR QUÉ sale ese importe.

    Se DERIVA de `TRAMOS_COMERCIAL` a propósito. Antes eran seis `if` escritos a
    mano, o sea los tramos otra vez, en el mismo fichero, con otras palabras. Y
    ya se rompió: al añadir el tramo de 9.000 € el importe pasó a 50 € y la
    etiqueta se quedó diciendo «más de 6.000 €» —el número bien y la explicación
    mintiendo—. Derivándolo, añadir un tramo no puede desincronizar el rótulo.
    """
    try:
        v = float(valoracion or 0)
    except (TypeError, ValueError):
        v = 0.0
    anterior = None
    for tope, _ in TRAMOS_COMERCIAL:
        if tope is None:
            break
        cabe = v < tope if BORDE_AL_ALZA else v <= tope
        if cabe:
            if anterior is None:
                return f"menos de {_euros(tope)}"
            return f"de {_euros(anterior)} a {_euros(tope)}"
        anterior = tope
    return f"más de {_euros(anterior)}" if anterior is not None else "todos"


def cuanto_falta_para_el_siguiente_tramo(valoracion: float, muebles: int) -> Optional[dict]:
    """Cuánto le falta a este pedido para saltar de tramo, y qué supone en euros.

    Es el motor del PLAN DE ESTIMULACIÓN que pidió el master: no basta con
    enseñarle al comercial lo que lleva ganado, hay que enseñarle lo que tiene a
    un paso. «Este pedido va por 11.400 €; con 600 € más pasas a 60 € por
    mueble, y con 14 muebles son 140 € más para ti.»

    Devuelve `None` cuando ya está en el tramo más alto: ahí no hay nada que
    perseguir, y enseñar un objetivo inalcanzable desmotiva en vez de estimular.

    El umbral se calcula con el mismo criterio del borde que el resto del módulo
    (`BORDE_AL_ALZA`): llegar JUSTO a 12.000 € ya cuenta como el tramo de
    arriba, así que lo que falta es llegar al número, no pasarlo.
    """
    try:
        v = max(0.0, float(valoracion or 0))
    except (TypeError, ValueError):
        v = 0.0
    uds = _entero_no_negativo(muebles)
    ahora = euros_por_mueble_comercial(v)

    # CUIDADO CON LA FORMA DE LA TABLA. Cada par es (hasta, euros): «hasta ese
    # importe se cobra eso». Así que el umbral para saltar NO es el `tope` del
    # tramo siguiente, sino el del tramo en el que se está AHORA.
    #
    # La primera versión cogía el siguiente y decía que a un pedido de 11.400 €
    # le faltaban 3.600 € cuando le faltaban 600: se saltaba el escalón entero.
    # Un plan de estimulación que enseña un objetivo seis veces más lejos de lo
    # que está desanima en vez de estimular, que es lo contrario de para lo que
    # se hizo.
    for i, (tope, _euros) in enumerate(TRAMOS_COMERCIAL):
        if tope is None:
            break                                  # ya está en el más alto
        cabe = v < tope if BORDE_AL_ALZA else v <= tope
        if not cabe:
            continue
        if i + 1 >= len(TRAMOS_COMERCIAL):
            break
        euros = TRAMOS_COMERCIAL[i + 1][1]
        faltan = round(max(0.0, tope - v), 2)
        if not BORDE_AL_ALZA:
            faltan = round(faltan + 0.01, 2)
        extra_por_mueble = round(euros - ahora, 2)
        if extra_por_mueble <= 0:
            break
        return {
            "faltan": faltan,
            "desde": round(v, 2),
            "hasta": tope,
            "porMuebleAhora": ahora,
            "porMuebleSiSalta": euros,
            "extraPorMueble": extra_por_mueble,
            "extraTotal": round(extra_por_mueble * uds, 2),
            "muebles": uds,
            "tramoSiguiente": _nombre_del_tramo(tope),
        }
    return None


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
