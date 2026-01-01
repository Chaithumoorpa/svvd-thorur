'use client';

import React, { useState, useEffect } from 'react';
import {
    Ticket,
    Search,
    Filter,
    Download,
    QrCode,
    Clock,
    CheckCircle2,
    XCircle,
    MoreVertical,
    Printer,
    ChevronRight,
    ChevronLeft,
    Plus,
    Calendar,
    User,
    Phone,
    IndianRupee,
    AlertCircle
} from 'lucide-react';
import Link from 'next/link';
import { api, getPoojas, Pooja } from '@/lib/api';

interface SevaTicket {
    id: string;
    ticket_number: string;
    devotee_name: string;
    mobile_number: string;
    seva_name: string;
    seva_date: string;
    seva_time?: string;
    status: 'ACTIVE' | 'USED' | 'CANCELLED';
    source: 'ONLINE' | 'COUNTER';
    amount: number;
    payment_status: 'FREE' | 'PAID';
    created_at: string;
}

export default function SevaTicketsPage() {
    const [tickets, setTickets] = useState<SevaTicket[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState('ALL');

    // Scan Modal State
    const [isScanModalOpen, setIsScanModalOpen] = useState(false);
    const [scannedTicket, setScannedTicket] = useState('');
    const [scanStatus, setScanStatus] = useState<'idle' | 'scanning' | 'success' | 'error'>('idle');
    const [scanMessage, setScanMessage] = useState('');

    // Create Modal State
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [sevas, setSevas] = useState<Pooja[]>([]);
    const [creating, setCreating] = useState(false);
    const [createError, setCreateError] = useState('');
    const [formData, setFormData] = useState({
        seva_id: '',
        devotee_name: '',
        mobile_number: '',
        seva_date: new Date().toISOString().split('T')[0],
        seva_time: '',
        amount: 0,
        payment_status: 'PAID'
    });

    useEffect(() => {
        fetchTickets();
        fetchSevas();
    }, [statusFilter]);

    const fetchTickets = async () => {
        setLoading(true);
        try {
            const params = statusFilter !== 'ALL' ? { status: statusFilter } : {};
            const res = await api.get('/seva-tickets/', { params });
            setTickets(res.data);
        } catch (error) {
            console.error('Failed to fetch tickets:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchSevas = async () => {
        try {
            const data = await getPoojas();
            setSevas(data.filter(s => s.is_active));
        } catch (error) {
            console.error('Failed to fetch sevas:', error);
        }
    };

    const filteredTickets = tickets.filter(t =>
        t.devotee_name.toLowerCase().includes(search.toLowerCase()) ||
        t.ticket_number.toLowerCase().includes(search.toLowerCase()) ||
        t.mobile_number.includes(search)
    );

    const handleScan = async (e: React.FormEvent) => {
        e.preventDefault();
        setScanStatus('scanning');
        try {
            const res = await api.post('/seva-tickets/scan', { qr_token: scannedTicket });
            if (res.data.success) {
                setScanStatus('success');
                setScanMessage(res.data.message);
                fetchTickets();
                setTimeout(() => {
                    setIsScanModalOpen(false);
                    setScanStatus('idle');
                    setScannedTicket('');
                }, 2000);
            } else {
                setScanStatus('error');
                setScanMessage(res.data.message);
            }
        } catch (error: any) {
            setScanStatus('error');
            const errorData = error.response?.data?.detail;
            const message = typeof errorData === 'string' ? errorData : (Array.isArray(errorData) ? errorData.map((err: any) => err.msg || err).join(', ') : 'Verification failed');
            setScanMessage(message);
        }
    };

    const handleDownloadPDF = async (ticketId: string, ticketNumber: string, action: 'print' | 'download') => {
        try {
            const res = await api.get(`/seva-tickets/${ticketId}/pdf?action=${action}`, {
                responseType: 'blob'
            });
            const blob = new Blob([res.data], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);

            if (action === 'download') {
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', `Ticket-${ticketNumber}.pdf`);
                document.body.appendChild(link);
                link.click();
                link.remove();
            } else {
                window.open(url, '_blank');
            }

            // Clean up the URL object after a short delay (for window.open to work)
            setTimeout(() => window.URL.revokeObjectURL(url), 100);
        } catch (error: any) {
            console.error('Failed to get PDF:', error);
            alert('Failed to generate PDF. Please try again.');
        }
    };

    const handleCreateTicket = async (e: React.FormEvent) => {
        e.preventDefault();
        setCreating(true);
        setCreateError('');
        try {
            const selectedSeva = sevas.find(s => s.id === parseInt(formData.seva_id));
            const payload = {
                ...formData,
                seva_id: parseInt(formData.seva_id),
                seva_name: selectedSeva?.name || '',
                amount: parseInt(formData.amount.toString()),
                // Fix 422: Ensure seva_time is null if empty
                seva_time: formData.seva_time || null
            };
            const res = await api.post('/seva-tickets/admin', payload);
            setIsCreateModalOpen(false);
            fetchTickets();
            // Securely open print window
            handleDownloadPDF(res.data.id, res.data.ticket_number, 'print');
        } catch (error: any) {
            const errorData = error.response?.data?.detail;
            const message = typeof errorData === 'string' ? errorData : (Array.isArray(errorData) ? errorData.map((err: any) => err.msg || err).join(', ') : 'Failed to create ticket');
            setCreateError(message);
        } finally {
            setCreating(false);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'ACTIVE': return 'bg-blue-50 text-blue-700 border-blue-100';
            case 'USED': return 'bg-emerald-50 text-emerald-700 border-emerald-100';
            case 'CANCELLED': return 'bg-red-50 text-red-700 border-red-100';
            default: return 'bg-gray-50 text-gray-700 border-gray-100';
        }
    };

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <Ticket className="w-6 h-6 text-blue-600" />
                        Seva Tickets
                    </h1>
                    <p className="text-gray-500 mt-1">Manage and verify devotee seva bookings</p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => setIsCreateModalOpen(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 transition-colors shadow-lg shadow-blue-600/20"
                    >
                        <Plus className="w-4 h-4" />
                        Create Ticket
                    </button>
                    <button
                        onClick={() => setIsScanModalOpen(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800 transition-colors shadow-lg shadow-slate-900/20"
                    >
                        <QrCode className="w-4 h-4" />
                        Scan Ticket
                    </button>
                </div>
            </div>

            {/* Filters & Search */}
            <div className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 flex flex-col md:flex-row gap-4">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search by name, ticket #, or mobile..."
                        className="w-full pl-10 pr-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
                <div className="flex items-center gap-2">
                    <Filter className="w-4 h-4 text-gray-400 mr-1" />
                    {['ALL', 'ACTIVE', 'USED', 'CANCELLED'].map((status) => (
                        <button
                            key={status}
                            onClick={() => setStatusFilter(status)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${statusFilter === status
                                ? 'bg-blue-600 text-white shadow-sm'
                                : 'text-gray-600 hover:bg-gray-100'
                                }`}
                        >
                            {status}
                        </button>
                    ))}
                </div>
            </div>

            {/* Table */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-gray-50 border-b border-gray-100">
                            <tr>
                                <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Ticket Details</th>
                                <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Devotee</th>
                                <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Seva Details</th>
                                <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {loading ? (
                                Array.from({ length: 5 }).map((_, i) => (
                                    <tr key={i} className="animate-pulse">
                                        <td colSpan={5} className="px-6 py-4">
                                            <div className="h-12 bg-gray-50 rounded-lg"></div>
                                        </td>
                                    </tr>
                                ))
                            ) : filteredTickets.length > 0 ? (
                                filteredTickets.map((ticket) => (
                                    <tr key={ticket.id} className="hover:bg-gray-50/50 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col">
                                                <div className="flex items-center gap-2">
                                                    <span className="font-bold text-gray-900 text-sm">{ticket.ticket_number}</span>
                                                    <span className={`text-[10px] px-1.5 py-0.5 rounded-md font-bold ${ticket.source === 'COUNTER' ? 'bg-amber-50 text-amber-600 border border-amber-100' : 'bg-slate-50 text-slate-500 border border-slate-100'
                                                        }`}>
                                                        {ticket.source}
                                                    </span>
                                                </div>
                                                <span className="text-xs text-gray-400 flex items-center gap-1 mt-0.5">
                                                    <Clock className="w-3 h-3" />
                                                    {new Date(ticket.created_at).toLocaleDateString()}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col">
                                                <span className="font-medium text-gray-800 text-sm">{ticket.devotee_name}</span>
                                                <span className="text-xs text-gray-500">{ticket.mobile_number}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col">
                                                <span className="text-sm text-gray-700">{ticket.seva_name}</span>
                                                <div className="flex items-center gap-2 mt-0.5">
                                                    <span className="text-xs font-medium text-blue-600">{ticket.seva_date}</span>
                                                    <span className="text-xs text-gray-300">|</span>
                                                    <span className="text-xs font-bold text-slate-700">₹{ticket.amount}</span>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${getStatusColor(ticket.status)}`}>
                                                {ticket.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex justify-end items-center gap-2">
                                                <button
                                                    onClick={() => handleDownloadPDF(ticket.id, ticket.ticket_number, 'print')}
                                                    className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all"
                                                    title="Print PDF"
                                                >
                                                    <Printer className="w-4 h-4" />
                                                </button>
                                                <button
                                                    onClick={() => handleDownloadPDF(ticket.id, ticket.ticket_number, 'download')}
                                                    className="p-2 text-gray-400 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-all"
                                                    title="Download PDF"
                                                >
                                                    <Download className="w-4 h-4" />
                                                </button>
                                                <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-all">
                                                    <MoreVertical className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan={5} className="px-6 py-20 text-center">
                                        <div className="flex flex-col items-center justify-center text-gray-400">
                                            <Ticket className="w-12 h-12 mb-4 opacity-20" />
                                            <p className="text-lg font-medium">No tickets found</p>
                                            <p className="text-sm">Try adjusting your search or filters</p>
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                <div className="px-6 py-4 border-t border-gray-100 bg-gray-50/50 flex items-center justify-between">
                    <p className="text-xs text-gray-500">
                        Showing <span className="font-bold text-gray-700">{filteredTickets.length}</span> results
                    </p>
                    <div className="flex items-center gap-2">
                        <button className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-30" disabled>
                            <ChevronLeft className="w-5 h-5" />
                        </button>
                        <button className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-30" disabled>
                            <ChevronRight className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Create Manual Ticket Modal */}
            {isCreateModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <div className="bg-white w-full max-w-2xl rounded-[2.5rem] p-8 shadow-2xl animate-in zoom-in-95 duration-200 overflow-y-auto max-h-[95vh]">
                        <div className="flex justify-between items-start mb-6">
                            <div className="bg-blue-50 p-3 rounded-2xl text-blue-600">
                                <Plus className="w-6 h-6" />
                            </div>
                            <button
                                onClick={() => setIsCreateModalOpen(false)}
                                className="text-gray-400 hover:text-gray-600"
                            >
                                <XCircle className="w-6 h-6" />
                            </button>
                        </div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-2">Create Counter Ticket</h2>
                        <p className="text-gray-500 mb-8 text-sm">Fill in the devotee details to generate a ticket instantly.</p>

                        <form onSubmit={handleCreateTicket} className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Seva Selection */}
                            <div className="md:col-span-2 space-y-2">
                                <label className="text-xs font-bold text-gray-400 uppercase tracking-widest ml-1">Select Seva</label>
                                <div className="relative">
                                    <Calendar className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                    <select
                                        required
                                        value={formData.seva_id}
                                        onChange={(e) => {
                                            const seva = sevas.find(s => s.id === parseInt(e.target.value));
                                            setFormData({ ...formData, seva_id: e.target.value, amount: seva?.suggested_amount || 0 });
                                        }}
                                        className="w-full pl-12 pr-4 py-4 rounded-2xl border border-gray-100 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all appearance-none"
                                    >
                                        <option value="">Choose a Seva...</option>
                                        {sevas.map(seva => (
                                            <option key={seva.id} value={seva.id}>{seva.name} (₹{seva.suggested_amount})</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            {/* Devotee Name */}
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-gray-400 uppercase tracking-widest ml-1">Devotee Name</label>
                                <div className="relative">
                                    <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                    <input
                                        required
                                        type="text"
                                        placeholder="Full Name"
                                        className="w-full pl-12 pr-4 py-4 rounded-2xl border border-gray-100 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all font-medium"
                                        value={formData.devotee_name}
                                        onChange={(e) => setFormData({ ...formData, devotee_name: e.target.value })}
                                    />
                                </div>
                            </div>

                            {/* Mobile Number */}
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-gray-400 uppercase tracking-widest ml-1">Mobile Number</label>
                                <div className="relative">
                                    <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                    <input
                                        required
                                        type="tel"
                                        placeholder="10-digit number"
                                        className="w-full pl-12 pr-4 py-4 rounded-2xl border border-gray-100 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all font-medium"
                                        value={formData.mobile_number}
                                        onChange={(e) => setFormData({ ...formData, mobile_number: e.target.value })}
                                    />
                                </div>
                            </div>

                            {/* Seva Date */}
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-gray-400 uppercase tracking-widest ml-1">Seva Date</label>
                                <div className="relative">
                                    <input
                                        required
                                        type="date"
                                        className="w-full px-6 py-4 rounded-2xl border border-gray-100 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all font-medium"
                                        value={formData.seva_date}
                                        onChange={(e) => setFormData({ ...formData, seva_date: e.target.value })}
                                    />
                                </div>
                            </div>

                            {/* Amount */}
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-gray-400 uppercase tracking-widest ml-1">Amount Paid (₹)</label>
                                <div className="relative">
                                    <IndianRupee className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                    <input
                                        required
                                        type="number"
                                        className="w-full pl-12 pr-4 py-4 rounded-2xl border border-gray-100 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all font-bold text-blue-600"
                                        value={formData.amount}
                                        onChange={(e) => setFormData({ ...formData, amount: parseInt(e.target.value) || 0 })}
                                    />
                                </div>
                            </div>

                            {createError && (
                                <div className="md:col-span-2 flex items-center gap-3 p-4 bg-red-50 text-red-700 rounded-2xl text-sm font-medium border border-red-100 animate-in shake">
                                    <AlertCircle className="w-5 h-5" />
                                    {createError}
                                </div>
                            )}

                            <div className="md:col-span-2 pt-4 flex gap-4">
                                <button
                                    type="button"
                                    onClick={() => setIsCreateModalOpen(false)}
                                    className="flex-1 py-4 bg-gray-100 text-gray-600 rounded-2xl font-bold hover:bg-gray-200 transition-all"
                                >
                                    Cancel
                                </button>
                                <button
                                    disabled={creating}
                                    className="flex-[2] py-4 bg-blue-600 text-white rounded-2xl font-bold shadow-lg shadow-blue-600/20 hover:bg-blue-700 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                                >
                                    {creating ? (
                                        <>
                                            <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                                            Generating...
                                        </>
                                    ) : 'Create & Print Ticket'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Scan Modal */}
            {isScanModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <div className="bg-white w-full max-w-md rounded-[2.5rem] p-8 shadow-2xl animate-in zoom-in-95 duration-200">
                        <div className="flex justify-between items-start mb-6">
                            <div className="bg-blue-50 p-3 rounded-2xl text-blue-600">
                                <QrCode className="w-6 h-6" />
                            </div>
                            <button
                                onClick={() => setIsScanModalOpen(false)}
                                className="text-gray-400 hover:text-gray-600"
                            >
                                <XCircle className="w-6 h-6" />
                            </button>
                        </div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-2">Scan Ticket</h2>
                        <p className="text-gray-500 mb-8 text-sm">Enter the ticket token or scan the QR code to verify and mark as used.</p>

                        <form onSubmit={handleScan} className="space-y-6">
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-gray-400 uppercase tracking-widest ml-1">QR Token / ID</label>
                                <input
                                    type="text"
                                    value={scannedTicket}
                                    onChange={(e) => setScannedTicket(e.target.value)}
                                    placeholder="Paste token or scan"
                                    className="w-full px-6 py-4 rounded-2xl border border-gray-100 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-lg font-mono"
                                    autoFocus
                                />
                            </div>

                            {scanStatus === 'success' && (
                                <div className="flex items-center gap-3 p-4 bg-emerald-50 text-emerald-700 rounded-2xl text-sm font-medium border border-emerald-100 animate-in fade-in slide-in-from-top-2">
                                    <CheckCircle2 className="w-5 h-5" />
                                    {scanMessage}
                                </div>
                            )}

                            {scanStatus === 'error' && (
                                <div className="flex items-center gap-3 p-4 bg-red-50 text-red-700 rounded-2xl text-sm font-medium border border-red-100 animate-in shake">
                                    <XCircle className="w-5 h-5" />
                                    {scanMessage}
                                </div>
                            )}

                            <button
                                disabled={!scannedTicket || scanStatus === 'scanning'}
                                className="w-full py-4 bg-slate-900 text-white rounded-2xl font-bold shadow-lg shadow-slate-900/10 hover:bg-slate-800 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {scanStatus === 'scanning' ? (
                                    <>
                                        <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                                        Verifying...
                                    </>
                                ) : 'Verify & Mark Used'}
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
