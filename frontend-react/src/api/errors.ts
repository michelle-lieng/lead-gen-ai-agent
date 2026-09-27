/**
 * Typed API errors and user-friendly message mapping.
 * Ported from the Streamlit frontend's ui_errors.py so error UX stays consistent.
 */

export type ValidationDetail = { loc: (string | number)[]; msg: string; type?: string };

/** Raised when the backend returns a 4xx/5xx response. */
export class ApiError extends Error {
  status_code: number;
  detail: string | ValidationDetail[];
  code?: string;
  meta?: Record<string, unknown>;
  url?: string;

  constructor(params: {
    status_code: number;
    detail: string | ValidationDetail[];
    code?: string;
    meta?: Record<string, unknown>;
    url?: string;
  }) {
    super(typeof params.detail === 'string' ? params.detail : `HTTP ${params.status_code} error`);
    this.name = 'ApiError';
    this.status_code = params.status_code;
    this.detail = params.detail;
    this.code = params.code;
    this.meta = params.meta;
    this.url = params.url;
  }
}

/** Raised when the backend can't be reached at all (no response). */
export class NetworkError extends Error {
  constructor(message = "Can't reach the backend") {
    super(message);
    this.name = 'NetworkError';
  }
}

// Friendly messages for domain error codes (backend code -> user-facing text).
export const FRIENDLY_TEMPLATES: Record<string, string> = {
  // Projects
  DUPLICATE_PROJECT_NAME:
    "Project name '{project_name}' already exists. Please choose a different name and try again.",
  PROJECT_NOT_FOUND: "That project can't be found. It may have been deleted—try refreshing.",
  INVALID_PROJECT_CONFIGURATION:
    "This project's configuration is invalid. Please review the settings.",
  // Dataset / files
  INVALID_FILE:
    'That file looks invalid (empty, wrong type, or corrupted). Please upload a valid file.',
  INVALID_ENRICHMENT_COLUMN:
    'Your enrichment column selection is invalid. Please check the required columns.',
  PROJECT_DATASET_NOT_FOUND:
    "That dataset can't be found. It may have been removed—try refreshing.",
  // URLs
  URL_NOT_FOUND: "That URL entry can't be found. It may have been deleted—try refreshing.",
  DUPLICATE_URL: 'That URL is already in this project.',
  // Infrastructure
  DATABASE_FAILURE:
    'Database error. Please try again. If it keeps happening, the server may be down.',
  API_KEY_NOT_CONFIGURED:
    'Missing or invalid API key. Please enter your OpenAI and Jina API keys via the "API Keys" button.',
  // External APIs
  EXTERNAL_SCRAPER_ERROR:
    'Scraper service is having issues right now. Please try again in a moment.',
  SCRAPER_CREDITS_EXHAUSTED:
    'Your Jina API key has no credits remaining. Top up at jina.ai/api-dashboard or enter a different key via the "API Keys" button.',
  SCRAPER_API_KEY_INVALID:
    'Jina rejected your API key. Please check the key entered via the "API Keys" button.',
  OPENAI_TOKEN_LIMIT_EXCEEDED:
    'This request is too large for the AI to process. Try fewer URLs or smaller content.',
  // Enrichment
  DUPLICATE_ENRICHMENT_NAME:
    'That enrichment name already exists. Please choose a different name.',
  DUPLICATE_COLUMN_NAME:
    'That column name already exists. Please choose a different column name.',
  ENRICHMENT_NOT_FOUND: "That enrichment can't be found. It may have been deleted—try refreshing.",
  EMPTY_ENRICHMENT_FIELD:
    "The following fields cannot be empty or whitespace only: '{field_names_str}'. Please fill in all required fields.",
  INCOMPLETE_ENRICHMENT_CONFIG:
    "Result format '{result_format}' requires the following fields to be filled: '{fields_str}'",
  NO_LEADS_TO_ENRICH:
    'Cannot run enrichment: no leads provided. Please add leads before running enrichment.',
  // Jobs
  JOB_NOT_FOUND: "That job can't be found. It may have been deleted—try refreshing.",
  JOB_ALREADY_RUNNING: 'Still running enrichment on all leads... please wait.',
  // Generic / server fallback
  UNEXPECTED_INTERNAL_ERROR: 'Something went wrong on the server. Please try again.',
};

/** Codes whose server-side message is already the most useful thing to show. */
export const PASS_THROUGH_CODES = new Set(['OPENAI_REQUEST_FAILED']);

export const STATUS_FALLBACK_MESSAGES: Record<number, string> = {
  400: 'Bad request. Please check your input and try again.',
  401: "You're not authenticated. Please log in again.",
  403: "You don't have permission to do that.",
  404: 'Not found.',
  409: 'Conflict. This item may already exist.',
  413: 'Request too large. Try reducing the input size.',
  422: 'Some inputs are invalid. Please correct them and try again.',
  500: 'Server error. Please try again.',
  502: 'Upstream service error. Please try again soon.',
  503: 'Service temporarily unavailable. Please try again soon.',
  504: 'Request timed out. Please try again.',
};

function fillTemplate(template: string, meta: Record<string, unknown> = {}): string {
  return template.replace(/\{(\w+)\}/g, (match, key) =>
    key in meta ? String(meta[key]) : match,
  );
}

/** Turn any thrown error into a single user-facing message string. */
export function errorToMessage(err: unknown): string {
  if (err instanceof NetworkError) {
    return "Can't reach the backend. Check that the API server is running and reachable.";
  }
  if (err instanceof ApiError) {
    // 422 validation errors with a list detail
    if (err.status_code === 422 && Array.isArray(err.detail)) {
      const lines = err.detail.map((item) => {
        const loc = (item.loc || []).map(String).join(' → ');
        return `${loc}: ${item.msg || 'Invalid value'}`;
      });
      return `Please fix the highlighted input errors:\n${lines.join('\n')}`;
    }
    // Errors whose whole value is what the upstream service said: "temperature
    // is not supported with this model" and "you exceeded your current quota"
    // need different things done about them, and a house sentence covering
    // both would help with neither.
    if (err.code && PASS_THROUGH_CODES.has(err.code) && typeof err.detail === 'string') {
      return err.detail;
    }
    if (err.code) {
      const template = FRIENDLY_TEMPLATES[err.code];
      if (template) return fillTemplate(template, err.meta || {});
      return `${err.code}: ${err.message}`;
    }
    return (
      STATUS_FALLBACK_MESSAGES[err.status_code] ?? 'Request failed. Please try again.'
    );
  }
  if (err instanceof Error) return err.message;
  return 'An unexpected error occurred.';
}

/** True when the error is a missing/invalid API key (so the UI can prompt for keys). */
export function isApiKeyError(err: unknown): boolean {
  return err instanceof ApiError && err.code === 'API_KEY_NOT_CONFIGURED';
}
