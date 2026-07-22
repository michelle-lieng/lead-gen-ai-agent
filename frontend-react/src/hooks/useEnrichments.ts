import { useQuery } from '@tanstack/react-query';
import { getEnrichment, getEnrichments } from '../api/enrichments';
import { queryKeys } from './queryKeys';

export function useEnrichments(projectId: number | undefined) {
  return useQuery({
    queryKey: projectId ? queryKeys.enrichments(projectId) : ['enrichments', 'none'],
    queryFn: () => getEnrichments(projectId as number),
    enabled: projectId != null && !Number.isNaN(projectId),
  });
}

export function useEnrichment(enrichmentId: number | undefined) {
  return useQuery({
    queryKey: enrichmentId ? queryKeys.enrichment(enrichmentId) : ['enrichments', 'none'],
    queryFn: () => getEnrichment(enrichmentId as number),
    enabled: enrichmentId != null && !Number.isNaN(enrichmentId),
  });
}
