"""
Router para Clientes de Tiendas (Clientes-de-Tiendas)
Cada tienda/distribuidor puede gestionar sus propios clientes finales.
Solo visible para usuarios con isTienda=true o administradores.
"""
import logging
import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Header

from config import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/shop-clients", tags=["Shop Clients"])

# Campos del cliente de tienda -> nombre de campo en db.clients (CRM general)
_CRM_FIELD_MAP = {
    "code": "codigo",
    "name": "nombre",
    "company": "empresa",
    "email": "email",
    "phone": "telefono",
    "address": "direccion",
    "city": "localidad",
    "province": "provincia",
    "postalCode": "codigoPostal",
    "taxId": "cif",
    "notes": "notas",
}


async def _sync_to_crm_client(shop_client: dict):
    """Mantiene un cliente espejo en db.clients (CRM general) para cada cliente
    de tienda, marcado como segmento 'tienda' y atribuido al representante
    (usuario tienda) propietario. Así "Mis Clientes" deja de ser una isla y el
    cliente aparece también en el CRM general."""
    crm_data = {es: shop_client.get(en, "") for en, es in _CRM_FIELD_MAP.items()}
    crm_data["segmento"] = "tienda"
    crm_data["shopClientId"] = shop_client["id"]
    owner_id = shop_client.get("ownerUserId")
    crm_data["updatedAt"] = datetime.now(timezone.utc).isoformat()

    crm_client_id = shop_client.get("crmClientId")
    if crm_client_id:
        existing = await db.clients.find_one({"id": crm_client_id})
    else:
        existing = None

    if existing:
        await db.clients.update_one({"id": crm_client_id}, {"$set": crm_data})
        return crm_client_id

    crm_data["id"] = f"cli-{uuid.uuid4().hex[:8]}"
    crm_data["createdAt"] = crm_data["updatedAt"]
    if owner_id:
        crm_data["createdByUserId"] = owner_id
        crm_data["assignedRepresentativeId"] = owner_id
    await db.clients.insert_one(crm_data)

    await db.shop_clients.update_one(
        {"id": shop_client["id"]}, {"$set": {"crmClientId": crm_data["id"]}}
    )
    return crm_data["id"]


async def get_current_user_from_token(authorization: str = None):
    """Obtener usuario actual desde el token"""
    if not authorization:
        return None
    
    try:
        # El token viene como "Bearer <token>"
        token = authorization.replace("Bearer ", "")
        # Buscar usuario por token (simplificado - en producción usar JWT)
        user = await db.users.find_one({"id": token}, {"_id": 0})
        if not user:
            # Intentar buscar por username como fallback
            user = await db.users.find_one({"username": token}, {"_id": 0})
        return user
    except Exception as e:
        logger.error(f"Error getting user from token: {e}")
        return None


@router.get("")
async def get_shop_clients(
    search: str = None,
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    authorization: str = Header(None),
    user_id: str = None  # Parámetro alternativo para pasar el userId
):
    """
    Obtener clientes de tienda.
    - Si es admin/director: ve todos los clientes de todas las tiendas
    - Si es tienda: solo ve sus propios clientes
    """
    # Intentar obtener usuario actual
    current_user = await get_current_user_from_token(authorization)
    
    # Si no hay token, usar user_id del query param
    if not current_user and user_id:
        current_user = await db.users.find_one({"id": user_id}, {"_id": 0})
    
    query = {}
    
    # Filtrar por tienda propietaria si no es admin
    if current_user:
        is_admin = current_user.get("isAdmin") or current_user.get("isGerente") or current_user.get("isDirectorComercial")
        if not is_admin:
            # Solo ver clientes propios
            query["ownerUserId"] = current_user.get("id")
    
    # Filtros adicionales
    if status:
        query["status"] = status
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"company": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    
    clients = await db.shop_clients.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Agregar nombre de tienda propietaria para admins
    if current_user and (current_user.get("isAdmin") or current_user.get("isGerente") or current_user.get("isDirectorComercial")):
        for client in clients:
            if client.get("ownerUserId"):
                owner = await db.users.find_one({"id": client["ownerUserId"]}, {"_id": 0, "clientName": 1})
                client["ownerName"] = owner.get("clientName", "Desconocido") if owner else "Desconocido"
    
    return clients


@router.get("/by-owner/{owner_user_id}")
async def get_shop_clients_by_owner(
    owner_user_id: str,
    search: str = None,
    skip: int = 0,
    limit: int = 100
):
    """Obtener clientes de una tienda específica (para admins)"""
    query = {"ownerUserId": owner_user_id}
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"company": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    clients = await db.shop_clients.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    return clients


@router.get("/stats")
async def get_shop_clients_stats(
    user_id: str = None,
    authorization: str = Header(None)
):
    """Obtener estadísticas de clientes de tienda"""
    current_user = await get_current_user_from_token(authorization)
    if not current_user and user_id:
        current_user = await db.users.find_one({"id": user_id}, {"_id": 0})
    
    query = {}
    if current_user:
        is_admin = current_user.get("isAdmin") or current_user.get("isGerente") or current_user.get("isDirectorComercial")
        if not is_admin:
            query["ownerUserId"] = current_user.get("id")
    
    total = await db.shop_clients.count_documents(query)
    
    # Contar por estado
    active_query = {**query, "status": "active"}
    potential_query = {**query, "status": "potential"}
    
    active = await db.shop_clients.count_documents(active_query)
    potential = await db.shop_clients.count_documents(potential_query)
    
    return {
        "total": total,
        "active": active,
        "potential": potential,
        "inactive": total - active - potential
    }


@router.get("/{client_id}")
async def get_shop_client(
    client_id: str,
    user_id: str = None,
    authorization: str = Header(None)
):
    """Obtener un cliente de tienda por ID"""
    current_user = await get_current_user_from_token(authorization)
    if not current_user and user_id:
        current_user = await db.users.find_one({"id": user_id}, {"_id": 0})
    
    client = await db.shop_clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Verificar permisos
    if current_user:
        is_admin = current_user.get("isAdmin") or current_user.get("isGerente") or current_user.get("isDirectorComercial")
        if not is_admin and client.get("ownerUserId") != current_user.get("id"):
            raise HTTPException(status_code=403, detail="No tienes permiso para ver este cliente")
    
    return client


@router.post("")
async def create_shop_client(
    client_data: dict,
    user_id: str = None,
    authorization: str = Header(None)
):
    """Crear un nuevo cliente de tienda"""
    current_user = await get_current_user_from_token(authorization)
    if not current_user and user_id:
        current_user = await db.users.find_one({"id": user_id}, {"_id": 0})
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    # Verificar que el usuario puede crear clientes (es tienda o admin)
    is_admin = current_user.get("isAdmin") or current_user.get("isGerente") or current_user.get("isDirectorComercial")
    is_tienda = current_user.get("isTienda")
    
    if not is_admin and not is_tienda:
        raise HTTPException(status_code=403, detail="Solo tiendas y administradores pueden crear clientes de tienda")
    
    # Crear el cliente
    client_dict = {
        "id": f"shcli-{uuid.uuid4().hex[:8]}",
        "code": client_data.get("code", ""),
        "name": client_data.get("name", ""),
        "company": client_data.get("company", ""),
        "email": client_data.get("email", ""),
        "phone": client_data.get("phone", ""),
        "address": client_data.get("address", ""),
        "city": client_data.get("city", ""),
        "province": client_data.get("province", ""),
        "postalCode": client_data.get("postalCode", ""),
        "taxId": client_data.get("taxId", ""),
        "status": client_data.get("status", "potential"),
        "notes": client_data.get("notes", ""),
        "ownerUserId": current_user.get("id"),  # ID del usuario tienda propietario
        "ownerName": current_user.get("clientName", ""),  # Nombre de la tienda
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc)
    }
    
    # Si es admin creando para otra tienda
    if is_admin and client_data.get("ownerUserId"):
        client_dict["ownerUserId"] = client_data["ownerUserId"]
        owner = await db.users.find_one({"id": client_data["ownerUserId"]}, {"_id": 0, "clientName": 1})
        client_dict["ownerName"] = owner.get("clientName", "") if owner else ""
    
    await db.shop_clients.insert_one(client_dict)
    await _sync_to_crm_client(client_dict)

    result = await db.shop_clients.find_one({"id": client_dict["id"]}, {"_id": 0})
    return result


@router.put("/{client_id}")
async def update_shop_client(
    client_id: str,
    client_data: dict,
    user_id: str = None,
    authorization: str = Header(None)
):
    """Actualizar un cliente de tienda"""
    current_user = await get_current_user_from_token(authorization)
    if not current_user and user_id:
        current_user = await db.users.find_one({"id": user_id}, {"_id": 0})
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    # Verificar que el cliente existe
    existing = await db.shop_clients.find_one({"id": client_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Verificar permisos
    is_admin = current_user.get("isAdmin") or current_user.get("isGerente") or current_user.get("isDirectorComercial")
    if not is_admin and existing.get("ownerUserId") != current_user.get("id"):
        raise HTTPException(status_code=403, detail="No tienes permiso para editar este cliente")
    
    # Actualizar solo campos permitidos
    update_fields = ["code", "name", "company", "email", "phone", "address", 
                     "city", "province", "postalCode", "taxId", "status", "notes"]
    
    update_data = {k: v for k, v in client_data.items() if k in update_fields and v is not None}
    update_data["updatedAt"] = datetime.now(timezone.utc)
    
    await db.shop_clients.update_one({"id": client_id}, {"$set": update_data})

    result = await db.shop_clients.find_one({"id": client_id}, {"_id": 0})
    await _sync_to_crm_client(result)
    return result


@router.delete("/{client_id}")
async def delete_shop_client(
    client_id: str,
    user_id: str = None,
    authorization: str = Header(None)
):
    """Eliminar un cliente de tienda"""
    current_user = await get_current_user_from_token(authorization)
    if not current_user and user_id:
        current_user = await db.users.find_one({"id": user_id}, {"_id": 0})
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    # Verificar que el cliente existe
    existing = await db.shop_clients.find_one({"id": client_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Verificar permisos
    is_admin = current_user.get("isAdmin") or current_user.get("isGerente") or current_user.get("isDirectorComercial")
    if not is_admin and existing.get("ownerUserId") != current_user.get("id"):
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este cliente")
    
    await db.shop_clients.delete_one({"id": client_id})
    return {"success": True}


@router.post("/import")
async def import_shop_clients(
    data: dict,
    user_id: str = None,
    authorization: str = Header(None)
):
    """Importar clientes de tienda desde CSV/Excel"""
    current_user = await get_current_user_from_token(authorization)
    if not current_user and user_id:
        current_user = await db.users.find_one({"id": user_id}, {"_id": 0})
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    clients_data = data.get("clients", [])
    if not clients_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron clientes para importar")
    
    imported = 0
    errors = []
    
    for idx, client in enumerate(clients_data):
        try:
            client_dict = {
                "id": f"shcli-{uuid.uuid4().hex[:8]}",
                "code": client.get("code", ""),
                "name": client.get("name", client.get("nombre", "")),
                "company": client.get("company", client.get("empresa", "")),
                "email": client.get("email", ""),
                "phone": client.get("phone", client.get("telefono", "")),
                "address": client.get("address", client.get("direccion", "")),
                "city": client.get("city", client.get("ciudad", "")),
                "province": client.get("province", client.get("provincia", "")),
                "postalCode": client.get("postalCode", client.get("cp", "")),
                "taxId": client.get("taxId", client.get("cif", "")),
                "status": "potential",
                "notes": client.get("notes", client.get("notas", "")),
                "ownerUserId": current_user.get("id"),
                "ownerName": current_user.get("clientName", ""),
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc)
            }
            
            if client_dict["name"]:
                await db.shop_clients.insert_one(client_dict)
                await _sync_to_crm_client(client_dict)
                imported += 1
            else:
                errors.append(f"Fila {idx + 1}: Nombre requerido")
                
        except Exception as e:
            errors.append(f"Fila {idx + 1}: {str(e)}")
    
    return {
        "success": True,
        "imported": imported,
        "errors": errors
    }
