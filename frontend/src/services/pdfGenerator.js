import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

/**
 * Capitaliza correctamente un nombre
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
 * Genera un PDF del presupuesto - Formato A4 con totales al final de página
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
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4'
  });
  
  const pageWidth = 210;
  const pageHeight = 297;
  const margin = 12;
  const contentWidth = pageWidth - margin * 2;
  
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
      name.length > 50 ? name.substring(0, 50) + '...' : name,
      width,
      height,
      depth,
      apertura,
      `${price.toFixed(2)}€`
    ];
  });

  // Especificaciones
  const specs = [];
  if (globalFinish) specs.push(`Acabado: ${globalFinish}`);
  if (doorColorLow) specs.push(`Bajo: ${doorColorLow}`);
  if (doorColorHigh) specs.push(`Alto: ${doorColorHigh}`);
  if (doorColorColumns) specs.push(`Columnas: ${doorColorColumns}`);
  if (sideColor) specs.push(`Costados: ${sideColor}`);
  if (carcassMaterialName) specs.push(`Armazón: ${carcassMaterialName}`);

  // Calcular paginación
  const headerHeight = 50;
  const totalsHeight = 35;
  const footerHeight = 28;  // Aumentado para mostrar mejor las especificaciones
  const rowHeight = 6;
  const availableForRows = pageHeight - headerHeight - totalsHeight - footerHeight - 20;
  const maxRowsPerPage = Math.floor(availableForRows / rowHeight);
  
  const totalPages = Math.max(1, Math.ceil(tableData.length / maxRowsPerPage));

  // ==========================================
  // DIBUJAR ENCABEZADO
  // ==========================================
  const drawHeader = (pageNum) => {
    let yPos = margin;
    
    // Logo proporcionado (máximo 45mm ancho, mantener proporción)
    let logoEndX = margin;
    if (logo && logo.startsWith('data:image')) {
      try {
        const maxLogoWidth = 45;
        const maxLogoHeight = 18;
        
        // Crear una imagen temporal para obtener las dimensiones reales
        const img = new Image();
        img.src = logo;
        
        // Calcular proporción real del logo
        let imgWidth = maxLogoWidth;
        let imgHeight = maxLogoHeight;
        
        // Si podemos obtener las dimensiones reales, usarlas
        if (img.naturalWidth && img.naturalHeight) {
          const aspectRatio = img.naturalWidth / img.naturalHeight;
          imgWidth = maxLogoWidth;
          imgHeight = imgWidth / aspectRatio;
          if (imgHeight > maxLogoHeight) {
            imgHeight = maxLogoHeight;
            imgWidth = imgHeight * aspectRatio;
          }
        } else {
          // Fallback: asumir proporción del logo Luiggi (~3:1)
          const aspectRatio = 3;
          imgWidth = maxLogoWidth;
          imgHeight = imgWidth / aspectRatio;
          if (imgHeight > maxLogoHeight) {
            imgHeight = maxLogoHeight;
            imgWidth = imgHeight * aspectRatio;
          }
        }
        
        doc.addImage(logo, 'AUTO', margin, yPos, imgWidth, imgHeight);
        logoEndX = margin + imgWidth + 5;
      } catch (e) {
        console.error('Error adding logo:', e);
      }
    }
    
    // Nombre empresa y PRESUPUESTO TÉCNICO
    doc.setFontSize(14);
    doc.setTextColor(...primaryColor);
    doc.setFont('helvetica', 'bold');
    doc.text(companyName, logoEndX, yPos + 6);
    
    // PRESUPUESTO TÉCNICO más grande
    doc.setFontSize(9);
    doc.setTextColor(...accentColor);
    doc.setFont('helvetica', 'bold');
    doc.text('PRESUPUESTO TÉCNICO', logoEndX, yPos + 12);
    
    // Número de expediente (derecha)
    doc.setFontSize(10);
    doc.setTextColor(...primaryColor);
    doc.setFont('helvetica', 'bold');
    doc.text(`Nº ${budgetNumber || 'SIN NÚMERO'}`, pageWidth - margin, yPos + 4, { align: 'right' });
    
    doc.setFontSize(8);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...textGray);
    doc.text(new Date().toLocaleDateString('es-ES'), pageWidth - margin, yPos + 10, { align: 'right' });
    
    if (internalReference) {
      doc.text(`Ref: ${internalReference}`, pageWidth - margin, yPos + 15, { align: 'right' });
    }
    
    // Página
    doc.setFontSize(7);
    doc.text(`Página ${pageNum} de ${totalPages}`, pageWidth - margin, yPos + 20, { align: 'right' });
    
    yPos += 24;
    
    // Línea separadora
    doc.setDrawColor(...accentColor);
    doc.setLineWidth(0.8);
    doc.line(margin, yPos, pageWidth - margin, yPos);
    
    yPos += 6;
    
    // Datos del cliente
    doc.setFillColor(...lightGray);
    doc.roundedRect(margin, yPos, contentWidth, 14, 2, 2, 'F');
    
    doc.setFontSize(7);
    doc.setTextColor(...textGray);
    doc.text('CLIENTE', margin + 4, yPos + 5);
    
    doc.setFontSize(9);
    doc.setTextColor(...primaryColor);
    doc.setFont('helvetica', 'bold');
    doc.text(capitalizeName(customerName) || 'Sin especificar', margin + 4, yPos + 10);
    
    if (customerAddress) {
      doc.setFontSize(7);
      doc.setFont('helvetica', 'normal');
      doc.text(capitalizeName(customerAddress), margin + 70, yPos + 10);
    }
    
    return yPos + 18;
  };

  // ==========================================
  // DIBUJAR TOTALES (siempre al final de la página)
  // ==========================================
  const drawTotals = () => {
    const totalsY = pageHeight - totalsHeight - footerHeight;
    
    // Fondo para totales
    doc.setFillColor(...primaryColor);
    doc.roundedRect(margin, totalsY, contentWidth, 20, 2, 2, 'F');
    
    const sectionWidth = contentWidth / 4;
    
    // BRUTO LÍNEAS
    doc.setFontSize(6);
    doc.setTextColor(148, 163, 184);
    doc.text('BRUTO LÍNEAS', margin + 4, totalsY + 6);
    doc.setFontSize(10);
    doc.setTextColor(255, 255, 255);
    doc.setFont('helvetica', 'bold');
    doc.text(`${baseImponible.toFixed(2)}€`, margin + 4, totalsY + 14);
    
    // BASE IMPONIBLE
    doc.setFontSize(6);
    doc.setTextColor(148, 163, 184);
    doc.setFont('helvetica', 'normal');
    doc.text('BASE IMPONIBLE', margin + sectionWidth + 4, totalsY + 6);
    doc.setFontSize(10);
    doc.setTextColor(255, 255, 255);
    doc.setFont('helvetica', 'bold');
    doc.text(`${baseImponible.toFixed(2)}€`, margin + sectionWidth + 4, totalsY + 14);
    
    // IVA
    doc.setFontSize(6);
    doc.setTextColor(148, 163, 184);
    doc.setFont('helvetica', 'normal');
    doc.text(`IVA ${ivaRate}%`, margin + sectionWidth * 2 + 4, totalsY + 6);
    doc.setFontSize(10);
    doc.setTextColor(255, 255, 255);
    doc.setFont('helvetica', 'bold');
    doc.text(`${ivaAmount.toFixed(2)}€`, margin + sectionWidth * 2 + 4, totalsY + 14);
    
    // TOTAL (destacado)
    doc.setFillColor(...accentColor);
    doc.roundedRect(margin + sectionWidth * 3, totalsY, sectionWidth, 20, 2, 2, 'F');
    
    doc.setFontSize(6);
    doc.setTextColor(255, 255, 255);
    doc.setFont('helvetica', 'normal');
    doc.text('TOTAL PRESUPUESTO', margin + sectionWidth * 3 + 4, totalsY + 6);
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text(`${totalConIva.toFixed(2)}€`, margin + sectionWidth * 4 - 4, totalsY + 14, { align: 'right' });
  };

  // ==========================================
  // DIBUJAR FOOTER
  // ==========================================
  const drawFooter = () => {
    const footerY = pageHeight - footerHeight;
    
    // Especificaciones de materiales - mostrar en formato tabla
    if (specs.length > 0) {
      doc.setFillColor(248, 250, 252);
      doc.roundedRect(margin, footerY, contentWidth, 16, 1, 1, 'F');
      
      doc.setFontSize(5);
      doc.setTextColor(100, 116, 139);
      doc.setFont('helvetica', 'bold');
      doc.text('ESPECIFICACIONES DE ACABADOS', margin + 2, footerY + 3);
      
      doc.setFontSize(6);
      doc.setTextColor(...primaryColor);
      doc.setFont('helvetica', 'normal');
      
      // Dividir specs en columnas
      const colWidth = contentWidth / 3;
      specs.forEach((spec, i) => {
        const col = i % 3;
        const row = Math.floor(i / 3);
        const x = margin + 2 + (col * colWidth);
        const y = footerY + 7 + (row * 4);
        doc.text(spec, x, y);
      });
    }
    
    // Texto legal
    doc.setFontSize(5);
    doc.setTextColor(148, 163, 184);
    doc.text('Presupuesto válido 30 días. Consulte condiciones de montaje y transporte.', pageWidth / 2, footerY + 18, { align: 'center' });
    doc.text(`${companyName} - ${new Date().toLocaleString('es-ES')}`, pageWidth / 2, footerY + 22, { align: 'center' });
  };

  // ==========================================
  // GENERAR PÁGINAS
  // ==========================================
  let currentPage = 1;
  let rowIndex = 0;
  
  while (currentPage <= totalPages) {
    if (currentPage > 1) {
      doc.addPage();
    }
    
    // Dibujar encabezado
    let yPos = drawHeader(currentPage);
    
    // Título de sección
    doc.setFontSize(8);
    doc.setTextColor(...primaryColor);
    doc.setFont('helvetica', 'bold');
    doc.text('DETALLE DEL PRESUPUESTO', margin, yPos);
    yPos += 4;
    
    // Calcular filas para esta página
    const rowsThisPage = tableData.slice(rowIndex, rowIndex + maxRowsPerPage);
    
    if (rowsThisPage.length > 0) {
      autoTable(doc, {
        startY: yPos,
        head: [['UD', 'REF', 'DESCRIPCIÓN', 'AN', 'AL', 'FO', 'AP', 'IMPORTE']],
        body: rowsThisPage,
        theme: 'striped',
        headStyles: {
          fillColor: primaryColor,
          textColor: [255, 255, 255],
          fontStyle: 'bold',
          fontSize: 7,
          cellPadding: 2
        },
        bodyStyles: {
          fontSize: 7,
          cellPadding: 1.5
        },
        alternateRowStyles: {
          fillColor: [248, 250, 252]
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
        margin: { left: margin, right: margin },
        tableLineColor: [226, 232, 240],
        tableLineWidth: 0.1
      });
    }
    
    rowIndex += maxRowsPerPage;
    
    // Dibujar totales y footer solo en la última página
    if (currentPage === totalPages) {
      drawTotals();
      drawFooter();
    }
    
    currentPage++;
  }

  // Si no hay items
  if (tableData.length === 0) {
    let yPos = drawHeader(1);
    
    doc.setFontSize(10);
    doc.setTextColor(...textGray);
    doc.text('No hay artículos en este presupuesto', pageWidth / 2, yPos + 30, { align: 'center' });
    
    drawTotals();
    drawFooter();
  }

  // Guardar
  const fileName = `Presupuesto_${budgetNumber || 'SIN_NUMERO'}_${customerName?.replace(/\s+/g, '_') || 'Cliente'}.pdf`;
  doc.save(fileName);
  
  return fileName;
};

/**
 * Genera un PDF del presupuesto de armarios
 */
export const generateArmarioPresupuestoPDF = ({
  projectName = '',
  customerName = '',
  projectRef = '',
  dimensions = { width: 0, height: 0, depth: 0 },
  modules = 2,
  doorType = '',
  colors = {},
  pricing = {},
  specifications = {},
  boardsCalculation = {},
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
  
  const pageWidth = 210;
  const pageHeight = 297;
  const margin = 12;
  const contentWidth = pageWidth - margin * 2;
  
  const primaryColor = [30, 41, 59];
  const accentColor = hexToRgb(brandColor);
  const textGray = [100, 116, 139];
  const lightGray = [241, 245, 249];
  
  let yPos = margin;
  
  // Logo con proporción correcta
  let logoEndX = margin;
  if (logo && logo.startsWith('data:image')) {
    try {
      const maxLogoWidth = 40;
      const maxLogoHeight = 16;
      const img = new Image();
      img.src = logo;
      const aspectRatio = (img.naturalWidth && img.naturalHeight) ? img.naturalWidth / img.naturalHeight : 3;
      let imgWidth = maxLogoWidth;
      let imgHeight = imgWidth / aspectRatio;
      if (imgHeight > maxLogoHeight) {
        imgHeight = maxLogoHeight;
        imgWidth = imgHeight * aspectRatio;
      }
      doc.addImage(logo, 'AUTO', margin, yPos, imgWidth, imgHeight);
      logoEndX = margin + imgWidth + 5;
    } catch (e) {
      console.error('Error adding logo:', e);
    }
  }
  
  // Título
  doc.setFontSize(14);
  doc.setTextColor(...primaryColor);
  doc.setFont('helvetica', 'bold');
  doc.text(companyName, logoEndX, yPos + 6);
  
  doc.setFontSize(9);
  doc.setTextColor(...accentColor);
  doc.setFont('helvetica', 'bold');
  doc.text('PRESUPUESTO ARMARIO', logoEndX, yPos + 12);
  
  // Info proyecto (derecha)
  doc.setFontSize(9);
  doc.setTextColor(...primaryColor);
  doc.text(projectName || 'Sin nombre', pageWidth - margin, yPos + 4, { align: 'right' });
  
  doc.setFontSize(7);
  doc.setTextColor(...textGray);
  doc.text(new Date().toLocaleDateString('es-ES'), pageWidth - margin, yPos + 10, { align: 'right' });
  
  yPos += 22;
  
  // Línea separadora
  doc.setDrawColor(...accentColor);
  doc.setLineWidth(0.8);
  doc.line(margin, yPos, pageWidth - margin, yPos);
  
  yPos += 8;
  
  // Datos cliente y dimensiones
  doc.setFillColor(...lightGray);
  doc.roundedRect(margin, yPos, contentWidth, 14, 2, 2, 'F');
  
  doc.setFontSize(7);
  doc.setTextColor(...textGray);
  doc.text('CLIENTE', margin + 4, yPos + 5);
  doc.text('DIMENSIONES', margin + contentWidth / 2, yPos + 5);
  
  doc.setFontSize(9);
  doc.setTextColor(...primaryColor);
  doc.setFont('helvetica', 'bold');
  doc.text(capitalizeName(customerName) || 'Sin especificar', margin + 4, yPos + 10);
  doc.text(`${dimensions.width} x ${dimensions.height} x ${dimensions.depth} cm`, margin + contentWidth / 2, yPos + 10);
  
  yPos += 20;
  
  // Configuración
  doc.setFontSize(8);
  doc.setTextColor(...primaryColor);
  doc.setFont('helvetica', 'bold');
  doc.text('CONFIGURACIÓN', margin, yPos);
  yPos += 4;
  
  const configData = [
    ['Módulos', `${modules} módulos`],
    ['Tipo Puertas', doorType === 'sliding' ? 'Correderas' : 'Batientes'],
    ['Color Exterior', colors.exteriorName || '-'],
    ['Color Interior', colors.interiorName || '-']
  ];
  
  autoTable(doc, {
    startY: yPos,
    body: configData,
    theme: 'plain',
    bodyStyles: { fontSize: 7 },
    columnStyles: {
      0: { cellWidth: 40, fontStyle: 'bold' },
      1: { cellWidth: 'auto' }
    },
    margin: { left: margin, right: margin }
  });
  
  // Totales al final de la página
  const totalsY = pageHeight - 50;
  const subtotal = pricing.subtotal || 0;
  const ivaAmount = subtotal * (ivaRate / 100);
  const total = pricing.total || subtotal + ivaAmount;
  
  doc.setFillColor(...primaryColor);
  doc.roundedRect(margin, totalsY, contentWidth, 18, 2, 2, 'F');
  
  const sectionWidth = contentWidth / 3;
  
  doc.setFontSize(6);
  doc.setTextColor(148, 163, 184);
  doc.text('BASE IMPONIBLE', margin + 4, totalsY + 6);
  doc.setFontSize(10);
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.text(`${subtotal.toFixed(2)}€`, margin + 4, totalsY + 13);
  
  doc.setFontSize(6);
  doc.setTextColor(148, 163, 184);
  doc.setFont('helvetica', 'normal');
  doc.text(`IVA ${ivaRate}%`, margin + sectionWidth + 4, totalsY + 6);
  doc.setFontSize(10);
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.text(`${ivaAmount.toFixed(2)}€`, margin + sectionWidth + 4, totalsY + 13);
  
  doc.setFillColor(...accentColor);
  doc.roundedRect(margin + sectionWidth * 2, totalsY, sectionWidth, 18, 2, 2, 'F');
  
  doc.setFontSize(6);
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'normal');
  doc.text('TOTAL', margin + sectionWidth * 2 + 4, totalsY + 6);
  doc.setFontSize(12);
  doc.setFont('helvetica', 'bold');
  doc.text(`${total.toFixed(2)}€`, margin + sectionWidth * 3 - 4, totalsY + 13, { align: 'right' });
  
  // Footer
  doc.setFontSize(5);
  doc.setTextColor(148, 163, 184);
  doc.text(`${companyName} - ${new Date().toLocaleString('es-ES')}`, pageWidth / 2, pageHeight - 10, { align: 'center' });
  
  const fileName = `Presupuesto_Armario_${projectName?.replace(/\s+/g, '_') || 'SinNombre'}.pdf`;
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
  
  const pageWidth = 210;
  const pageHeight = 297;
  const margin = 12;
  const contentWidth = pageWidth - margin * 2;
  
  const primaryColor = [30, 41, 59];
  const accentColor = hexToRgb(brandColor);
  const textGray = [100, 116, 139];
  const lightGray = [241, 245, 249];
  
  let yPos = margin;
  
  // Logo
  if (logo && logo.startsWith('data:image')) {
    try {
      doc.addImage(logo, 'AUTO', margin, yPos, 40, 16);
    } catch (e) {
      console.error('Error adding logo:', e);
    }
  }
  
  // Título
  doc.setFontSize(14);
  doc.setTextColor(...primaryColor);
  doc.setFont('helvetica', 'bold');
  doc.text(companyName, margin + 45, yPos + 6);
  
  doc.setFontSize(9);
  doc.setTextColor(...accentColor);
  doc.setFont('helvetica', 'bold');
  doc.text('DESPIECE ARMARIO', margin + 45, yPos + 12);
  
  doc.setFontSize(8);
  doc.setTextColor(...primaryColor);
  doc.text(projectRef || 'Sin referencia', pageWidth - margin, yPos + 6, { align: 'right' });
  
  doc.setFontSize(7);
  doc.setTextColor(...textGray);
  doc.text(new Date().toLocaleDateString('es-ES'), pageWidth - margin, yPos + 11, { align: 'right' });
  
  yPos += 22;
  
  // Línea
  doc.setDrawColor(...accentColor);
  doc.setLineWidth(0.8);
  doc.line(margin, yPos, pageWidth - margin, yPos);
  
  yPos += 8;
  
  // Cliente y dimensiones
  doc.setFillColor(...lightGray);
  doc.roundedRect(margin, yPos, contentWidth, 14, 2, 2, 'F');
  
  doc.setFontSize(7);
  doc.setTextColor(...textGray);
  doc.text('CLIENTE', margin + 4, yPos + 5);
  doc.text('DIMENSIONES', margin + contentWidth / 2, yPos + 5);
  
  doc.setFontSize(9);
  doc.setTextColor(...primaryColor);
  doc.setFont('helvetica', 'bold');
  doc.text(capitalizeName(customerName) || 'Sin especificar', margin + 4, yPos + 10);
  doc.text(`${dimensions.width} x ${dimensions.height} x ${dimensions.depth} cm`, margin + contentWidth / 2, yPos + 10);
  
  yPos += 20;
  
  // Tableros
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
        fontSize: 7
      },
      bodyStyles: { fontSize: 7 },
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
        fontSize: 7
      },
      bodyStyles: { fontSize: 7 },
      columnStyles: {
        0: { cellWidth: 12, halign: 'center' },
        1: { cellWidth: 'auto' },
        2: { cellWidth: 25, halign: 'right' },
        3: { cellWidth: 25, halign: 'right' }
      },
      margin: { left: margin, right: margin }
    });
  }
  
  // Totales al final
  const totalsY = pageHeight - 40;
  const baseImponible = totals.subtotal || 0;
  const ivaAmount = baseImponible * (ivaRate / 100);
  const totalConIva = baseImponible + ivaAmount;
  
  doc.setFillColor(...primaryColor);
  doc.roundedRect(margin, totalsY, contentWidth, 18, 2, 2, 'F');
  
  const sectionWidth = contentWidth / 3;
  
  doc.setFontSize(6);
  doc.setTextColor(148, 163, 184);
  doc.text('BASE IMPONIBLE', margin + 4, totalsY + 6);
  doc.setFontSize(10);
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.text(`${baseImponible.toFixed(2)}€`, margin + 4, totalsY + 13);
  
  doc.setFontSize(6);
  doc.setTextColor(148, 163, 184);
  doc.setFont('helvetica', 'normal');
  doc.text(`IVA ${ivaRate}%`, margin + sectionWidth + 4, totalsY + 6);
  doc.setFontSize(10);
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.text(`${ivaAmount.toFixed(2)}€`, margin + sectionWidth + 4, totalsY + 13);
  
  doc.setFillColor(...accentColor);
  doc.roundedRect(margin + sectionWidth * 2, totalsY, sectionWidth, 18, 2, 2, 'F');
  
  doc.setFontSize(6);
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'normal');
  doc.text('TOTAL', margin + sectionWidth * 2 + 4, totalsY + 6);
  doc.setFontSize(12);
  doc.setFont('helvetica', 'bold');
  doc.text(`${totalConIva.toFixed(2)}€`, margin + sectionWidth * 3 - 4, totalsY + 13, { align: 'right' });
  
  // Footer
  doc.setFontSize(5);
  doc.setTextColor(148, 163, 184);
  doc.text(`${companyName} - ${new Date().toLocaleString('es-ES')}`, pageWidth / 2, pageHeight - 10, { align: 'center' });
  
  const fileName = `Despiece_Armario_${projectRef?.replace(/\s+/g, '_') || 'SinRef'}.pdf`;
  doc.save(fileName);
  
  return fileName;
};

/**
 * Genera un PDF del Informe Industrial de Fabricación
 */
export const generateManufacturingPDF = ({
  budgetNumber = '',
  customerName = '',
  globalFinish = '',
  carcassColor = '',
  doorColorLow = '',
  doorColorHigh = '',
  doorColorColumns = '',
  sideColor = '',
  items = [],
  allProducts = [],
  logo,
  brandColor = '#ea580c',
  companyName = 'LUIGGI HOME',
  distributorName = ''
}) => {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4'
  });

  const pageWidth = 210;
  const pageHeight = 297;
  const margin = 12;
  const contentWidth = pageWidth - margin * 2;

  const primaryColor = [30, 41, 59];
  const accentColor = hexToRgb(brandColor);
  const textGray = [100, 116, 139];
  const lightGray = [241, 245, 249];

  // Preparar datos de la tabla
  const tableData = items.map(item => {
    const product = allProducts.find(p => p.id === item.productId);
    const code = product?.code || item.productCode || item.customReference || '???';
    const name = product?.name || item.productName || item.manualDescription || 'Sin descripción';
    const width = item.customWidth || product?.width || 0;
    const height = item.customHeight || product?.height || 0;
    const depth = item.customDepth || product?.depth || 0;
    const apertura = item.openingDirection === 'left' ? 'IZQUIERDA' : 'DERECHA';
    const notes = [];
    if (item.hasSpecialWidthCut) notes.push('Corte Ancho');
    if (item.hasSpecialHeightCut) notes.push('Corte Alto');
    if (item.hasSpecialDepthCut) notes.push('Corte Fondo');
    if (item.hasVigaCut) notes.push('Corte Viga');
    
    return [
      item.quantity || 1,
      code,
      name,
      `${width} × ${height} × ${depth}`,
      apertura,
      notes.length > 0 ? notes.join(', ') : '-'
    ];
  });

  // Calcular páginas
  const rowsPerPage = 20;
  const totalPages = Math.ceil(tableData.length / rowsPerPage);

  for (let page = 1; page <= totalPages; page++) {
    if (page > 1) doc.addPage();
    
    let yPos = margin;

    // ==========================================
    // HEADER
    // ==========================================
    if (logo && logo.startsWith('data:image')) {
      try {
        doc.addImage(logo, 'AUTO', margin, yPos, 35, 14);
      } catch (e) {
        doc.setFontSize(16);
        doc.setFont('helvetica', 'bolditalic');
        doc.setTextColor(...primaryColor);
        doc.text(companyName, margin, yPos + 10);
      }
    } else {
      doc.setFontSize(16);
      doc.setFont('helvetica', 'bolditalic');
      doc.setTextColor(...primaryColor);
      doc.text(companyName, margin, yPos + 10);
    }

    if (distributorName) {
      doc.setFontSize(8);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(...accentColor);
      doc.text(distributorName.toUpperCase(), margin, yPos + 18);
    }

    // Título y datos (derecha)
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...primaryColor);
    doc.text('ORDEN DE FABRICACIÓN', pageWidth - margin, yPos + 6, { align: 'right' });
    
    doc.setFontSize(8);
    doc.setTextColor(...textGray);
    doc.text(`Expediente: ${budgetNumber}`, pageWidth - margin, yPos + 12, { align: 'right' });
    doc.text(`Fecha: ${new Date().toLocaleDateString('es-ES')}`, pageWidth - margin, yPos + 17, { align: 'right' });
    doc.text(`Página ${page} de ${totalPages}`, pageWidth - margin, yPos + 22, { align: 'right' });

    yPos += 28;

    // Línea separadora
    doc.setDrawColor(...accentColor);
    doc.setLineWidth(0.8);
    doc.line(margin, yPos, pageWidth - margin, yPos);
    yPos += 6;

    // ==========================================
    // INFO CLIENTE Y ACABADO GLOBAL
    // ==========================================
    doc.setFillColor(...lightGray);
    doc.roundedRect(margin, yPos, contentWidth / 2 - 2, 12, 2, 2, 'F');
    doc.setFontSize(6);
    doc.setTextColor(...textGray);
    doc.text('CLIENTE', margin + 3, yPos + 4);
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...primaryColor);
    doc.text(customerName || 'Sin especificar', margin + 3, yPos + 9);

    doc.setFillColor(255, 237, 213);
    doc.roundedRect(margin + contentWidth / 2 + 2, yPos, contentWidth / 2 - 2, 12, 2, 2, 'F');
    doc.setFontSize(6);
    doc.setTextColor(...textGray);
    doc.setFont('helvetica', 'normal');
    doc.text('ACABADO GLOBAL', margin + contentWidth / 2 + 5, yPos + 4);
    doc.setFontSize(8);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(194, 65, 12);
    doc.text(globalFinish || 'Sin especificar', margin + contentWidth / 2 + 5, yPos + 9);

    yPos += 18;

    // ==========================================
    // TÍTULO LISTA DE MUEBLES
    // ==========================================
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...primaryColor);
    doc.text('LISTA DE MUEBLES A FABRICAR', margin, yPos);
    yPos += 4;

    // ==========================================
    // TABLA DE MUEBLES
    // ==========================================
    const startRow = (page - 1) * rowsPerPage;
    const endRow = Math.min(startRow + rowsPerPage, tableData.length);
    const pageRows = tableData.slice(startRow, endRow);

    autoTable(doc, {
      startY: yPos,
      head: [['CANT.', 'REFERENCIA', 'DESCRIPCIÓN', 'MEDIDAS (mm)', 'APERT.', 'NOTAS']],
      body: pageRows,
      theme: 'striped',
      headStyles: {
        fillColor: primaryColor,
        textColor: [255, 255, 255],
        fontStyle: 'bold',
        fontSize: 7,
        cellPadding: 2
      },
      bodyStyles: {
        fontSize: 7,
        cellPadding: 2
      },
      alternateRowStyles: {
        fillColor: [248, 250, 252]
      },
      columnStyles: {
        0: { cellWidth: 12, halign: 'center' },
        1: { cellWidth: 28, fontStyle: 'bold' },
        2: { cellWidth: 60 },
        3: { cellWidth: 35, halign: 'center' },
        4: { cellWidth: 18, halign: 'center' },
        5: { cellWidth: 33 }
      },
      margin: { left: margin, right: margin }
    });

    // Solo en la última página: especificaciones de materiales
    if (page === totalPages) {
      const finalY = doc.lastAutoTable.finalY + 10;
      
      // ==========================================
      // ESPECIFICACIONES DE MATERIALES
      // ==========================================
      doc.setFillColor(...lightGray);
      doc.roundedRect(margin, finalY, contentWidth, 32, 2, 2, 'F');
      
      doc.setFontSize(8);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(...primaryColor);
      doc.text('ESPECIFICACIONES DE MATERIALES', margin + 4, finalY + 6);
      
      const specs = [];
      if (carcassColor) specs.push(['Armazón/Casco:', carcassColor]);
      if (globalFinish) specs.push(['Frentes:', globalFinish]);
      if (doorColorLow) specs.push(['Puertas Bajos:', doorColorLow]);
      if (doorColorHigh) specs.push(['Puertas Altos:', doorColorHigh]);
      if (doorColorColumns) specs.push(['Puertas Columnas:', doorColorColumns]);
      if (sideColor) specs.push(['Costados/Vistos:', sideColor]);
      
      doc.setFontSize(7);
      doc.setFont('helvetica', 'normal');
      
      const colWidth = contentWidth / 2;
      specs.forEach((spec, i) => {
        const col = i % 2;
        const row = Math.floor(i / 2);
        const x = margin + 4 + (col * colWidth);
        const y = finalY + 12 + (row * 5);
        
        doc.setTextColor(...textGray);
        doc.text(spec[0], x, y);
        doc.setTextColor(...primaryColor);
        doc.setFont('helvetica', 'bold');
        doc.text(spec[1], x + 30, y);
        doc.setFont('helvetica', 'normal');
      });
    }

    // ==========================================
    // FOOTER
    // ==========================================
    doc.setFontSize(5);
    doc.setTextColor(148, 163, 184);
    doc.text(`DOCUMENTO GENERADO POR ${companyName} MASTER INDUSTRIAL SYSTEM V2026`, pageWidth / 2, pageHeight - 8, { align: 'center' });
  }

  const fileName = `Orden_Fabricacion_${budgetNumber?.replace(/\s+/g, '_') || 'SinRef'}.pdf`;
  doc.save(fileName);
  
  return fileName;
};
