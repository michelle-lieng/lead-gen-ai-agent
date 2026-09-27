import { http } from './client';
import { Project, ProjectCreate, ProjectUpdate } from './types';

export async function getProjects(): Promise<Project[]> {
  const { data } = await http.get<Project[]>('/api/projects/');
  return data;
}

export async function getProject(projectId: number): Promise<Project> {
  const { data } = await http.get<Project>(`/api/projects/${projectId}`);
  return data;
}

export async function createProject(payload: ProjectCreate): Promise<Project> {
  const { data } = await http.post<Project>('/api/projects/', payload);
  return data;
}

export async function updateProject(
  projectId: number,
  payload: ProjectUpdate,
): Promise<Project> {
  const { data } = await http.put<Project>(`/api/projects/${projectId}`, payload);
  return data;
}

export async function deleteProject(projectId: number): Promise<void> {
  await http.delete(`/api/projects/${projectId}`);
}

/** Write (or rewrite) a project's example first messages from its title and description. */
export async function writeExamplePrompts(projectId: number): Promise<Project> {
  const { data } = await http.post<Project>(`/api/projects/${projectId}/example-prompts`);
  return data;
}
