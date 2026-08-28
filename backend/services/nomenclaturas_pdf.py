# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
nomenclaturas_pdf.py — Genera el catálogo de NOMENCLATURAS MV en PDF, bien
maquetado, con un DIBUJO por familia y CAMPOS RELLENABLES (formulario AcroForm)
para anotar medidas, cantidades y observaciones.

Fuente de datos: data/mv_tarifas_oficiales.json (tarifa T1, 56 familias).
Salida: bytes de un PDF A4.

Uso:
    from services.nomenclaturas_pdf import build_nomenclaturas_pdf
    pdf_bytes = build_nomenclaturas_pdf()
"""
import json
import os
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from services.marca import con_marca

_DATA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mv_tarifas_oficiales.json")

# ── Paleta ──────────────────────────────────────────────────────────────────
C_TXT   = HexColor("#1e293b")   # slate-800
C_MUT   = HexColor("#64748b")   # slate-500
C_LINE  = HexColor("#e2e8f0")   # slate-200
C_ACC   = HexColor("#4f46e5")   # indigo-600
C_ACC_L = HexColor("#eef2ff")   # indigo-50
C_ICON  = HexColor("#334155")   # slate-700
C_ICONB = HexColor("#f1f5f9")   # slate-100
C_FIELD = HexColor("#fffbeb")   # amber-50 (campos rellenables)
C_FIELDB= HexColor("#fcd34d")   # amber-300

# ── Metadatos por familia: título legible + tipo de dibujo + descripción ─────
# tipo ∈ {bajo, bajo1, alto, alto1, cajones, vitrina, fregadero, horno, campana,
#         escurreplatos, columna, mediacolumna, botellero, rincon, altillo,
#         puerta, lineal, box}
FAM_META = {
    "PUERTAS":                  ("Puertas", "puerta", "Puerta suelta (matriz alto × ancho)"),
    "VITRINA":                  ("Puertas vitrina", "vitrina", "Puerta con cristal (inglesa = PVI)"),
    "REJILLA_CONFESIONARIO":    ("Rejilla confesionario", "vitrina", "Rejilla gris o blanca"),
    "BAJO":                     ("Bajo", "bajo1", "Bajo con 1 balda. D/I = 1 puerta"),
    "BAJO_FREGADERO":           ("Bajo fregadero", "fregadero", "Chapa antihumedad = BFC"),
    "BAJO_RINCON_ESCUADRA":     ("Bajo rincón escuadra", "rincon", "BRI indep. · BRU puertas unidas"),
    "BAJO_RINCON_CIEGO":        ("Bajo rincón ciego", "rincon", "Indicar situación de la puerta"),
    "BAJO_HORNO":               ("Bajo horno", "horno", "Frente fijo inferior 9,5 cm"),
    "BAJO_TERMINAL":            ("Bajo terminal", "bajo", "BTS lat. suelo · BTZ zócalo · BTP chaflán"),
    "BAJO_PUERTA_CAJON":        ("Bajo puerta y cajón", "bajo", "1 cajón + 1 puerta"),
    "BAJO_5_CAJONES":           ("Bajo 5 cajones", "cajones", "5 frentes de cajón"),
    "BAJO_3CAJ_1GAV":           ("Bajo 3 cajones + 1 gaveta", "cajones", "BCG"),
    "BAJO_2GAV_1CAJ":           ("Bajo 2 gavetas + 1 cajón", "cajones", "BGC"),
    "BAJO_2CAJ_1GAV_1FRENTE":   ("Bajo 2 caj + 1 gav + 1 frente", "cajones", "BCGF"),
    "BAJO_2GAV_1FRENTE":        ("Bajo 2 gavetas + 1 frente", "cajones", "BGF"),
    "ALTO":                     ("Alto", "alto1", "Alturas 70 y 90. D/I = 1 puerta"),
    "ALTO_CAMPANA":             ("Alto campana", "campana", "ASCE extraplana · ASC clásica"),
    "ALTO_RINCON_CIEGO":        ("Alto rincón ciego", "rincon", ""),
    "ALTO_RINCON_ESCUADRA":     ("Alto rincón escuadra", "rincon", "ARI indep. · ARU unidas"),
    "ALTO_RINCON_CHAFLAN":      ("Alto rincón chaflán", "rincon", "ARC · ARCV vitrina"),
    "ALTO_DECORATIVO":          ("Alto decorativo", "box", "Sin puerta"),
    "ALTO_VITRINA":             ("Alto vitrina", "vitrina", ""),
    "ALTO_ESCURREPLATOS":       ("Alto escurreplatos", "escurreplatos", ""),
    "ALTO_MICROONDAS":          ("Alto microondas", "horno", "AMF con frente"),
    "ALTO_CALENTADOR":          ("Alto calentador", "horno", ""),
    "ALTO_CALDERA":             ("Alto caldera", "horno", "A=90/110 · F=45"),
    "ALTO_SOBREFRIGO":          ("Alto sobre-frigo", "horno", "ASF60A salvacorte · ASF60F free"),
    "ALTO_TERMINAL":            ("Alto terminal", "alto", ""),
    "ALTO_ABATIBLE":            ("Alto abatible", "alto", "2 puertas abatibles free"),
    "ALTO_COMBINADO":           ("Alto combinado", "alto", ""),
    "ALTO_COMBINADO_PLUS":      ("Alto combinado plus", "alto", "ACP"),
    "ALTO_COMBINADO_PLUS_J":    ("Alto combinado plus J", "alto", "ACPJ"),
    "ALTILLO":                  ("Altillo", "altillo", "Abatible free"),
    "ALTILLO_VITRINA":          ("Altillo vitrina", "vitrina", ""),
    "SOBREENCIMERA":            ("Sobreencimera", "altillo", "Alturas 127 y 147"),
    "SOBREENC_VITRINA":         ("Sobreencimera vitrina", "vitrina", ""),
    "SOBREENC_CAJON":           ("Sobreencimera cajón", "cajones", ""),
    "SOBREENC_VIT_CAJON":       ("Sobreencimera vitrina cajón", "vitrina", ""),
    "COLUMNA_DESPENSERO":       ("Columna despensero/escobero", "columna", "Alturas 200 y 220"),
    "COLUMNA_FRIGO":            ("Columna frigo", "columna", ""),
    "COLUMNA_HORNO":            ("Columna horno", "horno", "CHPC/CHGC/CHC según cajones"),
    "COLUMNA_HORNO_MICRO":      ("Columna horno + microondas", "horno", ""),
    "MEDIACOLUMNA":             ("Mediacolumna", "mediacolumna", "Altura 130"),
    "MEDIA_PUERTA_GAVETA":      ("Media puerta gaveta", "mediacolumna", "MPG"),
    "MEDIACOLUMNA_HORNO":       ("Mediacolumna horno", "horno", ""),
    "MEDIACOLUMNA_VITRINA":     ("Mediacolumna vitrina", "vitrina", ""),
    "MEDIACOL_VITRINA_GAVETA":  ("Mediacolumna vitrina gaveta", "vitrina", ""),
    "BOTELLEROS":               ("Botelleros", "botellero", "Anchos 7 y 9"),
    "ALTILLOS_DECORATIVOS":     ("Altillos decorativos", "altillo", ""),
    "LATERALES_COLOR":          ("Laterales color", "lineal", ""),
    "COSTADOS_COLOR":           ("Costados color", "lineal", ""),
    "REGLETA_COLOR":            ("Regleta color", "lineal", ""),
    "REGLETA_MELAMINA":         ("Regleta melamina", "lineal", ""),
    "COSTADOS_MELAMINA":        ("Costados melamina", "lineal", ""),
    "TECHO_COLOR":              ("Techo color", "lineal", "Fondos 35/50/60"),
    "ELEMENTOS_LINEALES":       ("Elementos lineales", "lineal", "Cornisa, zócalo, portaluz…"),
}

NOTAS = [
    "D/I = versión Derecha o Izquierda (indícala al pedir).",
    "El número del código = ANCHO en cm (B60 = 60 cm).",
    "Alturas: altos 70/90 · sobreencimera 127/147 · columnas 200/220 · mediacolumna 130.",
    "Los recuadros amarillos son RELLENABLES: anota medidas, unidades u observaciones.",
]


# ── Dibujos vectoriales (viewBox lógico 0..24, se escala a la caja destino) ───
def _draw_icon(c, tipo, x, y, box):
    """Dibuja el icono `tipo` dentro de una caja (x,y) de lado `box` puntos.
    Coordenadas de las formas en unidades 0..24 (como los SVG); se mapean con s()."""
    pad = box * 0.12
    inner = box - 2 * pad
    sc = inner / 24.0

    def X(u):  # x lógico → punto
        return x + pad + u * sc

    def Y(u):  # y lógico (SVG, top=0) → punto (reportlab, bottom=0)
        return y + pad + (24 - u) * sc

    c.setStrokeColor(C_ICON)
    c.setLineWidth(max(1.0, box * 0.045))
    c.setLineCap(1)
    c.setLineJoin(1)

    def rect(x0, y0, w, h):
        c.rect(X(x0), Y(y0 + h), w * sc, h * sc, stroke=1, fill=0)

    def line(x0, y0, x1, y1):
        c.line(X(x0), Y(y0), X(x1), Y(y1))

    def dot(cx, cy, r=0.7):
        c.circle(X(cx), Y(cy), r * sc, stroke=1, fill=1)

    t = tipo
    if t in ("bajo",):
        rect(3.5, 7, 17, 13); line(12, 7, 12, 20); dot(10.3, 13.5, .6); dot(13.7, 13.5, .6)
    elif t == "bajo1":
        rect(3.5, 7, 17, 13); dot(18.2, 13.5, .6)
    elif t == "alto":
        rect(4, 4, 16, 11); line(12, 4, 12, 15); dot(10.5, 12.5, .6); dot(13.5, 12.5, .6)
    elif t == "alto1":
        rect(4, 4, 16, 11); dot(18.5, 12.5, .6)
    elif t == "cajones":
        rect(3.5, 5, 17, 15); line(3.5, 10, 20.5, 10); line(3.5, 14.5, 20.5, 14.5)
        line(10, 7.5, 14, 7.5); line(10, 12.2, 14, 12.2); line(10, 17.2, 14, 17.2)
    elif t == "vitrina":
        rect(4, 4, 16, 16); line(12, 4, 12, 20); line(5.5, 6, 10.5, 11); line(13.5, 13, 18.5, 18)
    elif t == "fregadero":
        rect(3.5, 8, 17, 12)
        c.ellipse(X(6.5), Y(3), X(17.5), Y(7), stroke=1, fill=0); line(12, 3, 12, 8)
    elif t == "horno":
        rect(4, 4, 16, 16); rect(6.5, 8.5, 11, 9); line(8, 6.2, 16, 6.2)
    elif t == "campana":
        c.setLineJoin(1)
        p = c.beginPath(); p.moveTo(X(5), Y(9)); p.lineTo(X(8), Y(5)); p.lineTo(X(16), Y(5)); p.lineTo(X(19), Y(9)); p.close()
        c.drawPath(p, stroke=1, fill=0); line(3.5, 9, 20.5, 9); line(9, 12, 9, 13.5); line(15, 12, 15, 13.5)
    elif t == "escurreplatos":
        rect(4, 4, 16, 16); line(7, 10, 17, 10); line(7, 13.5, 17, 13.5)
        line(9, 10, 9, 13.5); line(12, 10, 12, 13.5); line(15, 10, 15, 13.5)
    elif t == "columna":
        rect(6.5, 2.5, 11, 19); line(6.5, 9, 17.5, 9); line(6.5, 15, 17.5, 15); dot(15.2, 12, .6)
    elif t == "mediacolumna":
        rect(6.5, 5, 11, 14); line(6.5, 12, 17.5, 12); dot(15.2, 9, .6); dot(15.2, 15, .6)
    elif t == "botellero":
        rect(7.5, 3, 9, 18)
        for yy in (6, 11, 16):
            line(8, yy, 16, yy + 3); line(16, yy, 8, yy + 3)
    elif t == "rincon":
        p = c.beginPath(); p.moveTo(X(3.5), Y(7)); p.lineTo(X(13), Y(7)); p.lineTo(X(13), Y(13))
        p.lineTo(X(20.5), Y(13)); p.lineTo(X(20.5), Y(20.5)); p.lineTo(X(3.5), Y(20.5)); p.close()
        c.drawPath(p, stroke=1, fill=0); dot(6, 16.5, .6)
    elif t == "altillo":
        rect(3.5, 8, 17, 7); line(6, 15, 6, 18); line(18, 15, 18, 18)
    elif t == "puerta":
        rect(7.5, 3, 9, 18); dot(14.2, 12, .7)
    elif t == "lineal":
        rect(3, 10.5, 18, 3)
    else:  # box
        rect(4, 5, 16, 15); line(12, 5, 12, 20)


def _widths(codes):
    """Extrae los anchos (cm) de una lista de códigos, ordenados y sin repetir."""
    ws = []
    for cod in codes:
        m = re.search(r"[A-Z](\d{2,3})", cod)
        if m:
            v = int(m.group(1))
            if 5 <= v <= 300 and v not in ws:
                ws.append(v)
    return sorted(ws)


def build_nomenclaturas_pdf(tariff: str = "T1") -> bytes:
    from io import BytesIO
    data = json.load(open(_DATA, "r", encoding="utf-8"))
    fams = data.get("tariffs", {}).get(tariff, {})

    buf = BytesIO()
    W, H = A4
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle("Nomenclaturas MV — Catálogo de familias (rellenable)")

    ML, MR, MT, MB = 14 * mm, 14 * mm, 16 * mm, 14 * mm
    col_gap = 6 * mm
    col_w = (W - ML - MR - col_gap) / 2.0
    # FICHA MÁS ALTA Y CAMPO MÁS GRANDE (master, 28/08: «que el PDF rellenable
    # sea mejor, con los campos un poquito más grandes cuando se descarga»).
    # Esto se rellena a mano, muchas veces en una tablet y con el dedo: un
    # recuadro de 6,6 mm y letra de 8 no se ve ni se acierta. Caben menos fichas
    # por página, y da igual: el PDF es para trabajar, no para ahorrar papel.
    card_h = 41 * mm
    row_gap = 3.4 * mm

    field_n = [0]

    def header(page_no):
        c.setFillColor(C_ACC)
        c.rect(0, H - 11 * mm, W, 11 * mm, stroke=0, fill=1)
        c.setFillColor(HexColor("#ffffff"))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(ML, H - 7.6 * mm, "NOMENCLATURAS MV · Catálogo de familias")
        c.setFont("Helvetica", 8)
        c.drawRightString(W - MR, H - 7.6 * mm, f"Tarifa {tariff} · rellenable")
        c.setFillColor(C_MUT)
        c.setFont("Helvetica", 7)
        c.drawRightString(W - MR, MB - 6 * mm, con_marca(f"pág. {page_no}", separador=" · "))

    def card(col, top_y, fam, meta, codes):
        titulo, tipo, desc = meta
        x = ML + (col_w + col_gap) * col
        y = top_y - card_h
        # marco
        c.setFillColor(HexColor("#ffffff"))
        c.setStrokeColor(C_LINE); c.setLineWidth(1)
        c.roundRect(x, y, col_w, card_h, 3 * mm, stroke=1, fill=1)
        # caja icono
        ib = 24 * mm
        ix, iy = x + 3 * mm, y + card_h - ib - 3 * mm
        c.setFillColor(C_ICONB); c.setStrokeColor(C_LINE)
        c.roundRect(ix, iy, ib, ib, 2 * mm, stroke=1, fill=1)
        _draw_icon(c, tipo, ix, iy, ib)
        # texto
        tx = ix + ib + 3.5 * mm
        c.setFillColor(C_TXT); c.setFont("Helvetica-Bold", 10.2)
        c.drawString(tx, y + card_h - 6.6 * mm, titulo[:32])
        # familia (código base) chip
        base = min(codes, key=len) if codes else ""
        base = re.sub(r"\d.*$", "", base) or base
        c.setFillColor(C_ACC_L)
        cw = c.stringWidth(base, "Helvetica-Bold", 8) + 5 * mm
        c.roundRect(tx, y + card_h - 12.4 * mm, cw, 5.0 * mm, 2 * mm, stroke=0, fill=1)
        c.setFillColor(C_ACC); c.setFont("Helvetica-Bold", 8.6)
        c.drawString(tx + 2.5 * mm, y + card_h - 11.2 * mm, base)
        # anchos
        ws = _widths(codes)
        if ws:
            txt = "Anchos: " + "·".join(str(w) for w in ws) + " cm"
        else:
            txt = f"{len(codes)} referencia(s)"
        c.setFillColor(C_MUT); c.setFont("Helvetica", 7.2)
        c.drawString(tx, y + card_h - 17.0 * mm, txt[:50])
        if desc:
            c.drawString(tx, y + card_h - 20.6 * mm, desc[:50])
        # ── EL RECUADRO PARA RELLENAR ────────────────────────────────────
        # Sigue siendo UNO por familia, y eso es a propósito: quien lo lee al
        # subirlo (`mv_relacion.extract_campos`) junta el valor con la ETIQUETA
        # del recuadro, así que una nota sin código —«2 · 60x80»— se entiende
        # porque se sabe de qué familia es. Partirlo en cuatro casillas sueltas
        # (uds, ancho, alto, notas) daría cuatro valores sin relación entre
        # ellos y habría que rehacer el lector; no compensa.
        #
        # Lo que sí cambia es el TAMAÑO y la PISTA. Antes ponía «Notas / medidas
        # / uds» y había que adivinar el formato; ahora se enseña escrito.
        fh = 10.5 * mm
        fx, fy = x + 3 * mm, y + 3 * mm
        fw = col_w - 6 * mm
        c.setFillColor(C_FIELD); c.setStrokeColor(C_FIELDB); c.setLineWidth(1.0)
        c.roundRect(fx, fy, fw, fh, 1.8 * mm, stroke=1, fill=1)
        # La etiqueta, con el formato que se espera. Un ejemplo vale más que una
        # explicación: quien rellena copia el patrón sin leer nada.
        c.setFillColor(C_MUT); c.setFont("Helvetica-Bold", 6.8)
        c.drawString(fx, fy + fh + 1.4 * mm, "Uds · código o medidas")
        c.setFillColor(HexColor("#94a3b8")); c.setFont("Helvetica-Oblique", 6.4)
        ej = f"ej.:  2 · {codes[0]}" if codes else "ej.:  2 · 60x80"
        c.drawRightString(fx + fw, fy + fh + 1.4 * mm, ej[:34])
        field_n[0] += 1
        c.acroForm.textfield(
            name=f"nota_{field_n[0]}", tooltip=f"{titulo}",
            x=fx + 1.2 * mm, y=fy + 1.2 * mm,
            width=fw - 2.4 * mm, height=fh - 2.4 * mm,
            borderWidth=0, forceBorder=False, fontSize=11,
            fillColor=C_FIELD, textColor=C_TXT, fieldFlags="",
        )

    # Portada breve + notas
    page = 1
    header(page)
    y = H - MT - 8 * mm
    c.setFillColor(C_TXT); c.setFont("Helvetica-Bold", 15)
    c.drawString(ML, y, "Muebles tipo a fabricar — nomenclatura")
    y -= 6 * mm
    c.setFillColor(C_MUT); c.setFont("Helvetica", 8.5)
    c.drawString(ML, y, "Una ficha por familia con su dibujo, código base y anchos disponibles. Rellena los recuadros amarillos.")
    y -= 7 * mm
    for n in NOTAS:
        c.setFillColor(C_ACC); c.setFont("Helvetica-Bold", 8)
        c.drawString(ML, y, "•")
        c.setFillColor(C_MUT); c.setFont("Helvetica", 8)
        c.drawString(ML + 3.5 * mm, y, n)
        y -= 4.6 * mm
    y -= 3 * mm

    # Zona de tarjetas: rejilla de 2 columnas. La primera página arranca bajo la
    # portada (y actual); las siguientes desde el tope.
    fam_list = [(f, FAM_META[f], list((info.get("items") or {}).keys()))
                for f, info in fams.items() if f in FAM_META]

    top_first = y                    # bajo la portada/notas
    top_next = H - MT                # tope en páginas siguientes
    top_y = top_first
    col = 0
    row_top = top_y
    for fam, meta, codes in fam_list:
        # ¿cabe una fila de tarjetas a partir de row_top?
        if row_top - card_h < MB:
            c.showPage(); page += 1; header(page)
            row_top = top_next
            col = 0
        card(col, row_top, fam, meta, codes)
        if col == 0:
            col = 1
        else:
            col = 0
            row_top -= card_h + row_gap

    c.showPage()
    c.save()
    return buf.getvalue()


if __name__ == "__main__":
    b = build_nomenclaturas_pdf()
    with open("/tmp/nomenclaturas_mv.pdf", "wb") as f:
        f.write(b)
    print("OK", len(b), "bytes")
