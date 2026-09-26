/**
 * How a value is set inside a cell.
 *
 * A yes/no answer is a select chip carrying its own word, so nothing depends on
 * decoding a colour. A blank is an en-rule in quiet ink rather than an empty
 * cell, because "not established" and "not asked" have to look different from
 * each other. Numbers are tabular and right-aligned; nothing else is.
 */

import { GridField, isBlank, readVerdict } from './fields';
import { Spinner } from '../ui/Primitives';

export function SelectChip({ value }: { value: unknown }) {
  const verdict = readVerdict(value);
  if (!verdict) {
    return <span className="chip">{String(value)}</span>;
  }
  return (
    <span className="chip" data-value={verdict}>
      {verdict === 'yes' ? 'Yes' : 'No'}
    </span>
  );
}

export function CellValue({
  field,
  value,
  settling,
  working,
}: {
  field: GridField;
  value: unknown;
  /** The answer just landed, so it fades in. */
  settling?: boolean;
  /** The run is working this record's row and has not answered yet. */
  working?: boolean;
}) {
  if (isBlank(value)) {
    // A field being filled right now says so, rather than showing a blank that
    // looks like a finished empty answer.
    if (working && field.ai) {
      return (
        <span className="cell__spinner" title="Researching this record">
          <Spinner size={11} />
        </span>
      );
    }
    return (
      <span className="cell__value cell__empty" aria-label="Empty">
        —
      </span>
    );
  }

  const className = [
    'cell__value',
    field.key === 'lead' ? 'cell__value--lead' : '',
    field.type === 'number' ? 'cell__value--num' : '',
    settling ? 'settle' : '',
  ]
    .filter(Boolean)
    .join(' ');

  if (field.type === 'select') {
    return (
      <span className={className}>
        <SelectChip value={value} />
      </span>
    );
  }

  return <span className={className}>{String(value)}</span>;
}
