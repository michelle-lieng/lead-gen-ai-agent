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
