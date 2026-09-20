import type { Metadata } from 'next';
import GalleryGrid from '@/components/public/GalleryGrid';
import { PageShell } from '@/components/public/SectionHeading';
import { fetchGallery } from '@/lib/server-api';

export const metadata: Metadata = {
  title: 'Gallery',
  description: 'Photographs of the temple, festivals and events.',
};

export default async function GalleryPage() {
  const items = await fetchGallery();
  return (
    <PageShell title="Temple Gallery" subtitle="Glimpses of the sacred spaces, festivals and rituals">
      <GalleryGrid items={items} />
    </PageShell>
  );
}
