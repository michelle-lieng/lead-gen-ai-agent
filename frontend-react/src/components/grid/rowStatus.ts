/**
 * Filtering the lead table by its yes/no columns, and the sources behind an
 * answer.
 *
 * Each yes/no column can be switched on as a filter: switched on, only records
 * that say Yes to it stay in view. Several switched on means Yes to all of them.
 */

import { GridRow, readVerdict } from './fields';

/** True when the record says Yes to every yes/no column switched on. */
export function passesYesFilters(row: GridRow, activeKeys: string[]): boolean {
  return activeKeys.every((key) => readVerdict(row[key]) === 'yes');
}

/** How many records say Yes to one yes/no column. */
export function yesCount(rows: GridRow[], key: string): number {
  return rows.filter((row) => readVerdict(row[key]) === 'yes').length;
}

const URL_PATTERN = /https?:\/\/[^\s<>"')\]]+/g;
const TRAILING = /[.,;:]+$/;

/** Each URL in the text, trailing sentence punctuation removed. */
function urls(text: string): string[] {
  return (text.match(URL_PATTERN) ?? []).map((url) => url.replace(TRAILING, ''));
}

/** How many distinct sources an evidence value cites. */
export function countSources(evidence: unknown): number {
  if (typeof evidence !== 'string') return 0;
  return new Set(urls(evidence)).size;
}

/** The text in runs, URLs marked as links; the runs join back to the input. */
export function splitLinks(text: string): Array<{ text: string; href?: string }> {
  const runs: Array<{ text: string; href?: string }> = [];
  let at = 0;
  for (const match of text.matchAll(URL_PATTERN)) {
    const url = match[0].replace(TRAILING, '');
    const start = match.index ?? 0;
    if (start > at) runs.push({ text: text.slice(at, start) });
    runs.push({ text: url, href: url });
    at = start + url.length;
  }
  if (at < text.length) runs.push({ text: text.slice(at) });
  return runs;
}
