# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LIQUIDACIÓN DE COMISIONES DE LOS COOPERATIVISTAS.

`comisiones.py` dice CUÁNTO se lleva cada uno. Este módulo dice CUÁNDO lo cobra,
que es harina de otro costal y donde está el riesgo de verdad: pagar dos veces,
pagar por un pedido que se cayó, o pagar por dinero que todavía no ha entrado.

LAS REGLAS, dictadas por el master el 25/08/2026:

    «las liquidaciones de comisiones se liquidan una vez al mes»

    «tanto el cooperativista comercial como el cooperativista montador ven los
    euros que van en progreso al irse aceptando los pedidos pero no se liberan
    hasta que no están totalmente servidos los pedidos y cobrados»

O sea que una comisión pasa por TRES estados, y solo el tercero es dinero
pagado:

  1. EN PROGRESO  — el pedido está aceptado. El cooperativista VE los euros
                    —para eso está el plan de estimulación— pero no son suyos
                    todavía. Si el pedido se cae, se caen con él.

  2. CONSOLIDADA  — el pedido está servido del todo Y cobrado del todo. Aquí la
                    comisión se «libera»: ya es un derecho, y entra en la
                    liquidación del mes en que se completó.

  3. LIQUIDADA    — ya se pagó en una liquidación cerrada. No vuelve a entrar
                    nunca más.

LAS DOS CONDICIONES SON UNA «Y», NO UNA «O». El master dijo «totalmente
servidos los pedidos Y cobrados». Servido sin cobrar no libera nada: la casa
habría puesto el material y el dinero seguiría fuera. Y cobrado sin servir
tampoco: un anticipo no es un pedido terminado.

«COBRADO» ES COBRADO DEL TODO. Este ERP lleva los cobros a cuenta (ver
`routes/rentabilidad.py`, `pendienteCobro`), así que un pedido puede estar
cobrado al 90%. Eso NO libera. Mientras quede un euro pendiente, la comisión se
queda en progreso. Se admite medio céntimo de tolerancia y nada más, que es
redondeo, no deuda.

EN QUÉ MES CAE: EN EL DE LA ENTREGA. El master, 25/08: «las comisiones se
liquidan cuando se entrega la mercancía […] y si se sirven en agosto se liquidan
en agosto». La fecha de cobro NO decide el mes.

Y no decide el mes porque no puede: «todos los pedidos antes de salir del
almacén tienen que estar cobrados». O sea que el cobro va SIEMPRE por delante de
la entrega, y el mes de la entrega es el más tardío de los dos por definición.

ENTONCES ¿PARA QUÉ SE SIGUE MIRANDO EL COBRO? Porque «tiene que estar cobrado»
es una norma de la casa, no una ley de la física. La norma la cumplen las
personas y el dato lo teclean las personas: un pedido puede salir con un
pendiente por un error, por un cobro que se apuntó tarde o por una excepción que
alguien autorizó. Si aquí se diera el cobro por hecho, ese día se pagaría una
comisión sobre dinero que no ha entrado, EN SILENCIO. Cuesta una comparación
dejarlo comprobado, y el día que la norma no se cumpla se entera alguien: la
línea sale marcada con `anomalia` en vez de liberarse sola. Un candado que se
apoya en que nadie se equivoque no es un candado.

LO QUE ESTE MÓDULO NO HACE, a propósito:

  · No decide quién es el comercial ni el montador de un pedido. Eso es
    asignación, y va en el pedido.
  · No lee la base de datos. Recibe pedidos ya normalizados (`normaliza`) y
    devuelve números. Así se puede probar entero sin Mongo, que es la única
    forma de tener candados de verdad sobre nómina.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Iterable, Optional

from services import comisiones

# ─── Los tres estados ────────────────────────────────────────────────────────
EN_PROGRESO = "en_progreso"
CONSOLIDADA = "consolidada"
LIQUIDADA = "liquidada"

# Los dos roles que cobran comisión.
COMERCIAL = "comercial"
MONTADOR = "montador"

# Medio céntimo. Por debajo de esto es redondeo; por encima es deuda y no libera.
TOLERANCIA_COBRO = 0.005

# En qué mes cae una comisión consolidada: en el de la ENTREGA de la mercancía.
# Master, 25/08: «si se sirven en agosto se liquidan en agosto». Ver la nota.
PERIODO_POR = "servido"


def _fecha(v) -> Optional[date]:
    """Acepta date, datetime o «2026-08-25...». Lo que no se entienda es None.

    None NO es «hoy» ni «el principio de los tiempos»: es «no se sabe», y una
    fecha que no se sabe no puede liberar una comisión (CLAUDE.md: nunca
    inventar un dato que no se tiene).
    """
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).date()
    except (TypeError, ValueError):
        return None


def periodo_de(v) -> Optional[str]:
    """La fecha -> «2026-08», que es la unidad de liquidación."""
    f = _fecha(v)
    return f"{f.year:04d}-{f.month:02d}" if f else None


def _num(v) -> float:
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def _entero(v) -> int:
    try:
        return max(0, int(v or 0))
    except (TypeError, ValueError):
        return 0


def normaliza(pedido: dict) -> dict:
    """Deja un pedido en los pocos datos de los que depende una comisión.

    Es IDEMPOTENTE, y se llama siempre. Hubo un intento de ahorrársela cuando el
    pedido «ya venía normalizado», mirando si traía la clave `aceptadoAt` — y un
    pedido crudo la trae, así que el atajo se saltaba la normalización y luego
    reventaba buscando una clave que no existía. Adivinar si un dato ya está
    preparado es justo la clase de atajo que no cabe en nómina: cuesta un
    microsegundo y quita una forma de romperse.

    Se hace explícito a propósito. Si este módulo leyera directamente los
    documentos de Mongo, cualquier cambio de nombre de un campo lo rompería en
    silencio — y en silencio, aquí, significa que alguien cobra de menos.
    """
    p = pedido or {}
    servido = _fecha(p.get("servidoAt"))
    cobrado = _fecha(p.get("cobradoAt"))
    return {
        "id": p.get("id") or p.get("_id") or "",
        "aceptadoAt": _fecha(p.get("aceptadoAt") or p.get("acceptedAt")),
        "servidoAt": servido,
        "cobradoAt": cobrado,
        "pendienteCobro": _num(p.get("pendienteCobro")),
        "anulado": bool(p.get("anulado") or p.get("rechazado")),
        "muebles": _entero(p.get("muebles")),
        "baseImponible": _num(p.get("baseImponible")),
        "manoPorMueble": _num(p.get("manoPorMueble")),
        "liquidadoEn": p.get("liquidadoEn") or None,
        "comercialId": p.get("comercialId") or "",
        "montadorUserId": p.get("montadorUserId") or "",
    }


def esta_servido(p: dict) -> bool:
    return p["servidoAt"] is not None


def esta_cobrado(p: dict) -> bool:
    """Cobrado del TODO. Un cobro a cuenta no libera nada."""
    return p["cobradoAt"] is not None and p["pendienteCobro"] <= TOLERANCIA_COBRO


def estado_de(pedido: dict) -> Optional[str]:
    """El estado de la comisión de un pedido, o None si no cuenta para nada.

    Devuelve None —y no «cero euros»— cuando el pedido ni siquiera está
    aceptado o se ha caído: son cosas distintas y mezclarlas haría que un pedido
    anulado apareciera en el panel del comercial como una línea a cero,
    recordándole lo que no va a cobrar.
    """
    p = normaliza(pedido)
    if p["anulado"] or p["aceptadoAt"] is None:
        return None
    if p["liquidadoEn"]:
        return LIQUIDADA
    if esta_servido(p) and esta_cobrado(p):
        return CONSOLIDADA
    return EN_PROGRESO


def periodo_de_consolidacion(pedido: dict) -> Optional[str]:
    """El mes en que se paga: el de la ENTREGA de la mercancía.

    Master, 25/08: «si se sirven en agosto se liquidan en agosto». La fecha de
    cobro no entra en esta cuenta — solo decide SI se libera, no CUÁNDO.
    """
    p = normaliza(pedido)
    if not (esta_servido(p) and esta_cobrado(p)):
        return None
    return periodo_de(p["servidoAt"])


def es_anomalia(pedido: dict) -> bool:
    """Salió del almacén sin estar cobrado del todo. No debería poder pasar.

    «Todos los pedidos antes de salir del almacén tienen que estar cobrados»
    (master, 25/08). Cuando aparece uno así, la comisión NO se libera —no se
    paga sobre dinero que no ha entrado— pero tampoco se queda callada en el
    montón de «en progreso», donde parecería un pedido normal a medio hacer. Se
    marca, para que se vea que hay mercancía fuera y dinero sin entrar.
    """
    p = normaliza(pedido)
    if p["anulado"] or p["aceptadoAt"] is None:
        return False
    return esta_servido(p) and not esta_cobrado(p)


def euros_de(pedido: dict, rol: str) -> float:
    """Lo que ese pedido le vale a ese rol. El cuánto sale de `comisiones.py`."""
    p = normaliza(pedido)
    if rol == COMERCIAL:
        d = comisiones.comision_comercial(p["baseImponible"], p["muebles"])
    elif rol == MONTADOR:
        d = comisiones.comision_montadores(p["manoPorMueble"], p["muebles"])
    else:
        raise ValueError(f"rol desconocido: {rol!r}")
    return d["total"]


def linea(pedido: dict, rol: str) -> Optional[dict]:
    """Una línea del panel: qué pedido, en qué estado y cuántos euros."""
    p = normaliza(pedido)
    est = estado_de(p)
    if est is None:
        return None
    return {
        "pedidoId": p["id"],
        "estado": est,
        "anomalia": es_anomalia(p),
        "euros": euros_de(p, rol),
        "muebles": p["muebles"],
        "periodo": p["liquidadoEn"] if est == LIQUIDADA else periodo_de_consolidacion(p),
        "porMueble": (comisiones.euros_por_mueble_comercial(p["baseImponible"])
                      if rol == COMERCIAL else round(p["manoPorMueble"], 2)),
        "tramo": (comisiones._nombre_del_tramo(p["baseImponible"])
                  if rol == COMERCIAL else None),
    }


def panel(pedidos: Iterable[dict], rol: str) -> dict:
    """Lo que ve un cooperativista al entrar en su área.

    Los tres montones separados, nunca sumados en uno solo: «en progreso» y
    «a cobrar» son promesas de distinto valor y juntarlas sería enseñar un
    número que no significa nada.
    """
    lineas = [l for l in (linea(p, rol) for p in (pedidos or [])) if l]
    por_estado = {EN_PROGRESO: [], CONSOLIDADA: [], LIQUIDADA: []}
    for l in lineas:
        por_estado[l["estado"]].append(l)

    def suma(k):
        return round(sum(l["euros"] for l in por_estado[k]), 2)

    return {
        "rol": rol,
        "enProgreso": {"euros": suma(EN_PROGRESO), "pedidos": len(por_estado[EN_PROGRESO]),
                       "lineas": por_estado[EN_PROGRESO]},
        "consolidada": {"euros": suma(CONSOLIDADA), "pedidos": len(por_estado[CONSOLIDADA]),
                        "lineas": por_estado[CONSOLIDADA]},
        "liquidada": {"euros": suma(LIQUIDADA), "pedidos": len(por_estado[LIQUIDADA]),
                      "lineas": por_estado[LIQUIDADA]},
    }


def liquidacion_del_mes(pedidos: Iterable[dict], rol: str, periodo: str) -> dict:
    """Lo que se le paga a ese cooperativista en la liquidación de ese mes.

    Entra SOLO lo consolidado en ese periodo. Lo ya liquidado no vuelve a entrar
    —esa es toda la gracia del tercer estado— y lo que está en progreso tampoco,
    por mucho que el cooperativista lo esté viendo en su panel.
    """
    dentro = []
    for p in (pedidos or []):
        l = linea(p, rol)
        if l and l["estado"] == CONSOLIDADA and l["periodo"] == periodo:
            dentro.append(l)
    return {
        "rol": rol,
        "periodo": periodo,
        "pedidos": len(dentro),
        "muebles": sum(l["muebles"] for l in dentro),
        "euros": round(sum(l["euros"] for l in dentro), 2),
        "lineas": dentro,
    }
