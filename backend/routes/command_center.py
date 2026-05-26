"""
Panel de Mando - LUIGGI HOME
Centro de control con KPIs, actividad de usuarios y métricas de negocio
"""
from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/command-center", tags=["CommandCenter"])

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


def now_utc(): return datetime.now(timezone.utc)
def days_ago(n): return now_utc() - timedelta(days=n)


@router.get("/overview")
async def get_overview():
    """KPIs principales del negocio"""
    today = now_utc().replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
    prev_month_end = month_start

    # ── Presupuestos ──────────────────────────────────────────────────────
    total_projects = await db.projects.count_documents({})
    month_projects = await db.projects.count_documents({"createdAt": {"$gte": month_start.isoformat()}})
    prev_month_projects = await db.projects.count_documents({
        "createdAt": {"$gte": prev_month_start.isoformat(), "$lt": prev_month_end.isoformat()}
    })

    # Proyectos por estado
    pipeline_status = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}, "total": {"$sum": "$totalPvp"}}}
    ]
    status_results = await db.projects.aggregate(pipeline_status).to_list(20)
    status_map = {r["_id"]: {"count": r["count"], "total": r["total"]} for r in status_results}

    # ── Facturación ───────────────────────────────────────────────────────
    inv_pipeline = [
        {"$match": {"status": {"$in": ["issued", "paid"]}}},
        {"$group": {
            "_id": None,
            "totalFacturado": {"$sum": "$total"},
            "totalPagado": {"$sum": {"$cond": [{"$eq": ["$status", "paid"]}, "$total", 0]}},
            "pendienteCobro": {"$sum": {"$cond": [{"$eq": ["$status", "issued"]}, "$total", 0]}},
        }}
    ]
    inv_result = await db.invoices.aggregate(inv_pipeline).to_list(1)
    inv_data = inv_result[0] if inv_result else {}

    inv_month = [
        {"$match": {"status": {"$in": ["issued","paid"]}, "createdAt": {"$gte": month_start.isoformat()}}},
        {"$group": {"_id": None, "total": {"$sum": "$total"}}}
    ]
    inv_month_result = await db.invoices.aggregate(inv_month).to_list(1)
    inv_month_total = inv_month_result[0]["total"] if inv_month_result else 0

    inv_overdue = await db.invoices.count_documents({
        "status": "issued",
        "dueDate": {"$lt": today.date().isoformat()}
    })

    # ── CRM ───────────────────────────────────────────────────────────────
    total_contacts = await db.contacts.count_documents({})
    month_contacts = await db.contacts.count_documents({"createdAt": {"$gte": month_start.isoformat()}})
    total_opps = await db.opportunities.count_documents({})
    active_opps = await db.opportunities.count_documents({"stage": {"$nin": ["won", "lost"]}})
    won_month = await db.opportunities.count_documents({
        "stage": "won",
        "updatedAt": {"$gte": month_start.isoformat()}
    })

    opp_value_pipeline = [
        {"$match": {"stage": {"$nin": ["won", "lost"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$value"}}}
    ]
    opp_value = await db.opportunities.aggregate(opp_value_pipeline).to_list(1)
    pipeline_value = opp_value[0]["total"] if opp_value else 0

    # ── Pedidos/Fábrica ───────────────────────────────────────────────────
    total_orders = await db.fabrica_orders.count_documents({})
    month_orders = await db.fabrica_orders.count_documents({"createdAt": {"$gte": month_start.isoformat()}})
    pending_orders = await db.fabrica_orders.count_documents({"status": {"$in": ["pending", "in_progress"]}})

    # ── Usuarios activos ──────────────────────────────────────────────────
    active_users_today = await db.user_activity.distinct("userId", {
        "timestamp": {"$gte": today}
    })
    active_users_week = await db.user_activity.distinct("userId", {
        "timestamp": {"$gte": week_start}
    })
    active_users_month = await db.user_activity.distinct("userId", {
        "timestamp": {"$gte": month_start}
    })

    # ── Evolución mensual (últimos 6 meses) ───────────────────────────────
    monthly_evolution = []
    for i in range(5, -1, -1):
        m_start = (now_utc().replace(day=1) - timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0)
        m_end = (m_start + timedelta(days=32)).replace(day=1)
        count = await db.projects.count_documents({
            "createdAt": {"$gte": m_start.isoformat(), "$lt": m_end.isoformat()}
        })
        inv_m = await db.invoices.aggregate([
            {"$match": {"createdAt": {"$gte": m_start.isoformat(), "$lt": m_end.isoformat()}, "status": {"$in": ["issued","paid"]}}},
            {"$group": {"_id": None, "total": {"$sum": "$total"}}}
        ]).to_list(1)
        monthly_evolution.append({
            "month": m_start.strftime("%b %Y"),
            "presupuestos": count,
            "facturado": inv_m[0]["total"] if inv_m else 0
        })

    return {
        "presupuestos": {
            "total": total_projects,
            "esteMes": month_projects,
            "mesPasado": prev_month_projects,
            "variacion": round((month_projects - prev_month_projects) / max(prev_month_projects, 1) * 100, 1),
            "porEstado": status_map,
        },
        "facturacion": {
            "totalFacturado": round(inv_data.get("totalFacturado", 0), 2),
            "totalPagado": round(inv_data.get("totalPagado", 0), 2),
            "pendienteCobro": round(inv_data.get("pendienteCobro", 0), 2),
            "esteMes": round(inv_month_total, 2),
            "facturasVencidas": inv_overdue,
        },
        "crm": {
            "totalContactos": total_contacts,
            "contactosMes": month_contacts,
            "totalOportunidades": total_opps,
            "oportunidadesActivas": active_opps,
            "ganadas_mes": won_month,
            "valorPipeline": round(pipeline_value, 2),
        },
        "fabrica": {
            "totalPedidos": total_orders,
            "pedidosMes": month_orders,
            "pendientes": pending_orders,
        },
        "usuarios": {
            "activosHoy": len(active_users_today),
            "activosSemana": len(active_users_week),
            "activosMes": len(active_users_month),
        },
        "evolucion": monthly_evolution,
        "generadoEn": now_utc().isoformat(),
    }


@router.get("/users-activity")
async def get_users_activity(days: int = 30):
    """Actividad detallada por usuario"""
    start = days_ago(days)

    pipeline = [
        {"$match": {"timestamp": {"$gte": start}}},
        {"$group": {
            "_id": "$userId",
            "username": {"$last": "$username"},
            "totalAcciones": {"$sum": 1},
            "logins": {"$sum": {"$cond": [{"$eq": ["$activityType", "login"]}, 1, 0]}},
            "presupuestosCreados": {"$sum": {"$cond": [{"$eq": ["$activityType", "budget_create"]}, 1, 0]}},
            "presupuestosEditados": {"$sum": {"$cond": [{"$eq": ["$activityType", "budget_update"]}, 1, 0]}},
            "pedidosCreados": {"$sum": {"$cond": [{"$eq": ["$activityType", "order_create"]}, 1, 0]}},
            "pedidosConfirmados": {"$sum": {"$cond": [{"$eq": ["$activityType", "order_confirm"]}, 1, 0]}},
            "pdfsGenerados": {"$sum": {"$cond": [{"$eq": ["$activityType", "budget_export_pdf"]}, 1, 0]}},
            "usoIA": {"$sum": {"$cond": [{"$eq": ["$activityType", "ai_telemetry"]}, 1, 0]}},
            "ultimaActividad": {"$max": "$timestamp"},
            "primeraActividad": {"$min": "$timestamp"},
        }},
        {"$sort": {"totalAcciones": -1}}
    ]

    results = await db.user_activity.aggregate(pipeline).to_list(100)

    # Enriquecer con datos del usuario (rol, email)
    for r in results:
        user = await db.users.find_one({"id": r["_id"]}, {"_id": 0, "email": 1, "isAdmin": 1, "isGerente": 1, "isRepresentative": 1, "isTienda": 1, "clientName": 1})
        if user:
            r["email"] = user.get("email", "")
            r["clientName"] = user.get("clientName", "")
            r["rol"] = (
                "Admin" if user.get("isAdmin") else
                "Gerente" if user.get("isGerente") else
                "Comercial" if user.get("isRepresentative") else
                "Tienda" if user.get("isTienda") else "Usuario"
            )
        r["_id"] = str(r["_id"])
        if r.get("ultimaActividad"):
            r["ultimaActividad"] = r["ultimaActividad"].isoformat() if hasattr(r["ultimaActividad"], "isoformat") else r["ultimaActividad"]
        if r.get("primeraActividad"):
            r["primeraActividad"] = r["primeraActividad"].isoformat() if hasattr(r["primeraActividad"], "isoformat") else r["primeraActividad"]

    return {"usuarios": results, "dias": days, "total": len(results)}


@router.get("/activity-timeline")
async def get_activity_timeline(days: int = 7, limit: int = 100):
    """Timeline de últimas acciones"""
    start = days_ago(days)
    LABELS = {
        "login": "Inicio sesión", "logout": "Cierre sesión",
        "budget_create": "Presupuesto creado", "budget_update": "Presupuesto editado",
        "budget_export_pdf": "PDF generado", "order_create": "Pedido creado",
        "order_confirm": "Pedido confirmado", "ai_telemetry": "Uso IA",
        "report_generate": "Informe generado", "settings_update": "Configuración cambiada",
    }
    cursor = db.user_activity.find(
        {"timestamp": {"$gte": start}}, {"_id": 0}
    ).sort("timestamp", -1).limit(limit)
    results = await cursor.to_list(limit)
    for r in results:
        if hasattr(r.get("timestamp"), "isoformat"):
            r["timestamp"] = r["timestamp"].isoformat()
        r["label"] = LABELS.get(r.get("activityType", ""), r.get("activityType", ""))
    return {"actividades": results}


@router.get("/performance/users")
async def get_user_performance(days: int = 30):
    """Ranking de rendimiento de comerciales"""
    start = days_ago(days)

    # Presupuestos por usuario
    proj_pipeline = [
        {"$match": {"createdAt": {"$gte": start.isoformat()}}},
        {"$group": {
            "_id": "$userId",
            "presupuestos": {"$sum": 1},
            "totalPvp": {"$sum": "$totalPvp"},
            "aceptados": {"$sum": {"$cond": [{"$in": ["$status", ["aceptado", "en_fabricacion", "entregado"]]}, 1, 0]}},
            "entregados": {"$sum": {"$cond": [{"$eq": ["$status", "entregado"]}, 1, 0]}},
        }}
    ]
    proj_results = {r["_id"]: r for r in await db.projects.aggregate(proj_pipeline).to_list(100)}

    # Facturas por creador (via projectId)
    inv_pipeline = [
        {"$match": {"createdAt": {"$gte": start.isoformat()}, "status": {"$in": ["issued","paid"]}}},
        {"$lookup": {"from": "projects", "localField": "projectId", "foreignField": "id", "as": "project"}},
        {"$unwind": {"path": "$project", "preserveNullAndEmpty": True}},
        {"$group": {
            "_id": "$project.userId",
            "facturas": {"$sum": 1},
            "totalFacturado": {"$sum": "$total"},
        }}
    ]
    inv_results = {r["_id"]: r for r in await db.invoices.aggregate(inv_pipeline).to_list(100)}

    # Oportunidades ganadas
    opp_pipeline = [
        {"$match": {"stage": "won", "updatedAt": {"$gte": start.isoformat()}}},
        {"$group": {"_id": "$assignedTo", "ganadas": {"$sum": 1}, "valorGanado": {"$sum": "$value"}}}
    ]
    opp_results = {r["_id"]: r for r in await db.opportunities.aggregate(opp_pipeline).to_list(100)}

    # Obtener todos los usuarios comerciales
    users = await db.users.find(
        {"isAdmin": {"$ne": True}},
        {"_id": 0, "id": 1, "username": 1, "clientName": 1, "email": 1, "isRepresentative": 1, "isTienda": 1}
    ).to_list(100)

    ranking = []
    for user in users:
        uid = user["id"]
        proj = proj_results.get(uid, {})
        inv = inv_results.get(uid, {})
        opp = opp_results.get(uid, {})
        presupuestos = proj.get("presupuestos", 0)
        aceptados = proj.get("aceptados", 0)
        conversion = round(aceptados / max(presupuestos, 1) * 100, 1)

        ranking.append({
            "userId": uid,
            "nombre": user.get("clientName") or user.get("username", ""),
            "email": user.get("email", ""),
            "rol": "Comercial" if user.get("isRepresentative") else "Tienda" if user.get("isTienda") else "Usuario",
            "presupuestos": presupuestos,
            "totalPvp": round(proj.get("totalPvp", 0), 2),
            "aceptados": aceptados,
            "conversion": conversion,
            "entregados": proj.get("entregados", 0),
            "facturas": inv.get("facturas", 0),
            "totalFacturado": round(inv.get("totalFacturado", 0), 2),
            "oportunidadesGanadas": opp.get("ganadas", 0),
            "valorGanado": round(opp.get("valorGanado", 0), 2),
        })

    ranking.sort(key=lambda x: x["totalPvp"], reverse=True)
    return {"ranking": ranking, "dias": days}


@router.get("/alerts")
async def get_alerts():
    """Alertas del sistema que requieren atención"""
    today = now_utc()
    alerts = []

    # Facturas vencidas
    overdue = await db.invoices.count_documents({
        "status": "issued",
        "dueDate": {"$lt": today.date().isoformat()}
    })
    if overdue > 0:
        alerts.append({"tipo": "error", "icono": "💸", "titulo": f"{overdue} factura{'s' if overdue>1 else ''} vencida{'s' if overdue>1 else ''}", "descripcion": "Facturas emitidas sin cobrar con fecha de vencimiento superada", "accion": "facturas"})

    # Presupuestos caducando en 7 días
    soon = (today + timedelta(days=7)).date().isoformat()
    expiring = await db.projects.count_documents({
        "status": {"$in": ["borrador", "enviado"]},
        "validUntil": {"$lte": soon, "$gte": today.date().isoformat()}
    })
    if expiring > 0:
        alerts.append({"tipo": "warning", "icono": "⏰", "titulo": f"{expiring} presupuesto{'s' if expiring>1 else ''} caduca en 7 días", "descripcion": "Presupuestos en estado borrador o enviado próximos a caducar", "accion": "archivo"})

    # Pedidos pendientes en fábrica > 3 días
    old_pending = await db.fabrica_orders.count_documents({
        "status": "pending",
        "createdAt": {"$lt": (today - timedelta(days=3)).isoformat()}
    })
    if old_pending > 0:
        alerts.append({"tipo": "warning", "icono": "🏭", "titulo": f"{old_pending} pedido{'s' if old_pending>1 else ''} en espera en fábrica >3 días", "descripcion": "Órdenes de fabricación sin procesar", "accion": "fabrica"})

    # Usuarios sin actividad > 7 días
    active_ids = await db.user_activity.distinct("userId", {"timestamp": {"$gte": days_ago(7)}})
    all_users = await db.users.count_documents({"isAdmin": {"$ne": True}})
    inactive = all_users - len(active_ids)
    if inactive > 0:
        alerts.append({"tipo": "info", "icono": "👤", "titulo": f"{inactive} usuario{'s' if inactive>1 else ''} sin actividad esta semana", "descripcion": "Comerciales o tiendas que no han accedido en 7 días", "accion": "usuarios"})

    # Oportunidades sin actualizar > 14 días
    stale_opps = await db.opportunities.count_documents({
        "stage": {"$nin": ["won", "lost"]},
        "updatedAt": {"$lt": days_ago(14).isoformat()}
    })
    if stale_opps > 0:
        alerts.append({"tipo": "info", "icono": "🎯", "titulo": f"{stale_opps} oportunidad{'es' if stale_opps>1 else ''} sin actualizar >14 días", "descripcion": "Oportunidades activas sin movimiento reciente", "accion": "crm"})

    return {"alertas": alerts, "total": len(alerts)}


@router.get("/realtime")
async def get_realtime():
    """Actividad en tiempo real - últimas 24h por hora"""
    now = now_utc()
    start = now - timedelta(hours=24)

    pipeline = [
        {"$match": {"timestamp": {"$gte": start}}},
        {"$group": {
            "_id": {"$hour": "$timestamp"},
            "acciones": {"$sum": 1},
            "usuarios": {"$addToSet": "$userId"}
        }},
        {"$sort": {"_id": 1}}
    ]
    results = await db.user_activity.aggregate(pipeline).to_list(24)

    horas = []
    for r in results:
        horas.append({
            "hora": f"{r['_id']:02d}:00",
            "acciones": r["acciones"],
            "usuarios": len(r["usuarios"])
        })

    # Últimas 10 acciones
    last_actions = await db.user_activity.find(
        {}, {"_id": 0}
    ).sort("timestamp", -1).limit(10).to_list(10)

    for a in last_actions:
        if hasattr(a.get("timestamp"), "isoformat"):
            a["timestamp"] = a["timestamp"].isoformat()

    return {"porHora": horas, "ultimasAcciones": last_actions}
