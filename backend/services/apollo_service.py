# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Servicio de prospección B2B basado exclusivamente en datos trazables de Apollo.

No devuelve directorios estáticos, contactos inventados ni resultados generados por IA.
Cada resultado incluye su proveedor, identificador de origen y fecha de consulta.
"""
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger(__name__)
APOLLO_API_URL = "https://api.apollo.io/v1"


def get_apollo_key() -> str:
    """Obtiene una clave Apollo válida desde el entorno del backend."""
    key = os.environ.get("APOLLO_API_KEY", "").strip()
    return "" if key == "eGMaEIMj0rE-g8SnywvDPA" else key


SECTORES_B2B = [
    {"id": "arquitectura", "nombre": "Estudios de Arquitectura", "keywords": ["arquitectura", "arquitecto", "estudio de arquitectura", "architecture", "edificacion"], "job_titles": ["Arquitecto", "Arquitecto Director", "Socio Fundador", "Lead Architect", "Director de Proyectos"], "icon": "Building2"},
    {"id": "interiorismo", "nombre": "Diseño de Interiores y Decoración", "keywords": ["interiorismo", "diseño de interiores", "decoracion", "interior design", "reformas interiores"], "job_titles": ["Interiorista", "Diseñador de Interiores", "Director Creativo", "Interior Designer", "Decorador"], "icon": "Palette"},
    {"id": "reformas", "nombre": "Empresas de Reformas Integrales", "keywords": ["reformas integrales", "rehabilitacion", "obras y reformas", "contratista"], "job_titles": ["Gerente", "Director General", "Jefe de Obras", "Responsable de Compras"], "icon": "Hammer"},
    {"id": "promotoras", "nombre": "Promotoras y Constructoras", "keywords": ["promotora inmobiliaria", "constructora", "promoción residencial", "real estate developer"], "job_titles": ["Director de Compras", "Director Técnico", "Jefe de Compras", "Director de Promociones"], "icon": "Building"},
    {"id": "tiendas", "nombre": "Estudios y Distribuidores de Cocinas", "keywords": ["tienda de cocinas", "estudio de cocinas", "distribuidor muebles"], "job_titles": ["Propietario", "Gerente", "Director Comercial", "Dpto. Prescripción"], "icon": "Store"},
]


def _empty_result(motivo: str, api_configurada: bool, pagina: int, limite: int) -> Dict[str, Any]:
    return {
        "success": True,
        "origen": "sin_fuente_verificable",
        "apiKeyConfigurada": api_configurada,
        "total": 0,
        "totalPaginas": 1,
        "pagina": pagina,
        "limite": limite,
        "prospectos": [],
        "mensaje": motivo,
    }


async def buscar_prospectos_apollo(
    sector: str = "todos",
    ubicacion: str = "España",
    cargo: str = "",
    termino: str = "",
    pagina: int = 1,
    limite: int = 30,
) -> Dict[str, Any]:
    """Busca organizaciones en Apollo, sin inferir ni fabricar datos de contacto.

    Apollo es la única fuente habilitada. Los emails/teléfonos solo se muestran si
    vienen de Apollo y nunca se marcan como verificados sin un estado explícito del proveedor.
    """
    pagina = max(1, int(pagina or 1))
    limite = max(1, min(int(limite or 30), 100))
    api_key = get_apollo_key()
    if not api_key:
        return _empty_result(
            "No hay una fuente B2B activa. Configura una clave oficial de Apollo para consultar datos en vivo.",
            False,
            pagina,
            limite,
        )
    if not httpx:
        return _empty_result("El cliente HTTP del servidor no está disponible para consultar Apollo.", True, pagina, limite)

    sec_cfg = next((s for s in SECTORES_B2B if s["id"] == sector), None)
    keywords = sec_cfg["keywords"] if sec_cfg else ["arquitectura", "interiorismo", "reformas", "promotora"]
    locations = [ubicacion] if ubicacion and ubicacion not in ("España", "Toda España") else ["Spain"]
    payload = {
        "api_key": api_key,
        "q_organization_keyword_tags": keywords[:5],
        "organization_locations": locations,
        "page": pagina,
        "per_page": limite,
    }
    if termino:
        payload["q_organization_name"] = termino

    try:
        headers = {"Content-Type": "application/json", "Cache-Control": "no-cache", "X-Api-Key": api_key}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(f"{APOLLO_API_URL}/organizations/search", json=payload, headers=headers)
        if response.status_code != 200:
            logger.warning("Apollo respondió %s al buscar prospectos", response.status_code)
            return _empty_result("Apollo no ha devuelto resultados válidos. No se mostrará ningún dato sin fuente comprobable.", True, pagina, limite)
        data = response.json()
    except Exception as exc:
        logger.warning("Error consultando Apollo: %s", exc)
        return _empty_result("No se pudo consultar Apollo en este momento. No se muestran datos de respaldo no verificables.", True, pagina, limite)

    consultado_en = datetime.now(timezone.utc).isoformat()
    prospectos = []
    for org in data.get("organizations") or []:
        org_id = str(org.get("id") or "")
        nombre_empresa = (org.get("name") or "").strip()
        if not nombre_empresa or not org_id:
            continue
        domain = (org.get("primary_domain") or "").strip()
        website = (org.get("website_url") or "").strip()
        if not website and domain:
            website = f"https://{domain}"
        prospectos.append({
            "id": f"apollo_org_{org_id}",
            "nombre": nombre_empresa,
            "cargo": "Organización localizada en Apollo",
            "empresa": nombre_empresa,
            "sector": sector if sector != "todos" else "sin_clasificar",
            "ciudad": (org.get("city") or "").strip(),
            "provincia": (org.get("state") or "").strip(),
            "pais": (org.get("country") or "España").strip(),
            "email": "",
            "email_verificado": False,
            "telefono": (org.get("phone") or org.get("sanitized_phone") or "").strip(),
            "telefono_verificado": False,
            "telefono_directo": "",
            "linkedin": (org.get("linkedin_url") or "").strip(),
            "web": website,
            "tamano_empresa": str(org.get("estimated_num_employees") or "No informado"),
            "proyectos_recientes": "Información corporativa procedente de Apollo; revisar antes de contactar.",
            "puntuacion_interes": None,
            "origen": "apollo_live_api",
            "proveedor": "Apollo.io",
            "source_record_id": org_id,
            "source_url": website,
            "consultado_en": consultado_en,
            "importable": True,
        })

    total = int(data.get("pagination", {}).get("total_entries") or data.get("total_entries") or len(prospectos))
    return {
        "success": True,
        "origen": "apollo_live_api",
        "apiKeyConfigurada": True,
        "total": total,
        "totalPaginas": max(1, (total + limite - 1) // limite),
        "pagina": pagina,
        "limite": limite,
        "prospectos": prospectos,
        "mensaje": "Resultados consultados en Apollo.io. Revisa cada dato antes de contactar.",
    }
