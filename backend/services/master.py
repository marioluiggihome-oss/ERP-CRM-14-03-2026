# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
QUIÉN ES EL MASTER. UN SOLO SITIO, PORQUE ES LA PUERTA DEL DINERO.

Por esta puerta pasan la tarifa MV, el coste, el margen, la rentabilidad, las
comisiones de los cooperativistas y el cierre del mes. Es el candado más caro
del ERP.

DOS COSAS SE ARREGLAN AQUÍ.

1. ESTABA ESCRITO CUATRO VECES. La misma tupla vivía copiada en
   `routes/cascos.py`, `routes/plan_negocio.py`, `routes/auth_routes.py` y
   `services/ai_usage.py`. Cuatro copias de una regla de permisos es una que se
   aprieta y tres que se quedan abiertas, y nadie lo nota hasta que alguien ve
   lo que no debía.

2. `isAdmin` YA NO ABRE ESTA PUERTA (master, 29/08). Administrar el ERP y ver
   lo que le cuesta a la casa cada mueble no son el mismo permiso, y el día que
   se le dé admin a quien lleve carpinter.io o Studio3K la diferencia se nota en
   euros.

   SE INTENTÓ EL 28/08 Y HUBO QUE REVERTIRLO EL MISMO DÍA. No porque la idea
   fuera mala: porque `isPrimaryAdmin` NO LLEGABA AL SERVIDOR —
   `get_current_user` reconstruía al usuario con trece campos del token y ese no
   estaba—, así que apretar era imposible por definición y el master se quedó
   sin su propia tarifa, con toda la relación a 0,00 €. Eso está arreglado
   (regla 25). Y por si acaso, ahora hay una VÁLVULA: ver `flags_en_vigor`.

SI TE QUEDAS FUERA: tu cuenta necesita `isPrimaryAdmin` o `isMaster`. Se marca
desde el panel Master, en Usuarios → «Admin principal».
"""
from __future__ import annotations

from typing import Optional

# QUIÉN ABRE LA PUERTA DEL DINERO. Ya sin `isAdmin` (master, 29/08).
#
# Administrar el ERP y ver lo que le cuesta a la casa cada mueble no son el
# mismo permiso: el día que se le dé `isAdmin` a quien lleve carpinter.io o
# Studio3K, la diferencia se nota en euros.
FLAGS_MASTER = ("isPrimaryAdmin", "isMaster")

# La lista ANCHA, la de antes. Ya no se usa para decidir: se usa para el rescate
# de abajo y para poder contar a quién afectó el cambio.
FLAGS_ANCHOS = ("isAdmin", "isPrimaryAdmin", "isMaster")

# Lo que este cambio le quita a quien solo era administrador.
FLAGS_QUE_SE_QUITAN = tuple(f for f in FLAGS_ANCHOS if f not in FLAGS_MASTER)


# ─── LA VÁLVULA: UN CANDADO NO PUEDE DEJAR LA CASA SIN DUEÑO ────────────────
#
# Esto MISMO se intentó el 28/08 y hubo que revertirlo con un despliegue el
# mismo día: la cuenta con la que trabaja el master es `isAdmin`, así que al
# apretar la lista se quedó fuera de su propia tarifa y TODA la relación de
# Cocina Montada 3 salió a 0,00 €. Un presupuesto a cero es lo peor que puede
# pasar aquí: no da error, se imprime igual y se puede enviar a un cliente.
#
# La causa de fondo ya está arreglada (`services/jwt_service.py`: hasta el 29/08
# `isPrimaryAdmin` NO LLEGABA SIQUIERA al servidor, así que apretar era
# imposible por definición). Aun así, apretar sin poder mirar la base de datos
# se apoya en que alguien se acordara de marcar la casilla — y un candado que se
# apoya en que nadie se equivoque no es un candado.
#
# Así que al arrancar se CUENTA. Si no hay NI UNA cuenta con `isPrimaryAdmin` o
# `isMaster`, el ERP se queda con la lista ancha y lo grita en el log, en vez de
# dejarse a sí mismo sin dueño. Se cierra solo en cuanto haya una cuenta
# marcada; hasta entonces, prefiere estar de más a estar de menos, porque el
# fallo por defecto aquí no es «alguien ve un precio que no debía»: es «la casa
# entera deja de poder presupuestar».
_rescate_activo = False


def activar_rescate(motivo: str = "") -> None:
    """Vuelve a la lista ancha porque no hay ningún master marcado."""
    global _rescate_activo
    _rescate_activo = True


def desactivar_rescate() -> None:
    global _rescate_activo
    _rescate_activo = False


def hay_rescate() -> bool:
    return _rescate_activo


def flags_en_vigor() -> tuple:
    """La lista con la que se está decidiendo AHORA MISMO."""
    return FLAGS_ANCHOS if _rescate_activo else FLAGS_MASTER


def es_master(user: Optional[dict]) -> bool:
    """Si esa persona puede ver el dinero de la casa y tocar la nómina."""
    return bool(user and any(user.get(f) for f in flags_en_vigor()))


async def comprobar_que_hay_master(db) -> dict:
    """Al arrancar: ¿queda alguien dentro? Si no, se abre la válvula.

    Devuelve el recuento, para que quede en el log de Railway y se pueda ver de
    un vistazo a quién afectó apretar la lista.
    """
    try:
        marcados = await db.users.count_documents(
            {"$or": [{f: True} for f in FLAGS_MASTER]})
        solo_admin = await db.users.count_documents(
            {"$and": [{"isAdmin": True}] + [{f: {"$ne": True}} for f in FLAGS_MASTER]})
    except Exception as e:                                   # noqa: BLE001
        # Si no se puede contar NO se aprieta: en la duda, la lista ancha. Un
        # Mongo lento al arrancar no puede dejar a la casa sin presupuestar.
        activar_rescate(f"no se pudo contar: {e}")
        return {"error": str(e), "rescate": True}
    if marcados == 0:
        activar_rescate("no hay ninguna cuenta con isPrimaryAdmin ni isMaster")
    else:
        desactivar_rescate()
    return {"conMarca": marcados, "soloAdmin": solo_admin, "rescate": hay_rescate()}
