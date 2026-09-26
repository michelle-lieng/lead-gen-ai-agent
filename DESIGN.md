---
name: Lead Register
description: A printed business register on a pale blue desk — ruled listings, one institutional ink, nothing in a box.
colors:
  navy: "#12305c"
  navy-deep: "#0c2244"
  navy-mid: "#1e4a87"
  navy-wash: "#dde6f4"
  navy-tint: "#eef3fa"
  ink: "#14181f"
  ink-2: "#4a5768"
  ink-3: "#8a97a9"
  ink-placeholder: "#66748a"
  spot: "#a6371f"
  spot-wash: "#fbeeea"
  paper: "#ffffff"
  paper-hover: "#f6f9fd"
  ground: "#e6ecf6"
  ground-deep: "#d8e1ef"
  hairline: "#ccd6e6"
  hairline-2: "#e2e9f3"
  success-ink: "#1d5f3f"
  success-wash: "#eef6f1"
  warning-ink: "#8a5a12"
  warning-wash: "#fbf3e6"
typography:
  display:
    fontFamily: "Archivo, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "20px"
    fontWeight: 600
    lineHeight: 1.45
    letterSpacing: "-0.012em"
    fontVariation: "'wdth' 118"
  headline:
    fontFamily: "Archivo, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "15px"
    fontWeight: 600
    lineHeight: 1.45
    letterSpacing: "-0.008em"
    fontVariation: "'wdth' 100"
  title:
    fontFamily: "Archivo, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1.45
    letterSpacing: "0.14em"
    fontVariation: "'wdth' 118"
  body:
    fontFamily: "Archivo, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: "normal"
    fontVariation: "'wdth' 100"
    fontFeature: "'tnum' 1, 'lnum' 1"
  listing:
    fontFamily: "Archivo, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "13.5px"
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: "0.002em"
    fontVariation: "'wdth' 80"
    fontFeature: "'tnum' 1, 'lnum' 1"
  label:
    fontFamily: "Archivo, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "10px"
    fontWeight: 600
    lineHeight: 1.45
    letterSpacing: "0.1em"
    fontVariation: "'wdth' 100"
  mono:
    fontFamily: "Azeret Mono, ui-monospace, Cascadia Mono, Consolas, monospace"
    fontSize: "10px"
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: "-0.02em"
rounded:
  none: "0"
  tab: "2px 2px 0 0"
spacing:
  hair: "2px"
  xs: "4px"
  sm: "6px"
  md: "8px"
  lg: "10px"
  xl: "12px"
  xxl: "14px"
  sheet: "18px"
  section: "22px"
  margin: "28px"
components:
  button-primary:
    backgroundColor: "{colors.navy}"
    textColor: "#ffffff"
    rounded: "{rounded.none}"
    padding: "0 12px"
    height: "30px"
    typography: "{typography.body}"
  button-primary-hover:
    backgroundColor: "{colors.navy-deep}"
    textColor: "#ffffff"
  button-plain:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "0 12px"
    height: "30px"
  button-plain-hover:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.navy}"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.none}"
    padding: "0 12px"
    height: "30px"
  button-quiet-hover:
    backgroundColor: "{colors.navy-tint}"
    textColor: "{colors.navy}"
  button-danger:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.spot}"
    rounded: "{rounded.none}"
    padding: "0 12px"
    height: "30px"
  button-danger-hover:
    backgroundColor: "{colors.spot-wash}"
    textColor: "{colors.spot}"
  button-compact:
    height: "24px"
    padding: "0 8px"
  input-field:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "6px 9px"
    height: "30px"
  input-field-disabled:
    backgroundColor: "{colors.navy-tint}"
    textColor: "{colors.ink-2}"
  chip:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.none}"
    padding: "4px 9px"
  chip-active:
    backgroundColor: "{colors.navy}"
    textColor: "#ffffff"
    rounded: "{rounded.none}"
    padding: "4px 9px"
  thumb-tab:
    backgroundColor: "#dbe4f2"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.tab}"
    padding: "0 12px"
    height: "30px"
    typography: "{typography.label}"
  thumb-tab-active:
    backgroundColor: "{colors.navy}"
    textColor: "#ffffff"
    rounded: "{rounded.tab}"
  section-bar:
    backgroundColor: "{colors.navy}"
    textColor: "#ffffff"
    rounded: "{rounded.none}"
    padding: "0 10px"
    height: "26px"
    typography: "{typography.title}"
  register-row:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    padding: "4px 12px"
    height: "34px"
    typography: "{typography.listing}"
  register-row-working:
    backgroundColor: "{colors.navy-tint}"
  register-row-head:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink-2}"
    height: "38px"
    typography: "{typography.label}"
  notice:
    backgroundColor: "{colors.navy-tint}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "9px 10px 10px"
    width: "min(384px, calc(100vw - 36px))"
---

# Design System: Lead Register

## Overview

**Creative North Star: "The Business Register"**

This is a page of a printed business register, not a SaaS data grid. A white sheet sits on a pale blue desk and carries a running head, a reversed-out section bar, a ruled listing, a key and a folio. Nothing is contained in a box. Structure comes from horizontal hairlines and alignment, and where two things must be separated, a rule separates them — never a card, never a radius, never an ambient shadow floating a panel over a grey canvas.

The density is institutional. Rows are 34px, the listing is set at 13.5px in a narrow width so more columns fit without shrinking the face, figures are tabular everywhere so columns of numbers stack, and the interface tells the truth in counts, dates and named failures rather than in reassurance. Colour is scarce by construction: one institutional navy does rules, reversed bars, focus and primary actions; near-black does text; a single spot red is held back for failure and destructive intent. The confirmed anti-reference is the lead-tool default — grey canvas, rounded cards, boxed cells, drop-shadowed panels, floating icon buttons.

Motion is a grammar of three moves on one 160ms clock: an answer inking in, a rule drawing left to right, and a single navy setting rule travelling down the gutter to the entry being worked. There is no loading skeleton, no pulse, no loop. Everything is suppressed under `prefers-reduced-motion`.

**Key Characteristics:**
- One institutional ink (navy #12305c), one text ink, one spot red held for failure
- Structure from horizontal hairlines and alignment; no cell borders, no card borders
- Square corners everywhere (0 radius) except the 2px outer cut of a thumb-index tab
- Archivo across three widths — expanded, regular, narrow — with weight held nearly constant
- Tabular lining figures globally; Azeret Mono reserved for machine column identifiers
- Exactly three motions on one 160ms clock
- Every icon and every boolean mark is drawn for this world, never a library glyph or a Unicode bullet

## Colors

A single navy institutional ink on white paper over a pale blue desk, with one earthen red as the second ink and nothing else.

### Primary
- **Register Navy** (`{colors.navy}`): The institutional ink. Heavy rules under the running head and the column head, reversed section bars, primary action fills, focus outlines, the travelling setting rule, the caret, the selection highlight, the key marks and the browser theme colour.
- **Navy Deep** (`{colors.navy-deep}`): The pressed state of a primary action, and the base of every translucent overlay and cast shadow (`#0c2244` at 33–40% alpha).
- **Navy Mid** (`{colors.navy-mid}`): Links at rest, the editable-cell hover underline, and the right-hand counts on a reversed bar's quiet variant.
- **Navy Wash / Navy Tint** (`{colors.navy-wash}` / `{colors.navy-tint}`): The two navy papers. Tint backs the enquiry desk, the working entry, the footnote under an entry, the key strip, the modal footer and inline notes. Wash is a softened border for a satisfied status control.

### Secondary
- **Register Red** (`{colors.spot}`): The second ink. It appears only on failure and destructive intent — a failed step in the clerk's log, an error line, a destructive action's label, a missing-keys status. It never marks "live" or "in progress"; running work is navy tint.
- **Red Wash** (`{colors.spot-wash}`): The ground behind a red-inked notice or a hovered destructive control.

### Tertiary
- **Notice Green / Notice Amber** (`{colors.success-ink}` / `{colors.warning-ink}` with their washes): Used nowhere but the notice slips, where severity has to read at a glance from the 2px rule at the slip's head.

### Neutral
- **Paper** (`{colors.paper}`): The sheet. Every listing, toolbar, modal and composer sits on it.
- **Paper Hover** (`{colors.paper-hover}`): The only row-hover tone, carried into the sticky and frozen cells so a hovered entry reads as one unbroken line.
- **Desk Blue / Desk Blue Deep** (`{colors.ground}` / `{colors.ground-deep}`): The desk the sheet lies on — the page background, the running head strip and the thumb-tab rail.
- **Text Ink** (`{colors.ink}`): Body and listing values.
- **Secondary Ink** (`{colors.ink-2}`): Column heads, labels, folio, timestamps, supporting prose, quiet controls.
- **Inactive Ink** (`{colors.ink-3}`): Inactive rules and empty-cell marks.
- **Placeholder Ink** (`{colors.ink-placeholder}`): Placeholders only, held at 4.7:1 on paper because placeholders in this world are read, not decoration.
- **Hairline / Hairline Light** (`{colors.hairline}` / `{colors.hairline-2}`): Three rule weights and only three — hairline-light separates entries, hairline separates regions and outlines controls, a 1–2px navy rule opens a column head or closes a running head or section.

### Named Rules
**The Two Inks Rule.** Navy is the institution and near-black is the text. The spot red is the second ink and is spent only on failure and destruction — if a state is merely busy, important or new, it gets navy or navy tint, never red.

**The Three Rule Weights Rule.** Exactly three: `#e2e9f3` between entries, `#ccd6e6` between regions and around controls, navy at 1–2px to open a head or close a section. A fourth weight is drift.

## Typography

**Display Font:** Archivo variable (with `ui-sans-serif`, `system-ui`, `-apple-system`, `Segoe UI`)
**Body Font:** Archivo variable — the same superfamily
**Label/Mono Font:** Azeret Mono (with `ui-monospace`, `Cascadia Mono`, `Consolas`)

**Character:** One superfamily set across three optical widths. A register differentiates by width, not weight: expanded for the running head and section bars, regular for interface chrome, narrow for the listing so more researched columns fit without shrinking the face. Azeret Mono appears only where the page is quoting a machine — a real SQL column identifier under its human column head.

### Hierarchy
- **Display** (600, 20px, `wdth 118`, -0.012em): The title of an empty page's preface. One per page at most; it drops to 18px under 760px.
- **Headline** (600, 15px, `wdth 100`, -0.008em): A contents-page entry name; a modal's title (set at `wdth 118`).
- **Title** (600, 11px, `wdth 118`, 0.14em, uppercase): The running head across the top of the page and the reversed section bar. This is the page's own identity line, not an eyebrow over a heading.
- **Body** (400, 14px/1.45, `wdth 100`): The base. Supporting prose sets at 13.5px or 12.5px and is measured at 44–78ch depending on the region.
- **Listing** (400, 13.5px, `wdth 80`, 0.002em): Every value in the register's rows and in an open cell editor.
- **Label** (600, 10px, `wdth 100`, 0.1em, uppercase): Column heads, field labels, the key, the folio, the status chip in the running head. Thumb-index tabs use the same treatment at 10.5px.
- **Mono** (400, 10px, -0.02em): Machine column identifiers, and the 10.5px timestamp column of the clerk's log.

### Named Rules
**The Width-Not-Weight Rule.** Hierarchy comes from Archivo's width axis (118 / 100 / 80). Weight stays in the 400–600 band; nothing is 700 or 300. If a new role needs to feel different, change its width before its weight.

**The Tabular Figures Rule.** `tnum` and `lnum` are on at the root and inherited by inputs, buttons and table cells. Every figure column is right-aligned. A proportional numeral anywhere in this system is a bug.

**The Mono Is A Quotation Rule.** Azeret Mono means "this string belongs to the machine." It is never used for emphasis, for numbers, or to make something look technical.

## Layout

The page is a vertical stack: a full-width running head (48px, 2px navy rule beneath) over a spread padded 14px from the desk. The spread is a white sheet that flexes to fill and an enquiry desk column fixed at 404px on its right; the two share a rule, so the spread reads as one sheet rather than two panels. Inside the sheet: a reversed section bar, a toolbar (8px/10px, hairline beneath), the scrolling listing, then a key strip and a folio at the foot.

The listing is a flex-row grid, not a table of boxes. A 48px entry-number gutter and the company column are frozen to the left; a 56px actions column is frozen to the right behind a single hairline fold. Data columns are fixed-width (234px for the lead, 158px for a text enrichment, 122px for a boolean, 78px for a figure) and the last one keeps a 22px right gutter so its values never run flush into the fold. Rows are 34px minimum with a 38px head. Horizontal scroll uses `scroll-snap-type: x proximity` with `scroll-padding-right: 80px` so a scrolled position lands on a column boundary.

The spacing rhythm is fine and even: 2, 4, 6, 8, 10, 12, 14 for interior padding and gaps; 18, 22, 28 for sheet margins and section separation. There is no 4px-multiple dogma — the values are register-tight and chosen per region.

**Responsive.** At 1400px the enquiry desk narrows to 326px and the spread padding drops to 10px, giving the listing back width on a 1280 laptop. At 1100px the spread folds to one column, the enquiry desk moves above the listing (the visitor's whole job is to type one sentence into it), the page takes over the scroll, and the listing keeps a 58vh scroller so the column heads still hold. At 760px the running head wraps and the folio drops to its own full-width line; the gutter narrows to 34px, the company column to 170px, row actions un-freeze and scroll with the row; the contents page drops its statistic columns and each entry prints its own summary line instead; and the listing scroller is capped at exactly `57px + (34px + 1px) × 8` so it ends on a whole row rather than slicing one through its type.

### Named Rules
**The Horizontal Rule Rule.** Structure is horizontal hairlines and alignment. There are no vertical cell borders and no card borders anywhere in the listing. The only vertical hairlines in the system mark a frozen edge — the divider at the end of the frozen left columns and the fold before the frozen actions column — and they mean "the sheet continues here," nothing else.

**The End-On-A-Whole-Row Rule.** A capped scroll region is sized from real row arithmetic, never estimated in vh, so a listing never ends mid-glyph.

## Elevation & Depth

The sheet itself is flat: no surface on the page is lifted. Depth is tonal and material — white paper on a pale blue desk, navy tint for a working or secondary region, hairlines for separation. Cast shadows exist, but only for things that are genuinely off the sheet, and all three derive from navy-deep at low alpha with a large negative spread, so they read as soft paper shadow rather than as a UI elevation ramp. Two additional shadows are inset and are not depth at all: they are ruled underlines drawn with `box-shadow` because a border would change the element's box.

### Shadow Vocabulary
- **Lifted leaf** (`box-shadow: 0 18px 40px -18px #0c224459`): A modal — a sheet laid over the desk. The only full-surface lift in the system.
- **Pinned slip** (`box-shadow: 0 10px 24px -14px #0c224466`): A notice at the foot of the desk.
- **The fold** (`box-shadow: -7px 0 8px -7px #0c224459`): Cast leftward by the frozen actions edge, and only while `data-more="true"` — the sheet really does carry on past it.
- **Focus rule** (`box-shadow: inset 0 -2px 0 -1px var(--navy)`): A focused field's thickened baseline.
- **Editable underline** (`box-shadow: inset 0 -1px 0 var(--navy-mid)`): A cell's editability, shown on hover as the same hairline the page is built from.

### Named Rules
**The Lifted-Leaf Rule.** A cast shadow means the element is physically off the sheet — an overlay, a pinned slip, or a fold with paper continuing behind it. Nothing that lives in the page's flow gets one. No card, toolbar, row, desk or section bar has a shadow, and no shadow in this system is hard or offset without blur.

## Shapes

Square-cornered throughout. Buttons, fields, chips, modals, notices, the search box and the status control all declare `border-radius: 0` explicitly rather than inheriting it. The single exception in the whole build is the thumb-index tab, cut `2px 2px 0 0` on its outer top corners only — the cut of a tab in a dictionary's fore-edge — and the active tab runs into the leaf it opens with `margin-bottom: -1px` so there is no edge between them.

The recurring silhouette is the rectangle-with-a-hairline: a 1px border in `{colors.hairline}` on white, filling navy when it is the primary action of its region. Controls come in three heights — 30px standard, 26px for head-level and search controls, 24px compact — and icon-only controls are square (26px, or 22px small) so the glyph sits on the button's own axis.

Marks are drawn, not typed. A boolean answer is a 9px square: filled for true, hollow for false, and an en-rule for not established — with the word riding alongside the mark and a permanent key at the foot of the sheet decoding all three.

### Named Rules
**The Square-Corner Rule.** Radius is 0. The one licensed curve is the 2px outer top corner of a thumb-index tab. Anything printed has square corners, and everything here is printed.

## Components

### Buttons
- **Shape:** Square (0 radius), 30px tall, 12px horizontal padding, 6px gap to an icon, 1px border on every tone so tones swap without the box resizing. Compact is 24px / 8px / 11px; icon-only is a 26px (or 22px) square.
- **Primary:** Navy fill, navy border, white label. Hover deepens to navy-deep.
- **Plain (default):** White paper, hairline border, text ink. Hover swaps border and label to navy.
- **Quiet:** Transparent with a transparent border. Hover fills navy-tint and inks navy. Used for row actions, dismissals and secondary run controls.
- **Danger:** White paper, hairline border, spot-red label. Hover takes a spot border and spot wash.
- **Active:** Every tone shifts `translateY(1px)` — the press of a stamp. Disabled is 0.42 opacity.
- **Loading:** The label stays and the icon is replaced by the ruled square spinner; the button reports `aria-busy`.
- Tones are declared on the stylesheet, not the component, so a bare `.reg-btn` element (a file-picker label, a row action) is identical to a rendered `<Button>`.

### Chips
- **Style:** White paper, hairline border, 0 radius, 4px/9px padding, secondary ink at 12px.
- **State:** Hover takes navy border and navy label. Selected fills navy with a white label. Used for the column pickers on the import sheet.

### Cards / Containers
There are no cards. A region is a white sheet (`{colors.paper}`) inside a 1px hairline, opened by a reversed navy section bar and closed by a folio over a hairline. Interior padding runs 8–18px depending on density. Shadow strategy: none (see Elevation & Depth). The one surface that is not paper is the enquiry desk, which sits in navy tint behind a left hairline.

### Inputs / Fields
- **Style:** White paper, 1px hairline all round, 0 radius, 6px/9px padding, 30px minimum height, 13px text. A field is a ruled line, not a box. Labels sit above in spaced small caps; hints sit below at 11.5px in secondary ink.
- **Focus:** Border goes navy and an inset 2px navy baseline thickens under the field. The caret is navy. No glow, no ring offset on the field itself.
- **Hover:** Border darkens one step to `#b3c1d6`.
- **Disabled:** Navy-tint ground, secondary ink, not-allowed cursor.
- **TextArea:** Same field, vertically resizable, 64px minimum, 1.5 line-height. The composer's textarea is 62px and non-resizable.
- **Inline cell editor:** No box at all — a bottom 2px navy rule under the narrow listing face.
- **Global focus-visible:** 2px navy outline at 1px offset, everywhere else.

### Navigation
- **Running head:** A 48px desk-blue strip under a 2px navy rule. A short 18px × 3px navy rule is the publication's mark, followed by "KIYU LABS" in expanded caps and the title in secondary ink at 0.16em. The folio — what page of the register this is — sits centre-left in spaced small caps with 1px × 11px hairline separators. The keys status control sits right: 26px, hairline outline, navy when satisfied, spot red on spot wash when not. Under 760px the folio drops to its own full-width line.
- **Thumb-index tabs:** Cut into the fore-edge of the enquiry desk on a desk-blue rail with a navy rule beneath. Inactive tabs are `#dbe4f2` with secondary-ink caps; hover lightens and inks navy; the active tab fills navy with white caps and merges into the leaf it opens.

### The Ruled Listing (signature)
A flex listing where horizontal hairlines and alignment do all the work. A sticky 38px head sits under a 1px navy rule with spaced small-caps column heads over their mono identifiers. The entry-number gutter and the company column freeze left; the actions column freezes right behind a 24px band of opaque paper cut by a single hairline — a clean cut reads as a sheet continuing, a half-glyph reads as broken rendering. Hover tints the row `{colors.paper-hover}`, carried explicitly into every frozen cell. A working entry takes navy tint. An editable cell shows its affordance as a hairline underline on hover. Row actions are invisible until the entry is hovered or the control is focused. Under an entry, the agent's working prints as a footnote on navy tint, pinned to the left edge so sideways scrolling never carries it off the page.

### The Travelling Setting Rule (signature)
One 3px navy rule in the entry-number gutter, with a 9px × 3px nib at its head, that travels to the entries being worked by transitioning `transform` and `height` on the one clock. It is not a per-row spinner and not a loop. Answers ink in behind it with a staggered 160ms opacity rise and a 2px settle.

### The Key and the Folio
Every register carries a key. The key strip sits on navy tint over a hairline at the foot of the sheet and decodes all three boolean marks in words. Below it, the folio counts what the page contains in spaced small caps over a hairline. Both are permanent page furniture, not conditional help.

### Notices
Marginalia pinned bottom-right, max 384px, stacked three deep, 7s life. A 1px hairline all round and a 2px rule at the head carrying the severity ink, over the matching wash. A drawn icon, a small-caps severity label, the message at 12.5px, and a quiet icon-only dismiss.

### Modals
An inserted leaf: white paper, 1px hairline, square corners, a 14px/18px header closed by a 2px navy rule, a scrolling body, and a navy-tint footer over a hairline with actions right-aligned. Default width 520px (430px for a confirm), 86vh maximum, over a `#0c224466` scrim with a 1.5px blur. It enters on the ink-settle move, traps focus, restores focus on close, and is used only where the task genuinely needs protected focus.

### Empty Pages
An empty region is set as the preface of a volume, never as blank paper and never as an illustration: a 44px × 3px navy rule, an expanded-width title, one sentence of what the page will hold at 56ch, the single action that fills it, and — where the sequence matters — a numbered list of what happens next, hairline-separated on a hairline ground.

### Motion
- **Clock:** 160ms, `cubic-bezier(0.16, 1, 0.3, 1)`, for every transition and both keyframe animations. Rule-draw runs at 1.5× the clock (240ms).
- **The three moves:** ink-settle (2px rise from 0 opacity), rule-draw (scaleX from the left edge), and the travelling setting rule.
- **The one exception:** the spinner, a ruled square sweeping its own border at 900ms linear — the only indeterminate device and the only motion off the clock, because an indeterminate wait has no duration to borrow.
- All motion collapses to 1ms under `prefers-reduced-motion: reduce`.

**The One Clock Rule.** Every transition and animation in the build reads `--clock` (160ms) and `--ease`. A hand-typed duration is drift. The 900ms spinner is the single named exception.

## Do's and Don'ts

### Do:
- **Do** separate with a horizontal hairline and hold with alignment. Three weights only: `#e2e9f3` between entries, `#ccd6e6` between regions, navy at 1–2px to open or close.
- **Do** keep every corner square. The only radius in the system is the 2px outer cut of a thumb-index tab.
- **Do** reach for the width axis before the weight axis — `wdth 118` for heads, `100` for interface, `80` for listing columns.
- **Do** set every figure tabular and lining, and right-align every figure column.
- **Do** spend the spot red only on failure and destruction. Running work is navy tint.
- **Do** run every new transition on `var(--clock)` and `var(--ease)`, and make sure it survives `prefers-reduced-motion`.
- **Do** draw new icons on the 16px grid at 1.25px stroke with square caps and miter joins, matching the existing set.
- **Do** carry the row's background explicitly into sticky and frozen cells, so a hovered or working entry reads as one unbroken line.
- **Do** give a boolean its word alongside its mark, and keep the key at the foot of the sheet.
- **Do** size a capped scroll region from real row arithmetic so it ends on a whole row.

### Don't:
- **Don't** put a card border or a vertical cell border in a listing. A vertical hairline is licensed only to mark a frozen edge or a fold.
- **Don't** cast a shadow on anything that lives in the page's flow. Shadows belong to overlays, pinned slips and the fold, and are always soft, downward and negative-spread — never hard, never offset without blur.
- **Don't** add a fourth rule weight, a fifth control height, or a second easing curve.
- **Don't** use a Unicode glyph, an icon font, or a library icon set. Every mark in this build is authored SVG; a Unicode bullet will not hold its weight against the page's hairlines.
- **Don't** set an eyebrow or kicker over a heading. The running head is the page's identity line and the section bar carries the heading; there is no third label stacked above a title.
- **Don't** introduce a system display face or a second sans. Archivo is the whole voice; Azeret Mono only quotes the machine.
- **Don't** use spot red to mean "live", "new" or "important".
- **Don't** add a loading skeleton, a pulse, a progress loop or a fabricated per-item counter. Progress is the setting rule, the clerk's log and real counts.
- **Don't** show an illustration on an empty page. Set the preface instead.
- **Don't** invent a colour outside the palette above; every ground in the build is paper, desk blue, navy tint or a notice wash.

<!-- Known limitation, carried not canonized: at a resting horizontal scroll position the listing's last partially-visible data column is cut at the fold. The fold is a single hairline over opaque paper with a cast shadow, and scroll-snap lands scrolled positions on column boundaries, but the at-rest cut remains. This is a defect the build carries, not a rule for future surfaces. -->
