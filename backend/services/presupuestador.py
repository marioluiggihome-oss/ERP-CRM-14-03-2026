# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
QUIÉN PUEDE USAR CADA PESTAÑA DEL PRESUPUESTADOR. LA MITAD DEL SERVIDOR.

Gemelo de `frontend/src/presupuestador.js`. La pantalla decide qué PESTAÑAS
enseña; esto decide qué se puede HACER, que es lo único que cierra de verdad.

POR QUÉ ESTABA A MEDIAS. Al juntar Cocina Montada 3 y Cocina Desmontada bajo el
Presupuestador (28/08) el corte se dejó solo en pantalla, a propósito y
escrito en la regla 22: apretar candados a ciegas ya había dejado al master sin
sus propios precios ESE MISMO DÍA. El orden correcto es mirar primero a quién
afecta y cerrar después, y eso es lo que se ha hecho ahora.

QUÉ SE CIERRA, Y QUÉ NO. Se cierran las ESCRITURAS de cada sección: crear,
modificar y borrar. Un usuario sin `canUseCascos` ya no puede tocar Cocina
Desmontada llamando a la API por su cuenta, que era el agujero.

Las LECTURAS de `/cascos/orders` se quedan como estaban, y eso es una decisión,
no un descuido: de esa lista comen también Rentabilidad, el Expediente y
Almacén, que tienen su propia puerta y su propio permiso. Cerrarla aquí les
quitaría datos a pantallas que no son el Presupuestador — que es exactamente el
error del 28/08 otra vez. Además esa lista ya está recortada por dueño: quien no
es un rol elevado solo ve sus propios pedidos.

EL PERMISO SALE DEL ORIGEN DEL PEDIDO, no de qué endpoint se llame. Los dos
guardan en `cascos_orders` —Cocina Montada 3 crea pedidos ahí desde el 28/08—,
así que preguntar «¿puede usar Cocina Desmontada?» en `POST /cascos/orders`
dejaría sin poder pedir a un usuario que solo tiene Montada. Se mira de qué
sección es el pedido y se pide el permiso de ESA sección.
"""
from __future__ import annotations

from typing import Optional

from services import origen_pedidos as OP
from services.master import es_master

MONTADA = "montada"
DESMONTADA = "desmontada"

NOMBRES = {
    MONTADA: "Cocina Montada",
    DESMONTADA: "Cocina Desmontada",
}


# `is None`, NO `if not user`. Un usuario sin ningún permiso puesto es un `{}`,
# y en Python `{}` es falso mientras que en JavaScript es verdadero. Con
# `if not user` el servidor le cerraba Cocina Montada a quien la pantalla se la
# abría —el caso más corriente que hay: el usuario recién creado, sin ningún
# campo—, y la relación entera daba 403 al guardar. Lo cazó el candado que
# compara las dos mitades ejecutando el JS de verdad; leyendo los dos ficheros
# en paralelo no se ve, porque están escritos igual.
def puede_montada(user: Optional[dict]) -> bool:
    """Cocina Montada 3: el permiso es «no estar desactivado», como siempre."""
    if user is None:
        return False
    return es_master(user) or user.get("canUsePresupuestador3") is not False


def puede_desmontada(user: Optional[dict]) -> bool:
    """Cocina Desmontada: permiso EXPLÍCITO, y nunca para una tienda."""
    if user is None:
        return False
    if es_master(user):
        return True
    return user.get("canUseCascos") is True and not user.get("isTienda")


def pestanas_de(user: Optional[dict]) -> list:
    """Las pestañas que le tocan a ese usuario, en orden."""
    fuera = []
    if puede_montada(user):
        fuera.append(MONTADA)
    if puede_desmontada(user):
        fuera.append(DESMONTADA)
    return fuera


def puede_entrar(user: Optional[dict]) -> bool:
    """Si ve alguna, ve la sección."""
    return bool(pestanas_de(user))


def seccion_de_origen(origen) -> str:
    """La pestaña a la que pertenece un pedido, por su origen.

    Lo que no se reconoce cae en Cocina Desmontada, que es de quien es esa
    colección de siempre: `cascos_orders` la creó Desmontada y Montada 3 se metió
    después marcando sus pedidos. Y es además lo conservador, porque Desmontada
    es el permiso EXPLÍCITO de los dos: en la duda se pide el más estricto, no el
    más flojo. Al revés, un origen mal escrito sería la puerta de atrás.
    """
    return MONTADA if str(origen or "").strip().lower() == OP.MONTADA_3 else DESMONTADA


def puede_con_el_pedido(user: Optional[dict], origen) -> bool:
    """Si esa persona puede crear, cambiar o borrar un pedido de esa sección."""
    seccion = seccion_de_origen(origen)
    return puede_montada(user) if seccion == MONTADA else puede_desmontada(user)
