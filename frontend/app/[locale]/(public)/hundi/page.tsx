import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { QrCode, Smartphone } from 'lucide-react';
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
        <div className="rounded-2xl border border-amber-200 bg-white p-7 text-center shadow-sm">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={`data:image/png;base64,${qr.qr_base64}`}
            alt={t('title')}
            className="mx-auto h-56 w-56 rounded-xl border border-amber-100"
          />
          <p className="mt-4 font-mono text-lg font-semibold text-maroon">{qr.upi_vpa}</p>

          <div className="mx-auto mt-6 max-w-md space-y-3 text-left text-sm text-gray-700">
            <p className="flex gap-2">
              <Smartphone className="mt-0.5 h-4 w-4 flex-none text-saffron" aria-hidden="true" />
              {t('howTo')}
            </p>
            <p className="rounded-lg bg-amber-50 p-3 text-gray-600">{t('directNote')}</p>
            <p className="text-gray-600">
              {t('receiptNote')} <Link href="/contact" className="font-medium text-maroon hover:underline">{t('contactLink')}</Link>.
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
