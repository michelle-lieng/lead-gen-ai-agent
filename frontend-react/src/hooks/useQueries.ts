import { useQuery } from '@tanstack/react-query';
import { getQueries } from '../api/leadsSerp';
import { queryKeys } from './queryKeys';

/**
 * The searches already run against this register. Shown on the idle Find
 * panel as the record of what has been asked before, so the panel carries the
 * register's provenance rather than sitting empty.
 */
export function useQueryHistory(projectId: number | undefined) {
  return useQuery({
    queryKey: projectId ? queryKeys.queries(projectId) : ['queries', 'none'],
    queryFn: () => getQueries(projectId as number),
    enabled: projectId != null && !Number.isNaN(projectId),
  });
}
