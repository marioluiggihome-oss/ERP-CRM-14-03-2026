# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Rutas de API para Prospección B2B con Apollo AI / Apollo.io.
Permite buscar arquitectos, interioristas y empresas de reformas e importarlos al CRM con un clic.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import logging

from services.db_client import get_db as _get_db
from services.jwt_service import require_auth, get_current_user
from services.apollo_service import (
    buscar_prospectos_apollo,
    SECTORES_B2B,
    get_apollo_key
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/apollo", tags=["Apollo B2B Prospección"], dependencies=[Depends(require_auth)])


class ApolloSearchRequest(BaseModel):
    sector: Optional[str] = "todos"
    ubicacion: Optional[str] = "España"
    cargo: Optional[str] = ""
    termino: Optional[str] = ""
    pagina: Optional[int] = 1
    limite: Optional[int] = 20


class ApolloImportRequest(BaseModel):
    id: str
    nombre: str
    cargo: Optional[str] = ""
    empresa: str
    sector: Optional[str] = "arquitectura"
    ciudad: Optional[str] = ""
    provincia: Optional[str] = ""
    email: Optional[str] = ""
    telefono: Optional[str] = ""
    telefono_directo: Optional[str] = ""
    linkedin: Optional[str] = ""
    web: Optional[str] = ""
    notas: Optional[str] = ""


@router.get("/status")
async def get_apollo_status():
    """Comprueba el estado de la integración de Apollo."""
    key = get_apollo_key()
    return {
        "success": True,
        "configurado": bool(key),
        "modo": "api_oficial" if key else "directorio_oficial_verificado",
        "sectoresDisponibles": len(SECTORES_B2B)
    }


class ApolloKeyRequest(BaseModel):
    apiKey: str


@router.post("/set-key")
async def set_apollo_key(req: ApolloKeyRequest):
    """Guarda la clave de API oficial de Apollo.io en el entorno."""
    import os
    os.environ["APOLLO_API_KEY"] = req.apiKey.strip()
    return {
        "success": True,
        "configurado": bool(req.apiKey.strip()),
        "mensaje": "Clave de Apollo.io configurada correctamente para búsquedas en vivo." if req.apiKey.strip() else "Clave eliminada. Se usará el directorio oficial verificado."
    }


@router.get("/sectores")
async def get_apollo_sectores():
    """Devuelve el catálogo de sectores B2B configurados."""
    return {
        "success": True,
        "sectores": SECTORES_B2B
    }


@router.post("/search")
async def search_apollo_prospects(req: ApolloSearchRequest):
    """Busca contactos B2B según los filtros seleccionados."""
    try:
        resultado = await buscar_prospectos_apollo(
            sector=req.sector or "todos",
            ubicacion=req.ubicacion or "España",
            cargo=req.cargo or "",
            termino=req.termino or "",
            pagina=req.pagina or 1,
            limite=req.limite or 20
        )
        return resultado
    except Exception as e:
        logger.error(f"Error en búsqueda de Apollo: {e}")
        raise HTTPException(status_code=500, detail=f"Error realizando búsqueda B2B: {str(e)}")


@router.post("/importar-crm")
async def import_prospect_to_crm(req: ApolloImportRequest, current_user: Optional[dict] = Depends(get_current_user)):
    """Importa un prospecto de Apollo directamente a la base de datos de Contactos y Oportunidades del CRM."""
    try:
        db = _get_db()
        user_id = (current_user or {}).get("id") or "anonymous"
        user_name = (current_user or {}).get("username") or (current_user or {}).get("clientName") or "Comercial"
        now = datetime.now(timezone.utc).isoformat()

        # Comprobar si ya existe el contacto por email o nombre de empresa
        query_existente = {}
        if req.email and req.email.strip():
            query_existente = {"email": req.email.strip().lower()}
        elif req.empresa and req.nombre:
            query_existente = {"company": req.empresa.strip(), "name": req.nombre.strip()}

        if query_existente:
            existente = await db.crm_contacts.find_one(query_existente, {"_id": 0, "id": 1, "name": 1})
            if existente:
                return {
                    "success": True,
                    "yaExistia": True,
                    "contactId": existente.get("id"),
                    "mensaje": f"El contacto '{req.nombre}' ({req.empresa}) ya existe en el CRM."
                }

        # 1. Crear Contacto en crm_contacts
        contact_id = f"cnt-{uuid.uuid4().hex[:10]}"
        nuevo_contacto = {
            "id": contact_id,
            "name": req.nombre.strip(),
            "company": req.empresa.strip(),
            "position": req.cargo.strip(),
            "email": (req.email or "").strip().lower(),
            "phone": (req.telefono_directo or req.telefono or "").strip(),
            "address": f"{req.ciudad}, {req.provincia}".strip(", "),
            "city": req.ciudad or "",
            "state": req.provincia or "",
            "country": "España",
            "website": req.web or "",
            "linkedin": req.linkedin or "",
            "status": "active",
            "tags": ["Apollo B2B", req.sector.capitalize() if req.sector else "Arquitectura", "Prescriptor"],
            "notes": req.notas or f"Prospecto importado desde Apollo AI. Cargo: {req.cargo}. Sector: {req.sector}.",
            "source": "Apollo B2B",
            "createdByUserId": user_id,
            "createdByName": user_name,
            "assignedTo": user_name,
            "assignedToId": user_id,
            "createdAt": now,
            "updatedAt": now
        }
        await db.crm_contacts.insert_one(nuevo_contacto)

        # 2. Crear Oportunidad inicial en el Pipeline
        opp_id = f"opp-{uuid.uuid4().hex[:10]}"
        nueva_oportunidad = {
            "id": opp_id,
            "title": f"Colaboración B2B - {req.empresa}",
            "contactId": contact_id,
            "contactName": req.nombre,
            "company": req.empresa,
            "stage": "lead",  # Etapa inicial del pipeline
            "value": 15000.0, # Estimación inicial de valor de proyecto
            "probability": 25,
            "expectedCloseDate": "",
            "notes": f"Contacto profesional ({req.cargo}). Presentación de catálogo de cocinas Luiggi Home y dossier para arquitectos/interioristas.",
            "source": "Apollo B2B",
            "priority": "high",
            "createdByUserId": user_id,
            "createdByName": user_name,
            "assignedTo": user_name,
            "assignedToId": user_id,
            "createdAt": now,
            "updatedAt": now
        }
        await db.crm_opportunities.insert_one(nueva_oportunidad)

        # 3. Registrar actividad en historial
        act_id = f"act-{uuid.uuid4().hex[:10]}"
        nueva_actividad = {
            "id": act_id,
            "contactId": contact_id,
            "opportunityId": opp_id,
            "type": "note",
            "subject": "Prospecto B2B importado desde Apollo AI",
            "description": f"Se ha dado de alta a {req.nombre} ({req.cargo} en {req.empresa}) desde la búsqueda de Apollo B2B.",
            "status": "completed",
            "date": now,
            "createdByUserId": user_id,
            "createdByName": user_name,
            "createdAt": now
        }
        await db.crm_activities.insert_one(nueva_actividad)

        return {
            "success": True,
            "yaExistia": False,
            "contactId": contact_id,
            "opportunityId": opp_id,
            "mensaje": f"¡{req.nombre} ({req.empresa}) importado con éxito al CRM!"
        }
    except Exception as e:
        logger.error(f"Error importando contacto de Apollo: {e}")
        raise HTTPException(status_code=500, detail=f"Error al importar contacto: {str(e)}")
