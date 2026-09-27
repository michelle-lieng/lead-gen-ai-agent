import { beforeEach, describe, expect, it, vi } from 'vitest';

/** An in-memory Storage: all the sidebar store touches of the browser. */
function memoryStorage(): Storage {
  const store = new Map<string, string>();
  return {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => void store.set(key, String(value)),
    removeItem: (key: string) => void store.delete(key),
    clear: () => store.clear(),
    key: (index: number) => [...store.keys()][index] ?? null,
    get length() {
      return store.size;
    },
  };
}

const globals = globalThis as { localStorage?: Storage };

/** The store reads storage once at load, so each test loads it fresh. */
async function load() {
  vi.resetModules();
  return import('./sidebar');
}

beforeEach(() => {
  globals.localStorage = memoryStorage();
});

describe('sidebar store', () => {
  it('starts expanded and remembers collapsing', async () => {
    const sidebar = await load();
    expect(sidebar.isSidebarCollapsed()).toBe(false);
    sidebar.setSidebarCollapsed(true);
    expect(sidebar.isSidebarCollapsed()).toBe(true);
    expect(localStorage.getItem('lead_gen_sidebar_collapsed')).toBe('1');
    sidebar.setSidebarCollapsed(false);
    expect(localStorage.getItem('lead_gen_sidebar_collapsed')).toBeNull();
  });

  it('reads the saved choice on load', async () => {
    localStorage.setItem('lead_gen_sidebar_collapsed', '1');
    const sidebar = await load();
    expect(sidebar.isSidebarCollapsed()).toBe(true);
  });

  it('counts storage that throws as expanded and still toggles', async () => {
    const throwing = memoryStorage();
    throwing.getItem = () => {
      throw new Error('blocked');
    };
    throwing.setItem = () => {
      throw new Error('blocked');
    };
    globals.localStorage = throwing;
    const sidebar = await load();
    expect(sidebar.isSidebarCollapsed()).toBe(false);
    sidebar.setSidebarCollapsed(true);
    expect(sidebar.isSidebarCollapsed()).toBe(true);
  });
});
