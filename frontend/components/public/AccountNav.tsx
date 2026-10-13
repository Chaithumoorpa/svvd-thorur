'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { LayoutDashboard, LogIn, LogOut, Ticket } from 'lucide-react';
import { getMe, isProbablySignedIn, logout } from '@/lib/api';
import type { Me } from '@/lib/types';

/**
 * Devotee sign-in/My Bookings link for the public header. Client-only since
 * the session is a browser cookie the server-rendered (cached) header can't
 * see, so this renders nothing until the check resolves (avoids a "Sign in"
 * flash for a devotee who is actually already signed in). Anonymous visitors
 * skip the server check entirely (see isProbablySignedIn).
 */
export default function AccountNav({ className = '' }: { className?: string }) {
  const [me, setMe] = useState<Me | null | undefined>(undefined);

  useEffect(() => {
    let cancelled = false;
    if (!isProbablySignedIn()) {
      setMe(null);
      return;
    }
    getMe()
      .then((m) => !cancelled && setMe(m))
      .catch(() => !cancelled && setMe(null));
    return () => {
      cancelled = true;
    };
  }, []);

  if (me === undefined) return null;

  // Color is inherited from the caller's own text color (header vs. mobile menu use
  // different backgrounds); only the hover treatment is fixed here.
  if (!me) {
    return (
      <Link href="/login" className={`inline-flex items-center gap-1 hover:underline ${className}`}>
        <LogIn className="h-3.5 w-3.5" aria-hidden="true" /> Sign in
      </Link>
    );
  }

  const isStaff = me.is_admin || me.is_trustee || me.permissions.length > 0;

  return (
    <span className={`inline-flex items-center gap-3 ${className}`}>
      {isStaff && (
        <Link href="/admin" className="inline-flex items-center gap-1 hover:underline">
          <LayoutDashboard className="h-3.5 w-3.5" aria-hidden="true" /> Admin
        </Link>
      )}
      <Link href="/my-bookings" className="inline-flex items-center gap-1 hover:underline">
        <Ticket className="h-3.5 w-3.5" aria-hidden="true" /> My Bookings
      </Link>
      <button
        type="button"
        onClick={async () => {
          await logout();
          window.location.href = '/';
        }}
        className="inline-flex items-center gap-1 hover:underline"
      >
        <LogOut className="h-3.5 w-3.5" aria-hidden="true" /> Sign out
      </button>
    </span>
  );
}
