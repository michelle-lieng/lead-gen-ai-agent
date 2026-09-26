/**
 * One project: the grid, and the enquiry panel that fills it.
 *
 * Everything the product does happens on this screen. The page owns the writes
 * — cell edits, record deletion, field renaming, import and export — and hands
 * presentation to the grid and the panel.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { updateEnrichment } from '../api/enrichments';
import { deleteMergedRow, fetchMergedResultsZip, updateMergedRow } from '../api/mergedResults';
import { useApiKeysDialog } from '../components/apiKeys/ApiKeys';
import { DataGrid, ROW_HEIGHT_PX, RowHeight } from '../components/grid/DataGrid';
import { ExpandedRecord } from '../components/grid/ExpandedRecord';
import { GridField, buildFields } from '../components/grid/fields';
import { ImportSheet } from '../components/imports/ImportSheet';
import { EnquiryPanel, PanelTab } from '../components/panel/EnquiryPanel';
import { AppShell, ProjectMenuButton, SidebarToggle } from '../components/shell/AppShell';
import { Icon } from '../components/ui/Icon';
import { Confirm, Modal } from '../components/ui/Modal';
import { PopItem, PopLabel, Popover } from '../components/ui/Popover';
import { Button, EmptyState, Field, IconButton } from '../components/ui/Primitives';
import { useNotify } from '../components/ui/Toasts';
import { useEnrichments } from '../hooks/useEnrichments';
import { useMergedResults } from '../hooks/useMergedResults';
import { useProject } from '../hooks/useProjects';
import { useQueryHistory } from '../hooks/useQueries';
import { queryKeys } from '../hooks/queryKeys';
import { useRegisterRun } from '../hooks/useRegisterRun';
import { triggerDownload } from '../utils/download';

const ROW_HEIGHTS: { id: RowHeight; label: string }[] = [
  { id: 'short', label: 'Short' },
  { id: 'medium', label: 'Medium' },
  { id: 'tall', label: 'Tall' },
];

const ROW_HEIGHT_KEY = 'kiyu.grid.rowHeight';

export function Project() {
  const { projectId } = useParams();
  const id = Number(projectId);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { notify, notifyError } = useNotify();
  // The keys dialog itself is opened from the sidebar's account slot; this page
  // only needs the gate that blocks a run when they are missing.
  const { requireKeys } = useApiKeysDialog();

  const { data: project, isLoading: loadingProject, isError } = useProject(id);
  const { data: results, isLoading: loadingResults } = useMergedResults(id);
  const { data: enrichments } = useEnrichments(id);
  const { data: pastQueries } = useQueryHistory(id);

  const run = useRegisterRun(id);

  const [tab, setTab] = useState<PanelTab>('find');
  // Below 1181px the panel stops being a column and becomes an overlay, so
  // opening it by default there would hide the table the visitor came for.
  const [panelOpen, setPanelOpen] = useState(
    () => typeof window === 'undefined' || window.matchMedia('(min-width: 1181px)').matches,
  );
  const [focusToken, setFocusToken] = useState(0);
  const [filter, setFilter] = useState('');
  const [rowHeight, setRowHeight] = useState<RowHeight>(
    () => (localStorage.getItem(ROW_HEIGHT_KEY) as RowHeight | null) ?? 'short',
  );
  const [heightAnchor, setHeightAnchor] = useState<HTMLElement | null>(null);
  const [importing, setImporting] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [deletingOne, setDeletingOne] = useState<string | null>(null);
  const [deletingMany, setDeletingMany] = useState(false);
  const [renamingField, setRenamingField] = useState<GridField | null>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  // A run reports on the tab it belongs to, so follow it there and make sure
  // the panel it reports in is actually on screen.
  useEffect(() => {
    if (run.kind) {
      setTab(run.kind);
      setPanelOpen(true);
    }
  }, [run.kind]);

  // Warn before a reload would abandon a run mid-flight.
  useEffect(() => {
    if (!run.running) return undefined;
    const onBeforeUnload = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener('beforeunload', onBeforeUnload);
    return () => window.removeEventListener('beforeunload', onBeforeUnload);
  }, [run.running]);

  const rows = useMemo(() => results?.data ?? [], [results]);

  const fields = useMemo(
    () => buildFields(results?.columns ?? [], rows, enrichments ?? []),
    [results?.columns, rows, enrichments],
  );

  const visibleRows = useMemo(() => {
    const needle = filter.trim().toLowerCase();
    if (!needle) return rows;
    return rows.filter((row) =>
      Object.values(row).some(
        (value) => value !== null && String(value).toLowerCase().includes(needle),
      ),
    );
  }, [rows, filter]);

  // Selection is held by company name, so a renamed or deleted record drops out
  // of it on the next refetch rather than lingering as a phantom.
  const liveSelection = useMemo(() => {
    const present = new Set(rows.map((row) => String(row.lead ?? '')));
    return new Set([...selected].filter((lead) => present.has(lead)));
  }, [rows, selected]);

  // The answers only: a field's reasoning and evidence are the same field's
  // working, and counting them would treble the tally the footer reports.
  const aiFieldCount = fields.filter((field) => field.ai && !field.note).length;

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.mergedResults(id) });
    queryClient.invalidateQueries({ queryKey: queryKeys.project(id) });
  };

  const chooseRowHeight = (next: RowHeight) => {
    setRowHeight(next);
    localStorage.setItem(ROW_HEIGHT_KEY, next);
    setHeightAnchor(null);
  };

  const editMutation = useMutation({
    mutationFn: ({ lead, key, value }: { lead: string; key: string; value: string }) =>
      updateMergedRow(id, lead, { [key]: value }),
    onSuccess: invalidate,
    onError: (error) => {
      notifyError(error);
      invalidate();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (leads: string[]) =>
      Promise.allSettled(leads.map((lead) => deleteMergedRow(id, lead))).then((outcomes) => ({
        leads,
        failed: outcomes.filter((outcome) => outcome.status === 'rejected').length,
      })),
    onSuccess: ({ leads, failed }) => {
      const done = leads.length - failed;
      if (done > 0) {
        notify(
          leads.length === 1
            ? `“${leads[0]}” deleted.`
            : `${done} ${done === 1 ? 'record' : 'records'} deleted.`,
          'success',
        );
      }
      if (failed > 0) {
        notify(
          `${failed} ${failed === 1 ? 'record' : 'records'} could not be deleted.`,
          'error',
        );
      }
      setDeletingOne(null);
      setDeletingMany(false);
      setExpanded(null);
      setSelected(new Set());
      invalidate();
    },
    onError: (error) => {
      notifyError(error);
      setDeletingOne(null);
      setDeletingMany(false);
    },
  });

  const renameMutation = useMutation({
    mutationFn: ({ enrichmentId, name }: { enrichmentId: number; name: string }) =>
      updateEnrichment(enrichmentId, { enrichment_name: name }),
    onSuccess: () => {
      notify('Field renamed.', 'success');
      setRenamingField(null);
      queryClient.invalidateQueries({ queryKey: queryKeys.enrichments(id) });
    },
    onError: notifyError,
  });

  const exportMutation = useMutation({
    mutationFn: () => fetchMergedResultsZip(id),
    onSuccess: (file) => {
      if (!file) {
        notify('Nothing to export yet.', 'info');
        return;
      }
      triggerDownload(file);
      notify(`Exported ${file.filename}.`, 'success');
    },
    onError: notifyError,
  });

  /* ------------------------------------------------------------ early states */

  if (loadingProject) {
    return (
      <AppShell activeId={id}>
        <main className="main main--plain">
          <div className="projectbar">
            <SidebarToggle />
            <span className="projectbar__title">
              <h1>Opening…</h1>
            </span>
          </div>
          <p className="quiet">Loading this project…</p>
        </main>
      </AppShell>
    );
  }

  if (isError || !project) {
    return (
      <AppShell activeId={id}>
        <main className="main main--plain">
          <div className="projectbar">
            <SidebarToggle />
            <span className="projectbar__title">
              <h1>Project not found</h1>
            </span>
          </div>
          <EmptyState
            icon="alert"
            title="This project is not here"
            body="It may have been deleted, or the link may be wrong."
            actions={
              <Button tone="primary" onClick={() => navigate('/')}>
                Back to home
              </Button>
            }
          />
        </main>
      </AppShell>
    );
  }

  /* ------------------------------------------------------------------ actions */

  const submit = (instruction: string) => {
    if (!requireKeys()) return;
    if (tab === 'find') {
      run.findLeads(instruction);
    } else {
      run.enrichRegister(
        instruction,
        rows.map((row) => String(row.lead ?? '')).filter(Boolean),
      );
    }
  };

  const askForField = () => {
    setPanelOpen(true);
    setTab('enrich');
    setFocusToken((token) => token + 1);
  };

  const selectionCount = liveSelection.size;

  return (
    <AppShell
      activeId={id}
      onClosePanel={() => setPanelOpen(false)}
      panel={
        panelOpen ? (
          <EnquiryPanel
            tab={tab}
            onTabChange={setTab}
            kind={run.kind}
            running={run.running}
            steps={run.steps}
            log={run.log}
            startedAt={run.startedAt}
            instruction={run.instruction}
            recordCount={rows.length}
            enrichments={enrichments ?? []}
            pastQueries={pastQueries ?? []}
            onSubmit={submit}
            onStop={run.stop}
            onClear={run.clear}
            onClose={() => setPanelOpen(false)}
            focusToken={focusToken}
          />
        ) : undefined
      }
    >
      <main className="main">
        <div className="projectbar">
          <SidebarToggle />
          <span className="projectbar__title">
            <h1 title={project.project_name}>{project.project_name}</h1>
            <ProjectMenuButton project={project} />
          </span>
          <span className="projectbar__spacer" />
        </div>

        <div className="toolbar">
          <button type="button" className="toolbar__tab" aria-current="page">
            <Icon name="field-select" size={13} />
            Leads
            <span>{rows.length.toLocaleString()}</span>
          </button>

          <span className="toolbar__rule" aria-hidden="true" />

          <label className="search">
            <Icon name="search" size={13} />
            <input
              ref={searchRef}
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
              placeholder="Search records"
              aria-label="Search records"
            />
            {filter && (
              <button
                type="button"
                onClick={() => {
                  setFilter('');
                  searchRef.current?.focus();
                }}
                aria-label="Clear search"
                style={{
                  display: 'flex',
                  border: 0,
                  background: 'none',
                  padding: 0,
                  cursor: 'pointer',
                  color: 'inherit',
                }}
              >
                <Icon name="close" size={11} />
              </button>
            )}
          </label>

          {filter && (
            <span className="toolbar__found">
              {visibleRows.length.toLocaleString()} of {rows.length.toLocaleString()}
            </span>
          )}

          <Button
            icon="rows"
            compact
            tone="quiet"
            aria-haspopup="menu"
            aria-expanded={heightAnchor !== null}
            onClick={(event) => setHeightAnchor(event.currentTarget)}
          >
            Row height
          </Button>

          <span className="toolbar__spacer" />

          <Button icon="import" compact tone="quiet" onClick={() => setImporting(true)}>
            Import
          </Button>
          <Button
            icon="download"
            compact
            tone="quiet"
            loading={exportMutation.isPending}
            disabled={rows.length === 0}
            onClick={() => exportMutation.mutate()}
          >
            Export
          </Button>

          <span className="toolbar__rule" aria-hidden="true" />

          {/* Labelled while the panel is hidden, because that is when the
              product's primary affordance has to be findable; icon-only while
              it is open, where the panel itself is the label and the view bar
              has 380px less room to give. */}
          {panelOpen ? (
            <IconButton
              icon="panel"
              label="Hide the agent panel"
              compact
              aria-pressed
              onClick={() => setPanelOpen(false)}
            />
          ) : (
            <Button
              icon="panel"
              compact
              tone="primary"
              aria-pressed={false}
              onClick={() => setPanelOpen(true)}
            >
              Ask the agent
            </Button>
          )}
        </div>

        {loadingResults && rows.length === 0 ? (
          <p className="quiet">Loading records…</p>
        ) : rows.length === 0 ? (
          <EmptyState
            fill
            icon="sparkle"
            title="This table is empty"
            body="Describe the companies you are looking for in the panel on the right. One sentence is enough — everything below happens on its own."
            actions={
              <>
                <Button tone="primary" icon="search" onClick={() => {
                  setPanelOpen(true);
                  setTab('find');
                  setFocusToken((token) => token + 1);
                }}>
                  Describe the leads you want
                </Button>
                <Button icon="import" onClick={() => setImporting(true)}>
                  Import a spreadsheet
                </Button>
              </>
            }
            sequence={[
              {
                head: 'You describe the companies',
                body: '“Dental clinics in Sydney”, or whatever you are actually looking for.',
              },
              {
                head: 'Search queries are written and run',
                body: 'Several angles on your description, searched and collected as sources.',
              },
              {
                head: 'Every source is read',
                body: 'Company names are extracted into this table, with how many sources each was found in.',
              },
              {
                head: 'You ask for a field',
                body: 'Switch to Enrich leads and ask one question. Every record is researched and the answers are written in.',
              },
            ]}
          />
        ) : visibleRows.length === 0 ? (
          <EmptyState
            icon="search"
            title="No records match that"
            body={`Nothing in this table contains “${filter}”.`}
            actions={<Button onClick={() => setFilter('')}>Clear search</Button>}
          />
        ) : (
          <DataGrid
            fields={fields}
            rows={visibleRows}
            rowHeight={rowHeight}
            settling={run.settling}
            workingLeads={run.workingLeads}
            workingField={run.workingField}
            busy={editMutation.isPending || deleteMutation.isPending}
            selected={liveSelection}
            onSelect={(lead, isSelected) =>
              setSelected((current) => {
                const next = new Set(current);
                if (isSelected) next.add(lead);
                else next.delete(lead);
                return next;
              })
            }
            onSelectAll={(isSelected) =>
              setSelected(
                isSelected
                  ? new Set(visibleRows.map((row) => String(row.lead ?? '')))
                  : new Set(),
              )
            }
            onEdit={(lead, key, value) => editMutation.mutate({ lead, key, value })}
            onExpand={setExpanded}
            onRenameField={setRenamingField}
            onAddField={askForField}
          />
        )}

        <div className="foot">
          {selectionCount > 0 ? (
            <span className="foot__sel">
              {selectionCount} {selectionCount === 1 ? 'record' : 'records'} selected
              <Button
                tone="danger"
                compact
                icon="trash"
                onClick={() => setDeletingMany(true)}
              >
                Delete
              </Button>
              <Button tone="quiet" compact onClick={() => setSelected(new Set())}>
                Clear
              </Button>
            </span>
          ) : (
            <span>
              {rows.length.toLocaleString()} {rows.length === 1 ? 'record' : 'records'}
              {filter && ` · ${visibleRows.length.toLocaleString()} shown`}
            </span>
          )}

          <span className="foot__spacer" />

          {/* The tallies are why the table is believable, so they survive onto a
              phone — abbreviated to hold one line, never dropped. */}
          <span className="foot__meta">
            {aiFieldCount} researched {aiFieldCount === 1 ? 'field' : 'fields'}
            {project.datasets_added > 0 &&
              ` · ${project.datasets_added} imported ${
                project.datasets_added === 1 ? 'dataset' : 'datasets'
              }`}
            {project.urls_processed > 0 &&
              ` · ${project.urls_processed.toLocaleString()} sources read`}
          </span>

          <span className="foot__meta--short">
            {aiFieldCount} {aiFieldCount === 1 ? 'field' : 'fields'}
            {project.urls_processed > 0 &&
              ` · ${project.urls_processed.toLocaleString()} sources`}
          </span>
        </div>
      </main>

      {heightAnchor && (
        <Popover
          anchor={heightAnchor}
          label="Row height"
          onClose={() => setHeightAnchor(null)}
          width={180}
        >
          <PopLabel>Row height</PopLabel>
          {ROW_HEIGHTS.map((option) => (
            <PopItem
              key={option.id}
              checked={rowHeight === option.id}
              onClick={() => chooseRowHeight(option.id)}
            >
              {option.label} · {ROW_HEIGHT_PX[option.id]}px
            </PopItem>
          ))}
        </Popover>
      )}

      <ExpandedRecord
        lead={expanded}
        rows={visibleRows}
        fields={fields}
        busy={editMutation.isPending}
        onClose={() => setExpanded(null)}
        onEdit={(lead, key, value) => editMutation.mutate({ lead, key, value })}
        onDelete={(lead) => setDeletingOne(lead)}
        onNavigate={setExpanded}
      />

      <ImportSheet open={importing} projectId={id} onClose={() => setImporting(false)} />

      <RenameFieldDialog
        field={renamingField}
        loading={renameMutation.isPending}
        onClose={() => setRenamingField(null)}
        onSave={(name) => {
          const enrichmentId = renamingField?.enrichment?.id;
          if (enrichmentId) renameMutation.mutate({ enrichmentId, name });
        }}
      />

      <Confirm
        open={deletingOne !== null}
        title="Delete this record?"
        message={`“${deletingOne}” will be removed from this table along with every answer recorded against it.`}
        confirmLabel="Delete record"
        destructive
        loading={deleteMutation.isPending}
        onConfirm={() => deletingOne && deleteMutation.mutate([deletingOne])}
        onCancel={() => setDeletingOne(null)}
      />

      <Confirm
        open={deletingMany}
        title={`Delete ${selectionCount} ${selectionCount === 1 ? 'record' : 'records'}?`}
        message="They will be removed from this table along with every answer recorded against them. This cannot be undone."
        confirmLabel={`Delete ${selectionCount} ${selectionCount === 1 ? 'record' : 'records'}`}
        destructive
        loading={deleteMutation.isPending}
        onConfirm={() => deleteMutation.mutate([...liveSelection])}
        onCancel={() => setDeletingMany(false)}
      />
    </AppShell>
  );
}

/* --------------------------------------------------------------- field rename */

function RenameFieldDialog({
  field,
  loading,
  onClose,
  onSave,
}: {
  field: GridField | null;
  loading: boolean;
  onClose: () => void;
  onSave: (name: string) => void;
}) {
  const [name, setName] = useState('');

  useEffect(() => {
    if (field) setName(field.name);
  }, [field]);

  return (
    <Modal
      open={field !== null}
      title="Rename field"
      note="Only the label changes. The underlying column keeps its name, so exports and anything built on them are unaffected."
      onClose={onClose}
      width={460}
      footer={
        <>
          <Button onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            tone="primary"
            icon="check"
            loading={loading}
            disabled={!name.trim() || name.trim() === field?.name}
            onClick={() => onSave(name.trim())}
          >
            Save
          </Button>
        </>
      }
    >
      <div style={{ display: 'grid', gap: 14 }}>
        <Field
          label="Field name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && name.trim()) onSave(name.trim());
          }}
        />
        {field?.identifier && (
          <p style={{ fontSize: 12, color: 'var(--text-2)' }}>
            Column:{' '}
            <code style={{ fontFamily: 'var(--face-mono)', fontSize: 11.5 }}>
              {field.identifier}
            </code>
          </p>
        )}
      </div>
    </Modal>
  );
}
