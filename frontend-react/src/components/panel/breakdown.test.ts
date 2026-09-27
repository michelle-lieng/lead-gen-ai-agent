import { describe, expect, it } from 'vitest';
import type { MessagePlan } from '../../api/types';
import type { ThreadLine } from '../../hooks/useProjectChat';
import {
  applyCardEdits,
  cardState,
  hasWork,
  isActiveCard,
  needsConfirmation,
  readCardPlan,
  summarisePlan,
} from './breakdown';

const plan: MessagePlan = {
  find: true,
  find_instruction: 'Companies based around Sydney Harbour',
  location: 'Sydney Harbour',
  criteria: ['Does this company invest in environmental causes?', 'Does it have 50+ staff?'],
  columns: ['Website'],
  continue_columns: [
    { enrichment_id: 3, name: 'Hours', column_name: 'hours', leads: ['a'] },
  ],
  reply: '',
};

const noEdits = {
  base: plan.find_instruction,
  removedCriteria: [],
  removedColumns: [],
  removedContinue: [],
  removedLocation: false,
};

const line = (kind: ThreadLine['kind'], text = '', role: ThreadLine['role'] = 'log'): ThreadLine => ({
  key: Math.random().toString(),
  at: new Date(),
  role,
  kind,
  text,
});

describe('needsConfirmation', () => {
  it('asks before a search or new columns', () => {
    expect(needsConfirmation(plan)).toBe(true);
    expect(needsConfirmation({ ...plan, find: false, criteria: [], columns: ['Website'] })).toBe(true);
  });
  it('runs continuing and replies straight away', () =>
    expect(needsConfirmation({ ...plan, find: false, criteria: [], columns: [] })).toBe(false));
});

describe('applyCardEdits', () => {
  it('uses the edited base search', () =>
    expect(applyCardEdits(plan, { ...noEdits, base: '  Cafes near Circular Quay ' }).find_instruction).toBe(
      'Cafes near Circular Quay',
    ));
  it('turns the search and its location off when the base is cleared', () => {
    const edited = applyCardEdits(plan, { ...noEdits, base: '   ' });
    expect(edited.find).toBe(false);
    expect(edited.location).toBe('');
  });
  it('drops removed criteria and columns but keeps continuing columns', () => {
    const edited = applyCardEdits(plan, { ...noEdits, removedCriteria: [0], removedColumns: [0] });
    expect(edited.criteria).toEqual(['Does it have 50+ staff?']);
    expect(edited.columns).toEqual([]);
    expect(edited.continue_columns).toHaveLength(1);
  });
});

describe('applyCardEdits: continuing columns and location', () => {
  it('drops a continuing column the user removed from the card', () =>
    expect(applyCardEdits(plan, { ...noEdits, removedContinue: [0] }).continue_columns).toEqual([]));
  it('skips Google Maps but keeps the web search when the location is removed', () => {
    const edited = applyCardEdits(plan, { ...noEdits, removedLocation: true });
    expect(edited.location).toBe('');
    expect(edited.find).toBe(true);
  });
  it('has nothing to run once the search and every chip, continuing ones included, are gone', () =>
    expect(
      hasWork(
        applyCardEdits(plan, {
          base: '',
          removedCriteria: [0, 1],
          removedColumns: [0],
          removedContinue: [0],
          removedLocation: false,
        }),
      ),
    ).toBe(false));
});

describe('hasWork', () => {
  it('is false once the search and every chip are gone', () => {
    const edited = applyCardEdits(
      { ...plan, continue_columns: [] },
      { ...noEdits, base: '', removedCriteria: [0, 1], removedColumns: [0] },
    );
    expect(hasWork(edited)).toBe(false);
  });
  it('is true while anything is left to run', () => expect(hasWork(plan)).toBe(true));
});

describe('isActiveCard and cardState', () => {
  const card = line('breakdown', 'Search …', 'agent');
  it('is active while it is the newest line and nothing runs', () => {
    expect(isActiveCard([line('text', 'hi', 'user'), card], 1, false)).toBe(true);
    expect(isActiveCard([card], 0, true)).toBe(false);
    expect(isActiveCard([card, line('text', 'more', 'user')], 0, false)).toBe(false);
  });
  it('reads what happened to it from the line after it', () => {
    expect(cardState([card], 0)).toBe('active');
    expect(cardState([card, line('result', 'Started.')], 0)).toBe('started');
    expect(cardState([card, line('result', 'Cancelled. Nothing ran.')], 0)).toBe('cancelled');
    expect(cardState([card, line('text', 'actually brisbane', 'user')], 0)).toBe('replaced');
  });
});

describe('summarisePlan', () => {
  it('names the search and counts criteria and columns', () =>
    expect(summarisePlan(plan)).toBe('Search "Companies based around Sydney Harbour" · 2 criteria · 1 column'));
  it('uses the singular and leaves out a search that is off', () =>
    expect(summarisePlan({ ...plan, find: false, criteria: ['x?'], columns: [] })).toBe('1 criterion · 0 columns'));
});

describe('readCardPlan', () => {
  it('reads the plan a card was saved with', () =>
    expect(readCardPlan({ plan })).toEqual(plan));
  it('fills lists an older plan left out', () =>
    expect(readCardPlan({ plan: { find: true, find_instruction: 'x' } })).toEqual({
      find: true, find_instruction: 'x', location: '', criteria: [], columns: [], continue_columns: [], reply: '',
    }));
  it('gives nothing for a missing or malformed payload', () => {
    expect(readCardPlan(undefined)).toBeNull();
    expect(readCardPlan({ plan: 'nope' })).toBeNull();
    expect(readCardPlan({ plan: { find: 'yes' } })).toBeNull();
  });
});
