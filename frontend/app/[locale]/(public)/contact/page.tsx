import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { Mail, MapPin, MessageCircle, Phone } from 'lucide-react';
import ContactForm from '@/components/public/ContactForm';
import { PageShell } from '@/components/public/SectionHeading';
import { fetchTemple } from '@/lib/server-api';
import { isEmbeddableMap, localizedAlternates, templeAddress } from '@/lib/site';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('metadata.contact');
  return { title: t('title'), description: t('description'), alternates: await localizedAlternates('/contact') };
}

export default async function ContactPage() {
  const temple = await fetchTemple();
  const address = templeAddress(temple);
  const [t, tCommon] = await Promise.all([getTranslations('contact'), getTranslations('common')]);
  const items = [
    address && { icon: MapPin, label: t('address'), node: <span>{address}</span> },
    temple?.contact_phone && { icon: Phone, label: t('phone'), node: <a className="hover:underline" href={`tel:${temple.contact_phone.replace(/\s/g, '')}`}>{temple.contact_phone}</a> },
    temple?.whatsapp_number && { icon: MessageCircle, label: t('whatsapp'), node: <a className="hover:underline" href={`https://wa.me/${temple.whatsapp_number.replace(/\D/g, '')}`} target="_blank" rel="noopener noreferrer">{temple.whatsapp_number}</a> },
    temple?.contact_email && { icon: Mail, label: t('email'), node: <a className="break-all hover:underline" href={`mailto:${temple.contact_email}`}>{temple.contact_email}</a> },
  ].filter(Boolean) as Array<{ icon: typeof Mail; label: string; node: React.ReactNode }>;

  return (
    <PageShell title={t('title')} subtitle={t('subtitle')}>
      <div className="grid gap-10 lg:grid-cols-5">
        <div className="space-y-6 lg:col-span-2">
          {items.length ? (
            <ul className="space-y-4">
              {items.map(({ icon: Icon, label, node }) => (
                <li key={label} className="flex gap-4 rounded-xl border border-amber-200 bg-white p-4">
                  <Icon className="mt-0.5 h-5 w-5 flex-none text-saffron" aria-hidden="true" />
                  <div><h2 className="text-sm font-semibold text-maroon">{label}</h2><p className="text-sm text-gray-700">{node}</p></div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="rounded-xl border border-dashed border-amber-300 bg-white p-6 text-sm text-gray-500">{t('empty')}</p>
          )}
          {temple?.map_url && (
            isEmbeddableMap(temple.map_url) ? (
              <iframe title={t('mapTitle')} src={temple.map_url} className="h-56 w-full rounded-xl border-0" loading="lazy" referrerPolicy="no-referrer-when-downgrade" sandbox="allow-scripts allow-same-origin allow-popups" />
            ) : (
              <a href={temple.map_url} target="_blank" rel="noopener noreferrer" className="inline-block font-semibold text-saffron hover:underline">{tCommon('getDirections')}</a>
            )
          )}
        </div>
        <div className="lg:col-span-3">
          <h2 className="mb-4 font-serif text-2xl font-bold text-maroon">{t('sendMessage')}</h2>
          <ContactForm />
        </div>
      </div>
    </PageShell>
  );
}
