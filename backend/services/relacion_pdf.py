"""
relacion_pdf.py — Relación de muebles detectados por el analizador, en PDF
RELLENABLE.

Por qué rellenable y no un PDF cerrado: lo que sale del analizador es un punto
de partida, no una verdad. En obra se corrige a mano (una medida, unas unidades,
un mueble que falta) y esa corrección tiene que poder volver al ERP. Los campos
son AcroForm, así que se rellenan en cualquier lector de PDF y luego se releen
de forma determinista, sin IA de por medio (igual que la plantilla MV).

Las cotas se escriben SOLO si vienen; una medida que no se conoce se deja en
blanco para que la ponga quien mide, nunca con un número plausible.
"""
import io
from datetime import datetime

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

C_TXT = HexColor("#1e293b")
C_MUT = HexColor("#64748b")
C_LINE = HexColor("#cbd5e1")
C_HEAD = HexColor("#f1f5f9")
C_FIELD = HexColor("#fffbe6")
C_FIELDB = HexColor("#f59e0b")
C_ZEBRA = HexColor("#f8fafc")  # fila alterna: separa sin dibujar cuadrícula

# Columnas: (título, ancho en mm, clave del dato, ¿rellenable?, ¿es número?)
# Los números van alineados a la derecha: así se comparan de un vistazo y un
# error de coma salta solo (criterio gráfico, en criterios_cocina.py).
COLUMNAS = [
    ("Uds", 12, "cantidad", True, True),
    ("Código", 30, "codigo", True, False),
    ("Descripción", 62, "descripcion", True, False),
    ("Ancho", 17, "ancho", True, True),
    ("Alto", 17, "alto", True, True),
    ("Fondo", 17, "fondo", True, True),
    ("Observaciones", 40, "observaciones", True, False),
]


def _cota(v):
    """Medida en mm como texto. Lo que no se sabe se deja EN BLANCO."""
    try:
        n = float(v)
    except (TypeError, ValueError):
        return ""
    return str(int(round(n))) if n > 0 else ""


def build_relacion_pdf(muebles: list, titulo: str = "", cliente: str = "",
                       observaciones: str = "") -> bytes:
    """Devuelve los bytes de un PDF rellenable con la relación de muebles."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    ML, MR, MT, MB = 12 * mm, 12 * mm, 14 * mm, 14 * mm
    ancho_util = W - ML - MR
    escala = ancho_util / (sum(col[1] for col in COLUMNAS) * mm)
    campo = [0]
    fila_par = [False]

    def cabecera(pagina: int):
        c.setFillColor(C_TXT)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(ML, H - MT, titulo or "Relación de muebles")
        c.setFillColor(C_MUT)
        c.setFont("Helvetica", 8)
        sub = datetime.now().strftime("%d/%m/%Y")
        if cliente:
            sub = f"{cliente} · {sub}"
        c.drawString(ML, H - MT - 5 * mm, sub)
        c.drawRightString(W - MR, H - MT - 5 * mm, f"pág. {pagina}")
        c.setFillColor(C_MUT)
        c.setFont("Helvetica-Oblique", 7)
        c.drawString(ML, H - MT - 9.5 * mm,
                     "Medidas en mm. Los recuadros amarillos son EDITABLES: corrige lo que haga falta "
                     "y vuelve a subir el PDF al ERP.")

    def fila_cabecera(y: float):
        c.setFillColor(C_HEAD)
        c.rect(ML, y - 6 * mm, ancho_util, 6 * mm, stroke=0, fill=1)
        c.setFillColor(C_MUT)
        c.setFont("Helvetica-Bold", 7)
        x = ML
        for titulo_col, w, _clave, _ed, es_num in COLUMNAS:
            cw = w * mm * escala
            # Cabecera de las columnas numéricas a la derecha, que es donde cae
            # la cifra. (reportlab no deja alinear el contenido de un campo de
            # formulario, así que la comparación visual se apoya en la cabecera
            # y en columnas estrechas.)
            if es_num:
                c.drawRightString(x + cw - 1.5 * mm, y - 4.2 * mm, titulo_col.upper())
            else:
                c.drawString(x + 1.5 * mm, y - 4.2 * mm, titulo_col.upper())
            x += cw
        return y - 6 * mm

    pagina = 1
    cabecera(pagina)
    y = fila_cabecera(H - MT - 14 * mm)
    alto_fila = 8 * mm

    for m in (muebles or []):
        if y - alto_fila < MB + 12 * mm:
            c.showPage()
            pagina += 1
            cabecera(pagina)
            y = fila_cabecera(H - MT - 14 * mm)
        datos = {
            "cantidad": str(int(m.get("cantidad") or 1)),
            "codigo": str(m.get("codigo") or "")[:24],
            "descripcion": str(m.get("descripcion") or "")[:60],
            "ancho": _cota(m.get("ancho")),
            "alto": _cota(m.get("alto")),
            "fondo": _cota(m.get("fondo")),
            "observaciones": str(m.get("observaciones") or "")[:40],
        }
        x = ML
        if fila_par[0]:
            c.setFillColor(C_ZEBRA)
            c.rect(ML, y - alto_fila, ancho_util, alto_fila, stroke=0, fill=1)
        fila_par[0] = not fila_par[0]
        c.setStrokeColor(C_LINE)
        c.setLineWidth(0.4)
        c.line(ML, y - alto_fila, W - MR, y - alto_fila)
        for _titulo_col, w, clave, editable, es_num in COLUMNAS:
            cw = w * mm * escala
            if editable:
                campo[0] += 1
                c.setFillColor(C_FIELD)
                c.setStrokeColor(C_FIELDB)
                c.setLineWidth(0.4)
                c.rect(x + 0.8 * mm, y - alto_fila + 1.2 * mm, cw - 1.6 * mm,
                       alto_fila - 2.4 * mm, stroke=1, fill=1)
                c.acroForm.textfield(
                    name=f"{clave}_{campo[0]}", tooltip=clave,
                    value=datos.get(clave, ""),
                    x=x + 1 * mm, y=y - alto_fila + 1.4 * mm,
                    width=cw - 2 * mm, height=alto_fila - 2.8 * mm,
                    borderWidth=0, forceBorder=False, fontSize=7.5,
                    fillColor=C_FIELD, textColor=C_TXT, fieldFlags="",
                )
            else:
                c.setFillColor(C_TXT)
                c.setFont("Helvetica", 7.5)
                c.drawString(x + 1.5 * mm, y - alto_fila + 3 * mm, datos.get(clave, ""))
            x += cw
        y -= alto_fila

    # Espacio para añadir a mano lo que falte: sin esto, quien mide no puede
    # apuntar un mueble que el analizador no vio.
    for _ in range(6):
        if y - alto_fila < MB + 12 * mm:
            c.showPage()
            pagina += 1
            cabecera(pagina)
            y = fila_cabecera(H - MT - 14 * mm)
        x = ML
        c.setStrokeColor(C_LINE)
        c.setLineWidth(0.4)
        c.line(ML, y - alto_fila, W - MR, y - alto_fila)
        for _titulo_col, w, clave, _ed, es_num in COLUMNAS:
            cw = w * mm * escala
            campo[0] += 1
            c.setFillColor(C_FIELD)
            c.setStrokeColor(C_FIELDB)
            c.setLineWidth(0.4)
            c.rect(x + 0.8 * mm, y - alto_fila + 1.2 * mm, cw - 1.6 * mm,
                   alto_fila - 2.4 * mm, stroke=1, fill=1)
            c.acroForm.textfield(
                name=f"{clave}_{campo[0]}", tooltip=clave, value="",
                x=x + 1 * mm, y=y - alto_fila + 1.4 * mm,
                width=cw - 2 * mm, height=alto_fila - 2.8 * mm,
                borderWidth=0, forceBorder=False, fontSize=7.5,
                fillColor=C_FIELD, textColor=C_TXT, fieldFlags="",
            )
            x += cw
        y -= alto_fila

    if observaciones:
        y -= 6 * mm
        c.setFillColor(C_MUT)
        c.setFont("Helvetica-Oblique", 7.5)
        for linea in str(observaciones)[:600].split("\n")[:6]:
            c.drawString(ML, y, linea[:150])
            y -= 4 * mm

    c.save()
    return buf.getvalue()
