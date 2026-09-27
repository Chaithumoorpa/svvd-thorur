'use client';

import React from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { CalendarCheck, Clock, HeartHandshake } from 'lucide-react';
import BlessingAnimation from '@/components/public/BlessingAnimation';
import { LoadingBlock, Notice } from '@/components/ui/States';
import { useLoad } from '@/hooks/useLoad';
import { getPersonalBlessing } from '@/lib/api';
import { formatDate } from '@/lib/format';

/** A devotee's own blessing page, for a seva booked for an occasion - linked
 * from the blessing email sent on the seva date. Opens (name, photo, the
 * blessing animation) from the seva date for 7 days, once the fee is paid. */
export default function PersonalBlessingPage() {
  const { id } = useParams<{ id: string }>();
  const view = useLoad(() => getPersonalBlessing(id), [id]);
  const data = view.data;

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-b from-amber-50 to-templeWhite px-4 py-10">
      <div className="w-full max-w-md rounded-2xl border border-amber-200 bg-white p-8 text-center shadow-lg">
        {view.loading ? (
          <LoadingBlock />
        ) : view.error || !data ? (
          <>
            <h1 className="font-serif text-xl font-bold text-red-900">Not found</h1>
            <p className="mt-2 text-sm text-gray-500">This page doesn&apos;t exist, or the link is incorrect.</p>
          </>
        ) : data.status === 'pending' ? (
          <>
            <HeartHandshake className="mx-auto h-10 w-10 text-saffron" aria-hidden="true" />
            <h1 className="mt-3 font-serif text-xl font-bold text-maroon">Your {data.seva_name} is booked</h1>
            <p className="mt-2 text-sm text-gray-600">
              Please pay the seva fee at the temple counter. Once it&apos;s paid, on{' '}
              {formatDate(data.seva_date)} you&apos;ll receive your blessing for your {data.occasion} by
              email, and this page will open.
            </p>
          </>
        ) : data.status === 'scheduled' ? (
          <>
            <CalendarCheck className="mx-auto h-10 w-10 text-saffron" aria-hidden="true" />
            <h1 className="mt-3 font-serif text-xl font-bold text-maroon">Your {data.seva_name} is booked</h1>
            <p className="mt-2 text-sm text-gray-600">
              On {formatDate(data.seva_date)} we&apos;ll email you your blessing for your {data.occasion},
              and this page will open for 7 days.
            </p>
          </>
        ) : data.status === 'expired' ? (
          <>
            <Clock className="mx-auto h-10 w-10 text-gray-400" aria-hidden="true" />
            <h1 className="mt-3 font-serif text-xl font-bold text-maroon">This page has closed</h1>
            <p className="mt-2 text-sm text-gray-600">
              Blessing pages are open for 7 days. This one - for your {data.occasion} on{' '}
              {formatDate(data.seva_date)} - is no longer available.
            </p>
          </>
        ) : (
          <>
            <h1 className="font-serif text-xl font-bold text-maroon">Blessings on your {data.occasion}</h1>
            <p className="mt-1 text-sm text-gray-500">{data.seva_name} · {formatDate(data.seva_date)}</p>
            {data.photo_url && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={data.photo_url}
                alt={`${data.devotee_name ?? 'Devotee'}'s ${data.occasion} photo`}
                className="mx-auto mt-4 max-h-72 rounded-2xl border border-amber-200 object-contain"
              />
            )}
            <div className="mt-4">
              <BlessingAnimation />
            </div>
            <p className="mt-2 font-serif text-lg text-maroon-dark">{data.devotee_name}</p>
            {data.visible_until && (
              <div className="mt-4">
                <Notice kind="success">Open until {formatDate(data.visible_until)}</Notice>
              </div>
            )}
          </>
        )}

        <p className="mt-6 text-sm">
          <Link href="/" className="text-red-900 hover:underline">← Back to the temple website</Link>
        </p>
      </div>
    </main>
  );
}
