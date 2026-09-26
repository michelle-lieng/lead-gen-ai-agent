/**
 * The workspace home: every project as a card, with the figures that say
 * whether it has been worked and how recently.
 */

import { useNavigate } from 'react-router-dom';
import { Project } from '../api/types';
import { AppShell, SidebarToggle, useShell } from '../components/shell/AppShell';
import { Icon } from '../components/ui/Icon';
import { PopItem, PopRule, Popover } from '../components/ui/Popover';
import { Button, EmptyState, IconButton } from '../components/ui/Primitives';
import { useProjects } from '../hooks/useProjects';
import { projectColor, projectInitials } from '../utils/project';
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
  const { createProject, renameProject, deleteProject } = useShell();
  const [menuFor, setMenuFor] = useState<{ project: Project; anchor: HTMLElement } | null>(
    null,
  );

  const total = projects?.length ?? 0;
  const totalRecords = (projects ?? []).reduce((sum, p) => sum + p.leads_collected, 0);

  return (
    <main className="main main--plain">
      <div className="projectbar">
        <SidebarToggle />
        <span className="projectbar__title">
          <h1>Home</h1>
          {total > 0 && (
            <span className="projectbar__meta">
              {total} {total === 1 ? 'project' : 'projects'} ·{' '}
              {totalRecords.toLocaleString()} {totalRecords === 1 ? 'record' : 'records'}
            </span>
          )}
        </span>
        <span className="projectbar__spacer" />
      </div>

      <div className="home">
        {isLoading && <p className="quiet">Loading your projects…</p>}

        {!isLoading && total === 0 && (
          <EmptyState
            icon="field-select"
            title="No projects yet"
            body="A project holds one search: the companies you find, and every field you ask about them. Create one and describe the leads you want in a sentence."
            actions={
              <Button tone="primary" icon="plus" onClick={createProject}>
                Create your first project
              </Button>
            }
          />
        )}

        {!isLoading && total > 0 && (
          <>
            <span className="home__label">Your projects</span>
            <div className="home__grid">
              {projects?.map((project) => (
                <div key={project.id} className="project">
                  <button
                    type="button"
                    className="project__open"
                    onClick={() => navigate(`/projects/${project.id}`)}
                  >
                    <span
                      className="project__icon"
                      style={{ background: projectColor(project.id) }}
                      aria-hidden="true"
                    >
                      {projectInitials(project.project_name)}
                    </span>
                    <span>
                      <span className="project__name">{project.project_name}</span>
                      {project.description && (
                        <span className="project__note">{project.description}</span>
                      )}
                    </span>
                    <span className="project__meta">
                      {project.leads_collected.toLocaleString()}{' '}
                      {project.leads_collected === 1 ? 'record' : 'records'}
                      {project.urls_processed > 0 &&
                        ` · ${project.urls_processed.toLocaleString()} sources read`}
                      <br />
                      Opened {formatRelative(project.date_added)} · worked{' '}
                      {formatRelative(project.last_updated)}
                    </span>
                  </button>

                  <span className="project__more">
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

              <button
                type="button"
                className="project project--new"
                onClick={createProject}
              >
                <Icon name="plus" size={18} />
                <b>Create a project</b>
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
              renameProject(menuFor.project);
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
              deleteProject(menuFor.project);
              setMenuFor(null);
            }}
          >
            Delete project
          </PopItem>
        </Popover>
      )}
    </main>
  );
}
