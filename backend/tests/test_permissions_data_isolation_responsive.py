# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Candados estáticos de permisos, aislamiento documental y responsive.

No dependen de una base de datos activa: verifican contratos de seguridad que deben
seguir presentes en frontend y backend aunque cambie la implementación interna.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend" / "src"
BACKEND = ROOT / "backend"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_matriz_central_cubre_partidas_sensibles():
    src = _text(FRONTEND / "modulePermissions.js")
    expected = {
        "electros": "canAccessElectros",
        "invoices": "canAccessInvoices",
        "gastos": "canAccessGastos",
        "library": "canAccessArchivo",
        "expediente": "canAccessExpediente",
        "almacen": "canAccessAlmacen",
        "armarios": "canAccessArmarios",
        "misPedidos": "canAccessPedidos",
        "visualizer": "canUseAIAnalysis",
        "propdata": "canUsePropData",
    }
    for tab, permission in expected.items():
        assert f"'{tab}':" in src
        assert permission in src
    assert "u?.[key] === true" in src


def test_menu_y_contenido_comparten_autorizador():
    src = _text(FRONTEND / "App.js")
    for tab in ("electros", "invoices", "gastos", "library", "expediente", "almacen"):
        assert f"canOpenTab('{tab}')" in src
    assert "canAccessTab(state.currentTab, state.currentUser" in src
    assert "if (!canAccessTab(state.currentTab, state.currentUser, state.settings))" in src


def test_altas_nuevas_no_reciben_permisos_sensibles_implicitamente():
    src = _text(FRONTEND / "components" / "SettingsModal.jsx")
    for permission in (
        "canAccessElectros", "canAccessInvoices", "canAccessGastos",
        "canAccessArchivo", "canAccessExpediente", "canAccessAlmacen",
        "canViewAllDocuments",
    ):
        assert f"{permission}: false" in src
        assert permission in src
    assert "Ver documentos de todos" in src


def test_guardias_backend_por_partida():
    expectations = {
        "routes/invoices.py": 'require_module_access("canAccessInvoices")',
        "routes/gastos.py": 'require_module_access("canAccessGastos")',
        "routes/almacen.py": 'require_module_access("canAccessAlmacen")',
        "routes/armarios.py": 'require_module_access("canAccessArmarios")',
        "routes/cascos.py": 'require_module_access("canUseCascos")',
        "routes/orders.py": 'require_module_access("canAccessPedidos")',
        "routes/ia_lab.py": 'require_module_access("canUseAIAnalysis")',
        "routes/propdata.py": 'require_module_access("canUsePropData")',
    }
    for relative, guard in expectations.items():
        assert guard in _text(BACKEND / relative)


def test_proyectos_fuerzan_propietario_del_token():
    src = _text(BACKEND / "routes" / "projects.py")
    assert 'project_data["userId"] = owner_id' in src
    assert 'project_data["ownerUserId"] = owner_id' in src
    assert 'return {"userId": uid}' in src
    assert "await _find_project(project_id, current_user)" in src
    assert "delete_one(_project_query(project_id, current_user))" in src
    assert '"userId": user_id' not in src


def test_facturas_y_adjuntos_tienen_ambito_documental():
    src = _text(BACKEND / "routes" / "invoices.py")
    assert "def _scoped_invoice_query" in src
    assert '"ownerUserId": owner_id' in src
    assert "await _find_invoice(invoice_id, current_user)" in src
    assert "invoice_filter=_invoice_scope(current_user)" in src
    assert "_backfill_invoice_ownership" in src
    assert 'invoices.find_one({"id": invoice_id}' not in src


def test_gastos_documentos_e_informes_tienen_propietario():
    src = _text(BACKEND / "routes" / "gastos.py")
    assert '"userId": current_user.get("id")' in src
    assert "def _gasto_scope" in src
    assert "_gasto_query({\"docId\": doc_id}, current_user)" in src
    assert "await _find_informe(informe_id, current_user)" in src
    assert 'str(payload.get("userId")' not in src


def test_almacenamiento_local_comercial_se_separa_por_usuario():
    src = _text(FRONTEND / "components" / "Invoices.jsx")
    assert "documentos_gestor_comercial:${currentUser?.id" in src
    assert "localStorage.getItem(localDocsKey)" in src
    assert "localStorage.setItem(localDocsKey" in src
    assert "localStorage.getItem('documentos_gestor_comercial')" not in src


def test_gestion_comercial_conserva_candados_responsive():
    src = _text(FRONTEND / "components" / "Invoices.jsx")
    for marker in (
        "overflow-x-hidden p-3 sm:p-6",
        "overflow-x-auto pb-1 w-full",
        "w-full sm:w-64 min-w-0",
        "grid grid-cols-1 sm:grid-cols-12",
        "max-h-[92dvh]",
        "showCreateMenu ? 'block' : 'hidden'",
    ):
        assert marker in src


def test_panel_maestro_conserva_candados_responsive():
    src = _text(FRONTEND / "components" / "SettingsModal.jsx")
    assert "max-h-[96dvh] sm:max-h-[90vh]" in src
    assert "grid grid-cols-1 sm:grid-cols-3" in src
    assert "overflow-x-auto sm:overflow-x-hidden" in src
