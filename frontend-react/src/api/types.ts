/** Shared API model types mirroring the FastAPI schemas. */

export interface Project {
  id: number;
  project_name: string;
  description: string | null;
  query_search_target: string | null;
  lead_minimum_criteria: string | null;
  date_added: string;
  last_updated: string;
  leads_collected: number;
  datasets_added: number;
  urls_processed: number;
}

export interface ProjectCreate {
  project_name: string;
  description?: string | null;
}

export interface ProjectUpdate {
  project_name?: string;
  description?: string | null;
  query_search_target?: string | null;
  lead_minimum_criteria?: string | null;
}

export interface QueryRecord {
  id: number;
  project_id: number;
  query: string;
  date_added: string;
}

export interface SerpUrl {
  id: number;
  project_id: number;
  query: string;
  title: string;
  link: string;
  snippet: string;
  date?: string | null;
  website_scraped?: string | null;
  status: string;
  created_at?: string | null;
}

export interface UrlCreate {
  link: string;
  title?: string | null;
  snippet?: string | null;
  date?: string | null;
}

export interface UrlUpdate {
  title?: string | null;
  snippet?: string | null;
  link?: string | null;
  date?: string | null;
}

export interface UrlGenerationResponse {
  urls_added: number;
  queries_processed: number;
}

export interface ExtractedLead {
  url: string;
  title: string;
  query: string;
  snippet: string;
  status: string;
  website_scraped?: string | null;
  leads: string[];
}

export interface LeadExtractionResponse {
  urls_processed: number;
  urls_skipped: number;
  urls_failed: number;
  total_urls_attempted: number;
  new_leads_extracted: number;
  extracted_leads: ExtractedLead[];
}

export type ResultFormat = 'True/False' | 'Text' | 'Number' | '';

export interface Enrichment {
  id: number;
  project_id: number;
  enrichment_name: string;
  column_name: string | null;
  enrichment_description: string | null;
  goal: string | null;
  acceptable_evidence: string | null;
  result_format: ResultFormat | null;
  result_true_if: string | null;
  result_false_if: string | null;
  result_number_value: string | null;
  result_text_value: string | null;
  date_added: string;
  last_updated: string;
}

export interface EnrichmentUpdate {
  enrichment_name?: string;
  column_name?: string;
  enrichment_description?: string;
  goal?: string;
  acceptable_evidence?: string;
  result_format?: string;
  result_true_if?: string;
  result_false_if?: string;
  result_number_value?: string;
  result_text_value?: string;
}

export type LeadRow = Record<string, unknown> & { lead: string };

export interface EnrichLeadsResponse {
  success: boolean;
  message: string;
  leads_processed: number;
  enrichment_id: number;
  project_id: number;
  enriched_leads: LeadRow[];
  columns: string[];
}

export interface MergedResultsResponse {
  data: Record<string, unknown>[];
  columns: string[];
  count: number;
}

export interface UploadDatasetResponse {
  success: boolean;
  message?: string;
  detail?: unknown;
  rows_processed?: number;
  project_dataset_id?: number;
}

export interface JobStatus {
  id: number;
  project_id: number;
  job_type: string;
  job_type_id: number | null;
  status: 'running' | 'completed' | 'failed';
  completed_at: string | null;
  error_message: string | null;
}

/** A downloaded file: raw bytes plus the filename parsed from the response. */
export interface DownloadedFile {
  blob: Blob;
  filename: string;
}
