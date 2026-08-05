# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Utilidades para convertir PDFs en imágenes.

Muchos catálogos y borradores llegan como PDF (a veces escaneados, sin capa de
texto). La IA de visión (Gemini) trabaja con imágenes, así que necesitamos
rasterizar cada página del PDF a PNG antes de enviarla.

Se usa PyMuPDF (fitz) porque trae su propio renderer y NO depende de binarios
del sistema (poppler), lo que simplifica el despliegue en Railway.
"""
import base64
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    fitz = None
    PYMUPDF_AVAILABLE = False


# Cabecera de un PDF: "%PDF"
_PDF_MAGIC = b"%PDF"


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
    if not PYMUPDF_AVAILABLE:
        logger.error("PyMuPDF (pymupdf) no está instalado: no se pueden convertir PDFs.")
        raise RuntimeError(
            "Falta la dependencia 'pymupdf' para procesar PDFs. "
            "Añádela a requirements.txt."
        )

    # Normalizar: quitar prefijo data: si viene
    if pdf_b64.startswith("data:"):
        pdf_b64 = pdf_b64.split(",", 1)[1]

    try:
        pdf_bytes = base64.b64decode(pdf_b64)
    except Exception as e:
        logger.error(f"No se pudo decodificar el PDF base64: {e}")
        return []

    images: List[str] = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        logger.error(f"No se pudo abrir el PDF: {e}")
        return []

    try:
        total = doc.page_count
        limit = total if max_pages is None else min(total, max_pages)
        for i in range(limit):
            try:
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=dpi)
                png_bytes = pix.tobytes("png")
                images.append(base64.b64encode(png_bytes).decode("utf-8"))
            except Exception as e:
                logger.warning(f"Error rasterizando página {i + 1}/{total}: {e}")
                continue
    finally:
        doc.close()

    logger.info(f"PDF convertido: {len(images)} página(s) rasterizada(s) a PNG.")
    return images


def split_pdf_to_pages_base64(pdf_b64: str, max_pages: Optional[int] = None) -> List[str]:
    """Divide un PDF de varias páginas en un PDF de 1 sola página por cada una
    (en base64), para poder procesar cada página como un documento independiente.

    Útil cuando llega un PDF combinado con muchas facturas dentro (una por
    página, como en una exportación/histórico), y hay que leer cada factura
    por separado en vez de intentar leerlas todas como si fueran una sola.
    """
    if not PYMUPDF_AVAILABLE:
        return []
    if pdf_b64.startswith("data:"):
        pdf_b64 = pdf_b64.split(",", 1)[1]
    try:
        pdf_bytes = base64.b64decode(pdf_b64)
    except Exception:
        return []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        return []
    out: List[str] = []
    try:
        total = doc.page_count
        limit = total if max_pages is None else min(total, max_pages)
        for i in range(limit):
            single = None
            try:
                single = fitz.open()
                single.insert_pdf(doc, from_page=i, to_page=i)
                out.append(base64.b64encode(single.tobytes()).decode("utf-8"))
            except Exception as e:
                logger.warning(f"No se pudo aislar la página {i + 1}/{total}: {e}")
            finally:
                if single is not None:
                    single.close()
    finally:
        doc.close()
    return out


def pdf_base64_to_text(pdf_b64: str, max_pages: Optional[int] = None) -> str:
    """Extrae el TEXTO de un PDF digital (todas las páginas por defecto).

    Devuelve "" si no hay PyMuPDF, si no se puede decodificar/abrir, o si el PDF
    es escaneado (sin capa de texto).
    """
    if not PYMUPDF_AVAILABLE:
        return ""
    if pdf_b64.startswith("data:"):
        pdf_b64 = pdf_b64.split(",", 1)[1]
    try:
        pdf_bytes = base64.b64decode(pdf_b64)
    except Exception:
        return ""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        return ""
    try:
        total = doc.page_count
        limit = total if max_pages is None else min(total, max_pages)
        parts = []
        for i in range(limit):
            try:
                parts.append(doc.load_page(i).get_text() or "")
            except Exception:
                continue
        return "\n".join(parts)
    finally:
        doc.close()
