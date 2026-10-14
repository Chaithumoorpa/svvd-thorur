'use client';

import React, { useState } from 'react';
import { CheckCircle2, HeartHandshake } from 'lucide-react';
import Field from '@/components/ui/Field';
import { Notice } from '@/components/ui/States';
import TurnstileWidget from '@/components/ui/TurnstileWidget';
import { btnGhost, btnPrimary, cardCls, inputCls } from '@/components/ui/styles';
import { useLoad } from '@/hooks/useLoad';
import { useTurnstile } from '@/hooks/useTurnstile';
import { apiError, confirmDonationPayment, createDonationOrder, getPaymentStatus } from '@/lib/api';
import { formatMoney } from '@/lib/format';
import { CheckoutDismissedError, openRazorpayCheckout } from '@/lib/razorpay';
import type { Donation, DonationType } from '@/lib/types';

const PRESET_AMOUNTS = [101, 501, 1001, 2100];
const TYPE_LABELS: Record<DonationType, string> = {
  general: 'General',
  annadanam: 'Annadanam (Food Offering)',
  festival: 'Festival',
  pooja: 'Pooja',
  construction: 'Construction',
  other: 'Other',
};
const TYPES = Object.keys(TYPE_LABELS) as DonationType[];

/** The public donation form - pays via Razorpay and records the donation only
 * once the payment is verified (see /donations/public/order and .../confirm).
 * Renders nothing while checking whether online payment is configured, and
 * hands back to the caller (the donations page's own "coming soon" block) if
 * it isn't - so the page never shows a form that would only 503. English-only,
 * matching BookSeva's own payment form. */
export default function DonationForm({ fallback }: { fallback: React.ReactNode }) {
  const status = useLoad(getPaymentStatus, []);

  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [pan, setPan] = useState('');
  const [address, setAddress] = useState('');
  const [amount, setAmount] = useState<number>(PRESET_AMOUNTS[1]);
  const [customAmount, setCustomAmount] = useState('');
  const [usingCustom, setUsingCustom] = useState(false);
  const [donationType, setDonationType] = useState<DonationType>('general');
  const [purpose, setPurpose] = useState('');
  const [occasion, setOccasion] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [donation, setDonation] = useState<Donation | null>(null);
  const turnstile = useTurnstile();

  const effectiveAmount = usingCustom ? Number(customAmount) || 0 : amount;
  const validAmount = effectiveAmount > 0 && effectiveAmount <= 1_000_000;

  function reset() {
    setName(''); setPhone(''); setEmail(''); setPan(''); setAddress('');
    setAmount(PRESET_AMOUNTS[1]); setCustomAmount(''); setUsingCustom(false);
    setDonationType('general'); setPurpose(''); setOccasion('');
    setError(''); setDonation(null); turnstile.reset();
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      const order = await createDonationOrder({
        donor_name: name.trim(), phone: phone.trim(), email: email.trim() || undefined,
        pan_number: pan.trim() || undefined, address: address.trim() || undefined,
        amount: effectiveAmount, donation_type: donationType, purpose: purpose.trim() || undefined,
        occasion: occasion.trim() || undefined, turnstile_token: turnstile.token || undefined,
      });
      const paid = await openRazorpayCheckout({
        keyId: order.key_id, orderId: order.order_id, amountPaise: order.amount_paise, currency: order.currency,
        name: 'Sri Varasidhi Vinayaka Swamy Devasthanam', description: TYPE_LABELS[donationType],
        prefill: { name: name.trim(), email: email.trim() || undefined, contact: phone.trim() },
      });
      const recorded = await confirmDonationPayment({
        payment_token: order.payment_token, razorpay_order_id: paid.razorpay_order_id,
        razorpay_payment_id: paid.razorpay_payment_id, razorpay_signature: paid.razorpay_signature,
      });
      turnstile.reset();
      setDonation(recorded);
    } catch (err) {
      turnstile.reset();
      if (err instanceof CheckoutDismissedError) {
        setError('Payment window closed. You can try again whenever you are ready.');
      } else {
        setError(apiError(err, 'Payment could not be completed. Please try again.'));
      }
    } finally {
      setBusy(false);
    }
  }

  if (status.loading) return null;
  if (!status.data?.enabled) return <>{fallback}</>;

  if (donation) {
    return (
      <div className={`${cardCls} mx-auto max-w-lg p-8 text-center`}>
        <CheckCircle2 className="mx-auto h-12 w-12 text-green-600" aria-hidden="true" />
        <h2 className="mt-3 font-serif text-2xl font-bold text-maroon">Thank you for your donation</h2>
        <p className="mt-2 text-sm text-gray-600">Your contribution has been recorded and a receipt has been issued.</p>
        <div className="mt-4 rounded-lg bg-amber-50 p-4">
          <p className="text-xs uppercase tracking-wide text-gray-500">Receipt Number</p>
          <p className="font-mono text-lg font-bold text-maroon-dark">{donation.receipt_number}</p>
          <p className="mt-1 text-sm text-gray-700">{formatMoney(donation.amount)}</p>
        </div>
        <p className="mt-4 text-xs text-gray-500">A copy of your receipt has been emailed to you, if an email address was provided.</p>
        <button type="button" className={`${btnGhost} mx-auto mt-6`} onClick={reset}>Make another donation</button>
      </div>
    );
  }

  return (
    <form onSubmit={submit} className={`${cardCls} mx-auto max-w-lg space-y-4 p-6 sm:p-8`}>
      <div className="text-center">
        <HeartHandshake className="mx-auto h-10 w-10 text-saffron" aria-hidden="true" />
        <h2 className="mt-2 font-serif text-2xl font-bold text-maroon">Make a Donation</h2>
        <p className="mt-1 text-sm text-gray-600">Your contribution supports the temple's daily worship and services.</p>
      </div>
      {error && <Notice kind="error">{error}</Notice>}

      <Field label="Full Name" required>
        <input className={inputCls} maxLength={150} autoComplete="name" value={name} onChange={(e) => setName(e.target.value)} />
      </Field>
      <Field label="Mobile Number" required hint="Used to send your receipt and for follow-up if needed">
        <input className={inputCls} type="tel" inputMode="tel" autoComplete="tel" value={phone} onChange={(e) => setPhone(e.target.value)} />
      </Field>
      <Field label="Email" hint="Optional - your receipt will be emailed here">
        <input className={inputCls} type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      </Field>

      <div>
        <span className="mb-1 block text-sm font-medium text-gray-700">Amount *</span>
        <div className="flex flex-wrap gap-2">
          {PRESET_AMOUNTS.map((preset) => (
            <button
              key={preset}
              type="button"
              onClick={() => { setUsingCustom(false); setAmount(preset); }}
              className={`rounded-lg border px-4 py-2 text-sm font-medium ${!usingCustom && amount === preset ? 'border-maroon bg-maroon text-white' : 'border-amber-300 bg-white text-maroon-dark hover:bg-amber-50'}`}
            >
              {formatMoney(preset)}
            </button>
          ))}
          <button
            type="button"
            onClick={() => setUsingCustom(true)}
            className={`rounded-lg border px-4 py-2 text-sm font-medium ${usingCustom ? 'border-maroon bg-maroon text-white' : 'border-amber-300 bg-white text-maroon-dark hover:bg-amber-50'}`}
          >
            Custom Amount
          </button>
        </div>
        {usingCustom && (
          <input
            className={`${inputCls} mt-2`} type="number" min={1} max={1_000_000} inputMode="decimal" autoFocus
            value={customAmount} onChange={(e) => setCustomAmount(e.target.value)}
          />
        )}
      </div>

      <Field label="Donation Type">
        <select className={inputCls} value={donationType} onChange={(e) => setDonationType(e.target.value as DonationType)}>
          {TYPES.map((type) => <option key={type} value={type}>{TYPE_LABELS[type]}</option>)}
        </select>
      </Field>
      <Field label="Purpose">
        <input className={inputCls} maxLength={1000} placeholder="e.g. In memory of, for a specific seva, etc." value={purpose} onChange={(e) => setPurpose(e.target.value)} />
      </Field>
      <Field label="Occasion" hint="Optional - birthday, anniversary, etc.">
        <input className={inputCls} maxLength={100} value={occasion} onChange={(e) => setOccasion(e.target.value)} />
      </Field>
      <Field label="PAN Number" hint="Optional - required only for 80G tax receipts above the exemption limit">
        <input className={inputCls} maxLength={20} value={pan} onChange={(e) => setPan(e.target.value.toUpperCase())} />
      </Field>
      <Field label="Address">
        <textarea className={inputCls} rows={2} maxLength={1000} value={address} onChange={(e) => setAddress(e.target.value)} />
      </Field>

      <div className="flex justify-center">
        <TurnstileWidget key={turnstile.widgetKey} onToken={turnstile.setToken} />
      </div>

      <button
        type="submit"
        className={`${btnPrimary} w-full justify-center`}
        disabled={busy || !validAmount || name.trim().length < 2 || phone.trim().length < 10}
      >
        {busy ? 'Opening payment…' : `Donate ${formatMoney(effectiveAmount)}`}
      </button>
    </form>
  );
}
