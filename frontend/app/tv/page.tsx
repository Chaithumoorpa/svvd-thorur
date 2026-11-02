'use client';

import React, { useEffect, useState } from 'react';
import { Calendar, Clock, Flower2, Image as ImageIcon, Megaphone, Sparkles, Users } from 'lucide-react';
import BlessingAnimation from '@/components/public/BlessingAnimation';
import { useLoad } from '@/hooks/useLoad';
import { getCommittee, getGallery, getHome, getPoojas, getSevaDay } from '@/lib/api';
import { formatDate, formatMoney, formatTimeRange } from '@/lib/format';
import { ALL_TV_SECTIONS } from '@/lib/tv';

const SCENE_MS = 12_000; // keep in step with the `progress` animation in tailwind.config.cjs
const REFRESH_MS = 5 * 60_000;
const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? '/api/v1';
const todayIST = () => new Date(Date.now() + 330 * 60_000).toISOString().slice(0, 10);

const QR_ITEMS = [
  { path: '/register', label: 'Register', hint: 'New devotee' },
  { path: '/login', label: 'Sign in', hint: 'See My Bookings' },
  { path: '/poojas', label: 'Book a seva', hint: 'Pay at the temple' },
];

/** Lobby TV display (open /tv fullscreen on the temple's TV). The scenes shown are chosen in
 * Admin > Temple Information > "Show on lobby TV". A TV has no keyboard, so register / sign in /
 * book are QR codes the devotee scans with a phone. Public data only - nothing private is fetched. */
export default function TvPage() {
  const home = useLoad(getHome, []);
  const extra = useLoad(async () => {
    const [poojas, gallery, committee] = await Promise.all([getPoojas(), getGallery().catch(() => []), getCommittee().catch(() => [])]);
    const seva = poojas.find((p) => p.public_blessings);
    const blessings = seva ? (await getSevaDay(seva.id, todayIST())).entries : [];
    return { poojas, gallery, committee, blessings };
  }, []);
  const [scene, setScene] = useState(0);
  const [clock, setClock] = useState('');
  const reloadHome = home.reload;
  const reloadExtra = extra.reload;

  useEffect(() => {
    const tick = () => setClock(new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit' }));
    tick();
    const timers = [setInterval(tick, 1000), setInterval(() => setScene((s) => s + 1), SCENE_MS),
      setInterval(() => { reloadHome(); reloadExtra(); }, REFRESH_MS)];
    return () => timers.forEach(clearInterval);
  }, [reloadHome, reloadExtra]);

  const d = home.data;
  const x = extra.data;
  const shown = d?.temple?.tv_sections ?? ALL_TV_SECTIONS;
  const on = (k: string) => shown.includes(k);
  const scenes: { key: string; node: React.ReactNode }[] = [];

  if (d && on('welcome')) scenes.push({ key: 'welcome', node: (
    <div className="flex flex-col items-center text-center">
      <p className="animate-fadeUp text-4xl text-amber-200">ఓం గం గణపతయే నమః</p>
      <h2 className="mt-4 animate-fadeUp bg-gradient-to-r from-amber-200 via-white to-amber-200 bg-[length:200%_auto] bg-clip-text font-serif text-8xl font-bold text-transparent animate-shimmer">
        {d.temple?.deity_name ?? 'Welcome'}
      </h2>
      <Lotus className="mt-6 animate-fadeUp" />
      <p className="mt-6 animate-fadeUp text-5xl text-amber-100">{d.temple?.tagline ?? 'Welcome, devotees'}</p>
    </div>) });
  if (d && on('timings') && d.timings.length) scenes.push({ key: 'timings', node: (
    <Stage icon={Clock} title="Darshan Timings">
      <div className="mt-10 grid gap-6">
        {d.timings.map((t, i) => (
          <div key={t.id} style={{ animationDelay: `${i * 0.25}s` }} className="flex animate-fadeUp items-center justify-between rounded-2xl border border-amber-300/30 bg-white/10 px-8 py-5 backdrop-blur">
            <div><p className="font-serif text-4xl text-amber-300">{t.label}</p>{t.note && <p className="text-2xl text-white/70">{t.note}</p>}</div>
            <p className="text-5xl font-semibold tabular-nums">{formatTimeRange(t.start_time, t.end_time)}</p>
          </div>))}
      </div>
    </Stage>) });
  if (x && on('poojas') && x.poojas.length) scenes.push({ key: 'poojas', node: (
    <Stage icon={Flower2} title="Poojas & Sevas">
      <div className="mt-10 grid grid-cols-2 gap-5">
        {x.poojas.slice(0, 6).map((p, i) => (
          <div key={p.id} style={{ animationDelay: `${i * 0.2}s` }} className="animate-fadeUp rounded-2xl border border-amber-300/30 bg-white/10 p-6 backdrop-blur">
            <p className="font-serif text-3xl text-white">{p.name}</p>
            <p className="mt-2 inline-block rounded-full bg-amber-400 px-4 py-1 text-2xl font-bold text-maroon-dark">{p.is_paid ? formatMoney(p.suggested_amount) : 'Free'}</p>
          </div>))}
      </div>
    </Stage>) });
  if (x && on('blessings')) x.blessings.forEach((e, i) => scenes.push({ key: `bless-${i}`, node: (
    <Stage icon={Sparkles} title="Today's Blessings">
      {e.photo_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={e.photo_url} alt="" className="mt-6 max-h-[42vh] animate-fadeUp rounded-3xl border-4 border-amber-300 object-contain shadow-2xl" />
      ) : (
        <div className="mt-6 w-full max-w-md"><BlessingAnimation /></div>)}
      <p className="mt-8 animate-fadeUp font-serif text-7xl text-white">{e.devotee_name}</p>
      <p className="mt-3 animate-fadeUp text-4xl text-amber-200">{e.occasion}</p>
    </Stage>) }));
  if (d && on('festivals') && d.festivals.length) scenes.push({ key: 'festivals', node: (
    <Stage icon={Calendar} title="Upcoming Festivals">
      <div className="mt-10 grid gap-6">
        {d.festivals.map((f, i) => (
          <div key={f.id} style={{ animationDelay: `${i * 0.25}s` }} className="flex animate-fadeUp items-center gap-8 rounded-2xl border border-amber-300/30 bg-white/10 px-8 py-5 backdrop-blur">
            <div className="rounded-xl bg-amber-400 px-5 py-3 text-center font-bold text-maroon-dark">
              <p className="text-5xl leading-none">{f.festival_date ? new Date(f.festival_date).getDate() : ''}</p>
              <p className="text-xl uppercase">{formatDate(f.festival_date, { month: 'short' })}</p>
            </div>
            <div><p className="font-serif text-4xl text-white">{f.name}</p>{f.description && <p className="text-2xl text-white/70">{f.description}</p>}</div>
          </div>))}
      </div>
    </Stage>) });
  if (d && on('announcements') && d.announcements.length) scenes.push({ key: 'news', node: (
    <Stage icon={Megaphone} title="Announcements">
      <div className="mt-10 space-y-6">
        {d.announcements.map((a, i) => (
          <div key={a.id} style={{ animationDelay: `${i * 0.25}s` }} className="animate-fadeUp rounded-2xl border-l-8 border-amber-400 bg-white/10 px-8 py-5 backdrop-blur">
            <p className="font-serif text-4xl text-amber-300">{a.title}</p>
            {a.message && <p className="mt-2 text-3xl text-white/90">{a.message}</p>}
          </div>))}
      </div>
    </Stage>) });
  if (x && on('gallery')) x.gallery.slice(0, 8).forEach((g) => scenes.push({ key: `gal-${g.id}`, node: (
    <div className="relative h-[68vh] overflow-hidden rounded-3xl border-4 border-amber-300/70 shadow-2xl">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={g.image_url} alt={g.title} className="h-full w-full animate-kenburns bg-white/10 object-contain" />
      <div className="absolute inset-x-0 bottom-0 flex items-center gap-4 bg-gradient-to-t from-black/80 to-transparent px-8 pb-6 pt-16">
        <ImageIcon className="h-9 w-9 text-amber-300" aria-hidden="true" /><p className="font-serif text-5xl">{g.title}</p>
      </div>
    </div>) }));
  if (x && on('committee') && x.committee.length) scenes.push({ key: 'committee', node: (
    <Stage icon={Users} title="Temple Committee">
      <div className="mt-10 grid grid-cols-4 gap-8">
        {x.committee.slice(0, 8).map((m, i) => (
          <div key={m.id} style={{ animationDelay: `${i * 0.15}s` }} className="animate-fadeUp text-center">
            {m.photo_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={m.photo_url} alt="" className="mx-auto h-40 w-40 rounded-full border-4 border-amber-300 object-cover" />
            ) : (
              <div className="mx-auto flex h-40 w-40 items-center justify-center rounded-full border-4 border-amber-300 bg-white/10 font-serif text-6xl text-amber-200">{m.name.charAt(0)}</div>)}
            <p className="mt-4 text-3xl font-semibold">{m.name}</p><p className="text-2xl text-amber-300">{m.position}</p>
          </div>))}
      </div>
    </Stage>) });

  const current = scenes.length ? scenes[scene % scenes.length] : null;
  const ticker = on('ticker') ? d?.announcements.map((a) => a.title).join('   ✦   ') ?? '' : '';

  return (
    <main className="relative flex h-screen w-screen flex-col overflow-hidden bg-[linear-gradient(120deg,#3d0a0a,#7a1c1c,#4a0f0f,#8a2a14,#3d0a0a)] bg-[length:300%_300%] text-white animate-gradientShift">
      <Mandala />
      <Petals />
      <header className="relative z-10 flex items-center gap-6 px-12 py-5">
        <div className="relative">
          <div className="absolute inset-0 animate-glowPulse rounded-full bg-amber-400/50 blur-xl" />
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/logo.png" alt="" className="relative h-24 w-24 rounded-full border-2 border-amber-300 bg-white object-cover" />
        </div>
        <h1 className="flex-1 bg-gradient-to-r from-amber-300 via-white to-amber-300 bg-[length:200%_auto] bg-clip-text font-serif text-5xl font-bold text-transparent animate-shimmer">
          {d?.temple?.name ?? 'Temple'}
        </h1>
        <Diya /><span className="text-5xl tabular-nums text-amber-100">{clock}</span><Diya />
      </header>
      <div className="relative z-10 flex min-h-0 flex-1 gap-10 px-12 pb-6">
        <section className="flex min-w-0 flex-1 flex-col">
          <div className="h-1.5 overflow-hidden rounded bg-white/15">
            <div key={current?.key} className="h-full animate-progress bg-gradient-to-r from-amber-400 to-amber-200" />
          </div>
          <div key={current?.key} className="flex flex-1 animate-slideIn flex-col justify-center">
            {current?.node ?? <p className="text-4xl text-white/70">{home.error ?? (d ? 'Nothing selected to show' : 'Loading…')}</p>}
          </div>
          <div className="flex justify-center gap-2" aria-hidden="true">
            {scenes.map((s) => <span key={s.key} className={`h-2.5 rounded-full transition-all duration-500 ${s.key === current?.key ? 'w-10 bg-amber-300' : 'w-2.5 bg-white/30'}`} />)}
          </div>
        </section>
        {on('qr') && (
          <aside className="flex w-[22rem] shrink-0 flex-col justify-center gap-5 self-center rounded-3xl border-2 border-amber-300/60 bg-cream p-6 text-maroon-dark shadow-2xl">
            <p className="text-center font-serif text-2xl font-bold">Scan with your phone</p>
            {QR_ITEMS.map((q) => (
              <div key={q.path} className="flex items-center gap-4">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={`${API}/public/qr?path=${encodeURIComponent(q.path)}`} alt={`QR code: ${q.label}`} className="h-28 w-28 rounded-lg border border-amber-300" />
                <div><p className="text-2xl font-bold">{q.label}</p><p className="text-lg text-gray-600">{q.hint}</p></div>
              </div>))}
          </aside>)}
      </div>
      {ticker && (
        <footer className="relative z-10 overflow-hidden border-t border-amber-300/30 bg-black/40 py-3 text-3xl text-amber-100">
          <div className="flex w-max animate-marquee whitespace-nowrap">
            <span className="px-8">{ticker}</span><span className="px-8" aria-hidden="true">{ticker}</span>
          </div>
        </footer>)}
    </main>
  );
}

function Stage({ icon: Icon, title, children }: { icon: React.ComponentType<{ className?: string }>; title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex animate-fadeUp items-center gap-5">
        <Icon className="h-14 w-14 text-amber-300" />
        <h2 className="font-serif text-7xl font-bold">{title}</h2>
      </div>
      <Lotus className="mt-3 !justify-start" />
      {children}
    </div>
  );
}

/** Lotus between two rules - the same ornament as the public site, in gold. */
function Lotus({ className = '' }: { className?: string }) {
  return (
    <div className={`flex items-center justify-center gap-3 text-amber-400 ${className}`} aria-hidden="true">
      <span className="h-px w-24 bg-gradient-to-r from-transparent to-amber-400/80" />
      <svg width="36" height="36" viewBox="0 0 32 32" fill="currentColor"><path d="M16 3c2 4 2 8 0 12-2-4-2-8 0-12zM16 29c2-4 2-8 0-12-2 4-2 8 0 12zM3 16c4-2 8-2 12 0-4 2-8 2-12 0zM29 16c-4-2-8-2-12 0 4 2 8 2 12 0z" opacity=".85" /><circle cx="16" cy="16" r="2.6" /></svg>
      <span className="h-px w-24 bg-gradient-to-l from-transparent to-amber-400/80" />
    </div>
  );
}

/** A little oil lamp with a flickering flame. */
function Diya() {
  return (
    <svg width="52" height="52" viewBox="0 0 52 52" aria-hidden="true">
      <path className="origin-bottom animate-flicker" style={{ transformBox: 'fill-box' }} d="M26 4c6 8 8 13 4 18-1.500 2-5 2-6.500 0C20 17 22 12 26 4z" fill="#ffb02e" />
      <path d="M26 12c3 4 3 7 1 9-1 1-2.500 1-3 0-1.500-2 0-5 2-9z" fill="#fff3c4" />
      <path d="M6 30h40c0 9-9 16-20 16S6 39 6 30z" fill="#c2410c" /><path d="M6 30h40" stroke="#fbbf24" strokeWidth="2" />
    </svg>
  );
}

/** Huge faint rangoli ring turning slowly behind everything. */
function Mandala() {
  return (
    <svg aria-hidden="true" viewBox="-100 -100 200 200" className="pointer-events-none absolute -right-48 top-1/2 h-[120vh] w-[120vh] -translate-y-1/2 animate-spinSlow text-amber-300 opacity-[0.10]">
      {[95, 80, 62, 40].map((r) => <circle key={r} r={r} fill="none" stroke="currentColor" strokeWidth="0.6" strokeDasharray={r % 2 ? '2 3' : undefined} />)}
      {Array.from({ length: 16 }, (_, i) => <ellipse key={i} cx="0" cy="-70" rx="9" ry="22" fill="currentColor" transform={`rotate(${i * 22.5})`} />)}
      {Array.from({ length: 8 }, (_, i) => <ellipse key={i} cx="0" cy="-34" rx="5" ry="12" fill="currentColor" transform={`rotate(${i * 45 + 22.5})`} />)}
    </svg>
  );
}

/** A few marigold petals drifting down the whole screen; off for reduced motion. */
function Petals() {
  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0 hidden motion-safe:block">
      {Array.from({ length: 14 }, (_, i) => (
        <span key={i} className="absolute top-0 animate-petalFall rounded-full bg-amber-400/60"
              style={{ left: `${(i * 7 + 3) % 100}%`, width: 10 + (i % 3) * 6, height: 10 + (i % 3) * 6, animationDelay: `${i * 1.1}s`, animationDuration: `${9 + (i % 4) * 2}s` }} />))}
    </div>
  );
}
