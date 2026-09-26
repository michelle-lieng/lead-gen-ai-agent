/**
 * The grid.
 *
 * Ruled both ways, 32px rows, the row-number gutter and the company field
 * frozen to the left, and a `+` closing the header row. Cells behave the way a
 * grid database's cells behave: click selects, arrow keys move, Enter or a
 * double-click edits, typing replaces, Escape cancels, Delete clears. That
 * keyboard model is most of the difference between a table of styled divs and
 * something a category-fluent user can trust on sight.
 *
 * Presentation only: every write is handed back to the caller, which owns the
 * mutations.
 */

import {
  KeyboardEvent as ReactKeyboardEvent,
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { GridField, GridRow, hasNotes } from './fields';
import { CellValue } from './CellValue';
import { FieldMenu } from './FieldMenu';
import { Icon } from '../ui/Icon';

export type RowHeight = 'short' | 'medium' | 'tall';

export const ROW_HEIGHT_PX: Record<RowHeight, number> = { short: 32, medium: 56, tall: 88 };

interface DataGridProps {
  fields: GridField[];
  rows: GridRow[];
  rowHeight: RowHeight;
  /** Records whose answers just landed, so their values fade in. */
  settling?: Set<string>;
  /** Records the run is working now. */
  workingLeads?: Set<string>;
  /** A write is in flight; editing is held off until it lands. */
  busy?: boolean;
  selected: Set<string>;
  onSelect: (lead: string, selected: boolean) => void;
  onSelectAll: (selected: boolean) => void;
  onEdit: (lead: string, key: string, value: string) => void;
  onExpand: (lead: string) => void;
  onRenameField: (field: GridField) => void;
  onAddField: () => void;
}

export function DataGrid({
  fields,
  rows,
  rowHeight,
  settling,
  workingLeads,
  busy = false,
  selected,
  onSelect,
  onSelectAll,
  onEdit,
  onExpand,
  onRenameField,
  onAddField,
}: DataGridProps) {
  const scrollerRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<HTMLTextAreaElement>(null);

  const [cursor, setCursor] = useState<{ r: number; c: number } | null>(null);
  const [editing, setEditing] = useState<{ r: number; c: number } | null>(null);
  const [draft, setDraft] = useState('');
  const [scrolled, setScrolled] = useState(false);
  const [fieldMenu, setFieldMenu] = useState<{ field: GridField; anchor: HTMLElement } | null>(
    null,
  );

  const totalWidth = useMemo(
    () => fields.reduce((sum, field) => sum + field.width, 0) + 66 + 44,
    [fields],
  );

  const frozenWidth = 66 + (fields[0]?.width ?? 0) + 16;

  /* ------------------------------------------------------------ scroll state */

  useEffect(() => {
    const scroller = scrollerRef.current;
    if (!scroller) return undefined;
    const measure = () => setScrolled(scroller.scrollLeft > 0);
    measure();
    scroller.addEventListener('scroll', measure, { passive: true });
    return () => scroller.removeEventListener('scroll', measure);
  }, []);

  /* --------------------------------------------------------------- the cursor */

  // Keep focus on the selected cell so the arrow keys keep working, and let the
  // browser scroll it into view rather than computing offsets by hand.
  useLayoutEffect(() => {
    if (!cursor || editing) return;
    const node = scrollerRef.current?.querySelector<HTMLElement>(
      `[data-r="${cursor.r}"][data-c="${cursor.c}"]`,
    );
    node?.focus({ preventScroll: false });
  }, [cursor, editing]);

  useLayoutEffect(() => {
    if (!editing) return;
    const editor = editorRef.current;
    if (!editor) return;
    editor.focus();
    editor.setSelectionRange(editor.value.length, editor.value.length);
    editor.style.height = 'auto';
    editor.style.height = `${Math.max(editor.scrollHeight, ROW_HEIGHT_PX[rowHeight])}px`;
  }, [editing, rowHeight]);

  // A cursor left pointing past the end of a shrunken table is not a cursor.
  useEffect(() => {
    setCursor((current) => {
      if (!current) return current;
      if (current.r < rows.length && current.c < fields.length) return current;
      return null;
    });
  }, [rows.length, fields.length]);

  const startEdit = useCallback(
    (r: number, c: number, initial?: string) => {
      const field = fields[c];
      const row = rows[r];
      if (!field || !row || !field.editable || busy) return;
      const current = row[field.key];
      setCursor({ r, c });
      setDraft(initial ?? (current === null || current === undefined ? '' : String(current)));
      setEditing({ r, c });
    },
    [fields, rows, busy],
  );

  const commit = useCallback(() => {
    if (!editing) return;
    const field = fields[editing.c];
    const row = rows[editing.r];
    setEditing(null);
    if (!field || !row) return;
    const before = row[field.key];
    const was = before === null || before === undefined ? '' : String(before);
    if (was !== draft) onEdit(String(row.lead ?? ''), field.key, draft);
  }, [editing, fields, rows, draft, onEdit]);

  const move = useCallback(
    (dr: number, dc: number) => {
      setCursor((current) => {
        const from = current ?? { r: 0, c: 0 };
        return {
          r: Math.min(Math.max(0, from.r + dr), rows.length - 1),
          c: Math.min(Math.max(0, from.c + dc), fields.length - 1),
        };
      });
    },
    [rows.length, fields.length],
  );

  const onGridKeyDown = (event: ReactKeyboardEvent<HTMLDivElement>) => {
    if (editing) return;
    if (event.altKey || event.ctrlKey || event.metaKey) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'c' && cursor) {
        const value = rows[cursor.r]?.[fields[cursor.c].key];
        navigator.clipboard?.writeText(value === null || value === undefined ? '' : String(value));
      }
      return;
    }

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        move(1, 0);
        return;
      case 'ArrowUp':
        event.preventDefault();
        move(-1, 0);
        return;
      case 'ArrowRight':
        event.preventDefault();
        move(0, 1);
        return;
      case 'ArrowLeft':
        event.preventDefault();
        move(0, -1);
        return;
      case 'Home':
        event.preventDefault();
        setCursor((current) => ({ r: current?.r ?? 0, c: 0 }));
        return;
      case 'End':
        event.preventDefault();
        setCursor((current) => ({ r: current?.r ?? 0, c: fields.length - 1 }));
        return;
      case 'Enter':
        if (!cursor) return;
        event.preventDefault();
        startEdit(cursor.r, cursor.c);
        return;
      case 'Escape':
        setCursor(null);
        return;
      case 'Backspace':
      case 'Delete': {
        if (!cursor) return;
        const field = fields[cursor.c];
        const row = rows[cursor.r];
        if (!field.editable || busy) return;
        event.preventDefault();
        if (row[field.key] !== null && row[field.key] !== undefined && row[field.key] !== '') {
          onEdit(String(row.lead ?? ''), field.key, '');
        }
        return;
      }
      default:
        break;
    }

    // Type to replace, the way a grid does.
    if (cursor && event.key.length === 1 && !event.repeat) {
      event.preventDefault();
      startEdit(cursor.r, cursor.c, event.key);
    }
  };

  const onEditorKeyDown = (event: ReactKeyboardEvent<HTMLTextAreaElement>) => {
    event.stopPropagation();
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      commit();
      move(1, 0);
    } else if (event.key === 'Escape') {
      event.preventDefault();
      setEditing(null);
    }
  };

  const allSelected = rows.length > 0 && rows.every((row) => selected.has(String(row.lead ?? '')));

  return (
    <div
      className="grid"
      ref={scrollerRef}
      data-scrolled={scrolled || undefined}
      data-rowheight={rowHeight}
      data-anyselected={selected.size > 0 || undefined}
      style={
        {
          '--row-h': `${ROW_HEIGHT_PX[rowHeight]}px`,
          '--frozen-w': `${frozenWidth}px`,
        } as React.CSSProperties
      }
      onKeyDown={onGridKeyDown}
    >
      <div
        className="grid__inner"
        role="grid"
        aria-label="Records"
        aria-rowcount={rows.length + 1}
        aria-colcount={fields.length + 1}
        style={{ minWidth: totalWidth }}
      >
        {/* ---------------------------------------------------- column heads */}
        <div className="grid__head" role="row" aria-rowindex={1}>
          <div
            className="cell cell--gutter cell--sticky"
            role="columnheader"
            aria-colindex={1}
          >
            <span className="gut__check" style={{ display: 'grid' }}>
              <input
                type="checkbox"
                className="gut__box"
                checked={allSelected}
                aria-label={allSelected ? 'Clear selection' : 'Select all records'}
                onChange={(event) => onSelectAll(event.target.checked)}
              />
            </span>
          </div>

          {fields.map((field, index) => (
            <div
              key={field.key}
              className={[
                'cell',
                index === 0 ? 'cell--sticky cell--first cell--frozen-edge' : '',
              ]
                .filter(Boolean)
                .join(' ')}
              role="columnheader"
              aria-colindex={index + 2}
              style={{ '--cw': `${field.width}px` } as React.CSSProperties}
            >
              <span className="head">
                <span className="head__icon" data-ai={field.ai || undefined}>
                  <Icon name={field.icon} size={13} />
                </span>
                <span className="head__name" title={field.name}>
                  {field.name}
                </span>
                <button
                  type="button"
                  className="head__menu"
                  aria-label={`${field.name} field options`}
                  aria-haspopup="menu"
                  aria-expanded={fieldMenu?.field.key === field.key}
                  onClick={(event) => setFieldMenu({ field, anchor: event.currentTarget })}
                >
                  <Icon name="chevron-down" size={12} />
                </button>
              </span>
            </div>
          ))}

          <div className="cell cell--add" role="columnheader" aria-colindex={fields.length + 2}>
            <button
              type="button"
              className="head__add"
              onClick={onAddField}
              title="Add a field by asking a question"
              aria-label="Add a field by asking a question"
            >
              <Icon name="plus" size={14} />
            </button>
          </div>

          <div className="cell cell--pad" role="presentation" />
        </div>

        {/* --------------------------------------------------------- records */}
        <div role="rowgroup">
          {rows.map((row, r) => {
            const lead = String(row.lead ?? '');
            const isWorking = workingLeads?.has(lead) ?? false;
            const isSettling = settling?.has(lead) ?? false;
            const isChecked = selected.has(lead);

            return (
              <div
                key={lead || r}
                className="grid__row"
                role="row"
                aria-rowindex={r + 2}
                aria-selected={isChecked || undefined}
                data-working={isWorking || undefined}
                data-selected={isChecked || undefined}
              >
                <div
                  className="cell cell--gutter cell--sticky"
                  role="gridcell"
                  aria-colindex={1}
                >
                  <span className="gut__no" aria-hidden="true">
                    {r + 1}
                  </span>
                  <span className="gut__check">
                    <input
                      type="checkbox"
                      className="gut__box"
                      checked={isChecked}
                      aria-label={`Select ${lead}`}
                      onChange={(event) => onSelect(lead, event.target.checked)}
                    />
                  </span>
                  <button
                    type="button"
                    className="gut__expand"
                    onClick={() => onExpand(lead)}
                    aria-label={`Expand ${lead}`}
                    title={
                      hasNotes(row, fields)
                        ? 'Expand record — including the agent’s working'
                        : 'Expand record'
                    }
                  >
                    <Icon name="expand" size={11} />
                  </button>
                </div>

                {fields.map((field, c) => {
                  const isCursor = cursor?.r === r && cursor.c === c;
                  const isEditing = editing?.r === r && editing.c === c;
                  const value = row[field.key];

                  return (
                    <div
                      key={field.key}
                      className={[
                        'cell',
                        'cell--data',
                        c === 0 ? 'cell--sticky cell--first cell--frozen-edge' : '',
                        isCursor && !isEditing ? 'cell--selected' : '',
                        isEditing ? 'cell--editing' : '',
                      ]
                        .filter(Boolean)
                        .join(' ')}
                      role="gridcell"
                      aria-colindex={c + 2}
                      aria-readonly={!field.editable || undefined}
                      tabIndex={isCursor ? 0 : -1}
                      data-r={r}
                      data-c={c}
                      style={
                        {
                          '--cw': `${field.width}px`,
                          justifyContent: field.align === 'right' ? 'flex-end' : 'flex-start',
                          cursor: field.editable && !busy ? 'cell' : 'default',
                        } as React.CSSProperties
                      }
                      onMouseDown={() => {
                        if (!isEditing) setCursor({ r, c });
                      }}
                      onDoubleClick={() => startEdit(r, c)}
                    >
                      {isEditing ? (
                        <textarea
                          ref={editorRef}
                          className="cell__editor"
                          value={draft}
                          rows={1}
                          spellCheck={false}
                          style={{ textAlign: field.align }}
                          aria-label={`${field.name} for ${lead}`}
                          onChange={(event) => {
                            setDraft(event.target.value);
                            const node = event.currentTarget;
                            node.style.height = 'auto';
                            node.style.height = `${Math.max(
                              node.scrollHeight,
                              ROW_HEIGHT_PX[rowHeight],
                            )}px`;
                          }}
                          onBlur={commit}
                          onKeyDown={onEditorKeyDown}
                        />
                      ) : (
                        <CellValue
                          field={field}
                          value={value}
                          settling={isSettling}
                          working={isWorking}
                        />
                      )}
                    </div>
                  );
                })}

                <div className="cell cell--addpad" role="presentation" />
                <div className="cell cell--pad" role="presentation" />
              </div>
            );
          })}
        </div>
      </div>

      {fieldMenu && (
        <FieldMenu
          field={fieldMenu.field}
          anchor={fieldMenu.anchor}
          onClose={() => setFieldMenu(null)}
          onRename={(field) => {
            setFieldMenu(null);
            onRenameField(field);
          }}
        />
      )}
    </div>
  );
}
