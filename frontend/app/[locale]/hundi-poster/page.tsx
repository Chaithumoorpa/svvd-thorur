import type { Metadata } from 'next';
import { connection } from 'next/server';
import { getLocale, getTranslations } from 'next-intl/server';
import { BadgeCheck, Mail, Phone, ShieldCheck } from 'lucide-react';
import PrintButton from '@/components/public/PrintButton';
import { fetchHundiQr, fetchTemple } from '@/lib/server-api';
import { SITE_URL } from '@/lib/site';

/**
 * Printable A4 e-Hundi poster, one per language (/hundi-poster, /te/hundi-poster, ...).
 * Lives outside the (public) group so it has no site header/footer. Everything on
 * it is already public; the point is that a devotee standing in front of it can
 * verify it: logo, registered name, the account name their UPI app will show,
 * registration/PAN/80G numbers and the temple office's contact details.
 */
export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('hundiPoster');
  return { title: t('metaTitle'), robots: { index: false, follow: false } };
}

export default async function HundiPosterPage() {
  await connection(); // render per request: the "printed on" date must be today's
  const [qr, temple, t, td, th, locale] = await Promise.all([
    fetchHundiQr(), fetchTemple(), getTranslations('hundiPoster'), getTranslations('donate'), getTranslations('hundi'), getLocale(),
  ]);

  if (!qr.configured || !temple) {
    return <p className="mx-auto max-w-md p-10 text-center text-gray-600">{th('notConfigured')}</p>;
  }

  const place = [temple.address, temple.village, temple.district, [temple.state, temple.pincode].filter(Boolean).join(' ')]
    .filter(Boolean).join(', ');
  const website = SITE_URL.replace(/^https?:\/\//, '');
  const printedOn = new Intl.DateTimeFormat(locale === 'en' ? 'en-IN' : locale, { dateStyle: 'long', timeZone: 'Asia/Kolkata' })
    .format(new Date());
  const official: Array<[string, string]> = [
    [td('regNo'), temple.registration_number],
    [td('pan'), temple.pan_number],
    [td('eightyG'), temple.eighty_g_number],
  ].filter((row): row is [string, string] => Boolean(row[1]));

  return (
    <div className="min-h-screen bg-gray-100 py-6 print:min-h-0 print:bg-white print:py-0">
      <style>{'@page { size: A4; margin: 0 } @media print { html, body { background: #fff } }'}</style>

      <div className="mx-auto mb-4 flex max-w-[210mm] flex-wrap items-center justify-between gap-3 px-4 print:hidden">
        <p className="text-sm text-gray-600">{t('printHint')}</p>
        <PrintButton label={t('print')} />
      </div>

      <article className="mx-auto box-border flex h-[297mm] w-[210mm] max-w-full flex-col overflow-hidden bg-white p-[8mm] shadow-lg print:shadow-none">
        <div className="flex flex-1 flex-col rounded-[6mm] border-[2.5px] border-maroon p-[1.5mm]">
          <div className="flex flex-1 flex-col items-center rounded-[5mm] border border-saffron-light px-[10mm] pb-[4mm] pt-[5mm] text-center">
            <header className="flex flex-col items-center">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/logo.png" alt="" className="h-[22mm] w-[22mm]" />
              <h1 className="mt-[2mm] font-serif text-[21pt] font-bold leading-tight text-maroon">{temple.name}</h1>
              {temple.tagline && <p className="mt-[1mm] text-[11pt] text-gray-700">{temple.tagline}</p>}
              {place && <p className="mt-[1mm] text-[9.5pt] text-gray-600">{place}</p>}
            </header>

            <div className="mt-[4mm] rounded-full bg-maroon px-[7mm] py-[1.8mm] text-[13pt] font-semibold text-white">
              {t('title')} · {t('scanTitle')}
            </div>

            <div className="mt-[4mm] rounded-[5mm] border-[3px] border-saffron p-[2mm]">
              {/* Print-resolution PNG (~1040px) of the same QR as the website shows. */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/api/v1/temple/hundi-qr/print.png" alt={td('qrAlt')} className="block h-[80mm] w-[80mm]" />
            </div>

            <dl className="mt-[3mm] space-y-[0.5mm]">
              <div>
                <dt className="text-[9pt] uppercase tracking-wide text-gray-500">{td('upiId')}</dt>
                <dd className="font-mono text-[15pt] font-bold text-maroon">{qr.upi_vpa}</dd>
              </div>
              <div>
                <dt className="text-[9pt] uppercase tracking-wide text-gray-500">{td('accountName')}</dt>
                <dd className="text-[13pt] font-semibold text-gray-900">{qr.payee_name}</dd>
              </div>
            </dl>
            <p className="mt-[1.5mm] text-[9pt] text-gray-500">{td('apps')}</p>

            <div className="mt-[3mm] w-full rounded-[3mm] border border-green-300 bg-green-50 px-[5mm] py-[2.5mm] text-left text-[10pt] text-green-900">
              <p className="flex items-center gap-[1.5mm] font-semibold">
                <ShieldCheck className="h-[4.5mm] w-[4.5mm] shrink-0" aria-hidden="true" /> {td('verifyTitle')}
              </p>
              <p className="mt-[1mm]">{td.rich('verifyName', { name: qr.payee_name ?? temple.name, b: (c) => <strong>{c}</strong> })}</p>
              <p className="mt-[0.5mm]">{td('neverAsk')}</p>
            </div>

            {official.length > 0 && (
              <div className="mt-[3mm] w-full rounded-[3mm] border border-amber-300 bg-amber-50 px-[5mm] py-[2.5mm] text-left text-[10pt]">
                <p className="flex items-center gap-[1.5mm] font-semibold text-maroon">
                  <BadgeCheck className="h-[4.5mm] w-[4.5mm] shrink-0" aria-hidden="true" /> {td('officialDetails')}
                </p>
                <dl className="mt-[1mm] grid grid-cols-[auto_1fr] gap-x-[4mm] gap-y-[0.5mm]">
                  {official.map(([label, value]) => (
                    <div key={label} className="contents">
                      <dt className="text-gray-600">{label}</dt>
                      <dd className="break-all font-mono font-semibold text-gray-900">{value}</dd>
                    </div>
                  ))}
                </dl>
                {temple.eighty_g_number && <p className="mt-[1mm] text-[8.5pt] text-gray-700">{td('eightyGNote')}</p>}
              </div>
            )}

            <footer className="mt-auto w-full border-t border-amber-200 pt-[2.5mm] text-[9.5pt] text-gray-700">
              <p className="flex flex-wrap items-center justify-center gap-x-[5mm] gap-y-[1mm]">
                <span className="font-semibold text-maroon">{t('office')}</span>
                {temple.contact_phone && (
                  <span className="inline-flex items-center gap-[1mm]"><Phone className="h-[3.5mm] w-[3.5mm]" aria-hidden="true" />{temple.contact_phone}</span>
                )}
                {temple.contact_email && (
                  <span className="inline-flex items-center gap-[1mm]"><Mail className="h-[3.5mm] w-[3.5mm]" aria-hidden="true" />{temple.contact_email}</span>
                )}
                <span>{t('website')}: <strong>{website}</strong></span>
              </p>
              <p className="mt-[1mm] text-[8pt] text-gray-500">{t('printedOn', { date: printedOn })}</p>
            </footer>
          </div>
        </div>
      </article>
    </div>
  );
}
