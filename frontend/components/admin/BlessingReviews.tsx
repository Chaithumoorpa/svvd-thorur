'use client';

import React, { useState } from 'react';
import { Check, Eye, EyeOff, ImageOff, ShieldCheck, X } from 'lucide-react';
import ConfirmDialog from '@/components/admin/ConfirmDialog';
import { Notice } from '@/components/ui/States';
import { btnDanger, btnPrimary, cardCls } from '@/components/ui/styles';
import { useAction } from '@/hooks/useAction';
import { useLoad } from '@/hooks/useLoad';
import { getBlessingReviews, reviewBlessing } from '@/lib/api';
import { formatDate } from '@/lib/format';
import type { BlessingReview } from '@/lib/types';

/** Anyone with an email address can book a seva, so a devotee's photo, name
 * and occasion stay off the website until staff approve them here. Approving
 * publishes the photo (and shows the blessing if the devotee chose to);
 * rejecting deletes the photo and keeps the booking private - the seva and its
 * blessing email are unaffected. Renders nothing when there's nothing to review. */
export default function BlessingReviews({ onChanged }: { onChanged?: () => void }) {
  const reviews = useLoad(getBlessingReviews, []);
  const action = useAction();
  const [toReject, setToReject] = useState<BlessingReview | null>(null);

  async function decide(item: BlessingReview, approve: boolean) {
    const ok = await action.run(
      () => reviewBlessing(item.id, approve),
      approve ? `Approved ${item.devotee_name}'s blessing.` : `Rejected - ${item.devotee_name}'s photo was deleted.`,
    );
    if (ok) {
      setToReject(null);
      reviews.reload();
      onChanged?.();
    }
  }

  const items = reviews.data ?? [];
  if (!items.length && !action.success && !action.error) return null;

  return (
    <section aria-labelledby="blessing-reviews" className={`${cardCls} mb-6 p-4`}>
      <h2 id="blessing-reviews" className="flex items-center gap-2 font-semibold text-gray-900">
        <ShieldCheck className="h-5 w-5 text-amber-700" aria-hidden="true" />
        Blessings to review {items.length > 0 && <span className="rounded-full bg-amber-100 px-2 text-sm text-amber-800">{items.length}</span>}
      </h2>
      <p className="mt-1 text-sm text-gray-600">
        Nothing below is on the website yet. Approve only photos and wording suitable for the temple website.
      </p>
      {action.success && <div className="mt-3"><Notice kind="success">{action.success}</Notice></div>}
      {action.error && !toReject && <div className="mt-3"><Notice kind="error">{action.error}</Notice></div>}

      <ul className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <li key={item.id} className="flex flex-col rounded-lg border border-gray-200 p-3">
            {item.photo_preview_url ? (
              <a href={item.photo_preview_url} target="_blank" rel="noopener noreferrer" title="Open full size">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={item.photo_preview_url} alt={`Photo from ${item.devotee_name}`}
                     className="h-40 w-full rounded-md bg-gray-50 object-contain" />
              </a>
            ) : (
              <div className="flex h-40 items-center justify-center gap-2 rounded-md bg-gray-50 text-sm text-gray-400">
                <ImageOff className="h-5 w-5" aria-hidden="true" /> No photo
              </div>
            )}
            <p className="mt-2 font-medium text-gray-900">{item.devotee_name}</p>
            <p className="text-sm text-gray-600">{item.occasion}</p>
            <p className="text-xs text-gray-500">
              {item.seva_name} · {formatDate(item.seva_date)} · {item.ticket_number}
              {item.payment_status === 'PENDING' ? ' · fee not paid yet' : ''}
            </p>
            <p className="mt-1 flex items-center gap-1 text-xs text-gray-500">
              {item.show_publicly
                ? <><Eye className="h-3.5 w-3.5" aria-hidden="true" /> Wants it shown publicly</>
                : <><EyeOff className="h-3.5 w-3.5" aria-hidden="true" /> Private - photo on their own blessing page only</>}
            </p>
            <div className="mt-3 flex gap-2">
              <button type="button" className={btnPrimary} disabled={action.busy} onClick={() => decide(item, true)}>
                <Check className="h-4 w-4" aria-hidden="true" /> Approve
              </button>
              <button type="button" className={btnDanger} disabled={action.busy} onClick={() => { action.clear(); setToReject(item); }}>
                <X className="h-4 w-4" aria-hidden="true" /> Reject
              </button>
            </div>
          </li>
        ))}
      </ul>

      {toReject && (
        <ConfirmDialog
          title="Reject this blessing?"
          message={`${toReject.devotee_name}'s photo will be deleted and their booking kept private. The seva booking and their blessing email are not affected.`}
          confirmLabel="Reject"
          danger
          busy={action.busy}
          onConfirm={() => decide(toReject, false)}
          onCancel={() => setToReject(null)}
        />
      )}
    </section>
  );
}
