from pathlib import Path


SRC = Path(__file__).parents[2] / "frontend/src/components/AIRenderStudio.jsx"


def test_boton_mas_luz_preserva_diseno_y_usa_edicion_original():
    source = SRC.read_text(encoding="utf-8")
    start = source.index("const mejorarIluminacion")
    end = source.index("const resetEditChain", start)
    block = source[start:end]
    assert "Mejora ÚNICAMENTE la iluminación" in block
    assert "misma distribución" in block
    assert "distribución, cámara" in block
    assert "No añadas ni elimines ventanas o luminarias" in block


def test_edicion_acepta_accion_rapida_sin_romper_historial():
    source = SRC.read_text(encoding="utf-8")
    start = source.index("const editRender = async")
    end = source.index("const mejorarIluminacion", start)
    block = source[start:end]
    assert "forcedLines = null" in block
    assert "const allLines = forcedLines ||" in block
    assert "setEditAppliedChanges(prev => [...prev, ...allLines])" in block
