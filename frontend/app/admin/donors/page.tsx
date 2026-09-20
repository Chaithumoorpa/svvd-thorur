'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Heart, Pencil, Plus, Search, Trash2 } from 'lucide-react';
import AdminPage from '@/components/admin/AdminPage';
import { useAuth } from '@/components/admin/AuthContext';
import ConfirmDialog from '@/components/admin/ConfirmDialog';
import Field from '@/components/ui/Field';
import Modal from '@/components/ui/Modal';
import Pager from '@/components/ui/Pager';
import { EmptyBlock, ErrorBlock, LoadingBlock, Notice } from '@/components/ui/States';
import { btnDanger, btnGhost, btnPrimary, cardCls, inputCls } from '@/components/ui/styles';
import { useAction } from '@/hooks/useAction';
import { useLoad } from '@/hooks/useLoad';
import { createDonor, deleteDonor, listDonors, updateDonor } from '@/lib/api';
import { emptyToNull, formatMoney } from '@/lib/format';
import type { Donor } from '@/lib/types';

const PAGE_SIZE = 25;

interface FormState {
  name: string;
  phone: string;
  email: string;
  address: string;
  pan_number: string;
}
const blank: FormState = { name: '', phone: '', email: '', address: '', pan_number: '' };

export default function DonorsAdmin() {
  const { can } = useAuth();
  const canWrite = can('donors:write');
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const list = useLoad(() => listDonors(page, search, PAGE_SIZE), [page, search]);
  const action = useAction();
  const [editing, setEditing] = useState<{ id: number | null; form: FormState } | null>(null);
  const [toDelete, setToDelete] = useState<Donor | null>(null);

  const openEdit = (d: Donor) =>
    setEditing({
      id: d.id,
      // a masked PAN (read-only roles) must never be sent back
      form: { name: d.name, phone: d.phone ?? '', email: d.email ?? '', address: d.address ?? '', pan_number: d.pan_number?.includes('*') ? '' : d.pan_number ?? '' },
    });

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!editing) return;
    const { id, form } = editing;
    const payload = {
      name: form.name.trim(),
      phone: emptyToNull(form.phone),
      email: emptyToNull(form.email),
      address: emptyToNull(form.address),
      pan_number: emptyToNull(form.pan_number)?.toUpperCase() ?? null,
    };
    const ok = await action.run(
      () => (id === null ? createDonor(payload) : updateDonor(id, payload)),
      id === null ? 'Donor added.' : 'Donor updated.',
    );
    if (ok) {
      setEditing(null);
      list.reload();
    }
  }

  async function remove() {
    if (!toDelete) return;
    const ok = await action.run(() => deleteDonor(toDelete.id), 'Donor deactivated. Their donation history is kept.');
    if (ok) {
      setToDelete(null);
      list.reload();
    }
  }

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setEditing((cur) => (cur ? { ...cur, form: { ...cur.form, [key]: value } } : cur));

  return (
    <AdminPage
      title="Donors"
      description="Private donor directory. Nothing here is shown on the public website."
      actions={
        canWrite && (
          <button type="button" className={btnPrimary} onClick={() => setEditing({ id: null, form: { ...blank } })}>
            <Plus className="h-4 w-4" aria-hidden="true" /> Add donor
          </button>
        )
      }
    >
      <form
        role="search"
        className="mb-4 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          setPage(1);
          setSearch(searchInput.trim());
        }}
      >
        <div className="relative flex-1 sm:max-w-sm">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" aria-hidden="true" />
          <input
            aria-label="Search donors by name or phone"
            className={`${inputCls} pl-9`}
            placeholder="Search by name or phone"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
        </div>
        <button type="submit" className={btnGhost}>Search</button>
      </form>

      {action.success && <div className="mb-4"><Notice kind="success">{action.success}</Notice></div>}
      {action.error && !editing && !toDelete && <div className="mb-4"><Notice kind="error">{action.error}</Notice></div>}

      {list.loading ? (
        <LoadingBlock />
      ) : list.error ? (
        <ErrorBlock message={list.error} onRetry={list.reload} />
      ) : !list.data?.items.length ? (
        <EmptyBlock icon={<Heart className="h-10 w-10" />} title={search ? 'No donors match your search' : 'No donors yet'} hint={search ? undefined : 'Add a donor, then record their donations.'} />
      ) : (
        <>
          <div className={`${cardCls} overflow-x-auto`}>
            <table className="w-full min-w-[680px] text-left text-sm">
              <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th scope="col" className="px-4 py-3">Donor</th>
                  <th scope="col" className="px-4 py-3">Contact</th>
                  <th scope="col" className="px-4 py-3">PAN</th>
                  <th scope="col" className="px-4 py-3 text-right">Gifts</th>
                  <th scope="col" className="px-4 py-3 text-right">Total</th>
                  <th scope="col" className="px-4 py-3"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {list.data.items.map((d) => (
                  <tr key={d.id}>
                    <td className="px-4 py-3 font-medium text-gray-900">{d.name}</td>
                    <td className="px-4 py-3 text-gray-600">
                      {d.phone ?? '—'}
                      {d.email && <div className="text-xs text-gray-400">{d.email}</div>}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-600">{d.pan_number ?? '—'}</td>
                    <td className="px-4 py-3 text-right">
                      <Link className="text-red-900 hover:underline" href={`/admin/donations?donor=${d.id}`}>{d.donation_count}</Link>
                    </td>
                    <td className="px-4 py-3 text-right font-medium">{formatMoney(d.total_donated)}</td>
                    <td className="px-4 py-3">
                      {canWrite && (
                        <div className="flex justify-end gap-2">
                          <button type="button" className={btnGhost} onClick={() => openEdit(d)} aria-label={`Edit ${d.name}`}>
                            <Pencil className="h-4 w-4" />
                          </button>
                          <button type="button" className={btnDanger} onClick={() => setToDelete(d)} aria-label={`Deactivate ${d.name}`}>
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
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
        <Modal title={editing.id === null ? 'Add donor' : 'Edit donor'} onClose={() => { setEditing(null); action.clear(); }}>
          <form onSubmit={save} className="space-y-4">
            {action.error && <Notice kind="error">{action.error}</Notice>}
            <Field label="Full name" required>
              <input className={inputCls} maxLength={150} value={editing.form.name} onChange={(e) => set('name', e.target.value)} />
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Phone">
                <input type="tel" className={inputCls} value={editing.form.phone} onChange={(e) => set('phone', e.target.value)} />
              </Field>
              <Field label="Email">
                <input type="email" className={inputCls} value={editing.form.email} onChange={(e) => set('email', e.target.value)} />
              </Field>
            </div>
            <Field label="PAN" hint="Needed for 80G tax receipts. Format: ABCDE1234F">
              <input className={`${inputCls} uppercase`} maxLength={10} value={editing.form.pan_number} onChange={(e) => set('pan_number', e.target.value)} />
            </Field>
            <Field label="Address">
              <textarea className={inputCls} rows={2} maxLength={1000} value={editing.form.address} onChange={(e) => set('address', e.target.value)} />
            </Field>
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
          title="Deactivate donor?"
          message={`${toDelete.name} will be hidden from this list. Their donation history and receipts are kept.`}
          confirmLabel="Deactivate"
          danger
          busy={action.busy}
          onConfirm={remove}
          onCancel={() => { setToDelete(null); action.clear(); }}
        />
      )}
    </AdminPage>
  );
}
