import jsPDF from 'jspdf';
import 'jspdf-autotable';

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
  companyName = 'LUIGGI HOME'
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
      // Añadir logo (máximo 40x40mm)
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
  
  if (doorColorLow || doorColorHigh || carcassMaterialName) {
    doc.setFontSize(9);
    doc.setTextColor(...primaryColor);
    doc.setFont('helvetica', 'bold');
    doc.text('ESPECIFICACIONES:', margin, yPos);
    yPos += 6;
    
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    doc.setTextColor(71, 85, 105);
    
    const specs = [];
    if (doorColorLow) specs.push(`Puerta Bajo: ${doorColorLow}`);
    if (doorColorHigh) specs.push(`Puerta Alto: ${doorColorHigh}`);
    if (doorColorColumns) specs.push(`Columnas: ${doorColorColumns}`);
    if (sideColor) specs.push(`Costados: ${sideColor}`);
    if (carcassMaterialName) specs.push(`Armazón: ${carcassMaterialName}`);
    
    doc.text(specs.join('  |  '), margin, yPos);
    yPos += 12;
  }

  // ==========================================
  // TABLA MONTADA
  // ==========================================
  
  if (itemsMontada.length > 0) {
    doc.setFontSize(10);
    doc.setTextColor(...primaryColor);
    doc.setFont('helvetica', 'bold');
    doc.text('COCINA MONTADA', margin, yPos);
    yPos += 5;

    const montadaData = itemsMontada.map(item => [
      item.productCode || '-',
      item.productName || '-',
      item.quantity || 1,
      (item.unitPoints || 0).toFixed(2),
      (item.totalPoints || 0).toFixed(2),
      `€${((item.totalPoints || 0) * pointValueMontada).toFixed(2)}`
    ]);

    const totalPointsMontada = itemsMontada.reduce((sum, item) => sum + (item.totalPoints || 0), 0);
    const totalPriceMontada = totalPointsMontada * pointValueMontada;

    doc.autoTable({
      startY: yPos,
      head: [['REF', 'DESCRIPCIÓN', 'UDS', 'PTS/UD', 'PTS TOTAL', 'IMPORTE']],
      body: montadaData,
      foot: [['', '', '', '', 'SUBTOTAL', `€${totalPriceMontada.toFixed(2)}`]],
      theme: 'striped',
      headStyles: {
        fillColor: primaryColor,
        textColor: [255, 255, 255],
        fontStyle: 'bold',
        fontSize: 8
      },
      bodyStyles: {
        fontSize: 8
      },
      footStyles: {
        fillColor: accentColor,
        textColor: [255, 255, 255],
        fontStyle: 'bold',
        fontSize: 9
      },
      columnStyles: {
        0: { cellWidth: 25 },
        1: { cellWidth: 'auto' },
        2: { cellWidth: 15, halign: 'center' },
        3: { cellWidth: 20, halign: 'right' },
        4: { cellWidth: 25, halign: 'right' },
        5: { cellWidth: 25, halign: 'right' }
      },
      margin: { left: margin, right: margin }
    });

    yPos = doc.lastAutoTable.finalY + 10;
  }

  // ==========================================
  // TABLA DESPIECE
  // ==========================================
  
  if (itemsDespiece.length > 0) {
    // Verificar si necesitamos nueva página
    if (yPos > 230) {
      doc.addPage();
      yPos = 20;
    }

    doc.setFontSize(10);
    doc.setTextColor(...primaryColor);
    doc.setFont('helvetica', 'bold');
    doc.text('FORMATO DESPIECE', margin, yPos);
    yPos += 5;

    const despieceData = itemsDespiece.map(item => [
      item.productCode || '-',
      item.productName || '-',
      item.quantity || 1,
      (item.unitPoints || 0).toFixed(2),
      (item.totalPoints || 0).toFixed(2),
      `€${((item.totalPoints || 0) * pointValueDespiece).toFixed(2)}`
    ]);

    const totalPointsDespiece = itemsDespiece.reduce((sum, item) => sum + (item.totalPoints || 0), 0);
    const totalPriceDespiece = totalPointsDespiece * pointValueDespiece;

    doc.autoTable({
      startY: yPos,
      head: [['REF', 'DESCRIPCIÓN', 'UDS', 'PTS/UD', 'PTS TOTAL', 'IMPORTE']],
      body: despieceData,
      foot: [['', '', '', '', 'SUBTOTAL', `€${totalPriceDespiece.toFixed(2)}`]],
      theme: 'striped',
      headStyles: {
        fillColor: [100, 116, 139],
        textColor: [255, 255, 255],
        fontStyle: 'bold',
        fontSize: 8
      },
      bodyStyles: {
        fontSize: 8
      },
      footStyles: {
        fillColor: [100, 116, 139],
        textColor: [255, 255, 255],
        fontStyle: 'bold',
        fontSize: 9
      },
      columnStyles: {
        0: { cellWidth: 25 },
        1: { cellWidth: 'auto' },
        2: { cellWidth: 15, halign: 'center' },
        3: { cellWidth: 20, halign: 'right' },
        4: { cellWidth: 25, halign: 'right' },
        5: { cellWidth: 25, halign: 'right' }
      },
      margin: { left: margin, right: margin }
    });

    yPos = doc.lastAutoTable.finalY + 10;
  }

  // ==========================================
  // TOTAL GENERAL
  // ==========================================
  
  const totalPointsMontada = itemsMontada.reduce((sum, item) => sum + (item.totalPoints || 0), 0);
  const totalPointsDespiece = itemsDespiece.reduce((sum, item) => sum + (item.totalPoints || 0), 0);
  const totalPriceMontada = totalPointsMontada * pointValueMontada;
  const totalPriceDespiece = totalPointsDespiece * pointValueDespiece;
  const grandTotal = totalPriceMontada + totalPriceDespiece;

  // Verificar si necesitamos nueva página
  if (yPos > 250) {
    doc.addPage();
    yPos = 20;
  }

  // Caja de total
  doc.setFillColor(...primaryColor);
  doc.roundedRect(pageWidth - margin - 80, yPos, 80, 30, 3, 3, 'F');
  
  doc.setFontSize(9);
  doc.setTextColor(255, 255, 255);
  doc.text('TOTAL PRESUPUESTO', pageWidth - margin - 40, yPos + 10, { align: 'center' });
  
  doc.setFontSize(16);
  doc.setFont('helvetica', 'bold');
  doc.text(`€${grandTotal.toFixed(2)}`, pageWidth - margin - 40, yPos + 23, { align: 'center' });

  yPos += 45;

  // ==========================================
  // PIE DE PÁGINA
  // ==========================================
  
  // Verificar si hay espacio
  if (yPos > 260) {
    doc.addPage();
    yPos = 20;
  }

  doc.setFontSize(7);
  doc.setTextColor(148, 163, 184);
  doc.setFont('helvetica', 'normal');
  
  const footerText = [
    'Este presupuesto tiene una validez de 30 días desde la fecha de emisión.',
    'Los precios no incluyen IVA ni transporte. Consulte condiciones de montaje.',
    `Generado con LUIGGI HOME - ${new Date().toLocaleString('es-ES')}`
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

export default generateBudgetPDF;
