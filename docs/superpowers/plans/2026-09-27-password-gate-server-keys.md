# Password Gate and Server-Side Keys Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The whole app sits behind one shared password (a session lasts until the tab closes), and the OpenAI, Jina and Google Places keys are read from the backend's environment instead of being entered in the browser.

**Architecture:**
- `POST /api/auth/login` swaps the password for an HMAC-signed, expiring token.
- An HTTP middleware rejects every other `/api` request that lacks `Authorization: Bearer <token>`.
- `get_api_keys()` reads keys from settings, so no route changes.
- The frontend keeps the token in `sessionStorage`, sends it on every request, and shows a full-screen password gate whenever it has none. It learns which keys the server has from `GET /api/auth/status`.

**Tech Stack:** FastAPI, pydantic-settings, stdlib `hmac`/`hashlib`, pytest with FastAPI `TestClient`; React 18, axios, React Query, Vitest.

**Spec:** `docs/superpowers/specs/2026-09-27-password-gate-server-keys-design.md`

## Global Constraints

- **Env var names:**
  - `APP_PASSWORD`
  - `AUTH_SECRET`
  - `OPENAI_API_KEY`
  - `JINA_API_KEY`
  - `GOOGLE_PLACES_API_KEY`
- **Token format** is `<expiry unix seconds>.<HMAC-SHA256 hex of the expiry string>`, lifetime 12 hours.
  - The signing key is derived from both `AUTH_SECRET` and `APP_PASSWORD`, so changing either invalidates every token.
- **Error codes:**
  - `INVALID_PASSWORD` (401, after a 1 second wait)
  - `SESSION_REQUIRED` (401)
  - `AUTH_NOT_CONFIGURED` (503)
  - `API_KEY_NOT_CONFIGURED` (500, unchanged)
- **Error body shape** stays `{detail, code}` (plus `meta` when present).
- **Open without a token:**
  - `/api/health`
  - `POST /api/auth/login`
  - every `OPTIONS` request
  - any path not under `/api/` (`/`, `/docs`, `/openapi.json`)
- **Unconfigured auth:** when `APP_PASSWORD` or `AUTH_SECRET` is empty, every guarded route answers 503. The API never runs open.
- **No secrets in the frontend bundle or in source files.** The password lives only in `backend/.env` (gitignored) and deploy env vars.
- **Session storage key:** `lead_gen_session` in `sessionStorage`.
- **Old localStorage keys** `lead_gen_openai_key`, `lead_gen_jina_key` and `lead_gen_google_key` are removed on app load.
- **Do not commit.** The user commits their own work; commit steps below are replaced by "leave uncommitted".

## Review Focus

1. **A 401 from the guard must still carry CORS headers**, or the browser hides it and the SPA reports "can't reach the backend". The guard must sit inside `CORSMiddleware`. Tested in Task 2.
2. **CORS preflight (`OPTIONS`) carries no Authorization header**, so blocking it would break every request. Tested in Task 2.
3. **The `Authorization` header in other casings or spacing** (`bearer x`, extra spaces) should still work. Tested in Task 2.
4. **A token with its expiry edited but its old signature kept** must fail (a forged extension). Tested in Task 1.
5. **Data from a previous session must not show after sign-out or after a 401.** The React Query cache is cleared on both, which the browser check in Task 5 verifies.

---

### Task 1: Settings, errors and session tokens

**Files:**
- Modify: `backend/app/config.py`
  - Add `app_password: Optional[str] = None`, `auth_secret: Optional[str] = None` and `google_places_api_key: Optional[str] = None`.
  - Rewrite the "API Keys" comment: keys are read from the environment and are required for runs.
- Modify: `backend/app/exceptions.py`. Add after `ApiKeyNotConfiguredError`, in the same style:
  - `InvalidPasswordError`: 401, `INVALID_PASSWORD`, default message `"That password is not right."`
  - `AuthNotConfiguredError`: 503, `AUTH_NOT_CONFIGURED`, default message `"This server has no password set. Set APP_PASSWORD and AUTH_SECRET in the backend's environment."`
- Create: `backend/app/services/auth_service.py`
- Test: `backend/tests/test_auth_service.py`

**Interfaces:**
- Produces (in `auth_service`), all reading `settings` at call time, never at import:
  - `TOKEN_LIFETIME_SECONDS = 12 * 60 * 60`
  - `auth_configured() -> bool`: both `settings.app_password` and `settings.auth_secret` are non-empty after strip.
  - `check_password(candidate: str) -> bool`: `hmac.compare_digest` against `settings.app_password`, compared exactly with no stripping; False when not configured.
  - `issue_token(now: float | None = None) -> str`
  - `verify_token(token: str | None, now: float | None = None) -> bool`: False for None, malformed, a bad signature, expired, or not configured.
  - Signing key: `hashlib.sha256(f"{auth_secret}\n{app_password}".encode()).digest()`.

- [ ] **Step 1: Write the failing tests** in `backend/tests/test_auth_service.py`.
  - Setup: a fixture monkeypatches `settings.app_password = "pw-1"` and `settings.auth_secret = "secret-1"`.

```python
def test_a_fresh_token_verifies(): assert verify_token(issue_token(now=1000), now=1001)
def test_an_expired_token_fails(): assert not verify_token(issue_token(now=1000), now=1000 + TOKEN_LIFETIME_SECONDS + 1)
def test_an_extended_expiry_with_the_old_signature_fails():
    expiry, signature = issue_token(now=1000).split(".")
    assert not verify_token(f"{int(expiry) + 3600}.{signature}", now=1001)
def test_malformed_tokens_fail(): for t in [None, "", "abc", "1.2.3", "x.y"]: assert not verify_token(t, now=0)
def test_changing_the_password_signs_everyone_out(monkeypatch):
    token = issue_token(now=1000); monkeypatch.setattr(settings, "app_password", "pw-2")
    assert not verify_token(token, now=1001)
def test_check_password(): assert check_password("pw-1") and not check_password("pw-2") and not check_password("")
def test_nothing_verifies_when_auth_is_not_configured(monkeypatch):
    token = issue_token(now=1000); monkeypatch.setattr(settings, "auth_secret", "")
    assert not auth_configured() and not verify_token(token, now=1001) and not check_password("pw-1")
```

- [ ] **Step 2: Run** `../.venv/Scripts/python -m pytest tests/test_auth_service.py -q` from `backend/`.
  - Expected: collection error, `No module named 'app.services.auth_service'`.
- [ ] **Step 3: Implement the settings fields, the two errors, and `auth_service.py`** per the Interfaces block.
- [ ] **Step 4: Run the same command.**
  - Expected: 7 passed. Then the whole backend suite: `../.venv/Scripts/python -m pytest -q`, all passing.
- [ ] **Step 5: Leave uncommitted.**

### Task 2: Login, status and the guard

**Files:**
- Create: `backend/app/api/routes/auth.py` (router; mounted at `/api/auth`)
- Create: `backend/app/api/auth_guard.py`
- Modify: `backend/app/models/schemas.py`. Add:
  - `LoginRequest(password: str)`
  - `LoginResponse(token: str)`
  - `ServerKeysResponse(openai: bool, jina: bool, google: bool)`
- Modify: `backend/app/main.py`
  - Import `auth` with the other routes and mount `app.include_router(auth.router, prefix="/api/auth", tags=["auth"])`.
  - Register `app.middleware("http")(require_session)` **after** `unhandled_errors_as_json` and **before** `app.add_middleware(CORSMiddleware, ...)`, so it stays inside CORS.
  - Update the CORS comment: the browser now sends `Authorization`, not key headers.
- Test: `backend/tests/test_auth_routes.py`

**Interfaces:**
- Consumes: Task 1 `auth_configured`, `check_password`, `issue_token`, `verify_token`, `InvalidPasswordError`, `AuthNotConfiguredError`.
- Produces:
  - `auth_guard.is_open(method: str, path: str) -> bool`. True for:
    - `OPTIONS`
    - `path == "/api/health"`
    - `POST` on `/api/auth/login`
    - any path that is neither `/api` nor starts with `/api/`
  - `auth_guard.bearer_token(header: str | None) -> str | None`: scheme matched case-insensitively, surrounding spaces stripped.
  - `async def require_session(request, call_next)`. When the path is not open:
    - if not `auth_configured()`, return JSONResponse 503 `{"detail": AuthNotConfiguredError().args[0], "code": "AUTH_NOT_CONFIGURED"}`;
    - if the token doesn't verify, return 401 `{"detail": "Your session has ended. Enter the password again.", "code": "SESSION_REQUIRED"}`.
  - `routes/auth.py`:
    - `FAILED_LOGIN_DELAY_SECONDS = 1.0`
    - `POST /login` (`LoginRequest` → `LoginResponse`) raises `AuthNotConfiguredError` when not configured. A wrong password awaits `asyncio.sleep(FAILED_LOGIN_DELAY_SECONDS)` and then raises `InvalidPasswordError`.
    - `GET /status` → `ServerKeysResponse`: each field is `bool((key or "").strip())` for `settings.openai_api_key`, `settings.jina_api_key` and `settings.google_places_api_key`.
  - HTTP: `GET /api/auth/status` → `{openai, jina, google}`, and `POST /api/auth/login` → `{token}`.

- [ ] **Step 1: Write the failing tests.**
  - `test_auth_routes.py` builds a minimal app rather than importing `app.main`, which would pull in the database:
    - `FastAPI()`, then `include_router(auth.router, prefix="/api/auth")`, then `GET /api/ping` → `{"ok": True}`, then `GET /api/health` → `{"status": "healthy"}`, then `GET /docs-like` → `{}`.
    - `app.middleware("http")(require_session)`.
    - `CORSMiddleware(allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])`, added last.
    - An `AppError` handler returning `{"detail": str(exc), "code": exc.code}` with `exc.status_code`.
  - Fixture: monkeypatch `settings.app_password="pw-1"`, `settings.auth_secret="secret-1"` and `auth.FAILED_LOGIN_DELAY_SECONDS=0`.

```python
def test_login_returns_a_token_that_opens_the_api(client):
    token = client.post("/api/auth/login", json={"password": "pw-1"}).json()["token"]
    assert client.get("/api/ping", headers={"Authorization": f"Bearer {token}"}).status_code == 200
def test_wrong_password_is_401(client):
    r = client.post("/api/auth/login", json={"password": "nope"}); assert (r.status_code, r.json()["code"]) == (401, "INVALID_PASSWORD")
def test_no_token_is_401_with_cors_headers(client):
    r = client.get("/api/ping", headers={"Origin": "http://app.test"})
    assert (r.status_code, r.json()["code"]) == (401, "SESSION_REQUIRED") and r.headers["access-control-allow-origin"]
def test_a_bad_token_is_401(client): assert client.get("/api/ping", headers={"Authorization": "Bearer 1.abc"}).status_code == 401
def test_scheme_case_and_spacing_are_tolerated(client, token): assert client.get("/api/ping", headers={"Authorization": f"  bearer   {token} "}).status_code == 200
def test_health_login_preflight_and_non_api_paths_are_open(client):
    assert client.get("/api/health").status_code == 200
    assert client.options("/api/ping", headers={"Origin": "http://app.test", "Access-Control-Request-Method": "GET"}).status_code == 200
    assert client.get("/docs-like").status_code == 200
def test_unconfigured_auth_is_503_everywhere(client, monkeypatch):
    monkeypatch.setattr(settings, "auth_secret", "")
    assert client.get("/api/ping").json()["code"] == "AUTH_NOT_CONFIGURED"
    assert client.post("/api/auth/login", json={"password": "pw-1"}).status_code == 503
def test_status_reports_which_keys_the_server_has(client, token, monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "sk-x"); monkeypatch.setattr(settings, "jina_api_key", " ")
    monkeypatch.setattr(settings, "google_places_api_key", None)
    assert client.get("/api/auth/status", headers={"Authorization": f"Bearer {token}"}).json() == {"openai": True, "jina": False, "google": False}
def test_status_needs_a_session(client): assert client.get("/api/auth/status").status_code == 401
```

- [ ] **Step 2: Run** `../.venv/Scripts/python -m pytest tests/test_auth_routes.py -q`.
  - Expected: collection error, `cannot import name 'auth'` / `No module named 'app.api.auth_guard'`.
- [ ] **Step 3: Implement the schemas, `auth_guard.py` and `routes/auth.py`, and register both in `main.py`,** per the Interfaces block.
- [ ] **Step 4: Run the file, then the whole suite.**
  - Expected: 9 passed, then all backend tests pass.
  - Also run `../.venv/Scripts/python -c "import app.main"` from `backend/`. Expected: exits 0.
- [ ] **Step 5: Leave uncommitted.**

### Task 3: Keys from the environment, and setup docs

**Files:**
- Modify: `backend/app/api/deps.py`
  - `get_api_keys() -> ApiKeys` takes no parameters and returns `ApiKeys(settings.openai_api_key, settings.jina_api_key, settings.google_places_api_key)`.
  - The `Header` import and the header docstring go.
  - The three `require_*` messages become `"<Name> API key is not set on the server. Set <ENV_VAR> in the backend's environment."`, with `<ENV_VAR>` being `OPENAI_API_KEY`, `JINA_API_KEY` or `GOOGLE_PLACES_API_KEY`.
- Modify: `backend/env.example`. Add `APP_PASSWORD=`, `AUTH_SECRET=`, and uncommented `OPENAI_API_KEY=`, `JINA_API_KEY=` and `GOOGLE_PLACES_API_KEY=`, each with a one-line comment. The `AUTH_SECRET` comment gives a generator command: `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
- Modify: `render.yaml`
  - `lead-gen-backend` envVars: replace the "keys are no longer required here" comment with `sync: false` entries for all five variables.
- Modify: `README.md`
  - Replace the "Bring-your-own API keys" bullet and the "🔑 API Keys" section (lines ~19-31) with "Keys and password", listing the five env vars and saying a session lasts until the tab closes.
  - Fix lines ~39, 43, 84 and 217 so they no longer say keys are entered in the UI.
- Modify: `backend/.env`, gitignored. Append only the lines that are missing:
  - `APP_PASSWORD=` set to the password the user gave in chat;
  - `AUTH_SECRET=` set to a fresh `secrets.token_urlsafe(32)`;
  - `GOOGLE_PLACES_API_KEY=` left empty.

  Write it with a script that never prints the file. Do not change or print existing values.
- Test: `backend/tests/test_api_keys.py`

**Interfaces:**
- Consumes: Task 1 `settings.google_places_api_key`.
- Produces: `get_api_keys() -> ApiKeys` with no request dependencies. Routes use it through `Depends(get_api_keys)` unchanged.

- [ ] **Step 1: Write the failing tests.**

```python
def test_keys_come_from_the_environment(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "sk-o"); monkeypatch.setattr(settings, "jina_api_key", "jn")
    monkeypatch.setattr(settings, "google_places_api_key", "gk")
    keys = get_api_keys(); assert (keys.require_openai(), keys.require_jina(), keys.require_google()) == ("sk-o", "jn", "gk")
def test_a_missing_key_names_its_env_var(monkeypatch):
    monkeypatch.setattr(settings, "google_places_api_key", None)
    with pytest.raises(ApiKeyNotConfiguredError, match="GOOGLE_PLACES_API_KEY"): get_api_keys().require_google()
def test_request_headers_are_not_read():
    assert list(inspect.signature(get_api_keys).parameters) == []
```

- [ ] **Step 2: Run** `../.venv/Scripts/python -m pytest tests/test_api_keys.py -q`.
  - Expected: 3 failed: `get_api_keys()` returns header defaults, the message lacks the env var, and the signature has 3 parameters.
- [ ] **Step 3: Implement `deps.py`, then the docs and `.env` changes.**
- [ ] **Step 4: Run the file, then the whole backend suite.**
  - Expected: all pass.
  - Then `grep -c "^APP_PASSWORD=\|^AUTH_SECRET=\|^GOOGLE_PLACES_API_KEY=" backend/.env` should print `3`.
- [ ] **Step 5: Leave uncommitted.**

### Task 4: Frontend session store and client

**Files:**
- Create: `frontend-react/src/store/session.ts`, modelled on the old `store/apiKeys.ts` module store with `useSyncExternalStore`.
- Create: `frontend-react/src/api/auth.ts`
- Modify: `frontend-react/src/api/types.ts`. Add `ServerKeys { openai: boolean; jina: boolean; google: boolean }`.
- Modify: `frontend-react/src/api/client.ts`
  - The request interceptor sets `Authorization: Bearer <getToken()>` when a token exists. The key headers and the `getApiKeys` import go.
  - The response interceptor calls `clearToken()` when `status === 401` and the request URL is not `/api/auth/login`, then rejects as today.
  - Update the header comment.
- Modify: `frontend-react/src/hooks/queryKeys.ts`. Add `serverKeys: ['server-keys'] as const`.
- Test: `frontend-react/src/store/session.test.ts`

**Interfaces:**
- Produces, in `store/session.ts`:
  - `SESSION_STORAGE_KEY = 'lead_gen_session'`
  - `getToken(): string`, which returns `''` when there is none or storage throws.
  - `setToken(token: string): void`
  - `clearToken(): void`, which notifies subscribers.
  - `useSignedIn(): boolean`
  - `clearLegacyKeys(): void`, which removes the three `lead_gen_*_key` entries from `localStorage` and swallows errors.
  - `hasRequiredKeys(keys: ServerKeys | undefined): boolean`, true when both `openai` and `jina` are set.
- Produces, in `api/auth.ts`:
  - `login(password: string): Promise<string>`, which posts `/api/auth/login` and returns the token.
  - `getServerKeys(): Promise<ServerKeys>`, a `GET /api/auth/status`.

- [ ] **Step 1: Write the failing tests** in `session.test.ts`.
  - Setup: in-memory `sessionStorage` and `localStorage` stubs installed in `beforeEach`, as in `viewState.test.ts`.
  - The store module is re-imported fresh per test with `vi.resetModules()` and a dynamic `import('./session')`, because it caches state at load.

```ts
it('keeps the token for the tab and clears it', async () => { const s = await load(); s.setToken('t1'); expect(s.getToken()).toBe('t1'); expect(sessionStorage.getItem('lead_gen_session')).toBe('t1'); s.clearToken(); expect(s.getToken()).toBe(''); });
it('reads a token saved earlier in the tab', async () => { sessionStorage.setItem('lead_gen_session', 't2'); expect((await load()).getToken()).toBe('t2'); });
it('is signed out when storage throws', async () => { (globalThis as any).sessionStorage = { getItem: () => { throw new Error('x'); }, setItem: () => { throw new Error('x'); }, removeItem: () => { throw new Error('x'); } }; const s = await load(); expect(s.getToken()).toBe(''); expect(() => s.setToken('t')).not.toThrow(); });
it('removes keys saved by the old keys dialog', async () => { localStorage.setItem('lead_gen_openai_key', 'sk'); localStorage.setItem('other', 'keep'); (await load()).clearLegacyKeys(); expect(localStorage.getItem('lead_gen_openai_key')).toBeNull(); expect(localStorage.getItem('other')).toBe('keep'); });
it('needs OpenAI and Jina, not Google', async () => { const s = await load(); expect(s.hasRequiredKeys({ openai: true, jina: true, google: false })).toBe(true); expect(s.hasRequiredKeys({ openai: true, jina: false, google: true })).toBe(false); expect(s.hasRequiredKeys(undefined)).toBe(false); });
```

- [ ] **Step 2: Run** `npx vitest run src/store/session.test.ts` from `frontend-react/`.
  - Expected: FAIL, `Failed to resolve import "./session"`.
- [ ] **Step 3: Implement `session.ts`, `auth.ts`, the type, the query key and `client.ts`.**
- [ ] **Step 4: Run the file.**
  - Expected: 5 passed. `npx tsc --noEmit -p .` still reports errors only at the `store/apiKeys` usage sites, which Task 5 removes.
- [ ] **Step 5: Leave uncommitted.**

### Task 5: Password gate, server keys in the UI, dialog removed

**Files:**
- Create: `frontend-react/src/components/auth/PasswordGate.tsx`
- Create: `frontend-react/src/hooks/useServerKeys.ts`
- Modify: `frontend-react/src/App.tsx`. Replace `ApiKeysProvider` with `PasswordGate`, still inside `NotificationsProvider` and wrapping `RouterProvider`.
- Modify: `frontend-react/src/pages/Project.tsx`
  - Replace `useApiKeysDialog`/`useApiKeys` with `const { hasKeys, requireKeys } = useServerKeys()`.
  - The call sites at ~:83, :384 and :417 stay the same shape. Update the ~:63 comment.
- Modify: `frontend-react/src/components/panel/EnquiryPanel.tsx:427`. `const { googleKey } = useServerKeys();`
- Modify: `frontend-react/src/hooks/useRegisterRun.ts:205, :440`
  - `getApiKeys().googleKey` becomes `queryClient.getQueryData<ServerKeys>(queryKeys.serverKeys)?.google`.
  - The `:228` line becomes `` `Set GOOGLE_PLACES_API_KEY in the backend's environment to also search Google Maps for ${location}.` ``
- Modify: `frontend-react/src/components/shell/Sidebar.tsx`
  - The prop `onOpenKeys` becomes `onSignOut`. Keys come from `useServerKeys()`.
  - The button's `<b>` becomes `Sign out`, with `aria-label="Sign out"`.
  - Status line:
    - When `hasKeys`: `OpenAI and Jina set${googleKey ? ' · Google Places on' : ''}`.
    - Otherwise: `Server is missing OpenAI or Jina key`.
  - Update the header comment at ~:6.
- Modify: `frontend-react/src/components/shell/AppShell.tsx`
  - Drop `useApiKeysDialog`.
  - `onSignOut={() => { clearToken(); queryClient.clear(); }}`
- Modify: `frontend-react/src/api/errors.ts`
  - New `API_KEY_NOT_CONFIGURED` template: `"The server is missing an API key. Add it to the backend's environment and restart the backend."`
  - Reword the Jina templates (`SCRAPER_CREDITS_EXHAUSTED`, `SCRAPER_API_KEY_INVALID`) so they say to change `JINA_API_KEY` in the backend's environment instead of "via the API Keys button".
  - Add `INVALID_PASSWORD: 'That password is not right.'` and `SESSION_REQUIRED: 'Your session has ended. Enter the password again.'`
  - Add `AUTH_NOT_CONFIGURED: "This server has no password set. Set APP_PASSWORD and AUTH_SECRET in the backend's environment."`
- Modify: `frontend-react/src/styles/app.css`. Add `.gate` styles: a centred card on `var(--bg)`, using the existing tokens and the existing `Field` and `Button` primitives.
- Delete: `frontend-react/src/components/apiKeys/ApiKeys.tsx`, `frontend-react/src/store/apiKeys.ts`

**Interfaces:**
- Consumes: Task 4 (`useSignedIn`, `setToken`, `clearToken`, `clearLegacyKeys`, `hasRequiredKeys`, `login`, `getServerKeys`, `queryKeys.serverKeys`, `ServerKeys`) and Task 2's HTTP contract.
- Produces:
  - `useServerKeys(): { hasKeys: boolean; googleKey: boolean; requireKeys: () => boolean }`
    - It uses `useQuery({ queryKey: queryKeys.serverKeys, queryFn: getServerKeys, enabled: useSignedIn() })`.
    - `requireKeys()` returns `hasKeys`. When false it calls `notify('Set OPENAI_API_KEY and JINA_API_KEY in the backend\'s environment before running anything.', 'warning')`.
  - `PasswordGate({ children })`:
    - It calls `clearLegacyKeys()` once on mount.
    - Signed out: a form with a password `Field` (`autoFocus`, `autoComplete="current-password"`) and an `Enter` button that is disabled while empty or submitting. The error line uses `errorToMessage(err)`.
    - On success: `setToken(token)`.
    - When `useSignedIn()` turns false while signed in (a 401 or Sign out), call `queryClient.clear()` so no data from the old session remains.

- [ ] **Step 1: Run** `npx tsc --noEmit -p .`.
  - Expected: errors only where `store/apiKeys` / `components/apiKeys` are still imported. This is the RED for this wiring task; its behaviour is covered by Task 4's unit tests and the browser checks in Step 4.
- [ ] **Step 2: Implement every file above and delete the two files.**
- [ ] **Step 3: Run** `npx tsc --noEmit -p .` and `npx vitest run`.
  - Expected: tsc clean and all tests pass.
  - `grep -rn "apiKeys\|X-OpenAI-Key\|getApiKeys" src` should find nothing.
- [ ] **Step 4: Browser check.** The user's backend runs with `--reload` on :8000 and the frontend on :5173.
  - Step 4a: load `/`. Expected: only the password gate, and `GET /api/projects/` is never requested.
  - Step 4b: submit a wrong password. Expected: "That password is not right." after about 1s.
  - Step 4c: submit the right password, read from `backend/.env` inside a script (never typed into chat or logged). Expected: the projects list loads with no key dialog. The sidebar shows "Sign out" and the key status.
  - Step 4d: open a project. Expected: the grid and chat load, and example prompts appear if keys exist.
  - Step 4e: click Sign out. Expected: back to the gate, and the React Query cache is empty (`queryClient` has no `projects` data).
  - Step 4f: set `sessionStorage.lead_gen_session` to a forged value and reload. Expected: the first API call gets 401, the token is cleared, and the gate shows.
  - Step 4g: reset the viewport and sign out at the end.
- [ ] **Step 5: Leave uncommitted.**
