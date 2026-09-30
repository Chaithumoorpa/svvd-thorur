import { useCallback, useEffect, useRef, useState } from 'react';
import { isTurnstileBlocked } from '@/lib/turnstile';

const SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;

/**
 * Manages a Turnstile token's lifecycle for a form that may need to submit
 * more than once (a resend, or an auto-login right after registration) -
 * tokens are single-use, so `reset()`/`next()` remount the widget rather than
 * resubmitting an already-consumed token.
 *
 * Also exposes `blocked`: true whenever the widget is configured but hasn't
 * produced a usable token yet (not solved, expired, or failed to load).
 * Every Turnstile-gated form must fold this into its submit button's
 * `disabled` - without it, a devotee can submit straight through a failed
 * or unsolved challenge, and whether that's actually stopped then depends
 * entirely on the backend having TURNSTILE_SECRET_KEY configured.
 */
export function useTurnstile() {
  const [token, setToken] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const [widgetKey, setWidgetKey] = useState(0);
  const tokenRef = useRef<string | null>(null);

  useEffect(() => {
    tokenRef.current = token;
  }, [token]);

  const reset = useCallback(() => {
    setToken(null);
    setFailed(false);
    setWidgetKey((k) => k + 1);
  }, []);

  /** Remounts the widget and waits (briefly) for a freshly-solved token -
   * used when one form submission needs a second Turnstile-gated call right
   * after the first (e.g. register, then the auto sign-in that follows it). */
  const next = useCallback((timeoutMs = 4000): Promise<string | undefined> => {
    reset();
    return new Promise((resolve) => {
      const start = Date.now();
      const poll = () => {
        if (tokenRef.current) {
          resolve(tokenRef.current);
          return;
        }
        if (Date.now() - start > timeoutMs) {
          resolve(undefined);
          return;
        }
        setTimeout(poll, 150);
      };
      setTimeout(poll, 150);
    });
  }, [reset]);

  const required = Boolean(SITE_KEY);
  return { token, failed, setFailed, widgetKey, setToken, reset, next, required, blocked: isTurnstileBlocked(required, token, failed) };
}
