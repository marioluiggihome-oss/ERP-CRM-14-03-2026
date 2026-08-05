# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Utilidades para leer PDFs: rasterizar páginas, sacar el texto, partirlos y
leer los campos de formulario.

Es el ÚNICO sitio del backend que habla con una librería de PDF. Los demás
módulos (proforma_cascos, mv_relacion) usan las funciones de aquí. Así, si un
día hay que cambiar de librería otra vez, se cambia en un fichero y no en tres.

Por qué NO se usa PyMuPDF (fitz), que era lo que había hasta el 05/08/2026:
PyMuPDF es AGPL-3.0 salvo licencia comercial de pago. La AGPL obliga a poner el
código fuente a disposición de quien usa el programa **incluso a través de la
red**, que es exactamente lo que hace un carpintero al entrar en
`erp.luiggihome.es`. En un ERP propietario que se licencia a terceros, eso es
un problema, no un detalle. Ver AUDITORIA-LICENCIAS.md.

Lo sustituyen dos librerías permisivas, que además reparten el trabajo mejor:
  · **pypdf** (BSD-3-Clause) — estructura del PDF: texto, páginas y AcroForm.
  · **pypdfium2** (Apache-2.0 / BSD-3) — rasterizado, con el motor PDFium de
    Chrome. Como PyMuPDF, trae su propio renderer y NO depende de binarios del
    sistema (poppler), así que el despliegue en Railway sigue igual de simple.

La sustitución se comprobó comparando ambas contra los PDFs reales del
proyecto: campos de formulario idénticos, mismo número de páginas, mismo tamaño
de imagen y mismo recuento de trazos. En el render, la diferencia media es de
1,1 sobre 255 (antialiasing del texto).
"""
import base64
import io
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import pypdf
    import pypdfium2 as pdfium
    from pypdfium2 import raw as pdfium_raw
    PDF_DISPONIBLE = True
except ImportError:  # pragma: no cover - solo si faltan en el entorno
    pypdf = None
    pdfium = None
    pdfium_raw = None
    PDF_DISPONIBLE = False

# Nombre anterior de la bandera. Se mantiene para no romper nada que la mire.
PYMUPDF_AVAILABLE = PDF_DISPONIBLE

# Cabecera de un PDF: "%PDF"
_PDF_MAGIC = b"%PDF"

# PyMuPDF medía en DPI y PDFium en factor de escala. Un PDF son 72 puntos por
# pulgada, así que 150 dpi = escala 2,083. Sin esta conversión las imágenes
# saldrían de otro tamaño y la IA de visión leería peor las cotas pequeñas.
_PUNTOS_POR_PULGADA = 72.0


def _escala(dpi: float) -> float:
    return max(float(dpi), 1.0) / _PUNTOS_POR_PULGADA


def is_pdf_bytes(data: bytes) -> bool:
    """¿Estos bytes corresponden a un PDF? (acepta algún byte basura inicial)."""
    if not data:
        return False
    return _PDF_MAGIC in data[:1024]


def is_pdf_base64(b64: str) -> bool:
    """¿Esta cadena base64 (sin prefijo data:) decodifica a un PDF?"""
    if not b64:
        return False
    # Quitar prefijo data: si viene
    if b64.startswith("data:"):
        if "pdf" in b64.split(",", 1)[0].lower():
            return True
        b64 = b64.split(",", 1)[1]
    try:
        head = base64.b64decode(b64[:64] + "===")  # padding defensivo
    except Exception:
        return False
    return is_pdf_bytes(head)


def _sin_prefijo(b64: str) -> str:
    return b64.split(",", 1)[1] if b64.startswith("data:") else b64


def _a_bytes(pdf_b64: str) -> Optional[bytes]:
    try:
        return base64.b64decode(_sin_prefijo(pdf_b64))
    except Exception as e:
        logger.error(f"No se pudo decodificar el PDF base64: {e}")
        return None


# ─── Primitivas sobre bytes. Son las que usa el resto del backend ────────────

def paginas_a_png(pdf_bytes: bytes, dpi: float = 150, max_pages: Optional[int] = None,
                  paginas: Optional[List[int]] = None) -> List[bytes]:
    """Rasteriza páginas a PNG (bytes). `paginas` = índices concretos (0-based).

    Devuelve lista vacía si el PDF no se puede abrir: rasterizar es siempre un
    respaldo, y quedarse sin imágenes no debe tumbar la petición.
    """
    if not PDF_DISPONIBLE:
        return []
    try:
        doc = pdfium.PdfDocument(pdf_bytes)
    except Exception as e:
        logger.error(f"No se pudo abrir el PDF: {e}")
        return []
    fuera: List[bytes] = []
    try:
        total = len(doc)
        if paginas is None:
            limite = total if max_pages is None else min(total, max_pages)
            indices = range(limite)
        else:
            indices = [i for i in paginas if 0 <= i < total]
        for i in indices:
            try:
                imagen = doc[i].render(scale=_escala(dpi)).to_pil().convert("RGB")
                buf = io.BytesIO()
                imagen.save(buf, format="PNG")
                fuera.append(buf.getvalue())
            except Exception as e:
                logger.warning(f"Error rasterizando página {i + 1}/{total}: {e}")
                continue
    finally:
        try:
            doc.close()
        except Exception:
            pass
    return fuera


def texto_de_pdf(pdf_bytes: bytes, max_pages: Optional[int] = None) -> str:
    """Capa de texto del PDF. "" si es escaneado o no se puede abrir.

    OJO, diferencia con PyMuPDF: `pypdf` devuelve el texto de la PÁGINA y no el
    de los recuadros de formulario. Es lo correcto aquí — los valores de los
    campos se leen con `campos_de_formulario`, y antes salían DUPLICADOS (una
    vez como campo y otra dentro del texto).
    """
    if not PDF_DISPONIBLE:
        return ""
    try:
        lector = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    except Exception:
        return ""
    paginas = lector.pages
    limite = len(paginas) if max_pages is None else min(len(paginas), max_pages)
    trozos = []
    for i in range(limite):
        try:
            trozos.append(paginas[i].extract_text() or "")
        except Exception:
            continue
    return "\n".join(trozos)


def partir_en_paginas(pdf_bytes: bytes, max_pages: Optional[int] = None) -> List[bytes]:
    """Un PDF de una sola página por cada página del original."""
    if not PDF_DISPONIBLE:
        return []
    try:
        lector = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    except Exception:
        return []
    total = len(lector.pages)
    limite = total if max_pages is None else min(total, max_pages)
    fuera: List[bytes] = []
    for i in range(limite):
        try:
            escritor = pypdf.PdfWriter()
            escritor.add_page(lector.pages[i])
            buf = io.BytesIO()
            escritor.write(buf)
            fuera.append(buf.getvalue())
        except Exception as e:
            logger.warning(f"No se pudo aislar la página {i + 1}/{total}: {e}")
    return fuera


def _resolver(obj):
    try:
        return obj.get_object()
    except Exception:
        return obj


def campos_de_formulario(pdf_bytes: bytes) -> List[Tuple[str, str]]:
    """Campos AcroForm rellenados, como [(etiqueta, valor)] y EN ORDEN DE PÁGINA.

    El orden importa: la plantilla MV se lee recuadro a recuadro y el orden es
    el de la hoja. Por eso se recorren las anotaciones de cada página en vez de
    usar `get_fields()`, que devuelve un diccionario sin ese orden.

    La etiqueta es `/TU` (el rótulo del recuadro, lo que PyMuPDF llamaba
    `field_label`) y, si no la hay, `/T` (el nombre interno). Valor y etiqueta
    pueden estar en el propio widget o heredarse del campo padre cuando un mismo
    campo tiene varios recuadros, así que se sube por la cadena de padres.
    """
    if not PDF_DISPONIBLE:
        return []
    try:
        lector = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    except Exception:
        return []
    fuera: List[Tuple[str, str]] = []
    for pagina in lector.pages:
        try:
            anotaciones = pagina.get("/Annots") or []
        except Exception:
            continue
        for anot in anotaciones:
            try:
                nodo = _resolver(anot)
                if nodo.get("/Subtype") != "/Widget":
                    continue
                valor = etiqueta = nombre = None
                saltos = 0
                while nodo is not None and saltos < 8:   # tope: PDFs con ciclos
                    if valor is None and "/V" in nodo:
                        valor = _resolver(nodo["/V"])
                    if etiqueta is None and "/TU" in nodo:
                        etiqueta = _resolver(nodo["/TU"])
                    if nombre is None and "/T" in nodo:
                        nombre = _resolver(nodo["/T"])
                    nodo = _resolver(nodo["/Parent"]) if "/Parent" in nodo else None
                    saltos += 1
                texto = "" if valor is None else str(valor).strip()
                if texto:
                    fuera.append((str(etiqueta or nombre or "").strip(), texto))
            except Exception:
                continue
    return fuera


def contar_trazos(pdf_bytes: bytes, max_pages: int = 12) -> List[int]:
    """Trazos vectoriales por página. Sirve para distinguir una página de tabla
    (miles de líneas) de una vista 3D o un plano (una imagen y poco más)."""
    if not PDF_DISPONIBLE:
        return []
    try:
        doc = pdfium.PdfDocument(pdf_bytes)
    except Exception:
        return []
    try:
        fuera = []
        for i in range(min(len(doc), max_pages)):
            try:
                fuera.append(sum(1 for o in doc[i].get_objects()
                                 if o.type == pdfium_raw.FPDF_PAGEOBJ_PATH))
            except Exception:
                fuera.append(0)
        return fuera
    finally:
        try:
            doc.close()
        except Exception:
            pass


def numero_de_paginas(pdf_bytes: bytes) -> int:
    if not PDF_DISPONIBLE:
        return 0
    try:
        return len(pypdf.PdfReader(io.BytesIO(pdf_bytes)).pages)
    except Exception:
        return 0


# ─── API en base64, la que ya usaban las rutas ──────────────────────────────

def pdf_base64_to_png_base64(
    pdf_b64: str,
    dpi: int = 150,
    max_pages: Optional[int] = None,
) -> List[str]:
    """
    Convierte un PDF (en base64) en una lista de PNG (en base64, sin prefijo data:),
    una por página.

    Args:
        pdf_b64: PDF codificado en base64 (con o sin prefijo "data:application/pdf;base64,").
        dpi: resolución de rasterizado (150 es buen equilibrio calidad/tamaño).
        max_pages: límite opcional de páginas a convertir (None = todas).

    Returns:
        Lista de strings base64 (PNG). Lista vacía si no se pudo convertir.
    """
    if not PDF_DISPONIBLE:
        logger.error("Faltan pypdf/pypdfium2: no se pueden convertir PDFs.")
        raise RuntimeError(
            "Faltan las dependencias 'pypdf' y 'pypdfium2' para procesar PDFs. "
            "Añádelas a requirements.txt."
        )
    pdf_bytes = _a_bytes(pdf_b64)
    if pdf_bytes is None:
        return []
    imagenes = [base64.b64encode(p).decode("utf-8")
                for p in paginas_a_png(pdf_bytes, dpi=dpi, max_pages=max_pages)]
    logger.info(f"PDF convertido: {len(imagenes)} página(s) rasterizada(s) a PNG.")
    return imagenes


def split_pdf_to_pages_base64(pdf_b64: str, max_pages: Optional[int] = None) -> List[str]:
    """Divide un PDF de varias páginas en un PDF de 1 sola página por cada una
    (en base64), para poder procesar cada página como un documento independiente.

    Útil cuando llega un PDF combinado con muchas facturas dentro (una por
    página, como en una exportación/histórico), y hay que leer cada factura
    por separado en vez de intentar leerlas todas como si fueran una sola.
    """
    pdf_bytes = _a_bytes(pdf_b64) if PDF_DISPONIBLE else None
    if pdf_bytes is None:
        return []
    return [base64.b64encode(p).decode("utf-8")
            for p in partir_en_paginas(pdf_bytes, max_pages=max_pages)]


def pdf_base64_to_text(pdf_b64: str, max_pages: Optional[int] = None) -> str:
    """Extrae el TEXTO de un PDF digital (todas las páginas por defecto).

    Devuelve "" si falta la librería, si no se puede decodificar/abrir, o si el
    PDF es escaneado (sin capa de texto).
    """
    pdf_bytes = _a_bytes(pdf_b64) if PDF_DISPONIBLE else None
    if pdf_bytes is None:
        return ""
    return texto_de_pdf(pdf_bytes, max_pages=max_pages)
