'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Sparkles, Calendar, MapPin, ChevronRight } from 'lucide-react';

interface Festival {
    id: number;
    name: string;
    date: string;
    description: string;
}

export default function FestivalSevasPage() {
    const [festivals, setFestivals] = useState<Festival[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchFestivals = async () => {
            try {
                const res = await api.get('/festivals');
                setFestivals(res.data);
            } catch (error) {
                console.error('Failed to fetch festivals:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchFestivals();
    }, []);

    return (
        <div className="max-w-7xl mx-auto px-4 py-12">
            <div className="relative rounded-[3rem] overflow-hidden bg-slate-900 px-8 py-20 text-center mb-16">
                <div className="absolute inset-0 opacity-20 bg-[url('https://images.unsplash.com/photo-1534073828943-f801091bb18c?q=80&w=2000')] bg-cover bg-center"></div>
                <div className="relative z-10">
                    <span className="inline-block px-4 py-1.5 rounded-full bg-templeGold/20 text-templeGold text-xs font-bold uppercase tracking-wider mb-6">
                        Upcoming Events
                    </span>
                    <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">Festival Sevas</h1>
                    <p className="text-gray-300 max-w-2xl mx-auto text-lg">
                        Experience the grandeur of traditional festivals and participate in special sevas
                        organized during auspicious times of the year.
                    </p>
                </div>
            </div>

            {loading ? (
                <div className="space-y-6">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="h-48 bg-gray-50 rounded-3xl animate-pulse"></div>
                    ))}
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-8">
                    {festivals.map((festival) => (
                        <div key={festival.id} className="group bg-white rounded-3xl border border-gray-100 shadow-sm overflow-hidden flex flex-col md:flex-row hover:shadow-xl transition-all duration-300">
                            <div className="md:w-64 bg-templeGold/5 flex flex-col items-center justify-center p-8 border-r border-gray-50">
                                <span className="text-templeGold font-black text-4xl mb-2">
                                    {new Date(festival.date).getDate()}
                                </span>
                                <span className="text-templeDark font-bold uppercase tracking-widest text-sm">
                                    {new Date(festival.date).toLocaleString('default', { month: 'short' })}
                                </span>
                                <span className="text-gray-400 text-xs mt-2">
                                    {new Date(festival.date).getFullYear()}
                                </span>
                            </div>
                            <div className="flex-1 p-8">
                                <div className="flex items-center gap-2 text-templeGold mb-4">
                                    <Sparkles className="w-5 h-5" />
                                    <span className="text-sm font-bold uppercase tracking-wider">Festival Special</span>
                                </div>
                                <h3 className="text-3xl font-bold text-templeDark mb-4">{festival.name}</h3>
                                <p className="text-gray-500 mb-8 leading-relaxed max-w-3xl">
                                    {festival.description}
                                </p>
                                <div className="flex flex-wrap gap-4 items-center justify-between pt-6 border-t border-gray-50">
                                    <div className="flex items-center gap-2 text-gray-400 text-sm">
                                        <MapPin className="w-4 h-4" />
                                        Main Temple Complex
                                    </div>
                                    <button className="flex items-center gap-2 text-templeGold font-bold hover:gap-3 transition-all">
                                        Register for Seva <ChevronRight className="w-5 h-5" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
