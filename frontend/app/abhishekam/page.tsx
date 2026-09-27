'use client';

import React, { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { isAxiosError } from 'axios';
import { CalendarDays, CheckCircle2, Mail, Upload } from 'lucide-react';
import Field from '@/components/ui/Field';
import { Notice } from '@/components/ui/States';
import TurnstileWidget from '@/components/ui/TurnstileWidget';
import { btnGhost, btnPrimary, inputCls } from '@/components/ui/styles';
import { useTurnstile } from '@/hooks/useTurnstile';
import {
  apiError, createAbhishekam, requestAbhishekamOtp, uploadAbhishekamPhoto, verifyAbhishekamOtp,
} from '@/lib/api';
import { formatDate, todayISO } from '@/lib/format';
import type { Abhishekam, AbhishekamVisibility } from '@/lib/types';

type Step = 'email' | 'otp' | 'details' | 'done';

export default function AbhishekamPage() {
  const searchParams = useSearchParams();
  const [step, setStep] = useState<Step>('email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [bookingToken, setBookingToken] = useState('');
  const [name, setName] = useState('');
  const [mobile, setMobile] = useState('');
  const [occasion, setOccasion] = useState('');
  const [occasionDate, setOccasionDate] = useState(searchParams.get('date') || todayISO());
  const [relation, setRelation] = useState('');
  const [message, setMessage] = useState('');
  const [photoUrl, setPhotoUrl] = useState('');
  const [visibility, setVisibility] = useState<AbhishekamVisibility>('PRIVATE');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<Abhishekam | null>(null);
  const turnstile = useTurnstile();

  async function sendCode(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      await requestAbhishekamOtp(email.trim());
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
      const { booking_token } = await verifyAbhishekamOtp(email.trim(), code.trim());
      setBookingToken(booking_token);
      setStep('details');
    } catch (err) {
      setError(apiError(err, 'Incorrect or expired code. Please try again.'));
    } finally {
      setBusy(false);
    }
  }

  async function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setUploadError('');
    setUploading(true);
    try {
      setPhotoUrl(await uploadAbhishekamPhoto(file));
    } catch (err) {
      setUploadError(
        isAxiosError(err) && err.response?.status === 503
          ? 'Photo uploads are not set up yet. Please try again later.'
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
      const abhishekam = await createAbhishekam({
        devotee_name: name.trim(), mobile_number: mobile.trim(), email: email.trim(),
        occasion: occasion.trim(), occasion_date: occasionDate, relation: relation.trim() || undefined,
        message: message.trim() || undefined, photo_url: photoUrl, visibility, booking_token: bookingToken,
        turnstile_token: turnstile.token || undefined,
      });
      turnstile.reset();
      setResult(abhishekam);
      setStep('done');
    } catch (err) {
      turnstile.reset();
      setError(apiError(err, 'That date may be fully booked, or something else went wrong. Please try again.'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-b from-amber-50 to-templeWhite px-4 py-10">
      <div className="w-full max-w-md rounded-2xl border border-amber-200 bg-white p-8 shadow-lg">
        <div className="mb-6 text-center">
          <h1 className="font-serif text-2xl font-bold text-red-900">Abhishekam</h1>
          <p className="mt-1 text-sm text-gray-500">
            Book an Abhishekam for your birthday, wedding anniversary, or any special occasion, and
            receive the temple&apos;s blessings on your own page - Rs. 50, payable at the temple
            counter. Only 7 slots are available per day.
          </p>
          <Link href="/abhishekam/calendar" className="mt-2 inline-flex items-center gap-1 text-sm text-red-900 hover:underline">
            <CalendarDays className="h-4 w-4" aria-hidden="true" /> Check available dates
          </Link>
        </div>

        {step === 'done' && result ? (
          <div className="space-y-3 text-center">
            <CheckCircle2 className="mx-auto h-12 w-12 text-green-600" aria-hidden="true" />
            <h2 className="font-serif text-xl font-bold text-maroon">Request received</h2>
            <p className="rounded-lg bg-amber-50 py-3 font-mono text-lg font-bold text-maroon-dark">
              {result.reference_number}
            </p>
            <Notice kind="success">
              Please pay Rs. 50 in cash at the temple counter, quoting this reference number. On{' '}
              {formatDate(result.occasion_date)} you&apos;ll receive your blessing by email, and your page
              opens for 7 days.
            </Notice>
            <Link href={`/abhishekam/${result.id}`} className={`${btnGhost} inline-flex`}>
              View my page
            </Link>
          </div>
        ) : step === 'email' ? (
          <form onSubmit={sendCode} className="space-y-4">
            {error && <Notice kind="error">{error}</Notice>}
            <p className="text-sm text-gray-600">We&apos;ll email you a verification code before continuing.</p>
            <Field label="Email address" required>
              <input className={inputCls} type="email" autoComplete="email" autoFocus value={email} onChange={(e) => setEmail(e.target.value)} />
            </Field>
            <button type="submit" className={`${btnPrimary} w-full`} disabled={busy || !email.includes('@')}>
              <Mail className="h-4 w-4" aria-hidden="true" />
              {busy ? 'Sending…' : 'Send code'}
            </button>
          </form>
        ) : step === 'otp' ? (
          <form onSubmit={verifyCode} className="space-y-4">
            {error && <Notice kind="error">{error}</Notice>}
            <p className="text-sm text-gray-600">Enter the 6-digit code sent to <strong>{email}</strong>.</p>
            <Field label="Verification code" required>
              <input className={inputCls} inputMode="numeric" maxLength={6} autoFocus value={code}
                     onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))} />
            </Field>
            <div className="flex justify-between gap-2">
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
            <Field label="Your name" required><input className={inputCls} maxLength={100} autoFocus value={name} onChange={(e) => setName(e.target.value)} /></Field>
            <Field label="Mobile number" required><input className={inputCls} type="tel" value={mobile} onChange={(e) => setMobile(e.target.value)} /></Field>
            <Field label="Occasion" required hint="e.g. Birthday, Wedding Anniversary, House Warming">
              <input className={inputCls} maxLength={100} placeholder="e.g. Birthday" value={occasion} onChange={(e) => setOccasion(e.target.value)} />
            </Field>
            <Field label="Abhishekam date" required hint="Only 7 slots per day - check the calendar if you're not sure.">
              <input className={inputCls} type="date" min={todayISO()} value={occasionDate} onChange={(e) => setOccasionDate(e.target.value)} />
            </Field>
            <Field label="Who is this for?" hint="Optional - e.g. My son's birthday">
              <input className={inputCls} maxLength={200} value={relation} onChange={(e) => setRelation(e.target.value)} />
            </Field>
            <Field label="A personal message or wish" hint="Optional - shown on your page">
              <textarea className={inputCls} rows={3} maxLength={500} value={message} onChange={(e) => setMessage(e.target.value)} />
            </Field>
            <Field label="Photo" required hint="One photo, shown on your blessing page. Choosing another replaces it.">
              <div>
                <label className={`${btnGhost} cursor-pointer`}>
                  <Upload className="h-4 w-4" aria-hidden="true" />
                  {uploading ? 'Uploading…' : photoUrl ? 'Replace photo' : 'Upload one photo'}
                  <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" className="hidden" disabled={uploading} onChange={handleFileSelect} />
                </label>
                {uploadError && <p className="mt-1 text-xs text-red-600">{uploadError}</p>}
                {photoUrl && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={photoUrl} alt="Preview" className="mt-2 max-h-40 rounded-lg border border-gray-200 object-contain" />
                )}
              </div>
            </Field>
            <Field label="Show on the public calendar?" hint="Public: your name and occasion appear on the Abhishekam calendar, and your photo on that day's blessings page for 7 days. Private: nothing is shown publicly - you receive your blessing by email and on your own page.">
              <div className="flex gap-4 text-sm">
                <label className="flex items-center gap-2">
                  <input type="radio" name="visibility" checked={visibility === 'PRIVATE'} onChange={() => setVisibility('PRIVATE')} />
                  Private
                </label>
                <label className="flex items-center gap-2">
                  <input type="radio" name="visibility" checked={visibility === 'PUBLIC'} onChange={() => setVisibility('PUBLIC')} />
                  Public
                </label>
              </div>
            </Field>
            <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900">
              Fee: Rs. 50, payable in cash at the temple counter after you submit.
            </p>
            <div className="flex justify-center">
              <TurnstileWidget key={turnstile.widgetKey} onToken={turnstile.setToken} />
            </div>
            <button type="submit" className={`${btnPrimary} w-full`}
                    disabled={busy || !name.trim() || !mobile.trim() || !occasion.trim() || !photoUrl}>
              {busy ? 'Submitting…' : 'Submit request'}
            </button>
          </form>
        )}

        <p className="mt-6 text-center text-sm">
          <Link href="/" className="text-red-900 hover:underline">← Back to the temple website</Link>
        </p>
      </div>
    </main>
  );
}
