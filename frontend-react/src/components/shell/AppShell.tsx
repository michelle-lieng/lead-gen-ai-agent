/**
 * The app frame: sidebar, content region, and the enquiry panel.
 *
 * The content region carries the rounded seam where it meets the sidebar, so
 * both surfaces — the workspace home and a base — sit in the same shell and the
 * sidebar never reloads between them. Base creation, renaming and deletion live
 * here because the sidebar can start any of them from either surface.
 */

import {
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { deleteProject } from '../../api/projects';
import { Project } from '../../api/types';
import { useApiKeysDialog } from '../apiKeys/ApiKeys';
import { queryKeys } from '../../hooks/queryKeys';
import { useProjects } from '../../hooks/useProjects';
import { Confirm } from '../ui/Modal';
import { PopItem, PopRule, Popover } from '../ui/Popover';
import { IconButton } from '../ui/Primitives';
import { useNotify } from '../ui/Toasts';
import { BaseDialog } from './BaseDialog';
import { Sidebar } from './Sidebar';

interface ShellApi {
  openSidebar: () => void;
  createBase: () => void;
  renameBase: (project: Project) => void;
  deleteBase: (project: Project) => void;
}

const ShellContext = createContext<ShellApi | null>(null);

/** The sidebar button, shown only where the sidebar has collapsed to a drawer. */
export function SidebarToggle() {
  const shell = useContext(ShellContext);
  if (!shell) return null;
  return (
    <span className="side__toggle">
      <IconButton
        icon="sidebar"
        label="Show bases"
        compact
        onClick={shell.openSidebar}
      />
    </span>
  );
}

export function useShell(): ShellApi {
  const context = useContext(ShellContext);
  if (!context) throw new Error('useShell must be used inside AppShell');
  return context;
}

/**
 * The open base's own menu, in the base bar. It lives here so that renaming and
 * deleting a base run through the shell's one set of dialogs wherever they are
 * started from.
 */
export function BaseMenuButton({ project }: { project: Project }) {
  const { renameBase, deleteBase } = useShell();
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);

  return (
    <>
      <IconButton
        icon="more"
        label={`${project.project_name} options`}
        compact
        aria-haspopup="menu"
        aria-expanded={anchor !== null}
        onClick={(event) => setAnchor(event.currentTarget)}
      />
      {anchor && (
        <Popover
          anchor={anchor}
          label={`${project.project_name} options`}
          onClose={() => setAnchor(null)}
        >
          <PopItem
            icon="pencil"
            onClick={() => {
              setAnchor(null);
              renameBase(project);
            }}
          >
            Rename base
          </PopItem>
          <PopRule />
          <PopItem
            icon="trash"
            tone="danger"
            onClick={() => {
              setAnchor(null);
              deleteBase(project);
            }}
          >
            Delete base
          </PopItem>
        </Popover>
      )}
    </>
  );
}

export function AppShell({
  activeId,
  children,
  panel,
}: {
  activeId?: number;
  /** The content region: its own bars, body and footer. */
  children: ReactNode;
  panel?: ReactNode;
}) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { notify, notifyError } = useNotify();
  const { openDialog } = useApiKeysDialog();
  const { data: projects, isLoading } = useProjects();

  const [drawerOpen, setDrawerOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [renaming, setRenaming] = useState<Project | null>(null);
  const [deleting, setDeleting] = useState<Project | null>(null);

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: queryKeys.projects });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteProject(id),
    onSuccess: (_data, id) => {
      notify('Base deleted.', 'success');
      setDeleting(null);
      invalidate();
      // Leaving the base that was just deleted open would show a dead record.
      if (id === activeId) navigate('/');
    },
    onError: notifyError,
  });

  const openSidebar = useCallback(() => setDrawerOpen(true), []);
  const createBase = useCallback(() => setCreating(true), []);
  const renameBase = useCallback((project: Project) => setRenaming(project), []);
  const deleteBase = useCallback((project: Project) => setDeleting(project), []);
  const api = useMemo(
    () => ({ openSidebar, createBase, renameBase, deleteBase }),
    [openSidebar, createBase, renameBase, deleteBase],
  );

  return (
    <ShellContext.Provider value={api}>
      <div className="app" data-panel={panel ? 'open' : 'closed'}>
        {drawerOpen && (
          <div
            className="side__scrim"
            onClick={() => setDrawerOpen(false)}
            aria-hidden="true"
          />
        )}

        <Sidebar
          projects={projects ?? []}
          loading={isLoading}
          activeId={activeId}
          hidden={!drawerOpen}
          onCreate={() => setCreating(true)}
          onRename={setRenaming}
          onDelete={setDeleting}
          onOpenKeys={openDialog}
          onNavigate={() => setDrawerOpen(false)}
        />

        {children}

        {panel}
      </div>

      <BaseDialog
        open={creating}
        onClose={() => setCreating(false)}
        onSaved={(project) => {
          setCreating(false);
          invalidate();
          navigate(`/projects/${project.id}`);
        }}
      />

      <BaseDialog
        open={renaming !== null}
        project={renaming}
        onClose={() => setRenaming(null)}
        onSaved={() => {
          setRenaming(null);
          invalidate();
          queryClient.invalidateQueries({ queryKey: queryKeys.projects });
        }}
      />

      <Confirm
        open={deleting !== null}
        title="Delete this base?"
        message={`“${deleting?.project_name}” and every record, field and source in it will be removed. This cannot be undone.`}
        confirmLabel="Delete base"
        destructive
        loading={deleteMutation.isPending}
        onConfirm={() => deleting && deleteMutation.mutate(deleting.id)}
        onCancel={() => setDeleting(null)}
      />
    </ShellContext.Provider>
  );
}
