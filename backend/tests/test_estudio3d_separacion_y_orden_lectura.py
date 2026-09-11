from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NORMAL = ROOT / "frontend/src/components/AIRenderStudio.jsx"
PREMIUM = ROOT / "frontend/src/components/Estudio3DLab.jsx"


def test_estudio_normal_prioriza_render_y_deja_croquis_como_respaldo():
    source = NORMAL.read_text(encoding="utf-8")
    start = source.index("const deducirDistribucion")
    end = source.index("const detectarDistribucion", start)
    block = source[start:end]
    assert block.index("const img = currentImage()") < block.index("const croquis = originalRef || refImage")
    assert "Premium mantiene su propio" in block


def test_premium_no_comparte_sesion_con_estudio_normal():
    source = PREMIUM.read_text(encoding="utf-8")
    assert "leerSesion(estadoRef.current, 'estudio3dPremium')" in source
    assert "guardarSesion(f, 'estudio3dPremium', sesionRef.current)" in source
    assert "leerSesion(estadoRef.current, 'estudio3d')" not in source
    assert "guardarSesion(f, 'estudio3d', sesionRef.current)" not in source


def test_premium_no_consumo_el_preset_del_estudio_normal():
    source = PREMIUM.read_text(encoding="utf-8")
    assert "state?.estudio3dPremiumPreset" in source
    assert "const { estudio3dPremiumPreset, ...rest }" in source
    assert "state?.estudio3dPreset" not in source
    assert "const { estudio3dPreset, ...rest }" not in source
