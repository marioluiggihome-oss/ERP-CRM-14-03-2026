"""Candados del botón IA0: comparación con el camino del 11/07/2026."""
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RENDER = ROOT / "backend/services/luiggi_ai/render_3d.py"
HISTORICAL = ROOT / "backend/services/luiggi_ai/render_11jul.py"
ESTUDIO = ROOT / "frontend/src/components/EstudioCocinas.jsx"
RENDER_STUDIO = ROOT / "frontend/src/components/AIRenderStudio.jsx"


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


def test_ia1_sigue_siendomotor_gemini_y_ia0_tiene_boton():
    ui = _leer(ESTUDIO)
    assert "if (motorIA === 'ia0') return 'julio11';" in ui
    assert "['ia0','IA 0'" in ui
    assert "const [motorIA, setMotorIA] = useState('ia0');" in ui
    assert "return 'gemini';" in ui


def test_render_studio_visible_para_master_y_envia_ia0():
    ui = _leer(RENDER_STUDIO)
    assert "state?.currentUser?.isMaster === true" in ui
    assert "const [motor, setMotor] = useState('ia0');" in ui
    assert "if (motor === 'ia0') return 'julio11';" in ui
    assert "['ia0', 'IA 0'" in ui


def test_cambios_no_encadenan_renders_degradados():
    ui = _leer(RENDER_STUDIO)
    assert "const [editBaseImage, setEditBaseImage] = useState(null);" in ui
    assert "const baseImg = editBaseImage || img;" in ui
    assert "const dataUrl = editBaseImage || await imageToDataUrl(baseImg);" in ui
    assert "CAMBIOS YA APLICADOS QUE DEBES CONSERVAR" in ui
    assert "setEditAppliedChanges(prev => [...prev, ...allLines]);" in ui
