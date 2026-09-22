import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import GalleryGrid from '@/components/public/GalleryGrid';
import { PageShell } from '@/components/public/SectionHeading';
import { fetchGallery } from '@/lib/server-api';
import { localizedAlternates } from '@/lib/site';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('metadata.gallery');
  return { title: t('title'), description: t('description'), alternates: await localizedAlternates('/gallery') };
}

export default async function GalleryPage() {
  const items = await fetchGallery();
  const t = await getTranslations('gallery');
  return (
    <PageShell title={t('title')} subtitle={t('subtitle')}>
      <GalleryGrid items={items} />
    </PageShell>
  );
}
