# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary audience right now is **prospective Kiyu Labs clients being shown the product as a case study** — someone watching a screen share or clicking through a link, who has never seen the tool before and is evaluating whether Kiyu Labs can build them something real. They are not trained on it and will not read instructions.

Secondary, and the person actually driving: the **Kiyu Labs operator** (founder/engineer) running the demo live against their own OpenAI and Jina keys, or using the tool for genuine lead sourcing between demos.

Consequence: every screen has to be self-evident on first sight, and the product has to look finished under someone else's eyes. There is no "the user will learn it" allowance.

## Product Purpose

Discover and qualify potential corporate partners without hand-building lists. The operator describes the kind of organisation they want; the system generates search queries, searches, scrapes result pages, extracts company names, and merges them into one lead table. They then describe a question they want answered about every lead ("do they have more than one doctor?"), and the system researches each lead and writes the answer into a new column.

Success is a populated, exportable table of real companies with real enrichment columns, produced from plain-English input in minutes.

## Positioning

The differentiator is **enrichment as a column, defined in a sentence**. Lead databases sell static fields; this researches an arbitrary, project-specific question per lead against live web sources and returns a typed answer (True/False, Number, or Text) with defined evidence rules. The spreadsheet grows columns the user invents, not columns a vendor shipped.

Bring-your-own-keys is a deliberate position: no server-side credentials, keys live in the browser and travel per request.

## Operating Context

- Work is organised into **projects**. A project owns its queries, scraped URLs, extracted leads, enrichment definitions, and one merged results table.
- Two long-running operations dominate the experience: **lead extraction** (search → scrape → extract, minutes) and **enrichment** (per-lead research, minutes, scales with row count). Both are synchronous HTTP calls today with a 10-minute client timeout, and both are tracked as jobs with a running/completed/failed status.
- Users supply their own **OpenAI** and **Jina** keys through the UI; they are held in `localStorage` and sent as `X-OpenAI-Key` / `X-Jina-Key` headers. Nothing works without them.
- Leads also arrive by **CSV/Excel upload**, mapped onto a lead column and merged with scraped leads into the same table.
- Everything is exportable as CSV inside a ZIP.
- Searches are Australia-focused by design (the query prompt pins Australia and Sydney).

## Capabilities and Constraints

**Confirmed capabilities**
- Project CRUD with per-project counts of leads collected, datasets added, URLs processed.
- AI query generation from a project's `query_search_target`; queries are editable and persisted.
- URL discovery per query, and manual URL add/edit/delete.
- Lead extraction gated on a `lead_minimum_criteria` string that defines what counts as a lead.
- Enrichment definitions with a fixed shape: `enrichment_name`, `column_name` (lowercase SQL identifier), `goal`, `acceptable_evidence`, `result_format` (`True/False` | `Number` | `Text`), plus format-specific rules (`result_true_if` / `result_false_if` / `result_number_value` / `result_text_value`). The backend validates completeness; this shape is not changing.
- Test enrichment (does not persist) and real enrichment (writes a column into merged results).
- Merged results view combining scraped and uploaded leads with all enrichment columns.

**Constraints**
- Backend is FastAPI + PostgreSQL + SQLAlchemy; frontend is React 18 + Vite + TypeScript + MUI 6 + TanStack Query + React Router. Model in use is `gpt-5-mini` via the OpenAI Responses API and the Agents SDK.
- `column_name` must be lowercase alphanumeric with underscores and cannot start with a digit.
- No authentication or multi-tenancy. No background worker; long operations block the request.
- Deployed frontend on Vercel, backend on Render, CORS origins configurable.

**Decided in this cycle**
- The step-by-step pages (Collect Leads, Enrichments list, Review Leads, Review/Test Enrichment) are **replaced**, not kept as a fallback. The product becomes: a projects page, and a project page that is a table plus a chat with Find Leads and Enrich Leads tabs.
- A new backend endpoint drafts a complete enrichment configuration from one plain-English sentence, using the caller's OpenAI key. The resulting columns and database shape are unchanged.
- Find Leads runs the full pipeline from one sentence and streams its progress rather than asking for confirmation.
- Table cells are editable and rows deletable, which requires a merged-results write endpoint.
- CSV/Excel import is a toolbar action above the table, not a chat capability.

**Undecided**
- Whether the product ever gets accounts, sharing, or multi-tenancy.
- Whether long operations move to a background job queue with polling.

## Brand Commitments

Product name in the UI today is **AI Lead Generator**; the company behind it is **Kiyu Labs**.

The user supplied the Kiyu Labs marketing site as a binding colour reference: deep navy as the primary and button colour, a pale blue-grey section tint, near-black body text, white surfaces, and navy used for links and eyebrow labels. Type on the site is a geometric sans with a tall x-height. These are colour and identity constraints carried over from the brand, not a design direction for this product.

## Evidence on Hand

- A working backend with real endpoints and a real database schema; nothing about the pipeline needs to be faked.
- A public demo video: https://www.youtube.com/watch?v=GLnULm-Nle4
- The Kiyu Labs marketing site screenshots supplied in this request.
- No customer logos, testimonials, usage statistics, pricing, or benchmarks exist for this product. Do not fabricate any. The marketing-site testimonials belong to Kiyu Labs the agency and must not be restaged inside the product UI.

## Product Principles

1. **One sentence in, a column out.** Anything the user has to configure by hand is a failure of the agent behind it. Structured fields still exist in the database; they should not be the user's problem.
2. **The table is the product.** Every operation is judged by what it does to the grid. Chat is the input device, not the destination.
3. **Long waits must read as work.** Operations take minutes. Silence during them is the single biggest credibility risk in a live demo; visible progress is a feature, not a nicety.
4. **Legible to a stranger on a screen share.** No jargon labels, no unlabelled icons, no state that needs narration.
5. **Never invent results.** Extraction and enrichment report what they actually found, including failures, skips, and empty answers.

## Accessibility & Inclusion

No product-specific standard has been established. Baseline expectation only: the product is demoed on shared screens and projectors, so text contrast and target size must hold up at a distance and under compression.
