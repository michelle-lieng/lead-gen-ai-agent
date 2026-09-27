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

/**
 * Parse a backend timestamp. The API serialises naive `datetime.utcnow()`
 * values, so a string with no zone marker is UTC and must be told so — read as
 * local time it would land hours out.
 */
function parseTimestamp(value: string): Date {
  const hasZone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(value);
  return new Date(hasZone ? value : `${value}Z`);
}

/**
 * "2 hours ago", for the recency lines on the home grid.
 *
 * Anything a week old prints its date instead — past that, a relative figure
 * stops being easier to read than the date itself. A negative interval (clock
 * skew between the browser and the server) is reported as "just now" rather
 * than as a time in the future.
 */
export function formatRelative(value?: string | null): string {
  if (!value) return '';
  const date = parseTimestamp(value);
  if (Number.isNaN(date.getTime())) return value;

  const seconds = Math.round((Date.now() - date.getTime()) / 1000);
  if (seconds < 90) return 'just now';

  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;

  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} ${hours === 1 ? 'hour' : 'hours'} ago`;

  const days = Math.round(hours / 24);
  if (days === 1) return 'yesterday';
  if (days < 7) return `${days} days ago`;

  return date.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
}
