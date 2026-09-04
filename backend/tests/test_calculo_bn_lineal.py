from pathlib import Path


SRC = Path(__file__).parents[2] / "frontend/src/components/AIRenderStudio.jsx"


def test_bn_convierte_la_imagen_actual_a_lineas_sin_filtro_gris():
    source = SRC.read_text(encoding="utf-8")
    assert "convertirABnLineal" in source
    assert "src={schematic && bnImage ? bnImage" in source
    assert "filter: 'grayscale(100%) contrast(115%) brightness(88%)'" not in source
    assert "Convierte el dibujo actual en líneas negras sobre fondo blanco" in source
    assert "setBnImage(null)" in source
