'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { apiError } from '@/lib/api';

interface LoadState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

/**
 * Runs an async loader whenever `deps` change and exposes loading / error / data.
 * Stale responses (from a previous `deps` value) are ignored, so quick filter or page
 * changes can never show out-of-order results.
 */
export function useLoad<T>(loader: () => Promise<T>, deps: ReadonlyArray<unknown>): LoadState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const latest = useRef(0);
  const loaderRef = useRef(loader);
  loaderRef.current = loader;

  useEffect(() => {
    const id = ++latest.current;
    setLoading(true);
    setError(null);
    loaderRef
      .current()
      .then((result) => {
        if (id === latest.current) setData(result);
      })
      .catch((err) => {
        if (id === latest.current) setError(apiError(err, 'Could not load this data.'));
      })
      .finally(() => {
        if (id === latest.current) setLoading(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { data, loading, error, reload };
}
