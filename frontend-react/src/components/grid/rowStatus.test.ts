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
      { text: 'Source: ' },
      { text: 'https://a.com/x', href: 'https://a.com/x' },
      { text: '.' },
    ]));
});
