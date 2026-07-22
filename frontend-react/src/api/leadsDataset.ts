import { http } from './client';
import { UploadDatasetResponse } from './types';

export interface UploadDatasetArgs {
  projectId: number;
  datasetName: string;
  leadColumn: string;
  enrichmentColumnList: string[];
  enrichmentColumnExists: boolean;
  file: File;
}

export async function uploadDataset({
  projectId,
  datasetName,
  leadColumn,
  enrichmentColumnList,
  enrichmentColumnExists,
  file,
}: UploadDatasetArgs): Promise<UploadDatasetResponse> {
  const form = new FormData();
  form.append('dataset_name', datasetName);
  form.append('lead_column', leadColumn);
  form.append('enrichment_column_list', JSON.stringify(enrichmentColumnList ?? []));
  form.append('enrichment_column_exists', enrichmentColumnExists ? 'true' : 'false');
  form.append('file', file);

  const { data } = await http.post<UploadDatasetResponse>(
    `/api/projects/${projectId}/datasets`,
    form,
  );
  return data;
}
