# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
cambios_proyecto.py — CONTROL DE CAMBIOS de un proyecto.

Qué había, qué se cambia, quién lo hizo, qué costó y si hace falta aprobarlo.

Antes de esto, `projects.py` ya guardaba en `versions` una instantánea del
estado ANTERIOR cada vez que cambiaban las líneas o los totales. Servía para no
perder el trabajo, pero no contestaba a la pregunta que importa cuando algo se
tuerce: *«¿quién cambió esto, cuándo, a peticion de quién y cuánto nos costó?»*.
Para saber qué cambió había que comparar dos instantáneas a mano.

Este módulo es solo cálculo — sin base de datos — para poder probarlo.

DOS REGLAS QUE NO SE SALTAN
---------------------------
1. **El impacto se DERIVA de cifras reales, nunca se estima.** Si falta el
   total de antes o el de después, el impacto queda en `None`, no en 0. Cero
   significa "no cambió"; `None` significa "no se sabe". Confundirlos es
   exactamente el tipo de número inventado que aquí no puede salir.

2. **Quién pidió el cambio NO se adivina.** Es un dato que solo tiene la
   persona: nace vacío y lo rellena quien lo sepa. Deducirlo del usuario que
   tecleó sería falso — el comercial teclea lo que pide el cliente.
"""
from datetime import datetime, timezone

# Estados en los que el cliente ya ha dicho que sí. A partir de aquí un cambio
# de dinero o de líneas no es "seguir presupuestando": es tocar algo pactado, y
# alguien tiene que aprobarlo antes de que llegue a fábrica.
ESTADOS_COMPROMETIDOS = {"aceptado", "entregado"}

# Quién puede pedir un cambio. Cerrado para que el reparto pueda sumarse
# después, igual que las causas de las incidencias.
ORIGENES = {
    "cliente":   "El cliente",
    "comercial": "Comercial",
    "diseno":    "Diseño",
    "fabrica":   "Fábrica",
    "obra":      "Obra / montaje",
    "medicion":  "Corrección de medición",
}


def _num(v):
    """Convierte a número, o None si no hay dato. Un texto vacío NO es 0."""
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _delta(antes, despues):
    """Diferencia solo si se conocen LAS DOS puntas. Si falta una, None."""
    a, d = _num(antes), _num(despues)
    if a is None or d is None:
        return None
    return round(d - a, 2)


def _cuenta_lineas(proyecto):
    """Nº de líneas del proyecto (montada + despiece)."""
    n = 0
    for campo in ("itemsMontada", "itemsDespiece"):
        v = proyecto.get(campo)
        if isinstance(v, list):
            n += len(v)
    return n


def es_critico(estado_proyecto, hay_cambio_economico, hay_cambio_de_lineas):
    """¿Este cambio necesita aprobación antes de seguir?

    Solo si el proyecto ya estaba comprometido con el cliente Y se ha movido
    dinero o líneas. Retocar un borrador no bloquea nada: si todo pidiera
    aprobación, se aprobaría todo sin mirar y el control no serviría.
    """
    return bool(
        (estado_proyecto or "").lower() in ESTADOS_COMPROMETIDOS
        and (hay_cambio_economico or hay_cambio_de_lineas)
    )


def resumen_cambio(antes, despues, autor=None, ahora=None):
    """Compara dos estados del proyecto y describe el cambio.

    `antes` y `despues` son el documento del proyecto antes y después.
    Devuelve el registro que se guarda en `cambios`, o None si no hay nada
    reseñable que anotar.
    """
    antes = antes or {}
    despues = despues or {}
    ahora = ahora or datetime.now(timezone.utc)

    impacto_pvp = _delta(antes.get("totalPvp"), despues.get("totalPvp"))
    impacto_coste = _delta(antes.get("totalCoste"), despues.get("totalCoste"))

    lineas_antes = _cuenta_lineas(antes)
    lineas_despues = _cuenta_lineas(despues)
    lineas_netas = lineas_despues - lineas_antes

    # "Hubo cambio" es distinto de "el impacto es cero": un cambio de 0 € puede
    # existir (cambiar un acabado por otro del mismo precio) y hay que anotarlo.
    hay_economico = bool(impacto_pvp) or bool(impacto_coste)
    hay_lineas = lineas_netas != 0

    estado = despues.get("status") or antes.get("status")
    critico = es_critico(estado, hay_economico, hay_lineas)

    if not hay_economico and not hay_lineas:
        return None   # nada que anotar: no se ensucia el historial

    return {
        "fecha": ahora.isoformat(),
        "autor": autor or None,
        "estadoProyecto": estado,
        # Qué había → qué hay ahora.
        "pvpAntes": _num(antes.get("totalPvp")),
        "pvpDespues": _num(despues.get("totalPvp")),
        "impactoPvp": impacto_pvp,
        "costeAntes": _num(antes.get("totalCoste")),
        "costeDespues": _num(despues.get("totalCoste")),
        "impactoCoste": impacto_coste,
        "lineasAntes": lineas_antes,
        "lineasDespues": lineas_despues,
        "lineasNetas": lineas_netas,
        # Lo que NO se puede deducir: nace vacío y lo rellena una persona.
        "pedidoPor": None,
        "motivo": "",
        # Aprobación.
        "critico": critico,
        "aprobadoPor": None,
        "aprobadoAt": None,
    }


def cambios_sin_aprobar(cambios):
    """Cambios críticos que siguen sin aprobar. Son los que bloquean."""
    return [c for c in (cambios or []) if c.get("critico") and not c.get("aprobadoAt")]


def puede_fabricar(proyecto):
    """¿Se puede mandar este proyecto a fabricar?

    Devuelve (bool, motivo). El motivo se escribe para que lo lea una persona
    con prisa en fábrica: dice QUÉ falta, no "hay errores".
    """
    pendientes = cambios_sin_aprobar((proyecto or {}).get("cambios"))
    if not pendientes:
        return True, ""

    n = len(pendientes)
    detalle = []
    for c in pendientes[:3]:
        imp = c.get("impactoPvp")
        euros = f"{imp:+.2f} €" if imp is not None else "impacto sin calcular"
        detalle.append(f"{c.get('fecha', '')[:10]} ({euros})")

    return False, (
        f"{n} cambio(s) sin aprobar tras aceptar el presupuesto: "
        + "; ".join(detalle)
        + ("…" if n > 3 else "")
    )
