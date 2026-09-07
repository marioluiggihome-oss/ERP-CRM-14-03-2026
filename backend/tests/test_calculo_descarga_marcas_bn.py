# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
from pathlib import Path


SRC = Path(__file__).parents[2] / "frontend/src/components/AIRenderStudio.jsx"


def _source():
    return SRC.read_text(encoding="utf-8")


def test_descarga_con_marcas_usa_la_vista_bn_visible():
    source = _source()
    start = source.index("const descargarConMarcas")
    end = source.index("// Convierte un color hex", start)
    block = source[start:end]
    assert "schematic && bnImage ? bnImage : currentImage()" in block
    assert "const x = dx + (mk.x / 100) * dw, y = dy + (mk.y / 100) * dh" in block
    assert "a.download = `render_instalaciones_" in block


def test_exportacion_reutilizable_mantiene_la_misma_fuente_bn():
    source = _source()
    start = source.index("const renderMarcadoDataUrl")
    end = source.index("const esquemaGremioPDF", start)
    block = source[start:end]
    assert "schematic && bnImage ? bnImage : currentImage()" in block
    assert "const x = dx + (mk.x / 100) * dw, y = dy + (mk.y / 100) * dh" in block
