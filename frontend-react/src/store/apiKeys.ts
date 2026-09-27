/**
 * API key store.
 *
 * Keys are entered by the user in the UI and persisted to localStorage. They are
 * read both by React components (via the useApiKeys hook, which subscribes for
 * reactivity) and by the axios request interceptor (via getApiKeys, outside React).
 *
 * Security note: keys live in localStorage (readable by page JavaScript) and are
 * sent to the backend over HTTPS. Acceptable for this tool; documented in README.
 */

import { useSyncExternalStore } from 'react';

const OPENAI_STORAGE_KEY = 'lead_gen_openai_key';
const JINA_STORAGE_KEY = 'lead_gen_jina_key';
const GOOGLE_STORAGE_KEY = 'lead_gen_google_key';

export interface ApiKeysState {
  openaiKey: string;
  jinaKey: string;
  /** Optional: only location searches use it, to search Google Places. */
  googleKey: string;
}

function readFromStorage(): ApiKeysState {
  try {
    return {
      openaiKey: localStorage.getItem(OPENAI_STORAGE_KEY) ?? '',
      jinaKey: localStorage.getItem(JINA_STORAGE_KEY) ?? '',
      googleKey: localStorage.getItem(GOOGLE_STORAGE_KEY) ?? '',
    };
  } catch {
    return { openaiKey: '', jinaKey: '', googleKey: '' };
  }
}

let state: ApiKeysState = readFromStorage();
const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) listener();
}

/** Read the current keys synchronously (used by the axios interceptor). */
export function getApiKeys(): ApiKeysState {
  return state;
}

/** Persist and broadcast new keys. */
export function setApiKeys(next: ApiKeysState) {
  state = {
    openaiKey: next.openaiKey.trim(),
    jinaKey: next.jinaKey.trim(),
    googleKey: next.googleKey.trim(),
  };
  try {
    localStorage.setItem(OPENAI_STORAGE_KEY, state.openaiKey);
    localStorage.setItem(JINA_STORAGE_KEY, state.jinaKey);
    localStorage.setItem(GOOGLE_STORAGE_KEY, state.googleKey);
  } catch {
    /* ignore storage errors (e.g. private mode) */
  }
  emit();
}

/** Clear every key from memory and storage. */
export function clearApiKeys() {
  setApiKeys({ openaiKey: '', jinaKey: '', googleKey: '' });
}

/** True when both required keys (OpenAI and Jina) are present; Google is optional. */
export function hasBothKeys(s: ApiKeysState = state): boolean {
  return Boolean(s.openaiKey && s.jinaKey);
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** React hook exposing the current keys and mutators (reactive). */
export function useApiKeys() {
  const keys = useSyncExternalStore(subscribe, getApiKeys, getApiKeys);
  return {
    ...keys,
    hasKeys: hasBothKeys(keys),
    setKeys: setApiKeys,
    clearKeys: clearApiKeys,
  };
}
