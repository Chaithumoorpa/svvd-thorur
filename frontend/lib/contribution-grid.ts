import { addDaysISO, parseDate } from './format';

/** Days shown either side of today on the Abhishekam calendar: 182 + today
 * + 182 = a rolling 365-day window, today in the middle. */
export const WINDOW_DAYS_EACH_SIDE = 182;

export interface GridWeek {
  /** Seven YYYY-MM-DD dates, Sunday first; null where the week sticks out
   * past either end of the window. */
  days: (string | null)[];
  /** Short month name when this column starts a month (GitHub-style), else null. */
  monthLabel: string | null;
}

export function rollingWindow(today: string): { start: string; end: string } {
  return { start: addDaysISO(today, -WINDOW_DAYS_EACH_SIDE), end: addDaysISO(today, WINDOW_DAYS_EACH_SIDE) };
}

// Fixed, not toLocaleDateString: ICU spells September "Sept" in en-IN on some
// runtimes and "Sep" on others, and column labels need to stay one width.
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const monthName = (iso: string) => MONTHS[parseDate(iso).getMonth()];

/** Lays `start`..`end` (inclusive) out as week columns, the way GitHub's
 * contribution graph does: one column per Sunday-to-Saturday week, each
 * column labelled with the month that begins in it. */
export function buildWeeks(start: string, end: string): GridWeek[] {
  const firstSunday = addDaysISO(start, -parseDate(start).getDay());
  const weeks: GridWeek[] = [];
  for (let sunday = firstSunday; sunday <= end; sunday = addDaysISO(sunday, 7)) {
    const days = Array.from({ length: 7 }, (_, i) => {
      const day = addDaysISO(sunday, i);
      return day >= start && day <= end ? day : null;
    });
    const monthStart = days.find((d) => d !== null && d.endsWith('-01'));
    weeks.push({ days, monthLabel: monthStart ? monthName(monthStart) : null });
  }
  // Also name the first column's month, unless the next label is so close
  // the two would overlap.
  const firstLabelled = weeks.findIndex((w) => w.monthLabel !== null);
  if (weeks.length && weeks[0].monthLabel === null && (firstLabelled === -1 || firstLabelled >= 3)) {
    weeks[0].monthLabel = monthName(start);
  }
  return weeks;
}

/** 0-4 shading level for a day's booked slots, like GitHub's contribution levels. */
export function slotLevel(used: number, total: number): 0 | 1 | 2 | 3 | 4 {
  if (used <= 0) return 0;
  if (used >= total) return 4;
  const ratio = used / total;
  return ratio < 1 / 3 ? 1 : ratio < 2 / 3 ? 2 : 3;
}
