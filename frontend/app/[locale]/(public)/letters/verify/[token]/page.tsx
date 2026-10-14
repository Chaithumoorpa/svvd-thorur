import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { BadgeCheck, CircleSlash, PenLine, ShieldAlert } from 'lucide-react';
import { PageShell } from '@/components/public/SectionHeading';
import { Link } from '@/i18n/navigation';
import { fetchLetterVerification } from '@/lib/server-api';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('letterVerify');
  // Each link is private to the letter it's printed on - keep them out of search engines.
  return { title: t('metaTitle'), robots: { index: false, follow: false } };
}

/** Server times are UTC without a zone; letters are dated in IST. */
function istDate(value: string, locale: string): string {
  const d = new Date(value.endsWith('Z') || value.includes('+') ? value : `${value}${value.length <= 10 ? 'T00:00:00+05:30' : 'Z'}`);
  return d.toLocaleDateString(`${locale}-IN`, { timeZone: 'Asia/Kolkata', day: 'numeric', month: 'long', year: 'numeric' });
}

export default async function VerifyLetterPage({ params }: { params: Promise<{ locale: string; token: string }> }) {
  const { locale, token } = await params;
  const [result, t] = await Promise.all([fetchLetterVerification(token), getTranslations('letterVerify')]);

  if (result === 'not-found' || result === 'unavailable') {
    const missing = result === 'not-found';
    return (
      <PageShell title={t('title')} narrow>
        <div className={`rounded-xl border p-6 ${missing ? 'border-red-200 bg-red-50' : 'border-amber-200 bg-amber-50'}`} role="status">
          <p className={`flex items-center gap-2 text-lg font-semibold ${missing ? 'text-red-800' : 'text-amber-900'}`}>
            <ShieldAlert className="h-6 w-6" aria-hidden="true" />
            {missing ? t('notFound') : t('unavailableTitle')}
          </p>
          <p className="mt-2 text-sm text-gray-700">{missing ? t('notFoundText') : t('unavailableText')}</p>
          <p className="mt-4 text-sm">
            <Link href="/contact" className="font-medium text-maroon hover:underline">{t('contact')}</Link>
          </p>
        </div>
      </PageShell>
    );
  }

  const v = result;
  const revoked = v.status === 'REVOKED';
  const rows: Array<[string, string]> = [
    [t('reference'), v.reference_number],
    [t('type'), v.kind_label],
    [t('subject'), v.subject],
    ...(v.recipient_name ? [[t('issuedTo'), v.recipient_name] as [string, string]] : []),
    [t('letterDate'), istDate(v.letter_date, locale)],
    [t('issuedOn'), istDate(v.issued_at, locale)],
    ...(revoked && v.revoked_at ? [[t('revokedOn'), istDate(v.revoked_at, locale)] as [string, string]] : []),
  ];
  const groups = [
    { label: t('signedBy'), people: v.signatories.filter((s) => s.role === 'SIGNATORY') },
    { label: t('attestedBy'), people: v.signatories.filter((s) => s.role === 'ATTESTOR') },
  ].filter((g) => g.people.length);

  return (
    <PageShell title={t('title')} narrow>
      <div
        role="status"
        className={`rounded-xl border p-6 ${revoked ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'}`}
      >
        <p className={`flex items-center gap-2 text-lg font-semibold ${revoked ? 'text-red-800' : 'text-green-800'}`}>
          {revoked ? <CircleSlash className="h-6 w-6" aria-hidden="true" /> : <BadgeCheck className="h-6 w-6" aria-hidden="true" />}
          {revoked ? t('revoked') : t('genuine')}
        </p>
        <p className="mt-2 text-sm text-gray-700">
          {revoked ? t('revokedText', { temple: v.temple_name }) : t('genuineText', { temple: v.temple_name })}
        </p>
        {revoked && v.revoke_reason && (
          <p className="mt-2 text-sm text-red-800"><span className="font-medium">{t('reason')}:</span> {v.revoke_reason}</p>
        )}
      </div>

      <div className="mt-6 rounded-xl border border-amber-200 bg-white p-6 shadow-sm">
        <dl className="grid gap-x-6 gap-y-3 text-sm sm:grid-cols-[10rem_1fr]">
          {rows.map(([label, value]) => (
            <div key={label} className="contents">
              <dt className="font-medium text-gray-500">{label}</dt>
              <dd className="break-words text-gray-900">{value}</dd>
            </div>
          ))}
        </dl>

        {groups.map((g) => (
          <div key={g.label} className="mt-6">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-maroon">{g.label}</h2>
            <ul className="mt-2 divide-y divide-amber-100">
              {g.people.map((s) => (
                <li key={s.name} className="flex flex-wrap items-start justify-between gap-2 py-2.5 text-sm">
                  <span>
                    <span className="font-semibold text-gray-900">{s.name}</span>
                    {s.designation && <span className="text-gray-600"> · {s.designation}</span>}
                  </span>
                  <span className="inline-flex items-center gap-1 text-xs text-gray-500">
                    <PenLine className="h-3.5 w-3.5" aria-hidden="true" />
                    {s.method === 'digital' && s.signed_at ? t('digital', { date: istDate(s.signed_at, locale) }) : t('ink')}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <p className="mt-6 text-sm text-gray-600">
        {t('compare')} <Link href="/contact" className="font-medium text-maroon hover:underline">{t('contact')}</Link>
      </p>
    </PageShell>
  );
}
