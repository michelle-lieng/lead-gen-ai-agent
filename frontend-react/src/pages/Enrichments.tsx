import {
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Grid,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import LaunchIcon from '@mui/icons-material/Launch';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { createEnrichment, deleteEnrichment } from '../api/enrichments';
import { Enrichment } from '../api/types';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { LoadingButton } from '../components/common/LoadingButton';
import { useNotify } from '../components/common/Notifications';
import { PageHeader } from '../components/common/PageHeader';
import { EditEnrichmentDialog } from '../components/enrichments/EditEnrichmentDialog';
import { useEnrichments } from '../hooks/useEnrichments';
import { useProject } from '../hooks/useProjects';
import { queryKeys } from '../hooks/queryKeys';
import { formatDate } from '../utils/download';

export function Enrichments() {
  const { projectId } = useParams();
  const id = Number(projectId);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { notify, notifyError } = useNotify();
  const { data: project } = useProject(id);
  const { data: enrichments, isLoading } = useEnrichments(id);

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [editing, setEditing] = useState<Enrichment | null>(null);
  const [deleting, setDeleting] = useState<Enrichment | null>(null);

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: queryKeys.enrichments(id) });

  const createMutation = useMutation({
    mutationFn: () => createEnrichment(id, name.trim(), description.trim() || null),
    onSuccess: (enrichment) => {
      notify(`Enrichment "${enrichment.enrichment_name}" created.`, 'success');
      setName('');
      setDescription('');
      invalidate();
    },
    onError: notifyError,
  });

  const deleteMutation = useMutation({
    mutationFn: (enrichmentId: number) => deleteEnrichment(enrichmentId),
    onSuccess: () => {
      notify('Enrichment deleted.', 'success');
      setDeleting(null);
      invalidate();
    },
    onError: notifyError,
  });

  return (
    <Box>
      <PageHeader title={`Enrichments${project ? ` — ${project.project_name}` : ''}`} />

      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Create New Enrichment
          </Typography>
          <Stack spacing={2}>
            <TextField
              label="Enrichment Name"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. More than 1 doctor"
              fullWidth
            />
            <TextField
              label="Self Notes (optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              fullWidth
              multiline
              minRows={2}
            />
            <Box>
              <LoadingButton
                variant="contained"
                startIcon={<AddIcon />}
                loading={createMutation.isPending}
                disabled={!name.trim()}
                onClick={() => createMutation.mutate()}
              >
                Create Enrichment
              </LoadingButton>
            </Box>
          </Stack>
        </CardContent>
      </Card>

      <Typography variant="h6" gutterBottom>
        Your Enrichments{enrichments ? ` (${enrichments.length})` : ''}
      </Typography>

      {isLoading && <Typography color="text.secondary">Loading...</Typography>}
      {!isLoading && (!enrichments || enrichments.length === 0) && (
        <Typography color="text.secondary">No enrichments yet.</Typography>
      )}

      <Grid container spacing={2}>
        {enrichments?.map((enrichment) => (
          <Grid item xs={12} md={6} key={enrichment.id}>
            <Card
              variant="outlined"
              sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}
            >
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography variant="h6">{enrichment.enrichment_name}</Typography>
                {enrichment.enrichment_description && (
                  <Typography variant="body2" color="text.secondary">
                    {enrichment.enrichment_description}
                  </Typography>
                )}
                {enrichment.column_name && (
                  <Typography variant="caption" color="text.secondary" display="block">
                    Column: {enrichment.column_name}
                  </Typography>
                )}
                <Typography variant="caption" color="text.secondary" display="block">
                  Created: {formatDate(enrichment.date_added)} · Updated:{' '}
                  {formatDate(enrichment.last_updated)}
                </Typography>
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  startIcon={<LaunchIcon />}
                  onClick={() =>
                    navigate(`/projects/${id}/enrichments/${enrichment.id}/review`)
                  }
                >
                  Open
                </Button>
                <Button
                  size="small"
                  startIcon={<EditIcon />}
                  onClick={() => setEditing(enrichment)}
                >
                  Edit
                </Button>
                <Button
                  size="small"
                  color="error"
                  startIcon={<DeleteIcon />}
                  onClick={() => setDeleting(enrichment)}
                >
                  Delete
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      <EditEnrichmentDialog
        enrichment={editing}
        onClose={() => setEditing(null)}
        onSaved={() => {
          setEditing(null);
          invalidate();
        }}
      />

      <ConfirmDialog
        open={deleting !== null}
        title="Delete enrichment?"
        message={`Are you sure you want to delete "${deleting?.enrichment_name}"?`}
        confirmLabel="Delete"
        destructive
        loading={deleteMutation.isPending}
        onConfirm={() => deleting && deleteMutation.mutate(deleting.id)}
        onCancel={() => setDeleting(null)}
      />
    </Box>
  );
}
