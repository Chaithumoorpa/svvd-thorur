'use client';

/** Loads Razorpay's own Checkout.js once and opens it - used by both the
 * public donation form and BookSeva's "pay online" option. Checkout.js is a
 * hosted overlay (the actual card/UPI/netbanking entry happens inside it,
 * never on this page), so there's nothing here to validate beyond the result
 * it hands back. */

interface RazorpayCheckoutOptions {
  key: string;
  amount: number;
  currency: string;
  name: string;
  description?: string;
  order_id: string;
  prefill?: { name?: string; email?: string; contact?: string };
  theme?: { color?: string };
  handler: (response: CheckoutSuccess) => void;
  modal?: { ondismiss?: () => void };
}

interface RazorpayCheckout {
  open: () => void;
  on: (event: 'payment.failed', handler: (response: { error?: { description?: string } }) => void) => void;
}

declare global {
  interface Window {
    Razorpay?: new (options: RazorpayCheckoutOptions) => RazorpayCheckout;
  }
}

export interface CheckoutSuccess {
  razorpay_payment_id: string;
  razorpay_order_id: string;
  razorpay_signature: string;
}

/** Thrown by openRazorpayCheckout when the devotee closes the overlay
 * without completing payment - not an error to show, just "they changed
 * their mind"; callers should let the form stay as it was. */
export class CheckoutDismissedError extends Error {
  constructor() {
    super('Payment window closed');
    this.name = 'CheckoutDismissedError';
  }
}

const SCRIPT_URL = 'https://checkout.razorpay.com/v1/checkout.js';
let scriptPromise: Promise<void> | null = null;

function loadCheckoutScript(): Promise<void> {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('Payment can only be started in a browser.'));
  }
  if (window.Razorpay) return Promise.resolve();
  if (!scriptPromise) {
    scriptPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = SCRIPT_URL;
      script.async = true;
      script.onload = () => resolve();
      script.onerror = () => {
        scriptPromise = null; // let a retry try loading it again
        reject(new Error('Could not load the payment page. Please check your connection and try again.'));
      };
      document.body.appendChild(script);
    });
  }
  return scriptPromise;
}

export async function openRazorpayCheckout(opts: {
  keyId: string;
  orderId: string;
  amountPaise: number;
  currency: string;
  name: string;
  description?: string;
  prefill?: { name?: string; email?: string; contact?: string };
}): Promise<CheckoutSuccess> {
  await loadCheckoutScript();
  return new Promise((resolve, reject) => {
    if (!window.Razorpay) {
      reject(new Error('Could not load the payment page. Please check your connection and try again.'));
      return;
    }
    const checkout = new window.Razorpay({
      key: opts.keyId,
      amount: opts.amountPaise,
      currency: opts.currency,
      name: opts.name,
      description: opts.description,
      order_id: opts.orderId,
      prefill: opts.prefill,
      theme: { color: '#7a1c1c' },
      handler: (response) => resolve(response),
      modal: { ondismiss: () => reject(new CheckoutDismissedError()) },
    });
    checkout.on('payment.failed', (response) => {
      reject(new Error(response.error?.description || 'Payment failed. Please try again.'));
    });
    checkout.open();
  });
}
