'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Eye, EyeOff, UserPlus } from 'lucide-react';
import { apiError, login, register, setStoredToken } from '@/lib/api';
import { Notice } from '@/components/ui/States';
import { btnPrimary, inputCls } from '@/components/ui/styles';

export default function RegisterPage() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
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
      // Sign the devotee in immediately rather than making them re-enter their
      // credentials on a separate page right after they just typed them.
      const data = await login(username.trim(), password);
      setStoredToken(data.access_token);
      window.location.href = '/my-bookings';
    } catch (err) {
      setError(apiError(err, 'Could not create your account. Please try again.'));
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

        <p className="mt-4 text-center text-sm">
          Already have an account?{' '}
          <Link href="/login" className="text-red-900 hover:underline">
            Sign in
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
