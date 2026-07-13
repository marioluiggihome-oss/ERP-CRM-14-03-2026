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
    # Coste ESTIMADO: nº de llamadas por tipo × coste unitario configurable (€).
    cost_per = cfg.get("cost_per", {}) or {}
    est = 0.0
    for k, n in by_kind.items():
        est += (float(cost_per.get(k, 0) or 0)) * int(n or 0)
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
        "spend_url": cfg.get("spend_url", ""),
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
    if upd:
        await db.ai_usage_config.update_one({"_id": "cfg"}, {"$set": upd}, upsert=True)


# Compatibilidad: fija solo el umbral.
async def set_threshold(threshold: int):
    await set_config({"threshold": threshold})
