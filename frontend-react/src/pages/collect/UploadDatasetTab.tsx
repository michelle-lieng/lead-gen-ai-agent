import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  FormControl,
  FormControlLabel,
  InputLabel,
  ListItemText,
  MenuItem,
  OutlinedInput,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { uploadDataset } from '../../api/leadsDataset';
import { LoadingButton } from '../../components/common/LoadingButton';
import { useNotify } from '../../components/common/Notifications';
import { queryKeys } from '../../hooks/queryKeys';
import { parseSpreadsheet, ParsedSpreadsheet } from '../../utils/spreadsheet';

const ACCEPTED = '.csv,.xlsx,.xls';

export function UploadDatasetTab({ projectId }: { projectId: number }) {
  const queryClient = useQueryClient();
  const { notify, notifyError } = useNotify();

  const [file, setFile] = useState<File | null>(null);
  const [parsed, setParsed] = useState<ParsedSpreadsheet | null>(null);
  const [datasetName, setDatasetName] = useState('');
  const [leadColumn, setLeadColumn] = useState('');
  const [addEnrichment, setAddEnrichment] = useState(false);
  const [enrichmentColumns, setEnrichmentColumns] = useState<string[]>([]);

  const handleFile = async (selected: File | null) => {
    setFile(selected);
    setParsed(null);
    setLeadColumn('');
    setAddEnrichment(false);
    setEnrichmentColumns([]);
    if (!selected) return;
    setDatasetName(selected.name.replace(/\.[^.]+$/, ''));
    try {
      const result = await parseSpreadsheet(selected);
      setParsed(result);
      if (result.columns.length > 0) setLeadColumn(result.columns[0]);
    } catch (err) {
      notifyError(err);
    }
  };

  const nonLeadColumns = (parsed?.columns ?? []).filter((c) => c !== leadColumn);

  const uploadMutation = useMutation({
    mutationFn: () =>
      uploadDataset({
        projectId,
        datasetName: datasetName.trim(),
        leadColumn,
        enrichmentColumnList: addEnrichment ? enrichmentColumns : [],
        enrichmentColumnExists: addEnrichment,
        file: file as File,
      }),
    onSuccess: (result) => {
      if (result.success) {
        notify(result.message || 'Dataset uploaded.', 'success');
        queryClient.invalidateQueries({ queryKey: queryKeys.mergedResults(projectId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.project(projectId) });
      } else {
        notify(String(result.detail ?? result.message ?? 'Upload failed.'), 'error');
      }
    },
    onError: notifyError,
  });

  const canUpload =
    file &&
    datasetName.trim() &&
    leadColumn &&
    (!addEnrichment || enrichmentColumns.length > 0);

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Upload Existing Dataset
      </Typography>

      <Button variant="outlined" component="label" startIcon={<UploadFileIcon />}>
        Choose CSV or Excel file
        <input
          hidden
          type="file"
          accept={ACCEPTED}
          onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
        />
      </Button>
      {file && (
        <Typography variant="body2" sx={{ mt: 1 }} color="text.secondary">
          Selected: {file.name}
        </Typography>
      )}

      {parsed && (
        <>
          {parsed.sheetNames.length > 1 && (
            <Alert severity="info" sx={{ mt: 2 }}>
              {parsed.sheetNames.length} sheets detected. All sheets are merged on upload;
              the preview and column list below come from the first sheet.
            </Alert>
          )}

          <Typography variant="subtitle1" sx={{ mt: 2 }}>
            Data Preview ({parsed.rowCount} rows in first sheet)
          </Typography>
          <TableContainer sx={{ maxHeight: 320, mt: 1, border: '1px solid #e0e0e0' }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  {parsed.columns.map((col) => (
                    <TableCell key={col}>{col}</TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {parsed.preview.map((row, i) => (
                  <TableRow key={i}>
                    {parsed.columns.map((col) => (
                      <TableCell key={col}>{String(row[col] ?? '')}</TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="h6" sx={{ mt: 3 }} gutterBottom>
            Dataset Configuration
          </Typography>
          <Stack spacing={2} sx={{ maxWidth: 640 }}>
            <TextField
              label="Dataset Name"
              value={datasetName}
              onChange={(e) => setDatasetName(e.target.value)}
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>Lead Column</InputLabel>
              <Select
                label="Lead Column"
                value={leadColumn}
                onChange={(e) => {
                  setLeadColumn(e.target.value);
                  setEnrichmentColumns([]);
                }}
              >
                {parsed.columns.map((col) => (
                  <MenuItem key={col} value={col}>
                    {col}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControlLabel
              control={
                <Checkbox
                  checked={addEnrichment}
                  disabled={nonLeadColumns.length === 0}
                  onChange={(e) => setAddEnrichment(e.target.checked)}
                />
              }
              label="Add enrichment columns from dataset"
            />

            {addEnrichment ? (
              <FormControl fullWidth>
                <InputLabel>Enrichment Columns</InputLabel>
                <Select
                  multiple
                  label="Enrichment Columns"
                  value={enrichmentColumns}
                  onChange={(e) =>
                    setEnrichmentColumns(
                      typeof e.target.value === 'string'
                        ? e.target.value.split(',')
                        : e.target.value,
                    )
                  }
                  input={<OutlinedInput label="Enrichment Columns" />}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={value} size="small" />
                      ))}
                    </Box>
                  )}
                >
                  {nonLeadColumns.map((col) => (
                    <MenuItem key={col} value={col}>
                      <Checkbox checked={enrichmentColumns.includes(col)} />
                      <ListItemText primary={col} />
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            ) : (
              <Alert severity="info">
                A single column <strong>{datasetName || 'dataset'}_exists</strong> (all TRUE)
                will be created for these leads.
              </Alert>
            )}

            <Box>
              <LoadingButton
                variant="contained"
                startIcon={<UploadFileIcon />}
                loading={uploadMutation.isPending}
                disabled={!canUpload}
                onClick={() => uploadMutation.mutate()}
              >
                Upload Dataset
              </LoadingButton>
            </Box>
          </Stack>
        </>
      )}
    </Box>
  );
}
