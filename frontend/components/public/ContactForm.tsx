'use client';

import React, { useState } from 'react';
import { CheckCircle2, Send } from 'lucide-react';
import Field from '@/components/ui/Field';
import { Notice } from '@/components/ui/States';
import { btnPrimary, inputCls } from '@/components/ui/styles';
import { apiError, submitContact } from '@/lib/api';

export default function ContactForm() {
  const [form, setForm] = useState({ name: '', email: '', subject: '', message: '', website: '' });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [sent, setSent] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      await submitContact({ ...form, name: form.name.trim(), subject: form.subject.trim(), message: form.message.trim() });
      setSent(true);
    } catch (err) {
      setError(apiError(err, 'Your message could not be sent. Please try again.'));
    } finally {
      setBusy(false);
    }
  }

  if (sent) {
    return (
      <div role="status" className="rounded-2xl border border-green-200 bg-green-50 p-8 text-center">
        <CheckCircle2 className="mx-auto mb-3 h-12 w-12 text-green-600" aria-hidden="true" />
        <h3 className="font-serif text-xl font-bold text-green-900">Thank you</h3>
        <p className="mt-1 text-sm text-green-800">Your message has been received. The temple office will get back to you.</p>
      </div>
    );
  }

  const set = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setForm({ ...form, [key]: e.target.value });

  return (
    <form onSubmit={submit} className="space-y-4 rounded-2xl border border-amber-200 bg-white p-6 shadow-sm sm:p-8">
      {error && <Notice kind="error">{error}</Notice>}
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Your name" required><input className={inputCls} maxLength={100} autoComplete="name" value={form.name} onChange={set('name')} /></Field>
        <Field label="Email" required><input className={inputCls} type="email" autoComplete="email" value={form.email} onChange={set('email')} /></Field>
      </div>
      <Field label="Subject" required><input className={inputCls} maxLength={200} value={form.subject} onChange={set('subject')} /></Field>
      <Field label="Message" required><textarea className={inputCls} rows={5} maxLength={5000} value={form.message} onChange={set('message')} /></Field>
      {/* honeypot: hidden from people and assistive tech, bots fill it */}
      <div className="absolute -left-[9999px] h-0 w-0 overflow-hidden" aria-hidden="true">
        <label>Website<input tabIndex={-1} autoComplete="off" value={form.website} onChange={set('website')} /></label>
      </div>
      <button type="submit" className={`${btnPrimary} w-full sm:w-auto`} disabled={busy || form.name.trim().length < 2 || !form.email || form.subject.trim().length < 3 || form.message.trim().length < 5}>
        <Send className="h-4 w-4" aria-hidden="true" /> {busy ? 'Sending…' : 'Send message'}
      </button>
    </form>
  );
}
