'use client';

import type { CSSProperties, ReactNode } from 'react';

const PETALS = Array.from({ length: 14 }, (_, i) => ({
  dx: `${((i * 37) % 90) - 45}%`,
  dy: `${82 + (i % 4) * 4}%`,
  rot: `${(i % 2 ? 1 : -1) * (160 + (i % 5) * 40)}deg`,
  delay: (i * 0.37) % 5,
  duration: 4.2 + (i % 4) * 0.6,
  size: 10 + (i % 3) * 4,
  color: i % 2 === 0 ? '#d97a1f' : '#efb538',
}));

/**
 * A blessing card: a glowing Om at the top with marigold petals falling from
 * it onto whatever sits below - the devotee's photo on the blessing pages, or
 * an empty space when they added none. The petals are decorative, ignore
 * clicks, and stop for visitors who prefer reduced motion.
 */
export default function BlessingAnimation({ children }: { children?: ReactNode }) {
  return (
    <div className="relative mx-auto w-full max-w-md overflow-hidden rounded-2xl bg-gradient-to-b from-amber-50 to-cream pb-4">
      <div className="relative flex h-28 items-center justify-center" aria-hidden="true">
        <div className="absolute h-24 w-24 animate-glowPulse rounded-full bg-saffron/40 blur-xl" />
        <span className="relative font-serif text-5xl text-maroon-dark drop-shadow-sm">ॐ</span>
      </div>
      <div className="relative px-4">{children ?? <div className="h-32" />}</div>
      <div className="pointer-events-none absolute inset-0 z-10 motion-reduce:hidden" aria-hidden="true">
        {PETALS.map((p, i) => (
          <span
            key={i}
            className="absolute inset-0 animate-petalShower opacity-0"
            style={{
              '--dx': p.dx, '--dy': p.dy, '--rot': p.rot,
              animationDelay: `${p.delay}s`, animationDuration: `${p.duration}s`,
            } as CSSProperties}
          >
            <svg
              className="absolute left-1/2 top-12"
              style={{ marginLeft: -p.size / 2 }}
              width={p.size} height={p.size} viewBox="0 0 24 24" fill={p.color}
            >
              <path d="M12 2C7 6 4 10 4 14a8 8 0 0016 0c0-4-3-8-8-12z" />
            </svg>
          </span>
        ))}
      </div>
    </div>
  );
}
