import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { Printer, QrCode } from 'lucide-react';
import DonateUpi from '@/components/public/DonateUpi';
import { PageShell } from '@/components/public/SectionHeading';
import { Link } from '@/i18n/navigation';
import { fetchHundiQr } from '@/lib/server-api';
import { pageMetadata } from '@/lib/site';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('metadata.hundi');
  return pageMetadata('/hundi', { title: t('title'), description: t('description') });
}

export default async function HundiPage() {
  const [qr, t] = await Promise.all([fetchHundiQr(), getTranslations('hundi')]);

  return (
    <PageShell title={t('title')} subtitle={t('subtitle')} narrow>
      {qr.configured ? (
        <div className="space-y-4">
          <DonateUpi qr={qr} showHeading={false} />
          <div className="space-y-3 text-sm text-gray-700">
            <p className="rounded-lg bg-amber-50 p-3 text-gray-600">{t('directNote')}</p>
            <p className="text-gray-600">
              {t('receiptNote')} <Link href="/contact" className="font-medium text-maroon hover:underline">{t('contactLink')}</Link>.
            </p>
            <p>
              <Link href="/hundi-poster" className="inline-flex items-center gap-1.5 font-medium text-maroon hover:underline">
                <Printer className="h-4 w-4" aria-hidden="true" /> {t('printPoster')}
              </Link>
            </p>
          </div>
        </div>
      ) : (
        <p className="rounded-xl border border-dashed border-amber-300 bg-white p-8 text-center text-gray-500">
          <QrCode className="mx-auto mb-2 h-8 w-8 text-amber-300" aria-hidden="true" />
          {t('notConfigured')}
        </p>
      )}
    </PageShell>
  );
}
