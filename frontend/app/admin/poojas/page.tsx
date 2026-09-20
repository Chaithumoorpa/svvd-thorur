'use client';

import React, { useState } from 'react';
import { Pencil, Plus, Sparkles, Trash2 } from 'lucide-react';
import AdminPage, { StatusPill } from '@/components/admin/AdminPage';
import ConfirmDialog from '@/components/admin/ConfirmDialog';
import Field from '@/components/ui/Field';
import Modal from '@/components/ui/Modal';
import { EmptyBlock, ErrorBlock, LoadingBlock, Notice } from '@/components/ui/States';
import { btnDanger, btnGhost, btnPrimary, cardCls, inputCls } from '@/components/ui/styles';
import { useAction } from '@/hooks/useAction';
import { useLoad } from '@/hooks/useLoad';
import { createPooja, deletePooja, listAllPoojas, updatePooja } from '@/lib/api';
import { emptyToNull, formatMoney, formatTimeRange } from '@/lib/format';
import type { Pooja } from '@/lib/types';

const TYPES = [
  { value: 'daily', label: 'Daily pooja' },
  { value: 'weekly', label: 'Weekly pooja' },
  { value: 'monthly', label: 'Monthly pooja' },
  { value: 'festival', label: 'Festival seva' },
  { value: 'special', label: 'Special seva' },
];

interface FormState {
  name: string;
  description: string;
  pooja_type: string;
  start_time: string;
  end_time: string;
  is_paid: boolean;
  suggested_amount: string;
  sort_order: string;
  is_active: boolean;
}
const blank: FormState = {
  name: '', description: '', pooja_type: 'daily', start_time: '', end_time: '', is_paid: false,
  suggested_amount: '', sort_order: '0', is_active: true,
};

const hhmm = (t: string | null) => (t ? t.slice(0, 5) : '');
const toTime = (t: string) => (t ? (t.length === 5 ? `${t}:00` : t) : null);

export default function PoojasAdmin() {
  const list = useLoad(() => listAllPoojas(1, 200), []);
  const action = useAction();
  const [editing, setEditing] = useState<{ id: number | null; form: FormState } | null>(null);
  const [toDelete, setToDelete] = useState<Pooja | null>(null);

  const openEdit = (p: Pooja) =>
    setEditing({
      id: p.id,
      form: {
        name: p.name, description: p.description ?? '', pooja_type: p.pooja_type,
        start_time: hhmm(p.start_time), end_time: hhmm(p.end_time), is_paid: p.is_paid,
        suggested_amount: p.suggested_amount?.toString() ?? '', sort_order: String(p.sort_order),
        is_active: p.is_active,
      },
    });

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!editing) return;
    const { id, form } = editing;
    const amount = form.suggested_amount.trim();
    if (form.is_paid && (amount === '' || Number(amount) < 0)) {
      action.setError('A paid seva needs an amount.');
      return;
    }
    const payload = {
      name: form.name.trim(),
      description: emptyToNull(form.description),
      pooja_type: form.pooja_type,
      start_time: toTime(form.start_time),
      end_time: toTime(form.end_time),
      is_paid: form.is_paid,
      suggested_amount: amount === '' ? null : Number(amount),
      sort_order: Number(form.sort_order) || 0,
      is_active: form.is_active,
    };
    const ok = await action.run(
      () => (id === null ? createPooja(payload) : updatePooja(id, payload)),
      id === null ? 'Pooja added.' : 'Pooja updated.',
    );
    if (ok) {
      setEditing(null);
      list.reload();
    }
  }

  async function remove() {
    if (!toDelete) return;
    const ok = await action.run(() => deletePooja(toDelete.id), 'Pooja hidden from the website.');
    if (ok) {
      setToDelete(null);
      list.reload();
    }
  }

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setEditing((cur) => (cur ? { ...cur, form: { ...cur.form, [key]: value } } : cur));

  return (
    <AdminPage
      title="Poojas & Sevas"
      description="Daily rituals and sevas devotees can see (and, for free ones, book) on the website."
      actions={
        <button type="button" className={btnPrimary} onClick={() => setEditing({ id: null, form: { ...blank } })}>
          <Plus className="h-4 w-4" aria-hidden="true" /> Add pooja
        </button>
      }
    >
      {action.success && <div className="mb-4"><Notice kind="success">{action.success}</Notice></div>}
      {action.error && !editing && !toDelete && <div className="mb-4"><Notice kind="error">{action.error}</Notice></div>}

      {list.loading ? (
        <LoadingBlock />
      ) : list.error ? (
        <ErrorBlock message={list.error} onRetry={list.reload} />
      ) : !list.data?.items.length ? (
        <EmptyBlock icon={<Sparkles className="h-10 w-10" />} title="No poojas yet" hint="Add the daily rituals and sevas offered at the temple." />
      ) : (
        <ul className="grid gap-3 md:grid-cols-2">
          {list.data.items.map((p) => (
            <li key={p.id} className={`${cardCls} p-4`}>
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h2 className="font-semibold text-gray-900">{p.name}</h2>
                  <p className="text-xs text-gray-500">
                    {TYPES.find((t) => t.value === p.pooja_type)?.label ?? p.pooja_type}
                    {formatTimeRange(p.start_time, p.end_time) ? ` · ${formatTimeRange(p.start_time, p.end_time)}` : ''}
                  </p>
                </div>
                <StatusPill on={p.is_active} />
              </div>
              <p className="mt-2 text-sm text-gray-700">
                {p.is_paid ? `Fee ${formatMoney(p.suggested_amount)}` : 'Free'}
              </p>
              <div className="mt-3 flex gap-2">
                <button type="button" className={btnGhost} onClick={() => openEdit(p)}>
                  <Pencil className="h-4 w-4" aria-hidden="true" /> Edit
                </button>
                {p.is_active && (
                  <button type="button" className={btnDanger} onClick={() => setToDelete(p)} aria-label={`Hide ${p.name}`}>
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      {editing && (
        <Modal title={editing.id === null ? 'Add pooja' : 'Edit pooja'} onClose={() => { setEditing(null); action.clear(); }} wide>
          <form onSubmit={save} className="space-y-4">
            {action.error && <Notice kind="error">{action.error}</Notice>}
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Name" required className="sm:col-span-2">
                <input className={inputCls} maxLength={100} value={editing.form.name} onChange={(e) => set('name', e.target.value)} />
              </Field>
              <Field label="Type">
                <select className={inputCls} value={editing.form.pooja_type} onChange={(e) => set('pooja_type', e.target.value)}>
                  {TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </Field>
              <Field label="Display order" hint="Smaller numbers appear first.">
                <input type="number" min={0} className={inputCls} value={editing.form.sort_order} onChange={(e) => set('sort_order', e.target.value)} />
              </Field>
              <Field label="Start time">
                <input type="time" className={inputCls} value={editing.form.start_time} onChange={(e) => set('start_time', e.target.value)} />
              </Field>
              <Field label="End time">
                <input type="time" className={inputCls} value={editing.form.end_time} onChange={(e) => set('end_time', e.target.value)} />
              </Field>
              <label className="flex items-center gap-2 text-sm text-gray-700 sm:col-span-2">
                <input type="checkbox" checked={editing.form.is_paid} onChange={(e) => set('is_paid', e.target.checked)} />
                This seva has a fee (paid at the temple counter)
              </label>
              {editing.form.is_paid && (
                <Field label="Fee (₹)" required>
                  <input type="number" min={0} step="0.01" inputMode="decimal" className={inputCls} value={editing.form.suggested_amount} onChange={(e) => set('suggested_amount', e.target.value)} />
                </Field>
              )}
              <Field label="Description" className="sm:col-span-2">
                <textarea className={inputCls} rows={3} maxLength={3000} value={editing.form.description} onChange={(e) => set('description', e.target.value)} />
              </Field>
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input type="checkbox" checked={editing.form.is_active} onChange={(e) => set('is_active', e.target.checked)} />
              Visible on the website
            </label>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className={btnGhost} onClick={() => { setEditing(null); action.clear(); }}>Cancel</button>
              <button type="submit" className={btnPrimary} disabled={action.busy || editing.form.name.trim().length < 2}>
                {action.busy ? 'Saving…' : 'Save'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {toDelete && (
        <ConfirmDialog
          title="Hide this pooja?"
          message={`"${toDelete.name}" will be hidden from the website. Existing seva tickets are not affected.`}
          confirmLabel="Hide"
          danger
          busy={action.busy}
          onConfirm={remove}
          onCancel={() => { setToDelete(null); action.clear(); }}
        />
      )}
    </AdminPage>
  );
}
