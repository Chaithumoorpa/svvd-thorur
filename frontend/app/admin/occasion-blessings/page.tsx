'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Banknote, ExternalLink, HeartHandshake } from 'lucide-react';
import AdminPage, { StatusPill } from '@/components/admin/AdminPage';
import Pager from '@/components/ui/Pager';
import { EmptyBlock, ErrorBlock, LoadingBlock, Notice } from '@/components/ui/States';
import { btnGhost, cardCls, inputCls } from '@/components/ui/styles';
import { useAction } from '@/hooks/useAction';
import { useLoad } from '@/hooks/useLoad';
import { collectOccasionBlessingPayment, listOccasionBlessings } from '@/lib/api';
import { formatDate, formatMoney } from '@/lib/format';

const PAGE_SIZE = 25;

export default function OccasionBlessingsAdmin() {
  const [page, setPage] = useState(1);
  const [pendingOnly, setPendingOnly] = useState(true);
  const list = useLoad(() => listOccasionBlessings(page, pendingOnly, PAGE_SIZE), [page, pendingOnly]);
  const action = useAction();

  async function collect(id: string) {
    const ok = await action.run(() => collectOccasionBlessingPayment(id), 'Payment collected - the page is now live for 7 days.');
    if (ok) list.reload();
  }

  return (
    <AdminPage
      title="Occasion Blessings"
      description="Devotees' paid photo + occasion pages (Rs. 50, pay-at-counter). Collect payment here to make a page go live for 7 days."
    >
      <div className="mb-4 flex items-center gap-2">
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={pendingOnly}
            onChange={(e) => { setPage(1); setPendingOnly(e.target.checked); }}
          />
          Show pending payment only
        </label>
      </div>

      {action.success && <div className="mb-4"><Notice kind="success">{action.success}</Notice></div>}
      {action.error && <div className="mb-4"><Notice kind="error">{action.error}</Notice></div>}

      {list.loading ? (
        <LoadingBlock />
      ) : list.error ? (
        <ErrorBlock message={list.error} onRetry={list.reload} />
      ) : !list.data?.items.length ? (
        <EmptyBlock icon={<HeartHandshake className="h-10 w-10" />} title="No requests" hint={pendingOnly ? 'Nothing waiting on payment right now.' : 'No Occasion Blessing requests yet.'} />
      ) : (
        <>
          <div className={`${cardCls} overflow-x-auto`}>
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th scope="col" className="px-4 py-3">Reference</th>
                  <th scope="col" className="px-4 py-3">Devotee</th>
                  <th scope="col" className="px-4 py-3">Occasion</th>
                  <th scope="col" className="px-4 py-3">Date</th>
                  <th scope="col" className="px-4 py-3 text-right">Fee</th>
                  <th scope="col" className="px-4 py-3">Status</th>
                  <th scope="col" className="px-4 py-3"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {list.data.items.map((b) => (
                  <tr key={b.id}>
                    <td className="px-4 py-3 font-mono text-xs text-gray-700">{b.reference_number}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">{b.devotee_name}</div>
                      <div className="text-xs text-gray-400">{b.mobile_number}</div>
                    </td>
                    <td className="px-4 py-3 text-gray-700">
                      {b.occasion}
                      {b.relation && <div className="text-xs text-gray-400">{b.relation}</div>}
                    </td>
                    <td className="px-4 py-3 text-gray-600">{formatDate(b.occasion_date)}</td>
                    <td className="px-4 py-3 text-right font-medium">{formatMoney(b.amount)}</td>
                    <td className="px-4 py-3">
                      <StatusPill on={b.payment_status === 'PAID'} onLabel="Paid" offLabel="Pending" />
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        {b.payment_status === 'PENDING' ? (
                          <button type="button" className={btnGhost} disabled={action.busy} onClick={() => collect(b.id)}>
                            <Banknote className="h-4 w-4" aria-hidden="true" /> Collect payment
                          </button>
                        ) : (
                          <Link href={`/blessings/${b.id}`} target="_blank" className={btnGhost}>
                            <ExternalLink className="h-4 w-4" aria-hidden="true" /> View page
                          </Link>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pager page={page} pageSize={PAGE_SIZE} total={list.data.total} onPage={setPage} />
        </>
      )}
    </AdminPage>
  );
}
