'use client';

import React, { useState } from 'react';
import { KeyRound, Pencil, Plus, ShieldCheck, Trash2 } from 'lucide-react';
import AdminPage, { StatusPill } from '@/components/admin/AdminPage';
import { useAuth } from '@/components/admin/AuthContext';
import ConfirmDialog from '@/components/admin/ConfirmDialog';
import Field from '@/components/ui/Field';
import Modal from '@/components/ui/Modal';
import Pager from '@/components/ui/Pager';
import { EmptyBlock, ErrorBlock, LoadingBlock, Notice } from '@/components/ui/States';
import { btnGhost, btnPrimary, cardCls, inputCls } from '@/components/ui/styles';
import { useAction } from '@/hooks/useAction';
import { useLoad } from '@/hooks/useLoad';
import { createUser, deleteUser, listUsers, updateUser } from '@/lib/api';
import { emptyToNull } from '@/lib/format';
import type { AppUser, Role } from '@/lib/types';

const PAGE_SIZE = 25;
const ROLES: Array<{ value: Role; label: string; hint: string }> = [
  { value: 'SUPER_ADMIN', label: 'Super Admin', hint: 'Everything, including users and the audit log' },
  { value: 'ADMIN', label: 'Admin', hint: 'Manage all temple content, donors, donations and finance' },
  { value: 'TRUSTEE', label: 'Trustee', hint: 'View members, donors, donations and finance reports' },
  { value: 'STAFF', label: 'Staff', hint: 'Edit website content, tickets and messages' },
  { value: 'GENERAL_USER', label: 'No admin access', hint: 'Cannot open the admin area' },
];

interface FormState {
  username: string;
  password: string;
  email: string;
  phone: string;
  role: Role;
  is_active: boolean;
}
const blank: FormState = { username: '', password: '', email: '', phone: '', role: 'STAFF', is_active: true };

export default function UsersAdmin() {
  const { me } = useAuth();
  const [page, setPage] = useState(1);
  const list = useLoad(() => listUsers(page, PAGE_SIZE), [page]);
  const action = useAction();
  const [editing, setEditing] = useState<{ id: number | null; form: FormState } | null>(null);
  const [toDelete, setToDelete] = useState<AppUser | null>(null);

  async function remove() {
    if (!toDelete) return;
    const ok = await action.run(() => deleteUser(toDelete.id), 'User deleted.');
    if (ok) {
      setToDelete(null);
      list.reload();
    }
  }

  const openEdit = (u: AppUser) =>
    setEditing({
      id: u.id,
      form: { username: u.username, password: '', email: u.email ?? '', phone: u.phone ?? '', role: (u.roles[0] ?? 'GENERAL_USER') as Role, is_active: u.is_active },
    });

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!editing) return;
    const { id, form } = editing;
    const ok = await action.run(
      () =>
        id === null
          ? createUser({ username: form.username.trim(), password: form.password, email: emptyToNull(form.email), phone: emptyToNull(form.phone), roles: [form.role] })
          : updateUser(id, {
              email: emptyToNull(form.email),
              phone: emptyToNull(form.phone),
              roles: [form.role],
              is_active: form.is_active,
              ...(form.password ? { password: form.password } : {}),
            }),
      id === null ? 'User created. They must change the temporary password at first sign-in.' : 'User updated.',
    );
    if (ok) {
      setEditing(null);
      list.reload();
    }
  }

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setEditing((cur) => (cur ? { ...cur, form: { ...cur.form, [key]: value } } : cur));

  const roleLabel = (r: string) => ROLES.find((x) => x.value === r)?.label ?? r;
  const creating = editing?.id === null;

  return (
    <AdminPage
      title="Users & Roles"
      description="People who can sign in to the admin area. Access is enforced by the server."
      actions={
        <button type="button" className={btnPrimary} onClick={() => setEditing({ id: null, form: { ...blank } })}>
          <Plus className="h-4 w-4" aria-hidden="true" /> Add user
        </button>
      }
    >
      {action.success && <div className="mb-4"><Notice kind="success">{action.success}</Notice></div>}
      {action.error && !editing && <div className="mb-4"><Notice kind="error">{action.error}</Notice></div>}

      {list.loading ? (
        <LoadingBlock />
      ) : list.error ? (
        <ErrorBlock message={list.error} onRetry={list.reload} />
      ) : !list.data?.items.length ? (
        <EmptyBlock icon={<ShieldCheck className="h-10 w-10" />} title="No users" />
      ) : (
        <>
          <div className={`${cardCls} overflow-x-auto`}>
            <table className="w-full min-w-[600px] text-left text-sm">
              <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th scope="col" className="px-4 py-3">Username</th>
                  <th scope="col" className="px-4 py-3">Role</th>
                  <th scope="col" className="px-4 py-3">Contact</th>
                  <th scope="col" className="px-4 py-3">Status</th>
                  <th scope="col" className="px-4 py-3"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {list.data.items.map((u) => (
                  <tr key={u.id}>
                    <td className="px-4 py-3 font-medium text-gray-900">{u.username}{u.must_change_password && <span className="ml-2 text-xs text-amber-700">(temporary password)</span>}</td>
                    <td className="px-4 py-3 text-gray-700">{u.roles.map(roleLabel).join(', ')}</td>
                    <td className="px-4 py-3 text-gray-600">{u.email ?? '—'}{u.phone && <div className="text-xs text-gray-400">{u.phone}</div>}</td>
                    <td className="px-4 py-3"><StatusPill on={u.is_active} onLabel="Active" offLabel="Disabled" /></td>
                    <td className="px-4 py-3 text-right">
                      <button type="button" className={btnGhost} onClick={() => openEdit(u)} aria-label={`Edit ${u.username}`}><Pencil className="h-4 w-4" /></button>
                      {me.is_super_admin && u.id !== me.id && (
                        <button type="button" className={btnGhost} onClick={() => setToDelete(u)} aria-label={`Delete ${u.username}`}>
                          <Trash2 className="h-4 w-4 text-red-700" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pager page={page} pageSize={PAGE_SIZE} total={list.data.total} onPage={setPage} />
        </>
      )}

      {editing && (
        <Modal title={creating ? 'Add user' : `Edit ${editing.form.username}`} onClose={() => { setEditing(null); action.clear(); }}>
          <form onSubmit={save} className="space-y-4">
            {action.error && <Notice kind="error">{action.error}</Notice>}
            <Field label="Username" required hint={creating ? '3–100 letters, digits, . _ @ -' : 'Usernames cannot be changed.'}>
              <input className={inputCls} disabled={!creating} autoComplete="off" value={editing.form.username} onChange={(e) => set('username', e.target.value)} />
            </Field>
            <Field label={creating ? 'Temporary password' : 'Reset password'} required={creating} hint={creating ? 'At least 8 characters with a letter and a number. The user must change it at first sign-in.' : 'Leave empty to keep the current password.'}>
              <input type="password" autoComplete="new-password" className={inputCls} value={editing.form.password} onChange={(e) => set('password', e.target.value)} />
            </Field>
            <Field label="Role" hint={ROLES.find((r) => r.value === editing.form.role)?.hint}>
              <select className={inputCls} value={editing.form.role} onChange={(e) => set('role', e.target.value as Role)}>
                {ROLES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
              </select>
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Email"><input type="email" className={inputCls} value={editing.form.email} onChange={(e) => set('email', e.target.value)} /></Field>
              <Field label="Phone"><input type="tel" className={inputCls} value={editing.form.phone} onChange={(e) => set('phone', e.target.value)} /></Field>
            </div>
            {!creating && (
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input type="checkbox" checked={editing.form.is_active} onChange={(e) => set('is_active', e.target.checked)} />
                Account enabled
              </label>
            )}
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className={btnGhost} onClick={() => { setEditing(null); action.clear(); }}>Cancel</button>
              <button type="submit" className={btnPrimary} disabled={action.busy || (creating && (editing.form.username.trim().length < 3 || editing.form.password.length < 8))}>
                <KeyRound className="h-4 w-4" aria-hidden="true" /> {action.busy ? 'Saving…' : 'Save'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {toDelete && (
        <ConfirmDialog
          title="Delete user?"
          message={`This permanently deletes ${toDelete.username}'s account and login access. Any sevas they booked while signed in stay on record, just unlinked from the account. This can't be undone.`}
          confirmLabel="Delete"
          danger
          busy={action.busy}
          onConfirm={remove}
          onCancel={() => setToDelete(null)}
        />
      )}
    </AdminPage>
  );
}
