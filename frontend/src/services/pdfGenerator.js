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

export default generateBudgetPDF;
