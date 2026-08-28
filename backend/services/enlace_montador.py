# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LA FICHA DE MONTADOR Y LA CUENTA DE USUARIO ERAN DOS MUNDOS.

En la agenda de montajes, cada montaje apunta a una FICHA (`montadores.id`) y
lleva la referencia del presupuesto (`budgetRef` / `budgetId`). En la
liquidación, cada pedido apunta a una CUENTA (`montadorUserId`). Nadie unía las
dos cosas, así que el master tenía que volver a decir a mano quién montó cada
pedido cuando el ERP ya lo sabía: estaba en la agenda.

El puente es `usuario.montadorId`, un campo que YA existía en el modelo desde
antes y que no leía nadie. Ahora se usa:

    pedido --budgetRef--> montaje --montadorId--> ficha --montadorId--> usuario

SE SUGIERE, NO SE ASIGNA. Esto devuelve una propuesta; quien la aplica es el
master (CLAUDE.md, regla 20: asignar comercial o montador es suyo, porque mueve
una comisión de un bolsillo a otro). Ahorrar clics no puede convertirse en pagar
por deducción.

Y NO SE SUGIERE NADA EN LA DUDA. Los tres casos en que se calla:

  · el montaje apunta a una ficha que no tiene cuenta de usuario;
  · esa cuenta existe pero NO es socio montador. OJO CON ESTO, que el master lo
    subrayó el 28/08: «los montadores pueden ser externos o miembros de la
    cooperativa». En la agenda están LOS DOS, mezclados, porque los dos montan
    cocinas — pero solo el socio cobra comisión. Un externo con ficha, agenda y
    montajes hechos sigue sin entrar en la nómina, y la agenda no puede ser la
    puerta por la que entre;
  · hay varios montajes del mismo pedido con montadores DISTINTOS — ahí quién
    cobra lo decide el master, no un desempate escrito por mí.

En los tres, el pedido se queda sin sugerencia y sigue saliendo como «sin
asignar», que es justo donde el master lo va a ver.
"""
from __future__ import annotations

from typing import Iterable, Optional

from services import area_cooperativista as AC


def _texto(v) -> str:
    return str(v or "").strip()


def _refs_del_pedido(pedido: dict) -> tuple:
    """Por dónde se puede atar un pedido a un montaje de la agenda."""
    p = pedido or {}
    return tuple(r for r in (_texto(p.get("budgetNumber")),
                             _texto(p.get("projectReference")),
                             _texto(p.get("projectId")),
                             _texto(p.get("id"))) if r)


def _refs_del_montaje(montaje: dict) -> tuple:
    m = montaje or {}
    return tuple(r for r in (_texto(m.get("budgetRef")),
                             _texto(m.get("budgetId"))) if r)


def cuentas_por_ficha(usuarios: Iterable[dict]) -> dict:
    """`montadores.id` → la cuenta de usuario que lleva esa ficha.

    Si dos cuentas llevaran la misma ficha no se elige ninguna: eso es un error
    de datos, y resolverlo a dedo sería pagarle a una de las dos por sorteo.
    """
    por_ficha: dict = {}
    for u in (usuarios or []):
        ficha = _texto((u or {}).get("montadorId"))
        if not ficha:
            continue
        por_ficha.setdefault(ficha, []).append(u)
    return {f: cuentas[0] for f, cuentas in por_ficha.items() if len(cuentas) == 1}


def indexar_montajes(montajes: Iterable[dict]) -> dict:
    indice: dict = {}
    for m in (montajes or []):
        for r in _refs_del_montaje(m):
            indice.setdefault(r, []).append(m)
    return indice


def sugerencia_para(pedido: dict, indice_montajes: dict,
                    cuentas: dict) -> Optional[dict]:
    """Qué socio montador propone la agenda para ese pedido, o `None`.

    Devuelve también el porqué, para que la pantalla pueda enseñarlo: una
    sugerencia sobre nómina que no dice de dónde sale no es de fiar.
    """
    montajes, vistos = [], set()
    for r in _refs_del_pedido(pedido):
        for m in indice_montajes.get(r, []):
            if id(m) not in vistos:
                vistos.add(id(m))
                montajes.append(m)
    if not montajes:
        return None

    fichas = {_texto(m.get("montadorId")) for m in montajes}
    fichas.discard("")
    if len(fichas) != 1:
        # Varios montadores en el mismo pedido: lo decide el master.
        return None

    ficha = fichas.pop()
    cuenta = cuentas.get(ficha)
    if not cuenta:
        return None
    if AC.rol_de(cuenta) != AC.MONTADOR:
        # Monta cocinas, pero no es socio montador: no cobra comisión.
        return None

    m = montajes[0]
    return {
        "montadorUserId": _texto(cuenta.get("id")),
        "nombre": _texto(cuenta.get("clientName") or cuenta.get("username")),
        "porque": _texto(m.get("montadorName")) or ficha,
        "montajeRef": _refs_del_montaje(m)[0] if _refs_del_montaje(m) else "",
    }


def sugerencias(pedidos: Iterable[dict], montajes: Iterable[dict],
                usuarios: Iterable[dict]) -> dict:
    """`pedidoId` → sugerencia, SOLO para los pedidos que no tienen montador.

    Lo que el master ya asignó no se toca ni se propone cambiar: una sugerencia
    encima de una decisión suya es una invitación a deshacerla sin querer.
    """
    indice = indexar_montajes(montajes)
    cuentas = cuentas_por_ficha(usuarios)
    fuera = {}
    for p in (pedidos or []):
        if _texto((p or {}).get("montadorUserId")):
            continue
        s = sugerencia_para(p, indice, cuentas)
        if s:
            fuera[_texto((p or {}).get("id"))] = s
    return fuera
