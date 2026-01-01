'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Calendar, Clock, Banknote } from 'lucide-react';

interface Pooja {
    id: number;
    name: string;
    start_time?: string;
    end_time?: string;
    is_paid?: boolean;
    suggested_amount?: number | null;
    description?: string;
}

export default function DailyPoojasPage() {
    const [poojas, setPoojas] = useState<Pooja[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchPoojas = async () => {
            try {
                const res = await api.get('/poojas');
                setPoojas(res.data);
            } catch (error) {
                console.error('Failed to fetch poojas:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchPoojas();
    }, []);

    return (
        <div className="max-w-7xl mx-auto px-4 py-12">
            <div className="text-center mb-16">
                <h1 className="text-4xl md:text-5xl font-bold text-templeDark mb-4">Daily Poojas</h1>
                <p className="text-gray-500 max-w-2xl mx-auto">
                    Participate in our daily rituals and seek the divine blessings of Lord Vinayaka.
                    We offer various sevas throughout the day for the well-being of all devotees.
                </p>
            </div>

            {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {[1, 2, 3, 4, 5, 6].map(i => (
                        <div key={i} className="h-64 bg-gray-50 rounded-3xl animate-pulse"></div>
                    ))}
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {poojas.map((pooja) => (
                        <div key={pooja.id} className="group bg-white rounded-3xl p-8 border border-gray-100 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
                            <div className="bg-templeGold/10 w-14 h-14 rounded-2xl flex items-center justify-center mb-6 text-templeGold group-hover:scale-110 transition-transform">
                                <Calendar className="w-7 h-7" />
                            </div>
                            <h3 className="text-2xl font-bold text-templeDark mb-3">{pooja.name}</h3>
                            <p className="text-gray-500 text-sm mb-6 line-clamp-2">
                                {pooja.description || 'Special morning rituals and archana for the deity.'}
                            </p>

                            <div className="space-y-3">
                                <div className="flex items-center gap-3 text-sm text-gray-600">
                                    <Clock className="w-4 h-4 text-templeGold" />
                                    <span>{pooja.start_time || '6:30 AM'} - {pooja.end_time || '7:30 AM'}</span>
                                </div>
                                <div className="flex items-center gap-3 text-sm text-gray-600">
                                    <Banknote className="w-4 h-4 text-templeGold" />
                                    <span>{pooja.is_paid ? `₹${pooja.suggested_amount}` : 'Free'}</span>
                                </div>
                            </div>

                            <button className="w-full mt-8 py-3 bg-templeDark text-templeGold rounded-xl font-bold hover:bg-slate-800 transition-colors flex items-center justify-center gap-2">
                                Book Seva
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
