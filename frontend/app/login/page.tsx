'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Eye, EyeOff, LogIn, Mail } from 'lucide-react';
import { apiError, getMe, login, setStoredToken, verifyLoginOtp } from '@/lib/api';
import { Notice } from '@/components/ui/States';
import { btnGhost, btnPrimary, inputCls } from '@/components/ui/styles';

type Step = 'credentials' | 'otp';

export default function LoginPage() {
  const [step, setStep] = useState<Step>('credentials');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function finishLogin(data: { access_token: string; must_change_password: boolean }) {
    setStoredToken(data.access_token);
    if (data.must_change_password) {
      window.location.href = '/admin/change-password';
      return;
    }
    // Same login for everyone; where it lands depends on the account's roles.
    const me = await getMe();
    // full navigation so the admin layout starts from a clean auth state
    window.location.href = me.is_admin || me.is_trustee || me.permissions.length > 0 ? '/admin' : '/my-bookings';
  }

  async function onSubmitCredentials(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    setBusy(true);
    try {
      const data = await login(username.trim(), password);
      if (data.otp_required) {
        setStep('otp');
        setBusy(false);
        return;
      }
      await finishLogin({ access_token: data.access_token!, must_change_password: !!data.must_change_password });
    } catch (err) {
      setError(apiError(err, 'Sign in failed. Please try again.'));
      setBusy(false);
    }
  }

  async function onSubmitOtp(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    setBusy(true);
    try {
      const data = await verifyLoginOtp(username.trim(), code.trim());
      await finishLogin(data);
    } catch (err) {
      setError(apiError(err, 'Incorrect or expired code. Please try again.'));
      setBusy(false);
    }
  }

  async function resendCode() {
    setError('');
    setBusy(true);
    try {
      await login(username.trim(), password);
    } catch (err) {
      setError(apiError(err, 'Could not resend the code. Please try again.'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-b from-amber-50 to-templeWhite px-4 py-10">
      <div className="w-full max-w-sm rounded-2xl border border-amber-200 bg-white p-8 shadow-lg">
        <div className="mb-6 text-center">
          <Image src="/logo.png" alt="" width={64} height={64} className="mx-auto mb-3" />
          <h1 className="font-serif text-2xl font-bold text-red-900">Sign in</h1>
          <p className="mt-1 text-sm text-gray-500">For devotees and temple staff</p>
        </div>

        {step === 'credentials' ? (
          <form onSubmit={onSubmitCredentials} className="space-y-4" noValidate>
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
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
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
                  autoComplete="current-password"
                  required
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
            </div>
            <button type="submit" disabled={busy || !username || !password} className={`${btnPrimary} w-full`}>
              <LogIn className="h-4 w-4" aria-hidden="true" />
              {busy ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        ) : (
          <form onSubmit={onSubmitOtp} className="space-y-4" noValidate>
            {error && <Notice kind="error">{error}</Notice>}
            <p className="text-sm text-gray-600">
              <Mail className="mr-1 inline h-4 w-4 text-red-900" aria-hidden="true" />
              For your security, enter the 6-digit code just emailed to your account&apos;s address.
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
              {busy ? 'Verifying…' : 'Verify and sign in'}
            </button>
            <div className="flex items-center justify-between text-sm">
              <button type="button" className="text-red-900 hover:underline" onClick={() => { setStep('credentials'); setCode(''); setError(''); }}>
                ← Back
              </button>
              <button type="button" className={btnGhost} disabled={busy} onClick={resendCode}>
                Resend code
              </button>
            </div>
          </form>
        )}

        {step === 'credentials' && (
          <>
            <p className="mt-4 text-center text-sm">
              New here?{' '}
              <Link href="/register" className="text-red-900 hover:underline">
                Create an account
              </Link>
            </p>
            <p className="mt-2 text-center text-sm">
              <Link href="/forgot-password" className="text-red-900 hover:underline">
                Forgot password?
              </Link>
            </p>
          </>
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
