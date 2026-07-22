import { http, parseFilename } from './client';
import { DownloadedFile, MergedResultsResponse } from './types';

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
