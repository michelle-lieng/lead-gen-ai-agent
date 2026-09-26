/**
 * Creating and renaming a project. One form serves both, because the fields are
 * the same and only the verb changes.
 */

import { FormEvent, useEffect, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { createProject, updateProject } from '../../api/projects';
import { Project } from '../../api/types';
import { Modal } from '../ui/Modal';
import { Button, Field, TextArea } from '../ui/Primitives';
import { useNotify } from '../ui/Toasts';

export function ProjectDialog({
  open,
  project,
  onClose,
  onSaved,
}: {
  open: boolean;
  /** Present when renaming; absent when creating. */
  project?: Project | null;
  onClose: () => void;
  onSaved: (project: Project, created: boolean) => void;
}) {
  const { notify, notifyError } = useNotify();
  const [name, setName] = useState('');
  const [note, setNote] = useState('');

  // Load the record being edited each time the dialog opens on it.
  useEffect(() => {
    if (!open) return;
    setName(project?.project_name ?? '');
    setNote(project?.description ?? '');
  }, [open, project]);

  const mutation = useMutation({
    mutationFn: () =>
      project
        ? updateProject(project.id, {
            project_name: name.trim(),
            description: note.trim() || null,
          })
        : createProject({ project_name: name.trim(), description: note.trim() || null }),
    onSuccess: (saved) => {
      notify(
        project ? 'Project renamed.' : `Project “${saved.project_name}” created.`,
        'success',
      );
      onSaved(saved, !project);
    },
    onError: notifyError,
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (name.trim() && !mutation.isPending) mutation.mutate();
  };

  return (
    <Modal
      open={open}
      title={project ? 'Rename project' : 'Create a project'}
      note={
        project
          ? undefined
          : 'A project holds one search: the companies you find, and every field you ask about them.'
      }
      onClose={onClose}
      width={470}
      footer={
        <>
          <Button onClick={onClose} disabled={mutation.isPending}>
            Cancel
          </Button>
          <Button
            tone="primary"
            icon="check"
            loading={mutation.isPending}
            disabled={!name.trim()}
            onClick={() => mutation.mutate()}
          >
            {project ? 'Save' : 'Create project'}
          </Button>
        </>
      }
    >
      <form onSubmit={submit} style={{ display: 'grid', gap: 15 }}>
        <Field
          label="Name"
          value={name}
          required
          placeholder="Sydney dental clinics"
          onChange={(event) => setName(event.target.value)}
        />
        <TextArea
          label="Description (optional)"
          value={note}
          rows={3}
          placeholder="What this list is for."
          onChange={(event) => setNote(event.target.value)}
        />
        <button type="submit" hidden aria-hidden="true" tabIndex={-1} />
      </form>
    </Modal>
  );
}
