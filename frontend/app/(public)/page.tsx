'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import DeityCarousel from '@/components/DeityCarousel';
import { getAnnouncements, getFestivals, getPoojas, Festival } from '@/lib/api';

/* ---------------- TYPES ---------------- */

type Announcement = {
  id: number;
  title: string;
  message: string;
  start_date?: string;
  is_active: boolean;
};

type Pooja = {
  id: number;
  name: string;
  start_time?: string;
  is_active: boolean;
};

type HomeErrors = {
  announcements?: boolean;
  festivals?: boolean;
  poojas?: boolean;
};

/* ---------------- COMPONENT ---------------- */

export default function Home() {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [festivals, setFestivals] = useState<Festival[]>([]);
  const [poojas, setPoojas] = useState<Pooja[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errors, setErrors] = useState<HomeErrors>({});

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);

      try {
        const [annData, festData, poojaData] = await Promise.all([
          getAnnouncements().catch(err => {
            console.error(err);
            setErrors((prev: HomeErrors) => ({ ...prev, announcements: true }));
            return [];
          }),
          getFestivals().catch(err => {
            console.error(err);
            setErrors((prev: HomeErrors) => ({ ...prev, festivals: true }));
            return [];
          }),
          getPoojas().catch(err => {
            console.error(err);
            setErrors((prev: HomeErrors) => ({ ...prev, poojas: true }));
            return [];
          }),
        ]);

        setAnnouncements(
          annData.filter((a: Announcement) => a.is_active).slice(0, 3)
        );

        setFestivals(
          festData
            .filter((f: Festival) => f.is_active)
            .sort(
              (a: Festival, b: Festival) =>
                new Date(a.date || '').getTime() -
                new Date(b.date || '').getTime()
            )
            .slice(0, 3)
        );

        setPoojas(
          poojaData.filter((p: Pooja) => p.is_active).slice(0, 4)
        );
      } catch (err) {
        console.error('Critical error fetching homepage data', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const Skeleton = ({ className }: { className: string }) => (
    <div className={`animate-pulse bg-gray-200 rounded-lg ${className}`} />
  );

  return (
    <div className="bg-templeWhite min-h-screen">

      {/* HERO */}
      <section className="w-full">
        <DeityCarousel />
      </section>

      {/* ANNOUNCEMENTS */}
      <section className="max-w-7xl mx-auto px-4 py-16">
        <div className="flex justify-between items-end mb-10 border-b-2 border-templeGold pb-4">
          <div>
            <h2 className="text-3xl font-serif font-bold text-templeDark">
              Announcements
            </h2>
            <p className="text-gray-600 mt-2">
              Stay updated with the latest temple news
            </p>
          </div>
          <Link href="/announcements" className="text-templeGold font-semibold hover:underline">
            View All →
          </Link>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {loading ? (
            [1, 2, 3].map(i => <Skeleton key={i} className="h-48" />)
          ) : announcements.length ? (
            announcements.map(ann => (
              <div
                key={ann.id}
                className="bg-white p-6 rounded-xl shadow border-l-4 border-templeGold"
              >
                <p className="text-xs text-gray-500 mb-2">
                  {ann.start_date
                    ? new Date(ann.start_date).toLocaleDateString('en-IN')
                    : 'Announcement'}
                </p>
                <h3 className="text-xl font-bold text-templeDark mb-2">
                  {ann.title}
                </h3>
                <p className="text-gray-600 text-sm line-clamp-3">
                  {ann.message}
                </p>
              </div>
            ))
          ) : (
            <p className="col-span-full text-center text-gray-500 italic">
              No announcements available
            </p>
          )}
        </div>
      </section>

      {/* FESTIVALS */}
      <section className="max-w-7xl mx-auto px-4 py-16">
        <div className="flex justify-between items-end mb-10 border-b-2 border-red-800 pb-4">
          <div>
            <h2 className="text-3xl font-serif font-bold text-templeDark">
              Upcoming Festivals
            </h2>
            <p className="text-gray-600 mt-2">
              Join us in divine celebrations
            </p>
          </div>
          <Link href="/festivals" className="text-red-800 font-semibold hover:underline">
            View All →
          </Link>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {loading ? (
            [1, 2, 3].map(i => <Skeleton key={i} className="h-64" />)
          ) : festivals.length ? (
            festivals.map(fest => (
              <div key={fest.id} className="bg-white rounded-xl shadow">
                <div className="bg-red-800 text-white p-4 text-center">
                  <div className="text-2xl font-bold">
                    {fest.date ? new Date(fest.date).getDate() : '-'}
                  </div>
                  <div className="text-xs uppercase">
                    {fest.date ? new Date(fest.date).toLocaleString('default', {
                      month: 'long',
                    }) : 'TBD'}
                  </div>
                </div>
                <div className="p-6">
                  <h3 className="text-xl font-bold">{fest.name}</h3>
                  <p className="text-gray-600 text-sm line-clamp-3">
                    {fest.description}
                  </p>
                </div>
              </div>
            ))
          ) : (
            <p className="col-span-full text-center text-gray-500 italic">
              No upcoming festivals
            </p>
          )}
        </div>
      </section>

      {/* DAILY POOJAS */}
      <section className="bg-red-900 py-20 text-white">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-4xl font-serif font-bold text-center mb-12 italic">
            Daily Rituals
          </h2>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {loading ? (
              [1, 2, 3, 4].map(i => (
                <Skeleton key={i} className="h-40 bg-red-800" />
              ))
            ) : poojas.length ? (
              poojas.map(pooja => (
                <div
                  key={pooja.id}
                  className="bg-white/10 p-6 rounded-xl text-center"
                >
                  <div className="text-3xl mb-4">🕉️</div>
                  <h3 className="text-xl font-bold">{pooja.name}</h3>
                  <p className="text-templeGold text-sm">
                    {pooja.start_time?.slice(0, 5) || 'Anytime'}
                  </p>
                </div>
              ))
            ) : (
              <p className="col-span-full text-center italic">
                No poojas available
              </p>
            )}
          </div>

          <div className="mt-12 text-center">
            <Link
              href="/poojas"
              className="bg-templeGold text-templeDark px-10 py-3 rounded-full font-bold"
            >
              Book a Pooja
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
