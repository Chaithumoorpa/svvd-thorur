import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { useTranslations } from 'next-intl';
import { Clock, Sparkles } from 'lucide-react';
import BookSeva from '@/components/public/BookSeva';
import { PageShell } from '@/components/public/SectionHeading';
import { Link } from '@/i18n/navigation';
import { formatMoney, formatTimeRange } from '@/lib/format';
import { fetchPoojas } from '@/lib/server-api';
import { localizedAlternates } from '@/lib/site';
import type { Pooja } from '@/lib/types';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('metadata.poojas');
  return { title: t('title'), description: t('description'), alternates: await localizedAlternates('/poojas') };
}

const GROUPS: Array<{ id: string; titleKey: string; types: string[] }> = [
  { id: 'daily', titleKey: 'groupDaily', types: ['daily'] },
  { id: 'special', titleKey: 'groupSpecial', types: ['special', 'weekly', 'monthly'] },
  { id: 'festival', titleKey: 'groupFestival', types: ['festival'] },
];

function PoojaCard({ p }: { p: Pooja }) {
  const t = useTranslations('poojas');
  const time = formatTimeRange(p.start_time, p.end_time);
  return (
    <li className="flex flex-col rounded-2xl border border-amber-200 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-serif text-xl font-bold text-maroon">{p.name}</h3>
        <span className={`flex-none rounded-full px-3 py-1 text-xs font-semibold ${p.is_paid ? 'bg-amber-100 text-amber-800' : 'bg-green-100 text-green-800'}`}>
          {p.is_paid ? formatMoney(p.suggested_amount) : t('free')}
        </span>
      </div>
      {time && <p className="mt-1 flex items-center gap-1.5 text-sm text-gray-500"><Clock className="h-3.5 w-3.5" aria-hidden="true" />{time}</p>}
      {p.description && <p className="mt-3 text-sm leading-relaxed text-gray-700">{p.description}</p>}
      <div className="mt-auto pt-4">
        {p.is_paid ? (
          <p className="text-xs text-gray-500">{t('bookAtCounter')}</p>
        ) : (
          <BookSeva sevaId={p.id} sevaName={p.name} />
        )}
      </div>
    </li>
  );
}

export default async function PoojasPage({ searchParams }: { searchParams: { type?: string } }) {
  const poojas = await fetchPoojas();
  const t = await getTranslations('poojas');
  const only = GROUPS.find((g) => g.id === searchParams.type);
  const groups = (only ? [only] : GROUPS)
    .map((g) => ({ ...g, items: poojas.filter((p) => g.types.includes(p.pooja_type)) }))
    .filter((g) => g.items.length);
  const known = new Set(GROUPS.flatMap((g) => g.types));
  const other = only ? [] : poojas.filter((p) => !known.has(p.pooja_type));

  return (
    <PageShell title={t('title')} subtitle={t('subtitle')}>
      <nav aria-label={t('filterLabel')} className="mb-8 flex flex-wrap justify-center gap-2">
        {[{ id: '', titleKey: 'all' as const }, ...GROUPS].map((g) => (
          <Link
            key={g.id || 'all'}
            href={g.id ? `/poojas?type=${g.id}` : '/poojas'}
            aria-current={(searchParams.type ?? '') === g.id ? 'page' : undefined}
            className={`rounded-full border px-5 py-2 text-sm font-medium ${(searchParams.type ?? '') === g.id ? 'border-maroon bg-maroon text-white' : 'border-amber-300 bg-white text-maroon-dark hover:bg-amber-50'}`}
          >
            {t(g.titleKey)}
          </Link>
        ))}
      </nav>

      {groups.length === 0 && other.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-amber-300 bg-white p-12 text-center">
          <Sparkles className="mx-auto mb-3 h-10 w-10 text-amber-200" aria-hidden="true" />
          <p className="text-gray-500">{t('empty')}</p>
        </div>
      ) : (
        <div className="space-y-12">
          {groups.map((g) => (
            <section key={g.id} aria-labelledby={`g-${g.id}`}>
              <h2 id={`g-${g.id}`} className="mb-4 font-serif text-2xl font-bold text-maroon-dark">{t(g.titleKey)}</h2>
              <ul className="grid gap-5 md:grid-cols-2">{g.items.map((p) => <PoojaCard key={p.id} p={p} />)}</ul>
            </section>
          ))}
          {other.length > 0 && (
            <section>
              <h2 className="mb-4 font-serif text-2xl font-bold text-maroon-dark">{t('other')}</h2>
              <ul className="grid gap-5 md:grid-cols-2">{other.map((p) => <PoojaCard key={p.id} p={p} />)}</ul>
            </section>
          )}
        </div>
      )}
    </PageShell>
  );
}
