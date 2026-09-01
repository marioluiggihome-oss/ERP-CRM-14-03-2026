"""Candados del botón IA0: comparación con el camino del 11/07/2026."""
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RENDER = ROOT / "backend/services/luiggi_ai/render_3d.py"
HISTORICAL = ROOT / "backend/services/luiggi_ai/render_11jul.py"
ESTUDIO = ROOT / "frontend/src/components/EstudioCocinas.jsx"
RENDER_STUDIO = ROOT / "frontend/src/components/AIRenderStudio.jsx"
AI_ENGINE_ROUTE = ROOT / "backend/routes/ai_engine.py"


def _leer(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_ia0_conserva_el_prompt_de_croquis_del_11_de_julio():
    src = re.sub(r'"\s*\n\s*"', "", _leer(HISTORICAL))
    for frase in (
        "A HAND-DRAWN FLOOR PLAN / SKETCH has been attached",
        "reproduce the EXACT distribution shown in the sketch",
        "the NUMBER and ORDER of modules from left to right",
        "the POSITION of each appliance",
        "and the TALL COLUMNS",
        "The sketch is NOT decorative — it is a TECHNICAL blueprint",
        "The proportions and widths of each module must match the sketch",
    ):
        assert frase in src


def test_ia0_no_incorpora_reglas_de_agosto():
    src = re.sub(r'"\s*\n\s*"', "", _leer(HISTORICAL))
    for frase in (
        "FRONT-BY-FRONT FIDELITY",
        "EXACT MODULE LIST",
        "recortar_dibujo_base64",
        "_leer_cocina_del_dibujo",
        "ONLY THE DRAWING COUNTS",
    ):
        assert frase not in src


def test_ia0_esta_aislada_y_fuerza_modelo_historico():
    src = _leer(RENDER)
    assert 'provider == "julio11"' in src
    assert 'provider="julio11"' in src
    assert 'model_override="gemini-3-pro-image-preview"' in src
    assert 'parsed_params["motor"] = "IA 0 — camino del 11/07/2026"' in src


def test_ia0_es_interna_y_predeterminada_en_estudio_cocinas():
    ui = _leer(ESTUDIO)
    assert "if (motorIA === 'ia0') return 'julio11';" in ui
    assert "const [motorIA, setMotorIA] = useState('ia0');" in ui
    assert "return 'gemini';" in ui
    assert "['ia0','IA 0'" not in ui


def test_ia0_es_interna_y_predeterminada_en_render_studio():
    ui = _leer(RENDER_STUDIO)
    assert "const [motor, setMotor] = useState('ia0');" in ui
    assert "if (motor === 'ia0') return 'julio11';" in ui
    assert "['ia0', 'IA 0'" not in ui
    assert "Render 3D IA" not in ui


def test_cambios_no_encadenan_renders_degradados():
    ui = _leer(RENDER_STUDIO)
    assert "const [editBaseImage, setEditBaseImage] = useState(null);" in ui
    assert "const baseImg = editBaseImage || img;" in ui
    assert "const dataUrl = editBaseImage || await imageToDataUrl(baseImg);" in ui
    assert "CAMBIOS YA APLICADOS QUE DEBES CONSERVAR" in ui
    assert "setEditAppliedChanges(prev => [...prev, ...allLines]);" in ui


def test_api_no_expone_metadatos_tecnicos_del_render():
    src = _leer(AI_ENGINE_ROUTE)
    for campo in ("engine", "provider", "prompt_used", "model", "motorUsado", "motorDeRespaldo"):
        assert f'"{campo}"' in src
    assert "def limpiar_respuesta_render" in src
    assert src.count("return limpiar_respuesta_render(result)") >= 5
    assert "return limpiar_respuesta_render(final)" in src


def test_interfaz_filtra_errores_tecnicos_del_servidor():
    studio = _leer(RENDER_STUDIO)
    cocinas = _leer(ESTUDIO)
    assert "const mensajePublico" in studio
    assert "const mensajePublico" in cocinas
    assert "OpenAI|Anthropic|Claude|Flux|Banana|motor|modelo|proveedor|provider" in studio
    assert "OpenAI|Anthropic|Claude|Flux|Banana|motor|modelo|proveedor|provider" in cocinas


def test_ia7_es_ia0_mas_geometria_y_vanos_sin_tocar_ia0():
    src = _leer(RENDER)
    historico = _leer(HISTORICAL)
    assert 'provider == "julio11_plus"' in src
    assert 'provider="julio11_plus"' in src
    assert "prompt_del_croquis_22jul" in src
    assert "Preserve every window and door at the SAME position, width and height" in src
    assert "Geometry comes 100% from the drawings" in src
    assert 'model_override="gemini-3-pro-image-preview"' in src
    # IA0 continúa dependiendo exclusivamente de su módulo congelado.
    assert "prompt_del_croquis_11jul" in src
    assert "A HAND-DRAWN FLOOR PLAN / SKETCH" in historico


def test_ia7_mejora_la_calidad_de_entrada_sin_cambiar_el_perfil_estable():
    backend = _leer(RENDER)
    ui = _leer(RENDER_STUDIO)
    assert 'dpi_referencia = 280 if provider == "julio11_plus" else 150' in backend
    assert "await downscaleImage(file, 3000, 0.96, 'image/png')" in ui
    assert "const [motor, setMotor] = useState('ia0');" in ui
    assert "if (motor === 'ia7') return 'julio11_plus';" in ui


def test_comparar_pdf_usa_preview_sin_sustituir_el_original():
    ruta = _leer(AI_ENGINE_ROUTE)
    ui = _leer(RENDER_STUDIO)
    assert '@ai_engine_router.post("/pdf-preview")' in ruta
    assert "pdf_base64_to_png_base64(stripped, dpi=180, max_pages=1)" in ruta
    assert "const [pdfComparePreview, setPdfComparePreview] = useState(null);" in ui
    assert "body: JSON.stringify({ fileBase64: referencia })" in ui
    assert "pdfComparePreview || originalRef || refImage" in ui
    assert "setOriginalRef(prev => prev || b64)" in ui


def test_botonera_ia_es_solo_master_y_mantiene_ia0_por_defecto():
    ui = _leer(RENDER_STUDIO)
    inicio = ui.index("{isMaster && (", ui.index("Acción principal"))
    fin = ui.index("</div>\n                )}", inicio)
    botonera = ui[inicio:fin]
    for perfil in ("IA0", "IA1", "IA3", "IA5", "IA7"):
        assert f"'{perfil}'" in botonera
    assert "const [motor, setMotor] = useState('ia0');" in ui
    assert "Probar mejoras" not in ui
    assert "Prueba activa" not in ui
    assert ">Motor<" not in ui
