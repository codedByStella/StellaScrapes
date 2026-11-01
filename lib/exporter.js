'use strict';
/**
 * CSV / XLSX export for search results — the browser-facing equivalent of
 * router.py's export_csv() (CSV) and clean_permits.py's export_excel()
 * (styled Excel). Both take the same `records` + `columns` shape route()
 * and OUTPUT_COLUMNS_BY_TYPE already produce, so there's no reshaping
 * needed between "what the search API returned" and "what gets exported."
 */

const ExcelJS = require('exceljs');

const CSV_HEADER_LABELS = {
  date: 'Date', address: 'Address', city: 'City', record_type: 'Type',
  description: 'Description', contractor: 'Contractor', name: 'Name',
  status: 'Status', url: 'URL',
};

function safeSpreadsheetText(value) {
  const s = value === null || value === undefined ? '' : String(value);
  // Prefix formula-like text so spreadsheet applications treat it as data.
  return /^[\s\u0000-\u001f]*[=+\-@]/.test(s) ? `'${s}` : s;
}

function csvEscape(value) {
  const s = safeSpreadsheetText(value);
  if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

/** Build a CSV string from records, using only the given columns (in order). */
function toCsv(records, columns) {
  const header = columns.map(c => csvEscape(CSV_HEADER_LABELS[c] || c)).join(',');
  const rows = records.map(r => columns.map(c => csvEscape(r[c])).join(','));
  return [header, ...rows].join('\r\n') + '\r\n';
}

/** Build an .xlsx Buffer from records, using only the given columns (in order). */
async function toXlsxBuffer(records, columns, { sheetName = 'Results', title = '' } = {}) {
  const wb = new ExcelJS.Workbook();
  const ws = wb.addWorksheet(sheetName);

  let headerRowIndex = 1;
  if (title) {
    ws.mergeCells(1, 1, 1, columns.length);
    const titleCell = ws.getCell(1, 1);
    titleCell.value = title;
    titleCell.font = { bold: true, size: 13, color: { argb: 'FFFFFFFF' } };
    titleCell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF1C2B36' } };
    titleCell.alignment = { horizontal: 'center', vertical: 'middle' };
    ws.getRow(1).height = 26;
    headerRowIndex = 2;
  }

  const headerRow = ws.getRow(headerRowIndex);
  columns.forEach((c, i) => {
    const cell = headerRow.getCell(i + 1);
    cell.value = CSV_HEADER_LABELS[c] || c;
    cell.font = { bold: true, color: { argb: 'FFFFFFFF' } };
    cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF00A878' } };
  });
  headerRow.commit();
  ws.views = [{ state: 'frozen', ySplit: headerRowIndex }];

  for (const r of records) {
    ws.addRow(columns.map(c => safeSpreadsheetText(r[c] ?? '')));
  }

  // Auto-width, capped so one long description doesn't blow out the sheet.
  columns.forEach((c, i) => {
    const col = ws.getColumn(i + 1);
    let maxLen = (CSV_HEADER_LABELS[c] || c).length;
    for (const r of records) {
      const len = String(r[c] ?? '').length;
      if (len > maxLen) maxLen = len;
    }
    col.width = Math.min(maxLen + 2, 60);
  });

  return wb.xlsx.writeBuffer();
}

module.exports = { toCsv, toXlsxBuffer, CSV_HEADER_LABELS, safeSpreadsheetText };
