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
    """Devuelve la plataforma efectiva, incluyendo cuentas heredadas.

    Los vínculos históricos de CARPINTER.IO y STUDIO3K.IO se respetan aunque la
    ficha todavía no tenga el campo ``plataforma``. Solo una cuenta sin ninguna
    señal de negocio se considera de la plataforma histórica.
    """
    data = user or {}
    v = str(data.get("plataforma") or "").strip().lower()
    if v in TODAS:
        return v
    if data.get("isStudio3k") or data.get("linkedStudio3kAdminId") or data.get("canManageStudio3kUsers"):
        return STUDIO3K
    if data.get("isCarpintero") or data.get("linkedCarpinteroAdminId") or data.get("canManageCarpinteroUsers"):
        return CARPINTER
    return COOPERATIVA


def organizacion_de(user: Optional[dict]) -> str:
    """Devuelve el tenant efectivo dentro de una plataforma comercial.

    La marca (CARPINTER.IO o STUDIO3K.IO) no basta para aislar clientes: cada
    administrador delegado representa una organización independiente. Las cuentas
    heredadas se resuelven por su vínculo histórico; un administrador raíz o una
    cuenta comercial sin vínculo usa su propio id.
    """
    data = user or {}
    explicit = str(data.get("organizationId") or "").strip()
    if explicit:
        return explicit
    plataforma = plataforma_de(data)
    if plataforma == STUDIO3K:
        linked = str(data.get("linkedStudio3kAdminId") or "").strip()
        return linked or str(data.get("id") or "").strip()
    if plataforma == CARPINTER:
        linked = str(data.get("linkedCarpinteroAdminId") or "").strip()
        return linked or str(data.get("id") or "").strip()
    return COOPERATIVA


def normalizar_usuario_plataforma(data: Optional[dict], previous: Optional[dict] = None) -> dict:
    """Campos canónicos de marca/organización para crear o actualizar usuarios.

    El resultado se puede aplicar directamente con ``$set``. Si se cambia una
    cuenta de marca se limpian los flags y vínculos incompatibles, evitando que
    una misma ficha pertenezca simultáneamente a las dos plataformas.
    """
    incoming = dict(data or {})
    merged = {**(previous or {}), **incoming}
    plataforma = plataforma_de(merged)
    result = {"plataforma": plataforma}

    if plataforma == CARPINTER:
        result.update({
            "isCarpintero": True,
            "isStudio3k": False,
            "linkedStudio3kAdminId": None,
        })
    elif plataforma == STUDIO3K:
        result.update({
            "isStudio3k": True,
            "isCarpintero": False,
            "linkedCarpinteroAdminId": None,
        })
    else:
        result.update({
            "isCarpintero": False,
            "isStudio3k": False,
            "linkedCarpinteroAdminId": None,
            "linkedStudio3kAdminId": None,
        })

    normalized = {**merged, **result}
    result["organizationId"] = organizacion_de(normalized)
    return result


def es_de_la_cooperativa(user: Optional[dict]) -> bool:
    return plataforma_de(user) == COOPERATIVA


def plataforma_entrada(value: Optional[str]) -> str:
    """Normaliza la plataforma declarada por el acceso público.

    Una entrada desconocida se conserva vacía para que nunca pueda autorizar por
    accidente una cuenta de suscripción.
    """
    v = str(value or "").strip().lower()
    aliases = {
        "carpinteros": CARPINTER,
        "carpenter": CARPINTER,
        "s3k": STUDIO3K,
        "estudio3k": STUDIO3K,
    }
    v = aliases.get(v, v)
    return v if v in SOLO_SUSCRIPCIONES else ""


def suscripcion_permitida(user: Optional[dict]) -> bool:
    """Vigencia comercial server-side para cuentas de suscripción.

    Las cuentas heredadas sin ``subscriptionStatus`` siguen funcionando durante
    la migración. Solo los estados explícitamente bloqueados o una fecha vencida
    cierran el acceso. MASTER conserva soporte global.
    """
    from datetime import datetime, timezone
    from services.master import es_master

    if es_master(user):
        return True
    data = user or {}
    if plataforma_de(data) not in SOLO_SUSCRIPCIONES:
        return True
    status = str(data.get("subscriptionStatus") or "").strip().lower()
    if status in {"suspended", "cancelled", "expired", "inactive"}:
        return False
    expiration = data.get("accessExpirationDate")
    if not expiration:
        return True
    try:
        value = datetime.fromisoformat(str(expiration).replace("Z", "+00:00"))
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.date() >= datetime.now(timezone.utc).date()
    except (TypeError, ValueError):
        return False


def entrada_permitida(user: Optional[dict], entry: Optional[str]) -> bool:
    """Comprueba que una cuenta comercial entra desde su marca asignada.

    MASTER conserva acceso global para soporte y administración. Los usuarios de
    la plataforma histórica no quedan bloqueados por esta regla.
    """
    from services.master import es_master

    if es_master(user):
        return True
    plataforma = plataforma_de(user)
    if plataforma not in SOLO_SUSCRIPCIONES:
        return True
    return plataforma_entrada(entry) == plataforma


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
