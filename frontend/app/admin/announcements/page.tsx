'use client';

import React, { useState } from 'react';
import { Megaphone, Pencil, Plus, Trash2 } from 'lucide-react';
import AdminPage, { StatusPill } from '@/components/admin/AdminPage';
import ConfirmDialog from '@/components/admin/ConfirmDialog';
import Field from '@/components/ui/Field';
import Modal from '@/components/ui/Modal';
import Pager from '@/components/ui/Pager';
import { EmptyBlock, ErrorBlock, LoadingBlock, Notice } from '@/components/ui/States';
import { btnDanger, btnGhost, btnPrimary, cardCls, inputCls } from '@/components/ui/styles';
import { useAction } from '@/hooks/useAction';
import { useLoad } from '@/hooks/useLoad';
import {
  createAnnouncement, deleteAnnouncement, listAllAnnouncements, updateAnnouncement,
} from '@/lib/api';
import { emptyToNull, formatDate, todayISO } from '@/lib/format';
import type { Announcement } from '@/lib/types';

const PAGE_SIZE = 25;

interface FormState {
  title: string;
  message: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
}

const blank: FormState = { title: '', message: '', start_date: '', end_date: '', is_active: true };

function status(a: Announcement): { label: string; on: boolean } {
  const today = todayISO();
  if (!a.is_active) return { label: 'Hidden', on: false };
  if (a.start_date && a.start_date > today) return { label: 'Scheduled', on: false };
  if (a.end_date && a.end_date < today) return { label: 'Expired', on: false };
  return { label: 'Live', on: true };
}

export default function AnnouncementsAdmin() {
  const [page, setPage] = useState(1);
  const list = useLoad(() => listAllAnnouncements(page, PAGE_SIZE), [page]);
  const action = useAction();
  const [editing, setEditing] = useState<{ id: number | null; form: FormState } | null>(null);
  const [toDelete, setToDelete] = useState<Announcement | null>(null);

  const openNew = () => setEditing({ id: null, form: { ...blank } });
  const openEdit = (a: Announcement) =>
    setEditing({
      id: a.id,
      form: {
        title: a.title, message: a.message ?? '', start_date: a.start_date ?? '',
        end_date: a.end_date ?? '', is_active: a.is_active,
      },
    });

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!editing) return;
    const { id, form } = editing;
    const payload = {
      title: form.title.trim(),
      message: emptyToNull(form.message),
      start_date: emptyToNull(form.start_date),
      end_date: emptyToNull(form.end_date),
      is_active: form.is_active,
    };
    const ok = await action.run(
      () => (id === null ? createAnnouncement(payload) : updateAnnouncement(id, payload)),
      id === null ? 'Announcement published.' : 'Announcement updated.',
    );
    if (ok) {
      setEditing(null);
      list.reload();
    }
  }

  async function remove() {
    if (!toDelete) return;
    const ok = await action.run(() => deleteAnnouncement(toDelete.id), 'Announcement hidden from the website.');
    if (ok) {
      setToDelete(null);
      list.reload();
    }
  }

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setEditing((cur) => (cur ? { ...cur, form: { ...cur.form, [key]: value } } : cur));

  return (
    <AdminPage
      title="Announcements"
      description="Notices shown on the home page and the Announcements page."
      actions={
        <button type="button" className={btnPrimary} onClick={openNew}>
          <Plus className="h-4 w-4" aria-hidden="true" /> New announcement
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
        <EmptyBlock
          icon={<Megaphone className="h-10 w-10" />}
          title="No announcements yet"
          hint="Post a notice about a festival, timing change or special event."
          action={<button type="button" className={btnPrimary} onClick={openNew}>Create the first one</button>}
        />
      ) : (
        <>
          <ul className="space-y-3">
            {list.data.items.map((a) => {
              const st = status(a);
              return (
                <li key={a.id} className={`${cardCls} flex flex-wrap items-start justify-between gap-3 p-4`}>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="font-semibold text-gray-900">{a.title}</h2>
                      <StatusPill on={st.on} onLabel={st.label} offLabel={st.label} />
                      {a.source_festival_id != null && (
                        <span
                          className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800"
                          title="Posted automatically from a festival's auto-announce setting"
                        >
                          Auto
                        </span>
                      )}
                    </div>
                    {a.message && <p className="mt-1 line-clamp-2 text-sm text-gray-600">{a.message}</p>}
                    <p className="mt-2 text-xs text-gray-400">
                      {a.start_date || a.end_date
                        ? `Shown ${a.start_date ? `from ${formatDate(a.start_date)}` : ''} ${a.end_date ? `until ${formatDate(a.end_date)}` : ''}`
                        : 'Always shown while live'}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button type="button" className={btnGhost} onClick={() => openEdit(a)} aria-label={`Edit ${a.title}`}>
                      <Pencil className="h-4 w-4" />
                    </button>
                    {a.is_active && (
                      <button type="button" className={btnDanger} onClick={() => setToDelete(a)} aria-label={`Hide ${a.title}`}>
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
          <Pager page={page} pageSize={PAGE_SIZE} total={list.data.total} onPage={setPage} />
        </>
      )}

      {editing && (
        <Modal title={editing.id === null ? 'New announcement' : 'Edit announcement'} onClose={() => { setEditing(null); action.clear(); }}>
          <form onSubmit={save} className="space-y-4">
            {action.error && <Notice kind="error">{action.error}</Notice>}
            <Field label="Title" required>
              <input className={inputCls} maxLength={200} value={editing.form.title} onChange={(e) => set('title', e.target.value)} />
            </Field>
            <Field label="Message">
              <textarea className={inputCls} rows={4} maxLength={5000} value={editing.form.message} onChange={(e) => set('message', e.target.value)} />
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Show from" hint="Optional. Leave empty to show immediately.">
                <input type="date" className={inputCls} value={editing.form.start_date} onChange={(e) => set('start_date', e.target.value)} />
              </Field>
              <Field label="Show until" hint="Optional. Leave empty to keep it up.">
                <input type="date" className={inputCls} min={editing.form.start_date || undefined} value={editing.form.end_date} onChange={(e) => set('end_date', e.target.value)} />
              </Field>
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input type="checkbox" checked={editing.form.is_active} onChange={(e) => set('is_active', e.target.checked)} />
              Visible on the website
            </label>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className={btnGhost} onClick={() => { setEditing(null); action.clear(); }}>Cancel</button>
              <button type="submit" className={btnPrimary} disabled={action.busy || !editing.form.title.trim()}>
                {action.busy ? 'Saving…' : 'Save'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {toDelete && (
        <ConfirmDialog
          title="Hide announcement?"
          message={`"${toDelete.title}" will no longer appear on the website. You can show it again later by editing it.`}
          confirmLabel="Hide it"
          danger
          busy={action.busy}
          onConfirm={remove}
          onCancel={() => { setToDelete(null); action.clear(); }}
        />
      )}
    </AdminPage>
  );
}
