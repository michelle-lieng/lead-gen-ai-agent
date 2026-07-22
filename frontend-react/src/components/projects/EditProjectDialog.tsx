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
import { updateProject } from '../../api/projects';
import { Project } from '../../api/types';
import { LoadingButton } from '../common/LoadingButton';
import { useNotify } from '../common/Notifications';

interface EditProjectDialogProps {
  project: Project | null;
  onClose: () => void;
  onSaved: () => void;
}

/** Dialog for editing a project's name and notes. */
export function EditProjectDialog({ project, onClose, onSaved }: EditProjectDialogProps) {
  const { notify, notifyError } = useNotify();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  useEffect(() => {
    if (project) {
      setName(project.project_name);
      setDescription(project.description ?? '');
    }
  }, [project]);

  const mutation = useMutation({
    mutationFn: () =>
      updateProject(project!.id, {
        project_name: name.trim(),
        description: description.trim() || null,
      }),
    onSuccess: () => {
      notify('Project updated.', 'success');
      onSaved();
    },
    onError: notifyError,
  });

  return (
    <Dialog open={project !== null} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Edit Project</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <TextField
            label="Project Name"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
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
