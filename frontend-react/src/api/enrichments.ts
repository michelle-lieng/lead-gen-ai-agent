import { http } from './client';
import { EnrichLeadsResponse, Enrichment, EnrichmentUpdate, LeadRow } from './types';

export async function getEnrichments(projectId: number): Promise<Enrichment[]> {
  const { data } = await http.get<Enrichment[]>(
    `/api/projects/${projectId}/enrichments/`,
  );
  return data ?? [];
}

export async function getEnrichment(enrichmentId: number): Promise<Enrichment> {
  const { data } = await http.get<Enrichment>(`/api/enrichments/${enrichmentId}`);
  return data;
}

export async function createEnrichment(
  projectId: number,
  enrichmentName: string,
  enrichmentDescription?: string | null,
): Promise<Enrichment> {
  const { data } = await http.post<Enrichment>(
    `/api/projects/${projectId}/enrichments/`,
    { enrichment_name: enrichmentName, enrichment_description: enrichmentDescription },
  );
  return data;
}

export async function updateEnrichment(
  enrichmentId: number,
  payload: EnrichmentUpdate,
): Promise<Enrichment> {
  const { data } = await http.put<Enrichment>(`/api/enrichments/${enrichmentId}`, payload);
  return data;
}

export async function deleteEnrichment(enrichmentId: number): Promise<void> {
  await http.delete(`/api/enrichments/${enrichmentId}`);
}

export async function enrichLeads(
  projectId: number,
  enrichmentId: number,
  leadsData: LeadRow[],
): Promise<EnrichLeadsResponse> {
  const { data } = await http.post<EnrichLeadsResponse>(
    `/api/projects/${projectId}/enrichments/${enrichmentId}/enrich-leads`,
    { leads_data: leadsData },
  );
  return data;
}

export async function testEnrichLeads(
  projectId: number,
  enrichmentId: number,
  leadsData: LeadRow[],
): Promise<EnrichLeadsResponse> {
  const { data } = await http.post<EnrichLeadsResponse>(
    `/api/projects/${projectId}/enrichments/${enrichmentId}/test-enrich-leads`,
    { leads_data: leadsData },
  );
  return data;
}
