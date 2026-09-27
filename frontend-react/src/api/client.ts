/**
 * Axios instance with interceptors:
 *   - request: send the session token as `Authorization: Bearer <token>`
 *   - response: an ended session (401 SESSION_REQUIRED) clears the token, so
 *     the password gate shows again, and
 *     backend errors are normalised into ApiError / NetworkError
 */

import axios, { AxiosError, AxiosResponse } from 'axios';
import { BACKEND_URL, REQUEST_TIMEOUT_MS } from '../config';
import { clearToken, endsSession, getToken } from '../store/session';
import { ApiError, NetworkError, ValidationDetail } from './errors';

export const http = axios.create({
  baseURL: BACKEND_URL,
  timeout: REQUEST_TIMEOUT_MS,
  headers: { Accept: 'application/json' },
});

// Every route but login and health needs the session token.
http.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.set('Authorization', `Bearer ${token}`);
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

      // The session is missing, expired or forged: back to the password gate.
      if (endsSession(status, code)) clearToken();

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
