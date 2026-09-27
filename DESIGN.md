---
name: AI Lead Generator
description: A grid database played straight — Airtable's structure in Kiyu navy, where one sentence becomes a column.
colors:
  accent: "#12305c"
  accent-hover: "#0c2244"
  accent-soft: "#e7edf6"
  accent-tint: "#f3f6fb"
  surface: "#ffffff"
  surface-2: "#fbfbfc"
  surface-hover: "#f5f5f7"
  chrome: "#f7f7f8"
  chrome-hover: "#ececed"
  line: "#e3e3e6"
  line-2: "#ededf0"
  line-strong: "#d2d2d8"
  text: "#1d1d1f"
  text-2: "#666670"
  placeholder: "#71717a"
  text-3: "#a1a1aa"
  danger: "#b3261e"
  danger-hover: "#8f1e18"
  danger-soft: "#fdeceb"
  success: "#1d6b3f"
  warning: "#8a5a12"
  warning-soft: "#fdf4e5"
  chip-yes-bg: "#d6f5d9"
  chip-yes-ink: "#17501f"
  chip-no-bg: "#ffdedb"
  chip-no-ink: "#8a2318"
  chip-flat-bg: "#ebebef"
  chip-flat-ink: "#45454f"
  base-icon-navy: "#12305c"
  base-icon-teal: "#0f6f62"
  base-icon-violet: "#5b43b8"
  base-icon-amber: "#9c5410"
  base-icon-rose: "#a52c50"
  base-icon-green: "#246b39"
  selection-bg: "#c9d7ec"
typography:
  title:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "-0.008em"
  heading:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "15px"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "-0.006em"
  body:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  body-secondary:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "12.5px"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "normal"
  meta:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "11.5px"
    fontWeight: 400
    lineHeight: 1.3
    letterSpacing: "normal"
  label:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.05em"
  numeric:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: "tabular-nums"
  identifier:
    fontFamily: "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"
    fontSize: "11.5px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
rounded:
  sm: "3px"
  md: "6px"
  lg: "8px"
  seam: "12px"
  square: "0px"
spacing:
  "2": "2px"
  "4": "4px"
  "6": "6px"
  "8": "8px"
  "10": "10px"
  "12": "12px"
  "14": "14px"
  "16": "16px"
  "24": "24px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "#ffffff"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "0 11px"
    height: "30px"
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
    textColor: "#ffffff"
  button-plain:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "0 11px"
    height: "30px"
  button-plain-hover:
    backgroundColor: "{colors.surface-hover}"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.text-2}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "0 11px"
    height: "30px"
  button-quiet-hover:
    backgroundColor: "{colors.chrome-hover}"
    textColor: "{colors.text}"
  button-danger-solid:
    backgroundColor: "{colors.danger}"
    textColor: "#ffffff"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "0 11px"
    height: "30px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "6px 9px"
    height: "32px"
  chip-yes:
    backgroundColor: "{colors.chip-yes-bg}"
    textColor: "{colors.chip-yes-ink}"
    rounded: "{rounded.sm}"
    padding: "2px 8px"
  chip-no:
    backgroundColor: "{colors.chip-no-bg}"
    textColor: "{colors.chip-no-ink}"
    rounded: "{rounded.sm}"
    padding: "2px 8px"
  chip-neutral:
    backgroundColor: "{colors.chip-flat-bg}"
    textColor: "{colors.chip-flat-ink}"
    rounded: "{rounded.sm}"
    padding: "2px 8px"
  segmented-item:
    backgroundColor: "transparent"
    textColor: "{colors.text-2}"
    rounded: "4px"
    padding: "0 11px"
    height: "26px"
  segmented-item-selected:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.accent}"
  grid-cell:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    typography: "{typography.body}"
    rounded: "{rounded.square}"
    padding: "0 8px"
    height: "32px"
  grid-cell-selected:
    backgroundColor: "{colors.accent-soft}"
  grid-head-cell:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.text}"
    rounded: "{rounded.square}"
    padding: "0 8px"
    height: "32px"
  nav-item:
    backgroundColor: "transparent"
    textColor: "{colors.text}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "6px 30px 6px 8px"
  nav-item-active:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.accent}"
  base-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.lg}"
    padding: "14px"
  popover:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "5px"
  toast:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "11px 11px 11px 13px"
---

# Design System: AI Lead Generator

## Overview

**Creative North Star: "The Straight Base"**

This is a grid database that admits it is a grid database. The shell is the category standard — a sidebar of bases, one content region behind a rounded seam, one table ruled on both axes, cells that select and edit under the keyboard, fields that declare their type with an icon, records that expand. Nothing is stylised, ironised, or given a private twist. Convention is the commitment: a stranger watching a screen share recognises the arrangement before they read a word, and that borrowed literacy is what buys the product the right to be judged on what it actually does.

Density is the second commitment. Rows are 32px, body type is 13px, chrome type steps down to 12.5, 12, and 11.5, and the neutral palette is nearly all greys within six points of each other. The screen is quiet so the data is loud. Depth is almost absent: one hairline everywhere, one low card shadow, and heavier shadows reserved for things that genuinely float over the sheet — popovers, the cell editor, modals, the frozen-column edge.

Against that grey, one accent does all the work. Kiyu navy `#12305c` takes every place the category would spend its own blue: the 2px cell selection ring, focus rings, the active base pill's label, the primary button, the active view tab's 2px underline, the run progress strip, the checked checkbox, the AI field's sparkle. Two colour sets earn exceptions — a three-tone select-chip set sized to exactly what a boolean enrichment can return, and a six-colour base-icon set keyed deterministically off base id so a base keeps its colour across the sidebar, the home grid, and reloads. Confirmed anti-reference: the retired "Lead Register" world — its ruled paper sheet with no boxes, no radius and no vertical rules — and Airtable's own blue, wordmark and logo, which never appear.

**Key Characteristics:**
- Grid-database convention played straight, with no smuggled quirk
- One accent, Kiyu navy, and no second hue competing for it
- 13px Inter, 32px rows, hairline rules on both axes
- Near-flat: tonal layering first, shadow only for things that actually float
- Colour only where the data is categorical — chips and base icons — never as decoration
- One 140ms clock and one easing curve for everything that moves

## Colors

A near-monochrome grey chrome carrying one deep navy accent, with saturated colour admitted only where it encodes a value.

### Primary
- **Kiyu Navy** (`{colors.accent}`): The single accent. It is the 2px inset cell selection ring, the focus outline, the primary button fill, the active view tab's 2px underline, the active base's label in the sidebar, the checked checkbox, the caret in every input and editor, the AI field's sparkle icon, and the progress strip. Nothing else is ever accented.
- **Navy Pressed** (`{colors.accent-hover}`): Hover on solid navy surfaces and on links; also the ink inside a text selection.
- **Navy Wash** (`{colors.accent-soft}`): The 3px focus halo around inputs, the ground of a selected row, the progress strip's track, and the empty-state glyph plate.
- **Navy Breath** (`{colors.accent-tint}`): The tint on a row the run is working now, on a hovered example prompt, and behind the expanded record's working note.

### Secondary
- **Select Chip, Yes** (`{colors.chip-yes-bg}` on `{colors.chip-yes-ink}`): A pastel mint plate with its own dark ink, for a True answer in a single-select field.
- **Select Chip, No** (`{colors.chip-no-bg}` on `{colors.chip-no-ink}`): A pastel rose plate, deliberately a different token from danger red.
- **Select Chip, Neutral** (`{colors.chip-flat-bg}` on `{colors.chip-flat-ink}`): Every other select value, including the one an enrichment could not establish.

### Tertiary
- **Base Icons** (`{colors.base-icon-navy}`, `{colors.base-icon-teal}`, `{colors.base-icon-violet}`, `{colors.base-icon-amber}`, `{colors.base-icon-rose}`, `{colors.base-icon-green}`): Six saturated grounds for the rounded-square initials tile that identifies a base. Assigned deterministically from the base id, so a base keeps its colour in the sidebar, on the home grid, and across reloads. These are identity marks, never status.

### Neutral
- **White Content** (`{colors.surface}`): The content region, the grid's rows, cards, popovers, modals, toasts.
- **Strip Grey** (`{colors.surface-2}`): Header and footer strips — the view bar, the grid's header row, the footer tally bar, the modal foot, and the ground below the last record so the table has a visible end.
- **Row Hover** (`{colors.surface-hover}`): A hovered grid row.
- **Chrome** (`{colors.chrome}`): The sidebar and the ground the whole app sits on.
- **Chrome Hover** (`{colors.chrome-hover}`): Hover on quiet buttons, popover items and header-cell affordances.
- **Rule** (`{colors.line}`): The standard hairline — bar edges, card and popover borders, the frozen column's neighbours.
- **Rule Faint** (`{colors.line-2}`): Gridlines between cells and between rows; the quietest divider in the system.
- **Rule Firm** (`{colors.line-strong}`): Input borders, the header row's bottom edge, the frozen column's right edge, dashed new-base cards.
- **Ink** (`{colors.text}`): All primary reading text and cell values.
- **Ink Secondary** (`{colors.text-2}`): Labels, meta counts, hints, field labels, icons in chrome.
- **Placeholder Ink** (`{colors.placeholder}`): Input placeholders, held lighter than secondary ink but still at reading contrast because a placeholder is read.
- **Ink Faint** (`{colors.text-3}`): Empty-cell em dashes, disabled glyphs, log timestamps. Nothing a user must read.
- **Text Selection** (`{colors.selection-bg}`): The browser's own selection ground, themed to the accent family rather than left at system blue.

### Status
- **Danger** (`{colors.danger}` / `{colors.danger-hover}` / `{colors.danger-soft}`): Destructive actions and failures only — delete items, failed pipeline steps, error log lines, the missing-keys state.
- **Success** (`{colors.success}`): The completed-step mark in the run checklist.
- **Warning** (`{colors.warning}` / `{colors.warning-soft}`): The blocked-composer notice when a run cannot start.

### Named Rules

**The One Blue Rule.** Kiyu navy is the only accent in the system. Wherever the category would spend its own blue, spend this navy; there is no second accent hue and no decorative use of colour anywhere in the chrome.

**The Reserved Red Rule.** Red means destructive or failed, and nothing else. The rose select chip is a separate token with its own ink precisely so a "No" answer never reads as an error.

**The Colour-Is-Data Rule.** Saturated colour appears only where it encodes something: a select value, or a base's identity. A surface, a border, or a piece of chrome never gets colour for interest.

## Typography

**UI Font:** Inter (with `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, Roboto, sans-serif), at weights 400 / 500 / 600
**Identifier Font:** System mono (`ui-monospace`, SFMono-Regular, SF Mono, Menlo, Consolas)

**Character:** One neutral grotesque carrying the entire interface, set small and tight. There is no display face and no type contrast for drama; hierarchy is carried by half-point size steps, three weights, and grey. The only second face is system mono, and it is a signal rather than a style.

### Hierarchy
- **Title** (600, 16px, 1.4, `-0.008em`): Empty-state headings — the largest type in the product.
- **Heading** (600, 15px, 1.4, `-0.006em`): The base name in the base bar, the expanded record's title, modal headings.
- **Subhead** (600, 13–13.5px): Base card names, the workspace name, the panel heading, the active view tab.
- **Body** (400, 13px, 1.5): Cell values, popover items, input text, sidebar links, button labels (500). The system's default.
- **Body Secondary** (400, 12.5px, 1.55): Notes, hints, run steps, modal descriptions, empty-state bodies.
- **Meta** (400, 11.5–12px): Row numbers, record counts, source tallies, timestamps, the footer bar.
- **Label** (600, 11px, `0.05em`, uppercase): Section labels only — `BASES` in the sidebar, popover group headings, the run's request header, the expanded record's working note, the toast kind. Never a headline's companion.
- **Numeric** (tabular figures, 13px): Number cells, row numbers, and counts.
- **Identifier** (system mono, 11–11.5px): The real database column name in the field menu and the expanded record, and the log's timestamps.

### Named Rules

**The Scoped Figures Rule.** Tabular figures are applied to number cells, counts, row numbers and timestamps individually — never globally on `body`. Prose keeps proportional figures.

**The Mono-Means-Machine Rule.** System mono says "this string belongs to the database or the machine, not to you." It carries SQL identifiers, which live in the field menu and the expanded record, and the log's elapsed timestamps. A mono identifier never appears in a column head — the head carries the human field name.

**The One Face Rule.** Inter carries every human-readable string at every size. There is no display face, no second sans, and no type effect; a size step and a weight step are the only hierarchy devices.

## Layout

The app is a CSS grid of full-viewport height (`100dvh`) with no page scroll: a fixed 240px sidebar, a flexible content region, and — when open — a fixed 380px enquiry panel. The content region is itself a four-row grid: base bar (47px), view bar (40px), scrolling grid, footer tally bar (33px). Every region scrolls inside itself.

The content region meets the sidebar at a 12px rounded top-left seam over a 1px rule on its left and top edges — the shell's signature, and the only place a large radius appears.

**The view bar folds the tab strip in.** With exactly one real table and no saved views, the table tab sits in the same 40px bar as search, row height, import, export and the panel toggle, rather than claiming a third bar of its own.

**The grid** rules both axes: a 32px sticky header row on strip grey over a firm rule; a 66px gutter frozen left carrying the row number at rest; the Company field frozen beside it behind a heavier divider that casts a shadow once scrolled; 32px rows separated by the faintest rule; a `+` closing the header row; and strip grey below the last record so the table visibly ends. Column widths are set per field type (number 112px, select 164px, text 184px, long text 216px, Company 248px) so a real field name reads in its head. Row height is user-switchable — Default clips to one line, Medium clamps to two, Tall to four, and at Medium and Tall the cell content and the gutter both top-align together.

**Spacing rhythm** is a 2px ladder; 6, 8, 12 and 14 do nearly all the work. Control heights are 26px (compact), 28px (search, chips), 30px (buttons) and 32px (inputs, rows, header).

**Responsive behaviour is structural, not fluid.** At 1180px the enquiry panel stops being a column and becomes an overlay drawer over a scrim. At 1000px the sidebar becomes a slide-over with its own scrim and the seam flattens to square. At 720px the view bar keeps every control's text label and scrolls horizontally behind a 26px trailing mask, the primary "Ask the agent" toggle is reordered to lead that bar, the footer tallies switch to abbreviated strings, the expanded record's field rows stack, and the panel goes full width.

### Named Rules

**The Whole-Band Rule.** Sticky and frozen cells carry the row's background explicitly at every state, so a hovered, selected or working row reads as one unbroken band across the freeze line rather than two differently coloured halves.

**The Structural Breakpoint Rule.** At a breakpoint, a region changes what it *is* — column becomes drawer, bar becomes scroller. Nothing merely shrinks, and no control drops its text label to become an unlabelled icon.

## Elevation & Depth

Near-flat, tonal first. Depth is normally carried by three greys and a hairline: chrome behind, white content in front, strip grey for headers and footers. Shadow is not decoration here — it appears only when something genuinely sits above the sheet, and every shadow is soft-blurred with a small downward offset in a single cool-black (`rgba(20, 24, 35, …)`). There are no hard offset shadows anywhere in this world.

### Shadow Vocabulary
- **Card** (`0 1px 2px rgba(20,24,35,0.06), 0 1px 1px rgba(20,24,35,0.04)`): The barely-there lift under a raised control — the plain and primary buttons, the selected segment, the active base pill, a base card at rest. Removed entirely on `:active`, which is the press.
- **Card Raised** (`0 6px 16px -6px rgba(20,24,35,0.16), 0 2px 4px rgba(20,24,35,0.06)`): A base card on hover, paired with a 1px lift.
- **Popover** (`0 6px 20px -6px rgba(20,24,35,0.20), 0 1px 3px rgba(20,24,35,0.10)`): Menus, field menus, toasts.
- **Cell Editor** (`0 6px 16px -4px rgba(20,24,35,0.30), 0 2px 4px rgba(20,24,35,0.12)`): The cell being typed into, which must read as lifted off the sheet rather than merely selected.
- **Modal** (`0 24px 56px -16px rgba(20,24,35,0.32), 0 2px 8px rgba(20,24,35,0.10)`): Dialogs, and the panel and sidebar when they become drawers.
- **Frozen Edge** (`3px 0 7px -3px rgba(20,24,35,0.12)`): Cast rightward from the frozen columns, and only once the grid is actually scrolled horizontally.

### Named Rules

**The Earned Shadow Rule.** A shadow means the element is above the sheet. Flat chrome — bars, rows, cells, the sidebar — never takes one; a pressed button gives its shadow back.

**The Scrim Rule.** Anything overlaying the whole app sits on `rgba(20, 24, 35, 0.32–0.34)`, never on pure black.

## Shapes

Four radii and a square. Buttons, inputs, popovers, menus, the search field, the sidebar's pills and the composer take 6px. Select chips take 3px. Cards, modals, the empty-state glyph plate and the empty-state step list take 8px. The content region's top-left seam takes 12px and is the only large radius in the system. **Grid cells are square** — that is what makes the table read as a table, and the cell editor's 2px navy border keeps a near-square 2px radius for the same reason.

Small internal squares follow the same logic at reduced scale: 4px on popover items, header-cell affordances and small icon buttons; 5px on the sidebar's 22px base tile; 3px on the checkbox; full circles only for the account-slot dot and the numbered step markers.

Borders are a single hairline, never doubled and never thicker than 1px — with three deliberate exceptions, all of them state: the 2px inset navy ring on a selected cell, the 2px navy border on an open cell editor, and the 2px navy underline on the active view tab. The one dashed border in the system marks the "create a base" card as a slot rather than an object.

Icons are a single inline SVG set on a 16px grid at 1.5px stroke with round caps and joins. Field-type glyphs carry the most weight: they are how a column declares what it holds before anyone reads a value, and an AI-written field swaps its type glyph for a navy sparkle.

## Components

### Buttons
- **Shape:** Softly rounded (6px), 30px tall, 11px side padding, 6px gap to an icon. A compact variant drops to 26px / 9px / 12.5px; an icon-only button becomes a square of the same height.
- **Primary:** Navy fill, white label, card shadow. The single primary action per region — Find leads, Enrich, Create, Save.
- **Plain:** White fill, hairline border, ink label, card shadow. The default.
- **Quiet:** Transparent with secondary ink; picks up chrome-hover grey and full ink on hover. Every toolbar and chrome control.
- **Danger / Danger Solid:** White with red ink and a red-wash hover for a menu-level destructive action; solid red with white label for the confirmed one.
- **Hover / Focus / Press:** Background, border and shadow cross-fade on the one 140ms clock; `:active` removes the shadow; focus is the global 2px navy outline at 1px offset. Disabled drops to 45% opacity and loses its shadow.
- **Loading:** The button's own icon slot becomes a spinner and the control disables itself — the label never changes.

### Chips
- **Select value chip:** A pastel plate with matching dark ink at 3px radius, 2px/8px padding, 12px/500 type, ellipsised at the cell width. Three tones only: yes (mint), no (rose), neutral (grey).
- **Picker chip:** A 28px, 6px-radius white pill with a hairline border used for column selection on the import sheet; when active it inverts to solid navy with a white label.

### Cards / Containers
- **Corner Style:** 8px.
- **Background:** White on the chrome ground; the "create a base" slot is transparent with a dashed firm-grey border that turns navy over a navy-breath wash on hover.
- **Shadow Strategy:** Card at rest, Card Raised plus a 1px translate on hover (see Elevation).
- **Border:** One hairline, firming to `line-strong` on hover.
- **Internal Padding:** 14px, with a 38px coloured base tile, the name, an optional two-line clamped note, and a meta line pinned to the foot.

### Inputs / Fields
- **Style:** White, 6px radius, a firm-grey 1px border, 32px minimum height, 13px text, navy caret. Labels sit above at 12px/500 secondary ink; hints below at 12px.
- **Focus:** Border turns navy and a 3px navy-wash halo appears — no outline, no glow, no movement.
- **Search:** A borderless 28px control that fills with chrome-hover on hover and becomes a bordered white field with the same navy halo on focus-within; its input widens from 96px to 130px on phones when focused.
- **Disabled:** Chrome fill, secondary ink, not-allowed cursor.

### Navigation
- **Sidebar:** 240px on chrome grey. A workspace mark (navy rounded square with initials) over the workspace name and role line; an uppercase 11px `BASES` section label with a count; then the base list. Each item is a 6px-radius row with a 22px coloured initials tile, an ellipsised name, and a right-aligned tabular record count.
- **Active state:** The item becomes a **raised white pill** (white fill plus card shadow) with its name and count in navy. There is no accent bar down its side — that reads as a mark placed beside the item rather than as the item's own state.
- **Hover:** A flat `#ececee` wash; the `…` overflow control appears at the right.
- **Foot:** `+ Create a base`, then the API-keys status control in the account slot — a navy-wash dot when satisfied, red-wash with red ink when keys are missing.
- **Mobile:** Below 1000px the sidebar becomes a slide-over with a modal shadow over a scrim, revealed by a toggle in the base bar.

### The Grid
The product's centre of gravity. A sticky strip-grey 32px header row where each field shows its type icon (or a navy sparkle if an agent wrote it) beside its name, with a chevron to its field menu absolutely positioned at the right so it costs the name no width. A 66px gutter frozen at the left shows the tabular row number at rest and swaps it — via `display`, not opacity — for a checkbox plus an expand button on hover, on focus-within, when the row is selected, or for every row while any selection exists. The Company field is frozen beside the gutter behind a firm rule that casts a rightward shadow once scrolled. Cells are square, 8px padded, divided by the faintest rule on both axes; number cells are right-aligned and tabular; an empty cell shows a faint em dash.

- **Selected cell:** A 2px navy ring drawn inside the cell, over the gridlines.
- **Editing cell:** An absolutely positioned editor with a 2px navy border and the cell-editor shadow, growing to at least 232px wide and flipping to open leftward in the rightmost columns.
- **Row states:** hover grey, navy-soft when selected, navy-tint while the run is working that row — each carried across the frozen cells too.

### Enquiry Panel
380px behind a hairline on the right: a 47px head, two segmented tabs, the scrolling run feed, and the composer pinned at the foot with its textarea, status line and primary button. When a run is live, a 2px navy strip sits under the tabs with a 38% bar sweeping across a navy-wash track. The feed is a step checklist — a faint dash at rest, a navy spinner while running, a green check when done, red when failed — over a timestamped log in mono time and 12px text.

### Field Menu
A 6px-radius popover that scale-fades in from its own top-left origin. Uppercase 11px group labels, 13px items with a 4px radius and a chrome-hover wash, a navy check mark on the current choice, faint rules between groups, and — at the foot — the field's real database column name in system mono, which is the only place besides the expanded record where an identifier is shown.

### Toasts
Bottom-right, up to 376px, white with a hairline and the popover shadow, sliding up 8px on entry. An 11px uppercase kind label over 12.5px pre-wrapped text.

### Named Rules

**The Display-Not-Opacity Rule.** A control that is hidden until hover is removed from the document with `display: none`, never faded with `opacity: 0`. A transparent element left in the layer still swallows every click aimed at what is underneath it. Its replacement occupies the same width so nothing shifts.

**The One Pending Mark Rule.** A spinner appears only in the one field actually being filled. A blank cell in any other column is a finished empty answer and never borrows the pending mark.

**The Honest Progress Rule.** Progress is never a percentage. The pipeline has no percentage to report, so live work is shown as an indeterminate sweep plus real step boundaries, real counts, real elapsed time and named failures.

**The One Clock Rule.** Every transition and animation runs at 140ms on `cubic-bezier(0.16, 1, 0.3, 1)`: hover, selection, the popover's scale-fade from its own origin, the settle of an arriving answer, the drawers. The only exceptions are the two loops that must keep looping — the 720ms spinner and the 1.5s progress sweep. Everything collapses to 1ms under `prefers-reduced-motion`, where the spinner slows rather than stopping.

## Do's and Don'ts

### Do:
- **Do** spend Kiyu navy (`{colors.accent}`) wherever the grid-database convention would spend its own blue, and nowhere else.
- **Do** cut every button, input, chip and empty state from the shared control vocabulary, so the same action never looks like two different things on two surfaces.
- **Do** scope tabular figures to number cells, counts, row numbers and timestamps individually.
- **Do** keep system mono for machine strings — SQL identifiers in the field menu and expanded record, and log timestamps.
- **Do** repaint the row background explicitly on sticky and frozen cells for every row state, so a band never breaks at the freeze line.
- **Do** remove hover-revealed controls with `display: none` and give the replacement the same width.
- **Do** run every transition at 140ms on `cubic-bezier(0.16, 1, 0.3, 1)` and let `prefers-reduced-motion` collapse it.
- **Do** keep grid cells square; reserve the 12px radius for the content region's top-left seam alone.
- **Do** let a breakpoint change what a region is — column to drawer, bar to horizontal scroller — rather than shrinking it.
- **Do** use the 11px uppercase label for section headings only (`BASES`, popover groups, the run's request header).

### Don't:
- **Don't** introduce a second accent hue. The only saturated colour beyond navy is the three-tone select chip set and the six-colour base-icon set, and both encode data.
- **Don't** use red for anything but destructive actions and failures; the rose "No" chip is a separate token for exactly this reason.
- **Don't** render a percentage, a fake per-item counter, or any progress number the pipeline cannot actually report.
- **Don't** put a pending spinner in any cell other than the one field being filled.
- **Don't** hide an interactive control with `opacity: 0` while leaving it in the layer.
- **Don't** put a mono identifier in a column head — the head carries the human field name.
- **Don't** put an accent bar down the side of a list item; the active item is a raised white pill with a navy label.
- **Don't** apply tabular figures globally to `body`.
- **Don't** give flat chrome a shadow, or use a hard offset shadow anywhere — every shadow in this world is soft-blurred cool black.
- **Don't** drop a control's text label to an unlabelled icon at a narrow width; let the bar scroll instead.
- **Don't** ship a control that does nothing to make a bar look fuller.
