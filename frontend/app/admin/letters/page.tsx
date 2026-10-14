'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  BadgeCheck, Copy, FileSignature, FileText, PenLine, Plus, Send, ShieldOff, Stamp, Trash2, Undo2, Upload, X,
} from 'lucide-react';
import {
  apiError, createLetter, deleteLetter, getLetterPdf, getLetterTemplates, getMySignature, getSeal, getSealImage,
  getSignatureImage, letterAction, listLetters, listSignatures, markSignatoryInk, openBlobInNewTab, removeSeal,
  removeSignature, revokeLetter, updateLetter, uploadSeal, uploadSignature,
} from '@/lib/api';
import type {
  Letter, LetterInput, LetterKind, LetterStatus, LetterTemplate, Paged, SealStatus, SignatoryRole, SignatureStatus,
} from '@/lib/types';
import { useAuth } from '@/components/admin/AuthContext';
import AdminPage from '@/components/admin/AdminPage';
import ConfirmDialog from '@/components/admin/ConfirmDialog';
import Field from '@/components/ui/Field';
import Modal from '@/components/ui/Modal';
import Pager from '@/components/ui/Pager';
import { EmptyBlock, ErrorBlock, LoadingBlock, Notice } from '@/components/ui/States';
import { btnDanger, btnGhost, btnPrimary, cardCls, inputCls } from '@/components/ui/styles';
import { formatDate, formatDateTime, todayISO } from '@/lib/format';
import { CERTIFICATE_KINDS, LETTER_KINDS, LETTER_KIND_LABELS, LETTER_STATUS, SIGNATORY_STATUS } from '@/lib/labels';

const PAGE_SIZE = 25;
const PLACEHOLDER = /\[[^[\]\n]{1,60}\]/g;

const openPdf = (id: number) => openBlobInNewTab(() => getLetterPdf(id));

function StatusBadge({ status }: { status: LetterStatus }) {
  const s = LETTER_STATUS[status];
  return <span className={`inline-flex whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ${s.cls}`}>{s.label}</span>;
}

/** A private image (signature / seal) fetched with the session and shown from a blob URL. */
function PrivateImage({ load, alt, version, className }: { load: () => Promise<Blob>; alt: string; version: string; className?: string }) {
  const [src, setSrc] = useState<string | null>(null);
  useEffect(() => {
    let url = '';
    let live = true;
    load().then((blob) => { if (live) setSrc((url = URL.createObjectURL(blob))); }).catch(() => setSrc(null));
    return () => { live = false; if (url) URL.revokeObjectURL(url); };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reload only when the image changes
  }, [version]);
  // eslint-disable-next-line @next/next/no-img-element -- a private blob URL, not an optimisable asset
  return src ? <img src={src} alt={alt} className={className} /> : <span className="text-xs text-gray-400">…</span>;
}

// --------------------------------------------------------------------------------- editor
interface DraftSignatory { member_id: number; role: SignatoryRole; designation: string }

function toForm(letter: Letter | null, template: LetterTemplate | undefined): LetterInput & { signatoriesDraft: DraftSignatory[] } {
  if (letter) {
    return {
      kind: letter.kind, letter_date: letter.letter_date, subject: letter.subject, recipient_name: letter.recipient_name ?? '',
      recipient_address: letter.recipient_address ?? '', salutation: letter.salutation ?? '', body: letter.body,
      closing: letter.closing ?? '', include_seal: letter.include_seal, signatories: [],
      signatoriesDraft: letter.signatories.filter((s) => s.member_id !== null)
        .map((s) => ({ member_id: s.member_id as number, role: s.role, designation: s.designation ?? '' })),
    };
  }
  return {
    kind: template?.kind ?? 'GENERAL', letter_date: todayISO(), subject: template?.subject ?? '', recipient_name: '',
    recipient_address: '', salutation: template?.salutation ?? '', body: template?.body ?? '', closing: template?.closing ?? '',
    include_seal: true, signatories: [], signatoriesDraft: [],
  };
}

function LetterEditor({
  letter, templates, members, onSaved, onClose,
}: {
  letter: Letter | null; templates: LetterTemplate[]; members: SignatureStatus[];
  onSaved: (l: Letter) => void; onClose: () => void;
}) {
  const byKind = useMemo(() => new Map(templates.map((t) => [t.kind, t])), [templates]);
  const [form, setForm] = useState(() => toForm(letter, byKind.get('GENERAL')));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const active = members.filter((m) => m.is_active);
  const certificate = CERTIFICATE_KINDS.has(form.kind);
  const set = <K extends keyof typeof form>(key: K, value: (typeof form)[K]) => setForm((f) => ({ ...f, [key]: value }));
  const left = Array.from(new Set(
    [form.subject, form.recipient_name, form.recipient_address, form.salutation, form.body, form.closing]
      .flatMap((v) => (v ?? '').match(PLACEHOLDER) ?? []),
  ));

  function changeKind(kind: LetterKind) {
    const t = byKind.get(kind);
    const current = byKind.get(form.kind);
    const untouched = !form.body.trim() || form.body === current?.body;
    // A fresh template replaces the text only while it hasn't been edited.
    setForm((f) => ({
      ...f, kind,
      ...(t && untouched ? { subject: t.subject, salutation: t.salutation, body: t.body, closing: t.closing } : {}),
    }));
  }

  function setSignatory(i: number, patch: Partial<DraftSignatory>) {
    setForm((f) => ({ ...f, signatoriesDraft: f.signatoriesDraft.map((s, j) => (j === i ? { ...s, ...patch } : s)) }));
  }

  function addSignatory() {
    const used = new Set(form.signatoriesDraft.map((s) => s.member_id));
    const next = active.find((m) => !used.has(m.member_id));
    if (next) setForm((f) => ({ ...f, signatoriesDraft: [...f.signatoriesDraft, { member_id: next.member_id, role: 'SIGNATORY', designation: '' }] }));
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError('');
    const { signatoriesDraft, ...rest } = form;
    const data: LetterInput = {
      ...rest,
      recipient_address: certificate ? null : rest.recipient_address,
      salutation: certificate ? null : rest.salutation,
      signatories: signatoriesDraft.map((s) => ({ member_id: s.member_id, role: s.role, designation: s.designation || null })),
    };
    try {
      onSaved(letter ? await updateLetter(letter.id, data) : await createLetter(data));
    } catch (err) {
      setError(apiError(err, 'Could not save the letter.'));
      setBusy(false);
    }
  }

  return (
    <Modal title={letter ? 'Edit draft letter' : 'New letter'} onClose={onClose} wide>
      <form onSubmit={save} className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Type of letter" required>
            <select className={inputCls} value={form.kind} onChange={(e) => changeKind(e.target.value as LetterKind)}>
              {LETTER_KINDS.map((k) => <option key={k} value={k}>{LETTER_KIND_LABELS[k]}</option>)}
            </select>
          </Field>
          <Field label="Letter date" required>
            <input type="date" className={inputCls} value={form.letter_date} onChange={(e) => set('letter_date', e.target.value)} />
          </Field>
        </div>
        <Field label={certificate ? 'Issued to (name)' : 'To (name)'} hint="Shown on the public verification page.">
          <input className={inputCls} maxLength={200} value={form.recipient_name ?? ''} onChange={(e) => set('recipient_name', e.target.value)} />
        </Field>
        {!certificate && (
          <Field label="Address">
            <textarea className={inputCls} rows={2} maxLength={600} value={form.recipient_address ?? ''}
              onChange={(e) => set('recipient_address', e.target.value)} />
          </Field>
        )}
        <Field label="Subject" required hint={certificate ? 'Not printed on certificates - used for the list and verification page.' : undefined}>
          <input className={inputCls} minLength={2} maxLength={200} value={form.subject} onChange={(e) => set('subject', e.target.value)} />
        </Field>
        {!certificate && (
          <Field label="Salutation">
            <input className={inputCls} maxLength={100} value={form.salutation ?? ''} onChange={(e) => set('salutation', e.target.value)} />
          </Field>
        )}
        <Field label="Letter text" required hint="A blank line starts a new paragraph. Replace every [placeholder] before sending.">
          <textarea className={`${inputCls} font-serif leading-relaxed`} rows={12} minLength={10} maxLength={8000}
            value={form.body} onChange={(e) => set('body', e.target.value)} />
        </Field>
        {left.length > 0 && (
          <Notice kind="info">Still to fill in: {left.slice(0, 8).join(', ')}{left.length > 8 ? '…' : ''}</Notice>
        )}
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Closing">
            <input className={inputCls} maxLength={100} value={form.closing ?? ''} placeholder="Yours sincerely,"
              onChange={(e) => set('closing', e.target.value)} />
          </Field>
          <label className="flex items-center gap-2 self-end pb-2 text-sm text-gray-700">
            <input type="checkbox" checked={form.include_seal} onChange={(e) => set('include_seal', e.target.checked)} />
            Put the temple seal on the issued letter
          </label>
        </div>

        <fieldset className="rounded-lg border border-gray-200 p-3">
          <legend className="px-1 text-sm font-medium text-gray-700">Signatories</legend>
          {form.signatoriesDraft.length === 0 && <p className="text-sm text-gray-500">Add who signs (and who attests) this letter.</p>}
          <ul className="space-y-2">
            {form.signatoriesDraft.map((s, i) => {
              const m = members.find((x) => x.member_id === s.member_id);
              return (
                <li key={i} className="grid gap-2 sm:grid-cols-[1.4fr_0.9fr_1fr_auto] sm:items-center">
                  <select aria-label="Member" className={inputCls} value={s.member_id}
                    onChange={(e) => setSignatory(i, { member_id: Number(e.target.value) })}>
                    {active.map((x) => (
                      <option key={x.member_id} value={x.member_id}
                        disabled={x.member_id !== s.member_id && form.signatoriesDraft.some((o) => o.member_id === x.member_id)}>
                        {x.name}{x.position ? ` (${x.position})` : ''}
                      </option>
                    ))}
                  </select>
                  <select aria-label="Role" className={inputCls} value={s.role} onChange={(e) => setSignatory(i, { role: e.target.value as SignatoryRole })}>
                    <option value="SIGNATORY">Signs</option>
                    <option value="ATTESTOR">Attests</option>
                  </select>
                  <input aria-label="Designation" className={inputCls} maxLength={100} placeholder={m?.position ?? 'Designation'}
                    value={s.designation} onChange={(e) => setSignatory(i, { designation: e.target.value })} />
                  <button type="button" className={btnGhost} aria-label={`Remove ${m?.name ?? 'signatory'}`}
                    onClick={() => setForm((f) => ({ ...f, signatoriesDraft: f.signatoriesDraft.filter((_, j) => j !== i) }))}>
                    <X className="h-4 w-4" aria-hidden="true" />
                  </button>
                  {m && (!m.has_login || !m.has_signature) && (
                    <p className="text-xs text-gray-500 sm:col-span-4">
                      {!m.has_login ? 'No login - will sign the printed letter in ink.' : 'No signature on file yet - they can upload one when signing.'}
                    </p>
                  )}
                </li>
              );
            })}
          </ul>
          {form.signatoriesDraft.length < 6 && active.length > form.signatoriesDraft.length && (
            <button type="button" className={`${btnGhost} mt-3`} onClick={addSignatory}>
              <Plus className="h-4 w-4" aria-hidden="true" /> Add signatory
            </button>
          )}
        </fieldset>

        <p className="text-xs text-gray-500">Letters print in English. Use “Rs.” for amounts.</p>
        {error && <Notice kind="error">{error}</Notice>}
        <div className="flex justify-end gap-2">
          <button type="button" className={btnGhost} onClick={onClose} disabled={busy}>Cancel</button>
          <button type="submit" className={btnPrimary} disabled={busy}>{busy ? 'Saving…' : 'Save draft'}</button>
        </div>
      </form>
    </Modal>
  );
}

// --------------------------------------------------------------------------------- detail
function LetterDetail({
  letter, canWrite, onChange, onEdit, onClose,
}: {
  letter: Letter; canWrite: boolean; onChange: (l: Letter | null, message?: string) => void; onEdit: () => void; onClose: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [confirm, setConfirm] = useState<null | 'send' | 'recall' | 'issue' | 'delete'>(null);
  const [revoking, setRevoking] = useState(false);
  const [reason, setReason] = useState('');
  const [copied, setCopied] = useState(false);
  const allDone = letter.signatories.every((s) => s.status === 'SIGNED' || s.status === 'PAPER');

  async function run(fn: () => Promise<Letter | null>, message: string) {
    setBusy(true);
    setError('');
    try {
      onChange(await fn(), message);
    } catch (err) {
      setError(apiError(err));
    } finally {
      setBusy(false);
      setConfirm(null);
    }
  }

  const confirmText = {
    send: ['Send for signatures?', 'Each signatory is emailed and can sign from their own login. The letter can no longer be edited unless you recall it.', 'Send'],
    recall: ['Recall to draft?', 'Every signature collected so far is cleared and signatories will have to sign again.', 'Recall'],
    issue: ['Issue this letter?', 'It gets its reference number, the temple seal and a verification QR code. Issued letters cannot be edited - only revoked.', 'Issue'],
    delete: ['Delete this draft?', 'The draft is removed permanently.', 'Delete'],
  } as const;

  return (
    <Modal title={letter.reference_number ?? 'Draft letter'} onClose={onClose} wide>
      <div className="space-y-4 text-sm">
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge status={letter.status} />
          <span className="text-gray-500">{LETTER_KIND_LABELS[letter.kind]} · dated {formatDate(letter.letter_date)}</span>
        </div>
        <div>
          <p className="font-semibold text-gray-900">{letter.subject}</p>
          {letter.recipient_name && <p className="text-gray-600">To {letter.recipient_name}</p>}
          <p className="mt-1 text-xs text-gray-400">
            Drafted by {letter.created_by_name ?? 'unknown'} on {formatDateTime(letter.created_at)}
            {letter.issued_at ? ` · issued ${formatDateTime(letter.issued_at)}` : ''}
          </p>
        </div>
        {letter.status === 'REVOKED' && (
          <Notice kind="error">Revoked {formatDateTime(letter.revoked_at)}: {letter.revoke_reason}</Notice>
        )}

        <div className="rounded-lg border border-gray-200">
          <p className="border-b border-gray-100 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Signatures</p>
          <ul className="divide-y divide-gray-100">
            {letter.signatories.map((s) => {
              const st = SIGNATORY_STATUS[s.status];
              return (
                <li key={s.id} className="flex flex-wrap items-center justify-between gap-2 px-3 py-2">
                  <div>
                    <p className="font-medium text-gray-900">
                      {s.name} {s.role === 'ATTESTOR' && <span className="text-xs font-normal text-gray-500">(attests)</span>}
                    </p>
                    <p className="text-xs text-gray-500">
                      {s.designation ?? '-'}
                      {!s.has_login && ' · no login'}
                      {s.has_login && !s.has_signature && s.status === 'PENDING' && ' · no signature on file yet'}
                    </p>
                    {s.decline_reason && <p className="text-xs text-red-700">“{s.decline_reason}”</p>}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-medium ${st.cls}`}>
                      {st.label}{s.signed_at ? ` · ${formatDateTime(s.signed_at)}` : ''}
                    </span>
                    {canWrite && letter.status === 'AWAITING_SIGNATURES' && (s.status === 'PENDING' || s.status === 'DECLINED') && (
                      <button type="button" className="text-xs font-medium text-red-900 hover:underline" disabled={busy}
                        onClick={() => run(() => markSignatoryInk(letter.id, s.id), `${s.name} will sign the printed letter in ink.`)}>
                        Signs in ink instead
                      </button>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        </div>

        {letter.verify_url && (
          <div className="flex flex-wrap items-center gap-2 rounded-lg bg-green-50 p-3">
            <BadgeCheck className="h-4 w-4 text-green-700" aria-hidden="true" />
            <a href={letter.verify_url} target="_blank" rel="noreferrer" className="break-all text-green-800 underline">{letter.verify_url}</a>
            <button type="button" className="ml-auto text-xs font-medium text-green-800 hover:underline"
              onClick={() => navigator.clipboard.writeText(letter.verify_url ?? '').then(() => setCopied(true))}>
              <Copy className="mr-1 inline h-3.5 w-3.5" aria-hidden="true" />{copied ? 'Copied' : 'Copy link'}
            </button>
          </div>
        )}

        {error && <Notice kind="error">{error}</Notice>}

        <div className="flex flex-wrap gap-2 border-t border-gray-100 pt-4">
          <button type="button" className={btnGhost} onClick={() => openPdf(letter.id).catch((err) => setError(apiError(err)))}>
            <FileText className="h-4 w-4" aria-hidden="true" /> {letter.status === 'ISSUED' || letter.status === 'REVOKED' ? 'Open PDF' : 'Preview PDF'}
          </button>
          {canWrite && letter.status === 'DRAFT' && (
            <>
              <button type="button" className={btnGhost} onClick={onEdit}><PenLine className="h-4 w-4" aria-hidden="true" /> Edit</button>
              <button type="button" className={btnPrimary} onClick={() => setConfirm('send')} disabled={busy}>
                <Send className="h-4 w-4" aria-hidden="true" /> Send for signatures
              </button>
              <button type="button" className={btnDanger} onClick={() => setConfirm('delete')} disabled={busy}>
                <Trash2 className="h-4 w-4" aria-hidden="true" /> Delete
              </button>
            </>
          )}
          {canWrite && letter.status === 'AWAITING_SIGNATURES' && (
            <>
              <button type="button" className={btnPrimary} onClick={() => setConfirm('issue')} disabled={busy || !allDone}
                title={allDone ? undefined : 'Waiting for every signatory'}>
                <Stamp className="h-4 w-4" aria-hidden="true" /> Issue letter
              </button>
              <button type="button" className={btnGhost} onClick={() => setConfirm('recall')} disabled={busy}>
                <Undo2 className="h-4 w-4" aria-hidden="true" /> Recall to draft
              </button>
            </>
          )}
          {canWrite && letter.status === 'ISSUED' && (
            <button type="button" className={btnDanger} onClick={() => setRevoking(true)} disabled={busy}>
              <ShieldOff className="h-4 w-4" aria-hidden="true" /> Revoke
            </button>
          )}
        </div>
      </div>

      {confirm && (
        <ConfirmDialog
          title={confirmText[confirm][0]} message={confirmText[confirm][1]} confirmLabel={confirmText[confirm][2]}
          danger={confirm === 'delete' || confirm === 'recall'} busy={busy} onCancel={() => setConfirm(null)}
          onConfirm={() => {
            if (confirm === 'delete') run(async () => { await deleteLetter(letter.id); return null; }, 'Draft deleted.');
            else run(() => letterAction(letter.id, confirm), {
              send: 'Sent for signatures - signatories have been emailed.',
              recall: 'Recalled to draft.',
              issue: 'Letter issued.',
            }[confirm]);
          }}
        />
      )}
      {revoking && (
        <Modal title="Revoke this letter" onClose={() => setRevoking(false)}>
          <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); setRevoking(false); run(() => revokeLetter(letter.id, reason), 'Letter revoked.'); }}>
            <p className="text-sm text-gray-600">Anyone who scans its QR code will see that it was revoked, and why.</p>
            <Field label="Reason" required>
              <textarea className={inputCls} rows={3} minLength={3} maxLength={500} value={reason} onChange={(e) => setReason(e.target.value)} />
            </Field>
            <div className="flex justify-end gap-2">
              <button type="button" className={btnGhost} onClick={() => setRevoking(false)}>Cancel</button>
              <button type="submit" className={btnDanger} disabled={reason.trim().length < 3}>Revoke</button>
            </div>
          </form>
        </Modal>
      )}
    </Modal>
  );
}

// ----------------------------------------------------------------------- signatures & seal
function UploadButton({ label, onFile, busy }: { label: string; onFile: (f: File) => void; busy?: boolean }) {
  return (
    <label className={`${btnGhost} cursor-pointer`}>
      <Upload className="h-4 w-4" aria-hidden="true" /> {busy ? 'Cleaning up…' : label}
      <input type="file" accept="image/*" className="sr-only" disabled={busy}
        onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ''; if (f) onFile(f); }} />
    </label>
  );
}

function SignaturesPanel({ members, onMembers }: { members: SignatureStatus[]; onMembers: () => void }) {
  const [seal, setSeal] = useState<SealStatus | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [removing, setRemoving] = useState<SignatureStatus | 'seal' | null>(null);

  useEffect(() => { getSeal().then(setSeal).catch((err) => setError(apiError(err))); }, []);

  async function act(key: string, fn: () => Promise<unknown>) {
    setBusy(key);
    setError('');
    try {
      await fn();
    } catch (err) {
      setError(apiError(err, 'Could not read that photo. Try a clearer one on plain white paper.'));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-6">
      <Notice kind="info">
        A stored signature is placed on a letter only when that member signs it from their own login (with their password).
        Members are emailed when their signature is uploaded. Photograph signatures and the seal on plain white paper -
        the background is removed automatically.
      </Notice>
      {error && <Notice kind="error">{error}</Notice>}

      <section className={`${cardCls} p-4`}>
        <h2 className="font-semibold text-gray-900">Temple seal</h2>
        <p className="text-sm text-gray-500">Stamp the rubber seal on white paper and upload a photo or scan.</p>
        <div className="mt-3 flex flex-wrap items-center gap-4">
          <div className="flex h-28 w-28 items-center justify-center rounded-lg border border-dashed border-gray-300 bg-gray-50">
            {seal?.has_seal ? <PrivateImage load={getSealImage} alt="Temple seal" version={seal.uploaded_at ?? ''} className="max-h-24 max-w-24" />
              : <span className="text-xs text-gray-400">No seal</span>}
          </div>
          <UploadButton label={seal?.has_seal ? 'Replace' : 'Upload seal'} busy={busy === 'seal'}
            onFile={(f) => act('seal', async () => setSeal(await uploadSeal(f)))} />
          {seal?.has_seal && <button type="button" className={btnDanger} onClick={() => setRemoving('seal')}>Remove</button>}
        </div>
        {seal?.uploaded_at && <p className="mt-2 text-xs text-gray-400">Uploaded {formatDateTime(seal.uploaded_at)}</p>}
      </section>

      <section className={cardCls}>
        <h2 className="border-b border-gray-100 px-4 py-3 font-semibold text-gray-900">Member signatures</h2>
        {members.length === 0 ? (
          <p className="p-4 text-sm text-gray-500">Add committee members on the <Link href="/admin/members" className="underline">Members</Link> page first.</p>
        ) : (
          <ul className="divide-y divide-gray-100">
            {members.map((m) => (
              <li key={m.member_id} className="flex flex-wrap items-center gap-3 px-4 py-3">
                <div className="min-w-[10rem] flex-1">
                  <p className="font-medium text-gray-900">{m.name}{!m.is_active && <span className="ml-1 text-xs text-gray-400">(inactive)</span>}</p>
                  <p className="text-xs text-gray-500">
                    {m.position ?? '-'} · {m.has_login ? 'has a login - signs online' : 'no login - signs printed letters in ink'}
                  </p>
                </div>
                <div className="flex h-14 w-44 items-center justify-center rounded border border-dashed border-gray-200 bg-gray-50">
                  {m.has_signature ? (
                    <PrivateImage load={() => getSignatureImage(m.member_id)} alt={`Signature of ${m.name}`}
                      version={m.uploaded_at ?? ''} className="max-h-12 max-w-[10.5rem]" />
                  ) : <span className="text-xs text-gray-400">No signature</span>}
                </div>
                <div className="flex gap-2">
                  <UploadButton label={m.has_signature ? 'Replace' : 'Upload'} busy={busy === `m${m.member_id}`}
                    onFile={(f) => act(`m${m.member_id}`, async () => { await uploadSignature(m.member_id, f); onMembers(); })} />
                  {m.has_signature && <button type="button" className={btnDanger} onClick={() => setRemoving(m)}>Remove</button>}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {removing && (
        <ConfirmDialog
          title={removing === 'seal' ? 'Remove the seal?' : `Remove ${removing.name}'s signature?`}
          message="Letters already signed keep the image they were signed with. New letters can't use it until another is uploaded."
          confirmLabel="Remove" danger busy={busy === 'remove'} onCancel={() => setRemoving(null)}
          onConfirm={() => act('remove', async () => {
            if (removing === 'seal') { await removeSeal(); setSeal({ has_seal: false, uploaded_at: null }); }
            else { await removeSignature(removing.member_id); onMembers(); }
            setRemoving(null);
          })}
        />
      )}
    </div>
  );
}

// ----------------------------------------------------------------------------------- page
export default function LettersPage() {
  const { can } = useAuth();
  const canWrite = can('letters:write');
  const [tab, setTab] = useState<'letters' | 'signatures'>('letters');
  const [status, setStatus] = useState<LetterStatus | ''>('');
  const [q, setQ] = useState('');
  const [page, setPage] = useState(1);
  const [letters, setLetters] = useState<Paged<Letter> | null>(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [templates, setTemplates] = useState<LetterTemplate[]>([]);
  const [members, setMembers] = useState<SignatureStatus[]>([]);
  const [pendingMine, setPendingMine] = useState(0);
  const [open, setOpen] = useState<Letter | null>(null);
  const [editing, setEditing] = useState<Letter | 'new' | null>(null);

  const load = useCallback(() => {
    setError('');
    listLetters(page, { status: status || undefined, q: q.trim() || undefined }, PAGE_SIZE)
      .then(setLetters)
      .catch((err) => setError(apiError(err, 'Could not load letters.')));
  }, [page, status, q]);

  const loadMembers = useCallback(() => { if (canWrite) listSignatures().then(setMembers).catch(() => undefined); }, [canWrite]);

  useEffect(() => {
    const t = setTimeout(load, q ? 300 : 0);
    return () => clearTimeout(t);
  }, [load, q]);
  useEffect(() => {
    loadMembers();
    if (canWrite) getLetterTemplates().then(setTemplates).catch(() => undefined);
    getMySignature().then((m) => setPendingMine(m.pending.length)).catch(() => undefined);
  }, [canWrite, loadMembers]);

  function changed(letter: Letter | null, msg?: string) {
    setOpen(letter);
    if (msg) setMessage(msg);
    load();
  }

  return (
    <AdminPage
      title="Official Letters"
      description="Letters and certificates on the temple letterhead - signed by members themselves, sealed, and verifiable by QR code."
      actions={canWrite && tab === 'letters' && (
        <button type="button" className={btnPrimary} onClick={() => setEditing('new')} disabled={!templates.length}>
          <Plus className="h-4 w-4" aria-hidden="true" /> New letter
        </button>
      )}
    >
      {pendingMine > 0 && (
        <div className="mb-4">
          <Notice kind="info">
            {pendingMine === 1 ? 'A letter is' : `${pendingMine} letters are`} waiting for your signature.{' '}
            <Link href="/sign-letters" className="font-semibold underline">Review and sign</Link>
          </Notice>
        </div>
      )}
      {canWrite && (
        <div className="mb-4 flex gap-1 border-b border-gray-200" role="tablist">
          {([['letters', 'Letters', FileSignature], ['signatures', 'Signatures & seal', PenLine]] as const).map(([key, label, Icon]) => (
            <button key={key} type="button" role="tab" aria-selected={tab === key} onClick={() => setTab(key)}
              className={`-mb-px inline-flex items-center gap-1.5 border-b-2 px-3 py-2 text-sm font-medium ${
                tab === key ? 'border-red-900 text-red-900' : 'border-transparent text-gray-500 hover:text-gray-800'}`}>
              <Icon className="h-4 w-4" aria-hidden="true" /> {label}
            </button>
          ))}
        </div>
      )}
      {message && <div className="mb-4"><Notice kind="success">{message}</Notice></div>}

      {tab === 'signatures' && canWrite ? (
        <SignaturesPanel members={members} onMembers={loadMembers} />
      ) : (
        <>
          <div className="mb-4 flex flex-wrap gap-2">
            <select aria-label="Status" className={`${inputCls} w-auto`} value={status}
              onChange={(e) => { setStatus(e.target.value as LetterStatus | ''); setPage(1); }}>
              <option value="">All letters</option>
              {(Object.keys(LETTER_STATUS) as LetterStatus[]).map((s) => <option key={s} value={s}>{LETTER_STATUS[s].label}</option>)}
            </select>
            <input type="search" aria-label="Search" placeholder="Search subject, name or reference" className={`${inputCls} max-w-xs`}
              value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} />
          </div>
          {error ? (
            <ErrorBlock message={error} onRetry={load} />
          ) : letters === null ? (
            <LoadingBlock />
          ) : letters.items.length === 0 ? (
            <EmptyBlock title={status || q ? 'No letters match' : 'No letters yet'}
              hint={canWrite && !status && !q ? 'Start with “New letter” - pick a type and a ready template fills in.' : undefined} />
          ) : (
            <div className={`${cardCls} overflow-x-auto`}>
              <table className="w-full text-left text-sm">
                <thead className="border-b border-gray-100 text-xs uppercase text-gray-500">
                  <tr>
                    <th scope="col" className="px-4 py-2">Letter</th>
                    <th scope="col" className="px-4 py-2">Date</th>
                    <th scope="col" className="px-4 py-2">Signed</th>
                    <th scope="col" className="px-4 py-2">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {letters.items.map((l) => {
                    const done = l.signatories.filter((s) => s.status === 'SIGNED' || s.status === 'PAPER').length;
                    return (
                      <tr key={l.id} className="cursor-pointer hover:bg-amber-50/50" onClick={() => setOpen(l)}>
                        <td className="px-4 py-3">
                          <button type="button" className="text-left font-medium text-gray-900 hover:underline" onClick={(e) => { e.stopPropagation(); setOpen(l); }}>
                            {l.subject}
                          </button>
                          <p className="text-xs text-gray-500">
                            {l.reference_number ? <span className="font-mono">{l.reference_number}</span> : LETTER_KIND_LABELS[l.kind]}
                            {l.recipient_name ? ` · ${l.recipient_name}` : ''}
                          </p>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-gray-600">{formatDate(l.letter_date)}</td>
                        <td className="px-4 py-3 tabular-nums text-gray-600">{done}/{l.signatories.length}</td>
                        <td className="px-4 py-3"><StatusBadge status={l.status} /></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <div className="px-4 pb-3">
                <Pager page={page} pageSize={PAGE_SIZE} total={letters.total} onPage={setPage} />
              </div>
            </div>
          )}
        </>
      )}

      {open && (
        <LetterDetail letter={open} canWrite={canWrite} onChange={changed} onClose={() => setOpen(null)}
          onEdit={() => { setEditing(open); setOpen(null); }} />
      )}
      {editing && (
        <LetterEditor
          letter={editing === 'new' ? null : editing} templates={templates} members={members}
          onClose={() => setEditing(null)}
          onSaved={(l) => { setEditing(null); setMessage('Draft saved.'); setOpen(l); load(); }}
        />
      )}
    </AdminPage>
  );
}
