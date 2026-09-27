import { describe, expect, it } from 'vitest';
import { istInstant, localRange } from '@/components/public/TempleTime';

describe('TempleTime helpers', () => {
  it('reads a temple time as India time', () => {
    expect(istInstant('07:00:00', '2026-09-27').toISOString()).toBe('2026-09-27T01:30:00.000Z');
  });

  it('converts to a US zone, marking the previous day', () => {
    const text = localRange('America/New_York', '2026-09-27', '07:00:00', '08:30:00');
    expect(text).toMatch(/^9:30\s?PM \(prev\. day\) – 11:00\s?PM EDT \(prev\. day\)$/);
  });

  it('marks only the part of a range that falls on another day', () => {
    const text = localRange('America/New_York', '2026-09-27', '06:00:00', '12:00:00');
    expect(text).toMatch(/^8:30\s?PM \(prev\. day\) – 2:30\s?AM EDT$/);
  });

  it('converts to a UK zone on the same day', () => {
    expect(localRange('Europe/London', '2026-09-27', '07:00:00', null)).toMatch(/^2:30\s?AM (BST|GMT\+1)$/);
  });
});
