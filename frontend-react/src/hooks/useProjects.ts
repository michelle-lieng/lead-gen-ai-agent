import { useQuery } from '@tanstack/react-query';
import { getProject, getProjects } from '../api/projects';
import { queryKeys } from './queryKeys';

export function useProjects() {
  return useQuery({ queryKey: queryKeys.projects, queryFn: getProjects });
}

export function useProject(projectId: number | undefined) {
  return useQuery({
    queryKey: projectId ? queryKeys.project(projectId) : ['projects', 'none'],
    queryFn: () => getProject(projectId as number),
    enabled: projectId != null && !Number.isNaN(projectId),
  });
}
