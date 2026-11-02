'use client';

import React, { useEffect, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { FileText, LogIn, PenLine, Upload } from 'lucide-react';
import {
  apiError, declineLetter, getLetterPdf, getMySignature, getMySignatureImage, isProbablySignedIn, openBlobInNewTab,
  signLetter,
  uploadMySignature,
} from '@/lib/api';
import type { MySignature, PendingSignature } from '@/lib/types';
import Field from '@/components/ui/Field';
import Modal from '@/components/ui/Modal';
import { EmptyBlock, ErrorBlock, LoadingBlock, Notice } from '@/components/ui/States';
import { btnDanger, btnGhost, btnPrimary, inputCls } from '@/components/ui/styles';
import { formatDate, formatDateTime } from '@/lib/format';
import { LETTER_KIND_LABELS } from '@/lib/labels';

const openPdf = (id: number) => openBlobInNewTab(() => getLetterPdf(id)).catch(() => undefined);

function SignatureOnFile({ mine, onChange }: { mine: MySignature; onChange: (m: MySignature) => void }) {
  const [preview, setPreview] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!mine.has_signature) return setPreview(null);
    let url = '';
    getMySignatureImage().then((blob) => setPreview((url = URL.createObjectURL(blob)))).catch(() => setPreview(null));
    return () => { if (url) URL.revokeObjectURL(url); };
  }, [mine.has_signature, mine.uploaded_at]);

  async function upload(file: File | undefined) {
    if (!file) return;
    setBusy(true);
    setError('');
    try {
      onChange(await uploadMySignature(file));
    } catch (err) {
      setError(apiError(err, 'Could not read that photo. Try a clearer one on plain white paper.'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mb-6 rounded-xl border border-amber-200 bg-white p-4 shadow-sm">
      <h2 className="font-semibold text-gray-900">Your signature on file</h2>
      <p className="mt-1 text-sm text-gray-600">
        It is placed on a letter only when you press <strong>Sign</strong> below - nobody else can apply it.
      </p>
      <div className="mt-3 flex flex-wrap items-center gap-4">
        <div className="flex h-20 w-56 items-center justify-center rounded-lg border border-dashed border-gray-300 bg-gray-50">
          {preview ? (
            // eslint-disable-next-line @next/next/no-img-element -- a private blob URL, not an optimisable asset
            <img src={preview} alt="Your signature" className="max-h-16 max-w-[13rem]" />
          ) : (
            <span className="text-xs text-gray-400">No signature yet</span>
          )}
        </div>
        <label className={`${btnGhost} cursor-pointer`}>
          <Upload className="h-4 w-4" aria-hidden="true" />
          {busy ? 'Cleaning up…' : mine.has_signature ? 'Replace' : 'Upload a photo'}
          <input type="file" accept="image/*" className="sr-only" disabled={busy}
            onChange={(e) => { upload(e.target.files?.[0]); e.target.value = ''; }} />
        </label>
      </div>
      <p className="mt-2 text-xs text-gray-500">
        Sign on plain white paper with a dark pen and take a clear, well-lit photo. The paper is removed automatically.
      </p>
      {error && <div className="mt-2"><Notice kind="error">{error}</Notice></div>}
    </section>
  );
}

function SignDialog({ item, onDone, onClose }: { item: PendingSignature; onDone: (msg: string) => void; onClose: () => void }) {
  const [password, setPassword] = useState('');
  const [agree, setAgree] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const verb = item.role === 'ATTESTOR' ? 'attest' : 'sign';

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      await signLetter(item.letter_id, password);
      onDone(`Signed "${item.subject}". The office will issue it once everyone has signed.`);
    } catch (err) {
      setError(apiError(err, 'Could not sign the letter.'));
      setBusy(false);
    }
  }

  return (
    <Modal title={`${verb === 'sign' ? 'Sign' : 'Attest'} this letter`} onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        <p className="text-sm text-gray-700"><strong>{item.subject}</strong></p>
        <button type="button" className={btnGhost} onClick={() => openPdf(item.letter_id)}>
          <FileText className="h-4 w-4" aria-hidden="true" /> Read the letter first
        </button>
        <label className="flex items-start gap-2 text-sm text-gray-700">
          <input type="checkbox" className="mt-1" checked={agree} onChange={(e) => setAgree(e.target.checked)} />
          <span>I have read this letter and agree to {verb} it. My signature will be placed on it.</span>
        </label>
        <Field label="Your password" hint="Confirms it is really you signing." required>
          <input type="password" className={inputCls} value={password} autoComplete="current-password"
            onChange={(e) => setPassword(e.target.value)} />
        </Field>
        {error && <Notice kind="error">{error}</Notice>}
        <div className="flex justify-end gap-2">
          <button type="button" className={btnGhost} onClick={onClose} disabled={busy}>Cancel</button>
          <button type="submit" className={btnPrimary} disabled={busy || !agree || !password}>
            <PenLine className="h-4 w-4" aria-hidden="true" /> {busy ? 'Signing…' : verb === 'sign' ? 'Sign' : 'Attest'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function DeclineDialog({ item, onDone, onClose }: { item: PendingSignature; onDone: (msg: string) => void; onClose: () => void }) {
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await declineLetter(item.letter_id, reason);
      onDone(`You declined "${item.subject}". The office has been shown your reason.`);
    } catch (err) {
      setError(apiError(err, 'Could not decline the letter.'));
      setBusy(false);
    }
  }

  return (
    <Modal title="Decline to sign" onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        <Field label="What needs to change?" required>
          <textarea className={inputCls} rows={3} minLength={3} maxLength={500} value={reason}
            onChange={(e) => setReason(e.target.value)} />
        </Field>
        {error && <Notice kind="error">{error}</Notice>}
        <div className="flex justify-end gap-2">
          <button type="button" className={btnGhost} onClick={onClose} disabled={busy}>Cancel</button>
          <button type="submit" className={btnDanger} disabled={busy || reason.trim().length < 3}>
            {busy ? 'Please wait…' : 'Decline'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default function SignLettersPage() {
  const [signedIn, setSignedIn] = useState<boolean | null>(null);
  const [mine, setMine] = useState<MySignature | null>(null);
  const [error, setError] = useState('');
  const [done, setDone] = useState('');
  const [signing, setSigning] = useState<PendingSignature | null>(null);
  const [declining, setDeclining] = useState<PendingSignature | null>(null);

  function load() {
    setError('');
    getMySignature()
      .then(setMine)
      .catch((err) => setError(apiError(err, 'Could not load your letters.')));
  }

  useEffect(() => setSignedIn(isProbablySignedIn()), []);
  useEffect(() => { if (signedIn) load(); }, [signedIn]);

  function finish(message: string) {
    setSigning(null);
    setDeclining(null);
    setDone(message);
    load();
  }

  return (
    <main className="mx-auto min-h-[60vh] max-w-3xl px-4 py-10">
      <div className="mb-6 text-center">
        <Image src="/logo.png" alt="" width={56} height={56} className="mx-auto mb-3" />
        <h1 className="font-serif text-2xl font-bold text-maroon">Letters to sign</h1>
        <p className="mt-1 text-sm text-gray-500">Official temple letters waiting for your signature</p>
      </div>

      {signedIn === null ? (
        <LoadingBlock />
      ) : !signedIn ? (
        <EmptyBlock
          title="Sign in to see letters waiting for you"
          icon={<LogIn className="h-10 w-10" aria-hidden="true" />}
          action={<Link href="/login?next=/sign-letters" className={btnGhost}>Sign in</Link>}
        />
      ) : error ? (
        <ErrorBlock message={error} onRetry={load} />
      ) : mine === null ? (
        <LoadingBlock />
      ) : mine.member_id === null ? (
        <EmptyBlock
          title="Your login isn't linked to a committee member"
          hint="Only committee members sign temple letters. Ask the temple office to link your account to your member record."
        />
      ) : (
        <>
          {done && <div className="mb-4"><Notice kind="success">{done}</Notice></div>}
          <SignatureOnFile mine={mine} onChange={setMine} />
          {mine.pending.length === 0 ? (
            <EmptyBlock title="Nothing to sign" hint="You'll get an email when a letter needs your signature." />
          ) : (
            <ul className="space-y-3">
              {mine.pending.map((p) => (
                <li key={p.letter_id} className="rounded-xl border border-amber-200 bg-white p-4 shadow-sm">
                  <p className="text-xs font-medium uppercase tracking-wide text-amber-700">
                    {LETTER_KIND_LABELS[p.kind]} · {p.role === 'ATTESTOR' ? 'to attest' : 'to sign'}
                  </p>
                  <p className="mt-1 font-semibold text-gray-900">{p.subject}</p>
                  <p className="mt-0.5 text-sm text-gray-600">
                    {p.recipient_name ? `To ${p.recipient_name} · ` : ''}Dated {formatDate(p.letter_date)}
                    {p.sent_at ? ` · sent ${formatDateTime(p.sent_at)}` : ''}{p.requested_by ? ` by ${p.requested_by}` : ''}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button type="button" className={btnGhost} onClick={() => openPdf(p.letter_id)}>
                      <FileText className="h-4 w-4" aria-hidden="true" /> Read
                    </button>
                    <button type="button" className={btnPrimary} disabled={!mine.has_signature} onClick={() => setSigning(p)}
                      title={mine.has_signature ? undefined : 'Upload your signature first'}>
                      <PenLine className="h-4 w-4" aria-hidden="true" /> {p.role === 'ATTESTOR' ? 'Attest' : 'Sign'}
                    </button>
                    <button type="button" className={btnDanger} onClick={() => setDeclining(p)}>Decline</button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </>
      )}

      {signing && <SignDialog item={signing} onDone={finish} onClose={() => setSigning(null)} />}
      {declining && <DeclineDialog item={declining} onDone={finish} onClose={() => setDeclining(null)} />}

      <p className="mt-6 text-center text-sm">
        <Link href="/" className="text-red-900 hover:underline">← Back to the temple website</Link>
      </p>
    </main>
  );
}
