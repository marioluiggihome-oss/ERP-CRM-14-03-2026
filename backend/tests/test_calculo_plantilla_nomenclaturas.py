# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LA PLANTILLA RELLENABLE DE NOMENCLATURAS: SE RELLENA A MANO, EN PAPEL O TABLET.

El master, 28/08: «que el PDF rellenable sea mejor, con los campos un poquito
más grandes cuando se descarga».

DOS COSAS QUE HAY QUE SOSTENER A LA VEZ, Y TIRAN EN DIRECCIONES OPUESTAS:

1. QUE SE PUEDA RELLENAR. Un recuadro de 6,6 mm con letra de 8 no se ve ni se
   acierta con el dedo. Los campos son grandes a propósito; que quepan menos
   fichas por página da igual — el PDF es para trabajar, no para ahorrar papel.

2. QUE SE PUEDA VOLVER A LEER. Este PDF se sube después y `mv_relacion` saca de
   él la relación de muebles. Lo hace por los campos del formulario CON SU
   ETIQUETA, así que una nota sin código —«2 · 60x80»— se entiende porque se
   sabe de qué familia es. Si un rediseño se llevara por delante las etiquetas,
   o partiera el recuadro en cuatro casillas sueltas, el PDF seguiría
   descargándose igual de bonito y al subirlo no se leería nada.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services.nomenclaturas_pdf import build_nomenclaturas_pdf  # noqa: E402

# Lo que había antes y no puede volver: 6,6 mm de alto y letra de 8.
ALTO_MINIMO_MM = 8.0
LETRA_MINIMA = 10.0


def _pdf():
    return build_nomenclaturas_pdf()


def _campos(pdf_bytes):
    from pypdf import PdfReader
    return PdfReader(io.BytesIO(pdf_bytes)).get_fields() or {}


def test_hay_UN_RECUADRO_POR_FAMILIA_y_todos_con_su_etiqueta():
    """La etiqueta es lo que hace legible una nota sin código al releer el PDF."""
    campos = _campos(_pdf())
    assert len(campos) >= 50, f"solo {len(campos)} recuadros: faltan familias"
    sin_etiqueta = [k for k, v in campos.items() if not v.get("/TU")]
    assert not sin_etiqueta, (
        f"estos recuadros no dicen de qué familia son: {sin_etiqueta[:5]}. Al "
        "subir el PDF, una nota como «2 · 60x80» dejaría de entenderse")


def test_los_RECUADROS_SON_GRANDES_de_verdad():
    """Se mide el widget en el PDF, no el código: es lo que se ve al abrirlo."""
    from pypdf import PdfReader
    lector = PdfReader(io.BytesIO(_pdf()))
    altos = []
    for pagina in lector.pages:
        for anot in (pagina.get("/Annots") or []):
            obj = anot.get_object()
            if obj.get("/Subtype") != "/Widget" or not obj.get("/Rect"):
                continue
            x0, y0, x1, y1 = [float(v) for v in obj["/Rect"]]
            altos.append(abs(y1 - y0) / 72.0 * 25.4)      # puntos → mm
    assert altos, "no hay recuadros rellenables en el PDF"
    minimo = min(altos)
    assert minimo >= ALTO_MINIMO_MM, (
        f"el recuadro más pequeño mide {minimo:.1f} mm y hacen falta "
        f"{ALTO_MINIMO_MM} mm. Con menos no se acierta con el dedo en una "
        "tablet, que es donde se rellena.")


def test_la_LETRA_del_campo_no_vuelve_a_ser_diminuta():
    cuerpo = open(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "services", "nomenclaturas_pdf.py"), encoding="utf-8").read()
    i = cuerpo.index("c.acroForm.textfield(")
    trozo = cuerpo[i:i + 420]
    import re
    m = re.search(r"fontSize=([\d.]+)", trozo)
    assert m, "el campo ya no fija el tamaño de letra"
    assert float(m.group(1)) >= LETRA_MINIMA, (
        f"la letra del recuadro ha bajado a {m.group(1)}: lo que se escribe a "
        "mano tiene que leerse")


def test_se_ENSEÑA_EL_FORMATO_esperado_con_un_ejemplo():
    """Antes ponía «Notas / medidas / uds» y había que adivinar cómo escribirlo.

    Un ejemplo vale más que una explicación: quien rellena copia el patrón sin
    leer nada, y así lo que escribe se puede volver a leer.
    """
    from services.pdf_utils import texto_de_pdf
    texto = texto_de_pdf(_pdf())
    assert "Uds" in texto and "código o medidas" in texto, (
        "el recuadro ya no dice qué se espera dentro")
    assert "ej.:" in texto, (
        "no hay ejemplo del formato: sin él cada uno lo escribe a su manera y "
        "el lector no lo entiende")


def test_el_PDF_SIGUE_SIENDO_LEGIBLE_por_el_importador():
    """La prueba de que el círculo se cierra: lo que genera esta plantilla es lo
    que `mv_relacion` sabe leer."""
    from services.pdf_utils import campos_de_formulario
    # En blanco no hay valores; lo que se comprueba es que no reviente y que la
    # estructura sea la que espera el lector.
    assert campos_de_formulario(_pdf()) == [], (
        "una plantilla en blanco no puede traer valores")
    campos = _campos(_pdf())
    assert all(k.startswith("nota_") for k in campos), (
        f"han cambiado los nombres de los campos: {list(campos)[:3]}")


def test_el_PDF_DEJA_ESCRIBIR_de_verdad():
    """`/NeedAppearances` es lo que hace que un visor te deje rellenar.

    EL FALLO, encontrado por el master el 28/08: descargó la plantilla, la abrió
    y no le dejaba escribir en los recuadros. El PDF estaba bien —campos de
    texto, editables, con apariencia— pero sin esta bandera el documento le dice
    al visor «las casillas ya vienen dibujadas, no las repintes», y varios
    visores lo entienden como que no hay nada que escribir: se ve la casilla y
    al tocarla no pasa nada.

    Es de las cosas que no dan error en ninguna parte: el PDF se genera, se
    descarga y se abre. Solo se nota al intentar usarlo.
    """
    from pypdf import PdfReader
    acro = PdfReader(io.BytesIO(_pdf())).trailer["/Root"]["/AcroForm"]
    # `bool(...)` y no `is True`: pypdf devuelve su propio `BooleanObject`, que
    # se imprime como True y no ES True. Comparar por identidad daba rojo con el
    # PDF bien hecho.
    assert bool(acro.get("/NeedAppearances")), (
        "el formulario no lleva `/NeedAppearances`: se descarga bien y no se "
        "puede rellenar, que es justo lo que pasó el 28/08")


def test_ningun_recuadro_esta_BLOQUEADO_ni_oculto():
    """La otra forma de que no se pueda escribir: el campo llega de solo lectura
    o la anotación viene marcada como oculta. Ninguna de las dos da error."""
    from pypdf import PdfReader
    SOLO_LECTURA, OCULTO = 1, 2
    problemas = []
    for pagina in PdfReader(io.BytesIO(_pdf())).pages:
        for anot in (pagina.get("/Annots") or []):
            obj = anot.get_object()
            if obj.get("/Subtype") != "/Widget":
                continue
            nombre = obj.get("/T") or "?"
            if int(obj.get("/Ff") or 0) & SOLO_LECTURA:
                problemas.append(f"{nombre}: de solo lectura")
            if int(obj.get("/F") or 0) & OCULTO:
                problemas.append(f"{nombre}: oculto")
    assert not problemas, "; ".join(problemas[:5])
