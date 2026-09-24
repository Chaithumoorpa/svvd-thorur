'use client';

import React, { useState } from 'react';
import { CheckCircle2, Mail } from 'lucide-react';
import Field from '@/components/ui/Field';
import Modal from '@/components/ui/Modal';
import { Notice } from '@/components/ui/States';
import { btnGhost, btnPrimary, inputCls } from '@/components/ui/styles';
import { apiError, bookSeva, requestBookingOtp, verifyBookingOtp } from '@/lib/api';
import { formatDate, formatMoney, todayISO } from '@/lib/format';
import type { SevaTicket } from '@/lib/types';

type Step = 'email' | 'otp' | 'details' | 'done';

/** "Book" button + dialog for a seva. A paid seva still gets a ticket (PENDING),
 * with the fee collected in person at the temple counter instead of online - there's
 * no payment gateway yet. Booking is gated on a verified email either way: request a
 * code, verify it, then book. */
export default function BookSeva({
  sevaId,
  sevaName,
  isPaid = false,
  amount = 0,
}: {
  sevaId: number;
  sevaName: string;
  isPaid?: boolean;
  amount?: number;
}) {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState<Step>('email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [bookingToken, setBookingToken] = useState('');
  const [name, setName] = useState('');
  const [mobile, setMobile] = useState('');
  const [date, setDate] = useState(todayISO());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [ticket, setTicket] = useState<SevaTicket | null>(null);

  function close() {
    setOpen(false);
    setStep('email');
    setEmail('');
    setCode('');
    setBookingToken('');
    setName('');
    setMobile('');
    setError('');
    setTicket(null);
  }

  async function sendCode(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      await requestBookingOtp(email.trim());
      setStep('otp');
    } catch (err) {
      setError(apiError(err, 'Could not send the verification code. Please try again.'));
    } finally {
      setBusy(false);
    }
  }

  async function verifyCode(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      const { booking_token } = await verifyBookingOtp(email.trim(), code.trim());
      setBookingToken(booking_token);
      setStep('details');
    } catch (err) {
      setError(apiError(err, 'Incorrect or expired code. Please try again.'));
    } finally {
      setBusy(false);
    }
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      const booked = await bookSeva({
        seva_id: sevaId, devotee_name: name.trim(), mobile_number: mobile.trim(), seva_date: date,
        email: email.trim(), booking_token: bookingToken,
      });
      setTicket(booked);
      setStep('done');
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
          {step === 'done' && ticket ? (
            <div className="space-y-3 text-center">
              <CheckCircle2 className="mx-auto h-12 w-12 text-green-600" aria-hidden="true" />
              <h3 className="font-serif text-xl font-bold text-maroon">Seva booked</h3>
              <p className="text-sm text-gray-600">Please show this ticket number at the temple counter. A confirmation has also been emailed to you.</p>
              <p className="rounded-lg bg-amber-50 py-3 font-mono text-lg font-bold text-maroon-dark">{ticket.ticket_number}</p>
              <p className="text-sm text-gray-600">{ticket.seva_name} · {formatDate(ticket.seva_date)}<br />{ticket.devotee_name}</p>
              {ticket.payment_status === 'PENDING' && (
                <Notice kind="success">
                  Fee: {formatMoney(ticket.amount)} - please pay in cash at the temple counter when you arrive.
                </Notice>
              )}
              <button type="button" className={btnGhost} onClick={close}>Close</button>
            </div>
          ) : step === 'email' ? (
            <form onSubmit={sendCode} className="space-y-4">
              {error && <Notice kind="error">{error}</Notice>}
              <p className="text-sm text-gray-600">We&apos;ll email you a verification code before booking.</p>
              <Field label="Email address" required>
                <input className={inputCls} type="email" autoComplete="email" autoFocus value={email} onChange={(e) => setEmail(e.target.value)} />
              </Field>
              <div className="flex justify-end gap-2 pt-1">
                <button type="button" className={btnGhost} onClick={close}>Cancel</button>
                <button type="submit" className={btnPrimary} disabled={busy || !email.includes('@')}>
                  <Mail className="h-4 w-4" aria-hidden="true" />
                  {busy ? 'Sending…' : 'Send code'}
                </button>
              </div>
            </form>
          ) : step === 'otp' ? (
            <form onSubmit={verifyCode} className="space-y-4">
              {error && <Notice kind="error">{error}</Notice>}
              <p className="text-sm text-gray-600">Enter the 6-digit code sent to <strong>{email}</strong>.</p>
              <Field label="Verification code" required>
                <input className={inputCls} inputMode="numeric" maxLength={6} autoFocus value={code}
                       onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))} />
              </Field>
              <div className="flex justify-between gap-2 pt-1">
                <button type="button" className={btnGhost} onClick={() => { setStep('email'); setCode(''); setError(''); }}>Back</button>
                <div className="flex gap-2">
                  <button type="button" className={btnGhost} disabled={busy} onClick={sendCode}>Resend</button>
                  <button type="submit" className={btnPrimary} disabled={busy || code.length !== 6}>{busy ? 'Verifying…' : 'Verify'}</button>
                </div>
              </div>
            </form>
          ) : (
            <form onSubmit={submit} className="space-y-4">
              {error && <Notice kind="error">{error}</Notice>}
              {isPaid && (
                <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900">
                  This seva has a fee of {formatMoney(amount)}, payable in cash at the temple counter when you arrive.
                </p>
              )}
              <Field label="Devotee name" required><input className={inputCls} maxLength={100} autoComplete="name" autoFocus value={name} onChange={(e) => setName(e.target.value)} /></Field>
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
