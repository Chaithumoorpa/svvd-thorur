'use client';

import React, { Suspense, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useSearchParams } from 'next/navigation';
import { Eye, EyeOff, KeyRound } from 'lucide-react';
import { apiError, resetPassword } from '@/lib/api';
import { LoadingBlock, Notice } from '@/components/ui/States';
import { btnPrimary, inputCls } from '@/components/ui/styles';

function ResetPasswordForm() {
  const token = useSearchParams().get('token') ?? '';
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    setBusy(true);
    try {
      await resetPassword(token, password);
      setDone(true);
    } catch (err) {
      setError(apiError(err, 'This reset link is invalid or has expired.'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="w-full max-w-sm rounded-2xl border border-amber-200 bg-white p-8 shadow-lg">
      <div className="mb-6 text-center">
        <Image src="/logo.png" alt="" width={64} height={64} className="mx-auto mb-3" />
        <h1 className="font-serif text-2xl font-bold text-red-900">Set a new password</h1>
      </div>

      {!token ? (
        <Notice kind="error">This link is missing its reset token. Request a new one below.</Notice>
      ) : done ? (
        <Notice kind="success">Your password has been reset. You can now sign in.</Notice>
      ) : (
        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          {error && <Notice kind="error">{error}</Notice>}
          <div>
            <label htmlFor="password" className="mb-1 block text-sm font-medium text-gray-700">
              New password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                className={`${inputCls} pr-10`}
                autoComplete="new-password"
                autoFocus
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
          <button type="submit" disabled={busy || !password} className={`${btnPrimary} w-full`}>
            <KeyRound className="h-4 w-4" aria-hidden="true" />
            {busy ? 'Saving…' : 'Save new password'}
          </button>
        </form>
      )}

      <p className="mt-6 text-center text-sm">
        <Link href="/forgot-password" className="text-red-900 hover:underline">
          Request a new link
        </Link>
        {' · '}
        <Link href="/login" className="text-red-900 hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-b from-amber-50 to-templeWhite px-4 py-10">
      <Suspense fallback={<LoadingBlock />}>
        <ResetPasswordForm />
      </Suspense>
    </main>
  );
}
