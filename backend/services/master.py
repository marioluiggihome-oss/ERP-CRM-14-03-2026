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

2. `isAdmin` YA NO ABRE ESTA PUERTA (master, 28/08). Estaba dentro, así que
   CUALQUIER administrador veía la tarifa del proveedor, el margen de la casa y
   la nómina de los cooperativistas — y con el botón COOP, además, podía decidir
   quién cobra y cerrar el mes. «Administrar el ERP» y «ver lo que le cuesta a
   la casa cada mueble» no son el mismo permiso, y el día que se le dé admin a
   quien lleve carpinter.io o Studio3K, la diferencia se nota en euros.

SI TE QUEDAS FUERA. Tu cuenta necesita `isPrimaryAdmin` o `isMaster`. La cuenta
`admin` ya lo lleva (`scripts/sync_admin_permissions.py` lo pone), pero si algún
día un usuario tuyo pierde el acceso a Rentabilidad o a COOP, es esto: hay que
marcarle uno de los dos, no `isAdmin`.
"""
from __future__ import annotations

from typing import Optional

# Los dos únicos que abren la puerta del dinero. `isAdmin` NO está, y no es un
# olvido: ver el ERP no es ver lo que gana la casa.
FLAGS_MASTER = ("isPrimaryAdmin", "isMaster")

# Lo que era antes. Se deja escrito para que quede claro qué se quitó y cuándo,
# y para que el candado pueda comprobar que `isAdmin` sigue fuera.
FLAGS_ANTIGUOS = ("isAdmin", "isPrimaryAdmin", "isMaster")


def es_master(user: Optional[dict]) -> bool:
    """Si esa persona puede ver el dinero de la casa y tocar la nómina."""
    return bool(user and any(user.get(f) for f in FLAGS_MASTER))
