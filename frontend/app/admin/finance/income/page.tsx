'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { addIncome, IncomeSource, PaymentMode } from '@/lib/api';
import { ArrowLeftIcon, SaveIcon } from 'lucide-react';
import Link from 'next/link';

export default function AddIncomePage() {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [formData, setFormData] = useState({
        source_type: 'MANUAL' as IncomeSource,
        amount: '',
        payment_mode: 'CASH' as PaymentMode,
        reference_id: '',
        notes: ''
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.amount || parseInt(formData.amount) <= 0) {
            setError('Please enter a valid amount');
            return;
        }

        try {
            setLoading(true);
            setError(null);
            await addIncome({
                ...formData,
                amount: parseInt(formData.amount)
            });
            router.push('/admin/finance');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to add income');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 max-w-2xl mx-auto space-y-6">
            <div className="flex items-center gap-4">
                <Link
                    href="/admin/finance"
                    className="p-2 hover:bg-gray-100 rounded-full text-gray-500 transition"
                >
                    <ArrowLeftIcon size={20} />
                </Link>
                <div>
                    <h1 className="text-2xl font-bold text-gray-800">Add Income</h1>
                    <p className="text-gray-500">Record a new income transaction.</p>
                </div>
            </div>

            <form onSubmit={handleSubmit} className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 space-y-6">
                {error && (
                    <div className="p-4 bg-red-50 text-red-600 rounded-lg text-sm border border-red-100">
                        {error}
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-gray-700">Source Type</label>
                        <select
                            value={formData.source_type}
                            onChange={(e) => setFormData({ ...formData, source_type: e.target.value as IncomeSource })}
                            className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none"
                        >
                            <option value="MANUAL">Manual Entry</option>
                            <option value="HUNDI">Hundi</option>
                            <option value="DONATION">General Donation</option>
                            <option value="SEVA">Seva Ticket (Internal)</option>
                        </select>
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-gray-700">Amount (₹)</label>
                        <input
                            type="number"
                            value={formData.amount}
                            onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                            placeholder="0"
                            className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none"
                            required
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-gray-700">Payment Mode</label>
                        <select
                            value={formData.payment_mode}
                            onChange={(e) => setFormData({ ...formData, payment_mode: e.target.value as PaymentMode })}
                            className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none"
                        >
                            <option value="CASH">Cash</option>
                            <option value="UPI">UPI / QR</option>
                            <option value="BANK">Bank Transfer</option>
                            <option value="CHEQUE">Cheque</option>
                        </select>
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-gray-700">Reference ID (Optional)</label>
                        <input
                            type="text"
                            value={formData.reference_id}
                            onChange={(e) => setFormData({ ...formData, reference_id: e.target.value })}
                            placeholder="Txn ID, Receipt No, etc."
                            className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none"
                        />
                    </div>
                </div>

                <div className="space-y-2">
                    <label className="text-sm font-semibold text-gray-700">Notes (Optional)</label>
                    <textarea
                        value={formData.notes}
                        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                        rows={3}
                        placeholder="Add any additional details..."
                        className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none resize-none"
                    />
                </div>

                <div className="pt-4">
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-green-600 text-white font-bold py-3 rounded-lg hover:bg-green-700 transition flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                        {loading ? 'Saving...' : (
                            <>
                                <SaveIcon size={20} />
                                Save Income Transaction
                            </>
                        )}
                    </button>
                </div>
            </form>
        </div>
    );
}
