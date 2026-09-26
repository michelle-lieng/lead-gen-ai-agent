/**
 * The workspace home: every base as a card, with the figures that say whether
 * it has been worked and how recently.
 */

import { useNavigate } from 'react-router-dom';
import { Project } from '../api/types';
import { AppShell, SidebarToggle, useShell } from '../components/shell/AppShell';
import { Icon } from '../components/ui/Icon';
import { PopItem, PopRule, Popover } from '../components/ui/Popover';
import { Button, EmptyState, IconButton } from '../components/ui/Primitives';
import { useProjects } from '../hooks/useProjects';
import { baseColor, baseInitials } from '../utils/base';
import { formatRelative } from '../utils/download';
import { useState } from 'react';

export function Projects() {
  return (
    <AppShell>
      <Home />
    </AppShell>
  );
}

function Home() {
  const navigate = useNavigate();
  const { data: projects, isLoading } = useProjects();
  const { createBase, renameBase, deleteBase } = useShell();
  const [menuFor, setMenuFor] = useState<{ project: Project; anchor: HTMLElement } | null>(
    null,
  );

  const total = projects?.length ?? 0;
  const totalRecords = (projects ?? []).reduce((sum, p) => sum + p.leads_collected, 0);

  return (
    <main className="main main--plain">
      <div className="basebar">
        <SidebarToggle />
        <span className="basebar__title">
          <h1>Home</h1>
          {total > 0 && (
            <span className="basebar__meta">
              {total} {total === 1 ? 'base' : 'bases'} ·{' '}
              {totalRecords.toLocaleString()} {totalRecords === 1 ? 'record' : 'records'}
            </span>
          )}
        </span>
        <span className="basebar__spacer" />
        <Button tone="primary" icon="plus" compact onClick={createBase}>
          Create a base
        </Button>
      </div>

      <div className="home">
        {isLoading && <p className="quiet">Loading your bases…</p>}

        {!isLoading && total === 0 && (
          <EmptyState
            icon="field-select"
            title="No bases yet"
            body="A base holds one search: the companies you find, and every field you ask about them. Create one and describe the leads you want in a sentence."
            actions={
              <Button tone="primary" icon="plus" onClick={createBase}>
                Create your first base
              </Button>
            }
          />
        )}

        {!isLoading && total > 0 && (
          <>
            <span className="home__label">Your bases</span>
            <div className="home__grid">
              {projects?.map((project) => (
                <div key={project.id} className="base">
                  <button
                    type="button"
                    className="base__open"
                    onClick={() => navigate(`/projects/${project.id}`)}
                  >
                    <span
                      className="base__icon"
                      style={{ background: baseColor(project.id) }}
                      aria-hidden="true"
                    >
                      {baseInitials(project.project_name)}
                    </span>
                    <span>
                      <span className="base__name">{project.project_name}</span>
                      {project.description && (
                        <span className="base__note">{project.description}</span>
                      )}
                    </span>
                    <span className="base__meta">
                      {project.leads_collected.toLocaleString()}{' '}
                      {project.leads_collected === 1 ? 'record' : 'records'}
                      {project.urls_processed > 0 &&
                        ` · ${project.urls_processed.toLocaleString()} sources read`}
                      <br />
                      Opened {formatRelative(project.date_added)} · worked{' '}
                      {formatRelative(project.last_updated)}
                    </span>
                  </button>

                  <span className="base__more">
                    <IconButton
                      icon="more"
                      label={`Options for ${project.project_name}`}
                      compact
                      aria-haspopup="menu"
                      aria-expanded={menuFor?.project.id === project.id}
                      onClick={(event) =>
                        setMenuFor({ project, anchor: event.currentTarget })
                      }
                    />
                  </span>
                </div>
              ))}

              <button type="button" className="base base--new" onClick={createBase}>
                <Icon name="plus" size={18} />
                <b>Create a base</b>
                <span>Start a new search with its own table of companies.</span>
              </button>
            </div>
          </>
        )}
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
              renameBase(menuFor.project);
              setMenuFor(null);
            }}
          >
            Rename base
          </PopItem>
          <PopRule />
          <PopItem
            icon="trash"
            tone="danger"
            onClick={() => {
              deleteBase(menuFor.project);
              setMenuFor(null);
            }}
          >
            Delete base
          </PopItem>
        </Popover>
      )}
    </main>
  );
}
