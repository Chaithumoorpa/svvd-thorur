'use client';

import React, { useState } from 'react';
import { MonitorPlay, Save } from 'lucide-react';
import { Notice } from '@/components/ui/States';
import { btnGhost, btnPrimary, cardCls } from '@/components/ui/styles';
import { useAction } from '@/hooks/useAction';
import { updateTemple } from '@/lib/api';
import { TV_SECTIONS } from '@/lib/tv';

/** "Show on lobby TV" checkboxes. Only public content is offered - tickets, messages,
 * donors, donations, finance, users and the audit log can never appear on a screen. */
export default function TvSectionsCard({ initial }: { initial: string[] }) {
  const [picked, setPicked] = useState<string[]>(initial);
  const action = useAction();
  const toggle = (key: string) => setPicked((p) => (p.includes(key) ? p.filter((k) => k !== key) : [...p, key]));

  return (
    <section className={`${cardCls} mt-6 space-y-4 p-5`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 font-serif text-lg font-bold text-maroon-dark">
            <MonitorPlay className="h-5 w-5" aria-hidden="true" /> Show on lobby TV
          </h2>
          <p className="text-sm text-gray-600">Choose what the temple TV (<code>/tv</code>) rotates through. It refreshes within 5 minutes of saving.</p>
        </div>
        <div className="flex shrink-0 gap-2">
          <button type="button" className={btnGhost} onClick={() => setPicked(TV_SECTIONS.map((s) => s.key))}>All</button>
          <button type="button" className={btnGhost} onClick={() => setPicked([])}>None</button>
        </div>
      </div>
      {action.success && <Notice kind="success">{action.success}</Notice>}
      {action.error && <Notice kind="error">{action.error}</Notice>}
      <div className="grid gap-3 sm:grid-cols-2">
        {TV_SECTIONS.map((s) => (
          <label key={s.key} className="flex cursor-pointer items-start gap-3 rounded-lg border border-amber-100 p-3 hover:bg-amber-50">
            <input type="checkbox" className="mt-1 h-4 w-4 accent-maroon" checked={picked.includes(s.key)} onChange={() => toggle(s.key)} />
            <span><span className="block font-semibold text-gray-900">{s.label}</span><span className="block text-xs text-gray-500">{s.hint}</span></span>
          </label>
        ))}
      </div>
      <div className="flex justify-end">
        <button type="button" className={btnPrimary} disabled={action.busy}
                onClick={() => action.run(() => updateTemple({ tv_sections: picked }), 'TV display saved.')}>
          <Save className="h-4 w-4" aria-hidden="true" /> {action.busy ? 'Saving…' : 'Save TV display'}
        </button>
      </div>
    </section>
  );
}
