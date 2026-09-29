'use client';

import React, { Suspense, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { BellOff } from 'lucide-react';
import { LoadingBlock, Notice } from '@/components/ui/States';
import { btnGhost, btnPrimary } from '@/components/ui/styles';
import { useLoad } from '@/hooks/useLoad';
import { apiError, getNotificationPreference, setNotificationPreference } from '@/lib/api';

/** Reached from the unsubscribe link at the bottom of a darshan-timing or
 * announcement broadcast email. The GET lookup is read-only (so an email
 * client's link-prefetch can't silently opt someone out) - only the button
 * click actually changes anything, and it doubles as a resubscribe control
 * if the devotee already opted out. */
function UnsubscribeForm() {
  const token = useSearchParams().get('token') ?? '';
  const status = useLoad(() => getNotificationPreference(token), [token]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [receiveNotifications, setReceiveNotifications] = useState<boolean | null>(null);

  const current = receiveNotifications ?? status.data?.receive_notifications ?? null;

  async function toggle() {
    if (current === null) return;
    setError('');
    setBusy(true);
    try {
      const result = await setNotificationPreference(token, !current);
      setReceiveNotifications(result.receive_notifications);
    } catch (err) {
      setError(apiError(err, 'This link is invalid or has expired.'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="w-full max-w-sm rounded-2xl border border-amber-200 bg-white p-8 shadow-lg text-center">
      <Image src="/logo.png" alt="" width={64} height={64} className="mx-auto mb-3" />
      <BellOff className="mx-auto mb-2 h-8 w-8 text-maroon" aria-hidden="true" />
      <h1 className="font-serif text-2xl font-bold text-red-900">Notification preferences</h1>

      {!token ? (
        <Notice kind="error">This link is missing its token. Use the link from the email you received.</Notice>
      ) : status.loading ? (
        <LoadingBlock />
      ) : status.error ? (
        <Notice kind="error">{status.error}</Notice>
      ) : (
        <>
          {error && <Notice kind="error">{error}</Notice>}
          <p className="mt-3 text-sm text-gray-600">
            {status.data?.email && <>{status.data.email}<br /></>}
            {current
              ? 'You currently receive email notifications for darshan timing changes and new announcements.'
              : 'You are unsubscribed from these emails.'}
          </p>
          <button
            type="button"
            onClick={toggle}
            disabled={busy || current === null}
            className={`${current ? btnGhost : btnPrimary} mx-auto mt-6`}
          >
            {busy ? 'Saving…' : current ? 'Unsubscribe' : 'Resubscribe'}
          </button>
        </>
      )}

      <p className="mt-6 text-center text-sm">
        <Link href="/" className="text-red-900 hover:underline">Back to the website</Link>
      </p>
    </div>
  );
}

export default function UnsubscribePage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-b from-amber-50 to-templeWhite px-4 py-10">
      <Suspense fallback={<LoadingBlock />}>
        <UnsubscribeForm />
      </Suspense>
    </main>
  );
}
