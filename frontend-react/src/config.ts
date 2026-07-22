/**
 * Resolves the backend API base URL.
 *
 * Priority:
 *   1. window.__BACKEND_URL__  — injected at runtime in production (config.js)
 *   2. import.meta.env.VITE_BACKEND_URL — build-time env for local dev
 *   3. http://localhost:8000   — sensible default for local dev
 *
 * A trailing slash is stripped so `${BASE_URL}${path}` never doubles up.
 */
function resolveBackendUrl(): string {
  const runtime =
    typeof window !== 'undefined' && window.__BACKEND_URL__
      ? window.__BACKEND_URL__
      : '';
  const url = runtime || import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
  return url.replace(/\/+$/, '');
}

export const BACKEND_URL = resolveBackendUrl();

/** Long timeout (ms) — AI/scraping operations can take several minutes. */
export const REQUEST_TIMEOUT_MS = 600_000;
