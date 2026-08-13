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
    origen: Optional[str] = ""
    proveedor: Optional[str] = ""
    source_record_id: Optional[str] = ""
    source_url: Optional[str] = ""
    consultado_en: Optional[str] = ""


@router.get("/status")
async def get_apollo_status():
    """Comprueba el estado de la integración de Apollo."""
    key = get_apollo_key()
    return {
        "success": True,
        "configurado": bool(key),
        "modo": "api_oficial" if key else "sin_fuente_configurada",
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
        if req.origen != "apollo_live_api" or not req.source_record_id:
            raise HTTPException(status_code=400, detail="Solo se pueden importar resultados trazables obtenidos en vivo desde Apollo.")
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
            "tags": ["Apollo B2B", "Pendiente de verificación", req.sector.capitalize() if req.sector else "Sin clasificar"],
            "notes": req.notas or f"Organización importada desde Apollo.io. Revisar datos de contacto antes de cualquier acción comercial.",
            "source": "Apollo.io",
            "prospecting": {
                "provider": req.proveedor or "Apollo.io",
                "origin": req.origen,
                "sourceRecordId": req.source_record_id,
                "sourceUrl": req.source_url,
                "consultedAt": req.consultado_en,
                "dataQuality": "pendiente_verificacion_manual",
                "emailVerified": False,
                "phoneVerified": False,
            },
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
            "value": 0.0,
            "probability": 0,
            "expectedCloseDate": "",
            "notes": "Lead de prospección pendiente de verificación manual. No representa una oportunidad cualificada todavía.",
            "source": "Apollo.io",
            "priority": "normal",
            "prospecting": nuevo_contacto["prospecting"],
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
            "subject": "Organización B2B importada desde Apollo.io",
            "description": f"Se ha dado de alta a {req.empresa} desde Apollo.io. Datos pendientes de verificación manual antes de contactar.",
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


@router.get("/audit-crm")
async def audit_apollo_contacts(current_user: Optional[dict] = Depends(get_current_user)):
    """Resume la trazabilidad de los contactos de prospección ya existentes, sin modificarlos."""
    db = _get_db()
    query = {"$or": [{"source": "Apollo B2B"}, {"source": "Apollo.io"}, {"tags": "Apollo B2B"}]}
    total = await db.crm_contacts.count_documents(query)
    trazables = await db.crm_contacts.count_documents({**query, "prospecting.sourceRecordId": {"$exists": True, "$ne": ""}})
    return {
        "success": True,
        "totalProspeccionB2B": total,
        "conTrazabilidadIndividual": trazables,
        "pendientesDeRevision": max(0, total - trazables),
        "mensaje": "Los registros sin identificador de proveedor se consideran pendientes de verificación; esta auditoría no borra ni altera datos.",
    }
