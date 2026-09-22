'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Mail } from 'lucide-react';
import { apiError, forgotPassword } from '@/lib/api';
import { Notice } from '@/components/ui/States';
import { btnPrimary, inputCls } from '@/components/ui/styles';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    setBusy(true);
    try {
      await forgotPassword(email.trim());
      setSent(true);
    } catch (err) {
      setError(apiError(err, 'Something went wrong. Please try again.'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-b from-amber-50 to-templeWhite px-4 py-10">
      <div className="w-full max-w-sm rounded-2xl border border-amber-200 bg-white p-8 shadow-lg">
        <div className="mb-6 text-center">
          <Image src="/logo.png" alt="" width={64} height={64} className="mx-auto mb-3" />
          <h1 className="font-serif text-2xl font-bold text-red-900">Reset your password</h1>
          <p className="mt-1 text-sm text-gray-500">We&apos;ll email you a link to set a new one</p>
        </div>

        {sent ? (
          <Notice kind="success">
            If that email is registered, a reset link has been sent. It&apos;s valid for 1 hour - check
            your inbox (and spam folder).
          </Notice>
        ) : (
          <form onSubmit={onSubmit} className="space-y-4" noValidate>
            {error && <Notice kind="error">{error}</Notice>}
            <div>
              <label htmlFor="email" className="mb-1 block text-sm font-medium text-gray-700">
                Email address
              </label>
              <input
                id="email"
                type="email"
                className={inputCls}
                autoComplete="email"
                autoFocus
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <button type="submit" disabled={busy || !email} className={`${btnPrimary} w-full`}>
              <Mail className="h-4 w-4" aria-hidden="true" />
              {busy ? 'Sending…' : 'Send reset link'}
            </button>
          </form>
        )}

        <p className="mt-6 text-center text-sm">
          <Link href="/login" className="text-red-900 hover:underline">
            ← Back to sign in
          </Link>
        </p>
      </div>
    </main>
  );
}
