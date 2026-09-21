'use client';

import React, { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Download, FileText, HandHeart, Plus } from 'lucide-react';
import AdminPage from '@/components/admin/AdminPage';
import { useAuth } from '@/components/admin/AuthContext';
import Field from '@/components/ui/Field';
import Modal from '@/components/ui/Modal';
import Pager from '@/components/ui/Pager';
import { EmptyBlock, ErrorBlock, LoadingBlock, Notice } from '@/components/ui/States';
import { btnGhost, btnPrimary, cardCls, inputCls } from '@/components/ui/styles';
import { useAction } from '@/hooks/useAction';
import { useLoad } from '@/hooks/useLoad';
import { createDonation, downloadReceipt, issueReceipt, listDonations, listDonors, saveBlob } from '@/lib/api';
import { emptyToNull, formatDate, formatMoney } from '@/lib/format';
import type { Donation, DonationType, Donor, PaymentMode } from '@/lib/types';

const PAGE_SIZE = 25;
const TYPES: Array<{ value: DonationType; label: string }> = [
  { value: 'general', label: 'General' },
  { value: 'annadanam', label: 'Annadanam' },
  { value: 'festival', label: 'Festival' },
  { value: 'pooja', label: 'Pooja / Seva' },
  { value: 'construction', label: 'Construction' },
  { value: 'other', label: 'Other' },
];
const MODES: PaymentMode[] = ['CASH', 'UPI', 'BANK', 'CHEQUE'];

function DonorPicker({ onPick, picked }: { onPick: (d: Donor | null) => void; picked: Donor | null }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Donor[]>([]);
  useEffect(() => {
    if (picked || query.trim().length < 2) {
      setResults([]);
      return;
    }
    const handle = setTimeout(() => {
      listDonors(1, query.trim(), 6).then((r) => setResults(r.items)).catch(() => setResults([]));
    }, 250);
    return () => clearTimeout(handle);
  }, [query, picked]);

  if (picked) {
    return (
      <div className="flex items-center justify-between rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 text-sm">
        <span>{picked.name}{picked.phone ? ` · ${picked.phone}` : ''}</span>
        <button type="button" className="text-red-900 hover:underline" onClick={() => onPick(null)}>Change</button>
      </div>
    );
  }
  return (
    <div className="relative">
      <input className={inputCls} placeholder="Type a donor name or phone" value={query} onChange={(e) => setQuery(e.target.value)} autoComplete="off" />
      {results.length > 0 && (
        <ul className="absolute z-10 mt-1 w-full overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg">
          {results.map((d) => (
            <li key={d.id}>
              <button type="button" className="block w-full px-3 py-2 text-left text-sm hover:bg-amber-50" onClick={() => onPick(d)}>
                {d.name}<span className="text-gray-400">{d.phone ? ` · ${d.phone}` : ''}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {query.trim().length >= 2 && results.length === 0 && <p className="mt-1 text-xs text-gray-500">No matching donor. Add them on the Donors page first.</p>}
    </div>
  );
}

function DonationsInner() {
  const { can } = useAuth();
  const canWrite = can('donations:write');
  const params = useSearchParams();
  const donorFilter = params.get('donor') ? Number(params.get('donor')) : undefined;

  const [page, setPage] = useState(1);
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const list = useLoad(
    () => listDonations(page, { donor_id: donorFilter, start_date: start || undefined, end_date: end || undefined }, PAGE_SIZE),
    [page, start, end, donorFilter],
  );
  const action = useAction();
  const [creating, setCreating] = useState(false);
  const [donor, setDonor] = useState<Donor | null>(null);
  const [form, setForm] = useState({ amount: '', donation_type: 'general' as DonationType, payment_mode: 'CASH' as PaymentMode, purpose: '', donated_on: '' });

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!donor) return;
    const ok = await action.run(
      () =>
        createDonation({
          donor_id: donor.id,
          amount: Number(form.amount),
          donation_type: form.donation_type,
          payment_mode: form.payment_mode,
          purpose: emptyToNull(form.purpose),
          donated_on: form.donated_on ? `${form.donated_on}T12:00:00` : null,
        }),
      'Donation recorded.',
    );
    if (ok) {
      setCreating(false);
      setDonor(null);
      setForm({ amount: '', donation_type: 'general', payment_mode: 'CASH', purpose: '', donated_on: '' });
      list.reload();
    }
  }

  async function receipt(d: Donation) {
    const issued = d.receipt_number ? d : await action.run(() => issueReceipt(d.id));
    if (!issued) return;
    const blob = await action.run(() => downloadReceipt(d.id));
    if (blob) saveBlob(blob, `Receipt_${issued.receipt_number}.pdf`);
    list.reload();
  }

  return (
    <AdminPage
      title="Donations"
      description={donorFilter ? `Showing donations for donor #${donorFilter}.` : 'Every gift received, newest first. Recording a donation also adds it to the finance ledger.'}
      actions={
        canWrite && (
          <button type="button" className={btnPrimary} onClick={() => setCreating(true)}>
            <Plus className="h-4 w-4" aria-hidden="true" /> Record donation
          </button>
        )
      }
    >
      <div className="mb-4 flex flex-wrap items-end gap-3">
        <Field label="From"><input type="date" className={inputCls} value={start} onChange={(e) => { setPage(1); setStart(e.target.value); }} /></Field>
        <Field label="To"><input type="date" className={inputCls} min={start || undefined} value={end} onChange={(e) => { setPage(1); setEnd(e.target.value); }} /></Field>
        {(start || end) && <button type="button" className={btnGhost} onClick={() => { setStart(''); setEnd(''); setPage(1); }}>Clear</button>}
      </div>

      {action.success && <div className="mb-4"><Notice kind="success">{action.success}</Notice></div>}
      {action.error && !creating && <div className="mb-4"><Notice kind="error">{action.error}</Notice></div>}

      {list.loading ? (
        <LoadingBlock />
      ) : list.error ? (
        <ErrorBlock message={list.error} onRetry={list.reload} />
      ) : !list.data?.items.length ? (
        <EmptyBlock icon={<HandHeart className="h-10 w-10" />} title="No donations found" hint="Recorded donations will appear here." />
      ) : (
        <>
          <div className={`${cardCls} overflow-x-auto`}>
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th scope="col" className="px-4 py-3">Date</th>
                  <th scope="col" className="px-4 py-3">Donor</th>
                  <th scope="col" className="px-4 py-3">Type</th>
                  <th scope="col" className="px-4 py-3">Mode</th>
                  <th scope="col" className="px-4 py-3 text-right">Amount</th>
                  <th scope="col" className="px-4 py-3">Receipt</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {list.data.items.map((d) => (
                  <tr key={d.id}>
                    <td className="px-4 py-3 text-gray-600">{formatDate(d.donated_on)}</td>
                    <td className="px-4 py-3 font-medium text-gray-900">{d.donor_name ?? `#${d.donor_id}`}</td>
                    <td className="px-4 py-3 capitalize text-gray-600">{d.donation_type}</td>
                    <td className="px-4 py-3 text-gray-600">{d.payment_mode}</td>
                    <td className="px-4 py-3 text-right font-medium">{formatMoney(d.amount)}</td>
                    <td className="px-4 py-3">
                      <button type="button" className={btnGhost} disabled={action.busy || (!d.receipt_number && !canWrite)} onClick={() => receipt(d)}>
                        {d.receipt_number ? <Download className="h-4 w-4" aria-hidden="true" /> : <FileText className="h-4 w-4" aria-hidden="true" />}
                        {d.receipt_number ?? 'Issue receipt'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pager page={page} pageSize={PAGE_SIZE} total={list.data.total} onPage={setPage} />
        </>
      )}

      {creating && (
        <Modal title="Record donation" onClose={() => { setCreating(false); action.clear(); }}>
          <form onSubmit={save} className="space-y-4">
            {action.error && <Notice kind="error">{action.error}</Notice>}
            <Field label="Donor" required><DonorPicker picked={donor} onPick={setDonor} /></Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Amount (₹)" required>
                <input type="number" min="0.01" step="0.01" inputMode="decimal" className={inputCls} value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
              </Field>
              <Field label="Date" hint="Leave empty for today.">
                <input type="date" className={inputCls} max={new Date().toISOString().slice(0, 10)} value={form.donated_on} onChange={(e) => setForm({ ...form, donated_on: e.target.value })} />
              </Field>
              <Field label="Purpose">
                <select className={inputCls} value={form.donation_type} onChange={(e) => setForm({ ...form, donation_type: e.target.value as DonationType })}>
                  {TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </Field>
              <Field label="Payment mode">
                <select className={inputCls} value={form.payment_mode} onChange={(e) => setForm({ ...form, payment_mode: e.target.value as PaymentMode })}>
                  {MODES.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              </Field>
            </div>
            <Field label="Note"><input className={inputCls} maxLength={1000} value={form.purpose} onChange={(e) => setForm({ ...form, purpose: e.target.value })} /></Field>
            <p className="text-xs text-gray-500">This will also be added to the finance ledger automatically.</p>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className={btnGhost} onClick={() => { setCreating(false); action.clear(); }}>Cancel</button>
              <button type="submit" className={btnPrimary} disabled={action.busy || !donor || !(Number(form.amount) > 0)}>
                {action.busy ? 'Saving…' : 'Record donation'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </AdminPage>
  );
}

export default function DonationsAdmin() {
  return (
    <Suspense fallback={<LoadingBlock />}>
      <DonationsInner />
    </Suspense>
  );
}
