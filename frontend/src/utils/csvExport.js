/**
 * Lightweight Browser-Side CSV Export Utility for Multi-NoSQL Business Analytics.
 * Generates and downloads standard RFC 4180 CSV files directly in the browser
 * without external dependencies.
 */

export function exportToCsv(filename, columns, data) {
  if (!Array.isArray(data) || data.length === 0) {
    alert('No data available to export.');
    return;
  }

  // Header row
  const headers = columns.map((col) => `"${(col.label || col.key).replace(/"/g, '""')}"`);
  const rows = [headers.join(',')];

  // Data rows
  data.forEach((item) => {
    const rowValues = columns.map((col) => {
      let val = item[col.key];
      if (val === undefined || val === null) {
        val = '';
      } else if (typeof val === 'number') {
        // Keep clean numeric value or formatted string
        val = String(val);
      } else {
        val = String(val);
      }
      return `"${val.replace(/"/g, '""')}"`;
    });
    rows.push(rowValues.join(','));
  });

  const csvString = rows.join('\r\n');
  const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', filename.endsWith('.csv') ? filename : `${filename}.csv`);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
