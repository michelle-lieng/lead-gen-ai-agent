import { DownloadedFile } from '../api/types';

/** Trigger a browser download for a blob + filename. */
export function triggerDownload(file: DownloadedFile): void {
  const url = URL.createObjectURL(file.blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = file.filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

/** Format an ISO date string as "YYYY-MM-DD HH:MM:SS" (falls back to the raw value). */
export function formatDateTime(value?: string | null): string {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const pad = (n: number) => String(n).padStart(2, '0');
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ` +
    `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
  );
}

/** Just the date portion (YYYY-MM-DD). */
export function formatDate(value?: string | null): string {
  if (!value) return '';
  return value.slice(0, 10);
}
