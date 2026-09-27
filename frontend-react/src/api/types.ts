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

/** Who wrote a line of a project's conversation. */
export type ChatRole = 'user' | 'agent' | 'log';

export type ChatKind =
  | 'text'
  | 'step'
  | 'result'
  | 'error'
  | 'breakdown'
  | 'definition'
  | 'query';

export interface ChatEntryCreate {
  role: ChatRole;
  kind: ChatKind;
  text: string;
  payload?: Record<string, unknown> | null;
}

/** One saved line of a project's conversation. */
export interface ChatEntry extends ChatEntryCreate {
  id: number;
  project_id: number;
  /** ISO timestamp, UTC. */
  created_at: string;
}

export interface ChatHistory {
  /** Oldest first. */
  entries: ChatEntry[];
  /** True when older entries exist before the first one returned. */
  has_more: boolean;
}

/** An existing column to finish, with the leads it has no answer for yet. */
export interface ContinueColumn {
  enrichment_id: number;
  name: string;
  column_name: string;
  leads: string[];
}

/** What one Google Places search added to the table. */
export interface PlacesSearchResult {
  /** Distinct businesses Google returned. */
  found: number;
  /** Of those, how many were not in the table before. */
  new: number;
  existing: number;
  /** Normalized names of every business found. */
  leads: string[];
}

/** What the agent decided one chat message asks for. */
export interface MessagePlan {
  /** Search for companies: a new search, or more of the current one. */
  find: boolean;
  /** The base search: entity type plus its searchable anchor. */
  find_instruction: string;
  /** The place the message names, '' when none; searches Google Places first. */
  location: string;
  /** Yes/No questions, one new True/False column each. */
  criteria: string[];
  /** One research question per new column. */
  columns: string[];
  /** Existing columns to finish for the leads they have no answer for yet. */
  continue_columns: ContinueColumn[];
  /** A direct answer, when the message needs one. */
  reply: string;
}

/** A downloaded file: raw bytes plus the filename parsed from the response. */
export interface DownloadedFile {
  blob: Blob;
  filename: string;
}

/** What the backend drafts from a "find me leads like this" instruction. */
export interface LeadBrief {
  query_search_target: string;
  lead_minimum_criteria: string;
  num_queries: number;
}

/** Result of editing one row of the register. */
export interface MergedRowUpdateResponse {
  lead: string;
  updated: string[];
}
