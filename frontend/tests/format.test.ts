import { describe, expect, it } from 'vitest';
import { emptyToNull, formatDate, formatMoney, formatTime, formatTimeRange, parseDate, todayISO } from '@/lib/format';

describe('time formatting', () => {
  it('converts 24h API times to 12h', () => {
    expect(formatTime('06:00:00')).toBe('6:00 AM');
    expect(formatTime('12:30:00')).toBe('12:30 PM');
    expect(formatTime('00:05:00')).toBe('12:05 AM');
    expect(formatTime('20:30:00')).toBe('8:30 PM');
    expect(formatTime(null)).toBe('');
  });

  it('formats ranges and tolerates missing ends', () => {
    expect(formatTimeRange('06:00:00', '12:30:00')).toBe('6:00 AM – 12:30 PM');
    expect(formatTimeRange('06:00:00', null)).toBe('6:00 AM');
    expect(formatTimeRange(null, null)).toBe('');
  });
});

describe('dates', () => {
  it('parses plain dates as local dates (no UTC off-by-one)', () => {
    const d = parseDate('2026-03-01');
    expect([d.getFullYear(), d.getMonth(), d.getDate()]).toEqual([2026, 2, 1]);
  });

  it('formats a plain date without shifting the day', () => {
    expect(formatDate('2026-03-01', { day: 'numeric', month: 'short', year: 'numeric' })).toBe('1 Mar 2026');
    expect(formatDate(null)).toBe('');
  });

  it('todayISO matches YYYY-MM-DD', () => {
    expect(todayISO()).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});

describe('money and form helpers', () => {
  it('formats rupees with Indian grouping', () => {
    expect(formatMoney(1500.5)).toBe('₹1,500.50');
    expect(formatMoney(1234567)).toBe('₹12,34,567.00');
    expect(formatMoney(null)).toBe('₹0.00');
  });

  it('turns blank form values into null', () => {
    expect(emptyToNull('   ')).toBeNull();
    expect(emptyToNull(undefined)).toBeNull();
    expect(emptyToNull(' hi ')).toBe('hi');
  });
});
