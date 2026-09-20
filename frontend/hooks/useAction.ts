'use client';

import { useCallback, useState } from 'react';
import { apiError } from '@/lib/api';

/**
 * Wraps a mutation: tracks `busy`, turns failures into a readable `error` string and a
 * transient `success` message. Returns the action result (or undefined on failure).
 */
export function useAction() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const run = useCallback(async <T,>(fn: () => Promise<T>, successMessage?: string): Promise<T | undefined> => {
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await fn();
      if (successMessage) {
        setSuccess(successMessage);
        setTimeout(() => setSuccess(null), 4000);
      }
      return result;
    } catch (err) {
      setError(apiError(err));
      return undefined;
    } finally {
      setBusy(false);
    }
  }, []);

  const clear = useCallback(() => {
    setError(null);
    setSuccess(null);
  }, []);

  return { busy, error, success, run, clear, setError };
}
