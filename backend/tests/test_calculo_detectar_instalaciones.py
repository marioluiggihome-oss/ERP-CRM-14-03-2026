from pathlib import Path


SRC = Path(__file__).parents[2] / "frontend/src/components/AIRenderStudio.jsx"


def test_detectar_usa_la_imagen_visible_y_no_activa_bn():
    source = SRC.read_text(encoding="utf-8")
    start = source.index("const detectInstalaciones")
    end = source.index("// Genera un GIRO 360º", start)
    block = source[start:end]
    assert "const visibleImage = schematic && bnImage ? bnImage : currentImage();" in block
    assert "shrinkForSave(src)" in block
    assert "setMarks(validas); setMarkTool(null);" in block
    assert "if (validas.length) setSchematic(true)" not in block
    assert "No se localizaron puntos claros" in block


def test_detectar_filtra_por_tipo_de_estancia():
    source = SRC.read_text(encoding="utf-8")
    start = source.index("const detectInstalaciones")
    end = source.index("// Genera un GIRO 360º", start)
    block = source[start:end]
    assert "MARK_TYPES[m.type]?.tipos?.includes(tipo3d)" in block
    assert "setMarks(validas)" in block
