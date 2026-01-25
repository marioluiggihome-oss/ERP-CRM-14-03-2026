import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

/**
 * Capitaliza correctamente un nombre (primera letra mayúscula de cada palabra)
 */
const capitalizeName = (name) => {
  if (!name) return '';
  return name
    .toLowerCase()
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
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
  ] : [234, 88, 12];
}

/**
 * Genera un PDF del presupuesto actual - Formato A4 optimizado
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
  calculateLineDetails = null,
  ivaRate = 21
}) => {
  // Crear documento A4
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4'
  });
  
  const pageWidth = doc.internal.pageSize.getWidth(); // 210mm
  const pageHeight = doc.internal.pageSize.getHeight(); // 297mm
  const margin = 12;
  const contentWidth = pageWidth - margin * 2;
  
  // Colores
  const primaryColor = [30, 41, 59];
  const accentColor = hexToRgb(brandColor);
  const lightGray = [241, 245, 249];
  const textGray = [100, 116, 139];

  // Combinar items
  const allItems = [...itemsMontada, ...itemsDespiece];
  
  // Calcular totales
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
  
  const baseImponible = grandTotal;
  const ivaAmount = grandTotal * (ivaRate / 100);
  const totalConIva = grandTotal + ivaAmount;

  // Preparar datos de la tabla
  const tableData = allItems.map(item => {
    let product = allProducts.find(p => p.id === item.productId);
    let price = 0;
    
    if (item.isManual) {
      product = {
        code: item.customReference || 'MANUAL',
        name: item.manualDescription || 'CONCEPTO MANUAL'
      };
      price = (item.manualPoints || 0) * pointValueMontada * (item.quantity || 1);
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
      name.length > 45 ? name.substring(0, 45) + '...' : name,
      width,
      height,
      depth,
      apertura,
      `${price.toFixed(2)}€`
    ];
  });

  // Guardar especificaciones
  const specs = [];
  if (globalFinish) specs.push(`Acabado: ${globalFinish}`);
  if (doorColorLow) specs.push(`Bajo: ${doorColorLow}`);
  if (doorColorHigh) specs.push(`Alto: ${doorColorHigh}`);
  if (doorColorColumns) specs.push(`Columnas: ${doorColorColumns}`);
  if (sideColor) specs.push(`Costados: ${sideColor}`);
  if (carcassMaterialName) specs.push(`Armazón: ${carcassMaterialName}`);

  // ==========================================
  // FUNCIÓN PARA DIBUJAR ENCABEZADO
  // ==========================================
  const drawHeader = (pageNum, totalPages) => {
    let yPos = 10;
    
    // Logo
    let logoWidth = 0;
    const maxLogoHeight = 18;
    const maxLogoWidth = 40;
    
    if (logo && logo.startsWith('data:image')) {
      try {
        const aspectRatio = 2;
        let imgWidth = maxLogoWidth;
        let imgHeight = imgWidth / aspectRatio;
        if (imgHeight > maxLogoHeight) {
          imgHeight = maxLogoHeight;
          imgWidth = imgHeight * aspectRatio;
        }
        doc.addImage(logo, 'AUTO', margin, yPos, imgWidth, imgHeight);
        logoWidth = imgWidth + 5;
      } catch (e) {
        console.error('Error adding logo:', e);
      }
    }
    
    // Título empresa
    doc.setFontSize(16);
    doc.setTextColor(...primaryColor);
    doc.setFont('helvetica', 'bold');
    doc.text(companyName, margin + logoWidth, yPos + 6);
    
    // Subtítulo
    doc.setFontSize(7);
    doc.setTextColor(...accentColor);
    doc.text('PRESUPUESTO TÉCNICO', margin + logoWidth, yPos + 11);
    
    // Número de expediente (derecha)
    doc.setFontSize(10);
    doc.setTextColor(...primaryColor);
    doc.setFont('helvetica', 'bold');
    doc.text(`Nº ${budgetNumber || 'SIN NÚMERO'}`, pageWidth - margin, yPos + 3, { align: 'right' });
    
    doc.setFontSize(7);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...textGray);
    doc.text(`${new Date().toLocaleDateString('es-ES')}`, pageWidth - margin, yPos + 8, { align: 'right' });
    
    if (internalReference) {
      doc.text(`Ref: ${internalReference}`, pageWidth - margin, yPos + 12, { align: 'right' });
    }
    
    // Página
    doc.setFontSize(6);
    doc.text(`Página ${pageNum} de ${totalPages}`, pageWidth - margin, yPos + 16, { align: 'right' });
    
    yPos += 22;
    
    // Línea separadora
    doc.setDrawColor(...accentColor);
    doc.setLineWidth(0.8);
    doc.line(margin, yPos, pageWidth - margin, yPos);
    
    yPos += 6;
    
    // Datos del cliente (solo en primera página o más compacto en siguientes)
    if (pageNum === 1) {
      doc.setFillColor(...lightGray);
      doc.roundedRect(margin, yPos, contentWidth, 18, 2, 2, 'F');
      
      doc.setFontSize(7);
      doc.setTextColor(...textGray);
      doc.text('CLIENTE', margin + 4, yPos + 5);
      
      doc.setFontSize(10);
      doc.setTextColor(...primaryColor);
      doc.setFont('helvetica', 'bold');
      doc.text(capitalizeName(customerName) || 'Sin especificar', margin + 4, yPos + 11);
      
      if (customerAddress) {
        doc.setFontSize(8);
        doc.setFont('helvetica', 'normal');
        doc.text(capitalizeName(customerAddress), margin + 4, yPos + 15);
      }
      
      yPos += 22;
    } else {
      // En páginas siguientes, mostrar cliente en una línea
      doc.setFontSize(7);
      doc.setTextColor(...textGray);
      doc.text(`Cliente: ${capitalizeName(customerName) || 'Sin especificar'}`, margin, yPos + 3);
      yPos += 8;
    }
    
    return yPos;
  };

  // ==========================================
  // FUNCIÓN PARA DIBUJAR TOTALES (HORIZONTAL)
  // ==========================================
  const drawTotals = (yPos) => {
    const totalsHeight = 18;
    const boxY = yPos;
    
    // Fondo completo para totales
    doc.setFillColor(...primaryColor);
    doc.roundedRect(margin, boxY, contentWidth, totalsHeight, 2, 2, 'F');
    
    // Dividir en 4 secciones horizontales
    const sectionWidth = contentWidth / 4;
    
    // BRUTO LÍNEAS
    doc.setFontSize(6);
    doc.setTextColor(148, 163, 184);
    doc.text('BRUTO LÍNEAS', margin + 4, boxY + 6);
    doc.setFontSize(9);
    doc.setTextColor(255, 255, 255);
    doc.setFont('helvetica', 'bold');
    doc.text(`${baseImponible.toFixed(2)}€`, margin + 4, boxY + 13);
    
    // BASE IMPONIBLE NETO
    doc.setFontSize(6);
    doc.setTextColor(148, 163, 184);
    doc.setFont('helvetica', 'normal');
    doc.text('BASE IMPONIBLE', margin + sectionWidth + 4, boxY + 6);
    doc.setFontSize(9);
    doc.setTextColor(255, 255, 255);
    doc.setFont('helvetica', 'bold');
    doc.text(`${baseImponible.toFixed(2)}€`, margin + sectionWidth + 4, boxY + 13);
    
    // IVA
    doc.setFontSize(6);
    doc.setTextColor(148, 163, 184);
    doc.setFont('helvetica', 'normal');
    doc.text(`IVA ${ivaRate}%`, margin + sectionWidth * 2 + 4, boxY + 6);
    doc.setFontSize(9);
    doc.setTextColor(255, 255, 255);
    doc.setFont('helvetica', 'bold');
    doc.text(`${ivaAmount.toFixed(2)}€`, margin + sectionWidth * 2 + 4, boxY + 13);
    
    // TOTAL PRESUPUESTO (destacado)
    doc.setFillColor(...accentColor);
    doc.roundedRect(margin + sectionWidth * 3, boxY, sectionWidth, totalsHeight, 2, 2, 'F');
    
    doc.setFontSize(6);
    doc.setTextColor(255, 255, 255);
    doc.setFont('helvetica', 'normal');
    doc.text('TOTAL PRESUPUESTO', margin + sectionWidth * 3 + 4, boxY + 6);
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text(`${totalConIva.toFixed(2)}€`, margin + sectionWidth * 3 + sectionWidth - 4, boxY + 13, { align: 'right' });
    
    return boxY + totalsHeight + 4;
  };

  // ==========================================
  // FUNCIÓN PARA DIBUJAR PIE DE PÁGINA
  // ==========================================
  const drawFooter = (yPos) => {
    // Especificaciones
    if (specs.length > 0) {
      doc.setFontSize(6);
      doc.setTextColor(...textGray);
      doc.setFont('helvetica', 'normal');
      
      // Dividir specs en líneas si son muchas
      const specsText = specs.join('  •  ');
      if (specsText.length > 100) {
        const mid = Math.ceil(specs.length / 2);
        doc.text(specs.slice(0, mid).join('  •  '), pageWidth / 2, yPos, { align: 'center' });
        doc.text(specs.slice(mid).join('  •  '), pageWidth / 2, yPos + 4, { align: 'center' });
        yPos += 8;
      } else {
        doc.text(specsText, pageWidth / 2, yPos, { align: 'center' });
        yPos += 5;
      }
    }
    
    // Texto legal
    doc.setFontSize(5);
    doc.setTextColor(148, 163, 184);
    doc.text('Presupuesto válido 30 días. Consulte condiciones de montaje y transporte.', pageWidth / 2, yPos, { align: 'center' });
    doc.text(`${companyName} - ${new Date().toLocaleString('es-ES')}`, pageWidth / 2, yPos + 3, { align: 'center' });
  };

  // ==========================================
  // CALCULAR PAGINACIÓN
  // ==========================================
  
  // Altura disponible para contenido en primera página
  const headerHeightFirstPage = 60; // Encabezado completo con cliente
  const headerHeightOtherPages = 38; // Encabezado reducido
  const totalsHeight = 22;
  const footerHeight = 15;
  const rowHeight = 6; // Altura aproximada por fila de tabla
  
  // Espacio disponible para filas
  const availableFirstPage = pageHeight - headerHeightFirstPage - totalsHeight - footerHeight - 10;
  const availableOtherPages = pageHeight - headerHeightOtherPages - totalsHeight - footerHeight - 10;
  
  const maxRowsFirstPage = Math.floor(availableFirstPage / rowHeight);
  const maxRowsOtherPages = Math.floor(availableOtherPages / rowHeight);
  
  // Calcular número de páginas necesarias
  let totalPages = 1;
  let remainingRows = tableData.length;
  
  if (remainingRows > maxRowsFirstPage) {
    remainingRows -= maxRowsFirstPage;
    totalPages += Math.ceil(remainingRows / maxRowsOtherPages);
  }

  // ==========================================
  // GENERAR PÁGINAS
  // ==========================================
  
  let currentPage = 1;
  let rowIndex = 0;
  
  while (rowIndex < tableData.length || currentPage === 1) {
    if (currentPage > 1) {
      doc.addPage();
    }
    
    // Dibujar encabezado
    let yPos = drawHeader(currentPage, totalPages);
    
    // Calcular filas para esta página
    const maxRows = currentPage === 1 ? maxRowsFirstPage : maxRowsOtherPages;
    const pageRows = tableData.slice(rowIndex, rowIndex + maxRows);
    
    if (pageRows.length > 0) {
      // Título de sección
      doc.setFontSize(8);
      doc.setTextColor(...primaryColor);
      doc.setFont('helvetica', 'bold');
      doc.text('DETALLE DEL PRESUPUESTO', margin, yPos);
      yPos += 4;
      
      // Tabla de artículos
      autoTable(doc, {
        startY: yPos,
        head: [['UD', 'REF', 'DESCRIPCIÓN', 'AN', 'AL', 'FO', 'AP', 'IMPORTE']],
        body: pageRows,
        theme: 'striped',
        headStyles: {
          fillColor: primaryColor,
          textColor: [255, 255, 255],
          fontStyle: 'bold',
          fontSize: 6,
          cellPadding: 1.5
        },
        bodyStyles: {
          fontSize: 6,
          cellPadding: 1.2
        },
        alternateRowStyles: {
          fillColor: [248, 250, 252]
        },
        columnStyles: {
          0: { cellWidth: 8, halign: 'center' },
          1: { cellWidth: 22 },
          2: { cellWidth: 'auto' },
          3: { cellWidth: 10, halign: 'center' },
          4: { cellWidth: 10, halign: 'center' },
          5: { cellWidth: 10, halign: 'center' },
          6: { cellWidth: 8, halign: 'center' },
          7: { cellWidth: 20, halign: 'right' }
        },
        margin: { left: margin, right: margin },
        tableLineColor: [226, 232, 240],
        tableLineWidth: 0.1
      });
      
      yPos = doc.lastAutoTable.finalY + 5;
    }
    
    rowIndex += maxRows;
    
    // En la última página (o única página), dibujar totales y footer
    if (rowIndex >= tableData.length) {
      // Si no hay espacio suficiente para totales, crear nueva página
      if (yPos > pageHeight - totalsHeight - footerHeight - 5) {
        doc.addPage();
        currentPage++;
        yPos = drawHeader(currentPage, totalPages + 1);
      }
      
      yPos = drawTotals(yPos);
      drawFooter(yPos + 2);
      break;
    }
    
    currentPage++;
  }

  // Si no hay items, mostrar mensaje y totales
  if (tableData.length === 0) {
    let yPos = drawHeader(1, 1);
    
    doc.setFontSize(10);
    doc.setTextColor(...textGray);
    doc.text('No hay artículos en este presupuesto', pageWidth / 2, yPos + 20, { align: 'center' });
    
    yPos = drawTotals(yPos + 40);
    drawFooter(yPos + 2);
  }

  // ==========================================
  // DESCARGAR
  // ==========================================
  
  const fileName = `Presupuesto_${budgetNumber || 'SIN_NUMERO'}_${customerName?.replace(/\s+/g, '_') || 'Cliente'}.pdf`;
  doc.save(fileName);
  
  return fileName;
};

/**
 * Genera un PDF del despiece de armarios
 */
export const generateArmariosDespiecePDF = ({
  customerName = '',
  projectRef = '',
  dimensions = { width: 0, height: 0, depth: 0 },
  doorType = '',
  modules = [],
  boards = [],
  accessories = [],
  totals = {},
  ivaRate = 21,
  logo,
  brandColor = '#ea580c',
  companyName = 'LUIGGI HOME'
}) => {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4'
  });
  
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 12;
  const contentWidth = pageWidth - margin * 2;
  
  const primaryColor = [30, 41, 59];
  const accentColor = hexToRgb(brandColor);
  const textGray = [100, 116, 139];
  const lightGray = [241, 245, 249];
  
  let yPos = 15;
  
  // Logo
  let logoWidth = 0;
  if (logo && logo.startsWith('data:image')) {
    try {
      doc.addImage(logo, 'AUTO', margin, yPos, 35, 15);
      logoWidth = 40;
    } catch (e) {
      console.error('Error adding logo:', e);
    }
  }
  
  // Título
  doc.setFontSize(16);
  doc.setTextColor(...primaryColor);
  doc.setFont('helvetica', 'bold');
  doc.text(companyName, margin + logoWidth, yPos + 6);
  
  doc.setFontSize(7);
  doc.setTextColor(...accentColor);
  doc.text('DESPIECE ARMARIO', margin + logoWidth, yPos + 11);
  
  // Info proyecto (derecha)
  doc.setFontSize(9);
  doc.setTextColor(...primaryColor);
  doc.text(projectRef || 'Sin referencia', pageWidth - margin, yPos + 3, { align: 'right' });
  
  doc.setFontSize(7);
  doc.setTextColor(...textGray);
  doc.text(new Date().toLocaleDateString('es-ES'), pageWidth - margin, yPos + 8, { align: 'right' });
  
  yPos += 20;
  
  // Línea separadora
  doc.setDrawColor(...accentColor);
  doc.setLineWidth(0.8);
  doc.line(margin, yPos, pageWidth - margin, yPos);
  
  yPos += 8;
  
  // Datos cliente y dimensiones
  doc.setFillColor(...lightGray);
  doc.roundedRect(margin, yPos, contentWidth, 16, 2, 2, 'F');
  
  doc.setFontSize(7);
  doc.setTextColor(...textGray);
  doc.text('CLIENTE', margin + 4, yPos + 5);
  doc.text('DIMENSIONES', margin + contentWidth / 2, yPos + 5);
  
  doc.setFontSize(9);
  doc.setTextColor(...primaryColor);
  doc.setFont('helvetica', 'bold');
  doc.text(capitalizeName(customerName) || 'Sin especificar', margin + 4, yPos + 12);
  doc.text(`${dimensions.width} x ${dimensions.height} x ${dimensions.depth} cm`, margin + contentWidth / 2, yPos + 12);
  
  yPos += 22;
  
  // Tabla de tableros
  if (boards && boards.length > 0) {
    doc.setFontSize(8);
    doc.setTextColor(...primaryColor);
    doc.setFont('helvetica', 'bold');
    doc.text('LISTADO DE TABLEROS', margin, yPos);
    yPos += 4;
    
    const boardsData = boards.map(b => [
      b.quantity || 1,
      b.name || 'Tablero',
      `${b.width || 0} x ${b.height || 0}`,
      b.material || '-',
      `${(b.price || 0).toFixed(2)}€`
    ]);
    
    autoTable(doc, {
      startY: yPos,
      head: [['UDS', 'PIEZA', 'MEDIDAS (mm)', 'MATERIAL', 'PRECIO']],
      body: boardsData,
      theme: 'striped',
      headStyles: {
        fillColor: primaryColor,
        textColor: [255, 255, 255],
        fontStyle: 'bold',
        fontSize: 6,
        cellPadding: 1.5
      },
      bodyStyles: {
        fontSize: 6,
        cellPadding: 1.2
      },
      columnStyles: {
        0: { cellWidth: 12, halign: 'center' },
        1: { cellWidth: 'auto' },
        2: { cellWidth: 30, halign: 'center' },
        3: { cellWidth: 35 },
        4: { cellWidth: 22, halign: 'right' }
      },
      margin: { left: margin, right: margin }
    });
    
    yPos = doc.lastAutoTable.finalY + 8;
  }
  
  // Accesorios
  if (accessories && accessories.length > 0) {
    if (yPos > pageHeight - 80) {
      doc.addPage();
      yPos = 20;
    }
    
    doc.setFontSize(8);
    doc.setTextColor(...primaryColor);
    doc.setFont('helvetica', 'bold');
    doc.text('ACCESORIOS Y HERRAJES', margin, yPos);
    yPos += 4;
    
    const accData = accessories.map(a => [
      a.quantity || 1,
      a.name || 'Accesorio',
      `${(a.unitPrice || 0).toFixed(2)}€`,
      `${((a.quantity || 1) * (a.unitPrice || 0)).toFixed(2)}€`
    ]);
    
    autoTable(doc, {
      startY: yPos,
      head: [['UDS', 'DESCRIPCIÓN', 'PRECIO UD.', 'TOTAL']],
      body: accData,
      theme: 'striped',
      headStyles: {
        fillColor: primaryColor,
        textColor: [255, 255, 255],
        fontStyle: 'bold',
        fontSize: 6,
        cellPadding: 1.5
      },
      bodyStyles: {
        fontSize: 6,
        cellPadding: 1.2
      },
      columnStyles: {
        0: { cellWidth: 12, halign: 'center' },
        1: { cellWidth: 'auto' },
        2: { cellWidth: 25, halign: 'right' },
        3: { cellWidth: 25, halign: 'right' }
      },
      margin: { left: margin, right: margin }
    });
    
    yPos = doc.lastAutoTable.finalY + 8;
  }
  
  // Totales horizontales
  if (yPos > pageHeight - 40) {
    doc.addPage();
    yPos = 20;
  }
  
  const baseImponible = totals.subtotal || 0;
  const ivaAmount = baseImponible * (ivaRate / 100);
  const totalConIva = baseImponible + ivaAmount;
  
  doc.setFillColor(...primaryColor);
  doc.roundedRect(margin, yPos, contentWidth, 16, 2, 2, 'F');
  
  const sectionWidth = contentWidth / 3;
  
  // Base imponible
  doc.setFontSize(6);
  doc.setTextColor(148, 163, 184);
  doc.text('BASE IMPONIBLE', margin + 4, yPos + 5);
  doc.setFontSize(9);
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.text(`${baseImponible.toFixed(2)}€`, margin + 4, yPos + 11);
  
  // IVA
  doc.setFontSize(6);
  doc.setTextColor(148, 163, 184);
  doc.setFont('helvetica', 'normal');
  doc.text(`IVA ${ivaRate}%`, margin + sectionWidth + 4, yPos + 5);
  doc.setFontSize(9);
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.text(`${ivaAmount.toFixed(2)}€`, margin + sectionWidth + 4, yPos + 11);
  
  // Total
  doc.setFillColor(...accentColor);
  doc.roundedRect(margin + sectionWidth * 2, yPos, sectionWidth, 16, 2, 2, 'F');
  
  doc.setFontSize(6);
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'normal');
  doc.text('TOTAL', margin + sectionWidth * 2 + 4, yPos + 5);
  doc.setFontSize(11);
  doc.setFont('helvetica', 'bold');
  doc.text(`${totalConIva.toFixed(2)}€`, margin + sectionWidth * 3 - 4, yPos + 11, { align: 'right' });
  
  // Footer
  yPos += 22;
  doc.setFontSize(5);
  doc.setTextColor(148, 163, 184);
  doc.text(`${companyName} - Despiece generado el ${new Date().toLocaleString('es-ES')}`, pageWidth / 2, yPos, { align: 'center' });
  
  // Guardar
  const fileName = `Despiece_Armario_${projectRef?.replace(/\s+/g, '_') || 'SinRef'}.pdf`;
  doc.save(fileName);
  
  return fileName;
};
