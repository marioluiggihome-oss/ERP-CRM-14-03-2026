/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
// Simple PDF export utility
export const exportToPdf = (elementId, filename) => {
  // For now, just use browser's print dialog
  // In production, this would use jsPDF or similar library
  window.print();
};
