# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import sys


# Los servicios validan JWT al importar; la suite es unitaria y no usa este valor
# para emitir tokens ni conectarse a producción.
os.environ.setdefault("JWT_SECRET", "test-platform-isolation-secret-please-do-not-use")

BACKEND = Path(__file__).resolve().parents[1]
FRONTEND = BACKEND.parent / "frontend" / "src"
sys.path.insert(0, str(BACKEND))

from services.master import desactivar_rescate
from services.plataformas import (
    CARPINTER,
    COOPERATIVA,
    STUDIO3K,
    entrada_permitida,
    normalizar_usuario_plataforma,
    organizacion_de,
    plataforma_de,
    plataforma_entrada,
    suscripcion_permitida,
)


def test_plataforma_heredada_y_organizacion_se_deducen_de_los_vinculos():
    assert plataforma_de({"isCarpintero": True}) == CARPINTER
    assert plataforma_de({"linkedStudio3kAdminId": "studio-root"}) == STUDIO3K
    assert organizacion_de({"linkedStudio3kAdminId": "studio-root"}) == "studio-root"
    assert plataforma_de({}) == COOPERATIVA


def test_normalizacion_exclusiva_limpia_flags_y_vinculos_de_la_otra_marca():
    normalized = normalizar_usuario_plataforma(
        {"plataforma": STUDIO3K, "linkedStudio3kAdminId": "studio-root"},
        {"isCarpintero": True, "linkedCarpinteroAdminId": "carp-root"},
    )
    assert normalized["plataforma"] == STUDIO3K
    assert normalized["isStudio3k"] is True
    assert normalized["isCarpintero"] is False
    assert normalized["linkedCarpinteroAdminId"] is None
    assert normalized["organizationId"] == "studio-root"


def test_entrada_comercial_solo_acepta_su_marca_y_master_conserva_soporte():
    carp = {"id": "c1", "plataforma": CARPINTER}
    studio = {"id": "s1", "plataforma": STUDIO3K}
    master = {"id": "m1", "isMaster": True, "plataforma": COOPERATIVA}
    assert plataforma_entrada("carpinteros") == CARPINTER
    assert plataforma_entrada("s3k") == STUDIO3K
    assert entrada_permitida(carp, "carpinter")
    assert not entrada_permitida(carp, "studio3k")
    assert entrada_permitida(studio, "studio3k")
    assert entrada_permitida(master, "studio3k")


def test_suscripcion_bloquea_estados_y_fecha_vencida_pero_no_cuentas_heredadas():
    desactivar_rescate()
    assert suscripcion_permitida({"plataforma": CARPINTER})
    assert not suscripcion_permitida({"plataforma": CARPINTER, "subscriptionStatus": "suspended"})
    assert not suscripcion_permitida({"plataforma": STUDIO3K, "subscriptionStatus": "cancelled"})
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
    assert not suscripcion_permitida({"plataforma": CARPINTER, "accessExpirationDate": yesterday})
    assert suscripcion_permitida({"plataforma": CARPINTER, "subscriptionStatus": "suspended", "isMaster": True})


def test_backend_de_estudio_3d_registra_y_valida_propietario():
    source = (BACKEND / "routes" / "estudio_cocinas.py").read_text()
    assert '"estudio3d_task_owners"' in source
    assert '"organizationId": organizacion_de(current_user)' in source
    assert "async def _exigir_tarea_propia" in source
    assert 'await _exigir_tarea_propia(task_id, current_user)' in source
    assert 'async def galeria_eliminar(render_id: str, current_user: dict = Depends(require_auth))' in source
    assert 'query["userId"] = str(current_user.get("id") or "")' in source


def test_proyectos_3d_solo_tienen_alcance_global_para_master():
    source = (BACKEND / "routes" / "ai_engine.py").read_text()
    assert '"organizationId": (existing or {}).get("organizationId") or organizacion_de(owner)' in source
    assert "async def _design_accesible" in source
    assert "if not es_dueno and not es_master(current_user):" in source
    assert 'async def list_render_designs(current_user: dict = Depends(require_auth))' in source


def test_packs_conservan_marca_organizacion_y_retorno_simulado():
    packs = (BACKEND / "routes" / "render_packs.py").read_text()
    stripe = (BACKEND / "services" / "stripe_pagos.py").read_text()
    assert 'base.rstrip("/") + "/carp/app"' in packs
    assert 'base.rstrip("/") + "/s3k/app"' in packs
    assert '"organizationId": datos.get("organization_id") or ""' in packs
    assert '"plataforma": str(meta.get("plataforma") or "cooperativa")' in stripe


def test_detector_de_marca_soporta_subrutas_simuladas():
    source = (FRONTEND / "platformEntry.js").read_text()
    assert "path.startsWith('/carp/')" in source
    assert "path.startsWith('/s3k/')" in source
    assert "document.title = entry.title" in source


def test_panel_de_suscripciones_filtra_y_muestra_estado_sin_proveedor():
    source = (FRONTEND / "components" / "settings" / "SubscriptionTab.jsx").read_text()
    assert "platformFilter" in source
    assert "organizationFilter" in source
    assert "subscription_status: subscriptionStatus" in source
    assert "access_expiration_date: expirationDate || null" in source
    assert "Gemini Pro Image" not in source
    assert "Control global por plataforma, organización, plan, vigencia y usuario" in source


if __name__ == "__main__":
    raise SystemExit("Usa pytest para ejecutar esta suite")
