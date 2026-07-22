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
import { useNavigate } from 'react-router-dom';
import { createProject, deleteProject } from '../api/projects';
import { Project } from '../api/types';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { LoadingButton } from '../components/common/LoadingButton';
import { useNotify } from '../components/common/Notifications';
import { PageHeader } from '../components/common/PageHeader';
import { useProjects } from '../hooks/useProjects';
import { queryKeys } from '../hooks/queryKeys';
import { formatDate } from '../utils/download';
import { EditProjectDialog } from '../components/projects/EditProjectDialog';

export function Dashboard() {
  const { data: projects, isLoading } = useProjects();
  const queryClient = useQueryClient();
  const { notify, notifyError } = useNotify();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [editing, setEditing] = useState<Project | null>(null);
  const [deleting, setDeleting] = useState<Project | null>(null);

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: queryKeys.projects });

  const createMutation = useMutation({
    mutationFn: () =>
      createProject({ project_name: name.trim(), description: description.trim() || null }),
    onSuccess: (project) => {
      notify(`Project "${project.project_name}" created.`, 'success');
      setName('');
      setDescription('');
      invalidate();
    },
    onError: notifyError,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteProject(id),
    onSuccess: () => {
      notify('Project deleted.', 'success');
      setDeleting(null);
      invalidate();
    },
    onError: notifyError,
  });

  return (
    <Box>
      <PageHeader title="Dashboard" subtitle="Create and manage your lead-gen projects" />

      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Create New Project
          </Typography>
          <Stack spacing={2}>
            <TextField
              label="Project Name"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Seabin Leads"
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
                Create Project
              </LoadingButton>
            </Box>
          </Stack>
        </CardContent>
      </Card>

      <Typography variant="h6" gutterBottom>
        Your Projects{projects ? ` (${projects.length})` : ''}
      </Typography>

      {isLoading && <Typography color="text.secondary">Loading projects...</Typography>}
      {!isLoading && (!projects || projects.length === 0) && (
        <Typography color="text.secondary">No projects yet. Create one above.</Typography>
      )}

      <Grid container spacing={2}>
        {projects?.map((project) => (
          <Grid item xs={12} md={6} lg={4} key={project.id}>
            <ProjectCard
              project={project}
              onEdit={() => setEditing(project)}
              onDelete={() => setDeleting(project)}
            />
          </Grid>
        ))}
      </Grid>

      <EditProjectDialog
        project={editing}
        onClose={() => setEditing(null)}
        onSaved={() => {
          setEditing(null);
          invalidate();
        }}
      />

      <ConfirmDialog
        open={deleting !== null}
        title="Delete project?"
        message={`Are you sure you want to delete "${deleting?.project_name}"? This cannot be undone.`}
        confirmLabel="Delete"
        destructive
        loading={deleteMutation.isPending}
        onConfirm={() => deleting && deleteMutation.mutate(deleting.id)}
        onCancel={() => setDeleting(null)}
      />
    </Box>
  );
}

function ProjectCard({
  project,
  onEdit,
  onDelete,
}: {
  project: Project;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const navigate = useNavigate();
  return (
    <Card variant="outlined" sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Typography variant="h6">{project.project_name}</Typography>
        {project.description && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {project.description}
          </Typography>
        )}
        <Typography variant="caption" color="text.secondary" display="block">
          Created: {formatDate(project.date_added)} · Updated: {formatDate(project.last_updated)}
        </Typography>
        <Stack direction="row" spacing={3} sx={{ mt: 2 }}>
          <Metric label="Leads" value={project.leads_collected} />
          <Metric label="Datasets" value={project.datasets_added} />
          <Metric label="URLs" value={project.urls_processed} />
        </Stack>
      </CardContent>
      <CardActions>
        <Button
          size="small"
          startIcon={<LaunchIcon />}
          onClick={() => navigate(`/projects/${project.id}`)}
        >
          Open
        </Button>
        <Button size="small" startIcon={<EditIcon />} onClick={onEdit}>
          Edit
        </Button>
        <Button size="small" color="error" startIcon={<DeleteIcon />} onClick={onDelete}>
          Delete
        </Button>
      </CardActions>
    </Card>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <Box>
      <Typography variant="h6">{value}</Typography>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
    </Box>
  );
}
