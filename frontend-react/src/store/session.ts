/**
 * Session store: the token from signing in with the shared password.
 *
 * It lives in sessionStorage, so it ends when the tab closes. It is read by
 * React (useSignedIn, which subscribes) and by the axios interceptor
 * (getToken, outside React). Storage that throws counts as signed out.
 */

import { useSyncExternalStore } from 'react';
import type { ServerKeys } from '../api/types';

export const SESSION_STORAGE_KEY = 'lead_gen_session';

/** Where the removed API keys dialog kept keys in this browser. */
const LEGACY_KEY_ENTRIES = ['lead_gen_openai_key', 'lead_gen_jina_key', 'lead_gen_google_key'];

function readToken(): string {
  try {
    return sessionStorage.getItem(SESSION_STORAGE_KEY) ?? '';
  } catch {
    return '';
  }
}

let token = readToken();
const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) listener();
}

/** The current token, or '' when signed out. */
export function getToken(): string {
  return token;
}

export function setToken(next: string): void {
  token = next;
  try {
    sessionStorage.setItem(SESSION_STORAGE_KEY, next);
  } catch {
    /* kept in memory for this page only */
  }
  emit();
}

export function clearToken(): void {
  token = '';
  try {
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
  } catch {
    /* nothing stored to remove */
  }
  emit();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

const signedIn = () => token !== '';

/** True while this tab holds a session token (reactive). */
export function useSignedIn(): boolean {
  return useSyncExternalStore(subscribe, signedIn, signedIn);
}

/** Remove API keys the old keys dialog left in this browser. */
export function clearLegacyKeys(): void {
  for (const key of LEGACY_KEY_ENTRIES) {
    try {
      localStorage.removeItem(key);
    } catch {
      /* unreadable storage holds nothing to clear */
    }
  }
}

/**
 * True when an error response means this tab's session has ended. Other 401s
 * (a wrong password, Jina rejecting the server's key) leave the session alone.
 */
export function endsSession(status: number, code: string | undefined): boolean {
  return status === 401 && code === 'SESSION_REQUIRED';
}

/** Runs need OpenAI and Jina on the server; Google Places is optional. */
export function hasRequiredKeys(keys: ServerKeys | undefined): boolean {
  return Boolean(keys?.openai && keys?.jina);
}
