'use client';

import React, { useEffect, useState } from 'react';
import BlessingAnimation from '@/components/public/BlessingAnimation';
import { useLoad } from '@/hooks/useLoad';
import { getHome, getPoojas, getSevaDay } from '@/lib/api';
import { formatDate, formatTimeRange } from '@/lib/format';

const SCENE_MS = 12_000;
const REFRESH_MS = 5 * 60_000;
const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? '/api/v1';
const todayIST = () => new Date(Date.now() + 330 * 60_000).toISOString().slice(0, 10);

const QR_ITEMS = [
  { path: '/register', label: 'Register', hint: 'New devotee' },
  { path: '/login', label: 'Sign in', hint: 'See My Bookings' },
  { path: '/poojas', label: 'Book a seva', hint: 'Pay at the temple' },
];

/** Lobby TV display (open /tv fullscreen on the temple's TV): rotating scenes with
 * darshan timings, today's public blessings, festivals and announcements. A TV has
 * no keyboard, so register / sign in / book are QR codes the devotee scans with a phone. */
export default function TvPage() {
  const home = useLoad(getHome, []);
  const blessings = useLoad(async () => {
    const seva = (await getPoojas()).find((p) => p.public_blessings);
    return seva ? (await getSevaDay(seva.id, todayIST())).entries : [];
  }, []);
  const [scene, setScene] = useState(0);
  const [clock, setClock] = useState('');
  const reloadHome = home.reload;
  const reloadBlessings = blessings.reload;

  useEffect(() => {
    const tick = () => setClock(new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit' }));
    tick();
    const clockTimer = setInterval(tick, 1000);
    const sceneTimer = setInterval(() => setScene((s) => s + 1), SCENE_MS);
    const refreshTimer = setInterval(() => { reloadHome(); reloadBlessings(); }, REFRESH_MS);
    return () => { clearInterval(clockTimer); clearInterval(sceneTimer); clearInterval(refreshTimer); };
  }, [reloadHome, reloadBlessings]);

  const d = home.data;
  const entries = blessings.data ?? [];
  const scenes: { key: string; node: React.ReactNode }[] = [];
  if (d) {
    scenes.push({ key: 'welcome', node: (
      <Stage title={d.temple?.deity_name ?? 'Welcome'}>
        <p className="mt-6 animate-fadeUp text-5xl text-amber-200">{d.temple?.tagline ?? 'Om Namah Shivaya'}</p>
        <div className="mt-10 w-full max-w-md"><BlessingAnimation /></div>
      </Stage>) });
    if (d.timings.length) scenes.push({ key: 'timings', node: (
      <Stage title="Darshan Timings">
        <ul className="mt-8 space-y-6">
          {d.timings.map((t, i) => (
            <li key={t.id} style={{ animationDelay: `${i * 0.25}s` }} className="animate-fadeUp text-5xl">
              <span className="font-serif text-amber-300">{t.label}</span>
              <span className="ml-6 text-white">{formatTimeRange(t.start_time, t.end_time)}</span>
            </li>))}
        </ul>
      </Stage>) });
  }
  entries.forEach((e, i) => scenes.push({ key: `bless-${i}`, node: (
    <Stage title="Today's Blessings">
      {e.photo_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={e.photo_url} alt="" className="mt-6 max-h-[45vh] animate-fadeUp rounded-3xl border-4 border-amber-300 object-contain" />
      ) : (
        <div className="mt-6 w-full max-w-md"><BlessingAnimation /></div>)}
      <p className="mt-8 animate-fadeUp font-serif text-6xl text-white">{e.devotee_name}</p>
      <p className="mt-3 animate-fadeUp text-4xl text-amber-200">{e.occasion}</p>
    </Stage>) }));
  if (d?.festivals.length) scenes.push({ key: 'festivals', node: (
    <Stage title="Upcoming Festivals">
      <ul className="mt-8 space-y-6">
        {d.festivals.map((f, i) => (
          <li key={f.id} style={{ animationDelay: `${i * 0.25}s` }} className="animate-fadeUp text-5xl">
            <span className="font-serif text-amber-300">{f.name}</span>
            <span className="ml-6 text-white">{formatDate(f.festival_date, { day: 'numeric', month: 'long' })}</span>
          </li>))}
      </ul>
    </Stage>) });
  if (d?.announcements.length) scenes.push({ key: 'news', node: (
    <Stage title="Announcements">
      <ul className="mt-8 space-y-8">
        {d.announcements.map((a, i) => (
          <li key={a.id} style={{ animationDelay: `${i * 0.25}s` }} className="animate-fadeUp">
            <p className="font-serif text-4xl text-amber-300">{a.title}</p>
            {a.message && <p className="mt-2 text-3xl text-white/90">{a.message}</p>}
          </li>))}
      </ul>
    </Stage>) });

  const current = scenes.length ? scenes[scene % scenes.length] : null;
  const ticker = d?.announcements.map((a) => a.title).join('   ✦   ') ?? '';

  return (
    <main className="relative flex h-screen w-screen flex-col overflow-hidden bg-gradient-to-br from-maroon-dark via-maroon to-maroon-dark text-white">
      <Petals />
      <header className="relative z-10 flex items-center justify-between px-12 py-6">
        <h1 className="font-serif text-4xl text-amber-300">{d?.temple?.name ?? 'Temple'}</h1>
        <span className="text-4xl tabular-nums text-amber-100">{clock}</span>
      </header>
      <div className="relative z-10 flex min-h-0 flex-1 gap-8 px-12 pb-6">
        <section key={current?.key} className="flex flex-1 animate-slideIn flex-col justify-center">
          {current?.node ?? <p className="text-4xl text-white/70">{home.error ?? 'Loading…'}</p>}
        </section>
        <aside className="flex w-[22rem] shrink-0 flex-col justify-center self-center gap-5 rounded-3xl bg-cream p-6 text-maroon-dark">
          <p className="text-center font-serif text-2xl font-bold">Scan with your phone</p>
          {QR_ITEMS.map((q) => (
            <div key={q.path} className="flex items-center gap-4">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={`${API}/public/qr?path=${encodeURIComponent(q.path)}`} alt={`QR code: ${q.label}`} className="h-28 w-28 rounded-lg border border-amber-300" />
              <div><p className="text-2xl font-bold">{q.label}</p><p className="text-lg text-gray-600">{q.hint}</p></div>
            </div>))}
        </aside>
      </div>
      {ticker && (
        <footer className="relative z-10 overflow-hidden bg-black/30 py-3 text-3xl text-amber-100">
          <div className="flex w-max animate-marquee whitespace-nowrap">
            <span className="px-8">{ticker}</span><span className="px-8" aria-hidden="true">{ticker}</span>
          </div>
        </footer>)}
    </main>
  );
}

function Stage({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h2 className="animate-fadeUp font-serif text-7xl font-bold text-white">{title}</h2>
      <div className="mt-2 h-1 w-40 animate-fadeUp rounded bg-amber-400" />
      {children}
    </div>
  );
}

/** A few marigold petals drifting down the whole screen; off for reduced motion. */
function Petals() {
  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0 hidden motion-safe:block">
      {Array.from({ length: 10 }, (_, i) => (
        <span key={i} className="absolute top-0 animate-petalFall rounded-full bg-amber-400/60"
              style={{ left: `${(i * 10 + 4) % 100}%`, width: 10 + (i % 3) * 6, height: 10 + (i % 3) * 6, animationDelay: `${i * 1.3}s`, animationDuration: `${9 + (i % 4) * 2}s` }} />))}
    </div>
  );
}
