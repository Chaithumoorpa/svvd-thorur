'use client';

import React, { useState } from 'react';
import { CheckCircle2 } from 'lucide-react';
import Field from '@/components/ui/Field';
import Modal from '@/components/ui/Modal';
import { Notice } from '@/components/ui/States';
import { btnGhost, btnPrimary, inputCls } from '@/components/ui/styles';
import { apiError, bookSeva } from '@/lib/api';
import { formatDate, todayISO } from '@/lib/format';
import type { SevaTicket } from '@/lib/types';

/** "Book" button + dialog for a FREE seva. Paid sevas are booked at the counter. */
export default function BookSeva({ sevaId, sevaName }: { sevaId: number; sevaName: string }) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [mobile, setMobile] = useState('');
  const [date, setDate] = useState(todayISO());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [ticket, setTicket] = useState<SevaTicket | null>(null);

  function close() {
    setOpen(false);
    setError('');
    setTicket(null);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      setTicket(await bookSeva({ seva_id: sevaId, devotee_name: name.trim(), mobile_number: mobile.trim(), seva_date: date }));
    } catch (err) {
      setError(apiError(err, 'Could not book the seva. Please try again.'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button type="button" className={btnPrimary} onClick={() => setOpen(true)}>Book this seva</button>
      {open && (
        <Modal title={`Book: ${sevaName}`} onClose={close}>
          {ticket ? (
            <div className="space-y-3 text-center">
              <CheckCircle2 className="mx-auto h-12 w-12 text-green-600" aria-hidden="true" />
              <h3 className="font-serif text-xl font-bold text-maroon">Seva booked</h3>
              <p className="text-sm text-gray-600">Please show this ticket number at the temple counter.</p>
              <p className="rounded-lg bg-amber-50 py-3 font-mono text-lg font-bold text-maroon-dark">{ticket.ticket_number}</p>
              <p className="text-sm text-gray-600">{ticket.seva_name} · {formatDate(ticket.seva_date)}<br />{ticket.devotee_name}</p>
              <button type="button" className={btnGhost} onClick={close}>Close</button>
            </div>
          ) : (
            <form onSubmit={submit} className="space-y-4">
              {error && <Notice kind="error">{error}</Notice>}
              <Field label="Devotee name" required><input className={inputCls} maxLength={100} autoComplete="name" value={name} onChange={(e) => setName(e.target.value)} /></Field>
              <Field label="Mobile number" required hint="10 digits. Used to look up your booking at the temple."><input className={inputCls} type="tel" inputMode="tel" autoComplete="tel" value={mobile} onChange={(e) => setMobile(e.target.value)} /></Field>
              <Field label="Seva date" required><input className={inputCls} type="date" min={todayISO()} value={date} onChange={(e) => setDate(e.target.value)} /></Field>
              <div className="flex justify-end gap-2 pt-1">
                <button type="button" className={btnGhost} onClick={close}>Cancel</button>
                <button type="submit" className={btnPrimary} disabled={busy || name.trim().length < 2 || mobile.replace(/\D/g, '').length < 10 || !date}>{busy ? 'Booking…' : 'Confirm booking'}</button>
              </div>
            </form>
          )}
        </Modal>
      )}
    </>
  );
}
