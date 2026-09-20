'use client';

import React, { useState } from 'react';
import { Mail, Trash2 } from 'lucide-react';
import AdminPage from '@/components/admin/AdminPage';
import ConfirmDialog from '@/components/admin/ConfirmDialog';
import Field from '@/components/ui/Field';
import Modal from '@/components/ui/Modal';
import Pager from '@/components/ui/Pager';
import { EmptyBlock, ErrorBlock, LoadingBlock, Notice } from '@/components/ui/States';
import { btnDanger, btnGhost, btnPrimary, cardCls, inputCls } from '@/components/ui/styles';
import { useAction } from '@/hooks/useAction';
import { useLoad } from '@/hooks/useLoad';
import { deleteMessage, listMessages, updateMessage } from '@/lib/api';
import { formatDateTime } from '@/lib/format';
import type { ContactMessage, ContactStatus } from '@/lib/types';

const PAGE_SIZE = 20;
const STATUSES: Array<{ value: ContactStatus; label: string; cls: string }> = [
  { value: 'PENDING', label: 'New', cls: 'bg-amber-100 text-amber-800' },
  { value: 'IN_PROGRESS', label: 'In progress', cls: 'bg-blue-100 text-blue-800' },
  { value: 'RESOLVED', label: 'Resolved', cls: 'bg-green-100 text-green-800' },
  { value: 'REJECTED', label: 'Closed', cls: 'bg-gray-100 text-gray-600' },
];
const statusOf = (s: ContactStatus) => STATUSES.find((x) => x.value === s)!;

export default function MessagesAdmin() {
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState<ContactStatus | ''>('');
  const list = useLoad(() => listMessages(page, filter || undefined, PAGE_SIZE), [page, filter]);
  const action = useAction();
  const [open, setOpen] = useState<ContactMessage | null>(null);
  const [notes, setNotes] = useState('');
  const [toDelete, setToDelete] = useState<ContactMessage | null>(null);

  const openMessage = (m: ContactMessage) => {
    setOpen(m);
    setNotes(m.admin_notes ?? '');
  };

  async function setStatus(status: ContactStatus) {
    if (!open) return;
    const updated = await action.run(() => updateMessage(open.id, { status, admin_notes: notes }), 'Message updated.');
    if (updated) {
      setOpen(updated);
      list.reload();
    }
  }

  async function remove() {
    if (!toDelete) return;
    const ok = await action.run(() => deleteMessage(toDelete.id), 'Message deleted.');
    if (ok) {
      setToDelete(null);
      setOpen(null);
      list.reload();
    }
  }

  return (
    <AdminPage title="Messages" description="Messages sent through the website's Contact form.">
      <div className="mb-4 flex flex-wrap gap-2" role="group" aria-label="Filter by status">
        {[{ value: '' as const, label: 'All' }, ...STATUSES].map((s) => (
          <button
            key={s.value || 'all'}
            type="button"
            aria-pressed={filter === s.value}
            onClick={() => { setPage(1); setFilter(s.value); }}
            className={`rounded-full border px-3 py-1 text-sm ${filter === s.value ? 'border-red-900 bg-red-900 text-white' : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'}`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {action.error && !open && <div className="mb-4"><Notice kind="error">{action.error}</Notice></div>}

      {list.loading ? (
        <LoadingBlock />
      ) : list.error ? (
        <ErrorBlock message={list.error} onRetry={list.reload} />
      ) : !list.data?.items.length ? (
        <EmptyBlock icon={<Mail className="h-10 w-10" />} title="No messages" hint={filter ? 'Nothing with this status.' : 'Messages from devotees will appear here.'} />
      ) : (
        <>
          <ul className="space-y-2">
            {list.data.items.map((m) => (
              <li key={m.id}>
                <button type="button" onClick={() => openMessage(m)} className={`${cardCls} block w-full p-4 text-left transition hover:border-amber-400`}>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-semibold text-gray-900">{m.subject}</span>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusOf(m.status).cls}`}>{statusOf(m.status).label}</span>
                  </div>
                  <p className="mt-1 line-clamp-1 text-sm text-gray-600">{m.message}</p>
                  <p className="mt-1 text-xs text-gray-400">{m.name} · {m.email} · {formatDateTime(m.created_at)}</p>
                </button>
              </li>
            ))}
          </ul>
          <Pager page={page} pageSize={PAGE_SIZE} total={list.data.total} onPage={setPage} />
        </>
      )}

      {open && (
        <Modal title={open.subject} onClose={() => { setOpen(null); action.clear(); }} wide>
          <div className="space-y-4">
            {action.error && <Notice kind="error">{action.error}</Notice>}
            {action.success && <Notice kind="success">{action.success}</Notice>}
            <p className="text-sm text-gray-500">
              From <strong className="text-gray-800">{open.name}</strong> ·{' '}
              <a className="text-red-900 underline" href={`mailto:${open.email}?subject=${encodeURIComponent(`Re: ${open.subject}`)}`}>{open.email}</a> · {formatDateTime(open.created_at)}
            </p>
            <p className="whitespace-pre-wrap rounded-lg bg-gray-50 p-4 text-sm text-gray-800">{open.message}</p>
            <Field label="Internal notes" hint="Only staff can see these.">
              <textarea className={inputCls} rows={3} maxLength={5000} value={notes} onChange={(e) => setNotes(e.target.value)} />
            </Field>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap gap-2">
                {STATUSES.map((s) => (
                  <button key={s.value} type="button" disabled={action.busy} className={open.status === s.value ? btnPrimary : btnGhost} onClick={() => setStatus(s.value)}>
                    {s.label}
                  </button>
                ))}
              </div>
              <button type="button" className={btnDanger} onClick={() => setToDelete(open)}>
                <Trash2 className="h-4 w-4" aria-hidden="true" /> Delete
              </button>
            </div>
          </div>
        </Modal>
      )}

      {toDelete && (
        <ConfirmDialog
          title="Delete message?"
          message="This permanently deletes the message and your notes."
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
