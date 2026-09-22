import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { Clock, Moon, Sun } from 'lucide-react';
import { PageShell } from '@/components/public/SectionHeading';
import { formatTimeRange } from '@/lib/format';
import { fetchPoojas, fetchTimings } from '@/lib/server-api';
import { formatTime } from '@/lib/format';
import { localizedAlternates } from '@/lib/site';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('metadata.timings');
  return { title: t('title'), description: t('description'), alternates: await localizedAlternates('/timings') };
}

export default async function TimingsPage() {
  const [timings, poojas] = await Promise.all([fetchTimings(), fetchPoojas()]);
  const daily = poojas.filter((p) => p.pooja_type === 'daily' && p.start_time);
  const t = await getTranslations('timings');

  return (
    <PageShell title={t('title')} subtitle={t('subtitle')} narrow>
      {timings.length ? (
        <div className="grid gap-6 md:grid-cols-2">
          {timings.map((timing, i) => {
            const Icon = i % 2 === 0 ? Sun : Moon;
            const dark = i % 2 === 1;
            return (
              <section key={timing.id} className={`rounded-2xl p-7 shadow-sm ${dark ? 'bg-maroon-dark text-white' : 'border border-amber-200 bg-white'}`}>
                <div className="mb-3 flex items-center gap-3">
                  <Icon className={`h-7 w-7 ${dark ? 'text-saffron-light' : 'text-saffron'}`} aria-hidden="true" />
                  <h2 className={`font-serif text-2xl font-bold ${dark ? '' : 'text-maroon'}`}>{timing.label}</h2>
                </div>
                <p className={`text-3xl font-bold ${dark ? 'text-saffron-light' : 'text-gray-900'}`}>{formatTimeRange(timing.start_time, timing.end_time)}</p>
                <p className={`mt-1 text-sm ${dark ? 'text-amber-100/80' : 'text-gray-500'}`}>{timing.days}</p>
                {timing.note && <p className={`mt-3 text-sm ${dark ? 'text-amber-50' : 'text-gray-700'}`}>{timing.note}</p>}
              </section>
            );
          })}
        </div>
      ) : (
        <p className="rounded-xl border border-dashed border-amber-300 bg-white p-8 text-center text-gray-500">
          <Clock className="mx-auto mb-2 h-8 w-8 text-amber-300" aria-hidden="true" />
          {t('empty')}
        </p>
      )}

      {daily.length > 0 && (
        <section className="mt-10 rounded-2xl border border-amber-200 bg-white p-7" aria-labelledby="schedule-heading">
          <h2 id="schedule-heading" className="mb-4 font-serif text-2xl font-bold text-maroon">{t('dailyScheduleHeading')}</h2>
          <ul className="divide-y divide-amber-100">
            {daily.map((p) => (
              <li key={p.id} className="flex items-baseline justify-between gap-4 py-3">
                <span className="font-medium text-gray-800">{p.name}</span>
                <span className="text-sm text-gray-600">{formatTime(p.start_time)}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <p className="mt-8 rounded-xl border border-amber-200 bg-amber-50 p-5 text-sm text-gray-700">
        {t('note')}
      </p>
    </PageShell>
  );
}
