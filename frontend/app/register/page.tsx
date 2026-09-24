'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Eye, EyeOff, Mail, UserPlus } from 'lucide-react';
import { apiError, login, register, setStoredToken, verifyLoginOtp } from '@/lib/api';
import { Notice } from '@/components/ui/States';
import { btnGhost, btnPrimary, inputCls } from '@/components/ui/styles';

type Step = 'details' | 'otp';

export default function RegisterPage() {
  const [step, setStep] = useState<Step>('details');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    setBusy(true);
    try {
      await register({
        username: username.trim(),
        password,
        email: email.trim(),
        phone: phone.trim(),
      });
      // Sign the devotee in right away rather than making them re-enter their
      // credentials on a separate page - a registered account always has an
      // email, so this always needs the sign-in code as its second step.
      const data = await login(username.trim(), password);
      if (data.otp_required) {
        setStep('otp');
        setBusy(false);
        return;
      }
      setStoredToken(data.access_token!);
      window.location.href = '/my-bookings';
    } catch (err) {
      setError(apiError(err, 'Could not create your account. Please try again.'));
      setBusy(false);
    }
  }

  async function onSubmitOtp(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    setBusy(true);
    try {
      const data = await verifyLoginOtp(username.trim(), code.trim());
      setStoredToken(data.access_token);
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
              For your security, enter the 6-digit code just emailed to {email}.
            </p>
            <div>
              <label htmlFor="otp" className="mb-1 block text-sm font-medium text-gray-700">
                Sign-in code
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
              {busy ? 'Verifying…' : 'Verify and finish'}
            </button>
            <div className="flex items-center justify-between text-sm">
              <button type="button" className="text-red-900 hover:underline" onClick={() => { setStep('details'); setCode(''); setError(''); }}>
                ← Back
              </button>
              <button
                type="button"
                className={btnGhost}
                disabled={busy}
                onClick={async () => {
                  setBusy(true);
                  setError('');
                  try {
                    await login(username.trim(), password);
                  } catch (err) {
                    setError(apiError(err, 'Could not resend the code. Please try again.'));
                  } finally {
                    setBusy(false);
                  }
                }}
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
          <button type="submit" disabled={busy || !username || !email.trim() || !phone.trim() || !password} className={`${btnPrimary} w-full`}>
            <UserPlus className="h-4 w-4" aria-hidden="true" />
            {busy ? 'Creating account…' : 'Create account'}
          </button>
        </form>
        )}

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
