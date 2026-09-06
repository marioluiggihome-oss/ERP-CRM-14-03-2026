from pathlib import Path


SRC = Path(__file__).parents[2] / "frontend/src/components/AIRenderStudio.jsx"


def test_bn_genera_una_vista_lineal_de_la_misma_perspectiva():
    source = SRC.read_text(encoding="utf-8")
    assert "B/N convierte el render completo en una única vista lineal EN LA MISMA" in source
    assert "style: 'line-art'" in source
    assert "CONSERVA EXACTAMENTE la misma cámara, perspectiva, encuadre" in source
    assert "Mantén todos los elementos visibles del render" in source
    assert "No conviertas la imagen en alzado, planta, ficha técnica o varios dibujos separados." in source
    assert "No incluyas cotas, números, etiquetas, títulos, flechas, despiece ni texto." in source
    assert "setBnImage(lineImage)" in source
    assert "setSchematic(true)" in source
    assert "generarPlanosExactos(distribucion)" not in source[source.index("const alternarBn"):source.index("// ─── Plano en planta", source.index("const alternarBn"))]


def test_bn_no_sobrescribe_el_render_original():
    source = SRC.read_text(encoding="utf-8")
    block = source[source.index("const alternarBn"):source.index("// ─── Plano en planta", source.index("const alternarBn"))]
    assert "setRenderResult" not in block
    assert "setOriginal" not in block
    assert "referenceImage" in block
    assert "setRenderHistory" in block


def test_bn_no_usa_filtro_gris_local():
    source = SRC.read_text(encoding="utf-8")
    assert "convertirABnLineal" not in source
    assert "filter: 'grayscale(100%) contrast(115%) brightness(88%)'" not in source
