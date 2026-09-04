import os


RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ESTUDIO = os.path.join(RAIZ, "frontend", "src", "components", "EstudioCocinas.jsx")


def leer():
    with open(ESTUDIO, encoding="utf-8") as f:
        return f.read()


def test_edicion_parte_del_original_y_no_del_ultimo_render():
    fuente = leer()
    assert "imageToDataUrl(render.originalUrl || render.imageUrl)" in fuente
    assert "originalUrl: s.originalUrl || u" in fuente
    assert "editHistory: [...(s.editHistory || []), cambioActual]" in fuente


def test_edicion_conserva_el_historial_y_el_perfil_elegido():
    fuente = leer()
    assert "CAMBIOS YA APLICADOS QUE DEBES CONSERVAR" in fuente
    assert "provider: providerDeMotor()" in fuente
    assert "editingRender: true" in fuente
