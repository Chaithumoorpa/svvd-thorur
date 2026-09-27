'use client';

import React, { useEffect, useState } from 'react';
import { formatTimeRange } from '@/lib/format';

const IST_OFFSET_MINUTES = 330; // UTC+5:30, no daylight saving

/** A temple time ("HH:MM[:SS]", always India time) at the given IST date. */
export function istInstant(time: string, day: string): Date {
  const [y, m, d] = day.split('-').map(Number);
  const [h, mi] = time.split(':').map(Number);
  return new Date(Date.UTC(y, m - 1, d, h, mi) - IST_OFFSET_MINUTES * 60_000);
}

function todayInIndia(): string {
  return new Date(Date.now() + IST_OFFSET_MINUTES * 60_000).toISOString().slice(0, 10);
}

/** The visitor's zone, if it isn't India time on that day (browsers report
 * Asia/Calcutta or Asia/Kolkata for India). */
export function visitorZone(at: Date): string | null {
  try {
    const zone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (!zone) return null;
    const local = new Date(at.toLocaleString('en-US', { timeZone: zone }));
    const utc = new Date(at.toLocaleString('en-US', { timeZone: 'UTC' }));
    return Math.round((local.getTime() - utc.getTime()) / 60_000) === IST_OFFSET_MINUTES ? null : zone;
  } catch {
    return null;
  }
}

export function localRange(zone: string, day: string, start: string | null, end: string | null): string {
  const fmt = (t: string, withZone: boolean) =>
    istInstant(t, day).toLocaleTimeString(undefined, {
      timeZone: zone, hour: 'numeric', minute: '2-digit', ...(withZone ? { timeZoneName: 'short' } : {}),
    });
  const dayShift = (t: string) => {
    const there = istInstant(t, day).toLocaleDateString('en-CA', { timeZone: zone }); // YYYY-MM-DD
    return there < day ? ' (prev. day)' : there > day ? ' (next day)' : '';
  };
  if (start && end) return `${fmt(start, false)}${dayShift(start)} – ${fmt(end, true)}${dayShift(end)}`;
  const only = (start || end) as string;
  return `${fmt(only, true)}${dayShift(only)}`;
}

/**
 * A temple time, labelled IST - and, for a visitor whose browser is set to
 * another time zone (NRI devotees), that time in their zone too:
 * "7:00 AM – 8:30 AM IST · 9:30 PM – 11:00 PM EDT your time (prev. day)".
 * The server always renders the IST part; the local part is added in the
 * browser after it loads, so there's no hydration mismatch.
 */
export default function TempleTime({
  start,
  end,
  day,
  yourTimeLabel = 'your time',
  stacked = false,
  localClassName = 'text-xs font-normal text-gray-500',
}: {
  start: string | null | undefined;
  end?: string | null;
  /** The IST date the time is on (YYYY-MM-DD); defaults to today in India. */
  day?: string;
  yourTimeLabel?: string;
  /** Put the local time on its own line (large displays). */
  stacked?: boolean;
  localClassName?: string;
}) {
  const [local, setLocal] = useState<string | null>(null);
  const ist = formatTimeRange(start, end ?? null);

  useEffect(() => {
    if (!start && !end) return;
    const onDay = day ?? todayInIndia();
    const zone = visitorZone(istInstant((start || end) as string, onDay));
    setLocal(zone ? localRange(zone, onDay, start ?? null, end ?? null) : null);
  }, [start, end, day]);

  if (!ist) return null;
  return (
    <>
      {ist} IST
      {local && (stacked
        ? <span className={`block ${localClassName}`}>{local} {yourTimeLabel}</span>
        : <span className={localClassName}> · {local} {yourTimeLabel}</span>)}
    </>
  );
}
