import * as XLSX from 'xlsx';

export interface ParsedSpreadsheet {
  columns: string[];
  /** First N rows as objects keyed by column name (for preview). */
  preview: Record<string, unknown>[];
  sheetNames: string[];
  rowCount: number;
}

/**
 * Parse a CSV/XLSX/XLS file in the browser to extract column names and a small
 * preview. Only the first sheet is inspected for the column list (the backend
 * handles multi-sheet merging on upload).
 */
export async function parseSpreadsheet(
  file: File,
  previewRows = 10,
): Promise<ParsedSpreadsheet> {
  const buffer = await file.arrayBuffer();
  const workbook = XLSX.read(buffer, { type: 'array' });
  const sheetNames = workbook.SheetNames;
  const firstSheet = workbook.Sheets[sheetNames[0]];

  const json = XLSX.utils.sheet_to_json<Record<string, unknown>>(firstSheet, {
    defval: '',
  });

  const columns =
    json.length > 0
      ? Object.keys(json[0]).map((c) => c.trim())
      : (XLSX.utils.sheet_to_json<string[]>(firstSheet, { header: 1 })[0] ?? []).map(
          (c) => String(c).trim(),
        );

  return {
    columns,
    preview: json.slice(0, previewRows),
    sheetNames,
    rowCount: json.length,
  };
}
