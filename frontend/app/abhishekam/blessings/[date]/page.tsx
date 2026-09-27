'use client';

import React from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { CalendarDays } from 'lucide-react';
import BlessingsCarousel from '@/components/public/BlessingsCarousel';
import { ErrorBlock, LoadingBlock } from '@/components/ui/States';
import { btnGhost, btnPrimary } from '@/components/ui/styles';
import { useLoad } from '@/hooks/useLoad';
import { getAbhishekamDayFlyer } from '@/lib/api';
import { formatDate, formatLongDate as longDate, todayISO } from '@/lib/format';

/** A date's public blessings: while active (the date plus 6 more days) every
 * PUBLIC, paid Abhishekam's photo in a carousel; before and after that, just
 * the names and occasions - the same permanent timeline as the calendar. */
export default function DayBlessingsPage() {
  const { date } = useParams<{ date: string }>();
  const day = useLoad(() => getAbhishekamDayFlyer(date), [date]);
  const data = day.data;
  const withPhotos = data?.entries.filter((e) => e.photo_url) ?? [];

  return (
    <main className="min-h-screen bg-gradient-to-b from-amber-50 to-templeWhite px-4 py-10">
      <div className="mx-auto w-full max-w-xl rounded-2xl border border-amber-200 bg-white p-6 text-center shadow-lg sm:p-8">
        {day.loading ? (
          <LoadingBlock />
        ) : day.error || !data ? (
          <ErrorBlock message={day.error ?? 'Could not load this day.'} onRetry={day.reload} />
        ) : (
          <>
            <h1 className="font-serif text-2xl font-bold text-red-900">Blessings</h1>
            <p className="mt-1 text-sm text-gray-500">{longDate(data.date)}</p>

            <div className="mt-6">
              {data.blessing_status === 'active' && withPhotos.length > 0 ? (
                <>
                  <BlessingsCarousel entries={withPhotos} />
                  <p className="mt-4 text-xs text-gray-400">On display until {formatDate(data.visible_until)}</p>
                </>
              ) : data.entries.length === 0 ? (
                <p className="text-sm text-gray-600">No public blessings for this day.</p>
              ) : (
                <>
                  <p className="text-sm text-gray-600">
                    {data.blessing_status === 'upcoming'
                      ? `Photos for this day go on display on ${formatDate(data.date)}.`
                      : `Photos for this day were on display until ${formatDate(data.visible_until)}.`}
                  </p>
                  <ul className="mt-4 divide-y divide-amber-100 rounded-lg border border-amber-100 bg-amber-50/60 text-left">
                    {data.entries.map((entry, i) => (
                      <li key={i} className="px-4 py-2 text-sm">
                        <span className="font-medium text-maroon-dark">{entry.devotee_name}</span>
                        <span className="text-gray-600"> - {entry.occasion}</span>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>

            <div className="mt-8 flex flex-col justify-center gap-2 sm:flex-row">
              {data.date >= todayISO() && data.slots_used < data.slots_total && (
                <Link href={`/abhishekam?date=${data.date}`} className={`${btnPrimary} justify-center`}>
                  Book Abhishekam for this day
                </Link>
              )}
              <Link href="/abhishekam/calendar" className={`${btnGhost} justify-center`}>
                <CalendarDays className="h-4 w-4" aria-hidden="true" /> Abhishekam calendar
              </Link>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
