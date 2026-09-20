'use client';

import Link from 'next/link';
import { Calendar, Heart, Image as ImageIcon, Mail, Megaphone, Sparkles, Ticket, Users } from 'lucide-react';
import AdminPage from '@/components/admin/AdminPage';
import { useAuth } from '@/components/admin/AuthContext';
import { ErrorBlock, LoadingBlock } from '@/components/ui/States';
import { cardCls } from '@/components/ui/styles';
import { useLoad } from '@/hooks/useLoad';
import { getDashboardStats, getRecentActivity } from '@/lib/api';
import { formatDateTime } from '@/lib/format';
import type { Permission } from '@/lib/types';

interface Tile {
  label: string;
  href: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  permission: Permission;
  hint?: string;
}

export default function AdminDashboard() {
  const { me, can } = useAuth();
  const stats = useLoad(getDashboardStats, []);
  const activity = useLoad(async () => (can('audit:read') ? getRecentActivity() : []), []);

  if (stats.loading) return <LoadingBlock label="Loading dashboard…" />;
  if (stats.error || !stats.data) return <ErrorBlock message={stats.error ?? 'No data'} onRetry={stats.reload} />;
  const s = stats.data;

  const tiles: Tile[] = [
    { label: 'Pending messages', href: '/admin/messages', value: s.pending_messages, icon: Mail, permission: 'messages:manage', hint: 'need a reply' },
    { label: 'Seva tickets today', href: '/admin/seva-tickets', value: s.seva_tickets_today, icon: Ticket, permission: 'tickets:manage', hint: `${s.seva_tickets} in total` },
    { label: 'Live announcements', href: '/admin/announcements', value: s.announcements, icon: Megaphone, permission: 'content:write' },
    { label: 'Upcoming festivals', href: '/admin/festivals', value: s.upcoming_festivals, icon: Calendar, permission: 'content:write' },
    { label: 'Poojas & sevas', href: '/admin/poojas', value: s.poojas, icon: Sparkles, permission: 'content:write' },
    { label: 'Gallery photos', href: '/admin/gallery', value: s.gallery, icon: ImageIcon, permission: 'content:write' },
    { label: 'Members', href: '/admin/members', value: s.members, icon: Users, permission: 'members:read' },
    { label: 'Donors', href: '/admin/donors', value: s.donors, icon: Heart, permission: 'donors:read' },
  ];
  const visible = tiles.filter((t) => can(t.permission));

  return (
    <AdminPage title={`Namaste, ${me.username}`} description={me.last_login ? `Last sign-in: ${formatDateTime(me.last_login)}` : 'Welcome to the temple admin.'}>
      <section aria-label="Overview" className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {visible.map(({ label, href, value, icon: Icon, hint }) => (
          <Link key={label} href={href} className={`${cardCls} p-4 transition hover:border-amber-400 hover:shadow`}>
            <Icon className="h-5 w-5 text-red-800" aria-hidden="true" />
            <p className="mt-3 text-3xl font-bold text-gray-900">{value}</p>
            <p className="text-sm text-gray-600">{label}</p>
            {hint && <p className="text-xs text-gray-400">{hint}</p>}
          </Link>
        ))}
      </section>

      {can('audit:read') && (
        <section className={`${cardCls} mt-8 p-5`} aria-labelledby="recent-heading">
          <div className="mb-3 flex items-center justify-between">
            <h2 id="recent-heading" className="font-semibold text-gray-900">
              Recent changes
            </h2>
            <Link href="/admin/audit" className="text-sm text-red-900 hover:underline">
              Full audit log →
            </Link>
          </div>
          {activity.loading ? (
            <LoadingBlock />
          ) : activity.error ? (
            <ErrorBlock message={activity.error} onRetry={activity.reload} />
          ) : !activity.data?.length ? (
            <p className="py-6 text-center text-sm text-gray-500">No activity recorded yet.</p>
          ) : (
            <ul className="divide-y divide-gray-100">
              {activity.data.map((item) => (
                <li key={item.id} className="flex flex-wrap justify-between gap-2 py-2 text-sm">
                  <span className="text-gray-800">{item.text}</span>
                  <span className="text-xs text-gray-500">
                    {item.actor ?? 'system'} · {formatDateTime(item.created_at)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </AdminPage>
  );
}
