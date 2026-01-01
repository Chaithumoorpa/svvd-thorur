'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Edit2, Trash2, X, Plus, Search, Calendar } from 'lucide-react';
import { getFestivals, createFestival, updateFestival, deleteFestival, Festival, FestivalCreate } from '@/lib/api';

export default function FestivalsAdminPage() {
    const [festivals, setFestivals] = useState<Festival[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingId, setEditingId] = useState<number | null>(null);

    const [formData, setFormData] = useState<FestivalCreate & { is_active?: boolean }>({
        name: '',
        description: '',
        date: '',
    });

    const fetchFestivals = async () => {
        try {
            setLoading(true);
            const data = await getFestivals();
            setFestivals(data);
        } catch (error) {
            console.error('Failed to fetch festivals:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchFestivals();
    }, []);

    const filteredFestivals = useMemo(() => {
        return festivals.filter((f) =>
            f.name.toLowerCase().includes(searchQuery.toLowerCase())
        );
    }, [festivals, searchQuery]);

    const handleOpenModal = (festival?: Festival) => {
        if (festival) {
            setFormData({
                name: festival.name,
                description: festival.description || '',
                date: festival.date || '',
                is_active: festival.is_active,
            });
            setEditingId(festival.id);
        } else {
            setFormData({
                name: '',
                description: '',
                date: new Date().toISOString().split('T')[0],
            });
            setEditingId(null);
        }
        setIsModalOpen(true);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            if (editingId !== null) {
                const updated = await updateFestival(editingId, formData);
                setFestivals(festivals.map(f => f.id === editingId ? updated : f));
            } else {
                const created = await createFestival(formData);
                setFestivals([...festivals, created]);
            }
            setIsModalOpen(false);
        } catch (error) {
            console.error('Failed to save festival:', error);
            alert('Failed to save festival');
        }
    };

    const handleDelete = async (id: number) => {
        if (confirm('Are you sure you want to delete this festival?')) {
            try {
                await deleteFestival(id);
                setFestivals(festivals.filter(f => f.id !== id));
            } catch (error) {
                console.error('Failed to delete festival:', error);
                alert('Failed to delete festival');
            }
        }
    };

    return (
        <div className="p-6">
            <div className="space-y-6">
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Festivals</h1>
                        <p className="text-gray-600 mt-1">Manage annual temple festivals and events</p>
                    </div>
                    <button
                        onClick={() => handleOpenModal()}
                        className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors font-medium shadow-sm"
                    >
                        <Plus className="w-5 h-5" />
                        Add Festival
                    </button>
                </div>

                <div className="relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search festivals..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-12 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none transition-all"
                    />
                </div>

                <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    {loading ? (
                        <div className="p-12 text-center text-gray-400">Loading festivals...</div>
                    ) : filteredFestivals.length === 0 ? (
                        <div className="p-12 text-center text-gray-500">
                            No festivals found.
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-gray-50 border-b border-gray-200">
                                    <tr>
                                        <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Festival Name</th>
                                        <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Date</th>
                                        <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Status</th>
                                        <th className="px-6 py-4 text-right text-sm font-semibold text-gray-900">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200">
                                    {filteredFestivals.map((festival) => (
                                        <tr key={festival.id} className="hover:bg-gray-50 transition-colors">
                                            <td className="px-6 py-4">
                                                <p className="font-medium text-gray-900">{festival.name}</p>
                                                {festival.description && (
                                                    <p className="text-xs text-gray-500 truncate max-w-xs">{festival.description}</p>
                                                )}
                                            </td>
                                            <td className="px-6 py-4 text-sm text-gray-600">
                                                {festival.date || 'TBA'}
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`px-2 py-1 rounded text-xs font-medium ${festival.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                                    {festival.is_active ? 'Active' : 'Hidden'}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <div className="flex justify-end gap-2">
                                                    <button
                                                        onClick={() => handleOpenModal(festival)}
                                                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                                    >
                                                        <Edit2 className="w-4 h-4" />
                                                    </button>
                                                    <button
                                                        onClick={() => handleDelete(festival.id)}
                                                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                {isModalOpen && (
                    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                        <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 animate-in zoom-in duration-200">
                            <div className="flex justify-between items-center mb-6">
                                <h2 className="text-xl font-bold text-gray-900">
                                    {editingId !== null ? 'Edit Festival' : 'Add Festival'}
                                </h2>
                                <button onClick={() => setIsModalOpen(false)} className="p-1 hover:bg-gray-100 rounded-lg">
                                    <X className="w-6 h-6 text-gray-400" />
                                </button>
                            </div>

                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Festival Name *</label>
                                    <input
                                        type="text"
                                        required
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none"
                                        placeholder="e.g. Maha Shivaratri"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                                    <div className="relative">
                                        <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                        <input
                                            type="date"
                                            value={formData.date}
                                            onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                                            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                                    <textarea
                                        value={formData.description}
                                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none"
                                        rows={3}
                                        placeholder="Short description of the festival..."
                                    />
                                </div>

                                {editingId !== null && (
                                    <div className="flex items-center gap-2">
                                        <input
                                            type="checkbox"
                                            id="is_active"
                                            checked={formData.is_active}
                                            onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                                            className="w-4 h-4 text-orange-600 border-gray-300 rounded focus:ring-orange-500"
                                        />
                                        <label htmlFor="is_active" className="text-sm font-medium text-gray-700">Display on website</label>
                                    </div>
                                )}

                                <div className="flex gap-3 pt-6">
                                    <button
                                        type="button"
                                        onClick={() => setIsModalOpen(false)}
                                        className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium transition-colors"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        className="flex-1 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 font-medium transition-colors shadow-sm"
                                    >
                                        {editingId !== null ? 'Update Festival' : 'Add Festival'}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
