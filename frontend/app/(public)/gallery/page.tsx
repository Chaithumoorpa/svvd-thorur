'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { ImageIcon, Maximize2, X } from 'lucide-react';

interface GalleryItem {
    id: number;
    title: string;
    image_url: string;
    category?: string;
}

export default function GalleryPage() {
    const [items, setItems] = useState<GalleryItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedImage, setSelectedImage] = useState<string | null>(null);

    useEffect(() => {
        const fetchGallery = async () => {
            try {
                const res = await api.get('/gallery');
                setItems(res.data);
            } catch (error) {
                console.error('Failed to fetch gallery:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchGallery();
    }, []);

    return (
        <div className="max-w-7xl mx-auto px-4 py-12">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-16">
                <div>
                    <h1 className="text-4xl md:text-5xl font-bold text-templeDark mb-4">Temple Gallery</h1>
                    <p className="text-gray-500 max-w-xl">
                        A visual journey through the sacred spaces, vibrant festivals, and daily rituals
                        of Sri Varasiddhi Vinayaka Swamy Temple.
                    </p>
                </div>
                <div className="flex gap-2">
                    {['All', 'Temple', 'Festivals', 'Sevas'].map(cat => (
                        <button key={cat} className="px-5 py-2 rounded-full border border-gray-200 text-sm font-medium hover:bg-templeDark hover:text-white hover:border-templeDark transition-all">
                            {cat}
                        </button>
                    ))}
                </div>
            </div>

            {loading ? (
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
                        <div key={i} className="aspect-square bg-gray-50 rounded-3xl animate-pulse"></div>
                    ))}
                </div>
            ) : (
                <div className="columns-1 sm:columns-2 lg:columns-3 xl:columns-4 gap-6 space-y-6">
                    {items.map((item) => (
                        <div
                            key={item.id}
                            className="relative group rounded-3xl overflow-hidden cursor-zoom-in"
                            onClick={() => setSelectedImage(`http://localhost:8000${item.image_url}`)}
                        >
                            <img
                                src={`http://localhost:8000${item.image_url}`}
                                alt={item.title}
                                className="w-full h-auto object-cover transform group-hover:scale-110 transition-transform duration-700"
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-6">
                                <p className="text-white font-bold text-lg mb-1">{item.title}</p>
                                <div className="flex items-center gap-2 text-templeGold text-xs uppercase font-bold tracking-widest">
                                    <ImageIcon className="w-3 h-3" />
                                    {item.category || 'Temple View'}
                                </div>
                            </div>
                            <div className="absolute top-4 right-4 bg-white/20 backdrop-blur-md p-2 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity">
                                <Maximize2 className="w-5 h-5 text-white" />
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Lightbox */}
            {selectedImage && (
                <div className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center p-4 backdrop-blur-sm" onClick={() => setSelectedImage(null)}>
                    <button
                        className="absolute top-8 right-8 text-white/50 hover:text-white transition-colors"
                        onClick={() => setSelectedImage(null)}
                    >
                        <X className="w-10 h-10" />
                    </button>
                    <img
                        src={selectedImage}
                        alt="Full size"
                        className="max-w-full max-h-full rounded-2xl shadow-2xl animate-in zoom-in-95 duration-300"
                    />
                </div>
            )}
        </div>
    );
}
