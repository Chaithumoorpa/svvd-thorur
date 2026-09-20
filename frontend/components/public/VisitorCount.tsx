'use client';

import { useEffect, useState } from 'react';
import { getVisitorStats } from '@/lib/api';
import type { VisitorStats } from '@/lib/types';

/** Small, non-critical counter: fails silently (renders nothing) if the API is unavailable. */
export default function VisitorCount() {
  const [stats, setStats] = useState<VisitorStats | null>(null);
  useEffect(() => {
    getVisitorStats().then(setStats).catch(() => setStats(null));
  }, []);
  if (!stats) return null;
  return (
    <p className="text-xs text-amber-200/80">
      Visitors today: <span className="font-semibold text-amber-100">{stats.today_visitors.toLocaleString('en-IN')}</span> · Total:{' '}
      <span className="font-semibold text-amber-100">{stats.total_visitors.toLocaleString('en-IN')}</span>
    </p>
  );
}
