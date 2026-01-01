'use client';

import { useState, useEffect } from 'react';
import {
    getFinanceSummary,
    getLedger,
    FinanceSummary,
    LedgerEntry,
    exportFinanceCSV
} from '@/lib/api';
import {
    PlusIcon,
    ArrowUpIcon,
    ArrowDownIcon,
    WalletIcon,
    DownloadIcon,
    FilterIcon
} from 'lucide-react';
import Link from 'next/link';

export default function FinanceDashboard() {
    const [summary, setSummary] = useState<FinanceSummary | null>(null);
    const [ledger, setLedger] = useState<LedgerEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    useEffect(() => {
        fetchData();
    }, [startDate, endDate]);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [summaryData, ledgerData] = await Promise.all([
                getFinanceSummary(),
                getLedger(startDate || undefined, endDate || undefined)
            ]);
            setSummary(summaryData);
            setLedger(ledgerData);
        } catch (error) {
            console.error('Failed to fetch finance data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleExport = async () => {
        try {
            const blob = await exportFinanceCSV(startDate || undefined, endDate || undefined);
            const url = window.URL.createObjectURL(new Blob([blob]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', 'temple_finance_report.csv');
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (error) {
            console.error('Export failed:', error);
        }
    };

    return (
        <div className="p-6 space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-gray-800">Finance Dashboard</h1>
                    <p className="text-gray-500">Track temple income, expenses, and overall balance.</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={handleExport}
                        className="flex items-center gap-2 bg-white border border-gray-300 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 transition"
                    >
                        <DownloadIcon size={16} />
                        Export CSV
                    </button>
                    <Link
                        href="/admin/finance/income"
                        className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition"
                    >
                        <PlusIcon size={16} />
                        Add Income
                    </Link>
                    <Link
                        href="/admin/finance/expenses"
                        className="flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-700 transition"
                    >
                        <PlusIcon size={16} />
                        Add Expense
                    </Link>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <div className="flex items-center justify-between mb-4">
                        <div className="p-2 bg-green-50 rounded-lg text-green-600">
                            <ArrowUpIcon size={24} />
                        </div>
                        <span className="text-sm font-medium text-gray-400">Total Income</span>
                    </div>
                    <h3 className="text-2xl font-bold text-gray-800">
                        ₹{summary?.total_income.toLocaleString() || '0'}
                    </h3>
                </div>

                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <div className="flex items-center justify-between mb-4">
                        <div className="p-2 bg-red-50 rounded-lg text-red-600">
                            <ArrowDownIcon size={24} />
                        </div>
                        <span className="text-sm font-medium text-gray-400">Total Expenses</span>
                    </div>
                    <h3 className="text-2xl font-bold text-gray-800">
                        ₹{summary?.total_expenses.toLocaleString() || '0'}
                    </h3>
                </div>

                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <div className="flex items-center justify-between mb-4">
                        <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
                            <WalletIcon size={24} />
                        </div>
                        <span className="text-sm font-medium text-gray-400">Current Balance</span>
                    </div>
                    <h3 className="text-2xl font-bold text-gray-800">
                        ₹{summary?.balance.toLocaleString() || '0'}
                    </h3>
                </div>
            </div>

            {/* Analysis Charts */}
            {!loading && summary && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Income Breakdown */}
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <h3 className="text-lg font-bold text-gray-800 mb-4">Income Breakdown</h3>
                        <div className="space-y-4">
                            {Object.entries(summary.income_by_source).map(([source, amount]) => {
                                const percentage = summary.total_income > 0 ? (amount / summary.total_income) * 100 : 0;
                                return (
                                    <div key={source}>
                                        <div className="flex justify-between text-sm mb-1">
                                            <span className="text-gray-600 font-medium">{source}</span>
                                            <span className="text-gray-900 font-semibold">₹{amount.toLocaleString()}</span>
                                        </div>
                                        <div className="w-full bg-gray-100 rounded-full h-2.5">
                                            <div
                                                className="bg-green-500 h-2.5 rounded-full"
                                                style={{ width: `${percentage}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                );
                            })}
                            {Object.keys(summary.income_by_source).length === 0 && (
                                <p className="text-gray-400 text-sm italic">No income data available.</p>
                            )}
                        </div>
                    </div>

                    {/* Expense Breakdown */}
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <h3 className="text-lg font-bold text-gray-800 mb-4">Expense Breakdown</h3>
                        <div className="space-y-4">
                            {Object.entries(summary.expense_by_category).map(([category, amount]) => {
                                const percentage = summary.total_expenses > 0 ? (amount / summary.total_expenses) * 100 : 0;
                                return (
                                    <div key={category}>
                                        <div className="flex justify-between text-sm mb-1">
                                            <span className="text-gray-600 font-medium">{category}</span>
                                            <span className="text-gray-900 font-semibold">₹{amount.toLocaleString()}</span>
                                        </div>
                                        <div className="w-full bg-gray-100 rounded-full h-2.5">
                                            <div
                                                className="bg-red-500 h-2.5 rounded-full"
                                                style={{ width: `${percentage}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                );
                            })}
                            {Object.keys(summary.expense_by_category).length === 0 && (
                                <p className="text-gray-400 text-sm italic">No expense data available.</p>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Filters & Ledger */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-6 border-b border-gray-100 flex flex-wrap items-center justify-between gap-4">
                    <h2 className="text-lg font-bold text-gray-800">Transaction Ledger</h2>
                    <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2 text-sm">
                            <span className="text-gray-500">From:</span>
                            <input
                                type="date"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                                className="border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                            <span className="text-gray-500">To:</span>
                            <input
                                type="date"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                                className="border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                        </div>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-gray-50 text-gray-500 text-xs uppercase font-semibold">
                                <th className="px-6 py-3 border-b border-gray-100">Date</th>
                                <th className="px-6 py-3 border-b border-gray-100">Type</th>
                                <th className="px-6 py-3 border-b border-gray-100">Category/Source</th>
                                <th className="px-6 py-3 border-b border-gray-100">Description</th>
                                <th className="px-6 py-3 border-b border-gray-100">Payment</th>
                                <th className="px-6 py-3 border-b border-gray-100 text-right">Amount</th>
                            </tr>
                        </thead>
                        <tbody className="text-sm">
                            {loading ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center text-gray-400">
                                        Loading transactions...
                                    </td>
                                </tr>
                            ) : ledger.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center text-gray-400">
                                        No transactions found for the selected period.
                                    </td>
                                </tr>
                            ) : (
                                ledger.map((entry) => (
                                    <tr key={entry.id} className="hover:bg-gray-50 transition border-b border-gray-50 last:border-0">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {new Date(entry.date).toLocaleDateString()}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase ${entry.type === 'INCOME' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                                                }`}>
                                                {entry.type}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-gray-600">
                                            {entry.category_or_source}
                                        </td>
                                        <td className="px-6 py-4 text-gray-600 max-w-xs truncate">
                                            {entry.description}
                                        </td>
                                        <td className="px-6 py-4 text-gray-500">
                                            {entry.payment_mode}
                                        </td>
                                        <td className={`px-6 py-4 text-right font-semibold ${entry.amount > 0 ? 'text-green-600' : 'text-red-600'
                                            }`}>
                                            ₹{Math.abs(entry.amount).toLocaleString()}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
