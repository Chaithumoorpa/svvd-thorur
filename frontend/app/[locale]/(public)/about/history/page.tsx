import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { BookOpen } from 'lucide-react';
import { PageShell } from '@/components/public/SectionHeading';
import { fetchTemple } from '@/lib/server-api';
import { localizedAlternates, templeLocation, templeName } from '@/lib/site';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('metadata.history');
  return { title: t('title'), description: t('description'), alternates: await localizedAlternates('/about/history') };
}

export default async function HistoryPage() {
  const temple = await fetchTemple();
  const paragraphs = (temple?.history ?? '').split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);
  const t = await getTranslations('about.history');

  return (
    <PageShell title={t('title')} subtitle={temple ? `${templeName(temple)}${templeLocation(temple) ? ` · ${templeLocation(temple)}` : ''}` : undefined} narrow>
      {temple?.deity_name && (
        <p className="mb-6 rounded-xl border border-amber-200 bg-white p-4 text-center font-serif text-lg text-maroon">
          {t('presidingDeity')} <strong>{temple.deity_name}</strong>
        </p>
      )}
      {paragraphs.length ? (
        <article className="space-y-5 text-lg leading-relaxed text-gray-800">
          {paragraphs.map((p, i) => <p key={i} className="whitespace-pre-line">{p}</p>)}
        </article>
      ) : (
        <div className="rounded-2xl border border-dashed border-amber-300 bg-white p-12 text-center">
          <BookOpen className="mx-auto mb-3 h-10 w-10 text-amber-200" aria-hidden="true" />
          <p className="text-gray-500">{t('empty')}</p>
        </div>
      )}
    </PageShell>
  );
}
