'use client';

import React, { useEffect, useState } from 'react';
import { isAxiosError } from 'axios';
import { CheckCircle2, ImagePlus, Mail } from 'lucide-react';
import Field from '@/components/ui/Field';
import Modal from '@/components/ui/Modal';
import { Notice } from '@/components/ui/States';
import TurnstileWidget from '@/components/ui/TurnstileWidget';
import { btnGhost, btnPrimary, inputCls } from '@/components/ui/styles';
import { useTurnstile } from '@/hooks/useTurnstile';
import {
  apiError, bookSeva, getSevaDay, requestBookingOtp, uploadBlessingPhoto, verifyBookingOtp,
} from '@/lib/api';
import { formatDate, formatMoney, todayISO } from '@/lib/format';
import type { Pooja, SevaTicket } from '@/lib/types';

type Step = 'email' | 'otp' | 'details' | 'done';
/** Free slots on `date` - only shown while that's still the chosen date. */
type Availability = { date: string; left: number; total: number };

/** "Book" button + dialog for a seva - the one booking form, for every seva
 * including Abhishekam. A paid seva still gets a ticket (PENDING), with the fee
 * collected in person at the temple counter - there's no payment gateway yet.
 * Booking is gated on a verified email: request a code, verify it, then book.
 * A seva with daily_slot_cap shows the chosen date's free slots; one with
 * public_blessings lets the devotee add a photo and show their blessing. */
export default function BookSeva({
  seva,
  initialDate,
  autoOpen = false,
  label = 'Book this seva',
}: {
  seva: Pooja;
  initialDate?: string;
  autoOpen?: boolean;
  label?: string;
}) {
  const [open, setOpen] = useState(autoOpen);
  const [step, setStep] = useState<Step>('email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [bookingToken, setBookingToken] = useState('');
  const [name, setName] = useState('');
  const [mobile, setMobile] = useState('');
  const [date, setDate] = useState(initialDate && initialDate >= todayISO() ? initialDate : todayISO());
  const [occasion, setOccasion] = useState('');
  const [photoKey, setPhotoKey] = useState('');
  const [photoPreview, setPhotoPreview] = useState(''); // local object URL - the upload itself is private
  const [showPublicly, setShowPublicly] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [availability, setAvailability] = useState<Availability | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [ticket, setTicket] = useState<SevaTicket | null>(null);
  const turnstile = useTurnstile();
  const offersBlessing = seva.public_blessings && occasion.trim().length > 0;
  const slots = availability?.date === date ? availability : null;
  const full = slots !== null && slots.left <= 0;

  // Free slots for the chosen date, for a seva with a daily cap.
  useEffect(() => {
    if (!open || step !== 'details' || !seva.daily_slot_cap || !date) return;
    let cancelled = false;
    getSevaDay(seva.id, date)
      .then((day) => {
        if (!cancelled && day.slots_total) {
          setAvailability({ date, left: day.slots_total - day.slots_used, total: day.slots_total });
        }
      })
      .catch(() => !cancelled && setAvailability(null));
    return () => {
      cancelled = true;
    };
  }, [open, step, seva.id, seva.daily_slot_cap, date]);

  function close() {
    setOpen(false);
    setStep('email');
    setEmail('');
    setCode('');
    setBookingToken('');
    setName('');
    setMobile('');
    setOccasion('');
    setPhotoKey('');
    setPhotoPreview('');
    setShowPublicly(false);
    setUploadError('');
    setAvailability(null);
    setError('');
    setTicket(null);
    turnstile.reset();
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

  async function handlePhoto(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setUploadError('');
    setUploading(true);
    try {
      setPhotoKey(await uploadBlessingPhoto(file));
      setPhotoPreview(URL.createObjectURL(file));
    } catch (err) {
      setUploadError(
        isAxiosError(err) && err.response?.status === 503
          ? 'Photo uploads are not set up yet. You can still book without one.'
          : 'Upload failed. Try a smaller image.',
      );
    } finally {
      setUploading(false);
    }
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      const booked = await bookSeva({
        seva_id: seva.id, devotee_name: name.trim(), mobile_number: mobile.trim(), seva_date: date,
        email: email.trim(), booking_token: bookingToken, occasion: occasion.trim() || undefined,
        photo_key: offersBlessing && photoKey ? photoKey : undefined,
        show_publicly: offersBlessing ? showPublicly : undefined,
        turnstile_token: turnstile.token || undefined,
      });
      turnstile.reset();
      setTicket(booked);
      setStep('done');
    } catch (err) {
      turnstile.reset();
      setError(apiError(err, 'Could not book the seva. Please try again.'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button type="button" className={btnPrimary} onClick={() => setOpen(true)}>{label}</button>
      {open && (
        <Modal title={`Book: ${seva.name}`} onClose={close}>
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
              {ticket.occasion && (
                <p className="text-sm text-gray-600">
                  On {formatDate(ticket.seva_date)} we&apos;ll email you a blessing for your {ticket.occasion}.
                  {ticket.review_status && ' The temple reviews photos and public blessings before they appear on the website.'}
                </p>
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
              {seva.is_paid && (
                <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900">
                  This seva has a fee of {formatMoney(seva.suggested_amount)}, payable in cash at the temple counter when you arrive.
                </p>
              )}
              <Field label="Devotee name" required><input className={inputCls} maxLength={100} autoComplete="name" autoFocus value={name} onChange={(e) => setName(e.target.value)} /></Field>
              <Field label="Mobile number" required hint="10 digits. Used to look up your booking at the temple."><input className={inputCls} type="tel" inputMode="tel" autoComplete="tel" value={mobile} onChange={(e) => setMobile(e.target.value)} /></Field>
              <div>
                <Field label="Seva date" required>
                  <input className={inputCls} type="date" min={todayISO()} value={date} onChange={(e) => setDate(e.target.value)} />
                </Field>
                {slots && (
                  <p role="status" className={`mt-1 text-xs ${full ? 'text-red-700' : 'text-green-700'}`}>
                    {full
                      ? `Fully booked on ${formatDate(date)} - please choose another date.`
                      : `${slots.left} of ${slots.total} slots left on ${formatDate(date)}.`}
                  </p>
                )}
              </div>
              <Field label="Booking for a special occasion?" hint="Optional - e.g. Birthday, Wedding Anniversary. We'll email you a blessing on the seva date.">
                <input className={inputCls} maxLength={100} placeholder="e.g. Birthday" value={occasion} onChange={(e) => setOccasion(e.target.value)} />
              </Field>
              {offersBlessing && (
                <fieldset className="space-y-3 rounded-lg border border-amber-200 bg-amber-50/50 p-3">
                  <legend className="px-1 text-sm font-medium text-maroon-dark">Share your blessing (optional)</legend>
                  <div>
                    <label className={`${btnGhost} cursor-pointer`}>
                      <ImagePlus className="h-4 w-4" aria-hidden="true" />
                      {uploading ? 'Uploading…' : photoKey ? 'Replace photo' : 'Add one photo'}
                      <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" className="hidden" disabled={uploading} onChange={handlePhoto} />
                    </label>
                    <p className="mt-1 text-xs text-gray-500">Shown with your blessing on the seva date, once the temple has reviewed it.</p>
                    {uploadError && <p className="mt-1 text-xs text-red-600">{uploadError}</p>}
                    {photoKey && photoPreview && (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={photoPreview} alt="Your occasion photo" className="mt-2 max-h-32 rounded-lg border border-amber-200 object-contain" />
                    )}
                  </div>
                  <label className="flex items-start gap-2 text-sm text-gray-700">
                    <input type="checkbox" className="mt-1" checked={showPublicly} onChange={(e) => setShowPublicly(e.target.checked)} />
                    <span>
                      Show my blessing publicly
                      <span className="block text-xs text-gray-500">
                        Your name and occasion on the {seva.name} calendar, and your photo on that day&apos;s
                        blessings page for 7 days, after the temple approves it. Leave unticked to keep it
                        private - you still get your blessing by email.
                      </span>
                    </span>
                  </label>
                </fieldset>
              )}
              <div className="flex justify-center">
                <TurnstileWidget key={turnstile.widgetKey} onToken={turnstile.setToken} onError={turnstile.setFailed} />
              </div>
              <div className="flex justify-end gap-2 pt-1">
                <button type="button" className={btnGhost} onClick={close}>Cancel</button>
                <button type="submit" className={btnPrimary} disabled={busy || uploading || full || name.trim().length < 2 || mobile.replace(/\D/g, '').length < 10 || !date || turnstile.blocked}>{busy ? 'Booking…' : 'Confirm booking'}</button>
              </div>
            </form>
          )}
        </Modal>
      )}
    </>
  );
}
