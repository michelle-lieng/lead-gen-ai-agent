/**
 * Fields: what each column of the table holds, and how it is set.
 *
 * The backend returns a flat list of column names. Each AI field arrives as
 * three of them — the answer, its reasoning, and its evidence — and only the
 * answer earns a column; the other two belong to the expanded record, which is
 * where the working is read. A field's *type* is derived from the enrichment
 * that defined it, falling back to what the values actually look like, so an
 * imported column still declares itself correctly.
 */

import { Enrichment } from '../../api/types';
import { IconName } from '../ui/Icon';

export type GridRow = Record<string, unknown>;

export type FieldType = 'text' | 'longtext' | 'number' | 'select';

export interface GridField {
  /** The key this field reads from a row. */
  key: string;
  name: string;
  /** The real database column, shown in the field menu. */
  identifier?: string;
  type: FieldType;
  icon: IconName;
  width: number;
  align: 'left' | 'right';
  editable: boolean;
  /** Written by the agent rather than collected or imported. */
  ai: boolean;
  enrichment?: Enrichment;
  /** The reasoning and evidence keys, when the field has them. */
  noteKeys?: [string, string];
}

/** Keys the table never shows: primary keys and bookkeeping. */
const HIDDEN = new Set(['id', 'project_id']);

/** Collected rather than entered, so never typed into. */
const READ_ONLY = new Set(['serp_count']);

const WIDTH: Record<FieldType, number> = {
  text: 184,
  longtext: 208,
  number: 96,
  select: 148,
};

const ICON: Record<FieldType, IconName> = {
  text: 'field-text',
  longtext: 'field-longtext',
  number: 'field-number',
  select: 'field-select',
};

export type Verdict = 'yes' | 'no';

/**
 * Read a stored value as a yes/no answer. Enrichment columns are TEXT, so a
 * boolean arrives as "True"/"true"/"t"/"yes" depending on how it was written;
 * anything else is not a boolean at all.
 */
export function readVerdict(value: unknown): Verdict | null {
  if (value === true) return 'yes';
  if (value === false) return 'no';
  if (typeof value !== 'string') return null;
  const normalised = value.trim().toLowerCase();
  if (['true', 't', 'yes', 'y'].includes(normalised)) return 'yes';
  if (['false', 'f', 'no', 'n'].includes(normalised)) return 'no';
  return null;
}

export function isBlank(value: unknown): boolean {
  return value === null || value === undefined || value === '';
}

/** Longer answers get a taller field type, which changes how the cell wraps. */
function looksLong(values: unknown[]): boolean {
  return values.some((value) => typeof value === 'string' && value.length > 64);
}

function looksNumeric(values: unknown[]): boolean {
  return (
    values.length > 0 &&
    values.every((value) => typeof value === 'number' || /^-?[\d.,]+$/.test(String(value)))
  );
}

export function buildFields(columns: string[], rows: GridRow[], enrichments: Enrichment[]): GridField[] {
  const byColumnName = new Map(
    enrichments.filter((e) => e.column_name).map((e) => [e.column_name as string, e]),
  );
  const present = new Set(columns);

  const visible = columns.filter((key) => {
    if (HIDDEN.has(key)) return false;
    // Fold reasoning/evidence into the answer they belong to.
    const base = key.replace(/_(reasoning|evidence)$/, '');
    return base === key || !present.has(base);
  });

  return visible.map<GridField>((key) => {
    if (key === 'lead') {
      return {
        key,
        name: 'Company',
        type: 'text',
        icon: ICON.text,
        width: 248,
        align: 'left',
        editable: true,
        ai: false,
      };
    }

    if (key === 'serp_count') {
      return {
        key,
        name: 'Sources',
        identifier: key,
        type: 'number',
        icon: ICON.number,
        width: WIDTH.number,
        align: 'right',
        editable: false,
        ai: false,
      };
    }

    const enrichment = byColumnName.get(key);
    const noteKeys: [string, string] | undefined =
      present.has(`${key}_reasoning`) || present.has(`${key}_evidence`)
        ? [`${key}_reasoning`, `${key}_evidence`]
        : undefined;

    const values = rows.map((row) => row[key]).filter((value) => !isBlank(value));

    let type: FieldType;
    if (enrichment?.result_format === 'True/False') {
      type = 'select';
    } else if (enrichment?.result_format === 'Number') {
      type = 'number';
    } else if (enrichment?.result_format === 'Text') {
      type = looksLong(values) ? 'longtext' : 'text';
    } else if (values.length > 0 && values.every((value) => readVerdict(value) !== null)) {
      type = 'select';
    } else if (looksNumeric(values)) {
      type = 'number';
    } else {
      type = looksLong(values) ? 'longtext' : 'text';
    }

    return {
      key,
      name: enrichment?.enrichment_name ?? humanise(key),
      identifier: key,
      type,
      // An AI field carries its own mark, as the category does, rather than the
      // type glyph — what matters about it is that an agent wrote it.
      icon: enrichment ? 'sparkle' : ICON[type],
      width: WIDTH[type],
      align: type === 'number' ? 'right' : 'left',
      editable: !READ_ONLY.has(key),
      ai: Boolean(enrichment),
      enrichment,
      noteKeys,
    };
  });
}

/** A column name the agent never named: "annual_revenue" → "Annual revenue". */
function humanise(key: string): string {
  const words = key.replace(/_/g, ' ').trim();
  return words.charAt(0).toUpperCase() + words.slice(1);
}

export const FIELD_TYPE_LABEL: Record<FieldType, string> = {
  text: 'Single line text',
  longtext: 'Long text',
  number: 'Number',
  select: 'Single select',
};

/** The reasoning and evidence an AI field recorded for one record. */
export interface FieldNote {
  name: string;
  reasoning: string;
  evidence: string;
}

export function collectNotes(row: GridRow, fields: GridField[]): FieldNote[] {
  const notes: FieldNote[] = [];
  for (const field of fields) {
    if (!field.noteKeys) continue;
    const reasoning = String(row[field.noteKeys[0]] ?? '').trim();
    const evidence = String(row[field.noteKeys[1]] ?? '').trim();
    if (reasoning || evidence) notes.push({ name: field.name, reasoning, evidence });
  }
  return notes;
}

export function hasNotes(row: GridRow, fields: GridField[]): boolean {
  return fields.some((field) => {
    if (!field.noteKeys) return false;
    return Boolean(
      String(row[field.noteKeys[0]] ?? '').trim() || String(row[field.noteKeys[1]] ?? '').trim(),
    );
  });
}
