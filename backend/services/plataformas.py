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

    OJO: esto dice en qué NEGOCIO está, no que sea socio. Ser de la cooperativa
    es condición necesaria y no suficiente: dentro de la cooperativa la mayoría
    de la gente tampoco cobra comisión (ver `SER_COOPERATIVISTA_SE_MARCA`).
    """
    return es_de_la_cooperativa(user)


# ── QUIÉN ES SOCIO COOPERATIVISTA ────────────────────────────────────────────
#
# El master, 27/08/2026, corrigiendo la primera versión de esto: «no todos son
# de la cooperativa. Comercial cooperativista sí, montador cooperativista
# también. Los demás son independientes. El rol de comisiones solamente es para
# estos dos».
#
# SER COOPERATIVISTA SE MARCA, NO SE DEDUCE. La primera versión sacaba el socio
# del rol genérico del ERP —`isMontador`, `isRepresentative`— y eso estaba mal
# por donde más duele: `isRepresentative` es el comercial de toda la vida de la
# casa (hay comerciales sembrados con ese flag en `scripts/seed_comerciales.py`)
# e `isMontador` es el de la agenda de montajes. Con aquello, TODOS ellos
# entraban en la liquidación cobrando comisión de cooperativista sin que nadie
# lo hubiera decidido.
#
# Son dos marcas y no una sola casilla «es cooperativista» porque el rol decide
# CÓMO se paga: el comercial cobra por tramos según la valoración del pedido y
# el montador cobra la mano de obra por mueble. No es la misma nómina.
SER_COOPERATIVISTA_SE_MARCA = ("esCooperativistaComercial",
                               "esCooperativistaMontador")


def es_cooperativista_montador(user: Optional[dict]) -> bool:
    return bool((user or {}).get("esCooperativistaMontador")) and puede_tener_comision(user)


def es_cooperativista_comercial(user: Optional[dict]) -> bool:
    return bool((user or {}).get("esCooperativistaComercial")) and puede_tener_comision(user)


def es_cooperativista(user: Optional[dict]) -> bool:
    """Socio de la cooperativa: uno de los dos roles, y de la cooperativa.

    Todo lo demás —gerencia, dirección comercial, tienda, fábrica, prescriptor,
    controller y el comercial o el montador en nómina— es independiente y no
    cobra comisión.
    """
    return es_cooperativista_montador(user) or es_cooperativista_comercial(user)
