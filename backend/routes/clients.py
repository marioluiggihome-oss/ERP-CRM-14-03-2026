# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Router de CLIENTES — extraído tal cual de server.py (endpoints vivos).

Mantiene las rutas completas (/clients...) sin prefijo para conservar el
comportamiento y el ORDEN interno original (p.ej. /clients/segments antes que
/clients/{client_id}). Incluye el aislamiento por usuario (cada comercial ve
sus clientes; admin/dirección ven todos).
"""
import re
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends

from services.db_client import get_db as _get_db_singleton
db = _get_db_singleton()
from models.schemas import ClientUpdate
from services.jwt_service import get_current_user, require_auth, ADMIN_ROLE_FLAGS

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Clients"])


@router.get("/clients")
async def get_clients(activo: Optional[bool] = None, search: Optional[str] = None,
                      current_user: Optional[dict] = Depends(get_current_user)):
    """Obtener clientes. AISLAMIENTO por usuario: cada comercial ve SOLO sus
    clientes (creados o asignados); admin/dirección (ADMIN_ROLE_FLAGS) ven todos.
    Sin token (sesiones legacy) se mantiene el comportamiento anterior."""
    query = {}
    if activo is not None:
        query["activo"] = activo

    if current_user and current_user.get("id"):
        elevated = any(current_user.get(f) for f in ADMIN_ROLE_FLAGS)
        if not elevated:
            uid = current_user["id"]
            owner = {"$or": [
                {"createdByUserId": uid},
                {"assignedRepresentativeId": uid},
                {"linkedUserId": uid},
            ]}
            query = {"$and": [query, owner]} if query else owner

    clients = await db.clients.find(query, {"_id": 0}).to_list(5000)
    
    if search:
        search_lower = search.lower()
        clients = [c for c in clients if 
            search_lower in c.get("codigo", "").lower() or
            search_lower in c.get("nombre", "").lower() or
            search_lower in c.get("cif", "").lower() or
            search_lower in c.get("localidad", "").lower()
        ]

    # Para clientes segmento "tienda", resolver el nombre de la tienda
    # (assignedRepresentativeId) que los gestiona, para mostrarlo en el CRM.
    tienda_rep_ids = {c["assignedRepresentativeId"] for c in clients
                      if c.get("segmento") == "tienda" and c.get("assignedRepresentativeId")}
    if tienda_rep_ids:
        reps = await db.users.find(
            {"id": {"$in": list(tienda_rep_ids)}}, {"_id": 0, "id": 1, "username": 1, "clientName": 1}
        ).to_list(len(tienda_rep_ids))
        rep_names = {r["id"]: (r.get("clientName") or r.get("username") or r["id"]) for r in reps}
        for c in clients:
            if c.get("segmento") == "tienda" and c.get("assignedRepresentativeId") in rep_names:
                c["tiendaUserName"] = rep_names[c["assignedRepresentativeId"]]

    return clients

@router.get("/clients/segments")
async def get_client_segments():
    """Obtener lista de segmentos de clientes disponibles"""
    return {
        "segments": [
            {"id": "particular", "name": "Particular"},
            {"id": "profesional", "name": "Profesional"},
            {"id": "constructor", "name": "Constructor/Promotor"},
            {"id": "tienda", "name": "Tienda/Distribuidor"},
            {"id": "mayorista", "name": "Mayorista"}
        ]
    }

@router.get("/clients/tienda-users")
async def get_tienda_users(current_user: dict = Depends(require_auth)):
    """Lista de usuarios marcados como tienda/distribuidor, para poder vincular
    un cliente del CRM (segmento 'tienda') con la tienda real que lo gestiona
    en 'Mis Clientes'."""
    users = await db.users.find(
        {"isTienda": True}, {"_id": 0, "id": 1, "username": 1, "clientName": 1}
    ).to_list(500)
    return [
        {"id": u["id"], "name": u.get("clientName") or u.get("username") or u["id"]}
        for u in users
    ]


@router.get("/clients/{client_id}")
async def get_client(client_id: str,
                     current_user: Optional[dict] = Depends(get_current_user)):
    """Obtener un cliente por ID. Aislamiento por usuario: un comercial sólo puede
    acceder a un cliente propio; admin/dirección acceden a cualquiera."""
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if current_user and current_user.get("id"):
        elevated = any(current_user.get(f) for f in ADMIN_ROLE_FLAGS)
        if not elevated:
            uid = current_user["id"]
            owners = {client.get("createdByUserId"), client.get("assignedRepresentativeId"),
                      client.get("linkedUserId")}
            if uid not in owners:
                raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return client

@router.post("/clients")
async def create_client(client: dict, current_user: dict = Depends(require_auth)):
    """Crear un nuevo cliente. Acepta nombres de campo en español (codigo, nombre, cif, ...)
    o en inglés (code, name, taxId, ...). Esto evita fallos por discrepancia entre el
    formulario (español) y el modelo Pydantic (inglés)."""
    # Normalizar nombres de campo a la convención usada en la BD (español)
    field_map = {
        "code": "codigo",
        "name": "nombre",
        "taxId": "cif",
        "address": "direccion",
        "city": "localidad",
        "province": "provincia",
        "postalCode": "codigoPostal",
        "phone": "telefono",
        "discount": "descuento",
        "active": "activo",
        "notes": "notas",
    }
    client_data = dict(client) if isinstance(client, dict) else {}
    for en_key, es_key in field_map.items():
        if en_key in client_data and es_key not in client_data:
            client_data[es_key] = client_data.pop(en_key)

    codigo = (client_data.get("codigo") or "").strip().upper()
    if codigo:
        existing = await db.clients.find_one({"codigo": codigo})
        if existing:
            raise HTTPException(status_code=400, detail="El código de cliente ya existe")

    client_data["id"] = f"cli-{uuid.uuid4().hex[:8]}"
    client_data["codigo"] = codigo
    client_data["createdAt"] = datetime.now(timezone.utc).isoformat()
    client_data["updatedAt"] = datetime.now(timezone.utc).isoformat()

    # Sellar el creador para el aislamiento por usuario (cada uno ve los suyos)
    _uid = current_user.get("id") if current_user else None
    if _uid:
        client_data.setdefault("createdByUserId", _uid)
        if not client_data.get("assignedRepresentativeId"):
            client_data["assignedRepresentativeId"] = _uid

    await db.clients.insert_one(client_data)

    # Return without _id
    client_data.pop("_id", None)
    return client_data


@router.post("/clients/backfill-owner")
async def backfill_clients_owner(payload: dict = None, current_user: dict = Depends(require_auth)):
    """Asigna los clientes SIN dueño a un usuario (por defecto MARIO).

    Para datos antiguos creados antes del aislamiento por usuario. Solo
    admin/dirección. Body opcional: {"username": "MARIO"}.
    """
    if not any(current_user.get(f) for f in ADMIN_ROLE_FLAGS):
        raise HTTPException(status_code=403, detail="Solo administración puede reasignar clientes")
    username = ((payload or {}).get("username") or "MARIO").strip()
    rx = {"$regex": f"^{re.escape(username)}$", "$options": "i"}
    target = await db.users.find_one(
        {"$or": [{"username": rx}, {"clientName": rx}]},
        {"_id": 0, "id": 1, "username": 1, "clientName": 1},
    )
    if not target:
        raise HTTPException(status_code=404, detail=f"No se encontró el usuario '{username}'")
    uid = target["id"]
    sin_dueno = {"$or": [
        {"createdByUserId": {"$exists": False}},
        {"createdByUserId": ""},
        {"createdByUserId": None},
    ]}
    res = await db.clients.update_many(sin_dueno, {"$set": {"createdByUserId": uid}})
    await db.clients.update_many(
        {"$or": [
            {"assignedRepresentativeId": {"$exists": False}},
            {"assignedRepresentativeId": ""},
            {"assignedRepresentativeId": None},
        ]},
        {"$set": {"assignedRepresentativeId": uid}},
    )
    return {
        "success": True,
        "asignados": res.modified_count,
        "usuario": target.get("username") or target.get("clientName"),
        "userId": uid,
    }

@router.put("/clients/{client_id}")
async def update_client(client_id: str, client: ClientUpdate, current_user: dict = Depends(require_auth)):
    """Actualizar un cliente"""
    existing = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    update_data = {k: v for k, v in client.model_dump().items() if v is not None}
    
    if "codigo" in update_data:
        update_data["codigo"] = update_data["codigo"].upper()
        # Check if new codigo conflicts with another client
        conflict = await db.clients.find_one({
            "codigo": update_data["codigo"],
            "id": {"$ne": client_id}
        })
        if conflict:
            raise HTTPException(status_code=400, detail="El código de cliente ya existe")
    
    update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
    
    if update_data:
        await db.clients.update_one({"id": client_id}, {"$set": update_data})
    
    updated = await db.clients.find_one({"id": client_id}, {"_id": 0})
    return updated

@router.delete("/clients/{client_id}")
async def delete_client(client_id: str, force: bool = False, current_user: dict = Depends(require_auth)):
    """Eliminar un cliente. Si force=True, desvincula usuarios automáticamente."""
    # Check if client has linked users
    linked_users = await db.users.count_documents({"linkedClientId": client_id})
    if linked_users > 0:
        if force:
            # Admin force delete: unlink users first
            await db.users.update_many(
                {"linkedClientId": client_id},
                {"$set": {"linkedClientId": None}}
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"No se puede eliminar: {linked_users} usuario(s) vinculado(s). Use force=true para desvincular y eliminar."
            )
    
    result = await db.clients.delete_one({"id": client_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if linked_users > 0 and force:
        return {"message": f"Cliente eliminado. {linked_users} usuario(s) desvinculado(s)."}
    return {"message": "Cliente eliminado"}

@router.post("/clients/import-csv")
async def import_clients_csv(data: dict, current_user: dict = Depends(require_auth)):
    """Importar clientes desde CSV (lista de objetos)"""
    clients_data = data.get("clients", [])
    if not clients_data:
        raise HTTPException(status_code=400, detail="No hay datos para importar")
    
    imported = 0
    updated = 0
    errors = []
    
    for idx, client_row in enumerate(clients_data):
        try:
            codigo = str(client_row.get("codigo", "")).upper().strip()
            if not codigo:
                errors.append(f"Fila {idx+1}: Código vacío")
                continue
            
            client_doc = {
                "codigo": codigo,
                "nombre": str(client_row.get("nombre", "")).strip(),
                "cif": str(client_row.get("cif", "")).strip(),
                "direccion": str(client_row.get("direccion", "")).strip(),
                "localidad": str(client_row.get("localidad", "")).strip(),
                "provincia": str(client_row.get("provincia", "")).strip(),
                "codigoPostal": str(client_row.get("codigoPostal", client_row.get("cp", ""))).strip(),
                "telefono": str(client_row.get("telefono", "")).strip(),
                "email": str(client_row.get("email", "")).strip(),
                "descuento": float(client_row.get("descuento", 0)),
                "activo": client_row.get("activo", True) in [True, "true", "True", 1, "1", "SI", "si", "Sí"],
                "notas": str(client_row.get("notas", "")).strip(),
                "updatedAt": datetime.now(timezone.utc).isoformat()
            }
            
            # Check if exists
            existing = await db.clients.find_one({"codigo": codigo})
            if existing:
                await db.clients.update_one({"codigo": codigo}, {"$set": client_doc})
                updated += 1
            else:
                client_doc["id"] = f"cli-{uuid.uuid4().hex[:8]}"
                client_doc["createdAt"] = datetime.now(timezone.utc).isoformat()
                await db.clients.insert_one(client_doc)
                imported += 1
                
        except Exception as e:
            errors.append(f"Fila {idx+1}: {str(e)}")
    
    return {
        "imported": imported,
        "updated": updated,
        "errors": errors,
        "total": len(clients_data)
    }

@router.post("/clients/from-contact/{contact_id}")
async def create_client_from_contact(contact_id: str, current_user: dict = Depends(require_auth)):
    """Convertir un contacto del CRM en cliente potencial"""
    # Get contact from CRM
    contact = await db.contacts.find_one({"id": contact_id}, {"_id": 0})
    if not contact:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    
    # Check if already converted
    existing = await db.clients.find_one({"origenCrmContactId": contact_id})
    if existing:
        raise HTTPException(status_code=400, detail="Este contacto ya fue convertido a cliente")
    
    # Create client from contact data
    client_data = {
        "id": f"cli-{uuid.uuid4().hex[:8]}",
        "tipo": "potencial",
        "codigo": "",  # Sin código hasta que se active
        "nombre": contact.get("name", ""),
        "cif": "",
        "segmento": "",
        "direccion": contact.get("address", ""),
        "localidad": "",
        "provincia": "",
        "codigoPostal": "",
        "telefono": contact.get("phone", ""),
        "email": contact.get("email", ""),
        "descuento": 0,
        "activo": True,
        "notas": f"Convertido desde contacto CRM: {contact.get('company', '')}\n{contact.get('notes', '')}",
        "origenCrmContactId": contact_id,
        "usuarioVinculadoId": "",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "convertidoAt": None
    }
    
    await db.clients.insert_one(client_data)
    
    # Update contact to mark as converted
    await db.contacts.update_one(
        {"id": contact_id},
        {"$set": {"convertedToClientId": client_data["id"], "status": "customer"}}
    )
    
    if "_id" in client_data:
        del client_data["_id"]
    return client_data

@router.post("/clients/{client_id}/activate")
async def activate_client(client_id: str, data: dict, current_user: dict = Depends(require_auth)):
    """Activar un cliente potencial asignándole código"""
    codigo = data.get("codigo", "").upper().strip()
    if not codigo:
        raise HTTPException(status_code=400, detail="El código es obligatorio para activar")
    
    # Check client exists
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if client.get("tipo") == "activo":
        raise HTTPException(status_code=400, detail="El cliente ya está activo")
    
    # Check code not in use
    existing = await db.clients.find_one({"codigo": codigo, "id": {"$ne": client_id}})
    if existing:
        raise HTTPException(status_code=400, detail="El código ya está en uso por otro cliente")
    
    # Activate
    await db.clients.update_one(
        {"id": client_id},
        {"$set": {
            "tipo": "activo",
            "codigo": codigo,
            "convertidoAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    updated = await db.clients.find_one({"id": client_id}, {"_id": 0})
    return updated

@router.post("/clients/{client_id}/link-user")
async def link_client_to_user(client_id: str, data: dict, current_user: dict = Depends(require_auth)):
    """Vincular un cliente a un usuario del sistema"""
    user_id = data.get("userId", "")
    
    # Verify client exists
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if user_id:
        # Verify user exists
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Update user with client link
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"linkedClientId": client_id}}
        )
    
    # Update client with user link
    await db.clients.update_one(
        {"id": client_id},
        {"$set": {
            "usuarioVinculadoId": user_id,
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    updated = await db.clients.find_one({"id": client_id}, {"_id": 0})
    return updated
