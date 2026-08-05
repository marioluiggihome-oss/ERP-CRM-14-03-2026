# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Lectura de PDF sin PyMuPDF: que la sustitución no se lleve por delante nada.

El 05/08/2026 se cambió PyMuPDF (AGPL-3.0, obligaba a publicar el código al
servir el ERP por red) por pypdf + pypdfium2, ambas permisivas. De eso depende
el importador de la plantilla MV, que es de donde salen los muebles y por tanto
el presupuesto: si la lectura de los recuadros se rompe, el presupuesto sale
corto y nadie se entera.

Estas pruebas leen un PDF de verdad —generado con el mismo generador del ERP—
y comprueban lo que el negocio necesita: que los recuadros se lean COMPLETOS,
CON SU ETIQUETA y EN ORDEN. El orden importa porque la plantilla se interpreta
recuadro a recuadro.

Si alguien vuelve a meter PyMuPDF, la última prueba se pone en rojo.
"""
import importlib.util
import os
import sys
import types

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND = os.path.join(RAIZ, "backend")

# Se INTENTA importar, no solo localizar: una librería a medio instalar (un
# binario que no carga, por ejemplo) se encuentra pero revienta al usarla, y el
# fallo aparecería como si el código estuviera roto.
falta = []
for modulo in ("pypdf", "pypdfium2", "reportlab", "PIL"):
    try:
        importlib.import_module(modulo)
    except Exception as e:
        falta.append(f"{modulo} ({type(e).__name__})")
sin_libs = pytest.mark.skipif(
    bool(falta), reason=f"librerías no utilizables en este entorno: {', '.join(falta)}")


def _carga(nombre, monkeypatch):
    """Carga un módulo de services/ sin arrastrar services/__init__ (Mongo, dotenv)."""
    if "services" not in sys.modules:
        paquete = types.ModuleType("services")
        paquete.__path__ = [os.path.join(BACKEND, "services")]
        monkeypatch.setitem(sys.modules, "services", paquete)
    spec = importlib.util.spec_from_file_location(
        f"services.{nombre}", os.path.join(BACKEND, "services", f"{nombre}.py"))
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, f"services.{nombre}", mod)
    spec.loader.exec_module(mod)
    return mod


# Lo que se escribe en la plantilla. Se comprueba que vuelve TAL CUAL.
MUEBLES = [
    {"cantidad": 2, "codigo": "B60D", "descripcion": "Bajo 2 cajones",
     "ancho": 600, "alto": 800, "fondo": 580},
    {"cantidad": 1, "codigo": "A90", "descripcion": "Alto con balda",
     "ancho": 900, "alto": 700, "fondo": 330},
]


@pytest.fixture()
def pdf_relleno(monkeypatch):
    """PDF rellenable con dos muebles dentro, hecho por el generador del ERP."""
    relacion_pdf = _carga("relacion_pdf", monkeypatch)
    return relacion_pdf.build_relacion_pdf(MUEBLES, titulo="Prueba", cliente="TEST")


@pytest.fixture()
def pdf_utils(monkeypatch):
    return _carga("pdf_utils", monkeypatch)


@sin_libs
def test_se_leen_todos_los_recuadros_rellenados(pdf_utils, pdf_relleno):
    campos = pdf_utils.campos_de_formulario(pdf_relleno)
    valores = [v for _e, v in campos]
    # 2 muebles x 6 datos. Los recuadros vacíos NO cuentan.
    assert len(campos) == 12, f"se han perdido recuadros: {valores}"
    assert valores == ["2", "B60D", "Bajo 2 cajones", "600", "800", "580",
                       "1", "A90", "Alto con balda", "900", "700", "330"], \
        "los recuadros no vuelven en el orden de la hoja"


@sin_libs
def test_cada_recuadro_viene_con_su_etiqueta(pdf_utils, pdf_relleno):
    """Sin la etiqueta, una nota sin código ("2 - 90 x 60") no se puede situar."""
    campos = pdf_utils.campos_de_formulario(pdf_relleno)
    etiquetas = [e for e, _v in campos]
    assert etiquetas[:6] == ["cantidad", "codigo", "descripcion",
                             "ancho", "alto", "fondo"]
    assert all(e for e in etiquetas), "algún recuadro ha venido sin etiqueta"


@sin_libs
def test_el_lector_de_la_plantilla_mv_sigue_viendo_los_muebles(monkeypatch, pdf_relleno):
    """La cadena completa: PDF -> mv_relacion.extract_campos."""
    _carga("pdf_utils", monkeypatch)
    mv = _carga("mv_relacion", monkeypatch)
    campos = mv.extract_campos(pdf_relleno)
    assert len(campos) == 12
    assert ("codigo", "B60D") in campos and ("codigo", "A90") in campos


@sin_libs
def test_con_recuadros_rellenados_no_se_mezcla_la_capa_de_texto(monkeypatch, pdf_relleno):
    """Si hay campos, mandan ellos: el texto de la hoja duplicaría los valores."""
    _carga("pdf_utils", monkeypatch)
    mv = _carga("mv_relacion", monkeypatch)
    texto = mv.extract_form_and_text(pdf_relleno)
    assert "B60D" in texto and "A90" in texto
    assert "OBSERVACIONES" not in texto.upper(), \
        "se ha colado la cabecera impresa de la tabla en la relación"


@sin_libs
def test_se_rasteriza_a_imagen_y_se_cuentan_los_trazos(pdf_utils, pdf_relleno):
    """Rasterizar es el respaldo cuando el PDF no tiene capa de texto."""
    pngs = pdf_utils.paginas_a_png(pdf_relleno, dpi=144)
    assert len(pngs) == 1
    assert pngs[0].startswith(b"\x89PNG"), "eso no es un PNG"
    assert len(pngs[0]) > 2000, "la imagen ha salido vacía"
    # Un recuento por página. Es lo que separa una hoja de tabla de un plano.
    trazos = pdf_utils.contar_trazos(pdf_relleno)
    assert len(trazos) == pdf_utils.numero_de_paginas(pdf_relleno)
    assert trazos[0] > 0, "una hoja con tabla no puede tener cero trazos"


@sin_libs
def test_partir_un_pdf_deja_una_pagina_por_trozo(pdf_utils, pdf_relleno):
    trozos = pdf_utils.partir_en_paginas(pdf_relleno)
    assert len(trozos) == pdf_utils.numero_de_paginas(pdf_relleno)
    assert all(pdf_utils.numero_de_paginas(t) == 1 for t in trozos)


@sin_libs
def test_el_dpi_manda_en_el_tamano_de_la_imagen(pdf_utils, pdf_relleno):
    """PyMuPDF medía en DPI y PDFium en escala; si la conversión se rompe, las
    imágenes salen de otro tamaño y la IA lee peor las cotas."""
    from PIL import Image
    import io as _io
    a = Image.open(_io.BytesIO(pdf_utils.paginas_a_png(pdf_relleno, dpi=72)[0]))
    b = Image.open(_io.BytesIO(pdf_utils.paginas_a_png(pdf_relleno, dpi=144)[0]))
    assert b.width == pytest.approx(a.width * 2, abs=2), \
        f"el doble de dpi debería dar el doble de ancho ({a.width} -> {b.width})"
    assert a.width == pytest.approx(595, abs=2), "A4 a 72 dpi son 595 px de ancho"


def test_no_se_vuelve_a_usar_pymupdf():
    """CANDADO de licencia. PyMuPDF es AGPL: obliga a publicar el código fuente
    a quien use el ERP por la red. No se vuelve a meter sin permiso del master
    y sin comprar antes la licencia comercial de Artifex."""
    culpables = []
    for carpeta, subdirs, nombres in os.walk(BACKEND):
        subdirs[:] = [d for d in subdirs if d not in ("__pycache__", "tests")]
        for n in nombres:
            if not n.endswith(".py"):
                continue
            ruta = os.path.join(carpeta, n)
            with open(ruta, encoding="utf-8") as f:
                for i, linea in enumerate(f, 1):
                    limpia = linea.split("#")[0]
                    if "import fitz" in limpia or "import pymupdf" in limpia.lower():
                        culpables.append(f"{os.path.relpath(ruta, RAIZ)}:{i}")
    assert not culpables, (
        "vuelve a haber PyMuPDF (AGPL-3.0) en el backend: " + ", ".join(culpables) +
        ". Usa services/pdf_utils.py (pypdf + pypdfium2). Ver AUDITORIA-LICENCIAS.md.")


def test_requirements_no_trae_pymupdf():
    req = os.path.join(BACKEND, "requirements.txt")
    with open(req, encoding="utf-8") as f:
        lineas = [l.split("#")[0].strip().lower() for l in f]
    assert not [l for l in lineas if l.startswith("pymupdf") or l.startswith("fitz")], \
        "pymupdf ha vuelto a requirements.txt"
    texto = " ".join(lineas)
    assert "pypdf" in texto and "pypdfium2" in texto, \
        "faltan las librerías que sustituyen a PyMuPDF"
