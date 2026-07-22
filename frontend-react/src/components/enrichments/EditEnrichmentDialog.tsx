import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
} from '@mui/material';
import { useMutation } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { updateEnrichment } from '../../api/enrichments';
import { Enrichment } from '../../api/types';
import { LoadingButton } from '../common/LoadingButton';
import { useNotify } from '../common/Notifications';

interface EditEnrichmentDialogProps {
  enrichment: Enrichment | null;
  onClose: () => void;
  onSaved: () => void;
}

/** Dialog for editing an enrichment's name, column name and notes. */
export function EditEnrichmentDialog({
  enrichment,
  onClose,
  onSaved,
}: EditEnrichmentDialogProps) {
  const { notify, notifyError } = useNotify();
  const [name, setName] = useState('');
  const [columnName, setColumnName] = useState('');
  const [description, setDescription] = useState('');

  useEffect(() => {
    if (enrichment) {
      setName(enrichment.enrichment_name);
      setColumnName(enrichment.column_name ?? '');
      setDescription(enrichment.enrichment_description ?? '');
    }
  }, [enrichment]);

  const mutation = useMutation({
    mutationFn: () =>
      updateEnrichment(enrichment!.id, {
        enrichment_name: name.trim(),
        column_name: columnName.trim(),
        enrichment_description: description.trim(),
      }),
    onSuccess: () => {
      notify('Enrichment updated.', 'success');
      onSaved();
    },
    onError: notifyError,
  });

  return (
    <Dialog open={enrichment !== null} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Edit Enrichment</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <TextField
            label="Enrichment Name"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            fullWidth
          />
          <TextField
            label="Column Name"
            value={columnName}
            onChange={(e) => setColumnName(e.target.value)}
            helperText="Lowercase letters, numbers and underscores (e.g. more_than_1_doctor)"
            fullWidth
          />
          <TextField
            label="Self Notes"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            fullWidth
            multiline
            minRows={3}
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <LoadingButton
          variant="contained"
          loading={mutation.isPending}
          disabled={!name.trim()}
          onClick={() => mutation.mutate()}
        >
          Save
        </LoadingButton>
      </DialogActions>
    </Dialog>
  );
}
