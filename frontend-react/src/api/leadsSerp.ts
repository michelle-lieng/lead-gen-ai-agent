import { http, parseFilename } from './client';
import {
  DownloadedFile,
  LeadBrief,
  LeadExtractionResponse,
  QueryRecord,
  SerpUrl,
  UrlCreate,
  UrlGenerationResponse,
  UrlUpdate,
} from './types';

export async function generateQueries(
  projectId: number,
  numQueries = 3,
): Promise<string[]> {
  const { data } = await http.post<string[]>(`/api/projects/${projectId}/queries`, {
    num_queries: numQueries,
  });
  return data;
}

export async function getQueries(projectId: number): Promise<QueryRecord[]> {
  const { data } = await http.get<QueryRecord[]>(`/api/projects/${projectId}/queries`);
  return data ?? [];
}

export async function generateUrls(
  projectId: number,
  queries: string[],
): Promise<UrlGenerationResponse> {
  const { data } = await http.post<UrlGenerationResponse>(
    `/api/projects/${projectId}/urls`,
    { queries },
  );
  return data;
}

export async function getUrls(projectId: number): Promise<SerpUrl[]> {
  const { data } = await http.get<SerpUrl[]>(`/api/projects/${projectId}/urls`);
  return data ?? [];
}

export async function createUrl(projectId: number, payload: UrlCreate): Promise<SerpUrl> {
  const { data } = await http.post<SerpUrl>(
    `/api/projects/${projectId}/urls/create`,
    payload,
  );
  return data;
}

export async function updateUrl(
  projectId: number,
  urlId: number,
  payload: UrlUpdate,
): Promise<SerpUrl> {
  const { data } = await http.put<SerpUrl>(
    `/api/projects/${projectId}/urls/${urlId}`,
    payload,
  );
  return data;
}

export async function deleteUrl(projectId: number, urlId: number): Promise<void> {
  await http.delete(`/api/projects/${projectId}/urls/${urlId}`);
}

export async function generateLeads(projectId: number): Promise<LeadExtractionResponse> {
  const { data } = await http.post<LeadExtractionResponse>(
    `/api/projects/${projectId}/leads`,
  );
  return data;
}

export async function fetchLatestRunZip(
  projectId: number,
): Promise<DownloadedFile | null> {
  const response = await http.get(`/api/projects/${projectId}/leads/download`, {
    responseType: 'blob',
  });
  if (response.status === 204) return null;
  return {
    blob: response.data as Blob,
    filename: parseFilename(
      response.headers['content-disposition'],
      `project_${projectId}_leads.zip`,
    ),
  };
}

/**
 * Expand one plain-English instruction into the project's search target and
 * lead criteria, saving both to the project. This is what lets the chat take a
 * single sentence instead of a configuration form.
 */
export async function draftLeadBrief(
  projectId: number,
  instruction: string,
): Promise<LeadBrief> {
  const { data } = await http.post<LeadBrief>(
    `/api/projects/${projectId}/lead-brief`,
    { instruction },
  );
  return data;
}
