# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
TRES PLATAFORMAS EN EL MISMO ERP, Y SOLO UNA TIENE COOPERATIVISTAS.

El master, 25/08/2026: «la red de carpinter.io y la red de Studio3K son solo
para vender suscripciones a usuarios que pagan esas suscripciones de los
servicios establecidos y autorizados por el master. No tienen nada que ver con
el negocio de los cooperativistas: son plataformas independientes, aunque las
tengamos metidas en la misma gestión del ERP de momento».

    cooperativa   El negocio de verdad: cocinas, fabricación, montaje. Aquí
                  —y SOLO aquí— hay montadores y comerciales cooperativistas
                  que cobran comisión.
    carpinter     carpinter.io. Suscriptores que pagan por servicios.
    studio3k      Studio3K.io. Igual.

POR QUÉ ESTO ES UN CANDADO Y NO UNA ETIQUETA. Las tres comparten la colección de
usuarios «de momento», y ese «de momento» es el peligro: basta con que alguien
marque a un suscriptor de carpinter.io como «comercial» —un clic en la pantalla
de permisos— para que empiece a aparecer cobrando comisiones de la cooperativa.
No haría falta mala fe: los dos negocios usan la misma palabra para cosas
distintas.

Por eso la plataforma se comprueba ANTES que el rol. Ser comercial no basta: hay
que ser comercial DE LA COOPERATIVA.

EL DEFECTO ES `cooperativa` a propósito. Todos los usuarios que ya existen son
del negocio de siempre, y ninguno tiene este campo todavía. Si el defecto fuera
otro, el día del despliegue los cooperativistas de verdad se quedarían sin su
área sin que nadie hubiera cambiado nada.
"""
from __future__ import annotations

from typing import Optional

COOPERATIVA = "cooperativa"
CARPINTER = "carpinter"
STUDIO3K = "studio3k"

TODAS = (COOPERATIVA, CARPINTER, STUDIO3K)

# Las que venden suscripciones. Ni comisiones, ni cooperativistas, ni nómina.
SOLO_SUSCRIPCIONES = (CARPINTER, STUDIO3K)

NOMBRES = {
    COOPERATIVA: "Red de distribución",
    CARPINTER: "carpinter.io",
    STUDIO3K: "Studio3K.io",
}


def plataforma_de(user: Optional[dict]) -> str:
    """A qué plataforma pertenece un usuario. Por defecto, la cooperativa.

    Un valor que no se reconozca se trata como cooperativa y no se inventa una
    plataforma nueva: es mejor que un usuario mal etiquetado siga en el negocio
    de siempre —donde alguien lo verá— que mandarlo a un limbo donde no aparece
    en ninguna lista.
    """
    v = str((user or {}).get("plataforma") or "").strip().lower()
    return v if v in TODAS else COOPERATIVA


def es_de_la_cooperativa(user: Optional[dict]) -> bool:
    return plataforma_de(user) == COOPERATIVA


def puede_tener_comision(user: Optional[dict]) -> bool:
    """Solo la cooperativa reparte comisiones.

    Se llama antes que cualquier comprobación de rol. Un suscriptor de
    carpinter.io marcado como «comercial» sigue siendo un suscriptor.
    """
    return es_de_la_cooperativa(user)
