import os


RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RENDER = os.path.join(RAIZ, "backend", "services", "luiggi_ai", "render_3d.py")
ROUTE = os.path.join(RAIZ, "backend", "routes", "ai_engine.py")
ESTUDIO = os.path.join(RAIZ, "frontend", "src", "components", "EstudioCocinas.jsx")


def leer(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def test_el_servicio_acepta_una_referencia_de_plano_explicita():
    fuente = leer(RENDER)
    assert "reference_is_sketch: bool = False" in fuente
    assert "bool(reference_is_sketch) or self._is_sketch_reference" in fuente


def test_el_endpoint_transporta_la_referencia_de_plano():
    fuente = leer(ROUTE)
    assert "referenceIsSketch: Optional[bool]" in fuente
    assert "reference_is_sketch=bool(request.referenceIsSketch)" in fuente


def test_estudio_cocinas_marca_el_archivo_subido_como_croquis():
    fuente = leer(ESTUDIO)
    assert "referenceIsSketch: conCroquis" in fuente
    assert "if (motorIA === 'ia7') return 'julio11_plus';" in fuente
