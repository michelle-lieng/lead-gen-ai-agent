import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useMemo } from 'react';
import { LeadRow } from '../../api/types';

const HIDDEN = new Set(['id', 'project_id', 'serp_count']);

interface EnrichedResultsGridProps {
  columns: string[];
  rows: LeadRow[];
  /** When provided, only these columns are shown (in this order). */
  onlyColumns?: string[];
}

/** Renders enriched-lead results, stringifying booleans to True/False. */
export function EnrichedResultsGrid({ columns, rows, onlyColumns }: EnrichedResultsGridProps) {
  const gridColumns: GridColDef[] = useMemo(() => {
    const cols = onlyColumns ?? columns.filter((c) => !HIDDEN.has(c));
    return cols.map((col) => ({
      field: col,
      headerName: col,
      flex: col === 'lead' ? 1.2 : 1,
      minWidth: 140,
      valueGetter: (_value, row) => {
        const v = row[col];
        if (typeof v === 'boolean') return v ? 'True' : 'False';
        return v ?? '';
      },
    }));
  }, [columns, onlyColumns]);

  const gridRows = useMemo(
    () => rows.map((row, index) => ({ __rowId: index, ...row })),
    [rows],
  );

  return (
    <DataGrid
      autoHeight
      rows={gridRows}
      columns={gridColumns}
      getRowId={(row) => row.__rowId as number}
      pageSizeOptions={[5, 10, 25]}
      initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
      disableRowSelectionOnClick
    />
  );
}
