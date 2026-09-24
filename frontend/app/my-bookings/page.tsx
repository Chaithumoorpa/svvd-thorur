'use client';

import React, { useEffect, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Download, LogIn } from 'lucide-react';
import { apiError, downloadTicketPdf, getMyTickets, getStoredToken, saveBlob } from '@/lib/api';
import type { SevaTicket } from '@/lib/types';
import { EmptyBlock, ErrorBlock, LoadingBlock } from '@/components/ui/States';
import { btnGhost } from '@/components/ui/styles';
import { formatDate, formatMoney } from '@/lib/format';

const STATUS_STYLE: Record<SevaTicket['status'], string> = {
  ACTIVE: 'bg-green-100 text-green-800',
  USED: 'bg-gray-100 text-gray-600',
  CANCELLED: 'bg-red-100 text-red-700',
};

function TicketCard({ ticket }: { ticket: SevaTicket }) {
  const [downloading, setDownloading] = useState(false);

  async function download() {
    setDownloading(true);
    try {
      const blob = await downloadTicketPdf(ticket.id);
      saveBlob(blob, `${ticket.ticket_number}.pdf`);
    } catch {
      // best-effort - the ticket number below still lets them show up at the counter
    } finally {
      setDownloading(false);
    }
  }

  return (
    <li className="rounded-xl border border-amber-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-serif text-lg font-semibold text-maroon">{ticket.seva_name}</p>
          <p className="text-sm text-gray-600">{formatDate(ticket.seva_date)}{ticket.seva_time ? ` · ${ticket.seva_time}` : ''}</p>
          <p className="mt-1 font-mono text-xs text-gray-500">{ticket.ticket_number}</p>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${STATUS_STYLE[ticket.status]}`}>{ticket.status}</span>
      </div>
      <div className="mt-3 flex items-center justify-between gap-3">
        <p className="text-sm text-gray-700">
          {ticket.payment_status === 'PAID' ? formatMoney(ticket.amount)
            : ticket.payment_status === 'PENDING' ? <span className="font-medium text-amber-700">{formatMoney(ticket.amount)} due at counter</span>
            : 'Free'}
        </p>
        <button type="button" onClick={download} disabled={downloading} className={btnGhost}>
          <Download className="h-4 w-4" aria-hidden="true" /> {downloading ? 'Downloading…' : 'Download ticket'}
        </button>
      </div>
    </li>
  );
}

export default function MyBookingsPage() {
  const [signedIn, setSignedIn] = useState<boolean | null>(null);
  const [tickets, setTickets] = useState<SevaTicket[] | null>(null);
  const [error, setError] = useState('');

  function load() {
    setError('');
    setTickets(null);
    getMyTickets()
      .then(setTickets)
      .catch((err) => setError(apiError(err, 'Could not load your bookings.')));
  }

  useEffect(() => {
    setSignedIn(!!getStoredToken());
  }, []);

  useEffect(() => {
    if (signedIn) load();
  }, [signedIn]);

  return (
    <main className="mx-auto min-h-[60vh] max-w-3xl px-4 py-10">
      <div className="mb-6 text-center">
        <Image src="/logo.png" alt="" width={56} height={56} className="mx-auto mb-3" />
        <h1 className="font-serif text-2xl font-bold text-maroon">My Bookings</h1>
        <p className="mt-1 text-sm text-gray-500">Sevas you booked while signed in to your account</p>
      </div>

      {signedIn === null ? (
        <LoadingBlock />
      ) : !signedIn ? (
        <EmptyBlock
          title="Sign in to see your bookings"
          hint="Only sevas you book while signed in show up here. Bookings made without an account are tracked by your ticket number instead."
          icon={<LogIn className="h-10 w-10" aria-hidden="true" />}
          action={
            <Link href="/login" className={btnGhost}>
              Sign in
            </Link>
          }
        />
      ) : error ? (
        <ErrorBlock message={error} onRetry={load} />
      ) : tickets === null ? (
        <LoadingBlock />
      ) : tickets.length === 0 ? (
        <EmptyBlock title="No bookings yet" hint="Book a seva from the Poojas page - it'll show up here." />
      ) : (
        <ul className="space-y-3">
          {tickets.map((t) => (
            <TicketCard key={t.id} ticket={t} />
          ))}
        </ul>
      )}

      <p className="mt-6 text-center text-sm">
        <Link href="/" className="text-red-900 hover:underline">
          ← Back to the temple website
        </Link>
      </p>
    </main>
  );
}
