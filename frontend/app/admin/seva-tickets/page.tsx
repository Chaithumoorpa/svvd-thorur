'use client';

import React, { useState } from 'react';
import { Download, Plus, QrCode, Ticket, Trash2 } from 'lucide-react';
import AdminPage from '@/components/admin/AdminPage';
import ConfirmDialog from '@/components/admin/ConfirmDialog';
import Field from '@/components/ui/Field';
import Modal from '@/components/ui/Modal';
import Pager from '@/components/ui/Pager';
import { EmptyBlock, ErrorBlock, LoadingBlock, Notice } from '@/components/ui/States';
import { btnGhost, btnPrimary, cardCls, inputCls } from '@/components/ui/styles';
import { useAuth } from '@/components/admin/AuthContext';
import { useAction } from '@/hooks/useAction';
import { useLoad } from '@/hooks/useLoad';
import { createCounterTicket, deleteTicket, downloadTicketPdf, getPoojas, listTickets, saveBlob, scanTicket } from '@/lib/api';
import { formatDate, formatMoney, todayISO } from '@/lib/format';
import type { SevaTicket, TicketStatus } from '@/lib/types';

const PAGE_SIZE = 25;
const STATUS_CLS: Record<TicketStatus, string> = {
  ACTIVE: 'bg-green-100 text-green-800',
  USED: 'bg-gray-100 text-gray-600',
  CANCELLED: 'bg-red-100 text-red-700',
};

export default function SevaTicketsAdmin() {
  const { me } = useAuth();
  const [page, setPage] = useState(1);
  const [date, setDate] = useState('');
  const [status, setStatus] = useState<TicketStatus | ''>('');
  const [mobile, setMobile] = useState('');
  const list = useLoad(
    () => listTickets(page, { seva_date: date || undefined, status: status || undefined, mobile: mobile.trim() || undefined }, PAGE_SIZE),
    [page, date, status, mobile],
  );
  const sevas = useLoad(getPoojas, []);
  const action = useAction();

  const [scanOpen, setScanOpen] = useState(false);
  const [scanCode, setScanCode] = useState('');
  const [scanResult, setScanResult] = useState<{ ok: boolean; message: string } | null>(null);

  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({ seva_id: '', devotee_name: '', mobile_number: '', seva_date: todayISO(), payment_status: 'FREE' as 'FREE' | 'PAID', amount: '' });

  const [toDelete, setToDelete] = useState<SevaTicket | null>(null);

  async function remove() {
    if (!toDelete) return;
    const ok = await action.run(() => deleteTicket(toDelete.id), 'Ticket deleted.');
    if (ok) {
      setToDelete(null);
      list.reload();
    }
  }

  async function onScan(e: React.FormEvent) {
    e.preventDefault();
    const res = await action.run(() => scanTicket(scanCode.trim()));
    if (res) {
      setScanResult({ ok: res.success, message: res.message });
      if (res.success) {
        setScanCode('');
        list.reload();
      }
    }
  }

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    const ticket = await action.run(
      () =>
        createCounterTicket({
          seva_id: Number(form.seva_id),
          devotee_name: form.devotee_name.trim(),
          mobile_number: form.mobile_number.trim(),
          seva_date: form.seva_date,
          payment_status: form.payment_status,
          amount: form.payment_status === 'PAID' ? Number(form.amount || 0) : 0,
        }),
      'Ticket created.',
    );
    if (ticket) {
      setCreateOpen(false);
      setForm({ ...form, devotee_name: '', mobile_number: '', amount: '' });
      list.reload();
    }
  }

  async function pdf(id: string, number: string) {
    const blob = await action.run(() => downloadTicketPdf(id));
    if (blob) saveBlob(blob, `ticket_${number}.pdf`);
  }

  const onSevaChange = (id: string) => {
    const seva = sevas.data?.find((s) => String(s.id) === id);
    setForm((f) => ({ ...f, seva_id: id, payment_status: seva?.is_paid ? 'PAID' : 'FREE', amount: seva?.suggested_amount?.toString() ?? '' }));
  };

  return (
    <AdminPage
      title="Seva Tickets"
      description="Counter tickets, online bookings and ticket scanning."
      actions={
        <>
          <button type="button" className={btnGhost} onClick={() => { setScanOpen(true); setScanResult(null); }}>
            <QrCode className="h-4 w-4" aria-hidden="true" /> Scan ticket
          </button>
          <button type="button" className={btnPrimary} onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" aria-hidden="true" /> Counter ticket
          </button>
        </>
      }
    >
      <div className="mb-4 flex flex-wrap items-end gap-3">
        <Field label="Seva date"><input type="date" className={inputCls} value={date} onChange={(e) => { setPage(1); setDate(e.target.value); }} /></Field>
        <Field label="Status">
          <select className={inputCls} value={status} onChange={(e) => { setPage(1); setStatus(e.target.value as TicketStatus | ''); }}>
            <option value="">All</option>
            <option value="ACTIVE">Active</option>
            <option value="USED">Used</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </Field>
        <Field label="Mobile"><input className={inputCls} inputMode="tel" value={mobile} onChange={(e) => { setPage(1); setMobile(e.target.value); }} placeholder="Exact number" /></Field>
      </div>

      {action.success && <div className="mb-4"><Notice kind="success">{action.success}</Notice></div>}
      {action.error && !createOpen && !scanOpen && <div className="mb-4"><Notice kind="error">{action.error}</Notice></div>}

      {list.loading ? (
        <LoadingBlock />
      ) : list.error ? (
        <ErrorBlock message={list.error} onRetry={list.reload} />
      ) : !list.data?.items.length ? (
        <EmptyBlock icon={<Ticket className="h-10 w-10" />} title="No tickets found" hint="Try clearing the filters." />
      ) : (
        <>
          <div className={`${cardCls} overflow-x-auto`}>
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th scope="col" className="px-4 py-3">Ticket</th>
                  <th scope="col" className="px-4 py-3">Devotee</th>
                  <th scope="col" className="px-4 py-3">Seva</th>
                  <th scope="col" className="px-4 py-3">Date</th>
                  <th scope="col" className="px-4 py-3">Fee</th>
                  <th scope="col" className="px-4 py-3">Status</th>
                  <th scope="col" className="px-4 py-3"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {list.data.items.map((t) => (
                  <tr key={t.id}>
                    <td className="px-4 py-3 font-mono text-xs">{t.ticket_number}<div className="font-sans text-gray-400">{t.source === 'ONLINE' ? 'Online' : 'Counter'}</div></td>
                    <td className="px-4 py-3">{t.devotee_name}<div className="text-xs text-gray-400">{t.mobile_number}{t.email ? ` · ${t.email}` : ''}</div></td>
                    <td className="px-4 py-3 text-gray-700">{t.seva_name}</td>
                    <td className="px-4 py-3 text-gray-600">{formatDate(t.seva_date)}</td>
                    <td className="px-4 py-3 text-gray-600">{t.payment_status === 'PAID' ? formatMoney(t.amount) : 'Free'}</td>
                    <td className="px-4 py-3"><span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_CLS[t.status]}`}>{t.status.toLowerCase()}</span></td>
                    <td className="px-4 py-3 text-right">
                      <button type="button" className={btnGhost} onClick={() => pdf(t.id, t.ticket_number)} disabled={action.busy} aria-label={`Download ticket ${t.ticket_number}`}>
                        <Download className="h-4 w-4" />
                      </button>
                      {me.is_admin && (
                        <button type="button" className={btnGhost} onClick={() => setToDelete(t)} disabled={action.busy} aria-label={`Delete ticket ${t.ticket_number}`}>
                          <Trash2 className="h-4 w-4 text-red-700" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pager page={page} pageSize={PAGE_SIZE} total={list.data.total} onPage={setPage} />
        </>
      )}

      {scanOpen && (
        <Modal title="Scan ticket" onClose={() => { setScanOpen(false); action.clear(); }}>
          <form onSubmit={onScan} className="space-y-4">
            {action.error && <Notice kind="error">{action.error}</Notice>}
            {scanResult && <Notice kind={scanResult.ok ? 'success' : 'error'}>{scanResult.message}</Notice>}
            <Field label="QR code or ticket number" hint="Use a barcode scanner or type the ticket number, e.g. SVVD-2026-000123.">
              <input className={inputCls} autoComplete="off" value={scanCode} onChange={(e) => setScanCode(e.target.value)} />
            </Field>
            <div className="flex justify-end">
              <button type="submit" className={btnPrimary} disabled={action.busy || !scanCode.trim()}>{action.busy ? 'Checking…' : 'Validate ticket'}</button>
            </div>
          </form>
        </Modal>
      )}

      {createOpen && (
        <Modal title="Counter ticket" onClose={() => { setCreateOpen(false); action.clear(); }}>
          <form onSubmit={onCreate} className="space-y-4">
            {action.error && <Notice kind="error">{action.error}</Notice>}
            <Field label="Seva" required>
              <select className={inputCls} value={form.seva_id} onChange={(e) => onSevaChange(e.target.value)}>
                <option value="">Select a seva</option>
                {sevas.data?.map((s) => <option key={s.id} value={s.id}>{s.name}{s.is_paid ? ` — ${formatMoney(s.suggested_amount)}` : ''}</option>)}
              </select>
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Devotee name" required><input className={inputCls} maxLength={100} value={form.devotee_name} onChange={(e) => setForm({ ...form, devotee_name: e.target.value })} /></Field>
              <Field label="Mobile" required><input className={inputCls} inputMode="tel" value={form.mobile_number} onChange={(e) => setForm({ ...form, mobile_number: e.target.value })} /></Field>
              <Field label="Seva date" required><input type="date" className={inputCls} value={form.seva_date} onChange={(e) => setForm({ ...form, seva_date: e.target.value })} /></Field>
              <Field label="Payment">
                <select className={inputCls} value={form.payment_status} onChange={(e) => setForm({ ...form, payment_status: e.target.value as 'FREE' | 'PAID' })}>
                  <option value="FREE">Free</option>
                  <option value="PAID">Paid at counter</option>
                </select>
              </Field>
              {form.payment_status === 'PAID' && (
                <Field label="Amount received (₹)" required>
                  <input type="number" min="0" step="0.01" inputMode="decimal" className={inputCls} value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
                </Field>
              )}
            </div>
            {form.payment_status === 'PAID' && (
              <p className="text-xs text-gray-500">This will be added to the finance ledger automatically as cash income.</p>
            )}
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className={btnGhost} onClick={() => { setCreateOpen(false); action.clear(); }}>Cancel</button>
              <button type="submit" className={btnPrimary} disabled={action.busy || !form.seva_id || form.devotee_name.trim().length < 2 || !form.mobile_number.trim()}>
                {action.busy ? 'Creating…' : 'Create ticket'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {toDelete && (
        <ConfirmDialog
          title="Delete ticket?"
          message={`This permanently deletes ticket ${toDelete.ticket_number}${toDelete.payment_status === 'PAID' ? ' and removes its linked finance ledger entry' : ''}.`}
          confirmLabel="Delete"
          danger
          busy={action.busy}
          onConfirm={remove}
          onCancel={() => setToDelete(null)}
        />
      )}
    </AdminPage>
  );
}
