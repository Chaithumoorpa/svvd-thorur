import { describe, expect, it } from 'vitest';
import { isTurnstileBlocked } from '@/lib/turnstile';

describe('isTurnstileBlocked', () => {
  it('never blocks when the widget is not configured, regardless of token/failed state', () => {
    expect(isTurnstileBlocked(false, null, false)).toBe(false);
    expect(isTurnstileBlocked(false, null, true)).toBe(false);
    expect(isTurnstileBlocked(false, 'a-token', true)).toBe(false);
  });

  it('blocks a configured widget until a token exists', () => {
    expect(isTurnstileBlocked(true, null, false)).toBe(true);
  });

  it('unblocks once a token is solved', () => {
    expect(isTurnstileBlocked(true, 'a-token', false)).toBe(false);
  });

  it('blocks on a widget error even if an earlier token is still sitting in state', () => {
    expect(isTurnstileBlocked(true, 'stale-token', true)).toBe(true);
  });
});
