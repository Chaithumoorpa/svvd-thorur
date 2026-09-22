import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { useTranslations } from 'next-intl';
import { CalendarDays, MapPin } from 'lucide-react';
import JsonLd from '@/components/public/JsonLd';
import { PageShell } from '@/components/public/SectionHeading';
import { formatDate, parseDate, todayISO } from '@/lib/format';
import { fetchFestivals } from '@/lib/server-api';
import { SITE_URL } from '@/lib/site';
import type { Festival } from '@/lib/types';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('metadata.festivals');
  return { title: t('title'), description: t('description') };
}

const ended = (f: Festival, today: string) => !!f.festival_date && (f.end_date ?? f.festival_date) < today;

function FestivalCard({ f, muted }: { f: Festival; muted?: boolean }) {
  const t = useTranslations('festivals');
  const d = f.festival_date ? parseDate(f.festival_date) : null;
  return (
    <article className={`flex overflow-hidden rounded-2xl border bg-white shadow-sm ${muted ? 'border-gray-200 opacity-75' : 'border-amber-200'}`}>
      <div className={`flex w-24 flex-none flex-col items-center justify-center px-2 py-4 text-center text-white ${muted ? 'bg-gray-500' : 'bg-maroon'}`}>
        <span className="font-serif text-3xl font-bold leading-none">{d ? d.getDate() : '—'}</span>
        <span className="mt-1 text-xs uppercase tracking-wider text-amber-100">{d ? d.toLocaleString('en-IN', { month: 'short', year: 'numeric' }) : t('dateTba')}</span>
      </div>
      <div className="min-w-0 flex-1 p-5">
        <h3 className="font-serif text-xl font-bold text-maroon">{f.name}</h3>
        <p className="mt-1 flex flex-wrap items-center gap-x-3 text-xs text-gray-500">
          {f.end_date && f.festival_date && <span className="inline-flex items-center gap-1"><CalendarDays className="h-3 w-3" aria-hidden="true" />{formatDate(f.festival_date)} – {formatDate(f.end_date)}</span>}
          {f.location && <span className="inline-flex items-center gap-1"><MapPin className="h-3 w-3" aria-hidden="true" />{f.location}</span>}
        </p>
        {f.description && <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-gray-700">{f.description}</p>}
      </div>
    </article>
  );
}

export default async function FestivalsPage() {
  const festivals = await fetchFestivals();
  const today = todayISO();
  const upcoming = festivals.filter((f) => !ended(f, today));
  const past = festivals.filter((f) => ended(f, today)).reverse();
  const t = await getTranslations('festivals');

  const jsonLd = {
    '@context': 'https://schema.org',
    '@graph': upcoming.filter((f) => f.festival_date).map((f) => ({
      '@type': 'Event',
      name: f.name,
      startDate: f.festival_date,
      ...(f.end_date ? { endDate: f.end_date } : {}),
      ...(f.description ? { description: f.description } : {}),
      eventAttendanceMode: 'https://schema.org/OfflineEventAttendanceMode',
      url: `${SITE_URL}/festivals`,
    })),
  };

  return (
    <PageShell title={t('title')} subtitle={t('subtitle')} narrow>
      {upcoming.length > 0 && <JsonLd data={jsonLd} />}
      <section aria-labelledby="up-heading">
        <h2 id="up-heading" className="mb-4 font-serif text-2xl font-bold text-maroon">{t('upcomingHeading')}</h2>
        {upcoming.length ? (
          <div className="space-y-4">{upcoming.map((f) => <FestivalCard key={f.id} f={f} />)}</div>
        ) : (
          <p className="rounded-xl border border-dashed border-amber-300 bg-white p-8 text-center text-gray-500">{t('noUpcoming')}</p>
        )}
      </section>

      {past.length > 0 && (
        <section aria-labelledby="past-heading" className="mt-12">
          <h2 id="past-heading" className="mb-4 font-serif text-2xl font-bold text-gray-600">{t('pastHeading')}</h2>
          <div className="space-y-4">{past.slice(0, 6).map((f) => <FestivalCard key={f.id} f={f} muted />)}</div>
        </section>
      )}
    </PageShell>
  );
}
