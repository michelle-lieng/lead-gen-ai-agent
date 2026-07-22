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

export interface ApiKeysState {
  openaiKey: string;
  jinaKey: string;
}

function readFromStorage(): ApiKeysState {
  try {
    return {
      openaiKey: localStorage.getItem(OPENAI_STORAGE_KEY) ?? '',
      jinaKey: localStorage.getItem(JINA_STORAGE_KEY) ?? '',
    };
  } catch {
    return { openaiKey: '', jinaKey: '' };
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
  state = { openaiKey: next.openaiKey.trim(), jinaKey: next.jinaKey.trim() };
  try {
    localStorage.setItem(OPENAI_STORAGE_KEY, state.openaiKey);
    localStorage.setItem(JINA_STORAGE_KEY, state.jinaKey);
  } catch {
    /* ignore storage errors (e.g. private mode) */
  }
  emit();
}

/** Clear both keys from memory and storage. */
export function clearApiKeys() {
  setApiKeys({ openaiKey: '', jinaKey: '' });
}

/** True when both keys are present. */
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
