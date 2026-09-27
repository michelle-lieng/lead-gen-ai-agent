import { describe, expect, it } from 'vitest';
import { countSources, passesYesFilters, splitLinks, yesCount } from './rowStatus';

describe('passesYesFilters', () => {
  const row = { env: 'Yes', staff: 'No', website: 'x.com', blank: null };
  it('keeps every row when no filter is on', () => expect(passesYesFilters(row, [])).toBe(true));
  it('keeps a row that says yes to the column switched on', () =>
    expect(passesYesFilters(row, ['env'])).toBe(true));
  it('drops a row that says no or has no answer', () => {
    expect(passesYesFilters(row, ['staff'])).toBe(false);
    expect(passesYesFilters(row, ['blank'])).toBe(false);
  });
  it('needs yes for every column switched on', () =>
    expect(passesYesFilters(row, ['env', 'staff'])).toBe(false));
});

describe('yesCount', () => {
  it('counts the rows that say yes', () =>
    expect(yesCount([{ env: 'Yes' }, { env: true }, { env: 'No' }, { env: null }], 'env')).toBe(2));
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
      { text: 'Source: ' },
      { text: 'https://a.com/x', href: 'https://a.com/x' },
      { text: '.' },
    ]));
});
