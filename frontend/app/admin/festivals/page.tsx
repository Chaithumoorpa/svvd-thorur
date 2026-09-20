'use client';

import React, { useState } from 'react';
import { Calendar, Pencil, Plus, Trash2 } from 'lucide-react';
import AdminPage, { StatusPill } from '@/components/admin/AdminPage';
import ConfirmDialog from '@/components/admin/ConfirmDialog';
import Field from '@/components/ui/Field';
import Modal from '@/components/ui/Modal';
import Pager from '@/components/ui/Pager';
import { EmptyBlock, ErrorBlock, LoadingBlock, Notice } from '@/components/ui/States';
import { btnDanger, btnGhost, btnPrimary, cardCls, inputCls } from '@/components/ui/styles';
import { useAction } from '@/hooks/useAction';
import { useLoad } from '@/hooks/useLoad';
import { createFestival, deleteFestival, listAllFestivals, updateFestival } from '@/lib/api';
import { emptyToNull, formatDate } from '@/lib/format';
import type { Festival } from '@/lib/types';

const PAGE_SIZE = 25;
const TYPES = [
  { value: 'annual', label: 'Annual festival' },
  { value: 'monthly', label: 'Monthly event' },
  { value: 'special', label: 'Special occasion' },
];

interface FormState {
  name: string;
  description: string;
  festival_date: string;
  end_date: string;
  location: string;
  image_url: string;
  festival_type: string;
  is_active: boolean;
}
const blank: FormState = {
  name: '', description: '', festival_date: '', end_date: '', location: '', image_url: '',
  festival_type: 'annual', is_active: true,
};

export default function FestivalsAdmin() {
  const [page, setPage] = useState(1);
  const list = useLoad(() => listAllFestivals(page, PAGE_SIZE), [page]);
  const action = useAction();
  const [editing, setEditing] = useState<{ id: number | null; form: FormState } | null>(null);
  const [toDelete, setToDelete] = useState<Festival | null>(null);

  const openEdit = (f: Festival) =>
    setEditing({
      id: f.id,
      form: {
        name: f.name, description: f.description ?? '', festival_date: f.festival_date ?? '',
        end_date: f.end_date ?? '', location: f.location ?? '', image_url: f.image_url ?? '',
        festival_type: f.festival_type, is_active: f.is_active,
      },
    });

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!editing) return;
    const { id, form } = editing;
    const payload = {
      name: form.name.trim(),
      description: emptyToNull(form.description),
      festival_date: emptyToNull(form.festival_date),
      end_date: emptyToNull(form.end_date),
      location: emptyToNull(form.location),
      image_url: emptyToNull(form.image_url),
      festival_type: form.festival_type,
      is_active: form.is_active,
    };
    const ok = await action.run(
      () => (id === null ? createFestival(payload) : updateFestival(id, payload)),
      id === null ? 'Festival added.' : 'Festival updated.',
    );
    if (ok) {
      setEditing(null);
      list.reload();
    }
  }

  async function remove() {
    if (!toDelete) return;
    const ok = await action.run(() => deleteFestival(toDelete.id), 'Festival removed from the website.');
    if (ok) {
      setToDelete(null);
      list.reload();
    }
  }

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setEditing((cur) => (cur ? { ...cur, form: { ...cur.form, [key]: value } } : cur));

  return (
    <AdminPage
      title="Festivals & Events"
      description="Utsavams and special days listed on the Festivals page and home page."
      actions={
        <button type="button" className={btnPrimary} onClick={() => setEditing({ id: null, form: { ...blank } })}>
          <Plus className="h-4 w-4" aria-hidden="true" /> Add festival
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
        <EmptyBlock icon={<Calendar className="h-10 w-10" />} title="No festivals yet" hint="Add the temple's annual festivals and special days." />
      ) : (
        <>
          <ul className="space-y-3">
            {list.data.items.map((f) => (
              <li key={f.id} className={`${cardCls} flex flex-wrap items-start justify-between gap-3 p-4`}>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="font-semibold text-gray-900">{f.name}</h2>
                    <StatusPill on={f.is_active} />
                  </div>
                  <p className="mt-1 text-sm text-gray-600">
                    {f.festival_date ? formatDate(f.festival_date) : 'Date to be announced'}
                    {f.end_date ? ` – ${formatDate(f.end_date)}` : ''}
                    {f.location ? ` · ${f.location}` : ''}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button type="button" className={btnGhost} onClick={() => openEdit(f)} aria-label={`Edit ${f.name}`}>
                    <Pencil className="h-4 w-4" />
                  </button>
                  {f.is_active && (
                    <button type="button" className={btnDanger} onClick={() => setToDelete(f)} aria-label={`Remove ${f.name}`}>
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
          <Pager page={page} pageSize={PAGE_SIZE} total={list.data.total} onPage={setPage} />
        </>
      )}

      {editing && (
        <Modal title={editing.id === null ? 'Add festival' : 'Edit festival'} onClose={() => { setEditing(null); action.clear(); }} wide>
          <form onSubmit={save} className="space-y-4">
            {action.error && <Notice kind="error">{action.error}</Notice>}
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Name" required className="sm:col-span-2">
                <input className={inputCls} maxLength={150} value={editing.form.name} onChange={(e) => set('name', e.target.value)} />
              </Field>
              <Field label="Starts on">
                <input type="date" className={inputCls} value={editing.form.festival_date} onChange={(e) => set('festival_date', e.target.value)} />
              </Field>
              <Field label="Ends on" hint="For multi-day festivals.">
                <input type="date" className={inputCls} min={editing.form.festival_date || undefined} value={editing.form.end_date} onChange={(e) => set('end_date', e.target.value)} />
              </Field>
              <Field label="Type">
                <select className={inputCls} value={editing.form.festival_type} onChange={(e) => set('festival_type', e.target.value)}>
                  {TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </Field>
              <Field label="Location">
                <input className={inputCls} maxLength={200} value={editing.form.location} onChange={(e) => set('location', e.target.value)} />
              </Field>
              <Field label="Image link" hint="Optional. Web address of a photo." className="sm:col-span-2">
                <input className={inputCls} inputMode="url" placeholder="https://…" value={editing.form.image_url} onChange={(e) => set('image_url', e.target.value)} />
              </Field>
              <Field label="Description" className="sm:col-span-2">
                <textarea className={inputCls} rows={4} maxLength={5000} value={editing.form.description} onChange={(e) => set('description', e.target.value)} />
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
          title="Remove festival?"
          message={`"${toDelete.name}" will be hidden from the website. You can bring it back by editing it.`}
          confirmLabel="Remove"
          danger
          busy={action.busy}
          onConfirm={remove}
          onCancel={() => { setToDelete(null); action.clear(); }}
        />
      )}
    </AdminPage>
  );
}
