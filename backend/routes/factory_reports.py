# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Factory Reports Router - LUIGGI HOME
Sistema de generación de informes PDF para fábrica con despiece y logo
"""
from fastapi import APIRouter, HTTPException, Depends
from services.jwt_service import require_auth
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone
from typing import Optional, List, Dict
import logging
import os
import io

# PDF Generation
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import base64
from io import BytesIO
from services.db_client import get_db as _get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fabrica/reports", tags=["Factory Reports"])

# Database connection


def get_logo_from_base64(logo_base64: str) -> Optional[Image]:
    """Convierte logo base64 a objeto Image de ReportLab"""
    if not logo_base64:
        return None
    
    try:
        # Remover prefijo data:image si existe
        if ',' in logo_base64:
            logo_base64 = logo_base64.split(',')[1]
        
        logo_data = base64.b64decode(logo_base64)
        logo_buffer = BytesIO(logo_data)
        
        # Crear imagen con tamaño máximo
        img = Image(logo_buffer, width=50*mm, height=20*mm)
        img._restrictSize(50*mm, 20*mm)
        return img
    except Exception as e:
        logger.warning(f"Error processing logo: {e}")
        return None


async def get_global_settings():
    """Obtener configuración global incluyendo logo"""
    settings = await _get_db().settings.find_one({"id": "global-settings"}, {"_id": 0})
    return settings or {}


def create_factory_report_pdf(
    order_data: dict,
    despiece_data: list,
    settings: dict
) -> bytes:
    """
    Genera un PDF de informe de fábrica completo con:
    - Logo de la empresa
    - Información del pedido
    - Lista de muebles
    - Despiece detallado por mueble
    - Especificaciones de materiales
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=10,
        alignment=TA_CENTER
    )
    
    # Estilo para subtítulos
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#ea580c'),
        spaceBefore=15,
        spaceAfter=8
    )
    
    # Estilo para texto normal
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#334155')
    )
    
    # Estilo para texto pequeño
    small_style = ParagraphStyle(
        'CustomSmall',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#64748b')
    )
    
    elements = []
    
    # ==========================================
    # HEADER CON LOGO
    # ==========================================
    logo = settings.get('logo')
    if logo:
        logo_img = get_logo_from_base64(logo)
        if logo_img:
            elements.append(logo_img)
            elements.append(Spacer(1, 5*mm))
    
    # Título principal
    elements.append(Paragraph("INFORME DE PRODUCCIÓN", title_style))
    elements.append(Paragraph("Orden de Fabricación", subtitle_style))
    
    # ==========================================
    # INFORMACIÓN DEL PEDIDO
    # ==========================================
    order_number = order_data.get('orderNumber', 'N/A')
    mfg_number = order_data.get('manufacturingNumber', '')
    customer_name = order_data.get('customerName', 'Sin especificar')
    created_at = order_data.get('createdAt', '')
    
    # Formatear fecha
    if created_at:
        try:
            date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime('%d/%m/%Y %H:%M')
        except Exception:
            formatted_date = created_at[:10] if len(created_at) > 10 else created_at
    else:
        formatted_date = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    # Tabla de información del pedido
    info_data = [
        ['Nº ORDEN:', order_number, 'Nº FAB:', str(mfg_number) if mfg_number else 'N/A'],
        ['CLIENTE:', customer_name, 'FECHA:', formatted_date],
        ['ESTADO:', order_data.get('status', 'N/A').upper(), 'PRIORIDAD:', order_data.get('priority', 'normal').upper()],
    ]
    
    # Dirección de entrega si existe
    delivery_address = order_data.get('deliveryAddress', '')
    if delivery_address:
        info_data.append(['DIRECCIÓN:', delivery_address, '', ''])
    
    info_table = Table(info_data, colWidths=[25*mm, 60*mm, 25*mm, 60*mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1e293b')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10*mm))
    
    # ==========================================
    # LISTA DE MUEBLES
    # ==========================================
    elements.append(Paragraph("LISTA DE MUEBLES A FABRICAR", subtitle_style))
    
    items = order_data.get('items', [])
    if items:
        furniture_data = [['CANT.', 'REF.', 'DESCRIPCIÓN', 'MEDIDAS (cm)', 'ESTADO']]
        
        for item in items:
            code = item.get('productCode', 'N/A')
            name = item.get('productName', 'Sin descripción')
            if len(name) > 40:
                name = name[:40] + '...'
            
            width = item.get('width', 0)
            height = item.get('height', 0)
            depth = item.get('depth', 0)
            dimensions = f"{width} × {height} × {depth}"
            
            status = item.get('status', 'pending')
            status_display = {
                'pending': 'Pendiente',
                'in_progress': 'En proceso',
                'cutting': 'Cortando',
                'assembling': 'Montando',
                'finished': 'Terminado'
            }.get(status, status)
            
            furniture_data.append([
                str(item.get('quantity', 1)),
                code.upper(),
                name,
                dimensions,
                status_display
            ])
        
        furniture_table = Table(furniture_data, colWidths=[15*mm, 25*mm, 70*mm, 35*mm, 25*mm])
        furniture_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            # Body
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#334155')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            # Alternating rows
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (3, 0), (3, -1), 'CENTER'),
            ('ALIGN', (4, 0), (4, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(furniture_table)
    
    elements.append(Spacer(1, 10*mm))
    
    # ==========================================
    # DESPIECE DETALLADO
    # ==========================================
    if despiece_data:
        elements.append(Paragraph("DESPIECE DE COMPONENTES", subtitle_style))
        elements.append(Paragraph(
            "Lista de corte para fabricación - Todas las medidas en centímetros (cm)",
            small_style
        ))
        elements.append(Spacer(1, 5*mm))
        
        for furniture in despiece_data:
            # Título del mueble
            furniture_title = f"{furniture.get('productCode', '')} - {furniture.get('productName', '')}"
            elements.append(Paragraph(f"<b>{furniture_title}</b>", normal_style))
            
            dims = f"Dimensiones: {furniture.get('originalWidth', 0)} × {furniture.get('originalHeight', 0)} × {furniture.get('originalDepth', 0)} cm"
            elements.append(Paragraph(dims, small_style))
            elements.append(Spacer(1, 2*mm))
            
            # Tabla de componentes
            components = furniture.get('components', [])
            if components:
                comp_data = [['CANT.', 'PIEZA', 'LARGO (cm)', 'ANCHO (cm)', 'GROSOR', 'MATERIAL']]
                
                for comp in components:
                    comp_data.append([
                        str(comp.get('quantity', 1)),
                        comp.get('nameShort', comp.get('name', '')),
                        f"{comp.get('length', 0):.1f}",
                        f"{comp.get('width', 0):.1f}",
                        f"{comp.get('thickness', 18):.0f}mm",
                        comp.get('material', '')[:25]
                    ])
                
                comp_table = Table(comp_data, colWidths=[12*mm, 30*mm, 22*mm, 22*mm, 18*mm, 55*mm])
                comp_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ea580c')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 7),
                    ('FONTSIZE', (0, 1), (-1, -1), 7),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                    ('ALIGN', (2, 0), (4, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff7ed')]),
                ]))
                elements.append(comp_table)
            
            elements.append(Spacer(1, 5*mm))
    
    # ==========================================
    # RESUMEN DE MATERIALES
    # ==========================================
    elements.append(Paragraph("RESUMEN DE MATERIALES", subtitle_style))
    
    # Calcular totales por material
    material_totals = {}
    for furniture in despiece_data:
        qty = furniture.get('itemQuantity', 1)
        for comp in furniture.get('components', []):
            mat = comp.get('material', 'Sin especificar')
            if mat not in material_totals:
                material_totals[mat] = {'pieces': 0, 'area': 0}
            material_totals[mat]['pieces'] += comp.get('quantity', 1) * qty
            material_totals[mat]['area'] += comp.get('area', 0) * qty
    
    if material_totals:
        summary_data = [['MATERIAL', 'PIEZAS', 'ÁREA (m²)']]
        total_pieces = 0
        total_area = 0
        
        for mat, data in material_totals.items():
            summary_data.append([
                mat[:40],
                str(data['pieces']),
                f"{data['area']:.3f}"
            ])
            total_pieces += data['pieces']
            total_area += data['area']
        
        summary_data.append(['TOTAL', str(total_pieces), f"{total_area:.3f}"])
        
        summary_table = Table(summary_data, colWidths=[100*mm, 30*mm, 30*mm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f1f5f9')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(summary_table)
    
    # ==========================================
    # FOOTER
    # ==========================================
    elements.append(Spacer(1, 15*mm))
    footer_text = f"Documento generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} - LUIGGI HOME Master Industrial System v2026"
    elements.append(Paragraph(footer_text, small_style))
    
    # Generar PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


@router.get("/production/{order_id}")
async def generate_production_report(order_id: str, current_user: dict = Depends(require_auth)):
    """
    Genera un PDF de informe de producción completo para una orden de fabricación.
    Incluye: Logo, datos del pedido, lista de muebles, despiece detallado.
    """
    try:
        # Obtener orden de fabricación
        order = await _get_db().manufacturing_orders.find_one({"id": order_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Orden de fabricación no encontrada")
        
        # Obtener configuración global (incluye logo)
        settings = await get_global_settings()
        
        # Calcular despiece para cada item
        despiece_data = []
        for item in order.get('items', []):
            # Determinar categoría
            code = item.get('productCode', '').upper()
            name = item.get('productName', '').upper()
            
            category = ''
            if any(x in name for x in ['ALTO', 'ALTILLO']) or code.startswith('A') or code.startswith('9A'):
                category = 'ALTO'
            elif any(x in name for x in ['BAJO', 'FREGADERO']) or code.startswith('B') or code.startswith('9B'):
                category = 'BAJO'
            elif 'COLUMNA' in name or code.startswith('C') or code.startswith('CH'):
                category = 'COLUMNA'
            
            # Crear estructura de despiece simplificada
            w = item.get('width', 60)
            h = item.get('height', 70)
            d = item.get('depth', 58)
            g = 1.8  # 18mm grosor casco en cm
            back_g = 0.8  # 8mm grosor trasera en cm
            
            fondo_interior = d - back_g
            ancho_interior = w - (2 * g)
            
            components = [
                {
                    "name": "Lateral izquierdo",
                    "nameShort": "LAT-I",
                    "material": "Melamina Blanca",
                    "length": h,
                    "width": fondo_interior,
                    "thickness": 18,
                    "quantity": 1,
                    "area": round((h * fondo_interior) / 10000, 4)
                },
                {
                    "name": "Lateral derecho",
                    "nameShort": "LAT-D",
                    "material": "Melamina Blanca",
                    "length": h,
                    "width": fondo_interior,
                    "thickness": 18,
                    "quantity": 1,
                    "area": round((h * fondo_interior) / 10000, 4)
                },
                {
                    "name": "Tapa superior",
                    "nameShort": "TAPA-S",
                    "material": "Melamina Blanca",
                    "length": ancho_interior,
                    "width": fondo_interior,
                    "thickness": 18,
                    "quantity": 1,
                    "area": round((ancho_interior * fondo_interior) / 10000, 4)
                },
                {
                    "name": "Tapa inferior",
                    "nameShort": "TAPA-I",
                    "material": "Melamina Blanca",
                    "length": ancho_interior,
                    "width": fondo_interior,
                    "thickness": 18,
                    "quantity": 1,
                    "area": round((ancho_interior * fondo_interior) / 10000, 4)
                },
                {
                    "name": "Trasera",
                    "nameShort": "TRAS",
                    "material": "Tablero 8mm",
                    "length": ancho_interior,
                    "width": h - 0.6,
                    "thickness": 8,
                    "quantity": 1,
                    "area": round((ancho_interior * (h - 0.6)) / 10000, 4)
                }
            ]
            
            despiece_data.append({
                "productCode": item.get('productCode', ''),
                "productName": item.get('productName', ''),
                "category": category,
                "originalWidth": w,
                "originalHeight": h,
                "originalDepth": d,
                "itemQuantity": item.get('quantity', 1),
                "components": components,
                "totalPanels": len(components),
                "totalArea": sum(c['area'] for c in components)
            })
        
        # Generar PDF
        pdf_content = create_factory_report_pdf(order, despiece_data, settings)
        
        # Nombre del archivo
        order_number = order.get('orderNumber', 'SIN_NUMERO')
        filename = f"Informe_Produccion_{order_number}.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating production report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/production-from-budget/{budget_id}")
async def generate_production_report_from_budget(budget_id: str, current_user: dict = Depends(require_auth)):
    """
    Genera un PDF de informe de producción desde un presupuesto.
    Útil para generar el informe antes de que se cree la orden de fabricación.
    """
    try:
        # Obtener presupuesto
        project = await _get_db().projects.find_one({"id": budget_id}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
        
        # Obtener configuración global (incluye logo)
        settings = await get_global_settings()
        
        # Convertir presupuesto a formato de orden
        items = []
        for item in project.get('itemsMontada', []):
            items.append({
                'productCode': item.get('productCode', item.get('customReference', '')),
                'productName': item.get('productName', item.get('name', '')),
                'quantity': item.get('quantity', 1),
                'width': item.get('customWidth', item.get('width', 60)),
                'height': item.get('customHeight', item.get('height', 70)),
                'depth': item.get('customDepth', item.get('depth', 58)),
                'status': 'pending'
            })
        
        order_data = {
            'orderNumber': project.get('budgetNumber', 'N/A'),
            'manufacturingNumber': None,
            'customerName': project.get('customerName', ''),
            'deliveryAddress': project.get('customerAddress', ''),
            'createdAt': datetime.now(timezone.utc).isoformat(),
            'status': 'draft',
            'priority': 'normal',
            'items': items
        }
        
        # Calcular despiece
        despiece_data = []
        for item in items:
            w = item.get('width', 60)
            h = item.get('height', 70)
            d = item.get('depth', 58)
            g = 1.8
            back_g = 0.8
            
            fondo_interior = d - back_g
            ancho_interior = w - (2 * g)
            
            components = [
                {"name": "Lateral izquierdo", "nameShort": "LAT-I", "material": "Melamina Blanca",
                 "length": h, "width": fondo_interior, "thickness": 18, "quantity": 1,
                 "area": round((h * fondo_interior) / 10000, 4)},
                {"name": "Lateral derecho", "nameShort": "LAT-D", "material": "Melamina Blanca",
                 "length": h, "width": fondo_interior, "thickness": 18, "quantity": 1,
                 "area": round((h * fondo_interior) / 10000, 4)},
                {"name": "Tapa superior", "nameShort": "TAPA-S", "material": "Melamina Blanca",
                 "length": ancho_interior, "width": fondo_interior, "thickness": 18, "quantity": 1,
                 "area": round((ancho_interior * fondo_interior) / 10000, 4)},
                {"name": "Tapa inferior", "nameShort": "TAPA-I", "material": "Melamina Blanca",
                 "length": ancho_interior, "width": fondo_interior, "thickness": 18, "quantity": 1,
                 "area": round((ancho_interior * fondo_interior) / 10000, 4)},
                {"name": "Trasera", "nameShort": "TRAS", "material": "Tablero 8mm",
                 "length": ancho_interior, "width": h - 0.6, "thickness": 8, "quantity": 1,
                 "area": round((ancho_interior * (h - 0.6)) / 10000, 4)}
            ]
            
            despiece_data.append({
                "productCode": item.get('productCode', ''),
                "productName": item.get('productName', ''),
                "category": '',
                "originalWidth": w,
                "originalHeight": h,
                "originalDepth": d,
                "itemQuantity": item.get('quantity', 1),
                "components": components,
                "totalPanels": len(components),
                "totalArea": sum(c['area'] for c in components)
            })
        
        # Generar PDF
        pdf_content = create_factory_report_pdf(order_data, despiece_data, settings)
        
        budget_number = project.get('budgetNumber', 'SIN_NUMERO')
        filename = f"Informe_Produccion_{budget_number}.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating production report from budget: {e}")
        raise HTTPException(status_code=500, detail=str(e))
