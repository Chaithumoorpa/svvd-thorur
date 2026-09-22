import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { Users } from 'lucide-react';
import { PageShell } from '@/components/public/SectionHeading';
import { fetchCommittee } from '@/lib/server-api';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('metadata.committee');
  return { title: t('title'), description: t('description') };
}

export default async function CommitteePage() {
  const members = await fetchCommittee();
  const t = await getTranslations('committee');

  return (
    <PageShell title={t('title')} subtitle={t('subtitle')}>
      {members.length ? (
        <ul className="grid grid-cols-2 gap-6 md:grid-cols-3 lg:grid-cols-4">
          {members.map((m) => (
            <li key={m.id} className="rounded-2xl border border-amber-200 bg-white p-5 text-center shadow-sm">
              {m.photo_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={m.photo_url} alt="" loading="lazy" className="mx-auto mb-3 h-24 w-24 rounded-full border-2 border-saffron object-cover" />
              ) : (
                <span className="mx-auto mb-3 flex h-24 w-24 items-center justify-center rounded-full bg-amber-100 font-serif text-3xl font-bold text-maroon" aria-hidden="true">
                  {m.name.trim().charAt(0).toUpperCase()}
                </span>
              )}
              <h2 className="font-serif text-lg font-bold text-maroon-dark">{m.name}</h2>
              {m.position && <p className="text-sm text-gray-500">{m.position}</p>}
            </li>
          ))}
        </ul>
      ) : (
        <div className="rounded-2xl border border-dashed border-amber-300 bg-white p-12 text-center">
          <Users className="mx-auto mb-3 h-10 w-10 text-amber-200" aria-hidden="true" />
          <p className="text-gray-500">{t('empty')}</p>
        </div>
      )}
    </PageShell>
  );
}
