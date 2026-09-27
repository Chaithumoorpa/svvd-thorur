'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import Modal from '@/components/ui/Modal';
import { ErrorBlock, LoadingBlock, Notice } from '@/components/ui/States';
import { btnGhost, btnPrimary } from '@/components/ui/styles';
import { useLoad } from '@/hooks/useLoad';
import { getAbhishekamCalendar, getAbhishekamDayFlyer } from '@/lib/api';
import { formatDate, todayISO } from '@/lib/format';
import type { AbhishekamCalendarDay } from '@/lib/types';

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

function daysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate();
}

/** GitHub-contributions-style intensity, replicating the temple's paper
 * Abhishekam register (a full month x day grid) but colored by how many of
 * the DAILY_SLOT_CAP slots are taken that day. */
function cellClass(day: AbhishekamCalendarDay | undefined): string {
  if (!day || day.slots_used === 0) return 'bg-amber-50 text-amber-900 border-amber-100';
  const ratio = day.slots_used / day.slots_total;
  if (ratio >= 1) return 'bg-maroon text-white border-maroon';
  if (ratio >= 0.7) return 'bg-orange-500 text-white border-orange-500';
  if (ratio >= 0.4) return 'bg-amber-400 text-amber-950 border-amber-400';
  return 'bg-amber-200 text-amber-950 border-amber-200';
}

function DayFlyerModal({ date, onClose }: { date: string; onClose: () => void }) {
  const flyer = useLoad(() => getAbhishekamDayFlyer(date), [date]);
  const canBook = date >= todayISO() && (!flyer.data || flyer.data.slots_used < flyer.data.slots_total);

  return (
    <Modal title={formatDate(date, { day: 'numeric', month: 'long', year: 'numeric' })} onClose={onClose}>
      {flyer.loading ? (
        <LoadingBlock />
      ) : flyer.error || !flyer.data ? (
        <ErrorBlock message={flyer.error ?? 'Could not load this day.'} onRetry={flyer.reload} />
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            {flyer.data.slots_used} of {flyer.data.slots_total} slots taken.
          </p>
          {flyer.data.entries.length === 0 ? (
            <p className="text-sm text-gray-500">
              {flyer.data.slots_used > 0
                ? 'All bookings for this day are kept private.'
                : 'No Abhishekams booked for this day yet.'}
            </p>
          ) : (
            <ul className="space-y-3">
              {flyer.data.entries.map((entry, i) => (
                <li key={i} className="flex items-center gap-3 rounded-lg border border-amber-100 bg-amber-50 p-3">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={entry.photo_url} alt="" className="h-12 w-12 flex-none rounded-full border border-amber-200 object-cover" />
                  <div className="min-w-0">
                    <p className="font-medium text-maroon-dark">{entry.devotee_name}</p>
                    <p className="text-sm text-gray-600">{entry.occasion}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
          {canBook ? (
            <Link href={`/abhishekam?date=${date}`} className={`${btnPrimary} w-full justify-center`}>
              Book this day
            </Link>
          ) : date < todayISO() ? (
            <Notice kind="error">This date has passed.</Notice>
          ) : (
            <Notice kind="error">This day is fully booked.</Notice>
          )}
        </div>
      )}
    </Modal>
  );
}

export default function AbhishekamCalendarPage() {
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState(currentYear);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const calendar = useLoad(() => getAbhishekamCalendar(year), [year]);

  const byDate = new Map((calendar.data ?? []).map((d) => [d.date, d]));

  return (
    <main className="min-h-screen bg-gradient-to-b from-amber-50 to-templeWhite px-4 py-10">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 text-center">
          <h1 className="font-serif text-2xl font-bold text-red-900">Abhishekam Calendar</h1>
          <p className="mt-1 text-sm text-gray-500">
            Click any day to see who has been blessed, and whether slots remain.
          </p>
          <Link href="/abhishekam" className={`${btnGhost} mt-3 inline-flex`}>Book an Abhishekam</Link>
        </div>

        <div className="mb-4 flex items-center justify-center gap-4">
          <button type="button" className={btnGhost} onClick={() => setYear((y) => y - 1)} aria-label="Previous year">
            <ChevronLeft className="h-4 w-4" aria-hidden="true" />
          </button>
          <span className="text-lg font-semibold text-maroon-dark">{year}</span>
          <button type="button" className={btnGhost} onClick={() => setYear((y) => y + 1)} aria-label="Next year">
            <ChevronRight className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        {calendar.loading ? (
          <LoadingBlock />
        ) : calendar.error ? (
          <ErrorBlock message={calendar.error} onRetry={calendar.reload} />
        ) : (
          <div className="overflow-x-auto rounded-2xl border border-amber-200 bg-white p-4 shadow-sm">
            <table className="border-collapse text-xs">
              <tbody>
                {MONTH_NAMES.map((monthName, monthIndex) => (
                  <tr key={monthName}>
                    <th scope="row" className="sticky left-0 bg-white pr-3 text-right font-medium text-gray-600">
                      {monthName}
                    </th>
                    {Array.from({ length: 31 }, (_, i) => i + 1).map((dayNum) => {
                      if (dayNum > daysInMonth(year, monthIndex)) {
                        return <td key={dayNum} className="p-0.5" />;
                      }
                      const date = `${year}-${String(monthIndex + 1).padStart(2, '0')}-${String(dayNum).padStart(2, '0')}`;
                      const day = byDate.get(date);
                      return (
                        <td key={dayNum} className="p-0.5">
                          <button
                            type="button"
                            onClick={() => setSelectedDate(date)}
                            title={`${monthName} ${dayNum}, ${year} - ${day?.slots_used ?? 0}/${day?.slots_total ?? 7} slots taken`}
                            className={`h-5 w-5 rounded border text-[10px] leading-5 transition hover:ring-2 hover:ring-saffron ${cellClass(day)}`}
                          >
                            {dayNum}
                          </button>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="mt-4 flex items-center justify-center gap-4 text-xs text-gray-500">
          <span>Fewer slots taken</span>
          <span className="h-4 w-4 rounded border border-amber-100 bg-amber-50" />
          <span className="h-4 w-4 rounded border border-amber-200 bg-amber-200" />
          <span className="h-4 w-4 rounded border border-amber-400 bg-amber-400" />
          <span className="h-4 w-4 rounded border border-orange-500 bg-orange-500" />
          <span className="h-4 w-4 rounded border border-maroon bg-maroon" />
          <span>Fully booked</span>
        </div>

        <p className="mt-8 text-center text-sm">
          <Link href="/" className="text-red-900 hover:underline">← Back to the temple website</Link>
        </p>
      </div>

      {selectedDate && <DayFlyerModal date={selectedDate} onClose={() => setSelectedDate(null)} />}
    </main>
  );
}
