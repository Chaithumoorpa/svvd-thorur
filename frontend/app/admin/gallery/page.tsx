'use client';

import React, { useState } from 'react';
import { ImageIcon, Pencil, Plus, Trash2 } from 'lucide-react';
import AdminPage, { StatusPill } from '@/components/admin/AdminPage';
import ConfirmDialog from '@/components/admin/ConfirmDialog';
import Field from '@/components/ui/Field';
import Modal from '@/components/ui/Modal';
import Pager from '@/components/ui/Pager';
import { EmptyBlock, ErrorBlock, LoadingBlock, Notice } from '@/components/ui/States';
import { btnDanger, btnGhost, btnPrimary, cardCls, inputCls } from '@/components/ui/styles';
import { useAction } from '@/hooks/useAction';
import { useLoad } from '@/hooks/useLoad';
import { createGallery, deleteGallery, listAllGallery, updateGallery } from '@/lib/api';
import { emptyToNull } from '@/lib/format';
import type { GalleryItem } from '@/lib/types';

const PAGE_SIZE = 24;
const GALLERY_CATEGORIES = [
  { value: 'TEMPLE', label: 'Temple' },
  { value: 'FESTIVAL', label: 'Festivals' },
  { value: 'EVENT', label: 'Events' },
];

interface FormState {
  title: string;
  description: string;
  image_url: string;
  category: string;
  sort_order: string;
  is_active: boolean;
}
const blank: FormState = { title: '', description: '', image_url: '', category: 'TEMPLE', sort_order: '0', is_active: true };

export default function GalleryAdmin() {
  const [page, setPage] = useState(1);
  const list = useLoad(() => listAllGallery(page, PAGE_SIZE), [page]);
  const action = useAction();
  const [editing, setEditing] = useState<{ id: number | null; form: FormState } | null>(null);
  const [toDelete, setToDelete] = useState<GalleryItem | null>(null);

  const openEdit = (g: GalleryItem) =>
    setEditing({
      id: g.id,
      form: { title: g.title, description: g.description ?? '', image_url: g.image_url, category: g.category, sort_order: String(g.sort_order), is_active: g.is_active },
    });

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!editing) return;
    const { id, form } = editing;
    const payload = {
      title: form.title.trim(),
      description: emptyToNull(form.description),
      image_url: form.image_url.trim(),
      category: form.category,
      sort_order: Number(form.sort_order) || 0,
      is_active: form.is_active,
    };
    const ok = await action.run(
      () => (id === null ? createGallery(payload) : updateGallery(id, payload)),
      id === null ? 'Photo added.' : 'Photo updated.',
    );
    if (ok) {
      setEditing(null);
      list.reload();
    }
  }

  async function remove() {
    if (!toDelete) return;
    const ok = await action.run(() => deleteGallery(toDelete.id), 'Photo deleted.');
    if (ok) {
      setToDelete(null);
      list.reload();
    }
  }

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setEditing((cur) => (cur ? { ...cur, form: { ...cur.form, [key]: value } } : cur));

  return (
    <AdminPage
      title="Gallery"
      description="Photos shown on the public Gallery page."
      actions={
        <button type="button" className={btnPrimary} onClick={() => setEditing({ id: null, form: { ...blank } })}>
          <Plus className="h-4 w-4" aria-hidden="true" /> Add photo
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
        <EmptyBlock icon={<ImageIcon className="h-10 w-10" />} title="No photos yet" hint="Add a photo using its web address (link)." />
      ) : (
        <>
          <ul className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
            {list.data.items.map((g) => (
              <li key={g.id} className={`${cardCls} overflow-hidden`}>
                <div className="aspect-[4/3] bg-gray-100">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={g.image_url} alt={g.title} loading="lazy" className="h-full w-full object-cover" />
                </div>
                <div className="p-3">
                  <div className="flex items-start justify-between gap-1">
                    <p className="truncate text-sm font-medium text-gray-900">{g.title}</p>
                    <StatusPill on={g.is_active} />
                  </div>
                  <p className="text-xs text-gray-500">{g.category}</p>
                  <div className="mt-2 flex gap-2">
                    <button type="button" className={btnGhost} onClick={() => openEdit(g)} aria-label={`Edit ${g.title}`}>
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button type="button" className={btnDanger} onClick={() => setToDelete(g)} aria-label={`Delete ${g.title}`}>
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
          <Pager page={page} pageSize={PAGE_SIZE} total={list.data.total} onPage={setPage} />
        </>
      )}

      {editing && (
        <Modal title={editing.id === null ? 'Add photo' : 'Edit photo'} onClose={() => { setEditing(null); action.clear(); }}>
          <form onSubmit={save} className="space-y-4">
            {action.error && <Notice kind="error">{action.error}</Notice>}
            <Field label="Title" required>
              <input className={inputCls} maxLength={200} value={editing.form.title} onChange={(e) => set('title', e.target.value)} />
            </Field>
            <Field label="Image link" required hint="A web address starting with https:// or a path like /images/photo.jpg">
              <input className={inputCls} inputMode="url" value={editing.form.image_url} onChange={(e) => set('image_url', e.target.value)} />
            </Field>
            {editing.form.image_url && /^(https?:\/\/|\/)/.test(editing.form.image_url) && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={editing.form.image_url} alt="Preview" className="max-h-40 rounded-lg border border-gray-200 object-contain" />
            )}
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Category">
                <select className={inputCls} value={editing.form.category} onChange={(e) => set('category', e.target.value)}>
                  {GALLERY_CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
              </Field>
              <Field label="Display order" hint="Smaller numbers first.">
                <input type="number" min={0} className={inputCls} value={editing.form.sort_order} onChange={(e) => set('sort_order', e.target.value)} />
              </Field>
            </div>
            <Field label="Caption">
              <textarea className={inputCls} rows={2} maxLength={2000} value={editing.form.description} onChange={(e) => set('description', e.target.value)} />
            </Field>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input type="checkbox" checked={editing.form.is_active} onChange={(e) => set('is_active', e.target.checked)} />
              Visible on the website
            </label>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className={btnGhost} onClick={() => { setEditing(null); action.clear(); }}>Cancel</button>
              <button type="submit" className={btnPrimary} disabled={action.busy || !editing.form.title.trim() || !editing.form.image_url.trim()}>
                {action.busy ? 'Saving…' : 'Save'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {toDelete && (
        <ConfirmDialog
          title="Delete this photo?"
          message={`"${toDelete.title}" will be permanently removed from the gallery.`}
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
