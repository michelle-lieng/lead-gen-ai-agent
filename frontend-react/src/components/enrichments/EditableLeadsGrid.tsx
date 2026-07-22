import { Box, Button } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import {
  DataGrid,
  GridActionsCellItem,
  GridColDef,
  GridRowsProp,
} from '@mui/x-data-grid';
import { useMemo } from 'react';

interface EditableLeadsGridProps {
  leads: string[];
  onChange: (leads: string[]) => void;
}

/** Editable list of test leads (add / edit inline / delete). */
export function EditableLeadsGrid({ leads, onChange }: EditableLeadsGridProps) {
  const rows: GridRowsProp = useMemo(
    () => leads.map((lead, index) => ({ id: index, lead })),
    [leads],
  );

  const updateAt = (index: number, value: string) => {
    const next = [...leads];
    next[index] = value;
    onChange(next);
  };

  const removeAt = (index: number) => {
    onChange(leads.filter((_, i) => i !== index));
  };

  const columns: GridColDef[] = [
    { field: 'lead', headerName: 'Lead', flex: 1, editable: true },
    {
      field: 'actions',
      type: 'actions',
      width: 80,
      getActions: (params) => [
        <GridActionsCellItem
          key="delete"
          icon={<DeleteIcon />}
          label="Delete"
          onClick={() => removeAt(params.id as number)}
        />,
      ],
    },
  ];

  return (
    <Box>
      <DataGrid
        autoHeight
        rows={rows}
        columns={columns}
        processRowUpdate={(newRow) => {
          updateAt(newRow.id as number, String(newRow.lead ?? ''));
          return newRow;
        }}
        onProcessRowUpdateError={() => undefined}
        hideFooter
        disableRowSelectionOnClick
      />
      <Button
        size="small"
        startIcon={<AddIcon />}
        sx={{ mt: 1 }}
        onClick={() => onChange([...leads, ''])}
      >
        Add lead
      </Button>
    </Box>
  );
}
