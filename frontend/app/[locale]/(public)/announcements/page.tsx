import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { Bell, Megaphone } from 'lucide-react';
import { PageShell } from '@/components/public/SectionHeading';
import { formatDate } from '@/lib/format';
import { fetchAnnouncements } from '@/lib/server-api';
import { localizedAlternates } from '@/lib/site';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('metadata.announcements');
  return { title: t('title'), description: t('description'), alternates: await localizedAlternates('/announcements') };
}

export default async function AnnouncementsPage() {
  const items = await fetchAnnouncements();
  const t = await getTranslations('announcements');

  return (
    <PageShell title={t('title')} subtitle={t('subtitle')} narrow>
      {items.length ? (
        <ul className="space-y-5">
          {items.map((a) => (
            <li key={a.id}>
              <article className="rounded-2xl border border-amber-100 bg-white p-6 shadow-sm sm:p-8">
                <header className="mb-3 flex flex-wrap items-center justify-between gap-2 text-xs text-gray-500">
                  <span className="inline-flex items-center gap-1.5 font-semibold uppercase tracking-wider text-saffron">
                    <Bell className="h-3.5 w-3.5" aria-hidden="true" /> {t('notice')}
                  </span>
                  <time dateTime={(a.start_date ?? a.created_at).slice(0, 10)}>{formatDate(a.start_date ?? a.created_at, { day: 'numeric', month: 'long', year: 'numeric' })}</time>
                </header>
                <h2 className="font-serif text-2xl font-bold text-maroon">{a.title}</h2>
                {a.message && <p className="mt-3 whitespace-pre-line leading-relaxed text-gray-700">{a.message}</p>}
                {a.end_date && <p className="mt-4 text-xs text-gray-400">{t('validUntil', { date: formatDate(a.end_date) })}</p>}
              </article>
            </li>
          ))}
        </ul>
      ) : (
        <div className="rounded-2xl border border-dashed border-amber-300 bg-white p-12 text-center">
          <Megaphone className="mx-auto mb-3 h-12 w-12 text-amber-200" aria-hidden="true" />
          <h2 className="font-serif text-xl font-bold text-gray-600">{t('emptyTitle')}</h2>
          <p className="text-gray-500">{t('emptyText')}</p>
        </div>
      )}
    </PageShell>
  );
}
