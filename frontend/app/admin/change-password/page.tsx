'use client';

import React, { useState } from 'react';
import { Lock } from 'lucide-react';
import AdminPage from '@/components/admin/AdminPage';
import Field from '@/components/ui/Field';
import { Notice } from '@/components/ui/States';
import { btnPrimary, cardCls, inputCls } from '@/components/ui/styles';
import { apiError, changePassword } from '@/lib/api';

export default function ChangePasswordPage() {
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    if (next !== confirm) return setError('The new passwords do not match.');
    if (next.length < 8 || !/[A-Za-z]/.test(next) || !/\d/.test(next)) {
      return setError('Use at least 8 characters with a letter and a number.');
    }
    setBusy(true);
    try {
      await changePassword(current, next);
      setDone(true);
      setTimeout(() => (window.location.href = '/admin'), 1500);
    } catch (err) {
      setError(apiError(err, 'Could not change the password.'));
      setBusy(false);
    }
  }

  return (
    <AdminPage title="Change password" description="Choose a new password you have not used before.">
      <form onSubmit={onSubmit} className={`${cardCls} mx-auto max-w-md space-y-4 p-6`} noValidate>
        {error && <Notice kind="error">{error}</Notice>}
        {done && <Notice kind="success">Password changed. Redirecting…</Notice>}
        <Field label="Current password" required>
          <input type="password" autoComplete="current-password" className={inputCls} value={current} onChange={(e) => setCurrent(e.target.value)} />
        </Field>
        <Field label="New password" required hint="At least 8 characters, with a letter and a number.">
          <input type="password" autoComplete="new-password" className={inputCls} value={next} onChange={(e) => setNext(e.target.value)} />
        </Field>
        <Field label="Confirm new password" required>
          <input type="password" autoComplete="new-password" className={inputCls} value={confirm} onChange={(e) => setConfirm(e.target.value)} />
        </Field>
        <button type="submit" className={`${btnPrimary} w-full`} disabled={busy || done || !current || !next}>
          <Lock className="h-4 w-4" aria-hidden="true" /> {busy ? 'Saving…' : 'Update password'}
        </button>
      </form>
    </AdminPage>
  );
}
