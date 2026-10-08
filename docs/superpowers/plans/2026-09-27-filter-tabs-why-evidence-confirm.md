# Filter Tabs, Why/Evidence Toggle and Confirmation Card Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:**
- Filter tabs over the lead table: Matches all / All / Unclear.
- A collapsible "Why and evidence" view with source-count badges.
- A confirmation card in the chat. It shows the base search, criteria and columns before any search or column research runs.

**Architecture:**
- **Row logic.** A new pure module, `src/components/grid/rowStatus.ts`, classifies rows, counts evidence URLs and splits text into links. It is tested with Vitest, which is new.
- **Table.** `Project.tsx` owns the view state (tab, open note columns), persisted per project in localStorage. It passes the filtered rows plus a dimmed set and badge info to `DataGrid`.
- **Chat.** A new pure module, `src/components/panel/breakdown.ts`, decides whether a card is active and applies edits. `useRegisterRun.ask()` stops after interpreting, records a `breakdown` chat entry that carries the plan, and a new `start(plan)` runs it. `EnquiryPanel` renders the card.
- **Backend.** No changes.

**Tech Stack:** React 18 + TypeScript + Vite 5 (node 20.9), Vitest 2 (new devDependency), existing axios/TanStack Query.

**Spec:** the design approved in chat on 2026-09-27, restated here:

- **Filter tabs**
  - They use every AI answer column, not reasoning or evidence columns, whatever its format.
  - **Matches all:** no Yes/No answer is No, and no answer column is blank.
  - **Unclear:** nothing is No, and at least one answer column is blank.
  - **All:** every row. Rows with any No are dimmed there, and All is the only view that shows them.
  - They combine with the search box and are hidden when there are no AI columns. The default is **All**, and the choice is remembered per project.
- **Why and evidence**
  - Collapsed by default. Each AI answer cell shows a link badge with its source count (URLs found in the evidence text, `0` included).
  - A toolbar checkbox "Why and evidence" expands or collapses all note columns. Each AI answer column header has its own expand icon. Both are remembered per project.
  - Clicking a badge opens the record, where evidence URLs are clickable links.
- **Confirmation card**
  - A message that starts a search or adds criteria or columns shows a card instead of running. "continue" and plain replies run straight away.
  - The card has an editable base search, a location chip, criteria chips (Yes/No) and column chips, each with ×, plus **Start** and **Cancel**.
  - To add something, the user types in the chat and a new card replaces the old one.
  - A card is active only while it is the newest line in the thread and no run is going. It survives a reload.

## Global Constraints

- **Answer columns and note columns:** an answer column is a `GridField` with `ai === true && !note`. Note columns are `<key>_reasoning` / `<key>_evidence` (existing `NOTE_SUFFIX`).
- **Yes and No:** read them with the existing `readVerdict` (`fields.ts`). **Blank** means null, undefined, or a string that is empty after trim.
- **URLs:** match them with `/https?:\/\/[^\s<>"')\]]+/g`. Strip trailing `.,;:` from each match. Count distinct URLs.
- **localStorage keys:**
  - `kiyu.results.view.<projectId>`, with values `all | matches | unclear`;
  - `kiyu.results.notes.<projectId>`, a JSON `{ all: boolean, open: string[] }`.
  - Wrap every read and write in try/catch. With no stored value the page behaves as the defaults.
- **Card entry:** `role: 'agent'`, `kind: 'breakdown'`, `text` is a one-line summary, and `payload: { plan: MessagePlan }`.
- **Card copy:**
  - Buttons are `Start` and `Cancel`.
  - Inactive states read `Started`, `Cancelled` or `Replaced by a newer request`.
  - Cancelling writes the log line `Cancelled. Nothing ran.`
  - Start writes the log line `Started.` before the run's own lines.
- **Behaviour:** no backend changes. `continue_columns`-only and reply-only plans keep running immediately.
- **Commits:** don't commit unless the user asks.

## Review Focus

1. **Evidence text with no URLs, or the same URL twice:** the badge shows `0`, or counts it once. Tests `countSources` in Task 1.
2. **A project whose only AI column is Text or Number:** the tabs still work, blank means Unclear and filled means Match. Test `rowStatus` in Task 1.
3. **A reload while a card is pending:** the card is still active and Start still works; a card followed by any line is inactive. Test `isActiveCard` in Task 4 plus a browser check.
4. **The user clears the base search, or removes every chip:** clearing the base means no search. With nothing left, Start is disabled and shows the hint "Nothing left to run". Tests for `applyCardEdits` and `hasWork` in Task 4.
5. **Stored localStorage values from a deleted column, or malformed JSON:** ignored and no crash. Test `readNotesState` in Task 3.

---

## File Structure

| File | Responsibility |
|---|---|
| `frontend-react/package.json` | `vitest` devDependency, `"test": "vitest run"` (modify) |
| `src/components/grid/rowStatus.ts` | New, pure: `answerKeys`, `rowStatus`, `countSources`, `splitLinks` |
| `src/components/grid/rowStatus.test.ts` | New |
| `src/components/grid/viewState.ts` | New: `readView`/`writeView`, `readNotesState`/`writeNotesState` (localStorage, try/catch) |
| `src/components/grid/viewState.test.ts` | New |
| `src/pages/Project.tsx` | Filter tabs, notes checkbox, filtering, dim set, and the props below (modify) |
| `src/components/grid/DataGrid.tsx` | `dimmed?`, `collapsedNotes?`, `onToggleNotes?`, header icon, badge (modify) |
| `src/components/grid/ExpandedRecord.tsx` | Evidence rendered with `splitLinks` (modify) |
| `src/components/panel/breakdown.ts` | New, pure: `isActiveCard`, `applyCardEdits`, `hasWork`, `summarisePlan` |
| `src/components/panel/breakdown.test.ts` | New |
| `src/components/panel/EnquiryPanel.tsx` | `BreakdownCard` inside `Thread`; `onStart`/`onCancel` props (modify) |
| `src/hooks/useRegisterRun.ts` | `ask` stops at the card; new `start(plan)` and `cancel()` (modify) |
| `src/styles/app.css` | Tabs, badge, dimmed row, card styles (modify) |

---

### Task 1: Vitest and row logic

**Files:** `package.json`, `src/components/grid/rowStatus.ts`, `src/components/grid/rowStatus.test.ts`

**Interfaces:**
- Produces:
  - `answerKeys(fields: GridField[]): string[]` returns the keys of AI answer fields.
  - `rowStatus(row: GridRow, keys: string[], yesNoKeys: Set<string>): 'match' | 'unclear' | 'fails'`:
    - `fails` if any key in `yesNoKeys` reads No;
    - otherwise `unclear` if any key is blank;
    - otherwise `match`;
    - with `keys == []` it is `match`.
  - `countSources(evidence: unknown): number` counts distinct URLs, and returns 0 for blank or non-string input.
  - `splitLinks(text: string): Array<{ text: string; href?: string }>` splits text into URL and non-URL runs whose texts, joined, equal the input exactly.

- [ ] **Step 1:** `npm --prefix frontend-react install -D vitest@^2`, then add the script `"test": "vitest run"`. Expected: install succeeds, and `npx vitest --version` prints `2.x`.
- [ ] **Step 2: Write the failing tests** in `rowStatus.test.ts`:

```ts
import { describe, expect, it } from 'vitest';
import { countSources, rowStatus, splitLinks } from './rowStatus';

const keys = ['env', 'staff', 'website'];
const yesNo = new Set(['env', 'staff']);

describe('rowStatus', () => {
  it('matches when every yes/no is yes and every column has an answer', () =>
    expect(rowStatus({ env: 'Yes', staff: true, website: 'x.com' }, keys, yesNo)).toBe('match'));
  it('fails when any yes/no column is no, even with blanks', () =>
    expect(rowStatus({ env: 'No', staff: null, website: '' }, keys, yesNo)).toBe('fails'));
  it('is unclear when nothing is no but something is blank', () =>
    expect(rowStatus({ env: 'Yes', staff: '  ', website: 'x.com' }, keys, yesNo)).toBe('unclear'));
  it('treats a filled text-only column as a match and a blank one as unclear', () => {
    expect(rowStatus({ website: 'x.com' }, ['website'], new Set())).toBe('match');
    expect(rowStatus({ website: null }, ['website'], new Set())).toBe('unclear');
  });
  it('matches every row when there are no answer columns', () =>
    expect(rowStatus({}, [], new Set())).toBe('match'));
});

describe('countSources', () => {
  it('counts distinct urls and ignores trailing punctuation', () =>
    expect(countSources('See https://a.com/x, and https://a.com/x. Also http://b.org')).toBe(2));
  it('is zero for text without urls or for blanks', () => {
    expect(countSources('annual report, page 4')).toBe(0);
    expect(countSources(null)).toBe(0);
  });
});

describe('splitLinks', () => {
  it('marks urls as links and keeps the rest as text', () =>
    expect(splitLinks('Source: https://a.com/x.')).toEqual([
      { text: 'Source: ' }, { text: 'https://a.com/x', href: 'https://a.com/x' }, { text: '.' }]));
});
```

- [ ] **Step 3:** Run `cd frontend-react && npx vitest run src/components/grid/rowStatus.test.ts`. Expected: FAIL, cannot resolve `./rowStatus`.
- [ ] **Step 4: Implement** `rowStatus.ts`, using `readVerdict` from `./fields` for Yes/No.
- [ ] **Step 5:** Run the Step 3 command. Expected: 8 passed. Also run `npx tsc --noEmit -p .`. Expected: exit 0.

---

### Task 2: Filter tabs and dimmed rows

**Files:** `src/components/grid/viewState.ts` (the view part), `src/pages/Project.tsx`, `src/components/grid/DataGrid.tsx`, `src/styles/app.css`

**Interfaces:**
- Consumes: `answerKeys` and `rowStatus` from Task 1.
- Produces:
  - `type ResultsView = 'all' | 'matches' | 'unclear'`;
  - `readView(projectId: number): ResultsView`, which returns `'all'` for missing or invalid values;
  - `writeView(projectId: number, view: ResultsView): void`;
  - the DataGrid prop `dimmed?: Set<string>`, a set of lead names rendered with `data-dimmed` on the row.
- In `Project.tsx`:
  - `yesNoKeys` = answer fields with `type === 'select'`.
  - Compute status once per row.
  - `visibleRows` = search filter ∩ tab filter.
  - Tab counts are computed after the search filter.
  - Tabs render only when `answerKeys(fields).length > 0`, as three buttons with `aria-pressed`, labelled `Matches all · N`, `All · N`, `Unclear · N`.
  - `dimmed` = the leads with status `fails` (only visible in All).

- [ ] **Step 1: Write the failing test** `viewState.test.ts`:
  - after `writeView(7,'unclear')`, `readView(7)` is `'unclear'`;
  - `readView(8)` is `'all'`;
  - when localStorage holds `'garbage'` for 9, `readView(9)` is `'all'`.

  Use Vitest's `jsdom` environment for this file via the header `// @vitest-environment jsdom`. If jsdom isn't installed, add `jsdom` as a devDependency in this step.
- [ ] **Step 2:** Run it. Expected: FAIL, cannot resolve `./viewState`.
- [ ] **Step 3: Implement** `readView`/`writeView`, then wire up `Project.tsx`, `DataGrid.tsx` and the CSS (a dimmed row uses the muted text colour).
- [ ] **Step 4:** Run `npx vitest run` and `npx tsc --noEmit -p .`. Expected: all pass, and tsc exits 0.
- [ ] **Step 5: Browser check on project 18** (read-only, real data). Expected:
  - the tabs show with counts that add up (matches + unclear + fails = all);
  - switching the tab filters the rows;
  - a reload keeps the tab;
  - the search box still narrows within the tab.

---

### Task 3: Why and evidence toggle, badges and linked evidence

**Files:** `src/components/grid/viewState.ts` (the notes part), `src/pages/Project.tsx`, `src/components/grid/DataGrid.tsx`, `src/components/grid/ExpandedRecord.tsx`, `src/styles/app.css`

**Interfaces:**
- Consumes: `countSources` and `splitLinks` from Task 1.
- Produces:
  - `type NotesState = { all: boolean; open: string[] }`;
  - `readNotesState(projectId: number): NotesState`, which returns `{ all: false, open: [] }` for missing or malformed data;
  - `writeNotesState(projectId, state)`;
  - `notesOpen(state: NotesState, parentKey: string): boolean`, which is `state.all || state.open.includes(parentKey)`.
- DataGrid props:
  - `collapsedNotes?: Set<string>`, the answer keys whose notes are hidden. `Project.tsx` removes those note fields from `fields` before passing them.
  - `onToggleNotes?: (answerKey: string) => void`.
- Header: for fields with `noteKeys`, a button between `head__name` and `head__menu`, with icon `expand` and `aria-label` `Show why and evidence for <name>` / `Hide why and evidence for <name>`.
- Cell: when an answer's notes are collapsed, it renders `CellValue`, then a button `.cell__sources` showing `countSources(row[\`${key}_evidence\`])` with the `key` icon swapped for a link glyph (reuse an existing icon; no new SVG) and `aria-label` `<n> sources, open record`. It calls `onExpand(lead)` with `stopPropagation`.
- The toolbar checkbox "Why and evidence" sets `all`. Unticking it also clears `open`.
- In `ExpandedRecord`, evidence renders as `splitLinks` runs, with `<a href target="_blank" rel="noopener noreferrer">` for the links.

- [ ] **Step 1: Write the failing tests** in `viewState.test.ts`:
  - `readNotesState` round-trips a written state;
  - it returns the default for a missing key;
  - it returns the default for stored `'{not json'`;
  - it returns the default for `{"all":"yes"}` (wrong types);
  - `notesOpen({all:false, open:['env']}, 'env')` is true, and for `'staff'` it's false.
- [ ] **Step 2:** Run it. Expected: FAIL, as the notes functions are not exported yet.
- [ ] **Step 3: Implement** the functions, then wire up `Project.tsx`, `DataGrid.tsx`, `ExpandedRecord.tsx` and the CSS.
- [ ] **Step 4:** Run `npx vitest run` and `npx tsc --noEmit -p .`. Expected: all pass, and tsc exits 0.
- [ ] **Step 5: Browser check on project 18.** Expected:
  - by default there are no reasoning/evidence columns, and each "Clinic Opening Hours" cell shows a badge;
  - ticking the checkbox shows both note columns;
  - the header icon toggles one column;
  - a reload keeps the state;
  - clicking a badge opens the record, with evidence URLs as links.

---

### Task 4: Confirmation card before running

**Files:** `src/components/panel/breakdown.ts`, `src/components/panel/breakdown.test.ts`, `src/hooks/useRegisterRun.ts`, `src/components/panel/EnquiryPanel.tsx`, `src/pages/Project.tsx`, `src/styles/app.css`

**Interfaces:**
- Produces, in `breakdown.ts` (pure):
  - `needsConfirmation(plan: MessagePlan): boolean`, which is `plan.find || plan.criteria.length > 0 || plan.columns.length > 0`.
  - `summarisePlan(plan: MessagePlan): string`. For example `Search "Companies based around Sydney Harbour" · 1 criterion · 0 columns` (singular/plural by count; the search part is left out when `find` is false).
  - `type CardEdits = { base: string; removedCriteria: number[]; removedColumns: number[] }`.
  - `applyCardEdits(plan: MessagePlan, edits: CardEdits): MessagePlan`:
    - `find_instruction` becomes the trimmed `edits.base`;
    - `find` is `plan.find && base !== ''`;
    - `location` becomes `''` when `find` is false;
    - removed indices are filtered out;
    - `continue_columns` and `reply` are kept.
  - `hasWork(plan: MessagePlan): boolean`, which is `needsConfirmation(plan) || plan.continue_columns.length > 0`.
  - `isActiveCard(lines: ThreadLine[], index: number, running: boolean): boolean`: true if `lines[index].kind === 'breakdown'`, it is the last line, and `!running`.
  - `cardState(lines: ThreadLine[], index: number): 'active' | 'started' | 'cancelled' | 'replaced'`. It is decided by the first line after the card:
    - `Started.` gives `started`;
    - `Cancelled. Nothing ran.` gives `cancelled`;
    - anything else gives `replaced`;
    - no line after the card gives `active`.
- Produces, in `useRegisterRun`:
  - `ask(message)`:
    - it interprets exactly as today;
    - if `needsConfirmation(plan)`, it records the card entry (`summarisePlan` text, `payload: { plan }`), marks `understand` done with detail `waiting for Start`, calls `finish()` and returns;
    - otherwise it runs `continue_columns` and the reply as today.
  - `start(plan: MessagePlan)`: writes `Started.` and runs the existing post-interpret body (find → gap fill → criteria → columns → continue) with fresh steps.
  - `cancel()`: writes `Cancelled. Nothing ran.`
- Produces, in `EnquiryPanel`:
  - new props `onStart(plan)` and `onCancel()`;
  - `Thread` renders `kind === 'breakdown'` lines as `BreakdownCard`, which uses `payload.plan` and has local edit state;
  - it is interactive only when `isActiveCard`; otherwise it shows the `cardState` label.
  - Start is disabled when `!hasWork(applyCardEdits(...))`, with the hint `Nothing left to run`.
  - `Project.tsx` passes `onStart={(plan) => requireKeys() && run.start(plan)}` and `onCancel={run.cancel}`.

- [ ] **Step 1: Write the failing tests** in `breakdown.test.ts`, one or more per function, covering:
  - clearing the base turns off find and location;
  - removed chips are dropped;
  - `continue_columns` survive edits;
  - `hasWork` is false once everything is removed;
  - `isActiveCard` is false for a card that is not last, and false while running;
  - `cardState` covers all four states;
  - the `summarisePlan` singular/plural wording.
- [ ] **Step 2:** Run `npx vitest run src/components/panel/breakdown.test.ts`. Expected: FAIL, cannot resolve `./breakdown`.
- [ ] **Step 3: Implement** `breakdown.ts` until the tests pass.
- [ ] **Step 4: Split `ask` into `ask`/`start`/`cancel`** in `useRegisterRun.ts`, then add `BreakdownCard`, wire `Project.tsx`, and add the CSS. Run `npx vitest run` and `npx tsc --noEmit -p .`. Expected: all pass, and tsc exits 0.
- [ ] **Step 5: Harness check** in the in-app browser. Mount `useRegisterRun`, with the fake adapter installed on **every** loaded `client.ts` copy and the key store set on **every** `apiKeys.ts` copy (lessons from the Places plan), and a guard that aborts if the fake isn't used. **No real calls.** Cases:
  - (a) A plan with find and a criterion: `ask` makes only the `/chat/interpret` call, records a breakdown entry with the plan, and ends with `running: false`.
  - (b) `start(editedPlan)` after removing the criterion: it calls `/lead-brief`, `/queries`, `/urls` and never `/enrichments/draft`, and its first log line is `Started.`.
  - (c) A plan with only `continue_columns`: it runs straight away, with no breakdown entry.
  - (d) `cancel()` writes `Cancelled. Nothing ran.` and makes no API calls.
- [ ] **Step 6: Browser UI check** on a temporary project, with no keys needed:
  - Seed the thread with a user line plus a breakdown entry through `POST /chat`.
  - Open the project. Expect the card to show as active, the chips to be removable with ×, and Start to be disabled once everything is removed.
  - Reload. Expect the card still active.
  - Seed a following line. Expect the card to show `Replaced by a newer request`.
  - Delete the temporary project afterwards.
