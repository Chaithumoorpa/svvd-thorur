'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Megaphone, Bell, Calendar, ChevronRight } from 'lucide-react';

interface Announcement {
  id: number;
  title: string;
  message?: string;
  description?: string;
  date?: string;
  created_at?: string;
}

export default function AnnouncementsPage() {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await api.get('/announcements');
        setAnnouncements(res.data);
      } catch (error) {
        console.error('Failed to fetch announcements:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-4 py-12">
      <div className="flex items-center gap-4 mb-12">
        <div className="bg-templeGold/20 p-4 rounded-2xl text-templeGold">
          <Megaphone className="w-8 h-8" />
        </div>
        <div>
          <h1 className="text-4xl font-bold text-templeDark">Announcements</h1>
          <p className="text-gray-500">Stay updated with the latest news and happenings at the temple.</p>
        </div>
      </div>

      {loading ? (
        <div className="space-y-6">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-40 bg-gray-50 rounded-3xl animate-pulse"></div>
          ))}
        </div>
      ) : announcements.length > 0 ? (
        <div className="space-y-6">
          {announcements.map((ann) => (
            <div key={ann.id} className="group bg-white p-8 rounded-3xl border border-gray-100 shadow-sm hover:shadow-md transition-all">
              <div className="flex justify-between items-start gap-4 mb-4">
                <div className="flex items-center gap-2 text-templeGold">
                  <Bell className="w-4 h-4" />
                  <span className="text-xs font-bold uppercase tracking-widest">Notice</span>
                </div>
                <div className="flex items-center gap-2 text-gray-400 text-xs">
                  <Calendar className="w-4 h-4" />
                  {new Date(ann.created_at || ann.date || Date.now()).toLocaleDateString()}
                </div>
              </div>
              <h3 className="text-2xl font-bold text-templeDark mb-3 group-hover:text-templeGold transition-colors">
                {ann.title}
              </h3>
              <p className="text-gray-600 leading-relaxed">
                {ann.message || ann.description}
              </p>
              <div className="mt-6 flex justify-end">
                <button className="text-sm font-bold text-templeDark hover:text-templeGold flex items-center gap-1 transition-colors">
                  Read More <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-20 bg-gray-50 rounded-[3rem] border border-dashed border-gray-200">
          <Megaphone className="w-16 h-16 text-gray-200 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-400">No active announcements</h2>
          <p className="text-gray-400">Check back later for updates.</p>
        </div>
      )}
    </div>
  );
}
