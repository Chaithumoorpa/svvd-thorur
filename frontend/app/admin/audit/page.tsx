'use client';

import React, { useState } from 'react';
import { History } from 'lucide-react';
import AdminPage from '@/components/admin/AdminPage';
import Field from '@/components/ui/Field';
import Pager from '@/components/ui/Pager';
import { EmptyBlock, ErrorBlock, LoadingBlock } from '@/components/ui/States';
import { cardCls, inputCls } from '@/components/ui/styles';
import { useLoad } from '@/hooks/useLoad';
import { listAuditLogs } from '@/lib/api';
import { formatDateTime } from '@/lib/format';

const PAGE_SIZE = 50;
const ENTITIES = ['announcement', 'festival', 'pooja', 'gallery', 'member', 'donor', 'donation', 'income', 'expense', 'temple', 'temple_timing', 'seva_ticket', 'contact_message', 'user'];
const ACTION_CLS: Record<string, string> = {
  CREATE: 'bg-green-100 text-green-800',
  UPDATE: 'bg-blue-100 text-blue-800',
  DELETE: 'bg-red-100 text-red-700',
};

export default function AuditAdmin() {
  const [page, setPage] = useState(1);
  const [entity, setEntity] = useState('');
  const list = useLoad(() => listAuditLogs(page, { entity_type: entity || undefined }, PAGE_SIZE), [page, entity]);

  return (
    <AdminPage title="Audit Log" description="A permanent record of who changed what. Entries cannot be edited or deleted.">
      <div className="mb-4 max-w-xs">
        <Field label="Show">
          <select className={inputCls} value={entity} onChange={(e) => { setPage(1); setEntity(e.target.value); }}>
            <option value="">Everything</option>
            {ENTITIES.map((x) => <option key={x} value={x}>{x.replace(/_/g, ' ')}</option>)}
          </select>
        </Field>
      </div>

      {list.loading ? (
        <LoadingBlock />
      ) : list.error ? (
        <ErrorBlock message={list.error} onRetry={list.reload} />
      ) : !list.data?.items.length ? (
        <EmptyBlock icon={<History className="h-10 w-10" />} title="No activity recorded" />
      ) : (
        <>
          <div className={`${cardCls} overflow-x-auto`}>
            <table className="w-full min-w-[680px] text-left text-sm">
              <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th scope="col" className="px-4 py-3">When</th>
                  <th scope="col" className="px-4 py-3">Who</th>
                  <th scope="col" className="px-4 py-3">Action</th>
                  <th scope="col" className="px-4 py-3">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {list.data.items.map((l) => (
                  <tr key={l.id}>
                    <td className="whitespace-nowrap px-4 py-3 text-gray-600">{formatDateTime(l.created_at)}</td>
                    <td className="px-4 py-3 text-gray-900">{l.actor_username ?? 'system'}{l.ip_address && <div className="text-xs text-gray-400">{l.ip_address}</div>}</td>
                    <td className="px-4 py-3"><span className={`rounded-full px-2 py-0.5 text-xs font-medium ${ACTION_CLS[l.action] ?? 'bg-gray-100 text-gray-700'}`}>{l.action.toLowerCase()}</span></td>
                    <td className="px-4 py-3 text-gray-700">{l.summary ?? `${l.entity_type} ${l.entity_id ?? ''}`}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pager page={page} pageSize={PAGE_SIZE} total={list.data.total} onPage={setPage} />
        </>
      )}
    </AdminPage>
  );
}
