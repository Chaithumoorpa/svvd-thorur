'use client';

import React, { useEffect, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import BlessingAnimation from '@/components/public/BlessingAnimation';
import type { BlessingEntry } from '@/lib/types';

const AUTO_ADVANCE_MS = 6000;

/** One devotee's blessing at a time - the Om at the top showering petals onto
 * their photo below (or an empty space, if they added none). Auto-advances
 * unless hovered, focused, or the visitor prefers reduced motion; arrows,
 * dots, keys and swipes all work. */
export default function BlessingsCarousel({ entries }: { entries: BlessingEntry[] }) {
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const touchX = useRef<number | null>(null);
  const count = entries.length;
  const go = (i: number) => setIndex(((i % count) + count) % count);

  useEffect(() => {
    const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    if (paused || reduceMotion || count < 2) return;
    const timer = setInterval(() => setIndex((i) => (i + 1) % count), AUTO_ADVANCE_MS);
    return () => clearInterval(timer);
  }, [paused, count]);

  const entry = entries[index];
  return (
    <section
      aria-roledescription="carousel"
      aria-label="Blessings"
      className="space-y-3"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
      onKeyDown={(e) => {
        if (e.key === 'ArrowLeft') go(index - 1);
        if (e.key === 'ArrowRight') go(index + 1);
      }}
      onTouchStart={(e) => { touchX.current = e.touches[0].clientX; }}
      onTouchEnd={(e) => {
        if (touchX.current === null) return;
        const dx = e.changedTouches[0].clientX - touchX.current;
        if (Math.abs(dx) > 40) go(index + (dx < 0 ? 1 : -1));
        touchX.current = null;
      }}
    >
      <BlessingAnimation>
        <div
          role="group"
          aria-roledescription="slide"
          aria-label={`${index + 1} of ${count}`}
          aria-live={paused ? 'polite' : 'off'}
          className="relative"
        >
          {entry.photo_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              key={`${index}-${entry.photo_url}`}
              src={entry.photo_url}
              alt={`${entry.devotee_name}'s ${entry.occasion} photo`}
              className="mx-auto max-h-80 animate-slideIn rounded-2xl border border-amber-200 object-contain"
            />
          ) : (
            <div key={`${index}-none`} className="h-32" aria-hidden="true" />
          )}
          {count > 1 && (
            <>
              <button type="button" onClick={() => go(index - 1)} aria-label="Previous blessing"
                      className="absolute left-0 top-1/2 z-20 -translate-y-1/2 rounded-full bg-white/90 p-2 text-maroon shadow hover:bg-white">
                <ChevronLeft className="h-5 w-5" aria-hidden="true" />
              </button>
              <button type="button" onClick={() => go(index + 1)} aria-label="Next blessing"
                      className="absolute right-0 top-1/2 z-20 -translate-y-1/2 rounded-full bg-white/90 p-2 text-maroon shadow hover:bg-white">
                <ChevronRight className="h-5 w-5" aria-hidden="true" />
              </button>
            </>
          )}
        </div>
      </BlessingAnimation>

      <div className="text-center">
        <p className="font-serif text-xl text-maroon-dark">{entry.devotee_name}</p>
        <p className="text-sm text-gray-600">{entry.occasion}</p>
      </div>

      {count > 1 && (
        <div className="flex justify-center gap-2">
          {entries.map((e, i) => (
            <button
              key={i}
              type="button"
              onClick={() => go(i)}
              aria-label={`Show ${e.devotee_name}'s blessing`}
              aria-current={i === index}
              className={`h-2.5 w-2.5 rounded-full transition ${i === index ? 'bg-maroon' : 'bg-amber-200 hover:bg-saffron'}`}
            />
          ))}
        </div>
      )}
    </section>
  );
}
