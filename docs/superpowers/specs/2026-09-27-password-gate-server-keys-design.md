# Password gate and server-side API keys

## Intent

The app is used by one team through a shared deployment. Two things change:

1. **Keys live on the server.** OpenAI, Jina and Google Places keys are read
   from the backend's environment (`backend/.env` locally, env vars on
   Render). Nobody enters keys in the browser any more; the API keys dialog
   and its localStorage store are removed.
2. **One shared password guards the whole app.** Nothing in the app is shown,
   and no `/api` route answers, until the password is entered. Signing in
   lasts until the browser tab closes.

Success: opening the app shows only a password screen; the right password
shows the app as it is today with no key setup; the wrong one does not; any
`/api` call without a valid session gets 401; searches and columns run on the
server's keys.

## Constraints

- Frontend and backend are on different origins (Vercel or Render static
  frontend calling the Render backend directly). The design must not depend
  on cookies or credentialed CORS.
- The password and signing secret come from the environment only, never from
  source code or the frontend bundle.
- The frontend bundle is public; it holds no secret.
- Existing error shape stays: `{detail, code, meta}` with a stable `code`.

## Design

### Settings (`backend/app/config.py`)

| Env var                  | Purpose                                                    |
|--------------------------|------------------------------------------------------------|
| `APP_PASSWORD`           | The shared password.                                       |
| `AUTH_SECRET`            | Key that signs session tokens.                             |
| `OPENAI_API_KEY`         | Already declared, now used.                                |
| `JINA_API_KEY`           | Already declared, now used.                                |
| `GOOGLE_PLACES_API_KEY`  | New. Optional: without it, location searches use the web. |

Changing `APP_PASSWORD` or `AUTH_SECRET` invalidates every session: tokens
are signed with a key derived from both.

### Session tokens (`backend/app/services/auth_service.py`)

- A token is `<expiry unix seconds>.<HMAC-SHA256 hex of the expiry>`, signed
  with a key derived from `AUTH_SECRET` and `APP_PASSWORD`.
- Lifetime: 12 hours. This is a backstop only; the tab-scoped storage is what
  ends a session in practice.
- `check_password(candidate)` compares with `hmac.compare_digest`.
- `issue_token(now)` and `verify_token(token, now)`; verify rejects a bad
  signature, a malformed token and an expired one.
- Auth is **not configured** when `APP_PASSWORD` or `AUTH_SECRET` is empty.

### Endpoints (`backend/app/api/routes/auth.py`, prefix `/api/auth`)

- `POST /api/auth/login` `{password}` → `{token}`.
  - Wrong password: wait 1 second, then 401 `INVALID_PASSWORD`.
  - Auth not configured: 503 `AUTH_NOT_CONFIGURED`.
- `GET /api/auth/status` (requires a valid session) →
  `{openai: bool, jina: bool, google: bool}`: which keys the server has.

### Guard (middleware in `backend/app/main.py`)

- Every request whose path starts with `/api` needs
  `Authorization: Bearer <token>` that verifies, except `/api/health` and
  `POST /api/auth/login`. `OPTIONS` preflight requests pass through.
- No or bad token: 401 `SESSION_REQUIRED`.
- Auth not configured: 503 `AUTH_NOT_CONFIGURED` on every guarded route.
  The API never runs open.
- The middleware is registered so its responses still carry CORS headers,
  as the existing error middleware is.

### Keys (`backend/app/api/deps.py`)

- `get_api_keys()` builds `ApiKeys` from settings instead of the
  `X-OpenAI-Key`, `X-Jina-Key` and `X-Google-Key` headers. The headers are
  no longer read.
- `require_openai`, `require_jina` and `require_google` are unchanged, so a
  missing key still raises `API_KEY_NOT_CONFIGURED`. Its message now says to
  set the env var on the server.
- Routes are unchanged.

### Frontend

- **Session store (`store/session.ts`)**: token in `sessionStorage` under one
  key; `getToken`, `setToken`, `clearToken`, and a hook for signed-in state.
  Storage failures fall back to signed out.
- **HTTP client (`api/client.ts`)**: sends `Authorization: Bearer <token>`
  instead of the key headers. A 401 response clears the token, which shows
  the gate.
- **Gate (`components/auth/PasswordGate.tsx`)**: wraps the router in
  `App.tsx`. Signed out: a full-screen password form with an error line for a
  wrong password and for an unconfigured server. Signed in: the app.
- **Server keys (`hooks/useServerKeys.ts`)**: reads `/api/auth/status`
  through React Query and returns `{hasKeys, googleKey}`, where `hasKeys`
  means OpenAI and Jina are both set and `googleKey` is a boolean. It
  replaces `useApiKeys` at every usage site:
  - `Project.tsx` (example-prompt writing, `requireKeys()` before a run);
  - `Sidebar.tsx` (status line);
  - `EnquiryPanel.tsx` (Google note);
  - `useRegisterRun.ts` (whether a location search uses Places).
- **Before a run**: `requireKeys()` becomes a check against the server keys.
  When a key is missing, a toast says to set it in the backend's env.
- **Sidebar**: the "API keys" button becomes **Sign out** (clears the token).
  The status line still shows which keys the server has.
- **Removed**:
  - `components/apiKeys/ApiKeys.tsx`;
  - `store/apiKeys.ts`;
  - the key interceptor;
  - the three `lead_gen_*_key` localStorage entries, cleared once on load so
    old keys do not linger.
- **Docs**: the README "bring your own keys" section is replaced by the
  env-var setup; `backend/env.example` lists the new variables; `render.yaml`
  declares them as `sync: false`.

### Local setup

`backend/.env` gets:
- `APP_PASSWORD`, set to the password the user chose;
- a random `AUTH_SECRET`;
- an empty `GOOGLE_PLACES_API_KEY` for the user to fill in.

The file is gitignored.

## Error handling

| Case                               | Result                                                |
|------------------------------------|-------------------------------------------------------|
| Wrong password                     | 401 `INVALID_PASSWORD` after 1s; the gate says "That password is not right." |
| No/expired/forged token            | 401 `SESSION_REQUIRED`; the frontend clears the token and shows the gate. |
| Server missing password or secret  | 503 `AUTH_NOT_CONFIGURED`; the gate says the server has no password set. |
| Server missing an API key          | 500 `API_KEY_NOT_CONFIGURED` on the run that needs it, as today, worded for the server. |

## Testing

- **pytest**
  - Token issue/verify round trip; rejection of an expired, forged or
    malformed token, and of a token signed before the password changed.
  - `check_password` accepts and rejects.
  - Login returns a token; a wrong password gives 401; unconfigured auth
    gives 503.
  - The guard: an `/api` route without a token gives 401 and with a token
    passes; `/api/health`, login and `OPTIONS` pass without a token;
    unconfigured auth gives 503.
  - `get_api_keys` returns the settings' keys and ignores the headers.
  - `/api/auth/status` reports which keys are set.
- **vitest**: the session store round trip and fallback when storage throws.
- **Browser**: gate shows first; wrong password errors; right password loads
  projects; Sign out returns to the gate; a new tab asks again.

## Out of scope

- Per-user accounts, roles, or audit of who ran what.
- Lockout after repeated failures (the 1-second delay is the only throttle).
- Putting frontend and backend on one domain.
