'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Eye, EyeOff, Mail, UserPlus } from 'lucide-react';
import { apiError, register, requestRegisterCode } from '@/lib/api';
import { Notice } from '@/components/ui/States';
import TurnstileWidget from '@/components/ui/TurnstileWidget';
import { btnGhost, btnPrimary, inputCls } from '@/components/ui/styles';
import { useTurnstile } from '@/hooks/useTurnstile';

type Step = 'details' | 'otp';

export default function RegisterPage() {
  const [step, setStep] = useState<Step>('details');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [code, setCode] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const turnstile = useTurnstile();

  // Step 1: check the details and email a code. No account exists until step 2.
  async function sendCode() {
    setError('');
    setBusy(true);
    try {
      await requestRegisterCode({
        username: username.trim(), email: email.trim(), phone: phone.trim(),
        turnstile_token: turnstile.token || undefined,
      });
      turnstile.reset(); // single-use - a resend needs a fresh one
      setStep('otp');
    } catch (err) {
      turnstile.reset();
      setError(apiError(err, 'Could not send the code. Please try again.'));
    } finally {
      setBusy(false);
    }
  }

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    await sendCode();
  }

  // Step 2: the code proves the email; the account is created and signed in.
  async function onSubmitOtp(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    setBusy(true);
    try {
      await register({
        username: username.trim(), password, email: email.trim(), phone: phone.trim(),
        accept_terms: acceptTerms, email_code: code.trim(),
      });
      window.location.href = '/my-bookings';
    } catch (err) {
      setError(apiError(err, 'Incorrect or expired code. Please try again.'));
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-b from-amber-50 to-templeWhite px-4 py-10">
      <div className="w-full max-w-sm rounded-2xl border border-amber-200 bg-white p-8 shadow-lg">
        <div className="mb-6 text-center">
          <Image src="/logo.png" alt="" width={64} height={64} className="mx-auto mb-3" />
          <h1 className="font-serif text-2xl font-bold text-red-900">Create an account</h1>
          <p className="mt-1 text-sm text-gray-500">Book sevas and view your booking history</p>
        </div>

        {step === 'otp' ? (
          <form onSubmit={onSubmitOtp} className="space-y-4" noValidate>
            {error && <Notice kind="error">{error}</Notice>}
            <p className="text-sm text-gray-600">
              <Mail className="mr-1 inline h-4 w-4 text-red-900" aria-hidden="true" />
              To confirm it's your email, enter the 6-digit code we just sent to {email}. Your account is
              created once the code is confirmed.
            </p>
            <div>
              <label htmlFor="otp" className="mb-1 block text-sm font-medium text-gray-700">
                Sign-up code
              </label>
              <input
                id="otp"
                className={inputCls}
                inputMode="numeric"
                maxLength={6}
                autoFocus
                autoComplete="one-time-code"
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
              />
            </div>
            <button type="submit" disabled={busy || code.length !== 6} className={`${btnPrimary} w-full`}>
              {busy ? 'Creating account…' : 'Confirm and create account'}
            </button>
            <div className="flex items-center justify-between text-sm">
              <button type="button" className="text-red-900 hover:underline" onClick={() => { setStep('details'); setCode(''); setError(''); }}>
                ← Back
              </button>
              <button
                type="button"
                className={btnGhost}
                disabled={busy || turnstile.blocked}
                onClick={sendCode}
              >
                Resend code
              </button>
            </div>
          </form>
        ) : (
        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          {error && <Notice kind="error">{error}</Notice>}
          <div>
            <label htmlFor="username" className="mb-1 block text-sm font-medium text-gray-700">
              Username
            </label>
            <input
              id="username"
              className={inputCls}
              autoComplete="username"
              autoFocus
              required
              minLength={3}
              maxLength={100}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="email" className="mb-1 block text-sm font-medium text-gray-700">
              Email
            </label>
            <input
              id="email"
              type="email"
              className={inputCls}
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="phone" className="mb-1 block text-sm font-medium text-gray-700">
              Mobile number
            </label>
            <input
              id="phone"
              type="tel"
              className={inputCls}
              autoComplete="tel"
              required
              maxLength={20}
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
            <p className="mt-1 text-xs text-gray-500">10 digits.</p>
          </div>
          <div>
            <label htmlFor="password" className="mb-1 block text-sm font-medium text-gray-700">
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                className={`${inputCls} pr-10`}
                autoComplete="new-password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-500"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            <p className="mt-1 text-xs text-gray-500">At least 8 characters, with a letter and a digit.</p>
          </div>
          <label className="flex items-start gap-2 text-sm text-gray-700">
            <input
              type="checkbox" className="mt-1" required
              checked={acceptTerms} onChange={(e) => setAcceptTerms(e.target.checked)}
            />
            <span>
              I agree to the{' '}
              <Link href="/legal/terms" target="_blank" className="text-red-900 hover:underline">Terms &amp; Conditions</Link>
              {' '}and{' '}
              <Link href="/legal/privacy-policy" target="_blank" className="text-red-900 hover:underline">Privacy Policy</Link>.
            </span>
          </label>
          <button
            type="submit"
            disabled={busy || !username || !email.trim() || !phone.trim() || !password || !acceptTerms || turnstile.blocked}
            className={`${btnPrimary} w-full`}
          >
            <UserPlus className="h-4 w-4" aria-hidden="true" />
            {busy ? 'Sending code…' : 'Continue - email me a code'}
          </button>
        </form>
        )}

        <div className="mt-4 flex justify-center">
          <TurnstileWidget key={turnstile.widgetKey} onToken={turnstile.setToken} onError={turnstile.setFailed} />
        </div>

        {step === 'details' && (
          <p className="mt-4 text-center text-sm">
            Already have an account?{' '}
            <Link href="/login" className="text-red-900 hover:underline">
              Sign in
            </Link>
          </p>
        )}
        <p className="mt-2 text-center text-sm">
          <Link href="/" className="text-red-900 hover:underline">
            ← Back to the temple website
          </Link>
        </p>
      </div>
    </main>
  );
}
