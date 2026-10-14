'use client';

import React, { useState } from 'react';
import { AlertTriangle, Moon } from 'lucide-react';
import AdminPage from '@/components/admin/AdminPage';
import { useAuth } from '@/components/admin/AuthContext';
import { BarList, ColumnChart, StatTile } from '@/components/admin/charts';
import { ErrorBlock, LoadingBlock } from '@/components/ui/States';
import { cardCls, inputCls } from '@/components/ui/styles';
import { useLoad } from '@/hooks/useLoad';
import {
  getAuditAnalytics, getFestivalCosts, getFinanceAnalytics, getInventoryAnalytics, getInventorySummary,
} from '@/lib/api';
import { formatMoney } from '@/lib/format';
import { formatQty, shortCategory } from '@/lib/labels';
import type { Permission } from '@/lib/types';

type Tab = 'finance' | 'inventory' | 'audit';
const TABS: Array<{ id: Tab; label: string; permission: Permission }> = [
  { id: 'finance', label: 'Finance', permission: 'finance:read' },
  { id: 'inventory', label: 'Inventory', permission: 'inventory:read' },
  { id: 'audit', label: 'Audit log', permission: 'audit:read' },
];
const MONTH_OPTIONS = [3, 6, 12, 24];
const DAY_OPTIONS = [7, 30, 90, 365];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const rupees = (n: number) => formatMoney(n).replace(/\.00$/, '');
/** Axis/tile money: ₹1.2L, ₹45K. */
const shortRupees = (n: number) =>
  Math.abs(n) >= 1e7 ? `₹${(n / 1e7).toFixed(1).replace(/\.0$/, '')}Cr`
    : Math.abs(n) >= 1e5 ? `₹${(n / 1e5).toFixed(1).replace(/\.0$/, '')}L`
      : Math.abs(n) >= 1e3 ? `₹${(n / 1e3).toFixed(1).replace(/\.0$/, '')}K` : `₹${Math.round(n)}`;
const monthLabel = (key: string) => {
  const [y, m] = key.split('-').map(Number);
  return m === 1 ? `${MONTHS[0]} ${String(y).slice(2)}` : MONTHS[m - 1];
};
const monthFull = (key: string) => {
  const [y, m] = key.split('-').map(Number);
  return `${MONTHS[m - 1]} ${y}`;
};
const pctChange = (now: number, before: number) => (before ? ((now - before) / Math.abs(before)) * 100 : null);
/** Audit times in IST - "late night" is judged in the temple's time zone, so show it there too. */
const istTime = (utc: string) =>
  new Date(utc.endsWith('Z') || utc.includes('+') ? utc : `${utc}Z`).toLocaleString('en-IN', {
    timeZone: 'Asia/Kolkata', day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit',
  });
const titleCase = (s: string) => s.replace(/_/g, ' ').toLowerCase().replace(/^./, (c) => c.toUpperCase());

function Card({ title, children, className = '' }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <section className={`${cardCls} p-4 ${className}`} aria-label={title}>
      <h2 className="mb-3 text-sm font-semibold text-gray-700">{title}</h2>
      {children}
    </section>
  );
}

export default function AnalyticsPage() {
  const { can } = useAuth();
  const tabs = TABS.filter((t) => can(t.permission));
  const [tab, setTab] = useState<Tab>(tabs[0]?.id ?? 'finance');
  const [months, setMonths] = useState(12);
  const [days, setDays] = useState(30);

  return (
    <AdminPage title="Analytics" description="Trends in the temple's money, stock and admin activity. Every chart can be shown as a table.">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3 border-b border-gray-200">
        <div role="tablist" className="flex gap-1">
          {tabs.map((t) => (
            <button key={t.id} type="button" role="tab" aria-selected={tab === t.id} onClick={() => setTab(t.id)}
              className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium ${tab === t.id ? 'border-red-900 text-red-900' : 'border-transparent text-gray-500 hover:text-gray-800'}`}>
              {t.label}
            </button>
          ))}
        </div>
        <label className="mb-2 flex items-center gap-2 text-sm text-gray-600">
          Period
          {tab === 'audit' ? (
            <select className={`${inputCls} w-auto`} value={days} onChange={(e) => setDays(Number(e.target.value))}>
              {DAY_OPTIONS.map((d) => <option key={d} value={d}>{d === 365 ? 'Last 12 months' : `Last ${d} days`}</option>)}
            </select>
          ) : (
            <select className={`${inputCls} w-auto`} value={months} onChange={(e) => setMonths(Number(e.target.value))}>
              {MONTH_OPTIONS.map((m) => <option key={m} value={m}>Last {m} months</option>)}
            </select>
          )}
        </label>
      </div>
      {tab === 'finance' && <FinanceTab months={months} />}
      {tab === 'inventory' && <InventoryTab months={months} />}
      {tab === 'audit' && <AuditTab days={days} />}
    </AdminPage>
  );
}

// ---------------------------------------------------------------------------- finance
function FinanceTab({ months }: { months: number }) {
  const data = useLoad(() => getFinanceAnalytics(months), [months]);
  if (data.loading && !data.data) return <LoadingBlock />;
  if (data.error || !data.data) return <ErrorBlock message={data.error ?? 'No data'} onRetry={data.reload} />;
  const d = data.data;
  return (
    <div className={`space-y-4 ${data.loading ? 'opacity-60' : ''}`}>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Income" value={rupees(d.totals.income)} delta={pctChange(d.totals.income, d.previous.income)} />
        <StatTile label="Expenses (approved)" value={rupees(d.totals.expenses)} delta={pctChange(d.totals.expenses, d.previous.expenses)} goodWhenUp={false} />
        <StatTile label={d.totals.net >= 0 ? 'Surplus' : 'Deficit'} value={rupees(Math.abs(d.totals.net))} delta={pctChange(d.totals.net, d.previous.net)} />
        <StatTile label="Donations" value={String(d.donations.count)} hint={d.donations.count ? `${rupees(d.donations.total)} from ${d.donations.donors} donor${d.donations.donors === 1 ? '' : 's'} · avg ${rupees(d.donations.average)}` : undefined} />
      </div>
      <Card title="Income and expenses by month">
        <ColumnChart
          title="Income and expenses by month"
          labels={d.months.map((m) => monthLabel(m.month))}
          fullLabels={d.months.map((m) => monthFull(m.month))}
          series={[{ name: 'Income', values: d.months.map((m) => m.income) }, { name: 'Expenses', values: d.months.map((m) => m.expenses) }]}
          format={shortRupees}
          tickEvery={months > 12 ? 3 : 1}
        />
      </Card>
      <div className="grid gap-4 md:grid-cols-2">
        <Card title="Where the money went">
          <BarList title="Expenses by category" format={rupees} rows={d.expense_by_category.map((r) => ({ label: shortCategory(r.name), value: r.amount }))} />
        </Card>
        <Card title="Where it came from">
          <BarList title="Income by source" format={rupees} rows={d.income_by_source.map((r) => ({ label: titleCase(r.name), value: r.amount }))} />
        </Card>
        <Card title="How income was paid">
          <BarList title="Income by payment mode" format={rupees} rows={d.payment_modes.map((r) => ({ label: r.mode, value: r.amount, note: `${r.count} payment${r.count === 1 ? '' : 's'}` }))} />
        </Card>
        <Card title="Paid to most">
          {d.top_payees.length ? (
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase text-gray-500"><tr><th scope="col" className="py-1">Payee</th><th scope="col" className="py-1 text-right">Bills</th><th scope="col" className="py-1 text-right">Total</th></tr></thead>
              <tbody className="divide-y divide-gray-100 tabular-nums">
                {d.top_payees.map((p) => <tr key={p.name}><td className="py-1.5 text-gray-800">{p.name}</td><td className="py-1.5 text-right text-gray-600">{p.count}</td><td className="py-1.5 text-right font-medium">{rupees(p.amount)}</td></tr>)}
              </tbody>
            </table>
          ) : <p className="py-6 text-center text-sm text-gray-400">No approved expenses in this period.</p>}
        </Card>
      </div>
    </div>
  );
}

// -------------------------------------------------------------------------- inventory
function InventoryTab({ months }: { months: number }) {
  const data = useLoad(() => getInventoryAnalytics(months), [months]);
  const summary = useLoad(getInventorySummary, []);
  const festivals = useLoad(getFestivalCosts, []);
  if (data.loading && !data.data) return <LoadingBlock />;
  if (data.error || !data.data) return <ErrorBlock message={data.error ?? 'No data'} onRetry={data.reload} />;
  const d = data.data;
  const s = summary.data;
  return (
    <div className={`space-y-4 ${data.loading ? 'opacity-60' : ''}`}>
      {s && (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatTile label="Stock value" value={rupees(s.stock_value)} hint={`${s.consumables} items at average cost`} />
          <StatTile label="Used in this period" value={rupees(d.consumption.reduce((t, m) => t + m.used, 0))} hint={`${rupees(d.consumption.reduce((t, m) => t + m.written_off, 0))} written off`} />
          <StatTile label="Valuables" value={rupees(s.valuables_value)} hint={`${s.valuables} items · ${s.valuables_unverified} not verified this year`} />
          <StatTile label="Donations in kind" value={String(d.consumption.reduce((t, m) => t + m.donated_in, 0))} hint="received in this period" />
        </div>
      )}
      <Card title="Stock used per month (value at average cost)">
        <ColumnChart
          title="Stock used per month"
          labels={d.consumption.map((m) => monthLabel(m.month))}
          fullLabels={d.consumption.map((m) => monthFull(m.month))}
          series={[{ name: 'Used', values: d.consumption.map((m) => m.used) }]}
          format={shortRupees}
          tickEvery={months > 12 ? 3 : 1}
        />
      </Card>
      <div className="grid gap-4 md:grid-cols-2">
        <Card title="Stock value by category">
          <BarList title="Stock value by category" format={rupees} rows={d.stock_by_category.map((r) => ({ label: r.name, value: r.amount }))} empty="No stock recorded yet." />
        </Card>
        <Card title="Most used items">
          <BarList title="Most used items" format={rupees} rows={d.top_used.map((r) => ({ label: r.item_name, value: r.value, note: `${formatQty(r.quantity)} ${r.unit}` }))} empty="Nothing used in this period." />
        </Card>
        <Card title="Festival costs" className="md:col-span-2">
          <BarList title="Festival costs" format={rupees}
            rows={(festivals.data ?? []).slice(0, 10).map((c) => ({ label: c.festival_name, value: c.total_cost, note: `${rupees(c.stock_used_value)} stock + ${rupees(c.expenses_total)} expenses` }))}
            empty="No festival costs yet - record stock used for a festival, or tag expenses with it." />
        </Card>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------------------ audit
function AuditTab({ days }: { days: number }) {
  const data = useLoad(() => getAuditAnalytics(days), [days]);
  if (data.loading && !data.data) return <LoadingBlock />;
  if (data.error || !data.data) return <ErrorBlock message={data.error ?? 'No data'} onRetry={data.reload} />;
  const d = data.data;
  const t = d.totals;
  const dayLabels = d.per_day.map((x) => String(Number(x.date.slice(8))));
  return (
    <div className={`space-y-4 ${data.loading ? 'opacity-60' : ''}`}>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        <StatTile label="Changes recorded" value={t.events.toLocaleString('en-IN')} />
        <StatTile label="People active" value={String(t.active_users)} />
        <StatTile label="Sign-ins" value={String(t.logins)} />
        <StatTile label="Failed sign-ins" value={String(t.failed_logins)} hint={t.failed_logins ? 'see IPs below' : undefined} />
        <StatTile label="Deletions" value={String(t.deletions)} />
        <StatTile label="Late-night activity" value={String(t.off_hours)} hint="10 pm - 6 am IST" />
      </div>
      <Card title="Activity per day (IST)">
        <ColumnChart title="Activity per day" labels={dayLabels} fullLabels={d.per_day.map((x) => x.date)}
          series={[{ name: 'Changes', values: d.per_day.map((x) => x.count) }]}
          tickEvery={days > 31 ? Math.ceil(days / 15) : days > 14 ? 2 : 1} />
      </Card>
      <div className="grid gap-4 md:grid-cols-2">
        <Card title="Time of day (IST)">
          <ColumnChart title="Activity by hour of day" labels={d.by_hour.map((_, h) => String(h))}
            fullLabels={d.by_hour.map((_, h) => `${String(h).padStart(2, '0')}:00 - ${String(h).padStart(2, '0')}:59 IST`)}
            series={[{ name: 'Changes', values: d.by_hour }]} tickEvery={3} height={140} />
        </Card>
        <Card title="Who made the changes">
          <BarList title="Changes by person" rows={d.by_actor.map((a) => ({ label: a.name, value: a.count, note: a.deletions ? `${a.deletions} deletion${a.deletions === 1 ? '' : 's'}` : undefined }))} />
        </Card>
        <Card title="What kind of change">
          <BarList title="Changes by action" rows={d.by_action.map((a) => ({ label: titleCase(a.name), value: a.count }))} />
        </Card>
        <Card title="Which area">
          <BarList title="Changes by area" rows={d.by_entity.map((a) => ({ label: titleCase(a.name), value: a.count }))} />
        </Card>
      </div>
      {d.failed_login_ips.length > 0 && (
        <Card title="Failed sign-ins by IP address">
          <BarList title="Failed sign-ins by IP" rows={d.failed_login_ips.map((r) => ({ label: r.name, value: r.count }))} />
          <p className="mt-2 text-xs text-gray-500">Many failures from one address can mean someone is guessing passwords.</p>
        </Card>
      )}
      <Card title="Changes to look at">
        <p className="-mt-2 mb-3 text-xs text-gray-500">Deletions, voids, rejections, write-offs, stock corrections, password changes, failed sign-ins - and anything done late at night.</p>
        {d.sensitive.length ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="text-xs uppercase text-gray-500"><tr><th scope="col" className="py-1">When (IST)</th><th scope="col" className="py-1">Who</th><th scope="col" className="py-1">What</th><th scope="col" className="py-1">IP</th></tr></thead>
              <tbody className="divide-y divide-gray-100">
                {d.sensitive.map((e) => (
                  <tr key={e.id}>
                    <td className="whitespace-nowrap py-2 pr-3 align-top text-gray-600">
                      {istTime(e.created_at)}
                      {e.off_hours && <span className="ml-1 inline-flex items-center gap-0.5 rounded bg-indigo-50 px-1 text-xs text-indigo-800"><Moon className="h-3 w-3" aria-hidden="true" />late</span>}
                    </td>
                    <td className="py-2 pr-3 align-top text-gray-800">{e.actor ?? 'unknown'}</td>
                    <td className="py-2 pr-3 align-top">
                      <span className={`mr-1 inline-flex items-center gap-0.5 rounded px-1.5 text-xs font-medium ${['DELETE', 'DELETE_ACCOUNT', 'LOGIN_FAILED'].includes(e.action) ? 'bg-red-50 text-red-800' : 'bg-gray-100 text-gray-700'}`}>
                        {['DELETE', 'DELETE_ACCOUNT', 'LOGIN_FAILED'].includes(e.action) && <AlertTriangle className="h-3 w-3" aria-hidden="true" />}{titleCase(e.action)}
                      </span>
                      <span className="text-gray-700">{e.summary ?? titleCase(e.entity_type)}</span>
                    </td>
                    <td className="py-2 align-top font-mono text-xs text-gray-500">{e.ip_address ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <p className="py-6 text-center text-sm text-gray-400">Nothing unusual in this period.</p>}
      </Card>
    </div>
  );
}
