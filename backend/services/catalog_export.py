"""
Servicio de exportación de catálogo a Excel y PDF con imágenes SVG
"""
import io
import os
import base64
from xml.sax.saxutils import escape as _xml_escape
from typing import List, Dict, Optional
import xlsxwriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from PIL import Image

# cairosvg is optional - requires system library libcairo
try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except (ImportError, OSError):
    CAIROSVG_AVAILABLE = False
    cairosvg = None


# Dibujos técnicos originales de la tarifa MV (escaneados de la tarifa en papel),
# uno por familia/categoría. Se reutilizan en todas las tarifas (T1-T21), ya que
# el mueble es el mismo objeto físico independientemente del acabado/tarifa.
MV_DRAWINGS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "mv_drawings")


def _mv_drawing_path(category: str) -> Optional[str]:
    path = os.path.join(MV_DRAWINGS_DIR, f"{category}.png")
    return path if os.path.isfile(path) else None


def get_cabinet_svg(code: str, name: str, category: str) -> str:
    """Genera el SVG del mueble según su código y categoría"""
    stroke = '#4338ca'
    fill = '#eef2ff'
    
    code_upper = code.upper()
    name_upper = (name or '').upper()
    
    # Detectar tipo de mueble
    icon_type = '1P'  # Default
    
    # Herrajes especiales
    if 'HK' in code_upper:
        if 'HK-' in code_upper or any(x in code_upper for x in ['FLAP', 'FREFLAP']):
            icon_type = 'HK-TOP'
        else:
            icon_type = 'HK-TOP'
    elif 'HS' in code_upper:
        icon_type = 'HS'
    elif 'HL' in code_upper:
        icon_type = 'HL'
    elif 'HF' in code_upper:
        icon_type = 'HF'
    # HORNO+MICRO primero
    elif 'HM' in code_upper or 'CHM' in code_upper or 'PHM' in code_upper or ('HORNO' in name_upper and 'MICRO' in name_upper):
        icon_type = 'HORNO+MICRO'
    # Solo MICRO
    elif 'AM' in code_upper or 'BM' in code_upper or 'MICRO' in name_upper:
        icon_type = 'MICRO'
    # Solo HORNO
    elif any(x in code_upper for x in ['CH', 'BH', 'PH', 'VH']) or 'HORNO' in name_upper:
        icon_type = 'HORNO'
    elif 'BP' in code_upper or 'PLACA' in name_upper:
        icon_type = 'PLACA'
    elif 'BF' in code_upper or 'FREGADERO' in name_upper:
        icon_type = 'FREG'
    elif 'AT' in code_upper or 'TERMO' in name_upper:
        icon_type = 'TERMO'
    elif 'AE' in code_upper or 'ESCURRE' in name_upper:
        icon_type = 'ESCURRE'
    elif 'AC' in code_upper or 'CAMPANA' in name_upper:
        icon_type = 'CAMPANA'
    elif 'PE' in code_upper or 'EXTRAIBLE' in name_upper or 'EXTRAÍBLE' in name_upper:
        icon_type = 'EXTRAIBLE'
    elif 'BOT' in code_upper or 'BOTELLERO' in name_upper:
        icon_type = 'BOTELLERO'
    elif 'ESC' in code_upper or 'ESCOBERO' in name_upper:
        icon_type = 'ESCOBERO'
    elif 'FRI' in code_upper or 'FRIGO' in name_upper:
        icon_type = 'FRIGO'
    elif 'CACEROLERO' in name_upper or 'CAJONES' in name_upper or 'CAJÓN' in name_upper:
        icon_type = 'CAJONES'
    elif any(x in code_upper for x in ['ARA', 'BRA', 'ARC', 'BRC']):
        icon_type = 'RINCON'
    elif any(x in code_upper for x in ['3C', '4C', '5C']):
        icon_type = '3C'
    elif '2P' in code_upper:
        icon_type = '2P'
    elif '1V' in code_upper or '2V' in code_upper:
        icon_type = '1V'
    elif 'ABL' in code_upper or 'ABATIBLE' in name_upper:
        icon_type = 'ABATIBLE'
    
    # Por categoría
    if category == 'COLUMNAS':
        if 'FRIGO' in name_upper or 'FRI' in code_upper:
            icon_type = 'FRIGO'
        elif 'HORNO' in name_upper:
            icon_type = 'HORNO'
        elif 'ESCOBERO' in name_upper:
            icon_type = 'ESCOBERO'
        elif icon_type == '1P':
            icon_type = 'COLUMNA'
    elif category == 'BAJOS':
        if icon_type == '1P':
            icon_type = 'BAJO'
    elif category == 'ALTOS':
        if icon_type == '1P':
            icon_type = 'ALTO'
    
    # Generar SVG según tipo
    svgs = {
        'HK-TOP': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="14" width="28" height="22" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <path d="M8 14 L8 4 L32 4 L32 14" stroke="#dc2626" stroke-width="1.5" fill="#fef2f2"/>
            <circle cx="10" cy="4" r="1" fill="#dc2626"/><circle cx="30" cy="4" r="1" fill="#dc2626"/>
            <text x="20" y="21" text-anchor="middle" font-size="5" fill="#dc2626" font-weight="bold">HK</text>
        </svg>''',
        'HS': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="12" width="28" height="24" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <rect x="8" y="4" width="24" height="10" rx="1" stroke="#059669" stroke-width="1.5" fill="#ecfdf5"/>
            <circle cx="20" cy="9" r="3" stroke="#059669" stroke-width="1" fill="#d1fae5"/>
            <text x="20" y="19" text-anchor="middle" font-size="5" fill="#059669" font-weight="bold">HS</text>
        </svg>''',
        'HL': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="12" width="28" height="24" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <rect x="8" y="4" width="24" height="10" rx="1" stroke="#7c3aed" stroke-width="1.5" fill="#ede9fe"/>
            <text x="20" y="19" text-anchor="middle" font-size="5" fill="#7c3aed" font-weight="bold">HL</text>
        </svg>''',
        'HF': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="14" width="28" height="22" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <path d="M8 8 L8 2 L32 2 L32 8" stroke="#0891b2" stroke-width="1.5" fill="#ecfeff"/>
            <path d="M8 8 L20 12 L32 8" stroke="#0891b2" stroke-width="1.5" fill="#cffafe"/>
            <text x="20" y="21" text-anchor="middle" font-size="5" fill="#0891b2" font-weight="bold">HF</text>
        </svg>''',
        'HORNO': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="6" width="28" height="30" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <rect x="10" y="10" width="20" height="14" rx="1" stroke="#d97706" stroke-width="1.5" fill="#fef3c7"/>
            <circle cx="20" cy="17" r="3" fill="#f59e0b"/>
            <rect x="10" y="28" width="20" height="4" rx="1" fill="#fcd34d"/>
        </svg>''',
        'MICRO': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="10" width="28" height="20" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <rect x="9" y="13" width="16" height="14" rx="1" stroke="#3b82f6" stroke-width="1" fill="#dbeafe"/>
            <circle cx="30" cy="17" r="2" fill="#3b82f6"/>
            <circle cx="30" cy="23" r="2" fill="#3b82f6"/>
        </svg>''',
        'HORNO+MICRO': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="4" width="28" height="32" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <rect x="9" y="7" width="22" height="12" rx="1" stroke="#d97706" stroke-width="1" fill="#fef3c7"/>
            <rect x="9" y="22" width="16" height="10" rx="1" stroke="#3b82f6" stroke-width="1" fill="#dbeafe"/>
        </svg>''',
        'FREG': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="6" width="28" height="28" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <rect x="10" y="10" width="20" height="12" rx="1" stroke="#0ea5e9" stroke-width="1.5" fill="#e0f2fe"/>
            <circle cx="20" cy="16" r="4" stroke="#0ea5e9" stroke-width="1" fill="#bae6fd"/>
            <line x1="20" y1="8" x2="20" y2="4" stroke="#0ea5e9" stroke-width="2"/>
        </svg>''',
        'PLACA': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="12" width="28" height="20" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <rect x="8" y="8" width="24" height="4" rx="1" fill="#1f2937"/>
            <circle cx="14" cy="10" r="2" fill="#ef4444"/><circle cx="26" cy="10" r="2" fill="#ef4444"/>
        </svg>''',
        'CAMPANA': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 36 L8 20 L32 20 L32 36" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <path d="M12 20 L12 12 L28 12 L28 20" stroke="{stroke}" stroke-width="1.5" fill="#e2e8f0"/>
            <rect x="18" y="4" width="4" height="8" fill="#94a3b8"/>
        </svg>''',
        'CAJONES': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="6" width="28" height="28" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <line x1="6" y1="14" x2="34" y2="14" stroke="{stroke}" stroke-width="1"/>
            <line x1="6" y1="22" x2="34" y2="22" stroke="{stroke}" stroke-width="1"/>
            <line x1="6" y1="30" x2="34" y2="30" stroke="{stroke}" stroke-width="1"/>
            <rect x="17" y="9" width="6" height="2" rx="1" fill="{stroke}"/>
            <rect x="17" y="17" width="6" height="2" rx="1" fill="{stroke}"/>
            <rect x="17" y="25" width="6" height="2" rx="1" fill="{stroke}"/>
        </svg>''',
        'EXTRAIBLE': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="6" width="28" height="28" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <rect x="10" y="10" width="20" height="20" rx="1" stroke="#f97316" stroke-width="1.5" fill="#fff7ed" stroke-dasharray="3,2"/>
            <path d="M20 15 L20 25 M16 21 L20 25 L24 21" stroke="#f97316" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        'BOTELLERO': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="6" width="28" height="28" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <ellipse cx="14" cy="24" rx="3" ry="8" stroke="#7c3aed" stroke-width="1" fill="#ede9fe"/>
            <ellipse cx="26" cy="24" rx="3" ry="8" stroke="#7c3aed" stroke-width="1" fill="#ede9fe"/>
            <rect x="11" y="12" width="6" height="4" rx="1" fill="#7c3aed"/>
            <rect x="23" y="12" width="6" height="4" rx="1" fill="#7c3aed"/>
        </svg>''',
        'ESCOBERO': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="10" y="4" width="20" height="32" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <line x1="16" y1="8" x2="16" y2="28" stroke="#64748b" stroke-width="2"/>
            <ellipse cx="16" cy="30" rx="4" ry="3" fill="#94a3b8"/>
        </svg>''',
        'FRIGO': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="8" y="4" width="24" height="32" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <line x1="8" y1="16" x2="32" y2="16" stroke="{stroke}" stroke-width="1.5"/>
            <rect x="26" y="8" width="3" height="4" rx="1" fill="{stroke}"/>
            <rect x="26" y="20" width="3" height="6" rx="1" fill="{stroke}"/>
            <text x="20" y="12" text-anchor="middle" font-size="4" fill="{stroke}">❄</text>
        </svg>''',
        'RINCON': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <path d="M6 6 L34 6 L34 34 L20 34 L20 20 L6 20 Z" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <path d="M20 20 L34 34" stroke="{stroke}" stroke-width="1" stroke-dasharray="2,2"/>
        </svg>''',
        'ABATIBLE': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="14" width="28" height="22" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <path d="M8 14 L8 6 L32 6 L32 14" stroke="#dc2626" stroke-width="1.5" fill="#fef2f2"/>
            <path d="M20 10 L20 3 M17 5 L20 3 L23 5" stroke="#dc2626" stroke-width="1.5" stroke-linecap="round"/>
        </svg>''',
        'COLUMNA': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="10" y="4" width="20" height="32" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <line x1="10" y1="14" x2="30" y2="14" stroke="{stroke}" stroke-width="1"/>
            <line x1="10" y1="24" x2="30" y2="24" stroke="{stroke}" stroke-width="1"/>
            <rect x="24" y="7" width="3" height="4" rx="1" fill="{stroke}"/>
            <rect x="24" y="17" width="3" height="4" rx="1" fill="{stroke}"/>
            <rect x="24" y="27" width="3" height="4" rx="1" fill="{stroke}"/>
        </svg>''',
        'ALTO': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="10" width="28" height="24" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <rect x="8" y="12" width="24" height="20" rx="1" stroke="{stroke}" stroke-width="1" fill="white"/>
            <rect x="27" y="18" width="3" height="8" rx="1" fill="{stroke}"/>
        </svg>''',
        'BAJO': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="6" width="28" height="28" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <rect x="8" y="8" width="24" height="24" rx="1" stroke="{stroke}" stroke-width="1" fill="white"/>
            <rect x="27" y="14" width="3" height="10" rx="1" fill="{stroke}"/>
        </svg>''',
        '2P': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="6" width="28" height="28" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <line x1="20" y1="8" x2="20" y2="32" stroke="{stroke}" stroke-width="1.5"/>
            <rect x="9" y="16" width="3" height="8" rx="1" fill="{stroke}"/>
            <rect x="28" y="16" width="3" height="8" rx="1" fill="{stroke}"/>
        </svg>''',
        '1V': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="6" width="28" height="28" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <rect x="10" y="10" width="20" height="20" rx="1" stroke="#0ea5e9" stroke-width="1" fill="#e0f2fe"/>
            <line x1="10" y1="20" x2="30" y2="20" stroke="#0ea5e9" stroke-width="0.5"/>
            <line x1="20" y1="10" x2="20" y2="30" stroke="#0ea5e9" stroke-width="0.5"/>
        </svg>''',
        '3C': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="6" width="28" height="28" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <line x1="6" y1="15" x2="34" y2="15" stroke="{stroke}" stroke-width="1"/>
            <line x1="6" y1="24" x2="34" y2="24" stroke="{stroke}" stroke-width="1"/>
            <rect x="17" y="9" width="6" height="3" rx="1" fill="{stroke}"/>
            <rect x="17" y="18" width="6" height="3" rx="1" fill="{stroke}"/>
            <rect x="17" y="27" width="6" height="3" rx="1" fill="{stroke}"/>
        </svg>''',
        '1P': f'''<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="6" width="28" height="28" rx="2" stroke="{stroke}" stroke-width="2" fill="{fill}"/>
            <rect x="8" y="8" width="24" height="24" rx="1" stroke="{stroke}" stroke-width="1" fill="white"/>
            <rect x="27" y="16" width="3" height="8" rx="1" fill="{stroke}"/>
        </svg>'''
    }
    
    return svgs.get(icon_type, svgs['1P'])


def svg_to_png_bytes(svg_string: str, width: int = 40, height: int = 40) -> bytes:
    """Convierte SVG a PNG bytes"""
    try:
        if not CAIROSVG_AVAILABLE:
            raise ImportError("cairosvg not available")
        png_bytes = cairosvg.svg2png(
            bytestring=svg_string.encode('utf-8'),
            output_width=width,
            output_height=height
        )
        return png_bytes
    except Exception as e:
        # Devolver imagen placeholder si falla
        img = Image.new('RGB', (width, height), color='#f1f5f9')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()


async def generate_catalog_excel_with_images(
    products: List[Dict],
    module: Optional[str] = None
) -> io.BytesIO:
    """Genera Excel del catálogo con imágenes SVG de los muebles"""
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Catálogo Productos')
    
    # Formatos
    header_format = workbook.add_format({
        'bold': True, 'bg_color': '#1e293b', 'font_color': 'white',
        'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 11
    })
    cell_format = workbook.add_format({
        'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 10
    })
    code_format = workbook.add_format({
        'bold': True, 'align': 'center', 'valign': 'vcenter',
        'border': 1, 'font_size': 10, 'bg_color': '#f1f5f9'
    })
    name_format = workbook.add_format({
        'align': 'left', 'valign': 'vcenter', 'border': 1, 'font_size': 10, 'text_wrap': True
    })
    price_format = workbook.add_format({
        'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 10, 'num_format': '0.00'
    })
    
    # Encabezados con GRUPO en lugar de ZONA
    headers = ['IMAGEN', 'REF', 'DESCRIPCIÓN', 'AN', 'AL', 'FO', 'CATEGORÍA', 'SERIE', 'G1', 'G2', 'G3', 'G4', 'G5', 'G6']
    col_widths = [8, 15, 40, 8, 8, 8, 15, 15, 10, 10, 10, 10, 10, 10]
    
    for col, (header, width) in enumerate(zip(headers, col_widths)):
        worksheet.write(0, col, header, header_format)
        worksheet.set_column(col, col, width)
    
    # Altura de filas para las imágenes
    worksheet.set_default_row(40)
    worksheet.set_row(0, 20)  # Header más pequeño
    
    # Filas de datos con imágenes
    for row_num, product in enumerate(products, start=1):
        code = product.get('code', '')
        name = product.get('name', '')
        width = product.get('width', '')
        height = product.get('height', '')
        depth = product.get('depth', '')
        category = product.get('category', '')
        series = product.get('series', '')
        zone_points = product.get('zonePoints', {}) or {}
        
        # Generar imagen SVG
        svg = get_cabinet_svg(code, name, category)
        png_bytes = svg_to_png_bytes(svg, 36, 36)
        
        # Insertar imagen
        img_stream = io.BytesIO(png_bytes)
        worksheet.insert_image(row_num, 0, '', {
            'image_data': img_stream,
            'x_offset': 5, 'y_offset': 2,
            'x_scale': 1, 'y_scale': 1
        })
        
        worksheet.write(row_num, 1, code, code_format)
        worksheet.write(row_num, 2, name, name_format)
        worksheet.write(row_num, 3, width, cell_format)
        worksheet.write(row_num, 4, height, cell_format)
        worksheet.write(row_num, 5, depth, cell_format)
        worksheet.write(row_num, 6, category, cell_format)
        worksheet.write(row_num, 7, series, cell_format)
        
        # Grupos de precios G1-G6
        for i, zone_key in enumerate(['Z1', 'Z2', 'Z3', 'Z4', 'Z5', 'Z6']):
            value = zone_points.get(zone_key, 0) or 0
            worksheet.write(row_num, 8 + i, value, price_format)
    
    # Filtros automáticos
    worksheet.autofilter(0, 0, len(products), len(headers) - 1)
    worksheet.freeze_panes(1, 0)
    
    workbook.close()
    output.seek(0)
    return output


async def generate_catalog_pdf_with_images(
    products: List[Dict],
    module: Optional[str] = None
) -> io.BytesIO:
    """Genera PDF del catálogo con imágenes SVG de los muebles"""
    output = io.BytesIO()
    
    doc = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        rightMargin=10*mm,
        leftMargin=10*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=10*mm,
        alignment=TA_CENTER
    )
    
    elements = []
    
    # Título
    module_name = module.upper() if module else 'COMPLETO'
    elements.append(Paragraph(f"CATÁLOGO TÉCNICO LUIGGI - {module_name}", title_style))
    elements.append(Spacer(1, 5*mm))
    
    # Preparar datos de tabla
    table_data = [['IMG', 'REF', 'DESCRIPCIÓN', 'AN', 'AL', 'FO', 'CAT.', 'SERIE', 'G1', 'G2', 'G3', 'G4', 'G5', 'G6']]
    
    for product in products[:500]:  # Limitar para PDF
        code = product.get('code', '')
        name = product.get('name', '')[:35]  # Truncar nombre
        width = str(product.get('width', ''))
        height = str(product.get('height', ''))
        depth = str(product.get('depth', ''))
        category = product.get('category', '')[:10]
        series = product.get('series', '')[:10]
        zone_points = product.get('zonePoints', {}) or {}
        
        # Generar imagen
        svg = get_cabinet_svg(code, name, product.get('category', ''))
        png_bytes = svg_to_png_bytes(svg, 24, 24)
        img = RLImage(io.BytesIO(png_bytes), width=20, height=20)
        
        row = [
            img, code, name, width, height, depth, category, series,
            str(zone_points.get('Z1', 0) or 0),
            str(zone_points.get('Z2', 0) or 0),
            str(zone_points.get('Z3', 0) or 0),
            str(zone_points.get('Z4', 0) or 0),
            str(zone_points.get('Z5', 0) or 0),
            str(zone_points.get('Z6', 0) or 0)
        ]
        table_data.append(row)
    
    # Crear tabla
    col_widths = [25, 55, 130, 25, 25, 25, 45, 55, 35, 35, 35, 35, 35, 35]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('BACKGROUND', (1, 1), (1, -1), colors.HexColor('#f1f5f9')),  # Columna REF
    ]))
    
    elements.append(table)
    
    # Nota al pie
    if len(products) > 500:
        note_style = ParagraphStyle('Note', fontSize=8, textColor=colors.gray)
        elements.append(Spacer(1, 5*mm))
        elements.append(Paragraph(f"* Mostrando primeros 500 de {len(products)} productos. Usar Excel para catálogo completo.", note_style))
    
    doc.build(elements)
    output.seek(0)
    return output


SLATE_900 = colors.HexColor('#0f172a')
SLATE_800 = colors.HexColor('#1e293b')
SLATE_400 = colors.HexColor('#94a3b8')
ORANGE_500 = colors.HexColor('#f97316')
ORANGE_400 = colors.HexColor('#fb923c')


def _draw_mv_cover(canvas, doc):
    """Dibuja el fondo de la portada estilo Login (slate oscuro + acento naranja)."""
    width, height = A4
    canvas.saveState()
    # Fondo slate-900 a pantalla completa
    canvas.setFillColor(SLATE_900)
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    # Banda inferior slate-800 (simula el degradado del login)
    canvas.setFillColor(SLATE_800)
    canvas.rect(0, 0, width, height * 0.32, fill=1, stroke=0)
    # Línea de acento naranja
    canvas.setFillColor(ORANGE_500)
    canvas.rect(0, height * 0.32, width, 2.2 * mm, fill=1, stroke=0)
    canvas.setStrokeColor(ORANGE_500)
    canvas.setLineWidth(0.8)
    canvas.line(20 * mm, height * 0.32 - 4 * mm, width - 20 * mm, height * 0.32 - 4 * mm)
    # Footer
    canvas.setFillColor(SLATE_400)
    canvas.setFont('Helvetica', 8)
    canvas.drawCentredString(width / 2, 12 * mm, "© 2026 LUIGGI HOME · Sistema Profesional de Presupuestos")
    canvas.restoreState()


def _draw_mv_header_footer(canvas, doc):
    """Cabecera/pie para las páginas de contenido del catálogo MV."""
    width, height = landscape(A4)
    canvas.saveState()
    canvas.setFillColor(SLATE_800)
    canvas.rect(0, height - 12 * mm, width, 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawString(10 * mm, height - 8 * mm, "CATÁLOGO TÉCNICO 2026 · LUIGGI HOME · Tarifas MV")
    canvas.setFillColor(ORANGE_400)
    canvas.setFont('Helvetica', 8)
    canvas.drawRightString(width - 10 * mm, 8 * mm, f"Página {doc.page}")
    canvas.restoreState()


async def generate_mv_catalog_pdf(products: List[Dict], meta: Optional[Dict] = None) -> io.BytesIO:
    """
    Genera el "Catálogo técnico 2026" de tarifas MV (T1-T21) en PDF, con:
    - Portada estilo Login (fondo slate + acento naranja + logo + título)
    - Página de notas/auditoría de precios
    - Tablas de precios por categoría con todas las tarifas T1-T21
    """
    output = io.BytesIO()
    meta = meta or {}
    point_value = meta.get('pointValue', 3.33)

    styles = getSampleStyleSheet()

    # --- Estilos portada ---
    cover_brand_style = ParagraphStyle(
        'CoverBrand', fontName='Helvetica-BoldOblique', fontSize=34,
        textColor=colors.white, alignment=TA_CENTER, leading=38
    )
    cover_brand_sub_style = ParagraphStyle(
        'CoverBrandSub', fontName='Helvetica-Bold', fontSize=11,
        textColor=ORANGE_500, alignment=TA_CENTER, leading=14, spaceAfter=10 * mm
    )
    cover_title_style = ParagraphStyle(
        'CoverTitle', fontName='Helvetica-Bold', fontSize=30,
        textColor=colors.white, alignment=TA_CENTER, leading=34, spaceAfter=4 * mm
    )
    cover_subtitle_style = ParagraphStyle(
        'CoverSubtitle', fontName='Helvetica', fontSize=13,
        textColor=ORANGE_400, alignment=TA_CENTER, leading=18, spaceAfter=14 * mm
    )
    cover_meta_style = ParagraphStyle(
        'CoverMeta', fontName='Helvetica', fontSize=9,
        textColor=SLATE_400, alignment=TA_CENTER, leading=13
    )

    cover_elements = [
        Spacer(1, 55 * mm),
        Paragraph("LUIGGI", cover_brand_style),
        Paragraph("HOME MASTER", cover_brand_sub_style),
        Spacer(1, 18 * mm),
        Paragraph("CATÁLOGO TÉCNICO 2026", cover_title_style),
        Paragraph("Tarifas MV · T1 — T21", cover_subtitle_style),
        Paragraph(
            f"Generado el {_xml_escape(str(meta.get('fecha', '')))} &nbsp;·&nbsp; {len(products)} referencias &nbsp;·&nbsp; "
            f"Valor punto: {point_value} €",
            cover_meta_style
        ),
        PageBreak(),
    ]

    # --- Página de auditoría / notas de revisión ---
    note_title_style = ParagraphStyle(
        'NoteTitle', parent=styles['Heading1'], fontSize=16,
        textColor=SLATE_800, spaceAfter=6 * mm
    )
    note_section_style = ParagraphStyle(
        'NoteSection', parent=styles['Heading3'], fontSize=11,
        textColor=ORANGE_500 if False else colors.HexColor('#c2410c'), spaceAfter=2 * mm, spaceBefore=4 * mm
    )
    note_body_style = ParagraphStyle(
        'NoteBody', fontName='Helvetica', fontSize=9, leading=13,
        textColor=colors.HexColor('#334155')
    )

    audit_elements = [
        Paragraph("Auditoría de precios y notas de revisión", note_title_style),
        Paragraph(
            "Cada tarifa (T1...T21) es una lista de precios INDEPENDIENTE expresada en puntos. "
            f"El precio en EUR se calcula como: puntos × {point_value}. Las tarifas no son "
            "necesariamente crecientes entre sí: cada una refleja un acabado/serie distinto.",
            note_body_style
        ),
        Spacer(1, 4 * mm),
    ]
    estado = meta.get('estado')
    if estado:
        audit_elements.append(Paragraph("Estado de la transcripción", note_section_style))
        audit_elements.append(Paragraph(_xml_escape(str(estado)), note_body_style))

    notas_revision = meta.get('notas_revision') or []
    if notas_revision:
        audit_elements.append(Paragraph("Anomalías detectadas en la revisión", note_section_style))
        for nota in notas_revision:
            if isinstance(nota, dict):
                texto = nota.get('nota') or nota.get('detalle') or str(nota)
            else:
                texto = str(nota)
            audit_elements.append(Paragraph(f"⚠ {_xml_escape(str(texto))}", note_body_style))
            audit_elements.append(Spacer(1, 1.5 * mm))

    notas_tarifas = meta.get('notas_tarifas') or []
    if notas_tarifas:
        audit_elements.append(Paragraph("Notas específicas por tarifa", note_section_style))
        for nt in notas_tarifas:
            tarifa = _xml_escape(str(nt.get('tarifa', '')))
            notas = nt.get('notas', {}) or {}
            for clave, texto in notas.items():
                audit_elements.append(Paragraph(
                    f"<b>{tarifa}</b> ({_xml_escape(str(clave))}): {_xml_escape(str(texto))}",
                    note_body_style
                ))
                audit_elements.append(Spacer(1, 1.5 * mm))

    audit_elements.append(PageBreak())

    # --- Tablas de precios por categoría, T1-T21 ---
    table_title_style = ParagraphStyle(
        'TableTitle', parent=styles['Heading2'], fontSize=13,
        textColor=SLATE_800, spaceAfter=3 * mm, spaceBefore=2 * mm
    )
    tariff_keys = [f'T{i}' for i in range(1, 22)]

    by_category = {}
    for p in products:
        cat = p.get('category') or 'SIN CATEGORÍA'
        by_category.setdefault(cat, []).append(p)

    catalog_elements = []
    for cat in sorted(by_category.keys()):
        items = sorted(by_category[cat], key=lambda p: (p.get('series') or '', p.get('code') or ''))

        drawing_path = _mv_drawing_path(cat)
        if drawing_path:
            with Image.open(drawing_path) as _im:
                iw, ih = _im.size
            draw_h = 22 * mm
            draw_w = draw_h * iw / ih
            header_table = Table(
                [[RLImage(drawing_path, width=draw_w, height=draw_h), Paragraph(cat, table_title_style)]],
                colWidths=[draw_w + 4 * mm, None],
            )
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4 * mm),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            catalog_elements.append(header_table)
        else:
            catalog_elements.append(Paragraph(cat, table_title_style))

        header = ['REF', 'DESCRIPCIÓN'] + tariff_keys
        table_data = [header]
        for p in items:
            zone_points = p.get('zonePoints', {}) or {}
            row = [p.get('code', ''), (p.get('name', '') or '')[:42]]
            for tk in tariff_keys:
                val = zone_points.get(tk)
                row.append(str(val) if val not in (None, '') else '—')
            table_data.append(row)

        col_widths = [22 * mm, 58 * mm] + [9.2 * mm] * len(tariff_keys)
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), SLATE_800),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 6.5),
            ('FONTSIZE', (0, 1), (-1, -1), 6),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#fff7ed')),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ]))
        catalog_elements.append(table)
        catalog_elements.append(Spacer(1, 6 * mm))

    # --- Construcción del documento con plantillas distintas para portada y contenido ---
    from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame
    from reportlab.lib.pagesizes import A4 as A4_PORTRAIT

    doc = BaseDocTemplate(output, pagesize=A4_PORTRAIT)
    cover_frame = Frame(0, 0, A4_PORTRAIT[0], A4_PORTRAIT[1], id='cover', leftPadding=20 * mm, rightPadding=20 * mm)
    notes_frame = Frame(15 * mm, 15 * mm, A4_PORTRAIT[0] - 30 * mm, A4_PORTRAIT[1] - 30 * mm, id='notes')
    content_frame = Frame(
        10 * mm, 12 * mm, landscape(A4)[0] - 20 * mm, landscape(A4)[1] - 26 * mm, id='content'
    )

    doc.addPageTemplates([
        PageTemplate(id='Cover', frames=[cover_frame], onPage=_draw_mv_cover, pagesize=A4_PORTRAIT),
        PageTemplate(id='Notes', frames=[notes_frame], pagesize=A4_PORTRAIT),
        PageTemplate(id='Content', frames=[content_frame], onPage=_draw_mv_header_footer, pagesize=landscape(A4)),
    ])

    from reportlab.platypus import NextPageTemplate

    elements = []
    elements.append(NextPageTemplate('Notes'))
    elements.extend(cover_elements)
    elements.append(NextPageTemplate('Content'))
    elements.extend(audit_elements)
    elements.extend(catalog_elements)

    doc.build(elements)
    output.seek(0)
    return output
