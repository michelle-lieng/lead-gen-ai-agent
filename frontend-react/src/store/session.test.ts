import { beforeEach, describe, expect, it, vi } from 'vitest';

/** An in-memory Storage: all the session store touches of the browser. */
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

const globals = globalThis as { sessionStorage?: Storage; localStorage?: Storage };

/** The store reads the token once at load, so each test loads it fresh. */
async function load() {
  vi.resetModules();
  return import('./session');
}

beforeEach(() => {
  globals.sessionStorage = memoryStorage();
  globals.localStorage = memoryStorage();
});

describe('session store', () => {
  it('keeps the token for the tab and clears it', async () => {
    const session = await load();
    session.setToken('t1');
    expect(session.getToken()).toBe('t1');
    expect(sessionStorage.getItem('lead_gen_session')).toBe('t1');
    session.clearToken();
    expect(session.getToken()).toBe('');
    expect(sessionStorage.getItem('lead_gen_session')).toBeNull();
  });

  it('reads a token saved earlier in the tab', async () => {
    sessionStorage.setItem('lead_gen_session', 't2');
    expect((await load()).getToken()).toBe('t2');
  });

  it('is signed out when storage throws', async () => {
    const fail = () => {
      throw new Error('blocked');
    };
    globals.sessionStorage = { ...memoryStorage(), getItem: fail, setItem: fail, removeItem: fail };
    const session = await load();
    expect(session.getToken()).toBe('');
    expect(() => session.setToken('t')).not.toThrow();
    expect(() => session.clearToken()).not.toThrow();
  });

  it('removes keys saved by the old keys dialog', async () => {
    localStorage.setItem('lead_gen_openai_key', 'sk');
    localStorage.setItem('lead_gen_jina_key', 'jn');
    localStorage.setItem('lead_gen_google_key', 'gk');
    localStorage.setItem('other', 'keep');
    (await load()).clearLegacyKeys();
    expect(localStorage.getItem('lead_gen_openai_key')).toBeNull();
    expect(localStorage.getItem('lead_gen_jina_key')).toBeNull();
    expect(localStorage.getItem('lead_gen_google_key')).toBeNull();
    expect(localStorage.getItem('other')).toBe('keep');
  });

  it('ends the session only when the server says it has ended', async () => {
    const session = await load();
    expect(session.endsSession(401, 'SESSION_REQUIRED')).toBe(true);
    // Jina rejecting the server's key is a 401 too, but not about the session.
    expect(session.endsSession(401, 'SCRAPER_API_KEY_INVALID')).toBe(false);
    expect(session.endsSession(401, 'INVALID_PASSWORD')).toBe(false);
    expect(session.endsSession(401, undefined)).toBe(false);
    expect(session.endsSession(503, 'AUTH_NOT_CONFIGURED')).toBe(false);
  });

  it('needs OpenAI and Jina, not Google', async () => {
    const session = await load();
    expect(session.hasRequiredKeys({ openai: true, jina: true, google: false })).toBe(true);
    expect(session.hasRequiredKeys({ openai: true, jina: false, google: true })).toBe(false);
    expect(session.hasRequiredKeys(undefined)).toBe(false);
  });
});
