"""
Clients router
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime, timezone
import uuid

from models.client import ClientCreate, ClientUpdate, CLIENT_SEGMENTS
from services.database import db

router = APIRouter(prefix="/api", tags=["clients"])


@router.get("/clients")
async def get_clients(activo: Optional[bool] = None, search: Optional[str] = None):
    """Get all clients"""
    query = {}
    if activo is not None:
        query["activo"] = activo
    
    clients = await db.clients.find(query, {"_id": 0}).to_list(5000)
    
    if search:
        search_lower = search.lower()
        clients = [c for c in clients if 
            search_lower in c.get("codigo", "").lower() or
            search_lower in c.get("nombre", "").lower() or
            search_lower in c.get("cif", "").lower() or
            search_lower in c.get("localidad", "").lower()
        ]
    
    return clients


@router.get("/clients/segments")
async def get_client_segments():
    """Get available client segments"""
    return {"segments": CLIENT_SEGMENTS}


@router.get("/clients/{client_id}")
async def get_client(client_id: str):
    """Get a client by ID"""
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return client


@router.post("/clients")
async def create_client(client: ClientCreate):
    """Create a new client"""
    if client.codigo and client.codigo.strip():
        existing = await db.clients.find_one({"codigo": client.codigo.upper()})
        if existing:
            raise HTTPException(status_code=400, detail="El código de cliente ya existe")
    
    client_data = client.model_dump()
    client_data["id"] = f"cli-{uuid.uuid4().hex[:8]}"
    client_data["codigo"] = client_data["codigo"].upper()
    client_data["createdAt"] = datetime.now(timezone.utc).isoformat()
    client_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
    
    await db.clients.insert_one(client_data)
    
    if "_id" in client_data:
        del client_data["_id"]
    return client_data


@router.put("/clients/{client_id}")
async def update_client(client_id: str, client: ClientUpdate):
    """Update a client"""
    existing = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    update_data = {k: v for k, v in client.model_dump().items() if v is not None}
    
    if "codigo" in update_data:
        update_data["codigo"] = update_data["codigo"].upper()
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
async def delete_client(client_id: str):
    """Delete a client"""
    linked_users = await db.users.count_documents({"linkedClientId": client_id})
    if linked_users > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede eliminar: {linked_users} usuario(s) vinculado(s)"
        )
    
    result = await db.clients.delete_one({"id": client_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"message": "Cliente eliminado"}


@router.post("/clients/import-csv")
async def import_clients_csv(data: dict):
    """Import clients from CSV"""
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
async def create_client_from_contact(contact_id: str):
    """Convert a CRM contact to a potential client"""
    contact = await db.contacts.find_one({"id": contact_id}, {"_id": 0})
    if not contact:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    
    existing = await db.clients.find_one({"origenCrmContactId": contact_id})
    if existing:
        raise HTTPException(status_code=400, detail="Este contacto ya fue convertido a cliente")
    
    client_data = {
        "id": f"cli-{uuid.uuid4().hex[:8]}",
        "tipo": "potencial",
        "codigo": "",
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
    
    await db.contacts.update_one(
        {"id": contact_id},
        {"$set": {"convertedToClientId": client_data["id"], "status": "customer"}}
    )
    
    if "_id" in client_data:
        del client_data["_id"]
    return client_data


@router.post("/clients/{client_id}/activate")
async def activate_client(client_id: str, data: dict):
    """Activate a potential client by assigning a code"""
    codigo = data.get("codigo", "").upper().strip()
    if not codigo:
        raise HTTPException(status_code=400, detail="El código es obligatorio para activar")
    
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if client.get("tipo") == "activo":
        raise HTTPException(status_code=400, detail="El cliente ya está activo")
    
    existing = await db.clients.find_one({"codigo": codigo, "id": {"$ne": client_id}})
    if existing:
        raise HTTPException(status_code=400, detail="El código ya está en uso por otro cliente")
    
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
async def link_client_to_user(client_id: str, data: dict):
    """Link a client to a system user"""
    user_id = data.get("userId", "")
    
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if user_id:
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"linkedClientId": client_id}}
        )
    
    await db.clients.update_one(
        {"id": client_id},
        {"$set": {
            "usuarioVinculadoId": user_id,
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    updated = await db.clients.find_one({"id": client_id}, {"_id": 0})
    return updated
