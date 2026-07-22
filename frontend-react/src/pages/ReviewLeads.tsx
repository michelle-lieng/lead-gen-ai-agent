import { Box, Grid, Typography } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useMutation } from '@tanstack/react-query';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { fetchMergedResultsZip } from '../api/mergedResults';
import { LoadingButton } from '../components/common/LoadingButton';
import { useNotify } from '../components/common/Notifications';
import { PageHeader } from '../components/common/PageHeader';
import { StatCard } from '../components/common/StatCard';
import { useProject } from '../hooks/useProjects';
import { useMergedResults } from '../hooks/useMergedResults';
import { triggerDownload } from '../utils/download';

const HIDDEN_COLUMNS = new Set(['id', 'project_id']);

export function ReviewLeads() {
  const { projectId } = useParams();
  const id = Number(projectId);
  const { notify, notifyError } = useNotify();
  const { data: project } = useProject(id);
  const { data: results, isLoading } = useMergedResults(id);

  const columns: GridColDef[] = useMemo(() => {
    if (!results) return [];
    return results.columns
      .filter((col) => !HIDDEN_COLUMNS.has(col))
      .map((col) => ({
        field: col,
        headerName: col,
        flex: col === 'lead' ? 1.5 : 1,
        minWidth: col === 'lead' ? 200 : 120,
        valueGetter: (_value, row) => {
          const v = row[col];
          if (typeof v === 'boolean') return v ? 'True' : 'False';
          return v ?? '';
        },
      }));
  }, [results]);

  // Some rows (dataset-derived / enriched) may lack an `id`, so assign a stable
  // synthetic row id from the index for the grid.
  const rows = useMemo(
    () => (results?.data ?? []).map((row, index) => ({ __rowId: index, ...row })),
    [results],
  );

  const stats = useMemo(() => {
    const data = results?.data ?? [];
    const enrichmentCols = (results?.columns ?? []).filter(
      (c) => !['id', 'project_id', 'lead', 'serp_count'].includes(c),
    );
    const serpLeads = data.filter((r) => Number(r.serp_count) > 0).length;
    return {
      total: results?.count ?? data.length,
      serpLeads,
      datasetLeads: data.length - serpLeads,
      enrichmentCols: enrichmentCols.length,
    };
  }, [results]);

  const downloadMutation = useMutation({
    mutationFn: () => fetchMergedResultsZip(id),
    onSuccess: (file) => {
      if (!file) {
        notify('No merged results to download yet.', 'info');
        return;
      }
      triggerDownload(file);
      notify(`Download ready: ${file.filename}`, 'success');
    },
    onError: notifyError,
  });

  const hasData = (results?.data?.length ?? 0) > 0;

  return (
    <Box>
      <PageHeader
        title={`Review Leads${project ? ` — ${project.project_name}` : ''}`}
        actions={
          <LoadingButton
            variant="contained"
            startIcon={<DownloadIcon />}
            loading={downloadMutation.isPending}
            disabled={!hasData}
            onClick={() => downloadMutation.mutate()}
          >
            Download CSV (ZIP)
          </LoadingButton>
        }
      />

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} md={3}>
          <StatCard label="Total Leads" value={stats.total} />
        </Grid>
        <Grid item xs={6} md={3}>
          <StatCard label="Unique SERP Leads" value={stats.serpLeads} />
        </Grid>
        <Grid item xs={6} md={3}>
          <StatCard label="Unique Dataset Leads" value={stats.datasetLeads} />
        </Grid>
        <Grid item xs={6} md={3}>
          <StatCard label="Enrichment Columns" value={stats.enrichmentCols} />
        </Grid>
      </Grid>

      {!isLoading && !hasData ? (
        <Typography color="text.secondary">
          No merged leads available yet. Collect leads or upload a dataset first.
        </Typography>
      ) : (
        <Box sx={{ width: '100%' }}>
          <DataGrid
            autoHeight
            loading={isLoading}
            rows={rows}
            columns={columns}
            getRowId={(row) => row.__rowId as number}
            pageSizeOptions={[10, 25, 50, 100]}
            initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
            disableRowSelectionOnClick
          />
        </Box>
      )}
    </Box>
  );
}
