/**
 * The sidebar: the workspace, its projects, and the account slot.
 *
 * Every project carries the coloured square it is recognised by.
 * Sign out sits at the very bottom, where a workspace puts the account, with
 * the server's key status under it: nothing runs without the OpenAI and Jina
 * keys, so that state is permanently on screen rather than behind a menu.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Project } from '../../api/types';
import { useServerKeys } from '../../hooks/useServerKeys';
import { projectColor, projectInitials } from '../../utils/project';
import { Icon } from '../ui/Icon';
import { PopItem, PopRule, Popover } from '../ui/Popover';
import { IconButton } from '../ui/Primitives';

interface SidebarProps {
  projects: Project[];
  loading: boolean;
  activeId?: number;
  onCreate: () => void;
  onRename: (project: Project) => void;
  onDelete: (project: Project) => void;
  onSignOut: () => void;
  /** Closes the slide-over after navigating, on narrow screens. */
  onNavigate?: () => void;
  hidden?: boolean;
}

export function Sidebar({
  projects,
  loading,
  activeId,
  onCreate,
  onRename,
  onDelete,
  onSignOut,
  onNavigate,
  hidden,
}: SidebarProps) {
  const navigate = useNavigate();
  const { hasKeys, googleKey } = useServerKeys();
  const [menuFor, setMenuFor] = useState<{ project: Project; anchor: HTMLElement } | null>(
    null,
  );

  const go = (to: string) => {
    navigate(to);
    onNavigate?.();
  };

  return (
    <aside className="side" hidden={hidden}>
      <div className="side__top">
        <button
          type="button"
          className="side__mark"
          onClick={() => go('/')}
          aria-label="Kiyu Labs workspace home"
          title="Workspace home"
        >
          K
        </button>
        <span className="side__workspace">
          <b>Kiyu Labs</b>
          <span>Leads workspace</span>
        </span>
      </div>

      <div className="side__section">
        <span>Projects</span>
        <span>{projects.length > 0 ? projects.length : ''}</span>
      </div>

      <ul className="side__list">
        {loading && <li className="side__empty">Loading projects…</li>}

        {!loading && projects.length === 0 && (
          <li className="side__empty">
            No projects yet. Create one to start finding leads.
          </li>
        )}

        {projects.map((project) => (
          <li
            key={project.id}
            className="side__item"
            data-active={project.id === activeId || undefined}
          >
            <button
              type="button"
              className="side__link"
              aria-current={project.id === activeId ? 'page' : undefined}
              onClick={() => go(`/projects/${project.id}`)}
            >
              <span
                className="side__icon"
                style={{ background: projectColor(project.id) }}
                aria-hidden="true"
              >
                {projectInitials(project.project_name)}
              </span>
              <span className="side__name">{project.project_name}</span>
              {project.leads_collected > 0 && (
                <span className="side__count">
                  {project.leads_collected.toLocaleString()}
                </span>
              )}
            </button>

            <span className="side__more">
              <IconButton
                icon="more"
                label={`Options for ${project.project_name}`}
                compact
                size={13}
                aria-haspopup="menu"
                aria-expanded={menuFor?.project.id === project.id}
                onClick={(event) =>
                  setMenuFor({ project, anchor: event.currentTarget })
                }
              />
            </span>
          </li>
        ))}
      </ul>

      <div className="side__foot">
        <button type="button" className="side__create" onClick={onCreate}>
          <Icon name="plus" size={14} />
          Create a project
        </button>

        <button
          type="button"
          className="side__keys"
          data-missing={!hasKeys || undefined}
          onClick={onSignOut}
          aria-label="Sign out"
        >
          <span className="side__keys__dot" aria-hidden="true">
            <Icon name="key" size={12} />
          </span>
          <span style={{ minWidth: 0 }}>
            <b>Sign out</b>
            <span>
              {hasKeys
                ? `OpenAI and Jina set${googleKey ? ' · Google Places on' : ''}`
                : 'Server is missing OpenAI or Jina key'}
            </span>
          </span>
        </button>
      </div>

      {menuFor && (
        <Popover
          anchor={menuFor.anchor}
          label={`${menuFor.project.project_name} options`}
          align="end"
          onClose={() => setMenuFor(null)}
        >
          <PopItem
            icon="pencil"
            onClick={() => {
              onRename(menuFor.project);
              setMenuFor(null);
            }}
          >
            Rename project
          </PopItem>
          <PopRule />
          <PopItem
            icon="trash"
            tone="danger"
            onClick={() => {
              onDelete(menuFor.project);
              setMenuFor(null);
            }}
          >
            Delete project
          </PopItem>
        </Popover>
      )}
    </aside>
  );
}
