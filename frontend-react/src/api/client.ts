/**
 * Axios instance with interceptors:
 *   - request: inject the user's API keys as X-OpenAI-Key / X-Jina-Key / X-Google-Key headers
 *   - response: normalise backend errors into ApiError / NetworkError
 */

import axios, { AxiosError, AxiosResponse } from 'axios';
import { BACKEND_URL, REQUEST_TIMEOUT_MS } from '../config';
import { getApiKeys } from '../store/apiKeys';
import { ApiError, NetworkError, ValidationDetail } from './errors';

export const http = axios.create({
  baseURL: BACKEND_URL,
  timeout: REQUEST_TIMEOUT_MS,
  headers: { Accept: 'application/json' },
});

// Inject API keys on every request (harmless where the backend ignores them).
http.interceptors.request.use((config) => {
  const { openaiKey, jinaKey, googleKey } = getApiKeys();
  if (openaiKey) config.headers.set('X-OpenAI-Key', openaiKey);
  if (jinaKey) config.headers.set('X-Jina-Key', jinaKey);
  if (googleKey) config.headers.set('X-Google-Key', googleKey);
  return config;
});

// Normalise errors so callers always deal with ApiError / NetworkError.
http.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response) {
      const { status, data } = error.response;
      let detail: string | ValidationDetail[] = `HTTP ${status} error`;
      let code: string | undefined;
      let meta: Record<string, unknown> | undefined;

      if (data && typeof data === 'object') {
        const body = data as Record<string, unknown>;
        if (body.detail !== undefined) detail = body.detail as string | ValidationDetail[];
        if (typeof body.code === 'string') code = body.code;
        if (body.meta && typeof body.meta === 'object') {
          meta = body.meta as Record<string, unknown>;
        }
      } else if (typeof data === 'string' && data) {
        detail = data;
      }

      return Promise.reject(
        new ApiError({ status_code: status, detail, code, meta, url: error.config?.url }),
      );
    }
    // No response => couldn't reach the server.
    return Promise.reject(new NetworkError(error.message));
  },
);

/** Parse a download filename from a Content-Disposition header. */
export function parseFilename(disposition: string | undefined, fallback: string): string {
  if (!disposition) return fallback;
  const match = /filename\*?=(?:UTF-8'')?"?([^;"]+)"?/i.exec(disposition);
  return match ? decodeURIComponent(match[1]).trim() : fallback;
}
