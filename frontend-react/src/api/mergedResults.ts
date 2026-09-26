import { http, parseFilename } from './client';
import {
  DownloadedFile,
  MergedResultsResponse,
  MergedRowUpdateResponse,
} from './types';

export async function getMergedResults(
  projectId: number,
): Promise<MergedResultsResponse> {
  const { data } = await http.get<MergedResultsResponse>(
    `/api/projects/${projectId}/results`,
  );
  return data;
}

export async function fetchMergedResultsZip(
  projectId: number,
): Promise<DownloadedFile | null> {
  const response = await http.get(`/api/projects/${projectId}/results/download`, {
    responseType: 'blob',
  });
  if (response.status === 204) return null;
  return {
    blob: response.data as Blob,
    filename: parseFilename(
      response.headers['content-disposition'],
      `project_${projectId}_merged_results.zip`,
    ),
  };
}

/** Edit one entry in the register, addressed by its current lead name. */
export async function updateMergedRow(
  projectId: number,
  lead: string,
  updates: Record<string, unknown>,
): Promise<MergedRowUpdateResponse> {
  const { data } = await http.patch<MergedRowUpdateResponse>(
    `/api/projects/${projectId}/results/row`,
    { lead, updates },
  );
  return data;
}

/** Remove one entry from the register. */
export async function deleteMergedRow(
  projectId: number,
  lead: string,
): Promise<void> {
  await http.delete(`/api/projects/${projectId}/results/row`, { params: { lead } });
}
