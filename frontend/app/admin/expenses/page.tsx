'use client';

import React, { useEffect, useState } from 'react';
import { Ban, Check, Copy, FileText, Paperclip, Pencil, Plus, Save, X } from 'lucide-react';
import AdminPage from '@/components/admin/AdminPage';
import { useAuth } from '@/components/admin/AuthContext';
import Field from '@/components/ui/Field';
import Modal from '@/components/ui/Modal';
import Pager from '@/components/ui/Pager';
import { EmptyBlock, ErrorBlock, LoadingBlock, Notice } from '@/components/ui/States';
import { btnDanger, btnGhost, btnPrimary, cardCls, inputCls } from '@/components/ui/styles';
import { useAction } from '@/hooks/useAction';
import { useLoad } from '@/hooks/useLoad';
import {
  approveExpense, copyBudgets, createExpense, getBudgetStatus, getExpenseBill, getFestivals, listExpenses,
  rejectExpense, setBudgets, updateExpense, uploadExpenseBill, voidExpense,
} from '@/lib/api';
import { photoUploadErrorMessage } from '@/lib/imageUpload';
import { emptyToNull, formatDate, formatMoney, todayISO } from '@/lib/format';
import { EXPENSE_CATEGORIES, EXPENSE_CATEGORY_KEYS, EXPENSE_STATUS, shortCategory } from '@/lib/labels';
import type { Expense, ExpenseCategory, ExpenseStatus, PaymentMode } from '@/lib/types';

const PAGE_SIZE = 25;
const MODES: PaymentMode[] = ['CASH', 'UPI', 'BANK', 'CHEQUE'];

type Form = {
  category: ExpenseCategory; description: string; amount: string; payment_mode: PaymentMode; paid_to: string;
  expense_date: string; notes: string; festival_id: string; bill_key: string | null; bill_name: string; reason: string;
};
const blankForm = (): Form => ({
  category: 'POOJA_SUPPLIES', description: '', amount: '', payment_mode: 'CASH', paid_to: '', expense_date: todayISO(),
  notes: '', festival_id: '', bill_key: null, bill_name: '', reason: '',
});
const fromExpense = (e: Expense): Form => ({
  category: e.category, description: e.description, amount: String(e.amount), payment_mode: e.payment_mode,
  paid_to: e.paid_to, expense_date: e.expense_date, notes: e.notes ?? '', festival_id: e.festival_id ? String(e.festival_id) : '',
  bill_key: null, bill_name: e.has_bill ? 'Bill attached' : '', reason: '',
});

const previousMonth = (m: string) => {
  const [y, mo] = m.split('-').map(Number);
  return mo === 1 ? `${y - 1}-12` : `${y}-${String(mo - 1).padStart(2, '0')}`;
};

export default function ExpensesAdmin() {
  const { me, can } = useAuth();
  const approver = can('finance:write');
  const seesAll = can('finance:read');
  const canSubmit = can('expenses:submit') || approver;
  const [tab, setTab] = useState<'list' | 'budgets'>('list');
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<ExpenseStatus | ''>(approver ? 'PENDING' : '');
  const [category, setCategory] = useState<ExpenseCategory | ''>('');
  const [q, setQ] = useState('');
  const expenses = useLoad(
    () => listExpenses(page, { status: status || undefined, category: category || undefined, q: q.trim() || undefined }, PAGE_SIZE),
    [page, status, category, q],
  );
  const festivals = useLoad(() => getFestivals(), []);
  const action = useAction();

  const [editing, setEditing] = useState<Expense | 'new' | null>(null);
  const [form, setForm] = useState<Form>(blankForm);
  const [uploading, setUploading] = useState(false);
  const [decision, setDecision] = useState<{ expense: Expense; kind: 'reject' | 'void' } | null>(null);
  const [reason, setReason] = useState('');

  // /admin/expenses?new=1 (the Finance page's "Add expense") opens the form straight away.
  useEffect(() => {
    if (canSubmit && new URLSearchParams(window.location.search).get('new') === '1') {
      setForm(blankForm());
      setEditing('new');
    }
  }, [canSubmit]);

  const openNew = () => { action.clear(); setForm(blankForm()); setEditing('new'); };
  const openEdit = (e: Expense) => { action.clear(); setForm(fromExpense(e)); setEditing(e); };
  const editable = (e: Expense) =>
    (e.status === 'PENDING' && (approver || e.submitted_by === me.id)) || (e.status === 'APPROVED' && approver);

  async function attachBill(ev: React.ChangeEvent<HTMLInputElement>) {
    const file = ev.target.files?.[0];
    ev.target.value = '';
    if (!file) return;
    setUploading(true);
    action.clear();
    try {
      const key = await uploadExpenseBill(file);
      setForm((f) => ({ ...f, bill_key: key, bill_name: file.name }));
    } catch (err) {
      action.setError(photoUploadErrorMessage(err, 'Bill uploads are not set up yet. You can save without one.'));
    } finally {
      setUploading(false);
    }
  }

  async function save(ev: React.FormEvent) {
    ev.preventDefault();
    const base = {
      category: form.category, description: form.description.trim(), amount: Number(form.amount),
      payment_mode: form.payment_mode, paid_to: form.paid_to.trim(), expense_date: form.expense_date,
      notes: emptyToNull(form.notes), festival_id: form.festival_id ? Number(form.festival_id) : null,
    };
    const ok = editing === 'new'
      ? await action.run(() => createExpense({ ...base, bill_key: form.bill_key }),
          approver ? 'Expense recorded.' : 'Expense submitted - an admin will approve it.')
      : editing && await action.run(() => updateExpense(editing.id, {
          ...base, ...(form.bill_key ? { bill_key: form.bill_key } : {}), reason: emptyToNull(form.reason),
        }), 'Expense updated.');
    if (ok) {
      setEditing(null);
      expenses.reload();
    }
  }

  async function approve(e: Expense) {
    if (await action.run(() => approveExpense(e.id), `Approved ${formatMoney(e.amount)} - ${e.description}.`)) expenses.reload();
  }

  async function decide(ev: React.FormEvent) {
    ev.preventDefault();
    if (!decision) return;
    const { expense, kind } = decision;
    const ok = await action.run(
      () => (kind === 'reject' ? rejectExpense(expense.id, reason.trim()) : voidExpense(expense.id, reason.trim())),
      kind === 'reject' ? 'Expense rejected.' : 'Expense voided.',
    );
    if (ok) {
      setDecision(null);
      setReason('');
      expenses.reload();
    }
  }

  async function viewBill(e: Expense) {
    const link = await action.run(() => getExpenseBill(e.id));
    if (link) window.open(link.url, '_blank', 'noopener');
  }

  const correctingApproved = editing !== 'new' && editing?.status === 'APPROVED';
  const formValid = Number(form.amount) > 0 && form.description.trim().length >= 2 && form.paid_to.trim().length >= 2
    && !!form.expense_date && (!correctingApproved || form.reason.trim().length >= 3);

  return (
    <AdminPage
      title="Expenses"
      description={approver
        ? 'Every rupee spent: approve staff submissions, attach bills, correct or void entries, and keep to monthly budgets.'
        : 'Record what you spend for the temple. An admin approves each expense before it counts in the accounts.'}
      actions={canSubmit && (
        <button type="button" className={btnPrimary} onClick={openNew}>
          <Plus className="h-4 w-4" aria-hidden="true" /> {approver ? 'Add expense' : 'Submit expense'}
        </button>
      )}
    >
      {seesAll && (
        <div role="tablist" className="mb-4 flex gap-1 border-b border-gray-200">
          {(['list', 'budgets'] as const).map((t) => (
            <button key={t} type="button" role="tab" aria-selected={tab === t} onClick={() => setTab(t)}
              className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium ${tab === t ? 'border-red-900 text-red-900' : 'border-transparent text-gray-500 hover:text-gray-800'}`}>
              {t === 'list' ? 'Expenses' : 'Monthly budgets'}
            </button>
          ))}
        </div>
      )}

      {action.success && <div className="mb-3"><Notice kind="success">{action.success}</Notice></div>}
      {action.error && !editing && !decision && <div className="mb-3"><Notice kind="error">{action.error}</Notice></div>}

      {tab === 'budgets' ? <Budgets canEdit={approver} /> : (
        <>
          <div className="mb-3 flex flex-wrap items-end gap-3">
            <Field label="Status">
              <select className={inputCls} value={status} onChange={(e) => { setPage(1); setStatus(e.target.value as ExpenseStatus | ''); }}>
                <option value="">All</option>
                {(Object.keys(EXPENSE_STATUS) as ExpenseStatus[]).map((s) => <option key={s} value={s}>{EXPENSE_STATUS[s].label}</option>)}
              </select>
            </Field>
            <Field label="Category">
              <select className={inputCls} value={category} onChange={(e) => { setPage(1); setCategory(e.target.value as ExpenseCategory | ''); }}>
                <option value="">All</option>
                {EXPENSE_CATEGORY_KEYS.map((c) => <option key={c} value={c}>{shortCategory(c)}</option>)}
              </select>
            </Field>
            <Field label="Search">
              <input className={inputCls} placeholder="Description or paid to" value={q} onChange={(e) => { setPage(1); setQ(e.target.value); }} />
            </Field>
          </div>

          {expenses.loading ? <LoadingBlock /> : expenses.error ? <ErrorBlock message={expenses.error} onRetry={expenses.reload} /> :
            !expenses.data?.items.length ? (
              <EmptyBlock title={status === 'PENDING' ? 'Nothing waiting for approval' : 'No expenses'}
                hint={status === 'PENDING' ? 'Expenses staff submit will appear here.' : 'Recorded expenses will appear here.'} />
            ) : (
              <>
                <div className={`${cardCls} overflow-x-auto`}>
                  <table className="w-full min-w-[760px] text-left text-sm">
                    <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-500">
                      <tr>
                        <th scope="col" className="px-4 py-3">Date</th>
                        <th scope="col" className="px-4 py-3">Details</th>
                        <th scope="col" className="px-4 py-3">Status</th>
                        <th scope="col" className="px-4 py-3 text-right">Amount</th>
                        <th scope="col" className="px-4 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {expenses.data.items.map((e) => (
                        <tr key={e.id} className={e.status === 'VOID' || e.status === 'REJECTED' ? 'text-gray-400' : ''}>
                          <td className="whitespace-nowrap px-4 py-3 align-top text-gray-600">{formatDate(e.expense_date)}</td>
                          <td className="px-4 py-3 align-top">
                            <p className={`font-medium ${e.status === 'VOID' ? 'line-through' : 'text-gray-900'}`}>{e.description}</p>
                            <p className="text-xs text-gray-500">
                              {shortCategory(e.category)} · {e.paid_to} · {e.payment_mode}
                              {e.festival_name && <> · {e.festival_name}</>}
                              {e.inventory_item_id && <> · from inventory</>}
                            </p>
                            <p className="text-xs text-gray-400">
                              by {e.submitted_by_name ?? '?'}{e.approved_by_name && e.status !== 'PENDING' && e.approved_by_name !== e.submitted_by_name && <> · {e.status === 'REJECTED' ? 'rejected' : 'approved'} by {e.approved_by_name}</>}
                            </p>
                            {e.rejection_reason && <p className="text-xs text-red-700">Rejected: {e.rejection_reason}</p>}
                            {e.void_reason && <p className="text-xs text-gray-600">Voided: {e.void_reason}</p>}
                          </td>
                          <td className="px-4 py-3 align-top">
                            <span className={`inline-flex whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ${EXPENSE_STATUS[e.status].cls}`}>{EXPENSE_STATUS[e.status].label}</span>
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 text-right align-top font-semibold">{formatMoney(e.amount)}</td>
                          <td className="px-4 py-3 align-top">
                            <div className="flex flex-wrap justify-end gap-1">
                              {e.has_bill && (
                                <button type="button" className={btnGhost} onClick={() => viewBill(e)} title="View bill">
                                  <FileText className="h-4 w-4" aria-hidden="true" /><span className="sr-only">View bill</span>
                                </button>
                              )}
                              {approver && e.status === 'PENDING' && (
                                <>
                                  <button type="button" className={btnPrimary} onClick={() => approve(e)} disabled={action.busy}>
                                    <Check className="h-4 w-4" aria-hidden="true" /> Approve
                                  </button>
                                  <button type="button" className={btnDanger} onClick={() => { action.clear(); setReason(''); setDecision({ expense: e, kind: 'reject' }); }}>
                                    <X className="h-4 w-4" aria-hidden="true" /> Reject
                                  </button>
                                </>
                              )}
                              {editable(e) && (
                                <button type="button" className={btnGhost} onClick={() => openEdit(e)} title={e.status === 'APPROVED' ? 'Correct' : 'Edit'}>
                                  <Pencil className="h-4 w-4" aria-hidden="true" /><span className="sr-only">Edit</span>
                                </button>
                              )}
                              {approver && (e.status === 'APPROVED' || e.status === 'PENDING') && (
                                <button type="button" className={btnGhost} onClick={() => { action.clear(); setReason(''); setDecision({ expense: e, kind: 'void' }); }} title="Void">
                                  <Ban className="h-4 w-4" aria-hidden="true" /><span className="sr-only">Void</span>
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <Pager page={page} pageSize={PAGE_SIZE} total={expenses.data.total} onPage={setPage} />
              </>
            )}
        </>
      )}

      {editing && (
        <Modal title={editing === 'new' ? (approver ? 'Add expense' : 'Submit expense') : correctingApproved ? 'Correct approved expense' : 'Edit expense'} onClose={() => setEditing(null)} wide>
          <form onSubmit={save} className="space-y-4">
            {action.error && <Notice kind="error">{action.error}</Notice>}
            {editing === 'new' && !approver && <Notice kind="info">An admin will check and approve this before it counts in the accounts.</Notice>}
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Category" required>
                <select className={inputCls} value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value as ExpenseCategory })}>
                  {EXPENSE_CATEGORY_KEYS.map((c) => <option key={c} value={c}>{EXPENSE_CATEGORIES[c]}</option>)}
                </select>
              </Field>
              <Field label="Amount (₹)" required>
                <input type="number" min="0.01" step="0.01" inputMode="decimal" className={inputCls} value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
              </Field>
              <Field label="Date" required>
                <input type="date" className={inputCls} max={todayISO()} value={form.expense_date} onChange={(e) => setForm({ ...form, expense_date: e.target.value })} />
              </Field>
              <Field label="Paid by">
                <select className={inputCls} value={form.payment_mode} onChange={(e) => setForm({ ...form, payment_mode: e.target.value as PaymentMode })}>
                  {MODES.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              </Field>
              <Field label="What was it for?" required className="sm:col-span-2">
                <input className={inputCls} maxLength={255} placeholder="e.g. 5 kg ghee for deepam" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              </Field>
              <Field label="Paid to" required>
                <input className={inputCls} maxLength={255} placeholder="Shop / person" value={form.paid_to} onChange={(e) => setForm({ ...form, paid_to: e.target.value })} />
              </Field>
              <Field label="Festival (optional)" hint="Counts towards that festival's cost.">
                <select className={inputCls} value={form.festival_id} onChange={(e) => setForm({ ...form, festival_id: e.target.value })}>
                  <option value="">-</option>
                  {festivals.data?.map((f) => <option key={f.id} value={f.id}>{f.name}{f.festival_date ? ` (${formatDate(f.festival_date)})` : ''}</option>)}
                </select>
              </Field>
              <Field label="Notes" className="sm:col-span-2">
                <input className={inputCls} maxLength={2000} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
              </Field>
            </div>
            <div className="flex flex-wrap items-center gap-3 rounded-lg border border-dashed border-gray-300 p-3">
              <label className={`${btnGhost} cursor-pointer`}>
                <Paperclip className="h-4 w-4" aria-hidden="true" /> {uploading ? 'Uploading…' : form.bill_name ? 'Replace bill' : 'Attach bill (photo or PDF)'}
                <input type="file" accept="image/*,application/pdf" className="sr-only" onChange={attachBill} disabled={uploading} />
              </label>
              <span className="text-sm text-gray-600">{form.bill_name || 'No bill attached'}</span>
            </div>
            {correctingApproved && (
              <Field label="Reason for the correction" required hint="Kept in the audit log with the old and new values.">
                <input className={inputCls} maxLength={500} value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} />
              </Field>
            )}
            <div className="flex justify-end gap-2">
              <button type="button" className={btnGhost} onClick={() => setEditing(null)}>Cancel</button>
              <button type="submit" className={btnPrimary} disabled={action.busy || uploading || !formValid}>
                <Save className="h-4 w-4" aria-hidden="true" /> {action.busy ? 'Saving…' : editing === 'new' && !approver ? 'Submit for approval' : 'Save'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {decision && (
        <Modal title={decision.kind === 'reject' ? 'Reject expense' : 'Void expense'} onClose={() => setDecision(null)}>
          <form onSubmit={decide} className="space-y-4">
            {action.error && <Notice kind="error">{action.error}</Notice>}
            <p className="text-sm text-gray-700">
              <strong>{formatMoney(decision.expense.amount)}</strong> - {decision.expense.description} ({decision.expense.paid_to})
            </p>
            {decision.kind === 'void' && (
              <p className="text-sm text-gray-500">
                A voided expense stops counting in the accounts but stays on record with your reason.
                {decision.expense.inventory_item_id && ' The stock it bought is not changed - record a write-off if the goods went back.'}
              </p>
            )}
            <Field label="Reason" required>
              <input className={inputCls} maxLength={500} value={reason} onChange={(e) => setReason(e.target.value)}
                placeholder={decision.kind === 'reject' ? 'e.g. No bill, wrong amount' : 'e.g. Entered twice'} />
            </Field>
            <div className="flex justify-end gap-2">
              <button type="button" className={btnGhost} onClick={() => setDecision(null)}>Cancel</button>
              <button type="submit" className={btnDanger} disabled={action.busy || reason.trim().length < 3}>
                {action.busy ? 'Please wait…' : decision.kind === 'reject' ? 'Reject' : 'Void expense'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </AdminPage>
  );
}

function Budgets({ canEdit }: { canEdit: boolean }) {
  const [month, setMonth] = useState(todayISO().slice(0, 7));
  const status = useLoad(() => getBudgetStatus(month), [month]);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const action = useAction();

  useEffect(() => {
    if (status.data) {
      setDraft(Object.fromEntries(status.data.lines.filter((l) => l.budget !== null).map((l) => [l.category, String(l.budget)])));
    }
  }, [status.data]);

  const lineFor = (c: ExpenseCategory) => status.data?.lines.find((l) => l.category === c);
  const dirty = EXPENSE_CATEGORY_KEYS.some((c) => (draft[c] ?? '') !== (lineFor(c)?.budget != null ? String(lineFor(c)!.budget) : ''));

  async function save() {
    const lines = EXPENSE_CATEGORY_KEYS
      .filter((c) => (draft[c] ?? '') !== (lineFor(c)?.budget != null ? String(lineFor(c)!.budget) : ''))
      .map((c) => ({ category: c, amount: Number(draft[c] || 0) }));
    if (await action.run(() => setBudgets(month, lines), 'Budgets saved.')) status.reload();
  }

  async function copyPrevious() {
    const from = previousMonth(month);
    if (await action.run(() => copyBudgets(month, from), `Copied the budgets from ${from}.`)) status.reload();
  }

  const s = status.data;
  return (
    <section aria-label="Monthly budgets">
      <div className="mb-3 flex flex-wrap items-end gap-3">
        <Field label="Month"><input type="month" className={inputCls} value={month} onChange={(e) => e.target.value && setMonth(e.target.value)} /></Field>
        {canEdit && (
          <>
            <button type="button" className={btnGhost} onClick={copyPrevious} disabled={action.busy}>
              <Copy className="h-4 w-4" aria-hidden="true" /> Copy last month&apos;s budgets
            </button>
            <button type="button" className={btnPrimary} onClick={save} disabled={action.busy || !dirty}>
              <Save className="h-4 w-4" aria-hidden="true" /> Save budgets
            </button>
          </>
        )}
      </div>
      {action.success && <div className="mb-3"><Notice kind="success">{action.success}</Notice></div>}
      {action.error && <div className="mb-3"><Notice kind="error">{action.error}</Notice></div>}
      {status.loading ? <LoadingBlock /> : status.error || !s ? <ErrorBlock message={status.error ?? 'No data'} onRetry={status.reload} /> : (
        <>
          <div className="mb-3 grid gap-3 sm:grid-cols-3">
            <div className={`${cardCls} p-4`}><p className="text-sm text-gray-500">Budget</p><p className="text-2xl font-bold">{formatMoney(s.total_budget)}</p></div>
            <div className={`${cardCls} p-4`}><p className="text-sm text-gray-500">Spent (approved)</p><p className={`text-2xl font-bold ${s.total_budget && s.total_spent > s.total_budget ? 'text-red-700' : 'text-gray-900'}`}>{formatMoney(s.total_spent)}</p></div>
            <div className={`${cardCls} p-4`}><p className="text-sm text-gray-500">Awaiting approval</p><p className="text-2xl font-bold text-amber-700">{formatMoney(s.total_pending)}</p></div>
          </div>
          <div className={`${cardCls} overflow-x-auto`}>
            <table className="w-full min-w-[680px] text-left text-sm">
              <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th scope="col" className="px-4 py-3">Category</th>
                  <th scope="col" className="px-4 py-3">Budget (₹)</th>
                  <th scope="col" className="px-4 py-3 text-right">Spent</th>
                  <th scope="col" className="px-4 py-3 text-right">Pending</th>
                  <th scope="col" className="w-1/4 px-4 py-3">Used</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {EXPENSE_CATEGORY_KEYS.map((c) => {
                  const l = lineFor(c);
                  const pct = l?.percent_used ?? null;
                  return (
                    <tr key={c}>
                      <td className="px-4 py-2 font-medium text-gray-800">{shortCategory(c)}</td>
                      <td className="px-4 py-2">
                        {canEdit ? (
                          <input type="number" min="0" step="100" inputMode="decimal" aria-label={`${shortCategory(c)} budget`} className={`${inputCls} max-w-[9rem]`}
                            value={draft[c] ?? ''} placeholder="No budget" onChange={(e) => setDraft({ ...draft, [c]: e.target.value })} />
                        ) : (l?.budget != null ? formatMoney(l.budget) : <span className="text-gray-400">-</span>)}
                      </td>
                      <td className={`px-4 py-2 text-right ${l?.over_budget ? 'font-semibold text-red-700' : ''}`}>{formatMoney(l?.spent ?? 0)}</td>
                      <td className={`px-4 py-2 text-right ${l?.pending ? 'text-amber-700' : 'text-gray-400'}`}>{l?.pending ? formatMoney(l.pending) : '-'}</td>
                      <td className="px-4 py-2">
                        {pct !== null ? (
                          <div className="flex items-center gap-2">
                            <div className="h-2 flex-1 overflow-hidden rounded-full bg-gray-100" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label={`${shortCategory(c)} budget used`}>
                              <div className={`h-full rounded-full ${pct > 100 ? 'bg-red-600' : pct > 85 ? 'bg-amber-500' : 'bg-green-600'}`} style={{ width: `${Math.min(pct, 100)}%` }} />
                            </div>
                            <span className={`w-12 text-right text-xs ${pct > 100 ? 'font-semibold text-red-700' : 'text-gray-600'}`}>{pct}%</span>
                          </div>
                        ) : <span className="text-xs text-gray-400">-</span>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {canEdit && <p className="mt-2 text-xs text-gray-500">Leave a budget empty (or 0) for no limit. Pending expenses are shown but only approved ones count as spent.</p>}
        </>
      )}
    </section>
  );
}
