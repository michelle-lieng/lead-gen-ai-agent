import { beforeEach, describe, expect, it } from 'vitest';
import {
  clampColumnWidth,
  fitColumnWidth,
  notesOpen,
  readColumnWidths,
  readNotesState,
  readYesFilters,
  writeColumnWidths,
  writeNotesState,
  writeYesFilters,
} from './viewState';

/** An in-memory localStorage: all these functions touch of the browser. */
function installStorage() {
  const store = new Map<string, string>();
  (globalThis as { localStorage?: Storage }).localStorage = {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => void store.set(key, String(value)),
    removeItem: (key: string) => void store.delete(key),
    clear: () => store.clear(),
    key: (index: number) => [...store.keys()][index] ?? null,
    get length() {
      return store.size;
    },
  };
}

beforeEach(installStorage);

describe('yes/no filters', () => {
  it('remembers which columns are switched on per project', () => {
    writeYesFilters(7, ['env', 'staff']);
    expect(readYesFilters(7)).toEqual(['env', 'staff']);
  });
  it('starts with every filter off', () => expect(readYesFilters(8)).toEqual([]));
  it('ignores stored values that are not a list of column keys', () => {
    localStorage.setItem('kiyu.results.filters.9', '{not json');
    expect(readYesFilters(9)).toEqual([]);
    localStorage.setItem('kiyu.results.filters.10', '["env", 3]');
    expect(readYesFilters(10)).toEqual([]);
  });
});

describe('why and evidence state', () => {
  it('remembers which columns are open per project', () => {
    writeNotesState(3, { all: false, open: ['env'] });
    expect(readNotesState(3)).toEqual({ all: false, open: ['env'] });
  });
  it('starts collapsed when nothing is stored', () =>
    expect(readNotesState(4)).toEqual({ all: false, open: [] }));
  it('ignores stored text that is not json', () => {
    localStorage.setItem('kiyu.results.notes.5', '{not json');
    expect(readNotesState(5)).toEqual({ all: false, open: [] });
  });
  it('ignores stored json of the wrong shape', () => {
    localStorage.setItem('kiyu.results.notes.6', '{"all":"yes"}');
    expect(readNotesState(6)).toEqual({ all: false, open: [] });
  });
  it('opens a column when all are open or when it is listed', () => {
    expect(notesOpen({ all: false, open: ['env'] }, 'env')).toBe(true);
    expect(notesOpen({ all: false, open: ['env'] }, 'staff')).toBe(false);
    expect(notesOpen({ all: true, open: [] }, 'staff')).toBe(true);
  });
});

describe('column widths', () => {
  it('remembers dragged widths per project', () => {
    writeColumnWidths(11, { lead: 320, env: 140 });
    expect(readColumnWidths(11)).toEqual({ lead: 320, env: 140 });
  });
  it('starts with no overrides', () => expect(readColumnWidths(12)).toEqual({}));
  it('drops stored entries that are not sensible widths', () => {
    localStorage.setItem('kiyu.results.widths.13', '{"lead": 300, "env": "wide", "x": -5}');
    expect(readColumnWidths(13)).toEqual({ lead: 300 });
    localStorage.setItem('kiyu.results.widths.14', '[1,2]');
    expect(readColumnWidths(14)).toEqual({});
  });
  it('keeps a dragged width within bounds and whole pixels', () => {
    expect(clampColumnWidth(10)).toBe(72);
    expect(clampColumnWidth(5000)).toBe(720);
    expect(clampColumnWidth(201.6)).toBe(202);
  });
});

describe('fitColumnWidth', () => {
  it('widens a column by exactly the part of its name that is cut off', () =>
    expect(fitColumnWidth(164, 230, 120)).toBe(274 + 4));
  it('leaves a column whose name already fits', () =>
    expect(fitColumnWidth(164, 90, 120)).toBeNull());
  it('never grows past the widest a column can be', () =>
    expect(fitColumnWidth(600, 900, 400)).toBe(720));
});
