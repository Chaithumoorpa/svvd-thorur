'use client';

import { useLoad } from '@/hooks/useLoad';
import { getPoojas } from '@/lib/api';
import type { Pooja } from '@/lib/types';

/** The seva behind the /abhishekam pages: the first active seva (in the
 * admin's sort order) with public blessings turned on - the temple's
 * Abhishekam. `data` is null once loaded if no seva offers them. */
export function useBlessingSeva() {
  return useLoad<Pooja | null>(
    async () => (await getPoojas()).find((p) => p.public_blessings) ?? null,
    [],
  );
}
