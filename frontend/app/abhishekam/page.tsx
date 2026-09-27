'use client';

import React from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { CalendarDays, Clock } from 'lucide-react';
import BookSeva from '@/components/public/BookSeva';
import TempleTime from '@/components/public/TempleTime';
import { ErrorBlock, LoadingBlock } from '@/components/ui/States';
import { btnGhost } from '@/components/ui/styles';
import { useBlessingSeva } from '@/hooks/useBlessingSeva';
import { formatMoney, formatTimeRange } from '@/lib/format';

/** The Abhishekam seva's own page - the same booking form as on /poojas. The
 * calendar's "Book Abhishekam for DD/MM" links here with ?date=, which opens
 * the form with that date filled in. */
export default function AbhishekamPage() {
  const date = useSearchParams().get('date') ?? undefined;
  const seva = useBlessingSeva();

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-b from-amber-50 to-templeWhite px-4 py-10">
      <div className="w-full max-w-md rounded-2xl border border-amber-200 bg-white p-8 text-center shadow-lg">
        {seva.loading ? (
          <LoadingBlock />
        ) : seva.error ? (
          <ErrorBlock message={seva.error} onRetry={seva.reload} />
        ) : !seva.data ? (
          <>
            <h1 className="font-serif text-2xl font-bold text-red-900">Abhishekam</h1>
            <p className="mt-2 text-sm text-gray-600">Online Abhishekam booking isn&apos;t open yet.</p>
            <Link href="/poojas" className={`${btnGhost} mt-4 inline-flex`}>See all sevas</Link>
          </>
        ) : (
          <>
            <h1 className="font-serif text-2xl font-bold text-red-900">{seva.data.name}</h1>
            <p className="mt-1 text-sm font-semibold text-amber-800">
              {seva.data.is_paid ? formatMoney(seva.data.suggested_amount) : 'Free'}
              {seva.data.daily_slot_cap ? ` · ${seva.data.daily_slot_cap} bookings a day` : ''}
            </p>
            {formatTimeRange(seva.data.start_time, seva.data.end_time) && (
              <p className="mt-1 inline-flex items-center gap-1 text-sm text-gray-500">
                <Clock className="h-3.5 w-3.5" aria-hidden="true" />
                <span><TempleTime start={seva.data.start_time} end={seva.data.end_time} stacked /></span>
              </p>
            )}
            {seva.data.description && <p className="mt-3 text-sm text-gray-700">{seva.data.description}</p>}
            <p className="mt-4 text-sm text-gray-600">
              Booking for a birthday, anniversary or any special occasion? Add it to your booking and on
              the day you&apos;ll receive the temple&apos;s blessing by email - and, if you like, it can
              appear on the temple website with your photo.
            </p>
            <div className="mt-6 flex flex-col items-center gap-3">
              <div className="text-left">{/* the dialog renders in place - keep it out of the card's centring */}
                <BookSeva seva={seva.data} initialDate={date} autoOpen={!!date} label={`Book ${seva.data.name}`} />
              </div>
              <Link href="/abhishekam/calendar" className="inline-flex items-center gap-1 text-sm font-medium text-maroon hover:underline">
                <CalendarDays className="h-4 w-4" aria-hidden="true" /> See available dates and blessings
              </Link>
            </div>
          </>
        )}
        <p className="mt-6 text-sm">
          <Link href="/" className="text-red-900 hover:underline">← Back to the temple website</Link>
        </p>
      </div>
    </main>
  );
}
