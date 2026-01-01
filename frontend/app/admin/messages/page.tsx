'use client';

import React, { useState, useEffect } from 'react';
import {
    Mail,
    Search,
    Filter,
    MoreHorizontal,
    CheckCircle2,
    Clock,
    AlertCircle,
    Trash2,
    ExternalLink,
    MessageSquare,
    User
} from 'lucide-react';
import { api } from '@/lib/api';

interface Message {
    id: number;
    name: string;
    email: string;
    subject: string;
    message: string;
    status: string;
    admin_notes?: string;
    created_at: string;
}

export default function MessagesPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [filterStatus, setFilterStatus] = useState('');
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
    const [adminNotes, setAdminNotes] = useState('');
    const [updating, setUpdating] = useState(false);

    const fetchMessages = async () => {
        setLoading(true);
        try {
            const url = `/contacts/${filterStatus ? `?status=${filterStatus}` : ''}`;
            const response = await api.get(url);
            setMessages(response.data);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMessages();
    }, [filterStatus]);

    const handleUpdateStatus = async (id: number, status: string) => {
        setUpdating(true);
        try {
            const response = await api.patch(`/contacts/${id}`, {
                status,
                admin_notes: adminNotes
            });
            const updated = response.data;
            setMessages(messages.map(m => m.id === id ? updated : m));
            if (selectedMessage?.id === id) {
                setSelectedMessage(updated);
            }
        } catch (err: any) {
            alert(err.message);
        } finally {
            setUpdating(false);
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm('Are you sure you want to delete this message?')) return;
        try {
            await api.delete(`/contacts/${id}`);
            setMessages(messages.filter(m => m.id !== id));
            if (selectedMessage?.id === id) setSelectedMessage(null);
        } catch (err: any) {
            alert(err.message);
        }
    };

    const filteredMessages = messages.filter(m =>
        m.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        m.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        m.subject.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'RESOLVED': return <CheckCircle2 className="w-4 h-4 text-green-500" />;
            case 'PENDING': return <Clock className="w-4 h-4 text-orange-500" />;
            default: return <AlertCircle className="w-4 h-4 text-gray-400" />;
        }
    };

    return (
        <div className="p-8 max-w-7xl mx-auto">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">Contact Messages</h1>
                    <p className="text-slate-500 text-sm mt-1">Manage all user inquiries and support requests</p>
                </div>
            </div>

            {/* Filters */}
            <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200 mb-6 flex flex-col md:flex-row gap-4">
                <div className="flex-1 relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                        type="text"
                        placeholder="Search by name, email or subject..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-900 transition-all"
                    />
                </div>
                <div className="flex items-center gap-2">
                    <Filter className="w-4 h-4 text-slate-400" />
                    <select
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value)}
                        className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none"
                    >
                        <option value="">All Status</option>
                        <option value="PENDING">Pending</option>
                        <option value="IN_PROGRESS">In Progress</option>
                        <option value="RESOLVED">Resolved</option>
                    </select>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* List Area */}
                <div className="lg:col-span-2 space-y-4">
                    {loading ? (
                        <div className="text-center py-12 bg-white rounded-xl border border-slate-200">
                            <div className="w-8 h-8 border-2 border-slate-200 border-t-slate-900 rounded-full animate-spin mx-auto mb-4"></div>
                            <p className="text-slate-500 text-sm">Loading messages...</p>
                        </div>
                    ) : filteredMessages.length === 0 ? (
                        <div className="text-center py-20 bg-white rounded-xl border border-slate-200">
                            <Mail className="w-12 h-12 text-slate-200 mx-auto mb-4" />
                            <h3 className="text-slate-900 font-medium">No messages found</h3>
                            <p className="text-slate-500 text-sm mt-1">Users haven't sent any messages yet.</p>
                        </div>
                    ) : (
                        filteredMessages.map((msg) => (
                            <div
                                key={msg.id}
                                onClick={() => {
                                    setSelectedMessage(msg);
                                    setAdminNotes(msg.admin_notes || '');
                                }}
                                className={`p-5 rounded-xl border transition-all cursor-pointer ${selectedMessage?.id === msg.id
                                    ? 'bg-white border-slate-900 shadow-md scale-[1.01]'
                                    : 'bg-white border-slate-200 hover:border-slate-300'
                                    }`}
                            >
                                <div className="flex items-start justify-between mb-3">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-600 font-bold">
                                            {msg.name.charAt(0).toUpperCase()}
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-slate-900">{msg.name}</h3>
                                            <p className="text-xs text-slate-500">{new Date(msg.created_at).toLocaleString()}</p>
                                        </div>
                                    </div>
                                    <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${msg.status === 'RESOLVED' ? 'bg-green-50 text-green-700' :
                                        msg.status === 'PENDING' ? 'bg-orange-50 text-orange-700' :
                                            'bg-blue-50 text-blue-700'
                                        }`}>
                                        {getStatusIcon(msg.status)}
                                        {msg.status}
                                    </div>
                                </div>
                                <h4 className="font-medium text-slate-800 mb-1">{msg.subject}</h4>
                                <p className="text-sm text-slate-600 line-clamp-2">{msg.message}</p>
                            </div>
                        ))
                    )}
                </div>

                {/* Details Area */}
                <div className="lg:col-span-1">
                    {selectedMessage ? (
                        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden sticky top-8">
                            <div className="p-6 border-b border-slate-100">
                                <div className="flex items-center justify-between mb-4">
                                    <h2 className="text-lg font-bold text-slate-900">Message Details</h2>
                                    <button
                                        onClick={() => handleDelete(selectedMessage.id)}
                                        className="p-2 text-slate-400 hover:text-red-600 transition-colors"
                                    >
                                        <Trash2 className="w-5 h-5" />
                                    </button>
                                </div>

                                <div className="space-y-4">
                                    <div className="flex items-start gap-3">
                                        <User className="w-5 h-5 text-slate-400 mt-0.5" />
                                        <div>
                                            <p className="text-xs text-slate-500 uppercase font-bold tracking-wider">From</p>
                                            <p className="text-sm text-slate-900 font-medium">{selectedMessage.name}</p>
                                            <p className="text-xs text-slate-500">{selectedMessage.email}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-start gap-3">
                                        <MessageSquare className="w-5 h-5 text-slate-400 mt-0.5" />
                                        <div>
                                            <p className="text-xs text-slate-500 uppercase font-bold tracking-wider">Message</p>
                                            <p className="text-sm text-slate-700 whitespace-pre-wrap mt-1 leading-relaxed">
                                                {selectedMessage.message}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="p-6 bg-slate-50 space-y-4">
                                <div>
                                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Admin Notes</label>
                                    <textarea
                                        rows={4}
                                        value={adminNotes}
                                        onChange={(e) => setAdminNotes(e.target.value)}
                                        placeholder="Add private notes about this request..."
                                        className="w-full px-4 py-3 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-900 transition-all resize-none"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Update Status</p>
                                    <div className="grid grid-cols-2 gap-2">
                                        <button
                                            disabled={updating}
                                            onClick={() => handleUpdateStatus(selectedMessage.id, 'PENDING')}
                                            className={`px-3 py-2 rounded-lg text-xs font-bold transition-all ${selectedMessage.status === 'PENDING'
                                                ? 'bg-orange-100 text-orange-700 ring-1 ring-orange-200'
                                                : 'bg-white border border-slate-200 text-slate-600 hover:border-slate-300'
                                                }`}
                                        >
                                            Pending
                                        </button>
                                        <button
                                            disabled={updating}
                                            onClick={() => handleUpdateStatus(selectedMessage.id, 'IN_PROGRESS')}
                                            className={`px-3 py-2 rounded-lg text-xs font-bold transition-all ${selectedMessage.status === 'IN_PROGRESS'
                                                ? 'bg-blue-100 text-blue-700 ring-1 ring-blue-200'
                                                : 'bg-white border border-slate-200 text-slate-600 hover:border-slate-300'
                                                }`}
                                        >
                                            In Progress
                                        </button>
                                        <button
                                            disabled={updating}
                                            onClick={() => handleUpdateStatus(selectedMessage.id, 'RESOLVED')}
                                            className={`px-3 py-2 rounded-lg text-xs font-bold transition-all col-span-2 ${selectedMessage.status === 'RESOLVED'
                                                ? 'bg-green-100 text-green-700 ring-1 ring-green-200'
                                                : 'bg-white border border-slate-200 text-slate-600 hover:border-slate-300'
                                                }`}
                                        >
                                            Mark as Resolved
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="h-[400px] flex flex-col items-center justify-center bg-white rounded-xl border border-dashed border-slate-300 text-slate-400 p-8 text-center">
                            <ExternalLink className="w-10 h-10 mb-4 opacity-20" />
                            <p className="text-sm">Select a message from the list to view full details and manage status.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
