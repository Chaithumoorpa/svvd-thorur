'use client';

import React, { useState, useMemo, useEffect } from 'react';
import { Edit2, Trash2, X, Plus, Search } from 'lucide-react';
import { getPoojas, createPooja, updatePooja, deletePooja, Pooja, PoojaCreate, PoojaUpdate } from '@/lib/api';

export default function PoojasPage() {
    const [poojas, setPoojas] = useState<Pooja[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingId, setEditingId] = useState<number | null>(null);

    const [formData, setFormData] = useState<PoojaCreate & { is_active?: boolean }>({
        name: '',
        description: '',
        start_time: '',
        end_time: '',
        pooja_type: 'daily',
        is_paid: false,
        suggested_amount: 0,
    });

    useEffect(() => {
        fetchPoojas();
    }, []);

    const fetchPoojas = async () => {
        try {
            setIsLoading(true);
            const data = await getPoojas();
            setPoojas(data);
        } catch (error) {
            console.error('Failed to fetch poojas:', error);
            alert('Failed to load poojas. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const filteredPoojas = useMemo(() => {
        return poojas.filter((pooja) =>
            pooja.name.toLowerCase().includes(searchQuery.toLowerCase())
        );
    }, [poojas, searchQuery]);

    const handleOpenModal = () => {
        setFormData({
            name: '',
            description: '',
            start_time: '',
            end_time: '',
            pooja_type: 'daily',
            is_paid: false,
            suggested_amount: 0
        });
        setEditingId(null);
        setIsModalOpen(true);
    };

    const handleEdit = (pooja: Pooja) => {
        setFormData({
            name: pooja.name,
            description: pooja.description || '',
            start_time: pooja.start_time || '',
            end_time: pooja.end_time || '',
            pooja_type: pooja.pooja_type,
            is_paid: pooja.is_paid,
            suggested_amount: pooja.suggested_amount || 0,
            is_active: pooja.is_active
        });
        setEditingId(pooja.id);
        setIsModalOpen(true);
    };

    const handleDelete = async (id: number) => {
        if (confirm('Are you sure you want to delete this pooja?')) {
            try {
                await deletePooja(id);
                setPoojas(poojas.filter((p) => p.id !== id));
            } catch (error) {
                console.error('Failed to delete pooja:', error);
                alert('Failed to delete pooja. Please try again.');
            }
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!formData.name.trim()) {
            alert('Please fill in required fields');
            return;
        }

        try {
            if (editingId !== null) {
                // Edit existing pooja
                // Clean up empty strings for optional fields
                const updateData: PoojaUpdate = {
                    ...formData,
                    description: formData.description || undefined,
                    start_time: formData.start_time || undefined,
                    end_time: formData.end_time || undefined,
                    suggested_amount: formData.suggested_amount || undefined,
                };
                const updatedPooja = await updatePooja(editingId, updateData);
                setPoojas(poojas.map((p) => (p.id === editingId ? updatedPooja : p)));
            } else {
                // Add new pooja
                const createData: PoojaCreate = {
                    name: formData.name,
                    description: formData.description || undefined,
                    start_time: formData.start_time || undefined,
                    end_time: formData.end_time || undefined,
                    pooja_type: formData.pooja_type,
                    is_paid: formData.is_paid,
                    suggested_amount: formData.suggested_amount || undefined,
                }
                const newPooja = await createPooja(createData);
                setPoojas([...poojas, newPooja]);
            }
            setIsModalOpen(false);
        } catch (error) {
            console.error('Failed to save pooja:', error);
            alert('Failed to save pooja. Please check inputs and try again.');
        }
    };

    const formatTime = (timeStr?: string) => {
        if (!timeStr) return '';
        // Basic formatting, assuming HH:MM:SS or HH:MM
        return timeStr.substring(0, 5);
    };

    return (
        <div className="p-6">
            <div className="space-y-6">
                {/* Header */}
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Poojas</h1>
                        <p className="text-gray-600 mt-1">Manage temple poojas and sevas</p>
                    </div>
                    <button
                        onClick={handleOpenModal}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
                    >
                        <Plus className="w-5 h-5" />
                        Add Pooja
                    </button>
                </div>

                {/* Search Bar */}
                <div className="relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search poojas..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-12 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition-all"
                    />
                </div>

                {/* Poojas Table */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                    {isLoading ? (
                        <div className="p-12 text-center text-gray-500">Loading poojas...</div>
                    ) : filteredPoojas.length === 0 ? (
                        <div className="p-12 text-center">
                            <p className="text-gray-500">
                                {poojas.length === 0 ? 'No poojas found' : 'No poojas match your search'}
                            </p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-gray-50 border-b border-gray-200">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Name</th>
                                        <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Type</th>
                                        <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Timing</th>
                                        <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Cost</th>
                                        <th className="px-6 py-3 text-right text-sm font-semibold text-gray-900">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200">
                                    {filteredPoojas.map((pooja) => (
                                        <tr key={pooja.id} className="hover:bg-gray-50 transition-colors">
                                            <td className="px-6 py-4">
                                                <p className="font-medium text-gray-900">{pooja.name}</p>
                                                {pooja.description && (
                                                    <p className="text-sm text-gray-500 truncate max-w-xs">{pooja.description}</p>
                                                )}
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium capitalize">
                                                    {pooja.pooja_type}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-sm text-gray-600">
                                                {formatTime(pooja.start_time)}
                                                {pooja.end_time && ` - ${formatTime(pooja.end_time)}`}
                                            </td>
                                            <td className="px-6 py-4 text-sm font-medium text-gray-900">
                                                {pooja.is_paid ? `₹${pooja.suggested_amount}` : 'Free'}
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <div className="flex justify-end gap-2">
                                                    <button
                                                        onClick={() => handleEdit(pooja)}
                                                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                                        title="Edit"
                                                    >
                                                        <Edit2 className="w-4 h-4" />
                                                    </button>
                                                    <button
                                                        onClick={() => handleDelete(pooja.id)}
                                                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                                        title="Delete"
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

                {/* Modal */}
                {isModalOpen && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                        <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
                            <div className="flex justify-between items-center p-6 border-b border-gray-200">
                                <h2 className="text-xl font-bold text-gray-900">
                                    {editingId !== null ? 'Edit Pooja' : 'Add Pooja'}
                                </h2>
                                <button
                                    onClick={() => setIsModalOpen(false)}
                                    className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
                                >
                                    <X className="w-6 h-6 text-gray-600" />
                                </button>
                            </div>

                            <form onSubmit={handleSubmit} className="p-6 space-y-4">
                                {/* Name */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                                    <input
                                        type="text"
                                        required
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none"
                                    />
                                </div>

                                {/* Type */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                                    <select
                                        value={formData.pooja_type}
                                        onChange={(e) => setFormData({ ...formData, pooja_type: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none"
                                    >
                                        <option value="daily">Daily</option>
                                        <option value="weekly">Weekly</option>
                                        <option value="special">Special</option>
                                    </select>
                                </div>

                                {/* Description */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                                    <textarea
                                        value={formData.description}
                                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none"
                                        rows={3}
                                    />
                                </div>

                                {/* Timings */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Start Time</label>
                                        <input
                                            type="time"
                                            value={formData.start_time}
                                            onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">End Time</label>
                                        <input
                                            type="time"
                                            value={formData.end_time}
                                            onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none"
                                        />
                                    </div>
                                </div>

                                {/* Cost */}
                                <div className="space-y-3">
                                    <div className="flex items-center gap-2">
                                        <input
                                            type="checkbox"
                                            id="is_paid"
                                            checked={formData.is_paid}
                                            onChange={(e) => setFormData({ ...formData, is_paid: e.target.checked })}
                                            className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                                        />
                                        <label htmlFor="is_paid" className="text-sm font-medium text-gray-700">Paid Service?</label>
                                    </div>

                                    {formData.is_paid && (
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">Amount (₹)</label>
                                            <input
                                                type="number"
                                                min="0"
                                                value={formData.suggested_amount}
                                                onChange={(e) => setFormData({ ...formData, suggested_amount: parseInt(e.target.value) || 0 })}
                                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none"
                                            />
                                        </div>
                                    )}
                                </div>

                                {/* Active Status (Only for edit) */}
                                {editingId !== null && (
                                    <div className="flex items-center gap-2 border-t pt-4">
                                        <input
                                            type="checkbox"
                                            id="is_active"
                                            checked={formData.is_active}
                                            onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                                            className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                                        />
                                        <label htmlFor="is_active" className="text-sm font-medium text-gray-700">Is Active?</label>
                                    </div>
                                )}

                                <div className="flex gap-3 pt-4 border-t border-gray-200">
                                    <button
                                        type="button"
                                        onClick={() => setIsModalOpen(false)}
                                        className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
                                    >
                                        {editingId !== null ? 'Update' : 'Add'}
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
