"""
Dashboard de Métricas - LUIGGI HOME
Métricas de producción y ventas para el Panel Maestro
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime, timezone, timedelta
import os
import logging

from motor.motor_asyncio import AsyncIOMotorClient

mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'luiggi_home')]

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard Métricas"])

try:
    from services.jwt_service import require_auth
except Exception:  # pragma: no cover
    from fastapi import HTTPException
    async def require_auth():
        raise HTTPException(status_code=503, detail="Auth service unavailable")


def get_date_range(period: str):
    """Calcula el rango de fechas según el período seleccionado"""
    now = datetime.now(timezone.utc)
    
    if period == "week":
        start = now - timedelta(days=7)
    elif period == "month":
        start = now - timedelta(days=30)
    elif period == "quarter":
        start = now - timedelta(days=90)
    elif period == "year":
        start = now - timedelta(days=365)
    elif period == "all":
        start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    else:
        start = now - timedelta(days=30)  # Default: mes
    
    return start.isoformat(), now.isoformat()


@router.get("/metrics")
async def get_dashboard_metrics(
    period: str = Query("month", description="Período: week, month, quarter, year, all"),
    current_user: dict = Depends(require_auth)
):
    """
    Obtiene todas las métricas del dashboard para el período seleccionado.
    Incluye métricas de producción y ventas.
    """
    try:
        start_date, end_date = get_date_range(period)
        
        # ============================================
        # MÉTRICAS DE PRODUCCIÓN (fabrica_orders)
        # ============================================
        
        # Total de órdenes de fabricación
        fab_orders = await db.fabrica_orders.find({
            "createdAt": {"$gte": start_date, "$lte": end_date}
        }, {"_id": 0}).to_list(5000)
        
        # Conteo por estado
        fab_by_status = {
            "draft": 0,
            "confirmed": 0,
            "in_production": 0,
            "ready": 0,
            "delivered": 0,
            "cancelled": 0
        }
        
        fab_by_priority = {
            "low": 0,
            "normal": 0,
            "high": 0,
            "urgent": 0
        }
        
        fab_by_factory = {}
        total_pieces = 0
        
        for order in fab_orders:
            status = order.get("status", "draft")
            priority = order.get("priority", "normal")
            factory = order.get("factoryName", "Sin asignar")
            
            if status in fab_by_status:
                fab_by_status[status] += 1
            if priority in fab_by_priority:
                fab_by_priority[priority] += 1
            
            fab_by_factory[factory] = fab_by_factory.get(factory, 0) + 1
            total_pieces += order.get("totalPieces", 0)
        
        # ============================================
        # MÉTRICAS DE VENTAS (orders confirmados)
        # ============================================
        
        # Pedidos confirmados
        confirmed_orders = await db.orders.find({
            "confirmedAt": {"$gte": start_date, "$lte": end_date}
        }, {"_id": 0}).to_list(5000)
        
        total_sales_value = 0
        orders_by_month = {}
        
        for order in confirmed_orders:
            # Valor total del pedido
            total_sales_value += float(order.get("budget", {}).get("totalWithIVA", 0) or 0)
            
            # Agrupar por mes
            confirmed_at = order.get("confirmedAt", "")
            if confirmed_at:
                try:
                    month_key = confirmed_at[:7]  # "2026-03"
                    orders_by_month[month_key] = orders_by_month.get(month_key, 0) + 1
                except:
                    pass
        
        # ============================================
        # MÉTRICAS DE PRESUPUESTOS (projects)
        # ============================================
        
        # Presupuestos creados en el período
        projects = await db.projects.find({
            "createdAt": {"$gte": start_date, "$lte": end_date}
        }, {"_id": 0}).to_list(5000)
        
        projects_by_status = {
            "draft": 0,
            "sent": 0,
            "accepted": 0,
            "rejected": 0,
            "completed": 0
        }
        
        total_budget_value = 0
        budgets_by_month = {}
        
        for project in projects:
            status = project.get("status", "draft")
            if status in projects_by_status:
                projects_by_status[status] += 1
            
            # Valor del presupuesto
            total_budget_value += float(project.get("totalWithIVA", 0) or 0)
            
            # Agrupar por mes
            created_at = project.get("createdAt", "")
            if created_at:
                try:
                    month_key = created_at[:7]
                    budgets_by_month[month_key] = budgets_by_month.get(month_key, 0) + 1
                except:
                    pass
        
        # ============================================
        # MÉTRICAS DE CLIENTES (clients)
        # ============================================
        
        total_clients = await db.clients.count_documents({})
        active_clients = await db.clients.count_documents({"status": "activo"})
        potential_clients = await db.clients.count_documents({"status": "potencial"})
        
        # ============================================
        # MÉTRICAS DE PRODUCTOS
        # ============================================
        
        total_products = await db.products.count_documents({})
        products_zc = await db.products.count_documents({"library": "ZC"})
        products_mv = await db.products.count_documents({"library": "MV"})
        
        # ============================================
        # TENDENCIA MENSUAL (últimos 6 meses)
        # ============================================
        
        monthly_trend = []
        for i in range(5, -1, -1):
            month_date = datetime.now(timezone.utc) - timedelta(days=i*30)
            month_key = month_date.strftime("%Y-%m")
            month_name = month_date.strftime("%b")
            
            monthly_trend.append({
                "month": month_key,
                "name": month_name,
                "pedidos": orders_by_month.get(month_key, 0),
                "presupuestos": budgets_by_month.get(month_key, 0)
            })
        
        # ============================================
        # ÚLTIMOS PEDIDOS
        # ============================================
        
        recent_orders = await db.orders.find(
            {}, {"_id": 0}
        ).sort("confirmedAt", -1).limit(5).to_list(5)
        
        recent_orders_list = []
        for order in recent_orders:
            recent_orders_list.append({
                "orderNumber": order.get("orderNumber", ""),
                "clientName": order.get("budget", {}).get("clientName", order.get("clientName", "")),
                "total": order.get("budget", {}).get("totalWithIVA", 0),
                "confirmedAt": order.get("confirmedAt", ""),
                "status": order.get("status", "confirmed")
            })
        
        # ============================================
        # ÓRDENES DE FABRICACIÓN PENDIENTES
        # ============================================
        
        pending_fab = await db.fabrica_orders.find(
            {"status": {"$in": ["confirmed", "in_production"]}},
            {"_id": 0}
        ).sort("createdAt", -1).limit(5).to_list(5)
        
        pending_fab_list = []
        for fab in pending_fab:
            pending_fab_list.append({
                "orderNumber": fab.get("orderNumber", ""),
                "manufacturingNumber": fab.get("manufacturingNumber"),
                "customerName": fab.get("customerName", ""),
                "totalPieces": fab.get("totalPieces", 0),
                "status": fab.get("status", ""),
                "priority": fab.get("priority", "normal"),
                "factoryName": fab.get("factoryName", "Sin asignar")
            })
        
        # ============================================
        # RESPUESTA COMPLETA
        # ============================================
        
        return {
            "period": period,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            
            # KPIs principales
            "kpis": {
                "totalFabOrders": len(fab_orders),
                "totalConfirmedOrders": len(confirmed_orders),
                "totalBudgets": len(projects),
                "totalSalesValue": round(total_sales_value, 2),
                "totalBudgetValue": round(total_budget_value, 2),
                "totalPiecesInProduction": total_pieces,
                "conversionRate": round((len(confirmed_orders) / max(len(projects), 1)) * 100, 1)
            },
            
            # Métricas de producción
            "production": {
                "byStatus": fab_by_status,
                "byPriority": fab_by_priority,
                "byFactory": fab_by_factory,
                "pendingOrders": pending_fab_list
            },
            
            # Métricas de ventas
            "sales": {
                "ordersByStatus": {
                    "confirmed": len([o for o in confirmed_orders if o.get("status") == "confirmed"]),
                    "in_production": len([o for o in confirmed_orders if o.get("status") == "in_production"]),
                    "delivered": len([o for o in confirmed_orders if o.get("status") == "delivered"])
                },
                "recentOrders": recent_orders_list
            },
            
            # Presupuestos
            "budgets": {
                "byStatus": projects_by_status,
                "avgValue": round(total_budget_value / max(len(projects), 1), 2)
            },
            
            # Clientes
            "clients": {
                "total": total_clients,
                "active": active_clients,
                "potential": potential_clients
            },
            
            # Productos
            "products": {
                "total": total_products,
                "zc": products_zc,
                "mv": products_mv
            },
            
            # Tendencia mensual
            "monthlyTrend": monthly_trend
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        return {
            "error": str(e),
            "kpis": {},
            "production": {},
            "sales": {},
            "budgets": {},
            "clients": {},
            "products": {},
            "monthlyTrend": []
        }


@router.get("/production-summary")
async def get_production_summary(current_user: dict = Depends(require_auth)):
    """Resumen rápido de producción para widgets"""
    try:
        # Pedidos pendientes de producción
        pending = await db.fabrica_orders.count_documents({
            "status": {"$in": ["confirmed", "in_production"]}
        })
        
        # Completados esta semana
        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        completed_week = await db.fabrica_orders.count_documents({
            "status": "delivered",
            "updatedAt": {"$gte": week_ago}
        })
        
        # Urgentes
        urgent = await db.fabrica_orders.count_documents({
            "status": {"$in": ["confirmed", "in_production"]},
            "priority": "urgent"
        })
        
        return {
            "pendingProduction": pending,
            "completedThisWeek": completed_week,
            "urgentOrders": urgent
        }
        
    except Exception as e:
        logger.error(f"Error getting production summary: {e}")
        return {"pendingProduction": 0, "completedThisWeek": 0, "urgentOrders": 0}
