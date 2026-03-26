"""
Routes for data exports to Excel
Extracted from server.py for better maintainability
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
from io import BytesIO
import pandas as pd
import jwt
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["exports"])
security = HTTPBearer()

# JWT settings from environment
JWT_SECRET = os.environ.get("JWT_SECRET", "luiggi-home-kitchen-2024-secret-key")

# Database connection will be imported from server
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "luiggi_home")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


@router.get("/clientes")
async def export_clientes_excel(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Exportar clientes a Excel"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user or not user.get("isAdmin"):
            raise HTTPException(status_code=403, detail="Solo administradores pueden exportar")
        
        clients = await db.clients.find({}).to_list(length=None)
        
        data = []
        for c in clients:
            data.append({
                'NOMBRE': c.get('name', ''),
                'EMPRESA': c.get('company', ''),
                'EMAIL': c.get('email', ''),
                'TELEFONO': c.get('phone', ''),
                'DIRECCION': c.get('address', ''),
                'CIUDAD': c.get('city', ''),
                'CP': c.get('postalCode', ''),
                'TIPO': c.get('type', ''),
                'SEGMENTO': c.get('segment', ''),
                'COMERCIAL': c.get('assignedTo', ''),
                'ESTADO': 'Activo' if c.get('isActive') else 'Potencial',
                'NOTAS': c.get('notes', ''),
                'CREADO': str(c.get('createdAt', ''))[:10],
            })
        
        df = pd.DataFrame(data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Clientes')
        output.seek(0)
        
        filename = f"LUIGGI_Clientes_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    except Exception as e:
        logger.error(f"Export clientes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/presupuestos")
async def export_presupuestos_excel(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Exportar presupuestos a Excel"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=403, detail="Usuario no encontrado")
        
        projects = await db.projects.find({}).to_list(length=None)
        
        if not projects:
            raise HTTPException(status_code=404, detail="No hay presupuestos para exportar")
        
        data = []
        for p in projects:
            items = p.get('items', [])
            total_pvp = sum(item.get('totalPrice', 0) for item in items)
            total_coste = sum(item.get('costPrice', 0) * item.get('quantity', 1) for item in items)
            
            data.append({
                'EXPEDIENTE': p.get('expediente', ''),
                'REFERENCIA': p.get('projectReference', ''),
                'CLIENTE': p.get('clientName', ''),
                'COMERCIAL': p.get('userName', ''),
                'FECHA': str(p.get('createdAt', ''))[:10],
                'TOTAL_PVP': round(total_pvp, 2),
                'TOTAL_COSTE': round(total_coste, 2),
                'MARGEN': round(total_pvp - total_coste, 2),
                'NUM_ARTICULOS': len(items),
                'ZONA': p.get('zone', ''),
                'ACABADO': p.get('finish', ''),
                'ESTADO': p.get('status', 'borrador'),
            })
        
        df = pd.DataFrame(data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Presupuestos')
        output.seek(0)
        
        filename = f"LUIGGI_Presupuestos_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    except Exception as e:
        logger.error(f"Export presupuestos error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crm")
async def export_crm_excel(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Exportar datos CRM a Excel (oportunidades, actividades, calendario)"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user or not user.get("canAccessCRM"):
            raise HTTPException(status_code=403, detail="Sin acceso a CRM")
        
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Oportunidades
            opportunities = await db.crm_opportunities.find({}).to_list(length=None)
            if opportunities:
                opp_data = []
                for o in opportunities:
                    opp_data.append({
                        'TITULO': o.get('title', ''),
                        'CLIENTE': o.get('clientName', ''),
                        'VALOR': o.get('value', 0),
                        'ETAPA': o.get('stage', ''),
                        'PROBABILIDAD': o.get('probability', 0),
                        'COMERCIAL': o.get('assignedTo', ''),
                        'FECHA_CIERRE': str(o.get('expectedCloseDate', ''))[:10],
                        'CREADO': str(o.get('createdAt', ''))[:10],
                    })
                pd.DataFrame(opp_data).to_excel(writer, index=False, sheet_name='Oportunidades')
            
            # Actividades
            activities = await db.crm_activities.find({}).to_list(length=None)
            if activities:
                act_data = []
                for a in activities:
                    act_data.append({
                        'TIPO': a.get('type', ''),
                        'TITULO': a.get('title', ''),
                        'DESCRIPCION': a.get('description', ''),
                        'CLIENTE': a.get('clientName', ''),
                        'COMERCIAL': a.get('userName', ''),
                        'FECHA': str(a.get('date', ''))[:10],
                        'COMPLETADA': 'Sí' if a.get('completed') else 'No',
                    })
                pd.DataFrame(act_data).to_excel(writer, index=False, sheet_name='Actividades')
            
            # Eventos calendario
            events = await db.crm_calendar.find({}).to_list(length=None)
            if events:
                evt_data = []
                for e in events:
                    evt_data.append({
                        'TITULO': e.get('title', ''),
                        'TIPO': e.get('type', ''),
                        'INICIO': str(e.get('start', '')),
                        'FIN': str(e.get('end', '')),
                        'CLIENTE': e.get('clientName', ''),
                        'COMERCIAL': e.get('userName', ''),
                        'NOTAS': e.get('notes', ''),
                    })
                pd.DataFrame(evt_data).to_excel(writer, index=False, sheet_name='Calendario')
        
        output.seek(0)
        
        filename = f"LUIGGI_CRM_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    except Exception as e:
        logger.error(f"Export CRM error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usuarios")
async def export_usuarios_excel(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Exportar usuarios a Excel (solo admin)"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user or not user.get("isAdmin"):
            raise HTTPException(status_code=403, detail="Solo administradores")
        
        users = await db.users.find({}).to_list(length=None)
        
        data = []
        for u in users:
            rol = "Director" if u.get('isAdmin') else \
                  "Resp. Delegación" if u.get('isResponsableDelegacion') else \
                  "Comercial" if u.get('isRepresentative') else \
                  "Tienda" if u.get('isTienda') else "Colaborador"
            
            data.append({
                'USUARIO': u.get('username', ''),
                'NOMBRE_CLIENTE': u.get('clientName', ''),
                'ROL': rol,
                'ACTIVO': 'Sí' if u.get('isActive') else 'No',
                'DESCUENTO': u.get('commercialDiscount', 0),
                'MODULOS': ', '.join(u.get('allowedModules', [])),
                'VER_COSTE': 'Sí' if u.get('canSeeCost') else 'No',
                'CRM': 'Sí' if u.get('canAccessCRM') else 'No',
                'IA_LAB': 'Sí' if u.get('canUseAIAnalysis') else 'No',
            })
        
        df = pd.DataFrame(data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Usuarios')
        output.seek(0)
        
        filename = f"LUIGGI_Usuarios_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    except Exception as e:
        logger.error(f"Export usuarios error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
