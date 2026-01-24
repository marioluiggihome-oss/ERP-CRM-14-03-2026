import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

/**
 * Genera un PDF del presupuesto actual
 * @param {Object} params - Parámetros del presupuesto
 */
export const generateBudgetPDF = ({
  budgetNumber,
  customerName,
  customerAddress,
  internalReference,
  itemsMontada = [],
  itemsDespiece = [],
  pointValueMontada = 1,
  pointValueDespiece = 0.88,
  doorColorLow,
  doorColorHigh,
  doorColorColumns,
  sideColor,
  carcassMaterialName,
  logo,
  brandColor = '#ea580c',
  companyName = 'LUIGGI HOME',
  globalFinish = '',
  allProducts = [],
  calculateLineDetails = null
}) => {
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();
  const margin = 15;
  let yPos = 20;

  // Colores
  const primaryColor = [30, 41, 59]; // slate-800
  const accentColor = hexToRgb(brandColor);
  const lightGray = [241, 245, 249]; // slate-100

  // ==========================================
  // CABECERA CON LOGO
  // ==========================================
  
  let logoWidth = 0;
  
  // Si hay logo, añadirlo
  if (logo && logo.startsWith('data:image')) {
    try {
      const logoSize = 35;
      doc.addImage(logo, 'PNG', margin, yPos - 10, logoSize, logoSize);
      logoWidth = logoSize + 8;
    } catch (e) {
      console.error('Error adding logo to PDF:', e);
    }
  }
  
  // Título de la empresa
  doc.setFontSize(22);
  doc.setTextColor(...primaryColor);
  doc.setFont('helvetica', 'bold');
  doc.text(companyName, margin + logoWidth, yPos);
  
  doc.setFontSize(10);
  doc.setTextColor(...accentColor);
  doc.text('PRESUPUESTO DE COCINA', margin + logoWidth, yPos + 7);
  
  // Número de expediente (derecha)
  doc.setFontSize(12);
  doc.setTextColor(...primaryColor);
  doc.setFont('helvetica', 'bold');
  doc.text(`Nº ${budgetNumber || 'SIN NÚMERO'}`, pageWidth - margin, yPos, { align: 'right' });
  
  doc.setFontSize(9);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(100, 116, 139);
  doc.text(`Fecha: ${new Date().toLocaleDateString('es-ES')}`, pageWidth - margin, yPos + 6, { align: 'right' });
  
  if (internalReference) {
    doc.text(`Ref: ${internalReference}`, pageWidth - margin, yPos + 11, { align: 'right' });
  }

  yPos += 25;

  // Línea separadora
  doc.setDrawColor(...accentColor);
  doc.setLineWidth(1);
  doc.line(margin, yPos, pageWidth - margin, yPos);
  
  yPos += 15;

  // ==========================================
  // DATOS DEL CLIENTE
  // ==========================================
  
  doc.setFillColor(...lightGray);
  doc.roundedRect(margin, yPos, pageWidth - margin * 2, 25, 3, 3, 'F');
  
  doc.setFontSize(8);
  doc.setTextColor(100, 116, 139);
  doc.text('CLIENTE', margin + 5, yPos + 6);
  
  doc.setFontSize(11);
  doc.setTextColor(...primaryColor);
  doc.setFont('helvetica', 'bold');
  doc.text(customerName || 'Sin especificar', margin + 5, yPos + 14);
  
  if (customerAddress) {
    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    doc.text(customerAddress, margin + 5, yPos + 20);
  }

  yPos += 35;

  // ==========================================
  // ESPECIFICACIONES
  // ==========================================
  
  if (doorColorLow || doorColorHigh || carcassMaterialName || globalFinish) {
    doc.setFontSize(9);
    doc.setTextColor(...primaryColor);
    doc.setFont('helvetica', 'bold');
    doc.text('ESPECIFICACIONES:', margin, yPos);
    yPos += 6;
    
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    doc.setTextColor(71, 85, 105);
    
    const specs = [];
    if (globalFinish) specs.push(`Acabado: ${globalFinish}`);
    if (doorColorLow) specs.push(`Puerta Bajo: ${doorColorLow}`);
    if (doorColorHigh) specs.push(`Puerta Alto: ${doorColorHigh}`);
    if (doorColorColumns) specs.push(`Columnas: ${doorColorColumns}`);
    if (sideColor) specs.push(`Costados: ${sideColor}`);
    if (carcassMaterialName) specs.push(`Armazón: ${carcassMaterialName}`);
    
    doc.text(specs.join('  |  '), margin, yPos);
    yPos += 12;
  }

  // ==========================================
  // TABLA DE ARTÍCULOS
  // ==========================================
  
  // Combinar items de montada y despiece
  const allItems = [...itemsMontada, ...itemsDespiece];
  
  if (allItems.length > 0) {
    doc.setFontSize(10);
    doc.setTextColor(...primaryColor);
    doc.setFont('helvetica', 'bold');
    doc.text('DETALLE DEL PRESUPUESTO', margin, yPos);
    yPos += 5;

    // Preparar datos de la tabla
    const tableData = allItems.map(item => {
      // Buscar producto
      let product = allProducts.find(p => p.id === item.productId);
      let price = 0;
      
      if (item.isManual) {
        product = {
          code: item.customReference || 'MANUAL',
          name: item.manualDescription || 'CONCEPTO MANUAL'
        };
        price = (item.manualPoints || 0) * pointValueMontada;
      } else if (product && calculateLineDetails) {
        const details = calculateLineDetails(item, product);
        price = details.total || 0;
      }
      
      const code = item.customReference || product?.code || '-';
      const name = item.manualDescription || product?.name || '-';
      const width = item.customWidth ? Math.round(item.customWidth / 10) : '-';
      const height = item.customHeight || '-';
      const depth = item.customDepth || '-';
      const apertura = item.openingDirection === 'Derecha' ? 'D' : item.openingDirection === 'Izquierda' ? 'I' : '-';
      
      return [
        item.quantity || 1,
        code,
        name.substring(0, 40),
        width,
        height,
        depth,
        apertura,
        `${price.toFixed(2)}€`
      ];
    });

    // Calcular total
    let grandTotal = 0;
    allItems.forEach(item => {
      let product = allProducts.find(p => p.id === item.productId);
      if (item.isManual) {
        grandTotal += (item.manualPoints || 0) * pointValueMontada * (item.quantity || 1);
      } else if (product && calculateLineDetails) {
        const details = calculateLineDetails(item, product);
        grandTotal += details.total || 0;
      }
    });

    autoTable(doc, {
      startY: yPos,
      head: [['UD', 'REF', 'DESCRIPCIÓN', 'AN', 'AL', 'FO', 'AP', 'IMPORTE']],
      body: tableData,
      theme: 'striped',
      headStyles: {
        fillColor: primaryColor,
        textColor: [255, 255, 255],
        fontStyle: 'bold',
        fontSize: 7
      },
      bodyStyles: {
        fontSize: 7
      },
      columnStyles: {
        0: { cellWidth: 10, halign: 'center' },
        1: { cellWidth: 25 },
        2: { cellWidth: 'auto' },
        3: { cellWidth: 12, halign: 'center' },
        4: { cellWidth: 12, halign: 'center' },
        5: { cellWidth: 12, halign: 'center' },
        6: { cellWidth: 10, halign: 'center' },
        7: { cellWidth: 22, halign: 'right' }
      },
      margin: { left: margin, right: margin }
    });

    yPos = doc.lastAutoTable.finalY + 10;

    // ==========================================
    // TOTALES CON IVA
    // ==========================================
    
    // Verificar si necesitamos nueva página
    if (yPos > 230) {
      doc.addPage();
      yPos = 20;
    }

    const baseImponible = grandTotal;
    const iva = grandTotal * 0.21;
    const totalConIva = grandTotal * 1.21;

    // Caja de totales
    const boxX = pageWidth - margin - 85;
    const boxWidth = 85;
    
    // Fondo
    doc.setFillColor(...primaryColor);
    doc.roundedRect(boxX, yPos, boxWidth, 52, 3, 3, 'F');
    
    // BRUTO LÍNEAS
    doc.setFontSize(7);
    doc.setTextColor(148, 163, 184);
    doc.text('BRUTO LÍNEAS', boxX + 5, yPos + 8);
    doc.setFontSize(10);
    doc.setTextColor(255, 255, 255);
    doc.text(`${baseImponible.toFixed(2)}€`, boxX + boxWidth - 5, yPos + 8, { align: 'right' });
    
    // BASE IMPONIBLE
    doc.setFontSize(7);
    doc.setTextColor(148, 163, 184);
    doc.text('BASE IMPONIBLE', boxX + 5, yPos + 18);
    doc.setFontSize(10);
    doc.setTextColor(255, 255, 255);
    doc.text(`${baseImponible.toFixed(2)}€`, boxX + boxWidth - 5, yPos + 18, { align: 'right' });
    
    // IVA
    doc.setFontSize(7);
    doc.setTextColor(148, 163, 184);
    doc.text('IVA 21%', boxX + 5, yPos + 28);
    doc.setFontSize(10);
    doc.setTextColor(255, 255, 255);
    doc.text(`${iva.toFixed(2)}€`, boxX + boxWidth - 5, yPos + 28, { align: 'right' });
    
    // Línea separadora
    doc.setDrawColor(...accentColor);
    doc.setLineWidth(0.5);
    doc.line(boxX + 5, yPos + 33, boxX + boxWidth - 5, yPos + 33);
    
    // TOTAL
    doc.setFontSize(8);
    doc.setTextColor(...accentColor);
    doc.setFont('helvetica', 'bold');
    doc.text('TOTAL PRESUPUESTO', boxX + 5, yPos + 42);
    doc.setFontSize(14);
    doc.setTextColor(255, 255, 255);
    doc.text(`${totalConIva.toFixed(2)}€`, boxX + boxWidth - 5, yPos + 48, { align: 'right' });

    yPos += 60;
  }

  // ==========================================
  // PIE DE PÁGINA
  // ==========================================
  
  // Verificar si hay espacio
  if (yPos > 265) {
    doc.addPage();
    yPos = 20;
  }

  doc.setFontSize(7);
  doc.setTextColor(148, 163, 184);
  doc.setFont('helvetica', 'normal');
  
  const footerText = [
    'Este presupuesto tiene una validez de 30 días desde la fecha de emisión.',
    'Consulte condiciones de montaje y transporte.',
    `Generado con ${companyName} - ${new Date().toLocaleString('es-ES')}`
  ];
  
  footerText.forEach((text, i) => {
    doc.text(text, pageWidth / 2, yPos + (i * 4), { align: 'center' });
  });

  // ==========================================
  // DESCARGAR
  // ==========================================
  
  const fileName = `Presupuesto_${budgetNumber || 'SIN_NUMERO'}_${customerName?.replace(/\s+/g, '_') || 'Cliente'}.pdf`;
  doc.save(fileName);
  
  return fileName;
};

/**
 * Convierte color hex a RGB
 */
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? [
    parseInt(result[1], 16),
    parseInt(result[2], 16),
    parseInt(result[3], 16)
  ] : [234, 88, 12]; // Default orange
}

/**
 * Genera un PDF del despiece de armarios
 */
export const generateArmariosDespiecePDF = ({
  customerName = '',
  projectRef = '',
  dimensions = { width: 0, height: 0, depth: 0 },
  accessories = [],
  boardsCalculation = null,
  pricing = null,
  colors = { exterior: '', interior: '' },
  companyName = 'LUIGGI HOME'
}) => {
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();
  const margin = 10;
  let yPos = 15;

  // Colores
  const primaryColor = [30, 41, 59];
  const orangeColor = [234, 88, 12];

  // ==========================================
  // CABECERA
  // ==========================================
  
  // Fondo naranja
  doc.setFillColor(...orangeColor);
  doc.rect(0, 0, pageWidth, 35, 'F');
  
  // Título
  doc.setFontSize(18);
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.text('DESPIECE PRIVADO - ARMARIOS', pageWidth / 2, 15, { align: 'center' });
  
  doc.setFontSize(9);
  doc.setFont('helvetica', 'normal');
  doc.text('Lista de Accesorios Numerados para Montaje', pageWidth / 2, 22, { align: 'center' });
  
  // Fecha
  doc.setFontSize(8);
  doc.text(`Generado: ${new Date().toLocaleString('es-ES')}`, pageWidth / 2, 30, { align: 'center' });

  yPos = 45;

  // ==========================================
  // INFO CLIENTE Y DIMENSIONES
  // ==========================================
  
  doc.setFillColor(255, 247, 237); // orange-50
  doc.rect(margin, yPos - 5, pageWidth - (margin * 2), 20, 'F');
  
  doc.setFontSize(8);
  doc.setTextColor(...orangeColor);
  doc.setFont('helvetica', 'bold');
  doc.text('CLIENTE', margin + 5, yPos);
  doc.text('REFERENCIA', margin + 50, yPos);
  doc.text('DIMENSIONES', margin + 100, yPos);
  doc.text('COLORES', margin + 150, yPos);
  
  doc.setFontSize(9);
  doc.setTextColor(...primaryColor);
  doc.setFont('helvetica', 'normal');
  doc.text(customerName || 'Sin especificar', margin + 5, yPos + 7);
  doc.text(projectRef || 'Sin referencia', margin + 50, yPos + 7);
  doc.text(`${dimensions.width} x ${dimensions.height} x ${dimensions.depth} mm`, margin + 100, yPos + 7);
  doc.text(`Ext: ${colors.exterior} / Int: ${colors.interior}`, margin + 150, yPos + 7);

  yPos += 25;

  // ==========================================
  // TABLA DE ACCESORIOS
  // ==========================================
  
  const tableData = accessories.map(acc => [
    acc.num.toString(),
    acc.code,
    acc.name,
    acc.category,
    acc.dimensions,
    acc.quantity.toString(),
    `${acc.unitPrice.toFixed(2)}€`,
    `${acc.totalPrice.toFixed(2)}€`,
    acc.notes || ''
  ]);

  doc.autoTable({
    startY: yPos,
    head: [['#', 'CÓDIGO', 'NOMBRE', 'CATEGORÍA', 'DIMENSIONES', 'CANT.', 'P.UNIT.', 'TOTAL', 'NOTAS']],
    body: tableData,
    styles: {
      fontSize: 7,
      cellPadding: 2,
      lineColor: [200, 200, 200],
      lineWidth: 0.1
    },
    headStyles: {
      fillColor: [30, 41, 59],
      textColor: [255, 255, 255],
      fontStyle: 'bold',
      fontSize: 7
    },
    columnStyles: {
      0: { cellWidth: 8, halign: 'center' },
      1: { cellWidth: 15, halign: 'center' },
      2: { cellWidth: 45 },
      3: { cellWidth: 22 },
      4: { cellWidth: 25, halign: 'center' },
      5: { cellWidth: 10, halign: 'center' },
      6: { cellWidth: 15, halign: 'right' },
      7: { cellWidth: 15, halign: 'right' },
      8: { cellWidth: 35 }
    },
    alternateRowStyles: {
      fillColor: [248, 250, 252]
    },
    margin: { left: margin, right: margin }
  });

  yPos = doc.lastAutoTable.finalY + 10;

  // ==========================================
  // RESUMEN TABLEROS
  // ==========================================
  
  if (boardsCalculation) {
    // Nueva página si no hay espacio
    if (yPos > 200) {
      doc.addPage();
      yPos = 20;
    }

    doc.setFillColor(30, 58, 138); // blue-900
    doc.rect(margin, yPos, pageWidth - (margin * 2), 45, 'F');
    
    doc.setFontSize(10);
    doc.setTextColor(255, 255, 255);
    doc.setFont('helvetica', 'bold');
    doc.text('CÁLCULO DE TABLEROS NECESARIOS', margin + 5, yPos + 8);
    
    doc.setFontSize(8);
    doc.setFont('helvetica', 'normal');
    doc.text(`Tablero estándar: ${boardsCalculation.boardSize} (${boardsCalculation.boardAreaM2.toFixed(2)} m²)`, margin + 5, yPos + 15);
    
    // Columnas de tableros
    const colWidth = (pageWidth - (margin * 2) - 10) / 3;
    
    // Tablero 18mm Estructura
    doc.setFontSize(8);
    doc.setFont('helvetica', 'bold');
    doc.text('18mm Estructura', margin + 5, yPos + 25);
    doc.setFont('helvetica', 'normal');
    doc.text(`${boardsCalculation.boards.tablero18mm.totalArea.toFixed(2)} m²`, margin + 5, yPos + 32);
    doc.text(`Tableros: ${boardsCalculation.boards.tablero18mm.boardsNeeded}`, margin + 5, yPos + 38);
    
    // Tablero 8mm Trasera
    doc.setFont('helvetica', 'bold');
    doc.text('8mm Trasera', margin + 5 + colWidth, yPos + 25);
    doc.setFont('helvetica', 'normal');
    doc.text(`${boardsCalculation.boards.tablero8mm.totalArea.toFixed(2)} m²`, margin + 5 + colWidth, yPos + 32);
    doc.text(`Tableros: ${boardsCalculation.boards.tablero8mm.boardsNeeded}`, margin + 5 + colWidth, yPos + 38);
    
    // Tablero 18mm Puertas
    doc.setFont('helvetica', 'bold');
    doc.text('18mm Puertas', margin + 5 + colWidth * 2, yPos + 25);
    doc.setFont('helvetica', 'normal');
    doc.text(`${boardsCalculation.boards.puertasTablero.totalArea.toFixed(2)} m²`, margin + 5 + colWidth * 2, yPos + 32);
    doc.text(`Tableros: ${boardsCalculation.boards.puertasTablero.boardsNeeded}`, margin + 5 + colWidth * 2, yPos + 38);

    yPos += 55;
    
    // Resumen total
    doc.setFillColor(234, 179, 8); // yellow-500
    doc.rect(margin, yPos, pageWidth - (margin * 2), 15, 'F');
    
    doc.setFontSize(10);
    doc.setTextColor(0, 0, 0);
    doc.setFont('helvetica', 'bold');
    doc.text(`TOTAL: ${boardsCalculation.totalArea.toFixed(2)} m²`, margin + 5, yPos + 10);
    doc.text(`TABLEROS A COMPRAR: ${boardsCalculation.totalBoards}`, pageWidth - margin - 5, yPos + 10, { align: 'right' });
  }

  // ==========================================
  // PIE DE PÁGINA
  // ==========================================
  
  doc.setFontSize(7);
  doc.setTextColor(148, 163, 184);
  doc.setFont('helvetica', 'normal');
  doc.text(`Generado con ${companyName} - ${new Date().toLocaleString('es-ES')}`, pageWidth / 2, 285, { align: 'center' });

  // Guardar
  const fileName = `Despiece_Armario_${customerName?.replace(/\s+/g, '_') || 'Armario'}.pdf`;
  doc.save(fileName);
  
  return fileName;
};

/**
 * Genera un PDF del presupuesto de armario
 */
export const generateArmarioPresupuestoPDF = ({
  projectName = '',
  customerName = '',
  projectRef = '',
  dimensions = { width: 0, height: 0, depth: 0 },
  modules = 0,
  doorType = '',
  colors = { exterior: '', exteriorName: '', interior: '', interiorName: '' },
  pricing = null,
  specifications = {},
  boardsCalculation = null,
  companyName = 'LUIGGI HOME',
  ivaRate = 21
}) => {
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();
  const margin = 15;
  let yPos = 20;

  // Colores
  const primaryColor = [30, 41, 59];
  const purpleColor = [124, 58, 237];

  // ==========================================
  // CABECERA
  // ==========================================
  
  doc.setFillColor(...purpleColor);
  doc.rect(0, 0, pageWidth, 40, 'F');
  
  doc.setFontSize(22);
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.text('PRESUPUESTO DE ARMARIO', pageWidth / 2, 18, { align: 'center' });
  
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.text(companyName, pageWidth / 2, 28, { align: 'center' });
  
  doc.setFontSize(8);
  doc.text(`Fecha: ${new Date().toLocaleDateString('es-ES')}`, pageWidth / 2, 36, { align: 'center' });

  yPos = 55;

  // ==========================================
  // INFO CLIENTE
  // ==========================================
  
  doc.setFillColor(245, 243, 255); // purple-50
  doc.rect(margin, yPos - 5, pageWidth - (margin * 2), 25, 'F');
  
  doc.setFontSize(8);
  doc.setTextColor(...purpleColor);
  doc.setFont('helvetica', 'bold');
  doc.text('PROYECTO', margin + 5, yPos);
  doc.text('CLIENTE', margin + 60, yPos);
  doc.text('REFERENCIA', margin + 115, yPos);
  
  doc.setFontSize(10);
  doc.setTextColor(...primaryColor);
  doc.setFont('helvetica', 'normal');
  doc.text(projectName || 'Sin nombre', margin + 5, yPos + 10);
  doc.text(customerName || 'Sin especificar', margin + 60, yPos + 10);
  doc.text(projectRef || 'Sin referencia', margin + 115, yPos + 10);

  yPos += 35;

  // ==========================================
  // ESPECIFICACIONES
  // ==========================================
  
  doc.setFontSize(12);
  doc.setTextColor(...primaryColor);
  doc.setFont('helvetica', 'bold');
  doc.text('ESPECIFICACIONES DEL ARMARIO', margin, yPos);
  
  yPos += 10;
  
  doc.setDrawColor(200, 200, 200);
  doc.line(margin, yPos, pageWidth - margin, yPos);
  
  yPos += 8;

  // Grid de especificaciones
  const specs = [
    ['Dimensiones', `${dimensions.width} x ${dimensions.height} x ${dimensions.depth} mm`],
    ['Módulos', `${modules} módulos`],
    ['Tipo de puerta', doorType === 'sliding' ? 'Corredera' : doorType === 'folding' ? 'Plegable' : 'Abatible'],
    ['Color exterior', `${colors.exterior} - ${colors.exteriorName}`],
    ['Color interior', `${colors.interior} - ${colors.interiorName}`],
    ['Baldas totales', specifications.shelves || '0'],
    ['Cajones totales', specifications.drawers || '0'],
    ['Barras de colgar', specifications.hangingRods || '0'],
  ];
  
  doc.setFontSize(9);
  const colWidth = (pageWidth - (margin * 2)) / 2;
  
  specs.forEach((spec, idx) => {
    const x = margin + (idx % 2) * colWidth;
    const y = yPos + Math.floor(idx / 2) * 8;
    
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...purpleColor);
    doc.text(spec[0] + ':', x, y);
    
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...primaryColor);
    doc.text(spec[1], x + 40, y);
  });

  yPos += Math.ceil(specs.length / 2) * 8 + 15;

  // ==========================================
  // DESGLOSE DE PRECIOS
  // ==========================================
  
  if (pricing) {
    doc.setFontSize(12);
    doc.setTextColor(...primaryColor);
    doc.setFont('helvetica', 'bold');
    doc.text('DESGLOSE DEL PRESUPUESTO', margin, yPos);
    
    yPos += 10;
    
    const priceItems = [
      ['Estructura base', pricing.base || 0],
      ['Sistema de puertas', pricing.doors || 0],
      ['Terminaciones', pricing.finishes || 0],
      ['Interior', pricing.interior || 0],
      ['Extras', pricing.extras || 0],
    ];
    
    doc.setFontSize(9);
    priceItems.forEach(item => {
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(...primaryColor);
      doc.text(item[0], margin + 5, yPos);
      doc.text(`${item[1].toFixed(2)} €`, pageWidth - margin - 5, yPos, { align: 'right' });
      yPos += 7;
    });
    
    yPos += 3;
    doc.setDrawColor(200, 200, 200);
    doc.line(margin, yPos, pageWidth - margin, yPos);
    yPos += 8;
    
    // Subtotal
    const subtotal = pricing.subtotal || (pricing.base + pricing.doors + pricing.finishes + pricing.interior + pricing.extras);
    doc.setFont('helvetica', 'bold');
    doc.text('Base imponible', margin + 5, yPos);
    doc.text(`${subtotal.toFixed(2)} €`, pageWidth - margin - 5, yPos, { align: 'right' });
    yPos += 7;
    
    // IVA
    const iva = subtotal * (ivaRate / 100);
    doc.setFont('helvetica', 'normal');
    doc.text(`IVA (${ivaRate}%)`, margin + 5, yPos);
    doc.text(`${iva.toFixed(2)} €`, pageWidth - margin - 5, yPos, { align: 'right' });
    yPos += 10;
    
    // Total
    doc.setFillColor(...purpleColor);
    doc.rect(margin, yPos, pageWidth - (margin * 2), 15, 'F');
    
    doc.setFontSize(14);
    doc.setTextColor(255, 255, 255);
    doc.setFont('helvetica', 'bold');
    doc.text('TOTAL PRESUPUESTO', margin + 5, yPos + 10);
    doc.text(`${(pricing.total || (subtotal + iva)).toFixed(2)} €`, pageWidth - margin - 5, yPos + 10, { align: 'right' });
  }

  yPos += 30;

  // ==========================================
  // TABLEROS NECESARIOS
  // ==========================================
  
  if (boardsCalculation) {
    doc.setFontSize(12);
    doc.setTextColor(...primaryColor);
    doc.setFont('helvetica', 'bold');
    doc.text('TABLEROS NECESARIOS', margin, yPos);
    
    yPos += 10;
    
    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    
    doc.text(`18mm Estructura: ${boardsCalculation.boards.tablero18mm.totalArea.toFixed(2)} m² (${boardsCalculation.boards.tablero18mm.boardsNeeded} tableros)`, margin + 5, yPos);
    yPos += 6;
    doc.text(`8mm Trasera: ${boardsCalculation.boards.tablero8mm.totalArea.toFixed(2)} m² (${boardsCalculation.boards.tablero8mm.boardsNeeded} tableros)`, margin + 5, yPos);
    yPos += 6;
    doc.text(`18mm Puertas: ${boardsCalculation.boards.puertasTablero.totalArea.toFixed(2)} m² (${boardsCalculation.boards.puertasTablero.boardsNeeded} tableros)`, margin + 5, yPos);
    yPos += 10;
    
    doc.setFont('helvetica', 'bold');
    doc.text(`TOTAL: ${boardsCalculation.totalArea.toFixed(2)} m² - ${boardsCalculation.totalBoards} tableros`, margin + 5, yPos);
  }

  // ==========================================
  // PIE DE PÁGINA
  // ==========================================
  
  doc.setFontSize(7);
  doc.setTextColor(148, 163, 184);
  doc.setFont('helvetica', 'normal');
  doc.text('Este presupuesto tiene una validez de 30 días desde la fecha de emisión.', pageWidth / 2, 275, { align: 'center' });
  doc.text(`Generado con ${companyName} - ${new Date().toLocaleString('es-ES')}`, pageWidth / 2, 280, { align: 'center' });

  // Guardar
  const fileName = `Presupuesto_Armario_${projectName?.replace(/\s+/g, '_') || 'Armario'}.pdf`;
  doc.save(fileName);
  
  return fileName;
};

export default generateBudgetPDF;
