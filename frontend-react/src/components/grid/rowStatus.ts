/**
 * How a record stands against the table's answer columns, and the sources
 * behind an answer.
 *
 * Every AI answer column counts towards a match, whatever its format: a yes/no
 * column must say yes, and any other column must hold an answer. Reasoning and
 * evidence columns are the working behind an answer, never a filter.
 */

import { GridField, GridRow, readVerdict } from './fields';

export type RowStatus = 'match' | 'unclear' | 'fails';

/** Keys of the AI answer columns, without their reasoning/evidence notes. */
export function answerKeys(fields: GridField[]): string[] {
  return fields.filter((field) => field.ai && !field.note).map((field) => field.key);
}

function blank(value: unknown): boolean {
  return value === null || value === undefined || (typeof value === 'string' && !value.trim());
}

/**
 * `fails` when any yes/no column says no; otherwise `unclear` when any answer
 * column is blank; otherwise `match`. A table with no answer columns matches.
 */
export function rowStatus(row: GridRow, keys: string[], yesNoKeys: Set<string>): RowStatus {
  if (keys.some((key) => yesNoKeys.has(key) && readVerdict(row[key]) === 'no')) return 'fails';
  if (keys.some((key) => blank(row[key]))) return 'unclear';
  return 'match';
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
