'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import Modal from '@/components/ui/Modal';
import { ErrorBlock, LoadingBlock, Notice } from '@/components/ui/States';
import { btnGhost, btnPrimary } from '@/components/ui/styles';
import { useBlessingSeva } from '@/hooks/useBlessingSeva';
import { useLoad } from '@/hooks/useLoad';
import { getSevaCalendar, getSevaDay } from '@/lib/api';
import { buildWeeks, rollingWindow, slotLevel } from '@/lib/contribution-grid';
import { formatDate, formatLongDate as longDate, todayISO } from '@/lib/format';
import type { Pooja } from '@/lib/types';

const LEVEL_CLASSES = [
  'bg-amber-50 border border-amber-200',
  'bg-amber-200',
  'bg-saffron-light',
  'bg-saffron',
  'bg-maroon',
] as const;
const LEVEL_LABELS = ['No bookings', 'A few slots booked', 'About half booked', 'Nearly full', 'Fully booked'];
const WEEKDAY_LABELS = ['', 'Mon', '', 'Wed', '', 'Fri', ''];
const CELL = 13; // px - GitHub's contribution squares are about this size
const SHADING_SCALE = 7; // for a seva with no daily limit: shade as if it had the paper register's 7

const dayMonth = (day: string) => formatDate(day, { day: '2-digit', month: '2-digit' }); // 01/06
const bookedText = (used: number, total: number | null) => (total ? `${used} of ${total} slots booked` : `${used} booked`);

function SlotDots({ used, total }: { used: number; total: number }) {
  return (
    <div className="flex gap-1" aria-hidden="true">
      {Array.from({ length: total }, (_, i) => (
        <span key={i} className={`h-3 w-3 rounded-full ${i < used ? 'bg-maroon' : 'border border-amber-300 bg-amber-50'}`} />
      ))}
    </div>
  );
}

function DayModal({ seva, day, today, onClose }: { seva: Pooja; day: string; today: string; onClose: () => void }) {
  const flyer = useLoad(() => getSevaDay(seva.id, day), [seva.id, day]);
  const data = flyer.data;
  const upcomingOrToday = day >= today;
  const bookable = upcomingOrToday && !!data && (data.slots_total === null || data.slots_used < data.slots_total);

  return (
    <Modal title={longDate(day)} onClose={onClose}>
      {flyer.loading ? (
        <LoadingBlock />
      ) : flyer.error || !data ? (
        <ErrorBlock message={flyer.error ?? 'Could not load this day.'} onRetry={flyer.reload} />
      ) : (
        <div className="space-y-4">
          <div className="space-y-2">
            <p className="text-sm text-gray-700">
              <strong className="text-maroon-dark">{bookedText(data.slots_used, data.slots_total)}</strong>
            </p>
            {data.slots_total && <SlotDots used={data.slots_used} total={data.slots_total} />}
          </div>

          {data.entries.length > 0 ? (
            <ul className="divide-y divide-amber-100 rounded-lg border border-amber-100 bg-amber-50/60">
              {data.entries.map((entry, i) => (
                <li key={i} className="px-3 py-2 text-sm">
                  <span className="font-medium text-maroon-dark">{entry.devotee_name}</span>
                  <span className="text-gray-600"> - {entry.occasion}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">
              {data.slots_used > 0
                ? 'Bookings for this day are private or awaiting payment.'
                : upcomingOrToday ? 'No bookings yet for this day.' : `No ${seva.name} was booked for this day.`}
            </p>
          )}

          <div className="flex flex-col gap-2 sm:flex-row">
            {bookable && (
              <Link href={`/abhishekam?date=${day}`} className={`${btnPrimary} justify-center`}>
                Book {seva.name} for {dayMonth(day)}
              </Link>
            )}
            {day <= today && data.entries.length > 0 && (
              <Link href={`/abhishekam/blessings/${day}`} className={`${btnGhost} justify-center`}>
                View blessings for {dayMonth(day)}
              </Link>
            )}
          </div>
          {upcomingOrToday && !bookable && <Notice kind="error">This day is fully booked.</Notice>}
        </div>
      )}
    </Modal>
  );
}

export default function AbhishekamCalendarPage() {
  const [today] = useState(todayISO);
  const { start, end } = useMemo(() => rollingWindow(today), [today]);
  const weeks = useMemo(() => buildWeeks(start, end), [start, end]);
  const seva = useBlessingSeva();
  const sevaId = seva.data?.id;
  const calendar = useLoad(
    () => (sevaId ? getSevaCalendar(sevaId, start, end) : Promise.resolve([])),
    [sevaId, start, end],
  );
  const [selected, setSelected] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const todayRef = useRef<HTMLButtonElement>(null);

  const byDate = useMemo(() => new Map((calendar.data ?? []).map((d) => [d.date, d])), [calendar.data]);
  const cap = seva.data?.daily_slot_cap;

  // On a narrow screen the grid scrolls sideways - start with today in view.
  useEffect(() => {
    const box = scrollRef.current;
    const cell = todayRef.current;
    if (box && cell) box.scrollLeft = cell.offsetLeft - box.clientWidth / 2;
  }, [calendar.data]);

  if (!seva.loading && !seva.error && !seva.data) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gradient-to-b from-amber-50 to-templeWhite px-4">
        <div className="text-center">
          <h1 className="font-serif text-2xl font-bold text-red-900">Abhishekam Calendar</h1>
          <p className="mt-2 text-sm text-gray-600">Online Abhishekam booking isn&apos;t open yet.</p>
          <Link href="/poojas" className={`${btnGhost} mt-4 inline-flex`}>See all sevas</Link>
        </div>
      </main>
    );
  }

  const name = seva.data?.name ?? 'Abhishekam';
  return (
    <main className="min-h-screen bg-gradient-to-b from-amber-50 to-templeWhite px-4 py-10">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 text-center">
          <h1 className="font-serif text-2xl font-bold text-red-900">{name} Calendar</h1>
          <p className="mx-auto mt-1 max-w-xl text-sm text-gray-600">
            The past six months and the next six. Each square is a day - the darker it is, the more of
            its {cap ? `${cap} ` : ''}{name} slots are booked. Tap a day to see who was blessed, or to book it.
          </p>
          <Link href="/abhishekam" className={`${btnPrimary} mt-4 inline-flex`}>Book {name}</Link>
        </div>

        {seva.loading || calendar.loading ? (
          <LoadingBlock />
        ) : seva.error || calendar.error ? (
          <ErrorBlock message={(seva.error ?? calendar.error) as string} onRetry={seva.error ? seva.reload : calendar.reload} />
        ) : (
          <div className="mx-auto w-fit max-w-full rounded-2xl border border-amber-200 bg-white p-4 shadow-sm">
            <div className="flex gap-2">
              <div
                aria-hidden="true"
                className="grid shrink-0 gap-[3px] pt-5 text-[10px] text-gray-500"
                style={{ gridTemplateRows: `repeat(7, ${CELL}px)` }}
              >
                {WEEKDAY_LABELS.map((label, i) => <span key={i} className="leading-[13px]">{label}</span>)}
              </div>
              <div ref={scrollRef} className="min-w-0 overflow-x-auto pb-2">
                <div className="inline-flex flex-col gap-1">
                  <div
                    aria-hidden="true"
                    className="grid h-4 grid-flow-col gap-[3px] text-[10px] text-gray-500"
                    style={{ gridAutoColumns: `${CELL}px` }}
                  >
                    {weeks.map((week, i) => (
                      <span key={i} className="overflow-visible whitespace-nowrap">{week.monthLabel ?? ''}</span>
                    ))}
                  </div>
                  <div
                    role="group"
                    aria-label={`${name} bookings from ${longDate(start)} to ${longDate(end)}`}
                    className="grid grid-flow-col gap-[3px]"
                    style={{ gridTemplateRows: `repeat(7, ${CELL}px)`, gridAutoColumns: `${CELL}px` }}
                  >
                    {weeks.flatMap((week, w) =>
                      week.days.map((day, d) => {
                        if (!day) return <span key={`${w}-${d}`} aria-hidden="true" />;
                        const info = byDate.get(day);
                        const used = info?.slots_used ?? 0;
                        const total = info?.slots_total ?? null;
                        const isToday = day === today;
                        return (
                          <button
                            key={day}
                            ref={isToday ? todayRef : undefined}
                            type="button"
                            onClick={() => setSelected(day)}
                            aria-label={`${longDate(day)}${isToday ? ' (today)' : ''}: ${bookedText(used, total)}`}
                            title={`${formatDate(day)}: ${bookedText(used, total)}`}
                            className={`rounded-[3px] transition hover:ring-2 hover:ring-saffron focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-maroon ${LEVEL_CLASSES[slotLevel(used, total ?? SHADING_SCALE)]} ${isToday ? 'ring-2 ring-maroon-dark ring-offset-1' : ''}`}
                          />
                        );
                      }),
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-gray-500">
              <span className="flex items-center gap-2">
                <span className="inline-block h-[13px] w-[13px] rounded-[3px] bg-amber-50 ring-2 ring-maroon-dark ring-offset-1" aria-hidden="true" />
                Today
              </span>
              <span className="flex items-center gap-1">
                <span>Free</span>
                {LEVEL_CLASSES.map((cls, i) => (
                  <span key={i} title={LEVEL_LABELS[i]} className={`inline-block h-[13px] w-[13px] rounded-[3px] ${cls}`} aria-hidden="true" />
                ))}
                <span>Full</span>
              </span>
            </div>
          </div>
        )}

        <p className="mt-8 text-center text-sm">
          <Link href="/" className="text-red-900 hover:underline">← Back to the temple website</Link>
        </p>
      </div>

      {selected && seva.data && (
        <DayModal seva={seva.data} day={selected} today={today} onClose={() => setSelected(null)} />
      )}
    </main>
  );
}
