'use client';

import React, { useEffect, useState } from 'react';
import { Save } from 'lucide-react';
import AdminPage from '@/components/admin/AdminPage';
import Field from '@/components/ui/Field';
import { ErrorBlock, LoadingBlock, Notice } from '@/components/ui/States';
import { btnPrimary, cardCls, inputCls } from '@/components/ui/styles';
import { useAction } from '@/hooks/useAction';
import { getHundiQr, getTemple, updateTemple } from '@/lib/api';
import { emptyToNull } from '@/lib/format';
import type { HundiQrInfo, Temple } from '@/lib/types';
import axios from 'axios';

type Form = Record<Exclude<keyof Temple, 'id'>, string>;

const FIELDS: Array<{ key: keyof Form; label: string; hint?: string; type?: string; wide?: boolean; area?: boolean; required?: boolean }> = [
  { key: 'name', label: 'Temple name', required: true, wide: true },
  { key: 'deity_name', label: 'Presiding deity' },
  { key: 'tagline', label: 'Tagline', hint: 'One line shown under the name.' },
  { key: 'address', label: 'Street address', wide: true },
  { key: 'village', label: 'Village / town' },
  { key: 'district', label: 'District' },
  { key: 'state', label: 'State' },
  { key: 'pincode', label: 'PIN code' },
  { key: 'contact_phone', label: 'Phone', type: 'tel' },
  { key: 'whatsapp_number', label: 'WhatsApp number', type: 'tel' },
  { key: 'contact_email', label: 'Email', type: 'email', wide: true },
  { key: 'map_url', label: 'Map link', hint: 'Google Maps share link.', wide: true },
  { key: 'hero_image_url', label: 'Home page banner image', hint: 'Optional web address of a wide photo.', wide: true },
  { key: 'facebook_url', label: 'Facebook page' },
  { key: 'instagram_url', label: 'Instagram page' },
  { key: 'youtube_url', label: 'YouTube channel' },
  {
    key: 'upi_vpa', label: 'UPI ID for e-Hundi', hint: 'e.g. temple@upi. Devotees scan a QR built from this to pay the Hundi directly - set to remove the Online Hundi page.',
  },
  { key: 'history', label: 'Temple history', area: true, wide: true, hint: 'Shown on the About page. Separate paragraphs with a blank line.' },
];

const toForm = (t: Temple | null): Form =>
  Object.fromEntries(FIELDS.map(({ key }) => [key, (t?.[key as keyof Temple] as string | null) ?? ''])) as Form;

function printHundiPoster(qr: HundiQrInfo, templeName: string) {
  const win = window.open('', '_blank');
  if (!win) return;
  win.document.write(`<!doctype html><html><head><title>Hundi QR</title><style>
    body { font-family: sans-serif; text-align: center; padding: 40px; }
    img { width: 320px; height: 320px; margin: 24px auto; }
    h1 { margin-bottom: 4px; } p { color: #444; }
  </style></head><body>
    <h1>${templeName}</h1>
    <p>Scan to offer to the Hundi via any UPI app</p>
    <img src="data:image/png;base64,${qr.qr_base64}" alt="Hundi UPI QR" />
    <p>${qr.upi_vpa}</p>
  </body></html>`);
  win.document.close();
  win.focus();
  win.print();
}

export default function TempleAdmin() {
  const [form, setForm] = useState<Form | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [hundiQr, setHundiQr] = useState<HundiQrInfo | null>(null);
  const action = useAction();

  useEffect(() => {
    getTemple()
      .then((t) => setForm(toForm(t)))
      .catch((err) => {
        // 404 = profile not created yet: start from an empty form
        if (axios.isAxiosError(err) && err.response?.status === 404) setForm(toForm(null));
        else setLoadError('Could not load the temple profile.');
      });
    getHundiQr().then(setHundiQr).catch(() => setHundiQr(null));
  }, [action.success]);

  if (loadError) return <ErrorBlock message={loadError} onRetry={() => window.location.reload()} />;
  if (!form) return <LoadingBlock />;

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!form) return;
    const payload: Record<string, string | null> = {};
    for (const { key } of FIELDS) payload[key] = emptyToNull(form[key]);
    await action.run(() => updateTemple(payload as never), 'Temple information saved. The website updates within a minute.');
  }

  return (
    <AdminPage title="Temple Information" description="Details shown across the public website: header, footer, contact and About pages.">
      <form onSubmit={save} className={`${cardCls} space-y-5 p-5`}>
        {action.success && <Notice kind="success">{action.success}</Notice>}
        {action.error && <Notice kind="error">{action.error}</Notice>}
        <div className="grid gap-4 sm:grid-cols-2">
          {FIELDS.map(({ key, label, hint, type, wide, area, required }) => (
            <Field key={key} label={label} hint={hint} required={required} className={wide ? 'sm:col-span-2' : undefined}>
              {area ? (
                <textarea className={inputCls} rows={8} maxLength={20000} value={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })} />
              ) : (
                <input type={type ?? 'text'} className={inputCls} value={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })} />
              )}
            </Field>
          ))}
        </div>
        <div className="flex justify-end">
          <button type="submit" className={btnPrimary} disabled={action.busy || !form.name.trim()}>
            <Save className="h-4 w-4" aria-hidden="true" /> {action.busy ? 'Saving…' : 'Save changes'}
          </button>
        </div>
      </form>

      {hundiQr?.configured && (
        <div className={`${cardCls} mt-6 flex flex-wrap items-center gap-4 p-5`}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={`data:image/png;base64,${hundiQr.qr_base64}`} alt="Hundi UPI QR" className="h-24 w-24 rounded border border-gray-200" />
          <div className="flex-1">
            <p className="font-medium text-gray-800">Online Hundi QR</p>
            <p className="text-sm text-gray-500">{hundiQr.upi_vpa} - shown on the public &quot;Online Hundi&quot; page.</p>
          </div>
          <button type="button" className={btnPrimary} onClick={() => printHundiPoster(hundiQr, form.name || 'Temple')}>
            Print poster
          </button>
        </div>
      )}
    </AdminPage>
  );
}
