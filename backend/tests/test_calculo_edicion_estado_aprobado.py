from pathlib import Path


SRC = Path(__file__).parents[2] / "frontend/src/components/AIRenderStudio.jsx"


def test_edicion_envia_base_original_y_ultimo_estado_aprobado():
    source = SRC.read_text(encoding="utf-8")
    start = source.index("const editRender = async")
    end = source.index("const mejorarIluminacion", start)
    block = source[start:end]
    assert "const baseImg = editBaseImage || img;" in block
    assert "EL ÚLTIMO DISEÑO APROBADO ES LA AUTORIDAD VISUAL" in block
    assert "Conserva exactamente todos los elementos" in block
    assert "referenceImage: dataUrl" in block
    assert "referenceImages: [img, ...(editRefImage ? [editRefImage] : [])]" in block


def test_la_nueva_orden_se_separa_de_los_cambios_conservados():
    source = SRC.read_text(encoding="utf-8")
    start = source.index("const editRender = async")
    end = source.index("const mejorarIluminacion", start)
    block = source[start:end]
    assert "CAMBIOS YA APLICADOS QUE DEBES CONSERVAR" in block
    assert "NUEVO CAMBIO QUE DEBES APLICAR AHORA" in block
    assert "setEditAppliedChanges(prev => [...prev, ...allLines])" in block
