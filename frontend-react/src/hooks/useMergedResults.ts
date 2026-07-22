import { useQuery } from '@tanstack/react-query';
import { getMergedResults } from '../api/mergedResults';
import { queryKeys } from './queryKeys';

export function useMergedResults(projectId: number | undefined) {
  return useQuery({
    queryKey: projectId ? queryKeys.mergedResults(projectId) : ['results', 'none'],
    queryFn: () => getMergedResults(projectId as number),
    enabled: projectId != null && !Number.isNaN(projectId),
  });
}
