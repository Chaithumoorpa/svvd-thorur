import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Manages a Turnstile token's lifecycle for a form that may need to submit
 * more than once (a resend, or an auto-login right after registration) -
 * tokens are single-use, so `reset()`/`next()` remount the widget rather than
 * resubmitting an already-consumed token.
 */
export function useTurnstile() {
  const [token, setToken] = useState<string | null>(null);
  const [widgetKey, setWidgetKey] = useState(0);
  const tokenRef = useRef<string | null>(null);

  useEffect(() => {
    tokenRef.current = token;
  }, [token]);

  const reset = useCallback(() => {
    setToken(null);
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

  return { token, widgetKey, setToken, reset, next };
}
