# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Servicio de Tracking de Actividad de Usuarios para LUIGGI HOME
- Registra acciones de usuarios
- Genera informes de uso
- Métricas y estadísticas
"""
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ActivityType(str, Enum):
    """Tipos de actividad rastreables"""
    LOGIN = "login"
    LOGOUT = "logout"
    BUDGET_CREATE = "budget_create"
    BUDGET_UPDATE = "budget_update"
    BUDGET_DELETE = "budget_delete"
    BUDGET_VIEW = "budget_view"
    BUDGET_EXPORT_PDF = "budget_export_pdf"
    ORDER_CREATE = "order_create"
    ORDER_UPDATE = "order_update"
    ORDER_CONFIRM = "order_confirm"
    CATALOG_VIEW = "catalog_view"
    PRODUCT_ADD = "product_add"
    PRODUCT_SEARCH = "product_search"
    SETTINGS_UPDATE = "settings_update"
    USER_CREATE = "user_create"
    AI_TELEMETRY = "ai_telemetry"
    FACTORY_VIEW = "factory_view"
    REPORT_GENERATE = "report_generate"
    FILE_UPLOAD = "file_upload"
    OTHER = "other"


class ActivityTracker:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.user_activity
        
    async def setup_indexes(self):
        """Crear índices para optimizar consultas"""
        await self.collection.create_index("userId")
        await self.collection.create_index("activityType")
        await self.collection.create_index([("userId", 1), ("timestamp", -1)])
        await self.collection.create_index([("activityType", 1), ("timestamp", -1)])

        # Índice TTL en 'timestamp': caduca la telemetría a los 180 días para
        # que la colección no crezca sin límite y acabe llenando la cuota de la
        # BD (lo que bloquearía las escrituras de contactos/visitas/presupuestos).
        # Como en despliegues previos puede existir ya un índice simple
        # 'timestamp_1' (sin TTL), MongoDB daría conflicto: en ese caso lo
        # eliminamos y lo recreamos con expiración.
        TTL_SECONDS = 180 * 24 * 3600
        try:
            await self.collection.create_index("timestamp", expireAfterSeconds=TTL_SECONDS)
        except Exception:
            try:
                await self.collection.drop_index("timestamp_1")
                await self.collection.create_index("timestamp", expireAfterSeconds=TTL_SECONDS)
                logger.info("Índice 'timestamp' recreado con TTL de 180 días")
            except Exception as e:
                logger.warning(f"No se pudo aplicar TTL a la actividad: {e}")
        logger.info("Índices de actividad creados")
    
    async def track(
        self,
        user_id: str,
        username: str,
        activity_type: ActivityType,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ):
        """Registrar una actividad de usuario"""
        try:
            activity = {
                "userId": user_id,
                "username": username,
                "activityType": activity_type.value,
                "timestamp": datetime.utcnow(),
                "details": details or {},
                "ipAddress": ip_address
            }
            
            await self.collection.insert_one(activity)
            logger.debug(f"Actividad registrada: {username} - {activity_type.value}")
            
        except Exception as e:
            logger.error(f"Error registrando actividad: {str(e)}")
    
    async def get_user_stats(
        self,
        user_id: Optional[str] = None,
        days: int = 30
    ) -> List[Dict]:
        """Obtener estadísticas de uso por usuario"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        match_stage = {"timestamp": {"$gte": start_date}}
        if user_id:
            match_stage["userId"] = user_id
        
        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": "$userId",
                    "username": {"$first": "$username"},
                    "totalActions": {"$sum": 1},
                    "logins": {
                        "$sum": {"$cond": [{"$eq": ["$activityType", "login"]}, 1, 0]}
                    },
                    "budgetsCreated": {
                        "$sum": {"$cond": [{"$eq": ["$activityType", "budget_create"]}, 1, 0]}
                    },
                    "budgetsUpdated": {
                        "$sum": {"$cond": [{"$eq": ["$activityType", "budget_update"]}, 1, 0]}
                    },
                    "ordersCreated": {
                        "$sum": {"$cond": [{"$eq": ["$activityType", "order_create"]}, 1, 0]}
                    },
                    "ordersConfirmed": {
                        "$sum": {"$cond": [{"$eq": ["$activityType", "order_confirm"]}, 1, 0]}
                    },
                    "pdfsExported": {
                        "$sum": {"$cond": [{"$eq": ["$activityType", "budget_export_pdf"]}, 1, 0]}
                    },
                    "aiTelemetryUses": {
                        "$sum": {"$cond": [{"$eq": ["$activityType", "ai_telemetry"]}, 1, 0]}
                    },
                    "lastActivity": {"$max": "$timestamp"},
                    "firstActivity": {"$min": "$timestamp"}
                }
            },
            {"$sort": {"totalActions": -1}}
        ]
        
        results = await self.collection.aggregate(pipeline).to_list(length=None)
        
        # Calcular días activos
        for r in results:
            r["_id"] = str(r["_id"]) if r["_id"] else None
            if r.get("lastActivity"):
                r["lastActivity"] = r["lastActivity"].isoformat()
            if r.get("firstActivity"):
                r["firstActivity"] = r["firstActivity"].isoformat()
        
        return results
    
    async def get_activity_timeline(
        self,
        user_id: Optional[str] = None,
        days: int = 30,
        limit: int = 100
    ) -> List[Dict]:
        """Obtener timeline de actividades"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        match_stage = {"timestamp": {"$gte": start_date}}
        if user_id:
            match_stage["userId"] = user_id
        
        cursor = self.collection.find(
            match_stage,
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit)
        
        results = await cursor.to_list(length=limit)
        
        for r in results:
            if r.get("timestamp"):
                r["timestamp"] = r["timestamp"].isoformat()
        
        return results
    
    async def get_daily_activity(self, days: int = 30) -> List[Dict]:
        """Obtener actividad agrupada por día"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {"$match": {"timestamp": {"$gte": start_date}}},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}
                    },
                    "totalActions": {"$sum": 1},
                    "uniqueUsers": {"$addToSet": "$userId"},
                    "logins": {
                        "$sum": {"$cond": [{"$eq": ["$activityType", "login"]}, 1, 0]}
                    },
                    "budgets": {
                        "$sum": {"$cond": [{"$eq": ["$activityType", "budget_create"]}, 1, 0]}
                    },
                    "orders": {
                        "$sum": {"$cond": [{"$eq": ["$activityType", "order_create"]}, 1, 0]}
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "date": "$_id",
                    "totalActions": 1,
                    "uniqueUsers": {"$size": "$uniqueUsers"},
                    "logins": 1,
                    "budgets": 1,
                    "orders": 1
                }
            },
            {"$sort": {"date": 1}}
        ]
        
        return await self.collection.aggregate(pipeline).to_list(length=None)
    
    async def get_activity_by_type(self, days: int = 30) -> List[Dict]:
        """Obtener actividad agrupada por tipo"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {"$match": {"timestamp": {"$gte": start_date}}},
            {
                "$group": {
                    "_id": "$activityType",
                    "count": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "activityType": "$_id",
                    "count": 1
                }
            },
            {"$sort": {"count": -1}}
        ]
        
        return await self.collection.aggregate(pipeline).to_list(length=None)
    
    async def get_usage_report(self, days: int = 30) -> Dict:
        """Generar informe completo de uso"""
        user_stats = await self.get_user_stats(days=days)
        daily_activity = await self.get_daily_activity(days=days)
        activity_by_type = await self.get_activity_by_type(days=days)
        
        # Calcular totales
        total_actions = sum(u.get("totalActions", 0) for u in user_stats)
        total_users = len(user_stats)
        active_users = len([u for u in user_stats if u.get("totalActions", 0) > 0])
        
        # Usuario más activo
        most_active = user_stats[0] if user_stats else None
        
        return {
            "period": {
                "days": days,
                "start": (datetime.utcnow() - timedelta(days=days)).isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "summary": {
                "totalActions": total_actions,
                "totalUsers": total_users,
                "activeUsers": active_users,
                "averageActionsPerUser": round(total_actions / active_users, 1) if active_users > 0 else 0
            },
            "mostActiveUser": most_active,
            "userStats": user_stats,
            "dailyActivity": daily_activity,
            "activityByType": activity_by_type,
            "generatedAt": datetime.utcnow().isoformat()
        }


# Instancia global
activity_tracker: ActivityTracker = None

def init_activity_tracker(db: AsyncIOMotorDatabase) -> ActivityTracker:
    global activity_tracker
    activity_tracker = ActivityTracker(db)
    return activity_tracker

def get_tracker() -> ActivityTracker:
    return activity_tracker
