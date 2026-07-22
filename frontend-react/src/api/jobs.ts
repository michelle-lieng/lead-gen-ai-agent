import { http } from './client';
import { JobStatus } from './types';

export async function getJobStatus(
  projectId: number,
  jobType: string,
  jobTypeId?: number,
): Promise<JobStatus | null> {
  const response = await http.get<JobStatus | null>(
    `/api/projects/${projectId}/jobs/${jobType}`,
    { params: jobTypeId != null ? { job_type_id: jobTypeId } : undefined },
  );
  if (response.status === 204) return null;
  return response.data ?? null;
}
