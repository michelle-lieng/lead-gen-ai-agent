/**
 * One record, expanded.
 *
 * This is where an AI field's working is read in full: the answer, then the
 * reasoning and the evidence the agent recorded against it. The grid carries
 * those two as their own columns, but a cell one line tall can only ever show
 * the start of a paragraph; here they are set out under the answer they
 * explain, which is what makes a researched answer checkable rather than
 * something to take on trust. They are read here as part of their answer, so
 * they are not repeated as fields of their own.
 *
 * Fields stay editable, as they are in the grid, through the same write path.
 */

import { useEffect, useState } from 'react';
import { GridField, GridRow, isBlank } from './fields';
import { SelectChip } from './CellValue';
import { splitLinks } from './rowStatus';
import { Icon } from '../ui/Icon';
import { Modal } from '../ui/Modal';
import { Button, IconButton } from '../ui/Primitives';

export function ExpandedRecord({
  lead,
  rows,
  fields,
  busy,
  onClose,
  onEdit,
  onDelete,
  onNavigate,
}: {
  /** The record being read, addressed by company name; null closes. */
  lead: string | null;
  rows: GridRow[];
  fields: GridField[];
  busy: boolean;
  onClose: () => void;
  onEdit: (lead: string, key: string, value: string) => void;
  onDelete: (lead: string) => void;
  onNavigate: (lead: string) => void;
}) {
  const index = rows.findIndex((row) => String(row.lead ?? '') === lead);
  const row = index >= 0 ? rows[index] : null;

  if (lead === null || !row) return null;

  return (
    <Modal
      open
      label={`Record: ${lead}`}
      onClose={onClose}
      width={720}
      head={
        <div className="rec__head">
          <span className="rec__nav">
            <IconButton
              icon="chevron-left"
              label="Previous record"
              compact
              disabled={index <= 0}
              onClick={() => onNavigate(String(rows[index - 1]?.lead ?? ''))}
            />
            <IconButton
              icon="chevron-right"
              label="Next record"
              compact
              disabled={index >= rows.length - 1}
              onClick={() => onNavigate(String(rows[index + 1]?.lead ?? ''))}
            />
          </span>
          <h2 className="rec__title">{lead}</h2>
          <span className="rec__count">
            {index + 1} of {rows.length}
          </span>
          <IconButton icon="close" label="Close record" compact onClick={onClose} />
        </div>
      }
      footer={
        <>
          <Button tone="danger" icon="trash" onClick={() => onDelete(lead)}>
            Delete record
          </Button>
          <div style={{ flex: 1 }} />
          <Button onClick={onClose}>Done</Button>
        </>
      }
    >
      <div className="rec__fields">
        {fields
          .filter((field) => !field.note)
          .map((field) => (
            <RecordField
              key={field.key}
              field={field}
              row={row}
              lead={lead}
              busy={busy}
              onEdit={onEdit}
            />
          ))}
      </div>
    </Modal>
  );
}

function RecordField({
  field,
  row,
  lead,
  busy,
  onEdit,
}: {
  field: GridField;
  row: GridRow;
  lead: string;
  busy: boolean;
  onEdit: (lead: string, key: string, value: string) => void;
}) {
  const value = row[field.key];
  const stored = isBlank(value) ? '' : String(value);
  const [draft, setDraft] = useState(stored);

  // Follow the stored value when the record refetches or the user moves record.
  useEffect(() => setDraft(stored), [stored, lead, field.key]);

  const reasoning = field.noteKeys ? String(row[field.noteKeys[0]] ?? '').trim() : '';
  const evidence = field.noteKeys ? String(row[field.noteKeys[1]] ?? '').trim() : '';

  const commit = () => {
    if (draft !== stored) onEdit(lead, field.key, draft);
  };

  return (
    <div className="rec__field">
      <span className="rec__label">
        <span className="head__icon" data-ai={field.ai || undefined}>
          <Icon name={field.icon} size={13} />
        </span>
        <span title={field.name}>{field.name}</span>
      </span>

      <div className="rec__value">
        {!field.editable ? (
          <p className="rec__ro" style={{ fontVariantNumeric: 'tabular-nums' }}>
            {stored || <span className="cell__empty">—</span>}
          </p>
        ) : field.type === 'select' ? (
          // A select value is a chip, not a text box: typing "Ys" into a boolean
          // column is not an edit anyone means to make.
          <p className="rec__ro">
            {stored ? <SelectChip value={value} /> : <span className="cell__empty">Not established</span>}
          </p>
        ) : field.type === 'longtext' ? (
          <textarea
            className="input"
            rows={Math.min(8, Math.max(2, Math.ceil(draft.length / 78)))}
            value={draft}
            disabled={busy}
            aria-label={field.name}
            onChange={(event) => setDraft(event.target.value)}
            onBlur={commit}
          />
        ) : (
          <input
            className="input"
            value={draft}
            disabled={busy}
            aria-label={field.name}
            style={field.type === 'number' ? { fontVariantNumeric: 'tabular-nums' } : undefined}
            onChange={(event) => setDraft(event.target.value)}
            onBlur={commit}
            onKeyDown={(event) => {
              if (event.key === 'Enter') event.currentTarget.blur();
            }}
          />
        )}

        {(reasoning || evidence) && (
          <dl className="rec__working">
            {reasoning && (
              <>
                <dt>How the agent answered</dt>
                <dd>{reasoning}</dd>
              </>
            )}
            {evidence && (
              <>
                <dt>Evidence</dt>
                <dd>
                  {splitLinks(String(evidence)).map((run, index) =>
                    run.href ? (
                      <a key={index} href={run.href} target="_blank" rel="noopener noreferrer">
                        {run.text}
                      </a>
                    ) : (
                      <span key={index}>{run.text}</span>
                    ),
                  )}
                </dd>
              </>
            )}
          </dl>
        )}
      </div>
    </div>
  );
}
