# Base Search Plus Criteria Columns Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One chat message such as "sydney harbour companies that invest in environmental causes" should do two things:
- search on a broad base ("companies around Sydney Harbour"),
- add a Yes/No column per qualifier ("Invests in environmental causes?").

It should not narrow the search to the qualifier.

**Architecture:**
- **Interpreter.** The chat interpreter (`agent_brief_service.interpret`) splits each message into:
  - `find_instruction`: the base, meaning entity type plus the searchable anchor (location or industry);
  - `criteria`: Yes/No questions for anything that has to be checked company by company.
- **Frontend.** The run hook first searches on the base, then drafts each criterion as a forced `True/False` enrichment column and researches it for every row.
- **Keeping columns full.** After any search, every existing column is filled for the rows that search added, so "get me 10 more" keeps criteria columns complete.

**Tech Stack:** FastAPI + SQLAlchemy + OpenAI `responses.parse` (backend, Python 3.13 venv at `.venv`); React 18 + TanStack Query + TypeScript (frontend-react).

**Spec:**
- The user request in this session (quoted in Goal).
- The approved design, `C:\Users\andys\.claude\plans\help-me-mock-up-graceful-wren.md` ("Column kinds → Criterion").

## Global Constraints

- **Base:** the base is the entity type plus the most searchable anchor in the message. The anchor is a location, an industry, or a listed category, i.e. something directories and lists are organised by.
- **Criteria:** everything else in the message that needs per-company research becomes a criterion. That includes behaviour, investments, policies, size, certifications and ownership model.
- **Criteria are Yes/No questions** phrased about one company, e.g. "Does this company invest in environmental causes?".
- **No qualifier means no criteria.** "dental clinics in Sydney" has no qualifier, so `criteria == []` and the behaviour is the same as today.
- **Criteria never filter the search.** Rows that answer No stay in the table. Filtering and "Matches all" views are a later plan.
- **Criterion columns are always `result_format == "True/False"`**, whatever the drafter would have picked.
- **Model and parameters:** `MODEL = "gpt-5-mini"`, and no `temperature` parameter (the model rejects it).
- **Copy:** chat copy follows the existing log style (`Target set: …`, `Column “…” · True/False`).
- **Honest replies:** a reply must never claim that work is running.
- **Commits:** don't commit unless the user asks. The commit steps below are for when they do.

## Review Focus

1. **Pure-base query** ("dental clinics in Sydney"): expect `criteria == []` and a search only. Test in Task 2 (`test_plan_without_qualifiers_has_no_criteria`).
2. **Qualifier that is already a column** (the user repeats "invests in environmental causes" after it exists): no duplicate column. Test in Task 2 (`test_criteria_matching_existing_columns_are_dropped`).
3. **"Get me 10 more" after criteria exist:** the new rows get the criterion answers too, not blanks. Test in Task 3 (`test_unanswered_columns_lists_only_columns_with_gaps`) plus manual step in Task 5.
4. **Model returns an empty base** (e.g. for "companies that invest in the environment"): fall back to the project's current search target, and if there is none, drop the search rather than search on an empty string. Tests in Task 2 (`test_empty_base_falls_back_to_current_target`, `test_find_with_no_base_and_no_target_is_dropped`).
5. **More than 5 criteria in one message:** cap criteria + columns at 5 new columns total so one message can't queue an unbounded research bill. Test in Task 2 (`test_new_columns_are_capped_at_five`).

---

## File Structure

| File | Responsibility |
|---|---|
| `backend/app/prompts/agent_briefs.py` | `INTERPRET_PROMPT`: teaches the base/criteria split (modify) |
| `backend/app/services/agent_brief_service.py` | `MessagePlan.criteria`; new pure `build_plan()` post-processor; `draft_enrichment(..., result_format=None)` (modify) |
| `backend/app/services/column_gaps.py` | New. Pure `unanswered_leads()` (moved here) and `unanswered_columns()` |
| `backend/app/api/routes/enrichments.py` | Draft request accepts `result_format`; new `GET /projects/{id}/enrichments/unanswered` (modify) |
| `backend/app/models/schemas.py` | `EnrichmentDraftRequest`, `MessagePlanResponse.criteria` (modify) |
| `backend/tests/` | New. `conftest.py`, `test_build_plan.py`, `test_column_gaps.py` |
| `backend/requirements-dev.txt` | New. `pytest` |
| `frontend-react/src/api/{types,enrichments}.ts` | `MessagePlan.criteria`; `draftEnrichment(…, resultFormat?)`; `getUnansweredColumns()` (modify) |
| `frontend-react/src/hooks/useRegisterRun.ts` | Run criteria columns after the base search; fill existing columns after any search (modify) |

---

### Task 1: Backend test harness

**Files:**
- Create: `backend/requirements-dev.txt`, `backend/tests/__init__.py`, `backend/tests/conftest.py`

**Interfaces:**
- Produces: `pytest` runnable from `backend/` as `../.venv/Scripts/python.exe -m pytest`. `conftest.py` inserts `backend/` on `sys.path` so tests can `import app...`. Tests must not need a database or OpenAI.

- [ ] **Step 1:** Create `backend/requirements-dev.txt` containing `-r requirements.txt` and `pytest>=8`.
- [ ] **Step 2:** Install it: `.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt`. Expected: `Successfully installed pytest-…`.
- [ ] **Step 3:** Create `backend/tests/conftest.py` that prepends the `backend` directory to `sys.path`.
- [ ] **Step 4:** Run `cd backend && ../.venv/Scripts/python.exe -m pytest -q`. Expected: `no tests ran` (exit code 5).
- [ ] **Step 5: Commit** `chore: add backend pytest harness`.

---

### Task 2: Interpreter splits a message into base search + criteria

**Files:**
- Modify: `backend/app/prompts/agent_briefs.py` (`INTERPRET_PROMPT`)
- Modify: `backend/app/services/agent_brief_service.py` (`MessagePlan`, `interpret`)
- Modify: `backend/app/models/schemas.py` (`MessagePlanResponse`)
- Test: `backend/tests/test_build_plan.py`

**Interfaces:**
- Produces:
  - `MessagePlan.criteria: list[str]`, defaulting to `[]`.
  - `build_plan(raw: MessagePlan, *, current_target: str | None, existing_columns: list[str], unanswered_by_name: dict[str, list[str]], enrichments: list) -> dict`. This is pure, with no I/O, and `interpret()` returns its result.
  - The returned dict keys, and `MessagePlanResponse` fields, are: `find: bool`, `find_instruction: str`, `criteria: list[str]`, `columns: list[str]`, `continue_columns: list[ContinueColumn]`, `reply: str`.
- Consumes: the existing `ContinueColumn` schema and `unanswered_leads`. After Task 3, import `unanswered_leads` from `app.services.column_gaps`.

- [ ] **Step 1: Write the failing tests** in `backend/tests/test_build_plan.py`:

```python
from app.services.agent_brief_service import MessagePlan, build_plan

def test_base_and_criteria_are_kept_separate():
    out = build_plan(
        MessagePlan(find=True, find_instruction="Companies based around Sydney Harbour",
                    criteria=["Does this company invest in environmental causes?"]),
        current_target=None, existing_columns=[], unanswered_by_name={}, enrichments=[])
    assert out["find"] is True
    assert out["find_instruction"] == "Companies based around Sydney Harbour"
    assert out["criteria"] == ["Does this company invest in environmental causes?"]
    assert out["columns"] == []

def test_plan_without_qualifiers_has_no_criteria():
    out = build_plan(MessagePlan(find=True, find_instruction="Dental clinics in Sydney"),
                     current_target=None, existing_columns=[], unanswered_by_name={}, enrichments=[])
    assert out["criteria"] == []

def test_criteria_matching_existing_columns_are_dropped():
    out = build_plan(
        MessagePlan(criteria=["Invests in environmental causes", "Has 50+ staff?"]),
        current_target="x", existing_columns=["invests in environmental causes"],
        unanswered_by_name={}, enrichments=[])
    assert out["criteria"] == ["Has 50+ staff?"]

def test_empty_base_falls_back_to_current_target():
    out = build_plan(MessagePlan(find=True, find_instruction="  ", criteria=["Q?"]),
                     current_target="Companies around Sydney Harbour",
                     existing_columns=[], unanswered_by_name={}, enrichments=[])
    assert out["find_instruction"] == "Companies around Sydney Harbour"

def test_find_with_no_base_and_no_target_is_dropped():
    out = build_plan(MessagePlan(find=True, find_instruction=""), current_target=None,
                     existing_columns=[], unanswered_by_name={}, enrichments=[])
    assert out["find"] is False and out["find_instruction"] == ""

def test_new_columns_are_capped_at_five():
    out = build_plan(MessagePlan(criteria=[f"C{i}?" for i in range(4)], columns=[f"R{i}" for i in range(4)]),
                     current_target="x", existing_columns=[], unanswered_by_name={}, enrichments=[])
    assert len(out["criteria"]) + len(out["columns"]) == 5
    assert out["criteria"] == ["C0?", "C1?", "C2?", "C3?"]  # criteria take priority
```

- [ ] **Step 2:** Run `cd backend && ../.venv/Scripts/python.exe -m pytest tests/test_build_plan.py -q`. Expected: FAIL with `ImportError: cannot import name 'build_plan'`.
- [ ] **Step 3: Implement.**
  - Add `criteria: list[str] = Field(default_factory=list)` to `MessagePlan`.
  - Add `criteria: list[str]` to `MessagePlanResponse`.
  - Move the post-processing that now sits at the end of `interpret()` (find fallback, column dedupe, `continue_columns`) into `build_plan()`, and add:
    - criteria are deduped case-insensitively, against existing columns and against each other;
    - `columns` are also deduped against the criteria;
    - criteria fill the 5-slot cap first, then columns.
  - `interpret()` calls `build_plan(...)` and returns it.
- [ ] **Step 4:** Run the Step 2 command. Expected: `6 passed`.
- [ ] **Step 5: Rewrite `INTERPRET_PROMPT` item 1–3.**
  - `find_instruction` is the **base only**: entity type plus the one most searchable anchor (location, industry or listed category). Example: "sydney harbour companies that invest in environmental causes" gives `Companies based around Sydney Harbour`.
  - A new item, `criteria`, holds each remaining qualifier that needs per-company checking, as a Yes/No question about one company. Example: `Does this company invest in or financially support environmental causes?`.
  - If the message has no qualifier, `criteria` is empty.
  - "More of the same" requests restate the current target and add no criteria.
  - Keep the existing `columns` item for non-Yes/No information requests (website, headcount number).
- [ ] **Step 6: Manual check against real OpenAI.** This costs about 3 `gpt-5-mini` calls using the key in `backend/.env`. Run a script that creates a temp project, calls `agent_brief_service.interpret` for the three messages below, prints the plans, and then deletes the project. Expected:
  - "sydney harbour companies that invest in environmental causes": base ≈ "Companies … Sydney Harbour" and 1 criterion about environmental causes.
  - "dental clinics in Sydney": `criteria == []`.
  - "franchise gyms in Brisbane with over 50 staff": the base mentions gyms and Brisbane; the criteria cover franchise model and 50+ staff. (Either "franchise" or "gym" may anchor; the location must stay in the base.)
- [ ] **Step 7: Commit** `feat: interpreter splits a message into base search and criteria`.

---

### Task 3: Know which columns have gaps, so new rows get filled

**Files:**
- Create: `backend/app/services/column_gaps.py`
- Modify: `backend/app/services/agent_brief_service.py` (import `unanswered_leads` from the new module; delete the local copy)
- Modify: `backend/app/api/routes/enrichments.py` (new endpoint)
- Test: `backend/tests/test_column_gaps.py`

**Interfaces:**
- Produces:
  - `unanswered_leads(rows: list[dict], column_name: str) -> list[str]`. This is the existing behaviour, moved: a lead is unanswered when both the value and `<col>_reasoning` are blank.
  - `unanswered_columns(rows: list[dict], enrichments: list) -> list[dict]`. It returns one `{enrichment_id, name, column_name, leads}` per enrichment that has ≥1 unanswered lead, in enrichment order.
  - `GET /api/projects/{project_id}/enrichments/unanswered` returns `list[ContinueColumn]`, and 404 `PROJECT_NOT_FOUND` for a missing project.

- [ ] **Step 1: Write the failing tests** in `backend/tests/test_column_gaps.py`:

```python
from types import SimpleNamespace as E
from app.services.column_gaps import unanswered_leads, unanswered_columns

ROWS = [
    {"lead": "A", "env": True,  "env_reasoning": "found report"},
    {"lead": "B", "env": None,  "env_reasoning": "searched, nothing found"},
    {"lead": "C", "env": None,  "env_reasoning": None},
    {"lead": "D", "env": "",    "env_reasoning": "  "},
]

def test_researched_leads_with_no_answer_are_not_unanswered():
    assert unanswered_leads(ROWS, "env") == ["C", "D"]

def test_unanswered_columns_lists_only_columns_with_gaps():
    ens = [E(id=1, enrichment_name="Env", column_name="env"),
           E(id=2, enrichment_name="Web", column_name="web"),
           E(id=3, enrichment_name="Draft", column_name=None)]
    rows = [dict(r, web="x.com", web_reasoning="r") for r in ROWS]
    assert unanswered_columns(rows, ens) == [
        {"enrichment_id": 1, "name": "Env", "column_name": "env", "leads": ["C", "D"]}]
```

- [ ] **Step 2:** Run `../.venv/Scripts/python.exe -m pytest tests/test_column_gaps.py -q`. Expected: FAIL with `ModuleNotFoundError: app.services.column_gaps`.
- [ ] **Step 3: Implement** both functions in `column_gaps.py` and switch `agent_brief_service` to import from it. Add the endpoint in `enrichments.py`. It reads `merged_results_service.get_merged_results(project_id)["data"]` and `enrichment_service.get_enrichments(project_id)`.
- [ ] **Step 4:** Run `../.venv/Scripts/python.exe -m pytest -q`. Expected: all of Task 2's and Task 3's tests pass (`8 passed`).
- [ ] **Step 5: Manual endpoint check** with FastAPI `TestClient` against the dev DB. Create a temp project, `GET …/enrichments/unanswered` and expect `[]`, then delete the project. Then request a missing project id and expect 404 with `"code": "PROJECT_NOT_FOUND"`.
- [ ] **Step 6: Commit** `feat: report columns with unanswered leads`.

---

### Task 4: Draft criteria as Yes/No columns

**Files:**
- Modify: `backend/app/models/schemas.py` (new `EnrichmentDraftRequest`)
- Modify: `backend/app/api/routes/enrichments.py` (`draft_enrichment` route)
- Modify: `backend/app/services/agent_brief_service.py` (`draft_enrichment`)
- Test: `backend/tests/test_build_plan.py` (add one test)

**Interfaces:**
- Produces:
  - `EnrichmentDraftRequest(instruction: str, result_format: Literal["True/False","Number","Text"] | None = None)`. It uses the same not-empty validator as `InstructionRequest`.
  - `draft_enrichment(project_id, instruction, *, openai_api_key, result_format=None)`. When `result_format` is given, it overrides the model's choice before the config is built, so `result_true_if` / `result_false_if` get filled for `"True/False"`.
- Constraint: the existing `POST /enrichments/draft` body `{instruction}` must keep working unchanged.

- [ ] **Step 1: Write the failing test.** Add a pure helper in `agent_brief_service.py`: `apply_format_override(draft: EnrichmentDraft, result_format: str | None) -> EnrichmentDraft`. Test it:

```python
from app.services.agent_brief_service import EnrichmentDraft, apply_format_override

def test_format_override_forces_true_false():
    d = EnrichmentDraft(enrichment_name="Env", column_name="env", result_format="Text",
                        goal="g", acceptable_evidence="e")
    assert apply_format_override(d, "True/False").result_format == "True/False"
    assert apply_format_override(d, None).result_format == "Text"
```

- [ ] **Step 2:** Run it. Expected: FAIL with an `ImportError`.
- [ ] **Step 3: Implement** the helper and the `result_format` parameter, and switch the route to `EnrichmentDraftRequest`.
- [ ] **Step 4:** Run `../.venv/Scripts/python.exe -m pytest -q`. Expected: `9 passed`.
- [ ] **Step 5: Commit** `feat: allow forcing a drafted column's result format`.

---

### Task 5: Run it from the chat: base search, then criteria columns, then fill gaps

**Files:**
- Modify: `frontend-react/src/api/types.ts` (`MessagePlan.criteria: string[]`)
- Modify: `frontend-react/src/api/enrichments.ts` (`draftEnrichment(projectId, instruction, resultFormat?: 'True/False' | 'Number' | 'Text')`, which sends `result_format` only when given; new `getUnansweredColumns(projectId): Promise<ContinueColumn[]>`)
- Modify: `frontend-react/src/hooks/useRegisterRun.ts`

**Interfaces:**
- Consumes:
  - Task 2's `criteria` field;
  - Task 3's `GET …/enrichments/unanswered`;
  - Task 4's `result_format` on draft;
  - the existing `runColumn(prefix, source, leads)`, whose `source` gains a variant `{ question: string; resultFormat?: 'True/False' }`.
- Order inside `ask()`:
  1. `runFind(plan.find_instruction)`.
  2. If the search ran and the project already had columns before this message, fill gaps: call `getUnansweredColumns`, then run `runColumn('gap-<n>', { existing }, existing.leads)` for each.
  3. Criteria: `runColumn('crit-<n>', { question, resultFormat: 'True/False' }, allLeads)`.
  4. Plain `columns`, as today.
  5. `continue_columns`, as today, skipping any column already filled in step 2.
- Planned steps shown in the panel:
  - "Search: <find_instruction>"
  - "Check: <criterion>" + "Research every entry"
  - "Fill new rows: <column name>". Gap steps can't be known upfront, so add them after the search finishes.
- Chat lines:
  - Before searching: `Base search: <find_instruction>`.
  - Once per criterion: `Criterion column: <question> · Yes/No`.

- [ ] **Step 1: Implement the API client changes.** Run `cd frontend-react && npx tsc --noEmit -p .`. Expected: no output (exit 0).
- [ ] **Step 2: Implement the `ask()` ordering above.** Run tsc again. Expected: exit 0.
- [ ] **Step 3: Manual end to end** in the in-app browser. This needs the user's OpenAI and Jina keys entered in the app, so the user runs this step or enters the keys themselves. In a fresh project, send `sydney harbour companies that invest in environmental causes`. Expected:
  - the thread shows `Base search: Companies … Sydney Harbour` and then `Criterion column: … environmental causes … · Yes/No`;
  - the table gets rows plus one True/False column with reasoning/evidence;
  - rows answering No are still present.
- [ ] **Step 4: Manual gap fill.** In the same project, send `get me 10 more`. Expected: the steps show "Fill new rows: <criterion column>", the new rows get Yes/No answers, and the existing answered rows are not re-researched (the batch count equals the number of new rows).
- [ ] **Step 5: Manual pure-base query.** In a new project, send `dental clinics in Sydney`. Expected: a search only, with no criterion column.
- [ ] **Step 6: Commit** `feat: chat searches on a base and adds criteria as Yes/No columns`.
