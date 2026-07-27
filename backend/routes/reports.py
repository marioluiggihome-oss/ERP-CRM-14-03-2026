"""
Reports Router - Generador de informes con filtros avanzados
=============================================================
Permite generar informes de rentabilidad, ventas, costes y márgenes
con filtros por fecha, cliente, categoría, tipo de documento, etc.
Exporta en JSON (para frontend) y PDF (para descarga).
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List
from datetime import datetime, date
import logging
import re

logger = logging.getLogger("reports")

# Seguridad: estos informes exponen facturacion, margenes y el desglose por
# cliente de toda la empresa (incluido descargable en PDF). Antes no exigian
# ningun token: cualquiera que conociera la URL podia verlos. Mismo criterio
# de acceso que el resto de Rentabilidad (rol elevado o canAccessRentabilidad).
try:
    from services.jwt_service import require_auth, ADMIN_ROLE_FLAGS

    async def require_reports_access(user: dict = Depends(require_auth)):
        if any(user.get(f) for f in ADMIN_ROLE_FLAGS) or user.get("canAccessRentabilidad"):
            return user
        raise HTTPException(status_code=403, detail="Sin acceso a los informes de rentabilidad")
    _REPORTS_DEPS = [Depends(require_reports_access)]
except Exception:  # pragma: no cover - fallback si no hay jwt_service
    _REPORTS_DEPS = []

router = APIRouter(tags=["reports"], dependencies=_REPORTS_DEPS)


# ========== HELPERS ==========

def classify_line(concepto: str) -> str:
    """Clasifica una línea de factura en categoría de producto.

    Coincidencia por PALABRA COMPLETA: buscar "placa" como subcadena marcaba
    "aplacado" (una encimera) como placa de cocción. Con límites de palabra cada
    término solo casa consigo mismo.
    """
    c = (concepto or "").lower()

    def tiene(*claves):
        return any(re.search(r'\b' + re.escape(k) + r'\w*', c) for k in claves)

    # Lo más específico primero.
    if tiene('lavadora'):
        return 'Lavadoras'
    if tiene('secadora'):
        return 'Secadoras'
    if tiene('lavavajillas'):
        return 'Lavavajillas'
    if tiene('combi', 'frigorífico', 'frigorifico', 'nevera'):
        return 'Refrigeración'
    if tiene('campana', 'extractor'):
        return 'Campanas'
    if tiene('horno'):
        return 'Hornos'
    if tiene('microondas'):
        return 'Microondas'
    if tiene('vinoteca', 'congelador', 'calentador', 'termo', 'caldera'):
        return 'Otros electrodomésticos'
    if tiene('grifo', 'grifería', 'griferia', 'monomando'):
        return 'Grifería'
    if tiene('fregadero', 'seno'):
        return 'Fregaderos'
    # Encimera ANTES que placa: "encimera ... con aplacado" es encimera.
    if tiene('encimera', 'silestone', 'dekton', 'granito', 'compac', 'neolith'):
        return 'Encimeras'
    if tiene('placa', 'inducción', 'induccion', 'vitrocerámica', 'vitroceramica'):
        return 'Placas de cocción'
    if tiene('fabricación', 'fabricacion') or 'cocina completa' in c or tiene('mueble'):
        return 'Fabricación mobiliario'
    if tiene('armario', 'vestidor'):
        return 'Armarios'
    if tiene('suelo', 'pavimento', 'tarima', 'parquet', 'parqué', 'laminado', 'spc',
             'vinílico', 'vinilico', 'rodapié', 'rodapie'):
        return 'Suelos'
    if tiene('aplacado', 'costado', 'panel', 'copete', 'zócalo', 'zocalo', 'remate', 'canto'):
        return 'Aplacados y remates'
    if tiene('puerta', 'frente', 'cajón', 'cajon', 'gaveta'):
        return 'Puertas y frentes'
    if tiene('herraje', 'bisagra', 'guía', 'guia', 'tirador', 'pata', 'colgador',
             'blum', 'accesorio'):
        return 'Herrajes y accesorios'
    if tiene('led', 'iluminación', 'iluminacion', 'luz', 'foco', 'enchufe', 'toma'):
        return 'Iluminación y electricidad'
    if tiene('tablero', 'melamina', 'banda', 'trasera', 'casco'):
        return 'Tableros y cascos'
    if tiene('montaje', 'instalación', 'instalacion') or 'mano de obra' in c:
        return 'Montaje/Instalación'
    if tiene('transporte', 'entregado', 'envío', 'envio', 'porte'):
        return 'Transporte/Logística'
    return 'Otros'


# ========== ENDPOINTS ==========

@router.get("/reports/rentabilidad")
async def generate_rentabilidad_report(
    fecha_desde: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    cliente: Optional[str] = Query(None, description="Filtrar por nombre de cliente (parcial)"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría de producto"),
    doc_type: Optional[str] = Query(None, description="Tipo de documento: factura, presupuesto, pedido"),
    min_venta: Optional[float] = Query(None, description="Venta mínima por línea"),
    max_venta: Optional[float] = Query(None, description="Venta máxima por línea"),
    created_by: Optional[str] = Query(None, description="Filtrar por usuario creador"),
    revisada: Optional[str] = Query(None, description="Check Controller: 'si' revisadas, 'no' faltan por revisar"),
    sort_by: Optional[str] = Query("fecha", description="Ordenar por: fecha, venta, margen, cliente"),
    sort_order: Optional[str] = Query("desc", description="Orden: asc, desc"),
):
    """
    Genera un informe de rentabilidad por líneas con filtros avanzados.
    Devuelve datos estructurados para el frontend y para generar PDF.
    """
    from server import db

    try:
        # Se filtra en MONGO lo que se puede (fecha, tipo, revisada) en vez de
        # traerlo todo y filtrar en Python. Antes se leía find({}) con tope 1000:
        # al superar 1000 fichas el informe PERDÍA documentos EN SILENCIO y los
        # totales salían mal sin avisar. Ahora se acota la consulta y se detecta
        # el truncado para avisar.
        q = {}
        if fecha_desde or fecha_hasta:
            rango = {}
            if fecha_desde:
                rango["$gte"] = fecha_desde
            if fecha_hasta:
                rango["$lte"] = fecha_hasta
            q["fecha"] = rango
        if doc_type:
            q["docType"] = {"$regex": f"^{re.escape(doc_type)}$", "$options": "i"}
        # OJO: `revisada` NO se empuja a Mongo. En base puede estar como booleano,
        # como "si" o como 1 según cómo se marcara; una igualdad estricta dejaría
        # fichas fuera. Se sigue filtrando en Python (por veracidad), que ya cubre
        # todas las variantes.

        MAX_FICHAS = 20000
        fichas = await db["sale_fichas"].find(q).sort("fecha", -1).to_list(length=MAX_FICHAS)
        truncado = len(fichas) >= MAX_FICHAS
        if truncado:
            logger.warning("reports: consulta truncada en %s fichas; el informe puede estar incompleto", MAX_FICHAS)

        # Coste EFECTIVO de una linea (alineado con Rentabilidad): en un ABONO
        # (venta < 0) el coste resta en negativo para que el margen sea el neto
        # (suma y resta), no la perdida total.
        def _coste_ef(line):
            v = float(line.get("venta", 0) or 0)
            c = float(line.get("coste", 0) or 0)
            return -abs(c) if v < 0 else c

        # Aplicar filtros
        filtered_fichas = []
        for ficha in fichas:
            # Documentos CONVERTIDOS (pedido->factura, etc.): su importe vive en el
            # documento de destino; incluirlos duplicaria las lineas (igual que en
            # la pantalla de Rentabilidad, se excluyen de los totales).
            if ficha.get("convertidoAId"):
                continue
            # Filtro por fecha
            ficha_fecha = ficha.get("fecha", "")
            if fecha_desde and ficha_fecha < fecha_desde:
                continue
            if fecha_hasta and ficha_fecha > fecha_hasta:
                continue

            # Filtro por Check Controller (revisada por el controller)
            if revisada == "si" and not ficha.get("revisada"):
                continue
            if revisada == "no" and ficha.get("revisada"):
                continue
            
            # Filtro por cliente: casa por NOMBRE o por CÓDIGO. Acepta VARIOS
            # clientes separados por '|' (no por coma, porque muchos nombres de
            # empresa la llevan: "... MONTELLANO, S.L."). Casa cualquiera de ellos.
            if cliente:
                queries = [c.lower().strip() for c in cliente.split("|") if c.strip()]
                ficha_cliente = ficha.get("cliente", "").lower()
                ficha_cod = str(ficha.get("clienteCodigo", "") or "").lower()
                if queries and not any(q in ficha_cliente or q in ficha_cod for q in queries):
                    continue
            
            # Filtro por tipo de documento
            if doc_type:
                if ficha.get("docType", "").lower() != doc_type.lower():
                    continue
            
            # Filtro por creador
            if created_by:
                if created_by.lower() not in ficha.get("createdByName", "").lower():
                    continue
            
            # Filtrar líneas por categoría y rango de venta
            lines = ficha.get("lines", [])
            filtered_lines = []
            for line in lines:
                # Filtro por categoría
                if categoria:
                    line_cat = classify_line(line.get("concepto", ""))
                    if categoria.lower() not in line_cat.lower():
                        continue
                
                # Filtro por rango de venta
                line_venta = line.get("venta", 0)
                if min_venta is not None and line_venta < min_venta:
                    continue
                if max_venta is not None and line_venta > max_venta:
                    continue
                
                filtered_lines.append(line)
            
            if filtered_lines:
                ficha_copy = {
                    "id": ficha.get("id", ""),
                    "ref": ficha.get("ref", ""),
                    "cliente": ficha.get("cliente", ""),
                    "fecha": ficha_fecha,
                    "docType": ficha.get("docType", ""),
                    "createdByName": ficha.get("createdByName", ""),
                    # Estado del Check Controller (para mostrarlo/filtrarlo en el informe).
                    "revisada": bool(ficha.get("revisada")),
                    "revisadaPor": ficha.get("revisadaPor", ""),
                    "revisadaAt": ficha.get("revisadaAt", ""),
                    "lines": filtered_lines,
                    "totals": {
                        "venta": sum(l.get("venta", 0) for l in filtered_lines),
                        "coste": sum(_coste_ef(l) for l in filtered_lines),
                        "margen": sum((float(l.get("venta", 0) or 0) - _coste_ef(l)) for l in filtered_lines),
                    }
                }
                # % unificado = incremento sobre coste (margen / coste)
                ficha_copy["totals"]["margenPct"] = (
                    (ficha_copy["totals"]["margen"] / ficha_copy["totals"]["coste"] * 100)
                    if ficha_copy["totals"]["coste"] > 0 else 0
                )
                filtered_fichas.append(ficha_copy)
        
        # Ordenar
        sort_key_map = {
            "fecha": lambda x: x.get("fecha", ""),
            "venta": lambda x: x["totals"]["venta"],
            "margen": lambda x: x["totals"]["margen"],
            "cliente": lambda x: x.get("cliente", ""),
        }
        sort_fn = sort_key_map.get(sort_by, sort_key_map["fecha"])
        filtered_fichas.sort(key=sort_fn, reverse=(sort_order == "desc"))
        
        # Calcular totales generales
        total_venta = sum(f["totals"]["venta"] for f in filtered_fichas)
        total_coste = sum(f["totals"]["coste"] for f in filtered_fichas)
        total_margen = sum(f["totals"]["margen"] for f in filtered_fichas)
        total_lines = sum(len(f["lines"]) for f in filtered_fichas)
        
        # Análisis por categoría
        categorias = {}
        for ficha in filtered_fichas:
            for line in ficha["lines"]:
                cat = classify_line(line.get("concepto", ""))
                if cat not in categorias:
                    categorias[cat] = {"venta": 0, "coste": 0, "margen": 0, "count": 0}
                _v = float(line.get("venta", 0) or 0)
                _ce = _coste_ef(line)
                categorias[cat]["venta"] += _v
                categorias[cat]["coste"] += _ce
                categorias[cat]["margen"] += (_v - _ce)
                categorias[cat]["count"] += 1
        
        # Análisis por cliente
        clientes = {}
        for ficha in filtered_fichas:
            cli = ficha.get("cliente", "Sin nombre")
            if cli not in clientes:
                clientes[cli] = {"venta": 0, "coste": 0, "margen": 0, "docs": 0}
            clientes[cli]["venta"] += ficha["totals"]["venta"]
            clientes[cli]["coste"] += ficha["totals"]["coste"]
            clientes[cli]["margen"] += ficha["totals"]["margen"]
            clientes[cli]["docs"] += 1
        
        # Top productos por venta
        all_lines = []
        for ficha in filtered_fichas:
            for line in ficha["lines"]:
                all_lines.append({
                    **line,
                    "cliente": ficha.get("cliente", ""),
                    "docRef": ficha.get("ref", ""),
                    "fecha": ficha.get("fecha", ""),
                    "categoria": classify_line(line.get("concepto", ""))
                })
        all_lines.sort(key=lambda x: x.get("venta", 0), reverse=True)
        
        return {
            "success": True,
            "generatedAt": datetime.utcnow().isoformat(),
            "filters": {
                "fecha_desde": fecha_desde,
                "fecha_hasta": fecha_hasta,
                "cliente": cliente,
                "categoria": categoria,
                "doc_type": doc_type,
                "min_venta": min_venta,
                "max_venta": max_venta,
                "created_by": created_by,
            },
            "truncado": truncado,
            "summary": {
                "totalVenta": round(total_venta, 2),
                "totalCoste": round(total_coste, 2),
                "totalMargen": round(total_margen, 2),
                # % unificado = incremento sobre coste (margen / coste)
                "margenPct": round((total_margen / total_coste * 100) if total_coste > 0 else 0, 2),
                "numFichas": len(filtered_fichas),
                "numLineas": total_lines,
            },
            "byCategory": [
                {"categoria": k, **v, "pctTotal": round(v["venta"] / total_venta * 100, 2) if total_venta > 0 else 0}
                for k, v in sorted(categorias.items(), key=lambda x: x[1]["venta"], reverse=True)
            ],
            "byClient": [
                {"cliente": k, **v, "pctTotal": round(v["venta"] / total_venta * 100, 2) if total_venta > 0 else 0}
                for k, v in sorted(clientes.items(), key=lambda x: x[1]["venta"], reverse=True)
            ],
            "fichas": filtered_fichas,
            "topLines": all_lines[:20],
        }
    
    except Exception as e:
        logger.error(f"Error generando informe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/rentabilidad/pdf")
async def generate_rentabilidad_pdf(
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    cliente: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    doc_type: Optional[str] = Query(None),
    min_venta: Optional[float] = Query(None),
    max_venta: Optional[float] = Query(None),
    created_by: Optional[str] = Query(None),
    revisada: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("fecha"),
    sort_order: Optional[str] = Query("desc"),
    detalle: Optional[int] = Query(0, description="1 = PDF superdetallado: TODOS los productos, documento a documento"),
):
    """
    Genera un PDF del informe de rentabilidad con los mismos filtros.
    Con `detalle=1` añade el desglose COMPLETO: cada documento con todas sus
    líneas de producto (cantidad, coste, venta, margen y % sobre coste).
    """
    from fastapi.responses import StreamingResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import mm
    import io
    
    # Obtener datos con los mismos filtros
    data = await generate_rentabilidad_report(
        fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
        cliente=cliente, categoria=categoria, doc_type=doc_type,
        min_venta=min_venta, max_venta=max_venta,
        created_by=created_by, revisada=revisada, sort_by=sort_by, sort_order=sort_order
    )
    
    if not data.get("success"):
        raise HTTPException(status_code=500, detail="Error generando datos del informe")
    
    # ── Paleta y marca (marca blanca: nombre de empresa desde settings) ──────
    INK = colors.HexColor('#1e1b4b')       # tinta principal (azul noche)
    ACCENT = colors.HexColor('#4f46e5')    # indigo
    GREEN = colors.HexColor('#059669')     # margen positivo
    RED = colors.HexColor('#dc2626')       # margen negativo
    SLATE = colors.HexColor('#64748b')     # texto tenue
    HEADBG = colors.HexColor('#1e293b')    # cabecera de tabla
    ROWALT = colors.HexColor('#f8fafc')    # fila alterna
    LINE = colors.HexColor('#e2e8f0')      # rejilla suave
    try:
        from server import db as _db
        _settings = await _db["settings"].find_one({"id": "global-settings"}) or {}
        company = (_settings.get("companyName") or "").strip()
    except Exception:
        company = ""

    def _eur(v):
        # Formato ESPAÑOL: miles con punto y decimales con coma (1.234,56 €).
        try:
            t = f"{float(v):,.2f}"
            return t.replace(",", "\x00").replace(".", ",").replace("\x00", ".") + " €"
        except Exception:
            return "0,00 €"
    def _pct(v):
        # Formato ESPAÑOL: decimales con coma (46,88%).
        try:
            return f"{float(v):.2f}".replace(".", ",") + "%"
        except Exception:
            return "0,00%"

    # Generar PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=16*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle('T', parent=styles['Title'], fontSize=19, spaceAfter=2, textColor=INK, alignment=0)
    eyebrow_style = ParagraphStyle('E', parent=styles['Normal'], fontSize=8, textColor=ACCENT, spaceAfter=1, fontName='Helvetica-Bold')
    subtitle_style = ParagraphStyle('S', parent=styles['Normal'], fontSize=9, textColor=SLATE)
    section_style = ParagraphStyle('H', parent=styles['Normal'], fontSize=11, textColor=INK, fontName='Helvetica-Bold', spaceAfter=3, spaceBefore=2)

    # ── Cabecera de marca ────────────────────────────────────────────────────
    if company:
        elements.append(Paragraph(company.upper(), eyebrow_style))
    elements.append(Paragraph("Informe de rentabilidad", title_style))
    elements.append(Paragraph("Venta − Coste = Margen · por proyecto", subtitle_style))

    # Filtros aplicados (en una línea sobria)
    filters_text = []
    if fecha_desde: filters_text.append(f"Desde {fecha_desde}")
    if fecha_hasta: filters_text.append(f"Hasta {fecha_hasta}")
    if cliente: filters_text.append(f"Cliente: {cliente}")
    if categoria: filters_text.append(f"Categoría: {categoria}")
    if doc_type: filters_text.append(f"Tipo: {doc_type}")
    if revisada == "si": filters_text.append("Solo documentos validados")
    elif revisada == "no": filters_text.append("Solo pendientes de validar")
    meta = f"Generado {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    if filters_text:
        meta += "  ·  " + "  ·  ".join(filters_text)
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph(meta, subtitle_style))
    elements.append(Spacer(1, 6*mm))

    # ── KPIs en tarjetas (Coste · Venta · Margen · % · Docs · Líneas) ────────
    summary = data["summary"]
    margen_val = summary['totalMargen']
    INK_H, GREEN_H, RED_H, ACCENT_H = '#1e1b4b', '#059669', '#dc2626', '#4f46e5'
    mpos = margen_val >= 0
    ppos = summary['margenPct'] >= 0
    kpi_cells = [
        ("COSTE TOTAL", _eur(summary['totalCoste']), INK_H),
        ("VENTA TOTAL", _eur(summary['totalVenta']), INK_H),
        ("MARGEN BRUTO", _eur(margen_val), GREEN_H if mpos else RED_H),
        ("% S/COSTE", _pct(summary['margenPct']), GREEN_H if ppos else RED_H),
        ("DOCUMENTOS", str(summary['numFichas']), ACCENT_H),
        ("LÍNEAS", str(summary['numLineas']), ACCENT_H),
    ]
    labels = [Paragraph(f"<font size=6.5 color='#94a3b8'><b>{l}</b></font>", styles['Normal']) for l, _, _ in kpi_cells]
    values = [Paragraph(f"<font size=13 color='{c}'><b>{v}</b></font>", styles['Normal']) for _, v, c in kpi_cells]
    kpi = Table([labels, values], colWidths=[86]*6)
    kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.6, LINE),
        ('INNERGRID', (0, 0), (-1, -1), 0.6, colors.white),
        ('LINEBEFORE', (1, 0), (-1, -1), 0.6, LINE),
        ('TOPPADDING', (0, 0), (-1, 0), 8), ('BOTTOMPADDING', (0, 0), (-1, 0), 1),
        ('TOPPADDING', (0, 1), (-1, 1), 0), ('BOTTOMPADDING', (0, 1), (-1, 1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(kpi)
    elements.append(Spacer(1, 7*mm))

    # ── Helper de tabla con estilo (orden Coste · Venta · Margen · %) ────────
    # Estilo de celda de TEXTO: se envuelve en Paragraph para que el texto largo
    # HAGA SALTO DE LÍNEA en vez de desbordarse encima de la columna siguiente
    # (era la causa de que "Ref/Concepto/Cliente" salieran pisados).
    cell_style = ParagraphStyle('cell', parent=styles['Normal'], fontSize=7.2, leading=8.6, textColor=INK)
    head_style = ParagraphStyle('head', parent=styles['Normal'], fontSize=7, leading=8.4,
                                textColor=colors.white, fontName='Helvetica-Bold')

    def styled_table(title, headers, rows, colw, money_cols=(), margin_col=None, pct_col=None,
                     text_cols=(0,), total_row=False):
        if title:
            elements.append(Paragraph(title, section_style))
        headers = [Paragraph(str(h), head_style) for h in headers]
        rows = [[Paragraph(str(v), cell_style) if i in text_cols else v
                 for i, v in enumerate(r)] for r in rows]
        body = [headers] + rows
        t = Table(body, colWidths=colw, repeatRows=1)
        st = [
            ('BACKGROUND', (0, 0), (-1, 0), HEADBG),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('FONTSIZE', (0, 1), (-1, -1), 7.5),
            ('TEXTCOLOR', (0, 1), (-1, -1), INK),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ROWALT]),
            ('LINEBELOW', (0, 0), (-1, 0), 0.8, ACCENT),
            ('LINEBELOW', (0, 1), (-1, -2), 0.4, LINE),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]
        # margen en verde/rojo
        if margin_col is not None:
            for i, r in enumerate(rows, start=1):
                try:
                    _cell = r[margin_col]
                    _txt = _cell.text if hasattr(_cell, 'text') else str(_cell)
                    val = float(_txt.replace('.', '').replace(',', '.').replace('€', '').replace('%', '').strip())
                except Exception:
                    val = 0
                st.append(('TEXTCOLOR', (margin_col, i), (margin_col, i), GREEN if val >= 0 else RED))
                st.append(('FONTNAME', (margin_col, i), (margin_col, i), 'Helvetica-Bold'))
        if pct_col is not None:
            st.append(('TEXTCOLOR', (pct_col, 1), (pct_col, -1), SLATE))
        if total_row and len(rows) >= 1:
            i = len(rows)   # última fila (índice en la tabla, con cabecera en 0)
            st += [('BACKGROUND', (0, i), (-1, i), colors.HexColor('#eef2ff')),
                   ('FONTNAME', (0, i), (-1, i), 'Helvetica-Bold'),
                   ('LINEABOVE', (0, i), (-1, i), 0.8, ACCENT)]
        t.setStyle(TableStyle(st))
        elements.append(t)
        elements.append(Spacer(1, 6*mm))

    # Por categoría — orden Coste · Venta · Margen · %
    if data["byCategory"]:
        rows = [[c["categoria"], str(c["count"]), _eur(c['coste']), _eur(c['venta']), _eur(c['margen']), _pct(c['pctTotal'])] for c in data["byCategory"]]
        styled_table("Por categoría", ["Categoría", "Líneas", "Coste", "Venta", "Margen", "% s/total"],
                     rows, [150, 42, 78, 78, 78, 52], margin_col=4, pct_col=5, text_cols=(0,))

    # Por cliente
    if data["byClient"]:
        rows = [[c["cliente"], str(c["docs"]), _eur(c['coste']), _eur(c['venta']), _eur(c['margen']), _pct(c['pctTotal'])] for c in data["byClient"]]
        styled_table("Por cliente", ["Cliente", "Docs", "Coste", "Venta", "Margen", "% s/total"],
                     rows, [162, 38, 76, 76, 76, 50], margin_col=4, pct_col=5, text_cols=(0,))

    # Top líneas por venta
    if data["topLines"]:
        rows = [[l.get("ref", "—") or "—", l.get("concepto", ""), l.get("cliente", ""),
                 _eur(l.get('venta', 0)), l.get("categoria", "")] for l in data["topLines"][:15]]
        styled_table("Top líneas por venta", ["Ref", "Concepto", "Cliente", "Venta", "Categoría"],
                     rows, [70, 190, 110, 62, 86], text_cols=(0, 1, 2, 4))

    # ── DETALLE COMPLETO POR DOCUMENTO Y PRODUCTO (PDF superdetallado) ──────
    if detalle:
        from reportlab.platypus import PageBreak
        elements.append(PageBreak())
        elements.append(Paragraph("Detalle por documento y producto", section_style))
        elements.append(Paragraph(
            "<font size=7.5 color='#64748b'>Todas las líneas de los documentos incluidos en el informe. "
            "% = margen sobre coste.</font>", styles['Normal']))
        elements.append(Spacer(1, 4*mm))
        for ficha in data.get("fichas", []):
            tot = ficha.get("totals", {}) or {}
            cab = (f"<b>{(ficha.get('ref') or '—')}</b> · {(ficha.get('cliente') or 'Sin cliente')[:46]}"
                   f" · {(ficha.get('fecha') or '')[:10]} · {(ficha.get('docType') or '').upper()}")
            if ficha.get("revisada"):
                cab += f" · <font color='#059669'>revisada{(' por ' + str(ficha.get('revisadaPor'))) if ficha.get('revisadaPor') else ''}</font>"
            elements.append(Paragraph(f"<font size=8.5 color='#0f172a'>{cab}</font>", styles['Normal']))
            filas = []
            for ln in ficha.get("lines", []):
                v = float(ln.get("venta", 0) or 0)
                c = float(ln.get("coste", 0) or 0)
                c = -abs(c) if v < 0 else c
                mg = v - c
                pc = (mg / c * 100) if c > 0 else 0
                cant = ln.get("cantidad", "")
                filas.append([
                    str(ln.get("ref", "") or "—"),
                    str(ln.get("concepto", "") or ""),
                    (f"{cant:g}".replace(".", ",") if isinstance(cant, (int, float)) else str(cant or "")),
                    _eur(c), _eur(v), _eur(mg), _pct(pc),
                ])
            if filas:
                filas.append(["", "TOTAL DOCUMENTO", "", _eur(tot.get("coste", 0)),
                              _eur(tot.get("venta", 0)), _eur(tot.get("margen", 0)),
                              _pct(tot.get("margenPct", 0))])
                styled_table("", ["Ref", "Producto / concepto", "Uds", "Coste", "Venta", "Margen", "%"],
                             filas, [68, 188, 28, 62, 62, 62, 42],
                             margin_col=5, pct_col=6, text_cols=(0, 1), total_row=True)

    # Footer sobrio (marca blanca)
    elements.append(Spacer(1, 6*mm))
    foot = company or "Informe de rentabilidad"
    elements.append(Paragraph(f"<font size=7 color='#94a3b8'>{foot} · Informe generado automáticamente</font>", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    
    filename = f"informe_rentabilidad_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/reports/available-filters")
async def get_available_filters():
    """Devuelve los valores disponibles para los filtros (clientes, categorías, etc.)"""
    from server import db

    try:
        # Solo se necesitan estos campos para poblar los desplegables de filtros:
        # con proyección y un tope alto no se pierden clientes al crecer la base.
        fichas = await db["sale_fichas"].find(
            {}, {"_id": 0, "cliente": 1, "clienteCodigo": 1, "docType": 1,
                 "createdByName": 1, "lines.concepto": 1}
        ).to_list(length=20000)

        clientes = set()
        clientes_map = {}  # nombre -> codigo (para poder buscar por código de cliente)
        categorias = set()
        creadores = set()
        doc_types = set()
        fechas = []

        for ficha in fichas:
            nom = ficha.get("cliente", "")
            clientes.add(nom)
            if nom and nom not in clientes_map:
                clientes_map[nom] = str(ficha.get("clienteCodigo", "") or "")
            doc_types.add(ficha.get("docType", ""))
            creadores.add(ficha.get("createdByName", ""))
            if ficha.get("fecha"):
                fechas.append(ficha["fecha"])
            for line in ficha.get("lines", []):
                categorias.add(classify_line(line.get("concepto", "")))

        return {
            "clientes": sorted([c for c in clientes if c]),
            "clientesInfo": sorted(
                [{"nombre": n, "codigo": c} for n, c in clientes_map.items() if n],
                key=lambda x: x["nombre"],
            ),
            "categorias": sorted([c for c in categorias if c]),
            "creadores": sorted([c for c in creadores if c]),
            "docTypes": sorted([d for d in doc_types if d]),
            "fechaMin": min(fechas) if fechas else None,
            "fechaMax": max(fechas) if fechas else None,
        }
    except Exception as e:
        logger.error(f"Error obteniendo filtros: {e}")
        raise HTTPException(status_code=500, detail=str(e))
