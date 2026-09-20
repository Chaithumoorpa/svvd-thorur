'use client';

import React, { useState } from 'react';
import { ArrowDownCircle, ArrowUpCircle, FileDown, Plus } from 'lucide-react';
import AdminPage from '@/components/admin/AdminPage';
import { useAuth } from '@/components/admin/AuthContext';
import Field from '@/components/ui/Field';
import Modal from '@/components/ui/Modal';
import Pager from '@/components/ui/Pager';
import { EmptyBlock, ErrorBlock, LoadingBlock, Notice } from '@/components/ui/States';
import { btnGhost, btnPrimary, cardCls, inputCls } from '@/components/ui/styles';
import { useAction } from '@/hooks/useAction';
import { useLoad } from '@/hooks/useLoad';
import { addExpense, addIncome, exportLedger, getFinanceSummary, getLedger, getMonthlyReportPdf, saveBlob } from '@/lib/api';
import { emptyToNull, formatDate, formatMoney, todayISO } from '@/lib/format';
import type { ExpenseCategory, IncomeSource, PaymentMode } from '@/lib/types';

const PAGE_SIZE = 25;
const MODES: PaymentMode[] = ['CASH', 'UPI', 'BANK', 'CHEQUE'];
const SOURCES: IncomeSource[] = ['HUNDI', 'SEVA', 'DONATION', 'MANUAL'];
const CATEGORIES: ExpenseCategory[] = ['SALARY', 'MATERIAL', 'MAINTENANCE', 'FESTIVAL', 'OTHER'];
const label = (v: string) => v.charAt(0) + v.slice(1).toLowerCase();

export default function FinanceAdmin() {
  const { can } = useAuth();
  const canWrite = can('finance:write');
  const [page, setPage] = useState(1);
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const summary = useLoad(getFinanceSummary, []);
  const ledger = useLoad(() => getLedger(page, start, end, PAGE_SIZE), [page, start, end]);
  const action = useAction();
  const [modal, setModal] = useState<'income' | 'expense' | null>(null);
  const [income, setIncome] = useState({ source_type: 'HUNDI' as IncomeSource, amount: '', payment_mode: 'CASH' as PaymentMode, notes: '' });
  const [expense, setExpense] = useState({ category: 'MATERIAL' as ExpenseCategory, description: '', amount: '', payment_mode: 'CASH' as PaymentMode, paid_to: '', expense_date: todayISO(), notes: '' });
  const [reportMonth, setReportMonth] = useState(todayISO().slice(0, 7));

  const refresh = () => {
    summary.reload();
    ledger.reload();
  };

  async function submitIncome(e: React.FormEvent) {
    e.preventDefault();
    const ok = await action.run(
      () => addIncome({ source_type: income.source_type, amount: Number(income.amount), payment_mode: income.payment_mode, notes: emptyToNull(income.notes) }),
      'Income recorded.',
    );
    if (ok) {
      setModal(null);
      setIncome({ ...income, amount: '', notes: '' });
      setPage(1);
      refresh();
    }
  }

  async function submitExpense(e: React.FormEvent) {
    e.preventDefault();
    const ok = await action.run(
      () => addExpense({ category: expense.category, description: expense.description.trim(), amount: Number(expense.amount), payment_mode: expense.payment_mode, paid_to: expense.paid_to.trim(), expense_date: expense.expense_date, notes: emptyToNull(expense.notes) }),
      'Expense recorded.',
    );
    if (ok) {
      setModal(null);
      setExpense({ ...expense, description: '', amount: '', paid_to: '', notes: '' });
      setPage(1);
      refresh();
    }
  }

  async function download(kind: 'csv' | 'pdf') {
    if (!start || !end) return action.setError('Choose both a start and an end date to export.');
    const blob = await action.run(() => exportLedger(kind, start, end));
    if (blob) saveBlob(blob, `ledger_${start}_${end}.${kind}`);
  }

  async function monthly() {
    const [y, m] = reportMonth.split('-').map(Number);
    const blob = await action.run(() => getMonthlyReportPdf(y, m));
    if (blob) saveBlob(blob, `finance_report_${reportMonth}.pdf`);
  }

  const s = summary.data;
  return (
    <AdminPage
      title="Finance"
      description="Income, expenses and the temple ledger. Donations recorded under Donations appear here automatically."
      actions={
        canWrite && (
          <>
            <button type="button" className={btnGhost} onClick={() => { action.clear(); setModal('expense'); }}>
              <ArrowUpCircle className="h-4 w-4 text-red-700" aria-hidden="true" /> Add expense
            </button>
            <button type="button" className={btnPrimary} onClick={() => { action.clear(); setModal('income'); }}>
              <Plus className="h-4 w-4" aria-hidden="true" /> Add income
            </button>
          </>
        )
      }
    >
      {summary.loading ? (
        <LoadingBlock />
      ) : summary.error || !s ? (
        <ErrorBlock message={summary.error ?? 'No data'} onRetry={summary.reload} />
      ) : (
        <>
          <section aria-label="Totals" className="grid gap-3 sm:grid-cols-3">
            <div className={`${cardCls} p-4`}><p className="text-sm text-gray-500">Total income</p><p className="text-2xl font-bold text-green-700">{formatMoney(s.total_income)}</p></div>
            <div className={`${cardCls} p-4`}><p className="text-sm text-gray-500">Total expenses</p><p className="text-2xl font-bold text-red-700">{formatMoney(s.total_expenses)}</p></div>
            <div className={`${cardCls} p-4`}><p className="text-sm text-gray-500">Balance</p><p className={`text-2xl font-bold ${s.balance < 0 ? 'text-red-700' : 'text-gray-900'}`}>{formatMoney(s.balance)}</p></div>
          </section>
          <section className="mt-3 grid gap-3 md:grid-cols-2">
            <div className={`${cardCls} p-4`}>
              <h2 className="mb-2 text-sm font-semibold text-gray-700">Income by source</h2>
              {Object.keys(s.income_by_source).length === 0 ? <p className="text-sm text-gray-400">Nothing yet.</p> : (
                <dl className="space-y-1 text-sm">{Object.entries(s.income_by_source).map(([k, v]) => <div key={k} className="flex justify-between"><dt className="text-gray-600">{label(k)}</dt><dd className="font-medium">{formatMoney(v)}</dd></div>)}</dl>
              )}
            </div>
            <div className={`${cardCls} p-4`}>
              <h2 className="mb-2 text-sm font-semibold text-gray-700">Expenses by category</h2>
              {Object.keys(s.expense_by_category).length === 0 ? <p className="text-sm text-gray-400">Nothing yet.</p> : (
                <dl className="space-y-1 text-sm">{Object.entries(s.expense_by_category).map(([k, v]) => <div key={k} className="flex justify-between"><dt className="text-gray-600">{label(k)}</dt><dd className="font-medium">{formatMoney(v)}</dd></div>)}</dl>
              )}
            </div>
          </section>
        </>
      )}

      <section className="mt-8" aria-labelledby="ledger-heading">
        <h2 id="ledger-heading" className="mb-3 text-lg font-semibold text-gray-900">Ledger</h2>
        <div className="mb-3 flex flex-wrap items-end gap-3">
          <Field label="From"><input type="date" className={inputCls} value={start} onChange={(e) => { setPage(1); setStart(e.target.value); }} /></Field>
          <Field label="To"><input type="date" className={inputCls} min={start || undefined} value={end} onChange={(e) => { setPage(1); setEnd(e.target.value); }} /></Field>
          <button type="button" className={btnGhost} onClick={() => download('csv')} disabled={action.busy}><FileDown className="h-4 w-4" aria-hidden="true" /> CSV</button>
          <button type="button" className={btnGhost} onClick={() => download('pdf')} disabled={action.busy}><FileDown className="h-4 w-4" aria-hidden="true" /> PDF</button>
          <div className="ml-auto flex items-end gap-2">
            <Field label="Monthly report"><input type="month" className={inputCls} value={reportMonth} onChange={(e) => setReportMonth(e.target.value)} /></Field>
            <button type="button" className={btnGhost} onClick={monthly} disabled={action.busy || !reportMonth}><FileDown className="h-4 w-4" aria-hidden="true" /> PDF</button>
          </div>
        </div>

        {action.success && <div className="mb-3"><Notice kind="success">{action.success}</Notice></div>}
        {action.error && !modal && <div className="mb-3"><Notice kind="error">{action.error}</Notice></div>}

        {ledger.loading ? (
          <LoadingBlock />
        ) : ledger.error ? (
          <ErrorBlock message={ledger.error} onRetry={ledger.reload} />
        ) : !ledger.data?.items.length ? (
          <EmptyBlock title="No transactions" hint="Recorded income and expenses will appear here." />
        ) : (
          <>
            <div className={`${cardCls} overflow-x-auto`}>
              <table className="w-full min-w-[640px] text-left text-sm">
                <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-500">
                  <tr>
                    <th scope="col" className="px-4 py-3">Date</th>
                    <th scope="col" className="px-4 py-3">Details</th>
                    <th scope="col" className="px-4 py-3">Mode</th>
                    <th scope="col" className="px-4 py-3 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {ledger.data.items.map((e) => (
                    <tr key={`${e.type}-${e.id}`}>
                      <td className="px-4 py-3 text-gray-600">{formatDate(e.date)}</td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center gap-1 font-medium text-gray-900">
                          {e.type === 'INCOME' ? <ArrowDownCircle className="h-4 w-4 text-green-600" aria-label="Income" /> : <ArrowUpCircle className="h-4 w-4 text-red-600" aria-label="Expense" />}
                          {label(e.category_or_source)}
                        </span>
                        <div className="text-xs text-gray-500">{e.description}</div>
                      </td>
                      <td className="px-4 py-3 text-gray-600">{e.payment_mode}</td>
                      <td className={`px-4 py-3 text-right font-medium ${e.amount < 0 ? 'text-red-700' : 'text-green-700'}`}>{formatMoney(e.amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pager page={page} pageSize={PAGE_SIZE} total={ledger.data.total} onPage={setPage} />
          </>
        )}
      </section>

      {modal === 'income' && (
        <Modal title="Add income" onClose={() => setModal(null)}>
          <form onSubmit={submitIncome} className="space-y-4">
            {action.error && <Notice kind="error">{action.error}</Notice>}
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Source"><select className={inputCls} value={income.source_type} onChange={(e) => setIncome({ ...income, source_type: e.target.value as IncomeSource })}>{SOURCES.map((x) => <option key={x} value={x}>{label(x)}</option>)}</select></Field>
              <Field label="Payment mode"><select className={inputCls} value={income.payment_mode} onChange={(e) => setIncome({ ...income, payment_mode: e.target.value as PaymentMode })}>{MODES.map((x) => <option key={x} value={x}>{x}</option>)}</select></Field>
              <Field label="Amount (₹)" required className="sm:col-span-2"><input type="number" min="0.01" step="0.01" inputMode="decimal" className={inputCls} value={income.amount} onChange={(e) => setIncome({ ...income, amount: e.target.value })} /></Field>
            </div>
            <Field label="Notes"><input className={inputCls} maxLength={2000} value={income.notes} onChange={(e) => setIncome({ ...income, notes: e.target.value })} /></Field>
            <p className="text-xs text-gray-500">Donations from named donors are better recorded under Donations, which also creates a receipt.</p>
            <div className="flex justify-end gap-2"><button type="button" className={btnGhost} onClick={() => setModal(null)}>Cancel</button><button type="submit" className={btnPrimary} disabled={action.busy || !(Number(income.amount) > 0)}>{action.busy ? 'Saving…' : 'Save income'}</button></div>
          </form>
        </Modal>
      )}

      {modal === 'expense' && (
        <Modal title="Add expense" onClose={() => setModal(null)}>
          <form onSubmit={submitExpense} className="space-y-4">
            {action.error && <Notice kind="error">{action.error}</Notice>}
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Category"><select className={inputCls} value={expense.category} onChange={(e) => setExpense({ ...expense, category: e.target.value as ExpenseCategory })}>{CATEGORIES.map((x) => <option key={x} value={x}>{label(x)}</option>)}</select></Field>
              <Field label="Payment mode"><select className={inputCls} value={expense.payment_mode} onChange={(e) => setExpense({ ...expense, payment_mode: e.target.value as PaymentMode })}>{MODES.map((x) => <option key={x} value={x}>{x}</option>)}</select></Field>
              <Field label="Amount (₹)" required><input type="number" min="0.01" step="0.01" inputMode="decimal" className={inputCls} value={expense.amount} onChange={(e) => setExpense({ ...expense, amount: e.target.value })} /></Field>
              <Field label="Date" required><input type="date" className={inputCls} max={todayISO()} value={expense.expense_date} onChange={(e) => setExpense({ ...expense, expense_date: e.target.value })} /></Field>
            </div>
            <Field label="Description" required><input className={inputCls} maxLength={255} value={expense.description} onChange={(e) => setExpense({ ...expense, description: e.target.value })} /></Field>
            <Field label="Paid to" required><input className={inputCls} maxLength={255} value={expense.paid_to} onChange={(e) => setExpense({ ...expense, paid_to: e.target.value })} /></Field>
            <Field label="Notes"><input className={inputCls} maxLength={2000} value={expense.notes} onChange={(e) => setExpense({ ...expense, notes: e.target.value })} /></Field>
            <div className="flex justify-end gap-2"><button type="button" className={btnGhost} onClick={() => setModal(null)}>Cancel</button><button type="submit" className={btnPrimary} disabled={action.busy || !(Number(expense.amount) > 0) || expense.description.trim().length < 2 || expense.paid_to.trim().length < 2}>{action.busy ? 'Saving…' : 'Save expense'}</button></div>
          </form>
        </Modal>
      )}
    </AdminPage>
  );
}
