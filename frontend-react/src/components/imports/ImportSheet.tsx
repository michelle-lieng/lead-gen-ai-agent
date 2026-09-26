/**
 * Importing a spreadsheet of leads.
 *
 * A toolbar action rather than something you ask the agent for: the panel is for
 * describing what you want researched, and a file needs its columns mapped
 * before its rows can become records.
 */

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { uploadDataset } from '../../api/leadsDataset';
import { queryKeys } from '../../hooks/queryKeys';
import { ParsedSpreadsheet, parseSpreadsheet } from '../../utils/spreadsheet';
import { Modal } from '../ui/Modal';
import { Button, Field } from '../ui/Primitives';
import { Icon } from '../ui/Icon';
import { useNotify } from '../ui/Toasts';

const ACCEPTED = '.csv,.xlsx,.xls';

export function ImportSheet({
  open,
  projectId,
  onClose,
}: {
  open: boolean;
  projectId: number;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const { notify, notifyError } = useNotify();

  const [file, setFile] = useState<File | null>(null);
  const [parsed, setParsed] = useState<ParsedSpreadsheet | null>(null);
  const [parsing, setParsing] = useState(false);
  const [name, setName] = useState('');
  const [leadColumn, setLeadColumn] = useState('');
  const [extraColumns, setExtraColumns] = useState<string[]>([]);

  const reset = () => {
    setFile(null);
    setParsed(null);
    setName('');
    setLeadColumn('');
    setExtraColumns([]);
  };

  const close = () => {
    reset();
    onClose();
  };

  const handleFile = async (selected: File | null) => {
    reset();
    if (!selected) return;
    setFile(selected);
    setName(selected.name.replace(/\.[^.]+$/, ''));
    setParsing(true);
    try {
      const result = await parseSpreadsheet(selected);
      setParsed(result);
      // Guess the lead column: the first one whose name mentions a company.
      const guess =
        result.columns.find((column) =>
          /company|business|name|organisation|organization|clinic|practice/i.test(column),
        ) ?? result.columns[0];
      setLeadColumn(guess ?? '');
    } catch (error) {
      notifyError(error);
      setFile(null);
    } finally {
      setParsing(false);
    }
  };

  const otherColumns = (parsed?.columns ?? []).filter((column) => column !== leadColumn);

  const upload = useMutation({
    mutationFn: () =>
      uploadDataset({
        projectId,
        datasetName: name.trim(),
        leadColumn,
        enrichmentColumnList: extraColumns,
        enrichmentColumnExists: extraColumns.length > 0,
        file: file as File,
      }),
    onSuccess: (result) => {
      if (result.success) {
        notify(
          result.message ?? `Imported ${result.rows_processed ?? 0} rows into this table.`,
          'success',
        );
        queryClient.invalidateQueries({ queryKey: queryKeys.mergedResults(projectId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.project(projectId) });
        close();
      } else {
        notify(String(result.detail ?? result.message ?? 'Import failed.'), 'error');
      }
    },
    onError: notifyError,
  });

  const ready = Boolean(file && name.trim() && leadColumn);

  return (
    <Modal
      open={open}
      title="Import a spreadsheet"
      note="Rows are matched to this table by company name, so an import can also fill in fields for companies you already have."
      onClose={close}
      width={660}
      footer={
        <>
          <Button onClick={close} disabled={upload.isPending}>
            Cancel
          </Button>
          <Button
            tone="primary"
            icon="import"
            loading={upload.isPending}
            disabled={!ready}
            onClick={() => upload.mutate()}
          >
            Import
          </Button>
        </>
      }
    >
      <div style={{ display: 'grid', gap: 18 }}>
        <div>
          <span className="field-label">File</span>
          <div className="file-drop">
            <label className="btn" data-tone="plain">
              <Icon name="import" size={14} />
              <span>{file ? 'Choose a different file' : 'Choose a CSV or Excel file'}</span>
              <input
                hidden
                type="file"
                accept={ACCEPTED}
                onChange={(event) => handleFile(event.target.files?.[0] ?? null)}
              />
            </label>
            {file && (
              <span className="file-note">
                {file.name}
                {parsed ? ` · ${parsed.rowCount.toLocaleString()} rows` : ''}
              </span>
            )}
            {parsing && <span className="file-note">Reading the file…</span>}
          </div>
        </div>

        {parsed && (
          <>
            {parsed.sheetNames.length > 1 && (
              <p className="note-line">
                {parsed.sheetNames.length} sheets found. All are merged on import; the
                columns below come from the first.
              </p>
            )}

            <Field
              label="Dataset name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              hint="Used to prefix any extra fields this file adds."
            />

            <div>
              <span className="field-label">Which column holds the company name?</span>
              <div className="picks">
                {parsed.columns.map((column) => (
                  <button
                    key={column}
                    type="button"
                    className="pick"
                    data-active={leadColumn === column}
                    aria-pressed={leadColumn === column}
                    onClick={() => {
                      setLeadColumn(column);
                      setExtraColumns((current) => current.filter((c) => c !== column));
                    }}
                  >
                    {column}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <span className="field-label">Bring across any other columns (optional)</span>
              {otherColumns.length === 0 ? (
                <p className="file-note">This file has no other columns.</p>
              ) : (
                <div className="picks">
                  {otherColumns.map((column) => (
                    <button
                      key={column}
                      type="button"
                      className="pick"
                      data-active={extraColumns.includes(column)}
                      aria-pressed={extraColumns.includes(column)}
                      onClick={() =>
                        setExtraColumns((current) =>
                          current.includes(column)
                            ? current.filter((c) => c !== column)
                            : [...current, column],
                        )
                      }
                    >
                      {column}
                    </button>
                  ))}
                </div>
              )}
              <p className="note-line" style={{ marginTop: 10 }}>
                {extraColumns.length > 0
                  ? `${extraColumns.length} ${extraColumns.length === 1 ? 'field' : 'fields'} will be added, prefixed with “${name.trim() || 'dataset'}”.`
                  : `One field, ${name.trim() || 'dataset'}_exists, will mark every company from this file.`}
              </p>
            </div>

            <div>
              <span className="field-label">Preview</span>
              <div className="preview">
                <table>
                  <thead>
                    <tr>
                      {parsed.columns.map((column) => (
                        <th key={column} data-lead={column === leadColumn}>
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {parsed.preview.slice(0, 6).map((row, index) => (
                      <tr key={index}>
                        {parsed.columns.map((column) => (
                          <td key={column} data-lead={column === leadColumn}>
                            {String(row[column] ?? '')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
}
