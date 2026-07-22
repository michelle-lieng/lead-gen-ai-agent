import { Alert, Box, Button, Stack, Typography } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import SaveIcon from '@mui/icons-material/Save';
import {
  DataGrid,
  GridActionsCellItem,
  GridColDef,
  GridRowId,
} from '@mui/x-data-grid';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { createUrl, deleteUrl, getUrls, updateUrl } from '../../api/leadsSerp';
import { LoadingButton } from '../../components/common/LoadingButton';
import { useNotify } from '../../components/common/Notifications';
import { queryKeys } from '../../hooks/queryKeys';

interface EditableUrlRow {
  id: number; // real id (>0) or a temp negative id for new rows
  isNew: boolean;
  query: string;
  link: string;
  title: string;
  snippet: string;
  date: string;
}

const norm = (v: unknown) => String(v ?? '').trim();

export function UrlsEditor({ projectId }: { projectId: number }) {
  const queryClient = useQueryClient();
  const { notify, notifyError } = useNotify();
  const { data: urls, isLoading } = useQuery({
    queryKey: queryKeys.urls(projectId),
    queryFn: () => getUrls(projectId),
  });

  const [rows, setRows] = useState<EditableUrlRow[]>([]);
  const [deletedIds, setDeletedIds] = useState<number[]>([]);
  const [tempIdSeq, setTempIdSeq] = useState(-1);
  const [saving, setSaving] = useState(false);

  // Snapshot of the original rows keyed by id, for diffing on save.
  const original = useMemo(() => {
    const map = new Map<number, EditableUrlRow>();
    (urls ?? []).forEach((u) =>
      map.set(u.id, {
        id: u.id,
        isNew: false,
        query: u.query ?? '',
        link: u.link ?? '',
        title: u.title ?? '',
        snippet: u.snippet ?? '',
        date: u.date ?? '',
      }),
    );
    return map;
  }, [urls]);

  useEffect(() => {
    setRows(Array.from(original.values()));
    setDeletedIds([]);
  }, [original]);

  const addRow = () => {
    setRows((prev) => [
      { id: tempIdSeq, isNew: true, query: 'Manual Entry', link: '', title: '', snippet: '', date: '' },
      ...prev,
    ]);
    setTempIdSeq((s) => s - 1);
  };

  const removeRow = (id: GridRowId) => {
    const numId = Number(id);
    setRows((prev) => prev.filter((r) => r.id !== numId));
    if (numId > 0) setDeletedIds((prev) => [...prev, numId]);
  };

  const hasChanges = useMemo(() => {
    if (deletedIds.length > 0) return true;
    return rows.some((row) => {
      if (row.isNew) return norm(row.link) !== '';
      const orig = original.get(row.id);
      if (!orig) return false;
      return (
        norm(row.link) !== norm(orig.link) ||
        norm(row.title) !== norm(orig.title) ||
        norm(row.snippet) !== norm(orig.snippet) ||
        norm(row.date) !== norm(orig.date)
      );
    });
  }, [rows, original, deletedIds]);

  const handleSave = async () => {
    setSaving(true);
    let created = 0;
    let updated = 0;
    let deleted = 0;
    try {
      // Deletions
      for (const id of deletedIds) {
        await deleteUrl(projectId, id);
        deleted += 1;
      }
      // Creations + updates
      for (const row of rows) {
        if (row.isNew) {
          if (norm(row.link) === '') continue; // URL required
          await createUrl(projectId, {
            link: norm(row.link),
            title: norm(row.title),
            snippet: norm(row.snippet),
            date: norm(row.date),
          });
          created += 1;
        } else {
          const orig = original.get(row.id);
          if (!orig) continue;
          const changed =
            norm(row.link) !== norm(orig.link) ||
            norm(row.title) !== norm(orig.title) ||
            norm(row.snippet) !== norm(orig.snippet) ||
            norm(row.date) !== norm(orig.date);
          if (!changed) continue;
          if (norm(row.link) === '') {
            notify('URL cannot be empty. Fix the highlighted row.', 'warning');
            continue;
          }
          await updateUrl(projectId, row.id, {
            link: norm(row.link),
            title: norm(row.title),
            snippet: norm(row.snippet),
            date: norm(row.date),
          });
          updated += 1;
        }
      }
      notify(`Saved. Created ${created} · Updated ${updated} · Deleted ${deleted}.`, 'success');
      await queryClient.invalidateQueries({ queryKey: queryKeys.urls(projectId) });
    } catch (err) {
      notifyError(err);
    } finally {
      setSaving(false);
    }
  };

  const columns: GridColDef[] = [
    { field: 'query', headerName: 'Query', width: 140, editable: false },
    { field: 'link', headerName: 'URL', flex: 1.5, minWidth: 220, editable: true },
    { field: 'title', headerName: 'Title', flex: 1, minWidth: 160, editable: true },
    { field: 'snippet', headerName: 'Snippet', flex: 2, minWidth: 220, editable: true },
    { field: 'date', headerName: 'Date', width: 120, editable: true },
    {
      field: 'actions',
      type: 'actions',
      width: 70,
      getActions: (params) => [
        <GridActionsCellItem
          key="delete"
          icon={<DeleteIcon />}
          label="Delete"
          onClick={() => removeRow(params.id)}
        />,
      ],
    },
  ];

  return (
    <Box>
      <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
        <Button size="small" startIcon={<AddIcon />} onClick={addRow}>
          Add URL
        </Button>
        <LoadingButton
          size="small"
          variant="contained"
          startIcon={<SaveIcon />}
          loading={saving}
          disabled={!hasChanges}
          onClick={handleSave}
        >
          Save Table
        </LoadingButton>
      </Stack>

      {!isLoading && rows.length === 0 && (
        <Typography color="text.secondary" sx={{ mb: 1 }}>
          No URLs yet. Generate URLs from your queries above, or add one manually.
        </Typography>
      )}

      <DataGrid
        autoHeight
        loading={isLoading}
        rows={rows}
        columns={columns}
        getRowId={(row) => row.id}
        processRowUpdate={(newRow: EditableUrlRow) => {
          setRows((prev) => prev.map((r) => (r.id === newRow.id ? newRow : r)));
          return newRow;
        }}
        onProcessRowUpdateError={() => undefined}
        pageSizeOptions={[10, 25, 50]}
        initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
        disableRowSelectionOnClick
      />
      {hasChanges && (
        <Alert severity="info" sx={{ mt: 1 }}>
          You have unsaved changes. Click "Save Table" to persist them.
        </Alert>
      )}
    </Box>
  );
}
