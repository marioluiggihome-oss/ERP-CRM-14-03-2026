# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
from pathlib import Path


SRC = Path(__file__).parents[2] / "frontend/src/components/AIRenderStudio.jsx"


def test_bn_genera_alzado_tecnico_vectorial_y_no_filtro_de_pixeles():
    source = SRC.read_text(encoding="utf-8")
    assert "B/N no es un filtro fotográfico: genera el ALZADO TÉCNICO" in source
    assert "generarPlanosExactos(distribucion)" in source
    assert "description?.toLowerCase().includes('alzado')" in source
    assert "setBnImage(alzadoImage)" in source
    assert "convertirABnLineal" not in source
    assert "filter: 'grayscale(100%) contrast(115%) brightness(88%)'" not in source
    assert "src={schematic && bnImage ? bnImage" in source
    assert "setBnImage(null)" in source


def test_bn_exige_distribucion_antes_de_generar():
    source = SRC.read_text(encoding="utf-8")
    assert "const distribucion = await deducirDistribucion(motivos, fallos)" in source
    assert "No se pudo obtener la distribución para generar el alzado técnico." in source
    assert "No se pudo generar el alzado técnico en blanco y negro." in source


def test_bn_no_sobrescribe_el_render_original():
    source = SRC.read_text(encoding="utf-8")
    block = source[source.index("const alternarBn"):source.index("// ─── Plano en planta", source.index("const alternarBn"))]
    assert "setRenderResult" not in block
    assert "setOriginal" not in block
    assert "setBnImage(alzadoImage)" in block
