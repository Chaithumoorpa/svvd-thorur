'use client';

import React, { useEffect, useState } from 'react';
import {
    getGallery,
    createGallery,
    updateGallery,
    deleteGallery,
    Gallery,
    GalleryCreate,
    GalleryUpdate,
} from '@/lib/api';
import { Plus, Edit2, Trash2, X, Image as ImageIcon } from 'lucide-react';

export default function GalleryPage() {
    const [items, setItems] = useState<Gallery[]>([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingItem, setEditingItem] = useState<Gallery | null>(null);

    // Form state
    const [formData, setFormData] = useState<GalleryCreate>({
        title: '',
        description: '',
        image_url: '',
        category: 'TEMPLE',
        is_active: true,
    });

    useEffect(() => {
        fetchGallery();
    }, []);

    const fetchGallery = async () => {
        try {
            const data = await getGallery();
            setItems(data);
        } catch (error) {
            console.error('Failed to fetch gallery items:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            if (editingItem) {
                await updateGallery(editingItem.id, formData);
            } else {
                await createGallery(formData);
            }
            setIsModalOpen(false);
            resetForm();
            fetchGallery();
        } catch (error) {
            console.error('Failed to save gallery item:', error);
            alert('Failed to save item. Please try again.');
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm('Are you sure you want to delete this item?')) return;
        try {
            await deleteGallery(id);
            fetchGallery();
        } catch (error) {
            console.error('Failed to delete item:', error);
            alert('Failed to delete item.');
        }
    };

    const openModal = (item?: Gallery) => {
        if (item) {
            setEditingItem(item);
            setFormData({
                title: item.title,
                description: item.description || '',
                image_url: item.image_url,
                category: item.category,
                is_active: item.is_active,
            });
        } else {
            setEditingItem(null);
            resetForm();
        }
        setIsModalOpen(true);
    };

    const resetForm = () => {
        setFormData({
            title: '',
            description: '',
            image_url: '',
            category: 'TEMPLE',
            is_active: true,
        });
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
            </div>
        );
    }

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-slate-900">Gallery Management</h1>
                <button
                    onClick={() => openModal()}
                    className="flex items-center gap-2 bg-slate-900 text-white px-4 py-2 rounded-md hover:bg-slate-800 transition-colors"
                >
                    <Plus className="w-4 h-4" />
                    Add Image
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {items.map((item) => (
                    <div
                        key={item.id}
                        className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden group"
                    >
                        <div className="relative aspect-video bg-gray-100">
                            <img
                                src={item.image_url}
                                alt={item.title}
                                className="w-full h-full object-cover"
                                onError={(e) => {
                                    // Fallback for broken images
                                    (e.target as HTMLImageElement).src = 'https://placehold.co/600x400?text=No+Image';
                                }}
                            />
                            <div className="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button
                                    onClick={() => openModal(item)}
                                    className="p-1.5 bg-white rounded-md shadow-sm hover:bg-gray-100 text-slate-700"
                                >
                                    <Edit2 className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={() => handleDelete(item.id)}
                                    className="p-1.5 bg-white rounded-md shadow-sm hover:bg-red-50 text-red-600"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                            <div className="absolute top-2 left-2">
                                <span className="px-2 py-1 bg-black/50 text-white text-xs rounded-md backdrop-blur-sm">
                                    {item.category}
                                </span>
                            </div>
                        </div>
                        <div className="p-4">
                            <h3 className="font-semibold text-slate-900 mb-1">{item.title}</h3>
                            {item.description && (
                                <p className="text-sm text-gray-500 line-clamp-2">
                                    {item.description}
                                </p>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
                    <div className="bg-white rounded-lg w-full max-w-md p-6 max-h-[90vh] overflow-y-auto">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-bold text-slate-900">
                                {editingItem ? 'Edit Image' : 'Add New Image'}
                            </h2>
                            <button
                                onClick={() => setIsModalOpen(false)}
                                className="text-gray-400 hover:text-gray-600"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">
                                    Title
                                </label>
                                <input
                                    type="text"
                                    required
                                    value={formData.title}
                                    onChange={(e) =>
                                        setFormData({ ...formData, title: e.target.value })
                                    }
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-500"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">
                                    Image URL
                                </label>
                                <input
                                    type="url"
                                    required
                                    value={formData.image_url}
                                    onChange={(e) =>
                                        setFormData({ ...formData, image_url: e.target.value })
                                    }
                                    placeholder="https://example.com/image.jpg"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-500"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">
                                    Category
                                </label>
                                <select
                                    value={formData.category}
                                    onChange={(e) =>
                                        setFormData({ ...formData, category: e.target.value })
                                    }
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-500"
                                >
                                    <option value="TEMPLE">Temple</option>
                                    <option value="FESTIVAL">Festival</option>
                                    <option value="EVENT">Event</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">
                                    Description
                                </label>
                                <textarea
                                    rows={3}
                                    value={formData.description}
                                    onChange={(e) =>
                                        setFormData({ ...formData, description: e.target.value })
                                    }
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-500"
                                />
                            </div>

                            <div className="flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    id="is_active"
                                    checked={formData.is_active}
                                    onChange={(e) =>
                                        setFormData({ ...formData, is_active: e.target.checked })
                                    }
                                    className="rounded border-gray-300 text-slate-900 focus:ring-slate-500"
                                />
                                <label htmlFor="is_active" className="text-sm font-medium text-slate-700">
                                    Active
                                </label>
                            </div>

                            <div className="flex gap-3 pt-4">
                                <button
                                    type="button"
                                    onClick={() => setIsModalOpen(false)}
                                    className="flex-1 px-4 py-2 border border-gray-300 text-slate-700 rounded-md hover:bg-gray-50 font-medium"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 px-4 py-2 bg-slate-900 text-white rounded-md hover:bg-slate-800 font-medium"
                                >
                                    {editingItem ? 'Update' : 'Create'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
