'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Clock, HeartHandshake } from 'lucide-react';
import BlessingAnimation from '@/components/public/BlessingAnimation';
import { LoadingBlock, Notice } from '@/components/ui/States';
import { getAbhishekamView } from '@/lib/api';
import { formatDate, formatDateTime } from '@/lib/format';
import { useLoad } from '@/hooks/useLoad';

export default function AbhishekamViewPage() {
  const params = useParams<{ id: string }>();
  const view = useLoad(() => getAbhishekamView(params.id), [params.id]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-b from-amber-50 to-templeWhite px-4 py-10">
      <div className="w-full max-w-md rounded-2xl border border-amber-200 bg-white p-8 text-center shadow-lg">
        {view.loading ? (
          <LoadingBlock />
        ) : view.error || !view.data ? (
          <>
            <h1 className="font-serif text-xl font-bold text-red-900">Not found</h1>
            <p className="mt-2 text-sm text-gray-500">
              This page doesn&apos;t exist, or the link is incorrect.
            </p>
          </>
        ) : view.data.status === 'pending' ? (
          <>
            <HeartHandshake className="mx-auto h-10 w-10 text-saffron" aria-hidden="true" />
            <h1 className="mt-3 font-serif text-xl font-bold text-maroon">Almost there</h1>
            <p className="mt-2 text-sm text-gray-600">
              Your {view.data.occasion} Abhishekam page for{' '}
              {formatDate(view.data.occasion_date)} will be ready as soon as the temple collects
              your Rs. 50 payment at the counter.
            </p>
            <p className="mt-3 rounded-lg bg-amber-50 py-2 font-mono text-sm font-bold text-maroon-dark">
              {view.data.reference_number}
            </p>
          </>
        ) : view.data.status === 'expired' ? (
          <>
            <Clock className="mx-auto h-10 w-10 text-gray-400" aria-hidden="true" />
            <h1 className="mt-3 font-serif text-xl font-bold text-maroon">This page has expired</h1>
            <p className="mt-2 text-sm text-gray-600">
              Abhishekam pages are visible for 7 days. This one - for {view.data.occasion} on{' '}
              {formatDate(view.data.occasion_date)} - is no longer available.
            </p>
          </>
        ) : (
          <>
            <h1 className="font-serif text-xl font-bold text-maroon">
              Blessings on your {view.data.occasion}
            </h1>
            <p className="mt-1 text-sm text-gray-500">{formatDate(view.data.occasion_date)}</p>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={view.data.photo_url ?? undefined}
              alt={`${view.data.devotee_name ?? 'Devotee'}'s occasion photo`}
              className="mx-auto mt-4 max-h-72 rounded-2xl border border-amber-200 object-contain"
            />
            <BlessingAnimation />
            <p className="mt-2 font-serif text-lg text-maroon-dark">{view.data.devotee_name}</p>
            {view.data.relation && <p className="text-sm text-gray-600">{view.data.relation}</p>}
            {view.data.message && (
              <p className="mt-3 rounded-lg bg-amber-50 px-4 py-3 text-sm italic text-gray-700">
                &ldquo;{view.data.message}&rdquo;
              </p>
            )}
            {view.data.expires_at && (
              <Notice kind="success">Visible until {formatDateTime(view.data.expires_at)}</Notice>
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
