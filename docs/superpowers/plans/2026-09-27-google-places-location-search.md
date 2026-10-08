# Google Places Location Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When a chat message names a location and the user has entered a Google Places key, search Google Places for businesses there first, then run the existing web search. Places results become ordinary leads plus an Address column.

**Architecture:**
- **Interpreter.** It gains a `location` field.
- **New Places service.** `places_service` calls Places Text Search (New) with the Pro field mask only, fetches up to 3 pages, and drops permanently-closed businesses.
- **Saving results.** Businesses are saved as `SerpLead`s under one "source" `SerpUrl` per query (`google-places:<query>`). They then flow through the existing aggregate → `merge_serp_leads` path, and a new fixed `address` column on `merged_results` is filled.
- **Frontend.** It gets an optional third key (`X-Google-Key`). `runFind` adds a Places step between the brief and the web queries.

**Tech Stack:** FastAPI, SQLAlchemy/Postgres, httpx (already a dependency), pytest (`backend/tests`), React 18 + TS + axios.

**Spec:** The design approved in chat on 2026-09-27, restated here:
- API: Places API (New) Text Search, **Pro fields only** (name, address, business status). No website or phone.
- Places first, then the existing web search; results merged by the existing name normalization.
- The key is entered in the app, optional. With no key, a location search runs the web search only and the chat says so once per message.
- Each Places search is one source; an Address column is added.
- Chat lines: `Google Places · <query>`, then `<N> businesses found on Google Maps · <new> new, <existing> already in the table.`

## Status (updated for commits `e3946fd`, `9380337`)

Your commits `e3946fd` "frontend changes" and `9380337` "backend route changes" contain everything built so far, so **BASE for the remaining work is `9380337`**. At that commit `pytest -q` → 19 passed.

| Task | State at `9380337` |
|---|---|
| 1. Interpreter reports the location | **Done:** `location` in `MessagePlan`/`build_plan`/`MessagePlanResponse`, prompt item 3, `address` in `RESERVED_COLUMNS` |
| 2. Places client | **Done:** `places_service.py` (`Place`, `parse_places`, `search_places`, `PLACES_URL`, `FIELD_MASK`), `GooglePlacesRequestError` |
| 3. Save Places results | **Partly done:** `new_place_names` and its 2 tests are in. Still to do: `save_places`, the `address` column, the `X-Google-Key` header, schemas, `POST /places` (Steps 4–7) |
| 4. Frontend key + Address column | Not started |
| 5. Places step in the chat | Not started |

The commit steps for Tasks 1–3 are covered by those two commits. The remaining commit steps still apply only if you ask.

## Global Constraints

- **Endpoint:** `POST https://places.googleapis.com/v1/places:searchText`.
- **Headers:** `X-Goog-Api-Key: <key>` and `X-Goog-FieldMask: places.displayName,places.formattedAddress,places.businessStatus,nextPageToken`. The field mask must never include websiteUri, phone or rating: those move the request to the Enterprise SKU (1,000 free/month instead of 5,000).
- **Paging:** body `{"textQuery": <query>, "pageSize": 20}`, plus `"pageToken"` on later pages. At most 3 requests per search (Google caps results at 60).
- **Closed businesses:** skip places whose `businessStatus == "CLOSED_PERMANENTLY"`, and places with no `displayName.text`.
- **Source row:** the source `SerpUrl.link` is `google-places:<query>`, and it is reused if it already exists (links are unique per project). Its `status` is `"processed"`, so `generate_leads` (which takes only `"unprocessed"`) never scrapes it.
- **Address:** the `merged_results.address` column is TEXT, created at startup with `ADD COLUMN IF NOT EXISTS`. It is filled only where empty, so it never overwrites a value.
- **Header naming:** request header `X-Google-Key`; frontend localStorage key `lead_gen_google_key`. The Google key is **not** part of `hasKeys` (OpenAI and Jina stay the only required keys).
- **Errors:** Google errors are surfaced with Google's own message via a new `GooglePlacesRequestError` (status 502, code `GOOGLE_PLACES_REQUEST_FAILED`), which the frontend passes through verbatim. A Places failure never aborts the run: the step is marked failed and the web search continues.
- **Model:** `MODEL = "gpt-5-mini"`, no `temperature`.
- **Commits:** don't commit unless the user asks.

## Review Focus

1. **Same business from Places and the web** (e.g. "Harbourside Hospitality Pty Ltd" vs "harbourside hospitality"): expect one row whose Sources count is 2. Covered by the Task 3 manual DB check.
2. **Same location search twice** ("get me more"): no duplicate `SerpLead`s under the Places source and the second run reports 0 new. Test `test_places_already_linked_are_not_saved_twice` in Task 3.
3. **Key enabled for a different API, or billing off:** Google returns 403 with a message. The user sees Google's message in the thread, the Places step shows failed, and the web search still runs. Test `test_google_error_carries_google_message` in Task 2, plus the Task 5 harness check.
4. **Location message with no Google key:** no Places call, one hint line, and the web search runs. Checked by the Task 5 harness.
5. **Address column on projects that never used Places:** it must not break results, export or editing, and it shows empty. Checked in Task 3 (export route) and Task 4 (grid field not editable).

---

## File Structure

| File | Responsibility |
|---|---|
| `backend/app/services/places_service.py` | New. `search_places()` (HTTP and paging), `parse_places()` (pure), `save_places()` (DB) |
| `backend/app/exceptions.py` | `GooglePlacesRequestError` (modify) |
| `backend/app/api/deps.py` | `ApiKeys.google_api_key`, `require_google()`, `X-Google-Key` header (modify) |
| `backend/app/api/routes/leads_serp.py` | `POST /projects/{id}/places` (modify) |
| `backend/app/models/schemas.py` | `PlacesSearchRequest`, `PlacesSearchResponse`; `MessagePlanResponse.location` (modify) |
| `backend/app/services/database_service.py` | Adds the `address` column at startup (modify) |
| `backend/app/services/merged_results_service.py` | `address` in the base columns (results and export) (modify) |
| `backend/app/services/agent_brief_service.py` + `prompts/agent_briefs.py` | `location` in `MessagePlan`, `build_plan`, the prompt; `address` in `RESERVED_COLUMNS` (modify) |
| `backend/tests/test_places_service.py` | New |
| `frontend-react/src/store/apiKeys.ts`, `api/client.ts`, `components/apiKeys/ApiKeys.tsx`, `components/shell/Sidebar.tsx` | Third, optional key (modify) |
| `frontend-react/src/api/leadsSerp.ts`, `api/types.ts`, `api/errors.ts` | `searchPlaces()`, types, pass-through code (modify) |
| `frontend-react/src/components/grid/fields.ts` | Read-only "Address" field (modify) |
| `frontend-react/src/hooks/useRegisterRun.ts` | Places step inside `runFind` (modify) |

---

### Task 1: Interpreter reports the location (done in `9380337`)

**Files:**
- Modify: `backend/app/services/agent_brief_service.py`, `backend/app/prompts/agent_briefs.py`, `backend/app/models/schemas.py`
- Test: `backend/tests/test_build_plan.py`

**Interfaces:**
- Produces:
  - `MessagePlan.location: str = ""`;
  - `build_plan(...)` output key `location: str`, which is stripped and is `""` whenever `find` is False;
  - `MessagePlanResponse.location: str`;
  - `"address"` added to `RESERVED_COLUMNS`.

- [x] **Step 1: Write the failing tests** (append to `test_build_plan.py`):

```python
def test_location_is_passed_through_for_a_search():
    out = build_plan(MessagePlan(find=True, find_instruction="Companies based around Sydney Harbour",
                                 location=" Sydney Harbour "),
                     current_target=None, existing_columns=[], unanswered_by_name={}, enrichments=[])
    assert out["location"] == "Sydney Harbour"

def test_location_is_dropped_when_nothing_is_searched():
    out = build_plan(MessagePlan(location="Sydney", columns=["Website"]),
                     current_target=None, existing_columns=[], unanswered_by_name={}, enrichments=[])
    assert out["location"] == ""
```

- [x] **Step 2:** Run `cd backend && ../.venv/Scripts/python.exe -m pytest tests/test_build_plan.py -q`. Expected: 2 failed (`KeyError: 'location'` or a pydantic extra-field error).
- [x] **Step 3: Implement** the field, the output key, and the schema field.
- [x] **Step 4: Add prompt item `location`.** It is the place named in the message (suburb, city, landmark, region), exactly as the user wrote it, e.g. "Sydney Harbour" or "Brisbane". It is empty when no place is named. For "more of the same", reuse the current search's place, if it has one.
- [x] **Step 5:** Run `../.venv/Scripts/python.exe -m pytest -q`. Expected: `12 passed`.
- [x] **Step 6: Manual check against real gpt-5-mini** (temp project, deleted afterwards). Expected:
  - "sydney harbour companies that invest in environmental causes" → `location` ≈ "Sydney Harbour";
  - "B2B SaaS companies that raised a Series A" → `location == ""`.
- [x] **Step 7: Commit** `feat: interpreter reports the location a search names` (only if the user asks).

---

### Task 2: Places client: HTTP, paging, errors (done in `9380337`)

**Files:**
- Create: `backend/app/services/places_service.py`
- Modify: `backend/app/exceptions.py`
- Test: `backend/tests/test_places_service.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class Place: name: str; address: str`.
  - `parse_places(payload: dict) -> list[Place]`. This is pure and applies the closed/nameless filter.
  - `async def search_places(query: str, api_key: str, *, client: httpx.AsyncClient | None = None, max_pages: int = 3) -> list[Place]`. It dedupes by exact name+address across pages, and uses a fresh `httpx.AsyncClient(timeout=30)` when `client` is None.
  - `PLACES_URL` and `FIELD_MASK` constants.
  - `GooglePlacesRequestError(AppError)`, with `status_code = 502` and `code = "GOOGLE_PLACES_REQUEST_FAILED"`. On a non-2xx response the message is `f"Google Places: {error.message}"` taken from Google's JSON `{"error": {"message": …}}`, falling back to `f"Google Places returned HTTP {status}"`. Network errors (`httpx.HTTPError`) give `"Could not reach Google Places: <exc>"`.

- [x] **Step 1: Write the failing tests** in `backend/tests/test_places_service.py`. Use `httpx.MockTransport`; no network.

```python
import json, httpx, pytest
from app.exceptions import GooglePlacesRequestError
from app.services.places_service import FIELD_MASK, PLACES_URL, Place, parse_places, search_places

def P(name, address="1 Quay St", status="OPERATIONAL"):
    return {"displayName": {"text": name}, "formattedAddress": address, "businessStatus": status}

def test_parse_skips_closed_and_nameless():
    payload = {"places": [P("A"), P("B", status="CLOSED_PERMANENTLY"), {"formattedAddress": "x"}]}
    assert parse_places(payload) == [Place(name="A", address="1 Quay St")]

def test_field_mask_stays_on_the_pro_sku():
    assert "websiteUri" not in FIELD_MASK and "PhoneNumber" not in FIELD_MASK and "rating" not in FIELD_MASK
    assert "places.displayName" in FIELD_MASK and "nextPageToken" in FIELD_MASK

async def run(handler, **kw):
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
        return await search_places("Companies around Sydney Harbour", "KEY", client=c, **kw)

def test_follows_page_tokens_up_to_three_pages():
    seen = []
    def handler(req):
        body = json.loads(req.content); seen.append(body)
        assert str(req.url) == PLACES_URL and req.headers["X-Goog-Api-Key"] == "KEY"
        assert req.headers["X-Goog-FieldMask"] == FIELD_MASK
        n = len(seen)
        return httpx.Response(200, json={"places": [P(f"Biz {n}")], "nextPageToken": f"t{n}"})
    places = asyncio_run(run(handler))
    assert [p.name for p in places] == ["Biz 1", "Biz 2", "Biz 3"]
    assert "pageToken" not in seen[0] and seen[1]["pageToken"] == "t1" and len(seen) == 3

def test_stops_when_no_next_page():
    def handler(req):
        return httpx.Response(200, json={"places": [P("Only")]})
    assert [p.name for p in asyncio_run(run(handler))] == ["Only"]

def test_google_error_carries_google_message():
    def handler(req):
        return httpx.Response(403, json={"error": {"message": "Places API (New) has not been used in project 123"}})
    with pytest.raises(GooglePlacesRequestError) as err:
        asyncio_run(run(handler))
    assert "Places API (New) has not been used" in str(err.value)
```

`asyncio_run` is `asyncio.run`: add `from asyncio import run as asyncio_run` at the top. (This avoids adding pytest-asyncio.)

- [x] **Step 2:** Run `../.venv/Scripts/python.exe -m pytest tests/test_places_service.py -q`. Expected: collection error `ModuleNotFoundError: app.services.places_service`.
- [x] **Step 3: Implement** the exception, then `places_service.py`.
- [x] **Step 4:** Run `../.venv/Scripts/python.exe -m pytest -q`. Expected: `17 passed`.
- [x] **Step 5: Commit** `feat: Google Places text search client` (only if the user asks).

---

### Task 3: Save Places results as leads, plus the address column and endpoint (Steps 1–3 done in `9380337`; resume at Step 4)

**Files:**
- Modify: `backend/app/services/places_service.py` (add `save_places`, `new_place_names`)
- Modify: `backend/app/services/database_service.py`, `backend/app/services/merged_results_service.py`
- Modify: `backend/app/api/deps.py`, `backend/app/api/routes/leads_serp.py`, `backend/app/models/schemas.py`
- Test: `backend/tests/test_places_service.py`

**Interfaces:**
- Consumes: `Place`, `search_places` (Task 2); `normalize_lead_name` (`app/utils/lead_utils.py`); `leads_serp_service._transform_leads_to_aggregated(project_id)`; `merged_results_service.merge_serp_leads(project_id)`; `project_service.update_project_counts_from_db(project_id)`.
- Produces:
  - `new_place_names(places: list[Place], already_linked: set[str]) -> list[tuple[str, Place]]`. It is pure. It returns `(normalized_name, place)` for places whose normalized name is non-empty, not already linked to this source, and not repeated within `places`. The first occurrence wins.
  - `save_places(project_id: int, query: str, places: list[Place]) -> dict`, returning `{"found": int, "new": int, "existing": int, "leads": list[str]}`:
    - `found` is `len(places)`;
    - `new` is the count of normalized names that were not in `merged_results` for this project before saving;
    - `existing` is `found - new`;
    - `leads` holds the normalized names of all found places.

    It gets or creates the source `SerpUrl` (`link=f"google-places:{query}"`, `query=query`, `title="Google Places"`, `status="processed"`) and inserts `SerpLead`s for `new_place_names`. It then runs aggregate → merge → counts. Finally it runs `UPDATE merged_results SET address = :a WHERE project_id = :p AND lead = :l AND (address IS NULL OR address = '')` for each place.
  - `ApiKeys.google_api_key`, `ApiKeys.require_google()` (raises `ApiKeyNotConfiguredError("Google Places API key not provided. Add it under API keys.")`), and a `get_api_keys` param `x_google_key` with `alias="X-Google-Key"`.
  - `PlacesSearchRequest(query: str)`, using the not-empty validator the same way as `InstructionRequest`.
  - `PlacesSearchResponse(found: int, new: int, existing: int, leads: list[str])`.
  - The route `POST /api/projects/{project_id}/places` requires only the Google key and returns `PlacesSearchResponse`.
  - `merged_results` gets an `address` column, created at startup inside `db_service.create_tables()`. `"address"` is included after `"serp_count"` in the `base_columns` of both `get_merged_results` and the CSV export.

- [x] **Step 1: Write the failing tests** (append to `test_places_service.py`):

```python
from app.services.places_service import new_place_names

def test_places_already_linked_are_not_saved_twice():
    places = [Place("Harbourside Hospitality Pty Ltd", "a"), Place("Blue Cove", "b")]
    assert [n for n, _ in new_place_names(places, {"harbourside hospitality"})] == ["blue cove"]

def test_duplicate_places_in_one_search_are_saved_once():
    places = [Place("Blue Cove", "a"), Place("BLUE COVE PTY LTD", "b")]
    out = new_place_names(places, set())
    assert [n for n, _ in out] == ["blue cove"] and out[0][1].address == "a"
```

- [x] **Step 2:** Run it. Expected: `ImportError: cannot import name 'new_place_names'`.
- [x] **Step 3: Implement** `new_place_names`. Run the tests. Expected: `19 passed`.
- [ ] **Step 4: Implement** `save_places`, the address column, the deps header, the schemas and the route.
- [ ] **Step 5: Manual DB check** with FastAPI `TestClient`, a temp project and **no Google call**: call `places_service.save_places` directly with hand-made `Place`s. Expected:
  - saving `[Place("Harbourside Hospitality Pty Ltd","1 Circular Quay"), Place("Blue Cove","Kirribilli Wharf")]` gives `found 2, new 2, existing 0`;
  - `GET /results` shows 2 rows with `address` filled and `serp_count == 1`;
  - saving the same list again gives `found 2, new 0, existing 2`, still with `serp_count == 1` and no duplicate `serp_leads`;
  - inserting a web-sourced `SerpLead` "harbourside hospitality" under another `SerpUrl` and re-merging gives `serp_count == 2` for that row;
  - `GET /api/projects/{id}/results/download` returns 200;
  - `POST /places` without the header returns the `API_KEY_NOT_CONFIGURED` code;
  - the temp project is deleted afterwards.
- [ ] **Step 6: One live Places call**, only if the user provides a key for this check: run `search_places("Companies around Sydney Harbour", key)` and print the count and the first 3 names. Otherwise ledger it as not run.
- [ ] **Step 7: Commit** `feat: save Google Places businesses as leads with an address column` (only if the user asks).

---

### Task 4: Frontend: optional Google key and Address column

**Files:**
- Modify: `frontend-react/src/store/apiKeys.ts`, `src/api/client.ts`, `src/components/apiKeys/ApiKeys.tsx`, `src/components/shell/Sidebar.tsx`, `src/components/grid/fields.ts`, `src/api/errors.ts`

**Interfaces:**
- Produces:
  - `ApiKeysState.googleKey: string`, persisted as `lead_gen_google_key`. `hasBothKeys` is unchanged (OpenAI + Jina).
  - An `X-Google-Key` header, sent when the key is non-empty.
  - Dialog field "Google Places key (optional)" with the hint *"Finds businesses on Google Maps when you name a location. Needs Places API (New) enabled."*
  - The Sidebar status adds "· Google Places on" when the key is set.
  - Grid field `address`: name "Address", type text, `editable: false`, `ai: false`.
  - `GOOGLE_PLACES_REQUEST_FAILED` added to `PASS_THROUGH_CODES`.

- [ ] **Step 1: Implement.** Run `cd frontend-react && npx tsc --noEmit -p .`. Expected: exit 0.
- [ ] **Step 2: In-app browser check.**
  - Open the API keys dialog. Expect three fields, and Save enabled with only OpenAI + Jina filled.
  - Type a dummy value such as `test-not-a-key` into the Google field (**not a real key**) and save. Confirm via `read_network_requests` that the next API request carries `X-Google-Key`. Clear it afterwards.
  - Open a project with rows. Expect no Address column error, and the column shows as empty.
- [ ] **Step 3: Commit** `feat: optional Google Places key and Address column` (only if the user asks).

---

### Task 5: Places step in the chat's search

**Files:**
- Modify: `frontend-react/src/api/leadsSerp.ts` (`searchPlaces(projectId: number, query: string): Promise<PlacesSearchResult>`), `src/api/types.ts` (`PlacesSearchResult {found,new,existing,leads}`, `MessagePlan.location: string`), `src/hooks/useRegisterRun.ts`

**Interfaces:**
- Consumes: Task 1 `location`, Task 3 `POST /places`, Task 4 `getApiKeys().googleKey`.
- Changes:
  - `runFind(instruction: string, location: string)`.
  - In `ask()`, plan normalisation adds `location: raw.location ?? ''`.
  - Planned steps gain `{ id: 'find-places', label: 'Search Google Maps' }` after `find-brief`, only when `plan.location` is set **and** a Google key is present.
- Behaviour inside `runFind`, after the brief:
  - **With a location and a key:**
    1. Write `Google Places · <instruction>`.
    2. Call `searchPlaces(projectId, instruction)`.
    3. Write `<found> businesses found on Google Maps · <new> new, <existing> already in the table.` (`result`).
    4. Call `markSettled(leads)` and `refreshRegister()`, and set the step to `done` with detail `<found> found`.
    5. On error: write the error (`error`), set `find-places` to `failed` with the message, and **continue** to the queries. Don't call `finish`.
  - **With a location and no key:** write the hint `Add a Google Places key under API keys to also search Google Maps for <location>.` once, and continue.
  - **Web search after Places:** if the web search then locates 0 sources, the run still ends cleanly. Places rows count as found, so the "No sources to read" line is kept but the new-row fill still runs.

- [ ] **Step 1: Implement.** Run `npx tsc --noEmit -p .`. Expected: exit 0.
- [ ] **Step 2: Harness check** in the in-app browser: mount `useRegisterRun` with a fake axios adapter, the same method as the previous plan's final review. **No real calls.** Three cases:
  - (a) Location plus key (the dummy key set in the store for the test): the calls go `…/lead-brief` → `…/places` → `…/queries`, the `find-places` step is done, and the chat shows both Places lines.
  - (b) Location, no key: no `/places` call, the hint line appears once, and the web steps still run.
  - (c) `/places` returns 502 `GOOGLE_PLACES_REQUEST_FAILED` with detail "Google Places: API key not valid": `find-places` is failed with that text, `/queries` is still called, and the run ends with `running: false`.
- [ ] **Step 3: Full suite.** Run `cd backend && ../.venv/Scripts/python.exe -m pytest -q`, then `cd ../frontend-react && npx tsc --noEmit -p .`. Expected: `19 passed`, tsc exit 0.
- [ ] **Step 4: Commit** `feat: chat searches Google Places first for location searches` (only if the user asks).
