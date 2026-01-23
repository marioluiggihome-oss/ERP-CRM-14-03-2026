// Simple PDF export utility
export const exportToPdf = (elementId, filename) => {
  // For now, just use browser's print dialog
  // In production, this would use jsPDF or similar library
  window.print();
};
