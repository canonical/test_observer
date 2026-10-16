// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

// Serialises grid contents to CSV and hands the file to the browser. SvGrid's
// own exportCsv only covers columns declared with a `field`, and the dashboard
// grid derives every cell through a `fieldFn`, so it would export empty rows.

/** Excel reads a file as the local codepage unless a UTF-8 BOM leads it. */
const BOM = "\ufeff";

function escapeCell(value: string): string {
  // A leading =, +, - or @ makes a spreadsheet treat the text as a formula, so
  // prefix those with a tab, which Excel and Sheets strip back out on display.
  const text = /^[=+\-@]/.test(value) ? `\t${value}` : value;
  return /["\n\r,\t]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

/** Serialises a header row and body rows to CSV text (CRLF line endings). */
export function toCsv(headers: string[], rows: string[][]): string {
  return [headers, ...rows]
    .map((row) => row.map(escapeCell).join(","))
    .join("\r\n");
}

/** Prompts the browser to save `text` as `filename`. */
export function downloadCsv(filename: string, text: string): void {
  const blob = new Blob([BOM + text], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  // Safari needs the URL to outlive the click, so release it on the next tick.
  setTimeout(() => {
    URL.revokeObjectURL(url);
  }, 0);
}
