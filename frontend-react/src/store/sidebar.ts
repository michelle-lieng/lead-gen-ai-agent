/**
 * Sidebar store: whether the projects sidebar is collapsed on wide screens.
 *
 * It lives in localStorage, so the choice survives moving between pages (each
 * page mounts its own shell) and reloads. Storage that throws counts as
 * expanded, and a failed write still collapses the sidebar for this page.
 */

import { useSyncExternalStore } from 'react';

export const SIDEBAR_STORAGE_KEY = 'lead_gen_sidebar_collapsed';

function readCollapsed(): boolean {
  try {
    return localStorage.getItem(SIDEBAR_STORAGE_KEY) === '1';
  } catch {
    return false;
  }
}

let collapsed = readCollapsed();
const listeners = new Set<() => void>();

export function isSidebarCollapsed(): boolean {
  return collapsed;
}

export function setSidebarCollapsed(next: boolean): void {
  collapsed = next;
  try {
    if (next) localStorage.setItem(SIDEBAR_STORAGE_KEY, '1');
    else localStorage.removeItem(SIDEBAR_STORAGE_KEY);
  } catch {
    // Remembered for this page only.
  }
  for (const listener of listeners) listener();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function useSidebarCollapsed(): boolean {
  return useSyncExternalStore(subscribe, isSidebarCollapsed);
}
