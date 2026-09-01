"""Candados del perfil CONTROLLER exclusivo solicitado para Jenaro."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend" / "src"
BACKEND = ROOT / "backend"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_controller_tiene_carcasa_exclusiva_aunque_haya_permisos_heredados():
    app = text(FRONTEND / "App.js")
    permissions = text(FRONTEND / "modulePermissions.js")
    assert "const _soloControllerUI = !!_u.isController" in app
    controller_condition = app[app.index("const _soloControllerUI"):app.index("if (_soloControllerUI)")]
    assert "_hasOtherAccess" not in controller_condition
    assert "if (esControllerExclusivo(u)) return tab === 'rentabilidad'" in permissions


def test_guardia_backend_impide_otros_modulos_a_controller():
    src = text(BACKEND / "services" / "jwt_service.py")
    assert 'es_controller_exclusivo = bool(user.get("isController"))' in src
    assert 'if flag_name == "canAccessRentabilidad"' in src
    assert 'raise HTTPException(status_code=403, detail="Perfil de consulta sin acceso a este módulo")' in src


def test_rentabilidad_falla_cerrada_y_controller_solo_puede_leer():
    src = text(BACKEND / "routes" / "rentabilidad.py")
    assert "_RENTA_DEPS = [Depends(require_rentabilidad), Depends(solo_lectura_controller)]" in src
    assert 'request.method.upper() not in ("GET", "HEAD", "OPTIONS")' in src
    assert "fallback si no hay jwt_service" not in src
    assert "_RENTA_DEPS = []" not in src


def test_panel_controller_oculta_escrituras_pero_conserva_adjuntos():
    src = text(FRONTEND / "components" / "RentabilidadPanel.jsx")
    assert "const soloLectura = !!currentUser?.isController" in src
    assert "!soloLectura && <div" in src
    assert "!soloLectura && <button onClick={() => delCost" in src
    assert "verCostDoc(c.docId)" in src
    assert "verIngresoDoc(i.docId)" in src
    assert "c.docId && <button onClick={() => verCostDoc" in src


def test_listado_controller_no_muestra_convertir_revisar_desmarcar_ni_borrar():
    src = text(FRONTEND / "components" / "RentabilidadLineas.jsx")
    assert "!soloLectura && NEXT_DOC_TYPE" in src
    assert "!soloLectura && f.docType === 'factura'" in src
    assert "!soloLectura && (bloqueada(f)" in src
    assert "disabled={soloLectura}" in src
    assert "!soloLectura && <>" in src


def test_asignar_controller_limpia_todos_los_demas_permisos():
    frontend = text(FRONTEND / "components" / "SettingsModal.jsx")
    users = text(BACKEND / "routes" / "users.py")
    assert "controllerOnlyForm(userForm, e.target.checked)" in frontend
    assert "def enforce_controller_only(data: dict)" in users
    assert 'if key.startswith("can") or key in _CONTROLLER_ROLE_FIELDS' in users
    assert '"canAccessRentabilidad": True' in users
    assert '"canViewAllDocuments": False' in users
    assert '"allowedModules": []' in users
    assert "controller_only_updates({**existing, **update_data})" in users


def test_jenaro_se_normaliza_en_despliegue_y_en_recreacion():
    server = text(BACKEND / "server.py")
    seed = text(BACKEND / "scripts" / "seed_comerciales.py")
    assert '"$regex": "^JENARO$"' in server
    assert "controller_only_updates(_jenaro)" in server
    assert 'c["username"].upper() == "JENARO"' in seed
    assert '"isController": True' in seed
    assert '"canAccessRentabilidad": True' in seed


def test_controller_lista_solo_facturas_revisadas_por_master():
    src = text(BACKEND / "routes" / "rentabilidad.py")
    assert 'query.update({"docType": "factura", "revisada": True})' in src
    assert "master_ids, master_names = await _master_reviewer_identities()" in src
    assert "if _reviewed_by_master(ficha, master_ids, master_names)" in src
    assert '"revisadaPorUserId": (user or {}).get("id", "")' in src
    assert '"revisadaPorMaster": _is_master_user(user)' in src


def test_revisiones_historicas_se_reconocen_sin_modificar_al_consultar():
    src = text(BACKEND / "routes" / "rentabilidad.py")
    helper = src[src.index("def _reviewed_by_master"):src.index("def _check_doc_size")]
    assert 'reviewer_name = str(ficha.get("revisadaPor")' in helper
    assert "reviewer_name in master_names" in helper
    list_block = src[src.index('@router.get("/rentabilidad/fichas")'):src.index('@router.get("/rentabilidad/fichas/{ficha_id}")')]
    assert "update_one" not in list_block
    assert "insert_one" not in list_block
    assert "delete_one" not in list_block


def test_detalle_y_adjuntos_validan_la_factura_master_visible():
    src = text(BACKEND / "routes" / "rentabilidad.py")
    assert "async def get_ficha(ficha_id: str, user: dict = Depends(require_rentabilidad))" in src
    assert "async def get_ficha_doc(ficha_id: str, doc_id: str, user: dict = Depends(require_rentabilidad))" in src
    assert 'raise HTTPException(status_code=404, detail="Ficha no disponible")' in src
    assert 'raise HTTPException(status_code=404, detail="Documento no disponible")' in src


def test_costes_ingresos_y_sus_adjuntos_quedan_en_el_mismo_ambito():
    src = text(BACKEND / "routes" / "rentabilidad.py")
    assert "async def _controller_visible_invoice_scope()" in src
    assert "async def list_project_costs(projectRef: Optional[str] = None, user: dict = Depends(require_rentabilidad))" in src
    assert "async def get_project_cost_doc(doc_id: str, user: dict = Depends(require_rentabilidad))" in src
    assert "async def list_ingresos(userId: Optional[str] = None, user: dict = Depends(require_rentabilidad))" in src
    assert "async def get_ingreso_doc(doc_id: str, user: dict = Depends(require_rentabilidad))" in src
    assert "visible_refs = await _controller_visible_invoice_scope()" in src


def test_frontend_envia_sesion_y_no_carga_metricas_globales_a_controller():
    lineas = text(FRONTEND / "components" / "RentabilidadLineas.jsx")
    panel = text(FRONTEND / "components" / "RentabilidadPanel.jsx")
    assert "fichas${qs}`, { headers: authHeaders() }" in lineas
    assert "fichas/${id}`, { headers: authHeaders() }" in lineas
    assert "docs/${docId}`, { headers: authHeaders() }" in lineas
    assert "if (soloLectura)" in panel
    assert "setAnalytics(null)" in panel
    assert "rentabilidad/ingresos`, { headers: authH }" in panel
    assert "project-costs?projectRef=${encodeURIComponent(row.ref)}`, { headers: authH }" in panel
