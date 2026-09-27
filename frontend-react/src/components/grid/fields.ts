/**
 * Fields: what each column of the table holds, and how it is set.
 *
 * The backend returns a flat list of column names. Each AI field arrives as
 * three of them — the answer, its reasoning, and its evidence — and all three
 * earn a column, the working sitting immediately to the right of the answer it
 * explains rather than only in the expanded record. A field's *type* is derived
 * from the enrichment that defined it, falling back to what the values actually
 * look like, so an imported column still declares itself correctly.
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
  /** Set on the agent's working columns, which stand beside their answer. */
  note?: NoteKind;
  /** For a working column, the key of the answer it explains. */
  parentKey?: string;
}

export type NoteKind = 'reasoning' | 'evidence';

const NOTE_KINDS: NoteKind[] = ['reasoning', 'evidence'];

const NOTE_SUFFIX = /_(reasoning|evidence)$/;

/** Keys the table never shows: primary keys and bookkeeping. */
const HIDDEN = new Set(['id', 'project_id']);

/** Collected rather than entered, so never typed into. */
const READ_ONLY = new Set(['serp_count']);

/* Wide enough that a real field name — "More than one doctor", "Sources" —
   reads in the column head without being cut to two syllables. */
const WIDTH: Record<FieldType, number> = {
  text: 184,
  longtext: 216,
  number: 112,
  select: 164,
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

  /* Answers keep the backend's order; each one pulls its own reasoning and
     evidence along behind it, so the working is always read beside the answer
     it explains however the columns arrived. A working column whose answer is
     missing is nobody's working, and stands as an ordinary column. */
  const ordered: string[] = [];
  const placed = new Set<string>();
  for (const key of columns) {
    if (HIDDEN.has(key) || placed.has(key)) continue;
    const parent = key.replace(NOTE_SUFFIX, '');
    if (parent !== key && present.has(parent) && !HIDDEN.has(parent)) continue;

    ordered.push(key);
    placed.add(key);
    for (const kind of NOTE_KINDS) {
      const noteKey = `${key}_${kind}`;
      if (present.has(noteKey) && !placed.has(noteKey)) {
        ordered.push(noteKey);
        placed.add(noteKey);
      }
    }
  }

  return ordered.map<GridField>((key) => {
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

    /* The agent's working: long prose or a list of sources, never typed into,
       and named after the answer it belongs to so it still says what it is
       once the answer has been scrolled off the left edge. */
    const noteMatch = NOTE_SUFFIX.exec(key);
    const parentKey = noteMatch ? key.slice(0, key.length - noteMatch[0].length) : null;
    if (parentKey && present.has(parentKey)) {
      const parent = byColumnName.get(parentKey);
      const kind = noteMatch![1] as NoteKind;
      return {
        key,
        name: `${parent?.enrichment_name ?? humanise(parentKey)} ${kind}`,
        identifier: key,
        type: 'longtext',
        // The type glyph, not the sparkle: the sparkle marks the answer, and
        // the working is told apart from it at a glance.
        icon: ICON.longtext,
        width: WIDTH.longtext,
        align: 'left',
        editable: false,
        ai: Boolean(parent),
        enrichment: parent,
        note: kind,
        parentKey,
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
