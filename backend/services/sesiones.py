# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CERRAR SESIONES DE VERDAD.

EL PROBLEMA
-----------
El ERP entra con un JWT firmado, válido 24 horas. `require_auth` comprueba la
FIRMA y la CADUCIDAD, y nada más. Existe una colección `active_sessions`, pero
solo se lee AL ENTRAR, para impedir que un usuario no administrador tenga dos
sesiones a la vez.

O sea que vaciar `active_sessions` —que es lo que hace `/auth/logout`— NO echa a
nadie: su token sigue siendo válido hasta 24 horas después. Quien ya está
dentro, sigue dentro. Hasta ahora la única forma real de echar a todo el mundo
era cambiar `JWT_SECRET` en Railway y reiniciar, que es un mazazo: obliga a un
redespliegue y no distingue entre un usuario y todos.

CÓMO SE CIERRA DE VERDAD
------------------------
Cada token lleva `iat` (el instante en que se emitió). Se guarda una fecha de
corte y se rechaza todo token emitido ANTES:

    · corte GENERAL      -> echa a todo el mundo.
    · corte POR USUARIO  -> echa solo a ese.

El que vuelve a entrar recibe un token nuevo, con `iat` posterior al corte, y
entra sin problema. No hace falta reiniciar nada ni tocar `JWT_SECRET`.

POR QUÉ CON CACHÉ
-----------------
Esto se consulta en CADA petición autenticada. Sin caché serían dos lecturas a
Mongo por petición, y `require_auth` hoy no hace ninguna. Se guarda en memoria
unos segundos: el retraso máximo entre pulsar «cerrar sesiones» y que empiecen a
rebotar es ese, y a cambio el coste por petición es cero casi siempre.

Y SI LA BASE DE DATOS NO CONTESTA
---------------------------------
Se deja pasar. Esto es una revocación, no la autenticación: la firma y la
caducidad del token ya se han comprobado antes. Tumbar el ERP entero —dejar a
todo el mundo fuera— porque no se puede leer una fecha de corte sería un
remedio peor que la enfermedad.
"""
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

DOC_ID = "sesiones"
COLECCION = "seguridad"
SEGUNDOS_CACHE = 10.0
SEGUNDOS_CACHE_FALLO = 5.0   # si la base no contesta, no se reintenta en cada petición

_cache: Dict[str, Any] = {"cuando": 0.0, "datos": None}


def _ahora() -> float:
    return datetime.now(timezone.utc).timestamp()


def _a_epoch(valor) -> Optional[float]:
    """Acepta lo que haya guardado: número, ISO o datetime."""
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, datetime):
        dt = valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    try:
        texto = str(valor).replace("Z", "+00:00")
        dt = datetime.fromisoformat(texto)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (TypeError, ValueError):
        return None


def invalidar_cache() -> None:
    """Tras cerrar sesiones, que el corte valga YA y no dentro de 10 segundos."""
    _cache["cuando"] = 0.0
    _cache["datos"] = None


async def _cortes() -> Dict[str, Any]:
    if _cache["datos"] is not None and (time.monotonic() - _cache["cuando"]) < SEGUNDOS_CACHE:
        return _cache["datos"]
    datos = {"general": None, "usuarios": {}}
    try:
        from services.db_client import get_db
        doc = await get_db()[COLECCION].find_one({"_id": DOC_ID})
        if doc:
            datos = {
                "general": _a_epoch(doc.get("general")),
                "usuarios": {k: _a_epoch(v) for k, v in (doc.get("usuarios") or {}).items()},
            }
    except Exception as e:      # noqa: BLE001 — ver cabecera: esto no puede echar a nadie
        # EL FALLO TAMBIÉN SE CACHEA, y aquí está el motivo: cuando Mongo no
        # contesta, cada intento se come el tiempo de espera entero (5 s). Sin
        # guardar el fallo, CADA petición del ERP pagaría esos 5 s y la
        # aplicación se arrastraría — un problema mucho más gordo que el que se
        # estaba resolviendo. Se guarda menos tiempo que un acierto para que se
        # recupere pronto en cuanto la base vuelva.
        logger.warning("No se pudo leer el corte de sesiones (%s). Se deja pasar.", e)
        _cache["datos"] = datos
        _cache["cuando"] = time.monotonic() - (SEGUNDOS_CACHE - SEGUNDOS_CACHE_FALLO)
        return datos
    _cache["datos"] = datos
    _cache["cuando"] = time.monotonic()
    return datos


async def token_revocado(payload: Dict[str, Any]) -> bool:
    """¿Este token se emitió ANTES del último cierre de sesiones?"""
    emitido = _a_epoch(payload.get("iat"))
    if emitido is None:
        # Un token sin `iat` es de antes de que esto existiera: se cierra, que
        # es justo lo que se quiere al echar a todo el mundo.
        cortes = await _cortes()
        return bool(cortes.get("general"))
    cortes = await _cortes()
    general = cortes.get("general")
    if general and emitido < general:
        return True
    uid = payload.get("sub")
    propio = (cortes.get("usuarios") or {}).get(uid) if uid else None
    return bool(propio and emitido < propio)


async def cerrar_todas(motivo: str = "") -> float:
    """Echa a TODO EL MUNDO. Devuelve el instante de corte."""
    corte = _ahora()
    from services.db_client import get_db
    db = get_db()
    await db[COLECCION].update_one(
        {"_id": DOC_ID},
        {"$set": {"general": corte, "motivo": motivo,
                  "cuando": datetime.now(timezone.utc).isoformat()}},
        upsert=True)
    # `active_sessions` solo se mira al entrar (sesión única). Se vacía también
    # para que nadie se quede con una sesión fantasma que le impida volver.
    try:
        await db.active_sessions.delete_many({})
    except Exception as e:      # noqa: BLE001
        logger.warning("Sesiones cerradas, pero no se pudo limpiar active_sessions: %s", e)
    invalidar_cache()
    logger.warning("SESIONES CERRADAS para TODOS los usuarios. Motivo: %s", motivo or "(sin indicar)")
    return corte


async def cerrar_de(user_id: str, motivo: str = "") -> float:
    """Echa a UN usuario. Devuelve el instante de corte."""
    if not user_id:
        raise ValueError("Falta el usuario")
    corte = _ahora()
    from services.db_client import get_db
    db = get_db()
    await db[COLECCION].update_one(
        {"_id": DOC_ID},
        {"$set": {f"usuarios.{user_id}": corte}},
        upsert=True)
    try:
        await db.active_sessions.delete_many({"user_id": user_id})
    except Exception as e:      # noqa: BLE001
        logger.warning("Sesión de %s cerrada, pero no se limpió active_sessions: %s", user_id, e)
    invalidar_cache()
    logger.warning("SESIÓN CERRADA para el usuario %s. Motivo: %s", user_id, motivo or "(sin indicar)")
    return corte
