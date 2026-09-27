'use client';

const PETALS = Array.from({ length: 12 }, (_, i) => ({
  left: (i * 8.3 + (i % 3) * 3) % 96,
  delay: (i % 6) * 0.9,
  duration: 5 + (i % 4),
  size: 10 + (i % 3) * 4,
  color: i % 2 === 0 ? '#d97a1f' : '#efb538',
}));

/** Purely decorative: a soft glow behind an Om symbol with marigold petals
 * drifting down - shown below a devotee's photo on the blessing pages. */
export default function BlessingAnimation() {
  return (
    <div
      className="relative mx-auto h-48 w-full max-w-md overflow-hidden rounded-2xl bg-gradient-to-b from-amber-50 to-cream"
      aria-hidden="true"
    >
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="h-28 w-28 animate-glowPulse rounded-full bg-saffron/40 blur-xl" />
      </div>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="font-serif text-5xl text-maroon-dark drop-shadow-sm">ॐ</span>
      </div>
      {PETALS.map((p, i) => (
        <span
          key={i}
          className="absolute top-0 animate-petalFall"
          style={{ left: `${p.left}%`, animationDelay: `${p.delay}s`, animationDuration: `${p.duration}s` }}
        >
          <svg width={p.size} height={p.size} viewBox="0 0 24 24" fill={p.color}>
            <path d="M12 2C7 6 4 10 4 14a8 8 0 0016 0c0-4-3-8-8-12z" />
          </svg>
        </span>
      ))}
    </div>
  );
}
