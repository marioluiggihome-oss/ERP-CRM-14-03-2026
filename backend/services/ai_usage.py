"""Contador de consumo de IA.

Registra CADA llamada al motor de IA (render, visión, texto, chat, búsqueda) en un
único punto (el servicio central llm_vision) e incrementa un contador mensual en
Mongo. El master puede consultarlo y fijar un umbral de alerta por exceso de uso.

Diseño defensivo: si algo falla al contar, NUNCA debe romper la llamada de IA.
"""
from datetime import datetime, timezone

try:
    from config import db  # instancia global de la base de datos
except Exception:  # pragma: no cover
    db = None


def _month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


# ─── Tarifas de referencia (EUR) para el cálculo de coste ────────────────────
# €/1M tokens de entrada y salida, y €/imagen para los modelos de imagen.
# Precios de lista (Nivel de pago) aproximados; ajustables por el master.
MODEL_PRICES = {
    "gemini-2.5-flash":              {"in": 0.28, "out": 2.30, "img": 0.0},
    "gemini-flash-latest":           {"in": 0.28, "out": 2.30, "img": 0.0},
    "gemini-3-flash-preview":        {"in": 0.28, "out": 2.30, "img": 0.0},
    "gemini-2.5-pro":                {"in": 1.15, "out": 9.25, "img": 0.0},
    "gemini-2.5-flash-image":        {"in": 0.28, "out": 2.30, "img": 0.036},
    "gemini-2.5-flash-image-preview":{"in": 0.28, "out": 2.30, "img": 0.036},
    "gemini-3-pro-image-preview":    {"in": 2.00, "out": 12.0, "img": 0.12},
}
# Coste estimado por TIPO de llamada cuando no se miden tokens reales.
DEFAULT_COST_PER = {"render": 0.12, "vision": 0.003, "otro": 0.003}


def cost_of(model: str, in_tokens: int = 0, out_tokens: int = 0, images: int = 0) -> float:
    """Coste (EUR) exacto de una llamada a partir de tokens reales y/o nº de imágenes."""
    p = MODEL_PRICES.get(model or "", MODEL_PRICES["gemini-2.5-flash"])
    return round(
        (int(in_tokens or 0) / 1_000_000) * p["in"]
        + (int(out_tokens or 0) / 1_000_000) * p["out"]
        + int(images or 0) * p["img"],
        6,
    )


async def record_ai_tokens(kind: str, model: str, in_tokens: int = 0, out_tokens: int = 0,
                           images: int = 0, user_id: str = None, count: bool = True):
    """Registra el consumo REAL de una llamada: tokens por modelo y coste exacto
    acumulado del mes. Best-effort (nunca rompe la llamada de IA).

    count=True suma también 1 al total y a by_kind (llamada nueva). Usar count=False
    cuando la llamada YA se contó con record_ai_usage() y solo queremos añadir el
    coste/tokens (evita el doble conteo)."""
    if db is None:
        return
    try:
        eur = cost_of(model, in_tokens, out_tokens, images)
        mdl = (model or "otro").replace(".", "_")
        inc = {
            f"tokens_in.{mdl}": int(in_tokens or 0),
            f"tokens_out.{mdl}": int(out_tokens or 0),
            f"images.{mdl}": int(images or 0),
            f"calls.{mdl}": 1,
            "real_cost": eur,
        }
        if count:
            inc["total"] = 1
            inc[f"by_kind.{kind or 'otro'}"] = 1
            if user_id:
                inc[f"by_user.{user_id}"] = 1
        await db.ai_usage.update_one(
            {"month": _month()},
            {"$inc": inc, "$setOnInsert": {"month": _month()}},
            upsert=True,
        )
    except Exception:
        pass


def usage_from_response(resp):
    """Extrae (in_tokens, out_tokens) de la respuesta de google-genai. Best-effort."""
    um = getattr(resp, "usage_metadata", None)
    if not um:
        return 0, 0
    return int(getattr(um, "prompt_token_count", 0) or 0), int(getattr(um, "candidates_token_count", 0) or 0)


async def record_ai_usage(kind: str, user_id: str = None):
    """Suma 1 al contador del mes en curso (total y por tipo). Best-effort."""
    if db is None:
        return
    try:
        inc = {"total": 1, f"by_kind.{kind or 'otro'}": 1}
        if user_id:
            inc[f"by_user.{user_id}"] = 1
        await db.ai_usage.update_one(
            {"month": _month()},
            {"$inc": inc, "$setOnInsert": {"month": _month()}},
            upsert=True,
        )
    except Exception:
        pass  # el contador nunca bloquea una llamada de IA


async def get_usage_summary():
    """Resumen del mes en curso + histórico (6 meses) + umbral, coste estimado y alerta."""
    if db is None:
        return {"total": 0, "by_kind": {}, "threshold": 0, "over": False, "pct": 0, "history": [], "cost": {}}
    month = _month()
    cur = await db.ai_usage.find_one({"month": month}) or {"month": month, "total": 0, "by_kind": {}}
    cfg = await db.ai_usage_config.find_one({"_id": "cfg"}) or {}
    threshold = int(cfg.get("threshold", 0) or 0)
    total = int(cur.get("total", 0) or 0)
    by_kind = cur.get("by_kind", {})
    # Coste ESTIMADO: nº de llamadas por tipo × coste unitario (€). Si el master no
    # ha configurado tarifas, se usan los valores por defecto precargados.
    cost_per = cfg.get("cost_per") or DEFAULT_COST_PER
    est = 0.0
    for k, n in by_kind.items():
        est += (float(cost_per.get(k, 0) or 0)) * int(n or 0)
    # Coste REAL acumulado del mes (medido con los tokens reales de cada llamada).
    real_cost = round(float(cur.get("real_cost", 0) or 0), 4)
    history = await db.ai_usage.find({}, {"_id": 0, "by_user": 0}).sort("month", -1).to_list(6)
    return {
        "current_month": month,
        "total": total,
        "by_kind": by_kind,
        "threshold": threshold,
        "over": threshold > 0 and total >= threshold,
        "warn": threshold > 0 and total >= threshold * 0.8,
        "pct": round(total / threshold * 100, 1) if threshold else 0,
        "history": history,
        "cost_per": cost_per,
        "estimated_cost": round(est, 2),
        "real_cost": real_cost,
        "by_model": {
            "calls": cur.get("calls", {}),
            "tokens_in": cur.get("tokens_in", {}),
            "tokens_out": cur.get("tokens_out", {}),
            "images": cur.get("images", {}),
        },
        "spend_url": cfg.get("spend_url", ""),
        "default_credits": int(cfg.get("default_credits", 0) or 0),
        "credits_per": cfg.get("credits_per", {"render": 1, "vision": 0}) or {"render": 1, "vision": 0},
    }


async def set_config(payload: dict):
    """Fija umbral, coste por tipo (€) y URL del panel del proveedor."""
    if db is None:
        return
    p = payload or {}
    upd = {}
    if "threshold" in p:
        upd["threshold"] = int(p.get("threshold", 0) or 0)
    if "cost_per" in p and isinstance(p["cost_per"], dict):
        upd["cost_per"] = {k: float(v or 0) for k, v in p["cost_per"].items()}
    if "spend_url" in p:
        upd["spend_url"] = str(p.get("spend_url") or "")
    if "default_credits" in p:
        upd["default_credits"] = int(p.get("default_credits", 0) or 0)
    if "credits_per" in p and isinstance(p["credits_per"], dict):
        upd["credits_per"] = {k: int(v or 0) for k, v in p["credits_per"].items()}
    if upd:
        await db.ai_usage_config.update_one({"_id": "cfg"}, {"$set": upd}, upsert=True)


# Compatibilidad: fija solo el umbral.
async def set_threshold(threshold: int):
    await set_config({"threshold": threshold})


# ─── CRÉDITOS DE IA POR USUARIO (ligados a la suscripción) ───────────────────
# Roles con acceso ILIMITADO (nunca se les descuentan créditos).
_UNLIMITED_FLAGS = ("isAdmin", "isPrimaryAdmin", "isGerente", "isDirectorComercial", "isMaster")


def _is_unlimited(user: dict) -> bool:
    """Admin/master (y roles equivalentes) tienen créditos ILIMITADOS."""
    if not user:
        return False
    return any(user.get(f) for f in _UNLIMITED_FLAGS)


async def _get_credits_config():
    cfg = await db.ai_usage_config.find_one({"_id": "cfg"}) or {}
    default_credits = int(cfg.get("default_credits", 0) or 0)
    credits_per = cfg.get("credits_per", {}) or {}
    # Valores por defecto: render cuesta 1 crédito, visión 0.
    if "render" not in credits_per:
        credits_per["render"] = 1
    if "vision" not in credits_per:
        credits_per["vision"] = 0
    return default_credits, credits_per


async def get_user_credits(user: dict) -> dict:
    """Estado de créditos del usuario en el mes en curso.

    Devuelve {asignados, consumidos_mes, restantes, ilimitado}.
    Admin/master → ilimitado=True. Si el campo del usuario `aiCreditsMonthly`
    está a 0/vacío, se usa el default global `ai_usage_config.default_credits`.
    """
    if db is None:
        return {"asignados": 0, "consumidos_mes": 0, "restantes": 0, "ilimitado": True}
    if _is_unlimited(user):
        return {"asignados": 0, "consumidos_mes": 0, "restantes": 0, "ilimitado": True}

    default_credits, _ = await _get_credits_config()
    try:
        assigned = int(user.get("aiCreditsMonthly", 0) or 0)
    except (TypeError, ValueError):
        assigned = 0
    if assigned <= 0:
        assigned = default_credits

    uid = user.get("id") or user.get("_id") or ""
    consumed = 0
    extra = 0
    try:
        doc = await db.ai_credits.find_one({"user_id": str(uid), "month": _month()})
        consumed = int((doc or {}).get("consumed", 0) or 0)
        # Creditos extra comprados (packs de renders) para el mes en curso.
        extra = int((doc or {}).get("extra", 0) or 0)
    except Exception:
        consumed = 0

    total = assigned + extra
    remaining = max(total - consumed, 0)
    return {
        "asignados": assigned,
        "extra": extra,
        "total": total,
        "consumidos_mes": consumed,
        "restantes": remaining,
        "ilimitado": False,
    }


async def consume_credits(user: dict, kind: str) -> dict:
    """Descuenta el coste (en créditos) de una llamada de tipo `kind` para el
    usuario y lo registra en la colección `ai_credits` por (user_id, month).

    Admin/master no consumen. Devuelve el estado de créditos actualizado.
    Best-effort: si algo falla, no lanza (el enforcement decide si bloquea).
    """
    if db is None or _is_unlimited(user):
        return await get_user_credits(user)

    _, credits_per = await _get_credits_config()
    try:
        cost = int(credits_per.get(kind, 0) or 0)
    except (TypeError, ValueError):
        cost = 0

    if cost > 0:
        uid = user.get("id") or user.get("_id") or ""
        try:
            await db.ai_credits.update_one(
                {"user_id": str(uid), "month": _month()},
                {"$inc": {"consumed": cost},
                 "$setOnInsert": {"user_id": str(uid), "month": _month()}},
                upsert=True,
            )
        except Exception:
            pass  # no bloquear por un fallo del contador
    return await get_user_credits(user)
