from pathlib import Path

SRC = Path(__file__).parents[2] / "frontend/src/components/AIRenderStudio.jsx"

def test_referencias_misma_cocina_tiene_control_real():
    s = SRC.read_text(encoding="utf-8")
    assert "sameProjectRefs" in s
    assert "generará un único render" in s
    assert "referenceImages: refs.slice(1, 3)" in s
    assert "desplegable de abajo" not in s
