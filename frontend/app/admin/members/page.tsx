'use client';

import React, { useState } from 'react';
import { Eye, Pencil, Plus, Trash2, Users } from 'lucide-react';
import AdminPage, { StatusPill } from '@/components/admin/AdminPage';
import { useAuth } from '@/components/admin/AuthContext';
import ConfirmDialog from '@/components/admin/ConfirmDialog';
import Field from '@/components/ui/Field';
import Modal from '@/components/ui/Modal';
import Pager from '@/components/ui/Pager';
import { EmptyBlock, ErrorBlock, LoadingBlock, Notice } from '@/components/ui/States';
import { btnDanger, btnGhost, btnPrimary, cardCls, inputCls } from '@/components/ui/styles';
import { useAction } from '@/hooks/useAction';
import { useLoad } from '@/hooks/useLoad';
import { createMember, deleteMember, listMembers, updateMember } from '@/lib/api';
import { emptyToNull } from '@/lib/format';
import type { Member } from '@/lib/types';

const PAGE_SIZE = 25;
const POSITIONS = ['Chairman', 'Trustee', 'Secretary', 'Treasurer', 'Priest', 'Staff', 'Volunteer'];

interface FormState {
  name: string;
  phone: string;
  email: string;
  position: string;
  photo_url: string;
  sort_order: string;
  show_on_website: boolean;
}
const blank: FormState = { name: '', phone: '', email: '', position: '', photo_url: '', sort_order: '0', show_on_website: false };

export default function MembersAdmin() {
  const { can } = useAuth();
  const canWrite = can('members:write');
  const [page, setPage] = useState(1);
  const list = useLoad(() => listMembers(page, PAGE_SIZE), [page]);
  const action = useAction();
  const [editing, setEditing] = useState<{ id: number | null; form: FormState } | null>(null);
  const [toDelete, setToDelete] = useState<Member | null>(null);

  const openEdit = (m: Member) =>
    setEditing({
      id: m.id,
      form: { name: m.name, phone: m.phone, email: m.email ?? '', position: m.position ?? '', photo_url: m.photo_url ?? '', sort_order: String(m.sort_order), show_on_website: m.show_on_website },
    });

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!editing) return;
    const { id, form } = editing;
    const payload = {
      name: form.name.trim(),
      phone: form.phone.trim(),
      email: emptyToNull(form.email),
      position: emptyToNull(form.position),
      photo_url: emptyToNull(form.photo_url),
      sort_order: Number(form.sort_order) || 0,
      show_on_website: form.show_on_website,
    };
    const ok = await action.run(
      () => (id === null ? createMember(payload) : updateMember(id, payload)),
      id === null ? 'Member added.' : 'Member updated.',
    );
    if (ok) {
      setEditing(null);
      list.reload();
    }
  }

  async function remove() {
    if (!toDelete) return;
    const ok = await action.run(() => deleteMember(toDelete.id), 'Member removed.');
    if (ok) {
      setToDelete(null);
      list.reload();
    }
  }

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setEditing((cur) => (cur ? { ...cur, form: { ...cur.form, [key]: value } } : cur));

  return (
    <AdminPage
      title="Temple Members"
      description="Trustees, priests and staff. Phone and email stay private; only name, position and photo can be shown on the website."
      actions={
        canWrite && (
          <button type="button" className={btnPrimary} onClick={() => setEditing({ id: null, form: { ...blank } })}>
            <Plus className="h-4 w-4" aria-hidden="true" /> Add member
          </button>
        )
      }
    >
      {action.success && <div className="mb-4"><Notice kind="success">{action.success}</Notice></div>}
      {action.error && !editing && !toDelete && <div className="mb-4"><Notice kind="error">{action.error}</Notice></div>}

      {list.loading ? (
        <LoadingBlock />
      ) : list.error ? (
        <ErrorBlock message={list.error} onRetry={list.reload} />
      ) : !list.data?.items.length ? (
        <EmptyBlock icon={<Users className="h-10 w-10" />} title="No members yet" hint="Add trustees, priests and staff." />
      ) : (
        <>
          <div className={`${cardCls} overflow-x-auto`}>
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th scope="col" className="px-4 py-3">Name</th>
                  <th scope="col" className="px-4 py-3">Position</th>
                  <th scope="col" className="px-4 py-3">Contact</th>
                  <th scope="col" className="px-4 py-3">Website</th>
                  {canWrite && <th scope="col" className="px-4 py-3"><span className="sr-only">Actions</span></th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {list.data.items.map((m) => (
                  <tr key={m.id}>
                    <td className="px-4 py-3 font-medium text-gray-900">{m.name}</td>
                    <td className="px-4 py-3 text-gray-600">{m.position ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-600">
                      {m.phone}
                      {m.email && <div className="text-xs text-gray-400">{m.email}</div>}
                    </td>
                    <td className="px-4 py-3">
                      {m.show_on_website ? (
                        <span className="inline-flex items-center gap-1 text-xs text-green-700"><Eye className="h-3 w-3" /> Shown</span>
                      ) : (
                        <StatusPill on={false} offLabel="Private" />
                      )}
                    </td>
                    {canWrite && (
                      <td className="px-4 py-3">
                        <div className="flex justify-end gap-2">
                          <button type="button" className={btnGhost} onClick={() => openEdit(m)} aria-label={`Edit ${m.name}`}>
                            <Pencil className="h-4 w-4" />
                          </button>
                          <button type="button" className={btnDanger} onClick={() => setToDelete(m)} aria-label={`Remove ${m.name}`}>
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pager page={page} pageSize={PAGE_SIZE} total={list.data.total} onPage={setPage} />
        </>
      )}

      {editing && (
        <Modal title={editing.id === null ? 'Add member' : 'Edit member'} onClose={() => { setEditing(null); action.clear(); }}>
          <form onSubmit={save} className="space-y-4">
            {action.error && <Notice kind="error">{action.error}</Notice>}
            <Field label="Full name" required>
              <input className={inputCls} maxLength={200} value={editing.form.name} onChange={(e) => set('name', e.target.value)} />
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Phone" required>
                <input type="tel" className={inputCls} value={editing.form.phone} onChange={(e) => set('phone', e.target.value)} />
              </Field>
              <Field label="Email">
                <input type="email" className={inputCls} value={editing.form.email} onChange={(e) => set('email', e.target.value)} />
              </Field>
              <Field label="Position">
                <input list="positions" className={inputCls} maxLength={100} value={editing.form.position} onChange={(e) => set('position', e.target.value)} />
              </Field>
              <datalist id="positions">{POSITIONS.map((p) => <option key={p} value={p} />)}</datalist>
              <Field label="Display order" hint="Smaller numbers first.">
                <input type="number" min={0} className={inputCls} value={editing.form.sort_order} onChange={(e) => set('sort_order', e.target.value)} />
              </Field>
            </div>
            <Field label="Photo link" hint="Optional. Only used if shown on the website.">
              <input className={inputCls} inputMode="url" value={editing.form.photo_url} onChange={(e) => set('photo_url', e.target.value)} />
            </Field>
            <label className="flex items-start gap-2 text-sm text-gray-700">
              <input type="checkbox" className="mt-1" checked={editing.form.show_on_website} onChange={(e) => set('show_on_website', e.target.checked)} />
              <span>
                Show on the website Committee page
                <span className="block text-xs text-gray-500">Only the name, position and photo are published — never the phone or email.</span>
              </span>
            </label>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className={btnGhost} onClick={() => { setEditing(null); action.clear(); }}>Cancel</button>
              <button type="submit" className={btnPrimary} disabled={action.busy || editing.form.name.trim().length < 2 || !editing.form.phone.trim()}>
                {action.busy ? 'Saving…' : 'Save'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {toDelete && (
        <ConfirmDialog
          title="Remove member?"
          message={`${toDelete.name} will be removed from the member list and the website.`}
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
