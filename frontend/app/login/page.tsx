'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Eye, EyeOff, LogIn } from 'lucide-react';
import { apiError, login, setStoredToken } from '@/lib/api';
import { Notice } from '@/components/ui/States';
import { btnPrimary, inputCls } from '@/components/ui/styles';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    setBusy(true);
    try {
      const data = await login(username.trim(), password);
      setStoredToken(data.access_token);
      // full navigation so the admin layout starts from a clean auth state
      window.location.href = data.must_change_password ? '/admin/change-password' : '/admin';
    } catch (err) {
      setError(apiError(err, 'Sign in failed. Please try again.'));
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-b from-amber-50 to-templeWhite px-4 py-10">
      <div className="w-full max-w-sm rounded-2xl border border-amber-200 bg-white p-8 shadow-lg">
        <div className="mb-6 text-center">
          <Image src="/logo.png" alt="" width={64} height={64} className="mx-auto mb-3" />
          <h1 className="font-serif text-2xl font-bold text-red-900">Temple Staff Sign In</h1>
          <p className="mt-1 text-sm text-gray-500">For temple administrators and trustees</p>
        </div>

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

        <p className="mt-4 text-center text-sm">
          <Link href="/forgot-password" className="text-red-900 hover:underline">
            Forgot password?
          </Link>
        </p>
        <p className="mt-2 text-center text-sm">
          <Link href="/" className="text-red-900 hover:underline">
            ← Back to the temple website
          </Link>
        </p>
      </div>
    </main>
  );
}
