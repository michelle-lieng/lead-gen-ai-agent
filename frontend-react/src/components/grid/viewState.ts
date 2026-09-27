/**
 * Per-project view choices for the lead table, remembered in this browser.
 *
 * Only conveniences live here: losing them (private window, cleared storage)
 * shows the table in its defaults, never breaks it.
 */

const filtersKey = (projectId: number) => `kiyu.results.filters.${projectId}`;

/** The yes/no columns switched on as filters; none by default. */
export function readYesFilters(projectId: number): string[] {
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(filtersKey(projectId)) ?? '[]');
    if (Array.isArray(parsed) && parsed.every((key) => typeof key === 'string')) return parsed;
  } catch {
    /* unreadable or malformed: every filter off */
  }
  return [];
}

export function writeYesFilters(projectId: number, keys: string[]): void {
  try {
    localStorage.setItem(filtersKey(projectId), JSON.stringify(keys));
  } catch {
    /* storage unavailable: the choice lasts for this visit only */
  }
}

/** Which answer columns show their reasoning and evidence columns. */
export interface NotesState {
  /** Every answer column's notes are open (the toolbar checkbox). */
  all: boolean;
  /** Answer column keys opened one at a time from their header. */
  open: string[];
}

const COLLAPSED: NotesState = { all: false, open: [] };

const notesKey = (projectId: number) => `kiyu.results.notes.${projectId}`;

export function readNotesState(projectId: number): NotesState {
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(notesKey(projectId)) ?? 'null');
    if (
      parsed &&
      typeof parsed === 'object' &&
      typeof (parsed as NotesState).all === 'boolean' &&
      Array.isArray((parsed as NotesState).open) &&
      (parsed as NotesState).open.every((key) => typeof key === 'string')
    ) {
      return { all: (parsed as NotesState).all, open: [...(parsed as NotesState).open] };
    }
  } catch {
    /* unreadable or malformed: start collapsed */
  }
  return { ...COLLAPSED, open: [] };
}

export function writeNotesState(projectId: number, state: NotesState): void {
  try {
    localStorage.setItem(notesKey(projectId), JSON.stringify(state));
  } catch {
    /* storage unavailable: the choice lasts for this visit only */
  }
}

export function notesOpen(state: NotesState, answerKey: string): boolean {
  return state.all || state.open.includes(answerKey);
}

export const MIN_COLUMN_WIDTH = 72;
export const MAX_COLUMN_WIDTH = 720;

/** A dragged width, kept to whole pixels and within bounds. */
export function clampColumnWidth(width: number): number {
  return Math.min(MAX_COLUMN_WIDTH, Math.max(MIN_COLUMN_WIDTH, Math.round(width)));
}

/**
 * The width that shows a column's whole name: its current width plus the part
 * of the name that is cut off (and a little air). Null when the name fits.
 */
export function fitColumnWidth(
  currentWidth: number,
  nameScrollWidth: number,
  nameClientWidth: number,
): number | null {
  const hidden = nameScrollWidth - nameClientWidth;
  if (hidden <= 0) return null;
  return clampColumnWidth(currentWidth + hidden + 4);
}

const widthsKey = (projectId: number) => `kiyu.results.widths.${projectId}`;

/** Widths the user dragged columns to, by column key; the rest keep their default. */
export function readColumnWidths(projectId: number): Record<string, number> {
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(widthsKey(projectId)) ?? '{}');
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return {};
    return Object.fromEntries(
      Object.entries(parsed as Record<string, unknown>).filter(
        (entry): entry is [string, number] =>
          typeof entry[1] === 'number' && Number.isFinite(entry[1]) && entry[1] > 0,
      ),
    );
  } catch {
    return {};
  }
}

export function writeColumnWidths(projectId: number, widths: Record<string, number>): void {
  try {
    localStorage.setItem(widthsKey(projectId), JSON.stringify(widths));
  } catch {
    /* storage unavailable: the widths last for this visit only */
  }
}

/**
 * Whether the agent panel is open when a project is first shown. A project
 * just created opens on its table with the panel closed; otherwise it opens
 * where there is room beside the table. `navigationState` is the router state
 * the project was reached with; creation passes `{ created: true }`.
 */
export function panelStartsOpen(navigationState: unknown, wideScreen: boolean): boolean {
  if ((navigationState as { created?: unknown } | null)?.created === true) return false;
  return wideScreen;
}
