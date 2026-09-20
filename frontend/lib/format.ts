const LOCALE = 'en-IN';

/** "06:00:00" -> "6:00 AM" */
export function formatTime(value: string | null | undefined): string {
  if (!value) return '';
  const [h, m] = value.split(':').map(Number);
  if (Number.isNaN(h) || Number.isNaN(m)) return value;
  const suffix = h >= 12 ? 'PM' : 'AM';
  return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${suffix}`;
}

export function formatTimeRange(start: string | null | undefined, end: string | null | undefined): string {
  if (start && end) return `${formatTime(start)} – ${formatTime(end)}`;
  return formatTime(start) || formatTime(end);
}

/** Parses a plain "YYYY-MM-DD" as a local date (avoids the UTC off-by-one of `new Date(str)`). */
export function parseDate(value: string): Date {
  const [y, m, d] = value.slice(0, 10).split('-').map(Number);
  return new Date(y, m - 1, d);
}

export function formatDate(value: string | null | undefined, options?: Intl.DateTimeFormatOptions): string {
  if (!value) return '';
  const date = value.length <= 10 ? parseDate(value) : new Date(value);
  return date.toLocaleDateString(LOCALE, options ?? { day: 'numeric', month: 'short', year: 'numeric' });
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '';
  return new Date(value.endsWith('Z') || value.includes('+') ? value : `${value}Z`).toLocaleString(LOCALE, {
    day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit',
  });
}

const money = new Intl.NumberFormat(LOCALE, { style: 'currency', currency: 'INR', maximumFractionDigits: 2 });
export const formatMoney = (value: number | null | undefined): string => money.format(value ?? 0);

/** Today as YYYY-MM-DD in the browser's local time. */
export function todayISO(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

/** Empty form strings become null so the API clears the field instead of storing "". */
export const emptyToNull = (value: string | undefined | null): string | null => {
  const trimmed = (value ?? '').trim();
  return trimmed === '' ? null : trimmed;
};
