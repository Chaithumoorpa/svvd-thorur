import { describe, expect, it } from 'vitest';
import { buildWeeks, rollingWindow, slotLevel } from '@/lib/contribution-grid';
import { addDaysISO } from '@/lib/format';

describe('addDaysISO', () => {
  it('crosses month and year boundaries', () => {
    expect(addDaysISO('2026-01-31', 1)).toBe('2026-02-01');
    expect(addDaysISO('2026-12-31', 1)).toBe('2027-01-01');
    expect(addDaysISO('2026-03-01', -1)).toBe('2026-02-28');
    expect(addDaysISO('2028-03-01', -1)).toBe('2028-02-29');
  });
});

describe('rollingWindow', () => {
  it('spans 365 days with today in the middle', () => {
    const { start, end } = rollingWindow('2026-09-27');
    expect(start).toBe('2026-03-29');
    expect(end).toBe('2027-03-28');
    const weeks = buildWeeks(start, end);
    expect(weeks.flatMap((w) => w.days).filter(Boolean)).toHaveLength(365);
  });
});

describe('buildWeeks', () => {
  // 2026-09-27 is a Sunday, 2026-10-03 the Saturday after it.
  it('puts each date under its weekday, Sunday first, blanking days outside the range', () => {
    const weeks = buildWeeks('2026-09-29', '2026-10-06');
    expect(weeks).toHaveLength(2);
    expect(weeks[0].days).toEqual([null, null, '2026-09-29', '2026-09-30', '2026-10-01', '2026-10-02', '2026-10-03']);
    expect(weeks[1].days).toEqual(['2026-10-04', '2026-10-05', '2026-10-06', null, null, null, null]);
  });

  it('labels the column where each month starts', () => {
    const weeks = buildWeeks('2026-09-06', '2026-11-07');
    const labels = weeks.map((w) => w.monthLabel);
    expect(labels[0]).toBe('Sep'); // first column, next label far enough away
    expect(labels[3]).toBe('Oct'); // week of 27 Sep - 3 Oct contains 1 Oct
    expect(labels[8]).toBe('Nov'); // week of 1 Nov
    expect(labels.filter(Boolean)).toHaveLength(3);
  });

  it("skips the first column's label when the next month starts right after", () => {
    const labels = buildWeeks('2026-09-27', '2026-11-07').map((w) => w.monthLabel);
    expect(labels[0]).toBe('Oct'); // that week holds 1 Oct itself
    expect(buildWeeks('2026-09-20', '2026-10-31').map((w) => w.monthLabel)[0]).toBeNull();
  });
});

describe('slotLevel', () => {
  it('maps 0-7 booked slots to GitHub-style levels, 4 meaning full', () => {
    expect([0, 1, 2, 3, 4, 5, 6, 7].map((used) => slotLevel(used, 7))).toEqual([0, 1, 1, 2, 2, 3, 3, 4]);
  });
});
