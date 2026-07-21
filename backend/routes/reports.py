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
    """Clasifica una línea de factura en categoría de producto."""
    c = concepto.lower()
    if 'lavadora' in c:
        return 'Lavadoras'
    elif 'secadora' in c:
        return 'Secadoras'
    elif 'lavavajillas' in c:
        return 'Lavavajillas'
    elif 'combi' in c or 'frigorífico' in c or 'frigorifico' in c:
        return 'Refrigeración'
    elif 'campana' in c:
        return 'Campanas'
    elif 'placa' in c or 'inducción' in c or 'induccion' in c:
        return 'Placas de cocción'
    elif 'horno' in c:
        return 'Hornos'
    elif 'microondas' in c:
        return 'Microondas'
    elif 'grifo' in c or 'monomando' in c:
        return 'Grifería'
    elif 'fregadero' in c:
        return 'Fregaderos'
    elif 'fabricación' in c or 'fabricacion' in c or 'cocina completa' in c or 'mueble' in c:
        return 'Fabricación mobiliario'
    elif 'transporte' in c or 'entregado' in c or 'envío' in c or 'envio' in c:
        return 'Transporte/Logística'
    elif 'armario' in c or 'vestidor' in c:
        return 'Armarios'
    elif 'encimera' in c or 'silestone' in c or 'dekton' in c:
        return 'Encimeras'
    elif 'montaje' in c or 'instalación' in c or 'instalacion' in c:
        return 'Montaje/Instalación'
    else:
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
        # Obtener todas las fichas de rentabilidad (por líneas de documentos)
        fichas_cursor = db["sale_fichas"].find({})
        fichas = await fichas_cursor.to_list(length=1000)

        # Aplicar filtros
        filtered_fichas = []
        for ficha in fichas:
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
            # clientes separados por coma; basta con que case cualquiera de ellos.
            if cliente:
                queries = [c.lower().strip() for c in cliente.split(",") if c.strip()]
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
                        "coste": sum(l.get("coste", 0) for l in filtered_lines),
                        "margen": sum(l.get("margen", 0) for l in filtered_lines),
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
                categorias[cat]["venta"] += line.get("venta", 0)
                categorias[cat]["coste"] += line.get("coste", 0)
                categorias[cat]["margen"] += line.get("margen", 0)
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
            "summary": {
                "totalVenta": round(total_venta, 2),
                "totalCoste": round(total_coste, 2),
                "totalMargen": round(total_margen, 2),
                # % unificado = incremento sobre coste (margen / coste)
                "margenPct": round((total_margen / total_coste * 100) if total_coste > 0 else 0, 1),
                "numFichas": len(filtered_fichas),
                "numLineas": total_lines,
            },
            "byCategory": [
                {"categoria": k, **v, "pctTotal": round(v["venta"] / total_venta * 100, 1) if total_venta > 0 else 0}
                for k, v in sorted(categorias.items(), key=lambda x: x[1]["venta"], reverse=True)
            ],
            "byClient": [
                {"cliente": k, **v, "pctTotal": round(v["venta"] / total_venta * 100, 1) if total_venta > 0 else 0}
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
):
    """
    Genera un PDF del informe de rentabilidad con los mismos filtros.
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
        try:
            return f"{float(v):,.2f} €"
        except Exception:
            return "0,00 €"
    def _pct(v):
        try:
            return f"{float(v):.2f}%"
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
        ("% MARGEN", _pct(summary['margenPct']), GREEN_H if ppos else RED_H),
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
    def styled_table(title, headers, rows, colw, money_cols=(), margin_col=None, pct_col=None):
        elements.append(Paragraph(title, section_style))
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
                    val = float(str(r[margin_col]).replace('.', '').replace(',', '.').replace('€', '').replace('%', '').strip())
                except Exception:
                    val = 0
                st.append(('TEXTCOLOR', (margin_col, i), (margin_col, i), GREEN if val >= 0 else RED))
                st.append(('FONTNAME', (margin_col, i), (margin_col, i), 'Helvetica-Bold'))
        if pct_col is not None:
            st.append(('TEXTCOLOR', (pct_col, 1), (pct_col, -1), SLATE))
        t.setStyle(TableStyle(st))
        elements.append(t)
        elements.append(Spacer(1, 6*mm))

    # Por categoría — orden Coste · Venta · Margen · %
    if data["byCategory"]:
        rows = [[c["categoria"], str(c["count"]), _eur(c['coste']), _eur(c['venta']), _eur(c['margen']), _pct(c['pctTotal'])] for c in data["byCategory"]]
        styled_table("Por categoría", ["Categoría", "Líneas", "Coste", "Venta", "Margen", "% s/total"],
                     rows, [110, 42, 78, 78, 78, 50], margin_col=4, pct_col=5)

    # Por cliente
    if data["byClient"]:
        rows = [[c["cliente"][:34], str(c["docs"]), _eur(c['coste']), _eur(c['venta']), _eur(c['margen']), _pct(c['pctTotal'])] for c in data["byClient"]]
        styled_table("Por cliente", ["Cliente", "Docs", "Coste", "Venta", "Margen", "% s/total"],
                     rows, [130, 38, 74, 74, 74, 50], margin_col=4, pct_col=5)

    # Top líneas por venta
    if data["topLines"]:
        rows = [[l.get("ref", "—")[:12], l.get("concepto", "")[:44], l.get("cliente", "")[:22], _eur(l.get('venta', 0)), l.get("categoria", "")] for l in data["topLines"][:15]]
        styled_table("Top líneas por venta", ["Ref", "Concepto", "Cliente", "Venta", "Categoría"],
                     rows, [52, 168, 90, 60, 78])

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
        fichas_cursor = db["sale_fichas"].find({})
        fichas = await fichas_cursor.to_list(length=1000)

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
