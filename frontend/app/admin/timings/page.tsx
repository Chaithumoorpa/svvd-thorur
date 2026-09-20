'use client';

import React, { useState } from 'react';
import { Clock, Pencil, Plus, Trash2 } from 'lucide-react';
import AdminPage, { StatusPill } from '@/components/admin/AdminPage';
import ConfirmDialog from '@/components/admin/ConfirmDialog';
import Field from '@/components/ui/Field';
import Modal from '@/components/ui/Modal';
import { EmptyBlock, ErrorBlock, LoadingBlock, Notice } from '@/components/ui/States';
import { btnDanger, btnGhost, btnPrimary, cardCls, inputCls } from '@/components/ui/styles';
import { useAction } from '@/hooks/useAction';
import { useLoad } from '@/hooks/useLoad';
import { createTiming, deleteTiming, listAllTimings, updateTiming } from '@/lib/api';
import { emptyToNull, formatTimeRange } from '@/lib/format';
import type { TempleTiming } from '@/lib/types';

interface FormState {
  label: string;
  start_time: string;
  end_time: string;
  days: string;
  note: string;
  sort_order: string;
  is_active: boolean;
}
const blank: FormState = { label: '', start_time: '', end_time: '', days: 'Daily', note: '', sort_order: '0', is_active: true };
const hhmm = (t: string) => t.slice(0, 5);
const full = (t: string) => (t.length === 5 ? `${t}:00` : t);

export default function TimingsAdmin() {
  const list = useLoad(listAllTimings, []);
  const action = useAction();
  const [editing, setEditing] = useState<{ id: number | null; form: FormState } | null>(null);
  const [toDelete, setToDelete] = useState<TempleTiming | null>(null);

  const openEdit = (t: TempleTiming) =>
    setEditing({
      id: t.id,
      form: { label: t.label, start_time: hhmm(t.start_time), end_time: hhmm(t.end_time), days: t.days, note: t.note ?? '', sort_order: String(t.sort_order), is_active: t.is_active },
    });

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!editing) return;
    const { id, form } = editing;
    if (form.end_time <= form.start_time) {
      action.setError('Closing time must be after opening time.');
      return;
    }
    const payload = {
      label: form.label.trim(),
      start_time: full(form.start_time),
      end_time: full(form.end_time),
      days: form.days.trim() || 'Daily',
      note: emptyToNull(form.note),
      sort_order: Number(form.sort_order) || 0,
      is_active: form.is_active,
    };
    const ok = await action.run(
      () => (id === null ? createTiming(payload) : updateTiming(id, payload)),
      'Timing saved. The website updates within a minute.',
    );
    if (ok) {
      setEditing(null);
      list.reload();
    }
  }

  async function remove() {
    if (!toDelete) return;
    const ok = await action.run(() => deleteTiming(toDelete.id), 'Timing deleted.');
    if (ok) {
      setToDelete(null);
      list.reload();
    }
  }

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setEditing((cur) => (cur ? { ...cur, form: { ...cur.form, [key]: value } } : cur));

  return (
    <AdminPage
      title="Darshan Timings"
      description="Opening hours shown on the Timings page and in the site footer."
      actions={
        <button type="button" className={btnPrimary} onClick={() => setEditing({ id: null, form: { ...blank } })}>
          <Plus className="h-4 w-4" aria-hidden="true" /> Add timing
        </button>
      }
    >
      {action.success && <div className="mb-4"><Notice kind="success">{action.success}</Notice></div>}
      {action.error && !editing && !toDelete && <div className="mb-4"><Notice kind="error">{action.error}</Notice></div>}

      {list.loading ? (
        <LoadingBlock />
      ) : list.error ? (
        <ErrorBlock message={list.error} onRetry={list.reload} />
      ) : !list.data?.length ? (
        <EmptyBlock icon={<Clock className="h-10 w-10" />} title="No timings yet" hint="Add the morning and evening darshan hours." />
      ) : (
        <ul className="space-y-3">
          {list.data.map((t) => (
            <li key={t.id} className={`${cardCls} flex flex-wrap items-center justify-between gap-3 p-4`}>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="font-semibold text-gray-900">{t.label}</h2>
                  <StatusPill on={t.is_active} />
                </div>
                <p className="text-lg text-red-900">{formatTimeRange(t.start_time, t.end_time)}</p>
                <p className="text-sm text-gray-500">{t.days}{t.note ? ` · ${t.note}` : ''}</p>
              </div>
              <div className="flex gap-2">
                <button type="button" className={btnGhost} onClick={() => openEdit(t)} aria-label={`Edit ${t.label}`}>
                  <Pencil className="h-4 w-4" />
                </button>
                <button type="button" className={btnDanger} onClick={() => setToDelete(t)} aria-label={`Delete ${t.label}`}>
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {editing && (
        <Modal title={editing.id === null ? 'Add timing' : 'Edit timing'} onClose={() => { setEditing(null); action.clear(); }}>
          <form onSubmit={save} className="space-y-4">
            {action.error && <Notice kind="error">{action.error}</Notice>}
            <Field label="Name" required hint="For example: Morning Darshan">
              <input className={inputCls} maxLength={100} value={editing.form.label} onChange={(e) => set('label', e.target.value)} />
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Opens" required>
                <input type="time" className={inputCls} value={editing.form.start_time} onChange={(e) => set('start_time', e.target.value)} />
              </Field>
              <Field label="Closes" required>
                <input type="time" className={inputCls} value={editing.form.end_time} onChange={(e) => set('end_time', e.target.value)} />
              </Field>
              <Field label="Days" hint="For example: Daily, or Tuesdays and Fridays">
                <input className={inputCls} maxLength={100} value={editing.form.days} onChange={(e) => set('days', e.target.value)} />
              </Field>
              <Field label="Display order" hint="Smaller numbers first.">
                <input type="number" min={0} className={inputCls} value={editing.form.sort_order} onChange={(e) => set('sort_order', e.target.value)} />
              </Field>
            </div>
            <Field label="Note" hint="Shown under the time, e.g. Suprabhatam 6:00 AM, Abhishekam 7:00 AM">
              <textarea className={inputCls} rows={2} maxLength={300} value={editing.form.note} onChange={(e) => set('note', e.target.value)} />
            </Field>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input type="checkbox" checked={editing.form.is_active} onChange={(e) => set('is_active', e.target.checked)} />
              Visible on the website
            </label>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className={btnGhost} onClick={() => { setEditing(null); action.clear(); }}>Cancel</button>
              <button type="submit" className={btnPrimary} disabled={action.busy || !editing.form.label.trim() || !editing.form.start_time || !editing.form.end_time}>
                {action.busy ? 'Saving…' : 'Save'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {toDelete && (
        <ConfirmDialog
          title="Delete this timing?"
          message={`"${toDelete.label}" will be removed from the website.`}
          confirmLabel="Delete"
          danger
          busy={action.busy}
          onConfirm={remove}
          onCancel={() => { setToDelete(null); action.clear(); }}
        />
      )}
    </AdminPage>
  );
}
