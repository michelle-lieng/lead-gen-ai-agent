/** Centralised React Query keys. */
export const queryKeys = {
  projects: ['projects'] as const,
  project: (id: number) => ['projects', id] as const,
  queries: (projectId: number) => ['projects', projectId, 'queries'] as const,
  urls: (projectId: number) => ['projects', projectId, 'urls'] as const,
  enrichments: (projectId: number) => ['projects', projectId, 'enrichments'] as const,
  enrichment: (id: number) => ['enrichments', id] as const,
  mergedResults: (projectId: number) => ['projects', projectId, 'results'] as const,
  chat: (projectId: number) => ['projects', projectId, 'chat'] as const,
};
