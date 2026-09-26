---
version: 1
slug: "frontend-react-src-pages-project-tsx"
primary_target: "frontend-react/src/pages/Project.tsx"
related_targets: ["frontend-react/src/pages/Projects.tsx","frontend-react/src/components/register/LeadRegister.tsx","frontend-react/src/components/desk/EnquiryDesk.tsx"]
---

## Scope

The two surfaces of the app: the workspace home (`Projects.tsx`) and the base page (`Project.tsx`) — a grid with a persistent enquiry panel on the right carrying Find Leads and Enrich Leads. Visitor mode: **Operate**.

This cycle **replaces the "Lead Register" visual world**. The user pinned Airtable as the visual authority in plain words ("it does not give off an airtable feel; make it more similar to airtable"), which is the standing exit — the category standard, played straight — and beats the roll by contract. The register's ruled-sheet world, its square corners, its three-width Archivo, its drawn boolean marks and its key/folio furniture are all retired. Product truth, data, columns, endpoints and behavior are preserved exactly.

## Audience and job

The operator runs real pipelines against their own OpenAI and Jina keys. The audience that sets the bar is a **prospective Kiyu Labs client watching a live demo** — never seen the tool, will not read instructions, judging whether Kiyu builds finished things.

The Airtable shell is the argument for this change: that audience already knows what a grid with field-type icons, a frozen first field and an expanded record means. Borrowed literacy replaces the outgoing world's need to teach itself.

Job: describe the companies you want in one sentence and watch them arrive; ask one question about every company and watch a column fill in.

## Constraints

- Craft bar, confirmed by the user: **Airtable** (grid density, field-type language, popover craft, expanded records) and **Notion databases** (empty states, inline-editing feel, typographic restraint).
- Kiyu navy `#12305c` is the single accent and takes every place Airtable spends blue. Airtable's own blue, wordmark and logo never appear.
- Enrichment's database shape is fixed (`column_name`, `goal`, `acceptable_evidence`, `result_format`, format-specific rules). The agent fills it; the user never sees it unless they ask.
- Extraction and enrichment are synchronous multi-minute calls. Progress must be real — actual step boundaries, actual counts, actual elapsed time. Never a fabricated per-item counter.
- **No backend work this cycle.** Everything in `backend/`, `api/`, `hooks/`, `store/` and `utils/` is untouched; `buildColumns`' derivation logic is kept and re-expressed as field *types*.
- Toolbar carries only what already works — search, row height, import, export. No Filter/Sort/Group/Hide-fields buttons, because a control that does nothing breaks the demo faster than an emptier toolbar.
- No `+ Add record` row: there is no merged-results create endpoint, and a button that fails is worse than its absence.
- Light only. Airtable is light-first and the product is demoed on projectors and shared screens.

## Direction contract

**THESIS:** The product is a base. It refuses the arrangement the outgoing world committed to — a ruled paper sheet with no boxes, no radius and no vertical rules — and adopts the grid database's own structure wholesale: a sidebar of bases, one table, cells that select and edit under the keyboard, fields that declare their type, records that expand. Convention is the commitment; there is no irony in it and no smuggled quirk. The one thing Airtable does not have is the right-hand enquiry panel where a sentence becomes a column, and that is the product's whole differentiator sitting in the shell's own vocabulary.

**OWN-WORLD:** Airtable's neutral chrome — white content surfaces, a cooler `#f7f7f8` sidebar and view bar, grey gridlines on both axes, near-black text, muted grey secondary. Kiyu navy `#12305c` is the only accent: the 2px cell selection ring, focus, the active sidebar base, the primary button, the active tab, the run progress strip. A six-colour pastel chip set carries boolean answers and base icons; one red for destructive and failure only. Inter as the UI face at 13px, tabular figures scoped to number cells rather than global. System mono carries SQL identifiers, and they move out of the header into the field menu and the expanded record. Radii are Airtable's: 6px on buttons, inputs, popovers and menus, 3px on select chips, 8px on cards, and the 12px rounded top-left seam where the content region meets the sidebar. Grid cells stay square. Rows are 32px by default with Medium and Tall in the row-height menu.

**STORY:** The visitor recognises the shell before they read a word — this is a database of companies with columns. They believe it because the grid shows real counts, real source tallies, real dates and named failures rather than claiming accuracy. They act by typing one sentence into the panel on the right, or by clicking the `+` at the end of the header row, which is the same act.

**FIRST VIEWPORT:** Three columns, full height, no page scroll. Left: a 240px sidebar on `#f7f7f8` — workspace mark, then the bases list (projects), each with a rounded-square coloured icon carrying its initials, the active one a white pill with a navy left accent; `+ Create` at the foot; the API-keys status control in Airtable's account slot at the very bottom, navy when satisfied and red when not. Centre: the white content region behind the 12px rounded top-left seam — base name and one real table tab with its record count, then the view bar (search, row height, import, export, panel toggle), then the grid. The grid rules both axes: a 32px header row where every field shows its type icon and name over a chevron to its field menu, a 66px gutter showing the row number at rest and swapping to checkbox plus expand-arrow on hover, Company frozen left behind a heavier divider, a `+` closing the header row, and the real record count in a footer bar. Right: the 380px enquiry panel behind a hairline — two segmented tabs, the run feed beneath, the composer pinned at the foot as the primary action.

**SIGNATURE INTERACTION:** *A column fills itself.* The `+` at the end of the header row focuses the Enrich composer; on submit a new field appears in the header with its sparkle-marked AI type icon and an empty column beneath it. Then the rows being worked take a navy tint, their target cells carry a small spinner, and each answer fades in as it actually lands, while the panel's step checklist and timestamped log narrate what was really read. Motion is quiet and functional on one ~140ms clock — selection and hover, popovers scale-fading from their own origin, the panel sliding — and all of it collapses under `prefers-reduced-motion`.

**FORM:** Airtable, played straight, as the standing exit taken by the user in plain words; it beats the roll by contract. Direction seed key 877c1072 (assigned index 4 not applicable — a user-pinned direction outranks the assignment). Code-led: no image generation exists in this harness, so ambition rides in this FIRST VIEWPORT block and the named signature interaction.

**FINISH:** unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Memorable moment

Clicking the `+` at the end of the header row, typing "does this clinic have more than one doctor?", and watching a new AI field appear and then ink itself in row by row while the log says which pages were actually read.

## Unresolved

- Whether long operations move to a background job queue; today the composer holds the run and the page must survive a reload mid-run without lying about state.
- Whether a merged-results create endpoint arrives, which is the only thing standing between this and Airtable's `+ Add record` row.
