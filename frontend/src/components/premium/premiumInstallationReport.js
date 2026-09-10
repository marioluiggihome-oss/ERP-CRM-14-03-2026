/* © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT] */
import { installationReady } from './premiumBrief';

export function installationReportData(rows) {
  if (!rows.length || !rows.every(installationReady)) throw new Error('Completa y confirma todos los puntos antes de exportar.');
  return ['electricidad', 'fontaneria'].map(trade => ({
    title: trade === 'electricidad' ? 'Electricidad' : 'Fontanería',
    body: rows.filter(r => r.trade === trade).map(r => [r.label, r.wall, r.origin, `${r.height} cm`, `${r.distance} cm`]),
  })).filter(group => group.body.length);
}

export async function downloadInstallationReport(rows) {
  const groups = installationReportData(rows);
  const [{ jsPDF }, { default: autoTable }] = await Promise.all([import('jspdf'), import('jspdf-autotable')]);
  const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
  doc.setProperties({ title: 'Relación de instalaciones', subject: 'Cotas aportadas y confirmadas del proyecto', author: '' });
  groups.forEach((group, index) => {
    if (index) doc.addPage();
    doc.setFontSize(18); doc.text(`Instalaciones / ${group.title}`, 14, 18);
    doc.setFontSize(9);
    doc.text('Alturas desde suelo terminado al eje de cada toma. Distancias horizontales desde la referencia indicada.', 14, 27);
    doc.text('Relación de cotas aportadas: contrastar con la obra y las fichas de los equipos. No es un plano de ejecución.', 14, 33);
    autoTable(doc, {
      startY: 40,
      head: [['Punto o equipo', 'Pared receptora', 'Origen y sentido horizontal', 'Altura al eje', 'Distancia al eje']],
      body: group.body,
      margin: { top: 20, right: 14, bottom: 18, left: 14 },
      styles: { fontSize: 9, cellPadding: 3, overflow: 'linebreak' },
      headStyles: { fillColor: [32, 61, 56] },
      columnStyles: { 0: { cellWidth: 61 }, 1: { cellWidth: 49 }, 2: { cellWidth: 91 }, 3: { cellWidth: 34 }, 4: { cellWidth: 34 } },
      showHead: 'everyPage',
      rowPageBreak: 'avoid',
    });
  });
  const pages = doc.getNumberOfPages();
  for (let page = 1; page <= pages; page++) {
    doc.setPage(page); doc.setFontSize(8);
    doc.text(`Relación de instalaciones | ${page} / ${pages}`, 14, 201);
  }
  doc.save('informe-instalaciones.pdf');
}
