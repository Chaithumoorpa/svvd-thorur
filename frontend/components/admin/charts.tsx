'use client';

/**
 * Small, dependency-free charts for the admin Analytics page.
 *
 * Conventions (shared by every chart here): thin marks with a 4px rounded data
 * end, a hairline grid, values in text colours (never the series colour), a
 * legend whenever there are two series, a hover/focus readout on every mark,
 * and a "Show as table" view so no number is only reachable by hovering.
 * Two categorical colours, checked for colour-blind separation: blue (slot 1)
 * and orange (slot 2).
 */
import React, { useId, useState } from 'react';

export const SERIES = ['#2a78d6', '#eb6834'] as const;

const compact = (n: number) =>
  Math.abs(n) >= 1e7 ? `${(n / 1e7).toFixed(1).replace(/\.0$/, '')}Cr`
    : Math.abs(n) >= 1e5 ? `${(n / 1e5).toFixed(1).replace(/\.0$/, '')}L`
      : Math.abs(n) >= 1e3 ? `${(n / 1e3).toFixed(1).replace(/\.0$/, '')}K`
        : String(Math.round(n));

/** Round tick step (1, 2, 2.5 or 5 x 10^n) giving about four intervals, and the
 * axis maximum that is a whole number of those steps above the data. */
function niceScale(max: number): { top: number; ticks: number[] } {
  if (max <= 0) return { top: 1, ticks: [0, 1] };
  const raw = max / 4;
  const pow = 10 ** Math.floor(Math.log10(raw));
  const step = ([1, 2, 2.5, 5, 10].find((s) => s * pow >= raw) ?? 10) * pow;
  const top = Math.ceil(max / step) * step;
  return { top, ticks: Array.from({ length: Math.round(top / step) + 1 }, (_, i) => i * step) };
}

function TableView({ caption, head, rows }: { caption: string; head: string[]; rows: Array<Array<string | number>> }) {
  return (
    <details className="mt-2 text-sm">
      <summary className="cursor-pointer text-xs text-gray-500 hover:text-gray-800">Show as table</summary>
      <table className="mt-2 w-full text-left text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead className="text-xs uppercase text-gray-500">
          <tr>{head.map((h, i) => <th key={h} scope="col" className={`py-1 ${i ? 'text-right' : ''}`}>{h}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-gray-100 tabular-nums">
          {rows.map((r, i) => (
            <tr key={i}>{r.map((c, j) => <td key={j} className={`py-1 ${j ? 'text-right' : ''}`}>{c}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </details>
  );
}

// ------------------------------------------------------------------- column chart
export interface ColumnSeries {
  name: string;
  values: number[];
}

/**
 * Vertical columns over a category axis (months, days, hours). One or two
 * series; two are drawn side by side with a 2px gap, never stacked or on a
 * second axis. Hover or focus a column group for its values.
 */
export function ColumnChart({
  title, labels, series, format = compact, height = 180, tickEvery = 1, fullLabels,
}: {
  title: string; labels: string[]; series: ColumnSeries[]; format?: (n: number) => string;
  height?: number; tickEvery?: number; fullLabels?: string[];
}) {
  const [active, setActive] = useState<number | null>(null);
  const id = useId();
  const { top: max, ticks } = niceScale(Math.max(0, ...series.flatMap((s) => s.values)));
  const n = labels.length;
  const slot = 100 / Math.max(n, 1);
  const two = series.length > 1;

  return (
    <figure aria-labelledby={`${id}-t`}>
      <figcaption id={`${id}-t`} className="sr-only">{title}</figcaption>
      {two && (
        <ul className="mb-2 flex flex-wrap gap-4 text-xs text-gray-600" aria-label="Legend">
          {series.map((s, i) => (
            <li key={s.name} className="flex items-center gap-1.5">
              <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: SERIES[i] }} aria-hidden="true" />{s.name}
            </li>
          ))}
        </ul>
      )}
      <div className="relative flex gap-2">
        {/* y axis */}
        <div className="relative w-10 shrink-0 text-right text-[11px] tabular-nums text-gray-400" style={{ height }}>
          {ticks.map((t) => (
            <span key={t} className="absolute right-0 -translate-y-1/2" style={{ top: `${(1 - t / max) * 100}%` }}>{format(t)}</span>
          ))}
        </div>
        <div className="relative flex-1">
          <div className="relative" style={{ height }}>
            {ticks.map((t) => (
              <div key={t} className="absolute inset-x-0 border-t border-gray-100" style={{ top: `${(1 - t / max) * 100}%` }} />
            ))}
            <div className="absolute inset-0 flex items-end">
              {labels.map((label, i) => (
                <button
                  key={label + i}
                  type="button"
                  className="group relative flex h-full items-end justify-center gap-[2px] focus:outline-none"
                  style={{ width: `${slot}%` }}
                  onPointerEnter={() => setActive(i)}
                  onPointerLeave={() => setActive((a) => (a === i ? null : a))}
                  onFocus={() => setActive(i)}
                  onBlur={() => setActive((a) => (a === i ? null : a))}
                  aria-label={`${fullLabels?.[i] ?? label}: ${series.map((s) => `${s.name} ${format(s.values[i] ?? 0)}`).join(', ')}`}
                >
                  {active === i && <span className="absolute inset-0 rounded bg-gray-100/70" aria-hidden="true" />}
                  {series.map((s, si) => {
                    const v = s.values[i] ?? 0;
                    return (
                      <span
                        key={s.name}
                        className="relative rounded-t"
                        style={{
                          height: v > 0 ? `max(2px, ${(v / max) * 100}%)` : 0,
                          width: two ? 'min(12px, 40%)' : 'min(24px, 70%)',
                          background: SERIES[si],
                          opacity: active === null || active === i ? 1 : 0.55,
                        }}
                      />
                    );
                  })}
                </button>
              ))}
            </div>
            {active !== null && (
              <div
                role="status"
                className="pointer-events-none absolute -top-2 z-10 -translate-x-1/2 -translate-y-full whitespace-nowrap rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-xs shadow"
                style={{ left: `${Math.min(Math.max((active + 0.5) * slot, 12), 88)}%` }}
              >
                <p className="text-gray-500">{fullLabels?.[active] ?? labels[active]}</p>
                {series.map((s, si) => (
                  <p key={s.name} className="flex items-center gap-1.5">
                    <span className="inline-block h-0.5 w-3" style={{ background: SERIES[si] }} aria-hidden="true" />
                    <strong className="font-semibold text-gray-900">{format(s.values[active] ?? 0)}</strong>
                    {two && <span className="text-gray-500">{s.name}</span>}
                  </p>
                ))}
              </div>
            )}
          </div>
          <div className="mt-1 flex text-[11px] text-gray-500">
            {labels.map((label, i) => (
              <span key={label + i} className="truncate text-center" style={{ width: `${slot}%` }}>{i % tickEvery === 0 ? label : ''}</span>
            ))}
          </div>
        </div>
      </div>
      <TableView caption={title} head={[ '', ...series.map((s) => s.name)]}
        rows={labels.map((l, i) => [fullLabels?.[i] ?? l, ...series.map((s) => format(s.values[i] ?? 0))])} />
    </figure>
  );
}

// ---------------------------------------------------------------------- bar list
/**
 * Horizontal bars, one series, sorted by the caller - for "which categories /
 * people / items" questions. Value at the bar tip; the name above it.
 */
export function BarList({
  title, rows, format = compact, empty = 'Nothing in this period.',
}: {
  title: string; rows: Array<{ label: string; value: number; note?: string }>; format?: (n: number) => string; empty?: string;
}) {
  const max = Math.max(0, ...rows.map((r) => r.value));
  if (!rows.length) return <p className="py-6 text-center text-sm text-gray-400">{empty}</p>;
  return (
    <figure>
      <figcaption className="sr-only">{title}</figcaption>
      <ul className="space-y-2.5">
        {rows.map((r) => (
          <li key={r.label} title={`${r.label}: ${format(r.value)}${r.note ? ` (${r.note})` : ''}`}>
            <div className="mb-1 flex items-baseline justify-between gap-2 text-sm">
              <span className="truncate text-gray-700">{r.label}{r.note && <span className="ml-1 text-xs text-gray-400">{r.note}</span>}</span>
              <span className="shrink-0 font-medium tabular-nums text-gray-900">{format(r.value)}</span>
            </div>
            <div className="h-2 rounded-r bg-gray-100">
              <div className="h-2 rounded-r" style={{ width: `${max ? Math.max((r.value / max) * 100, 1) : 0}%`, background: SERIES[0] }} />
            </div>
          </li>
        ))}
      </ul>
      <TableView caption={title} head={['', 'Value']} rows={rows.map((r) => [r.label, format(r.value)])} />
    </figure>
  );
}

// ---------------------------------------------------------------------- stat tile
export function StatTile({
  label, value, delta, goodWhenUp = true, hint,
}: {
  label: string; value: string; delta?: number | null; goodWhenUp?: boolean; hint?: string;
}) {
  const showDelta = delta !== undefined && delta !== null && Number.isFinite(delta);
  const good = showDelta && (delta! >= 0) === goodWhenUp;
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-gray-900">{value}</p>
      {showDelta && (
        <p className={`mt-0.5 text-xs font-medium ${delta === 0 ? 'text-gray-500' : good ? 'text-green-700' : 'text-red-700'}`}>
          {delta! > 0 ? '▲' : delta! < 0 ? '▼' : '='} {Math.abs(delta!).toFixed(0)}% vs previous period
        </p>
      )}
      {hint && <p className="mt-0.5 text-xs text-gray-400">{hint}</p>}
    </div>
  );
}
