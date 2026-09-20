'use client';

import { useEffect, useMemo, useState } from 'react';
import { ImageIcon, X } from 'lucide-react';
import type { GalleryItem } from '@/lib/types';

const LABELS: Record<string, string> = { TEMPLE: 'Temple', FESTIVAL: 'Festivals', EVENT: 'Events' };

/** Category filter + accessible lightbox. Data is rendered on the server and passed in. */
export default function GalleryGrid({ items }: { items: GalleryItem[] }) {
  const categories = useMemo(() => Array.from(new Set(items.map((i) => i.category))), [items]);
  const [category, setCategory] = useState<string>('ALL');
  const [selected, setSelected] = useState<GalleryItem | null>(null);
  const visible = category === 'ALL' ? items : items.filter((i) => i.category === category);

  useEffect(() => {
    if (!selected) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setSelected(null);
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [selected]);

  if (!items.length) {
    return (
      <div className="rounded-2xl border border-dashed border-amber-300 bg-white p-12 text-center">
        <ImageIcon className="mx-auto mb-3 h-12 w-12 text-amber-200" aria-hidden="true" />
        <p className="text-gray-500">Photographs will be added soon.</p>
      </div>
    );
  }

  return (
    <>
      {categories.length > 1 && (
        <div className="mb-8 flex flex-wrap justify-center gap-2" role="group" aria-label="Filter photographs">
          {['ALL', ...categories].map((c) => (
            <button
              key={c}
              type="button"
              aria-pressed={category === c}
              onClick={() => setCategory(c)}
              className={`rounded-full border px-5 py-2 text-sm font-medium transition ${category === c ? 'border-maroon bg-maroon text-white' : 'border-amber-300 bg-white text-maroon-dark hover:bg-amber-50'}`}
            >
              {c === 'ALL' ? 'All' : LABELS[c] ?? c.charAt(0) + c.slice(1).toLowerCase()}
            </button>
          ))}
        </div>
      )}

      <ul className="columns-2 gap-4 space-y-4 md:columns-3 lg:columns-4">
        {visible.map((item) => (
          <li key={item.id} className="break-inside-avoid">
            <button type="button" onClick={() => setSelected(item)} className="group block w-full overflow-hidden rounded-xl bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-saffron" aria-label={`View ${item.title}`}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={item.image_url} alt={item.description || item.title} loading="lazy" className="w-full transition duration-300 group-hover:scale-105" />
            </button>
          </li>
        ))}
      </ul>

      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-4" role="dialog" aria-modal="true" aria-label={selected.title} onClick={() => setSelected(null)}>
          <button type="button" className="absolute right-4 top-4 rounded-full bg-white/10 p-2 text-white hover:bg-white/25" aria-label="Close" onClick={() => setSelected(null)}>
            <X className="h-6 w-6" />
          </button>
          <figure className="max-h-full max-w-4xl" onClick={(e) => e.stopPropagation()}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={selected.image_url} alt={selected.description || selected.title} className="max-h-[80vh] rounded-lg object-contain" />
            <figcaption className="mt-3 text-center text-sm text-white">
              <strong>{selected.title}</strong>
              {selected.description && <span className="block text-white/70">{selected.description}</span>}
            </figcaption>
          </figure>
        </div>
      )}
    </>
  );
}
