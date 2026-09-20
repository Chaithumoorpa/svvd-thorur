'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  Banknote, Calendar, Church, Clock, HandHeart, Heart, History, Image as ImageIcon, LayoutDashboard,
  LogOut, Mail, Megaphone, Menu, ShieldCheck, Sparkles, Ticket, Users, X,
} from 'lucide-react';

import { AuthContext } from '@/components/admin/AuthContext';
import { LoadingBlock } from '@/components/ui/States';
import { getMe, setStoredToken, getStoredToken } from '@/lib/api';
import type { Me, Permission } from '@/lib/types';

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  permission?: Permission;
  group: string;
}

const NAV: NavItem[] = [
  { name: 'Dashboard', href: '/admin', icon: LayoutDashboard, permission: 'dashboard:view', group: 'Overview' },
  { name: 'Temple Info', href: '/admin/temple', icon: Church, permission: 'temple:write', group: 'Website' },
  { name: 'Timings', href: '/admin/timings', icon: Clock, permission: 'temple:write', group: 'Website' },
  { name: 'Announcements', href: '/admin/announcements', icon: Megaphone, permission: 'content:write', group: 'Website' },
  { name: 'Festivals', href: '/admin/festivals', icon: Calendar, permission: 'content:write', group: 'Website' },
  { name: 'Poojas & Sevas', href: '/admin/poojas', icon: Sparkles, permission: 'content:write', group: 'Website' },
  { name: 'Gallery', href: '/admin/gallery', icon: ImageIcon, permission: 'content:write', group: 'Website' },
  { name: 'Seva Tickets', href: '/admin/seva-tickets', icon: Ticket, permission: 'tickets:manage', group: 'Temple' },
  { name: 'Messages', href: '/admin/messages', icon: Mail, permission: 'messages:manage', group: 'Temple' },
  { name: 'Members', href: '/admin/members', icon: Users, permission: 'members:read', group: 'Temple' },
  { name: 'Donors', href: '/admin/donors', icon: Heart, permission: 'donors:read', group: 'Finance' },
  { name: 'Donations', href: '/admin/donations', icon: HandHeart, permission: 'donations:read', group: 'Finance' },
  { name: 'Finance', href: '/admin/finance', icon: Banknote, permission: 'finance:read', group: 'Finance' },
  { name: 'Users', href: '/admin/users', icon: ShieldCheck, permission: 'users:manage', group: 'Administration' },
  { name: 'Audit Log', href: '/admin/audit', icon: History, permission: 'audit:read', group: 'Administration' },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [me, setMe] = useState<Me | null>(null);
  const [checking, setChecking] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function check() {
      if (!getStoredToken()) {
        router.replace('/login');
        return;
      }
      try {
        const current = await getMe();
        if (cancelled) return;
        if (current.must_change_password && !pathname.startsWith('/admin/change-password')) {
          router.replace('/admin/change-password');
          return;
        }
        setMe(current);
      } catch {
        if (!cancelled) {
          setStoredToken(null);
          router.replace('/login');
        }
      } finally {
        if (!cancelled) setChecking(false);
      }
    }
    check();
    return () => {
      cancelled = true;
    };
    // verified once per admin session; an expired/disabled session is caught by the 401 handler
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const can = useCallback((p: Permission) => !!me?.permissions.includes(p), [me]);
  const ctx = useMemo(() => (me ? { me, can } : null), [me, can]);

  const logout = () => {
    setStoredToken(null);
    router.push('/');
  };

  if (checking && !me) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <LoadingBlock label="Verifying access…" />
      </div>
    );
  }
  if (!ctx || !me) return null;

  const visible = NAV.filter((item) => !item.permission || can(item.permission));
  const current = NAV.find((item) => (item.href === '/admin' ? pathname === '/admin' : pathname.startsWith(item.href)));
  const allowed = pathname.startsWith('/admin/change-password') || !current?.permission || can(current.permission);
  const hasAnyAccess = can('dashboard:view');
  const groups = Array.from(new Set(visible.map((i) => i.group)));

  return (
    <AuthContext.Provider value={ctx}>
      <div className="flex h-screen bg-gray-50">
        <div className="fixed left-3 top-3 z-50 lg:hidden">
          <button
            type="button"
            onClick={() => setSidebarOpen((open) => !open)}
            aria-label={sidebarOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={sidebarOpen}
            className="rounded-lg bg-white p-2 shadow"
          >
            {sidebarOpen ? <X /> : <Menu />}
          </button>
        </div>

        <aside
          aria-label="Admin navigation"
          className={`fixed z-40 flex h-full w-64 flex-col overflow-y-auto bg-slate-900 text-white transition-transform lg:static lg:translate-x-0 ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          <div className="border-b border-slate-700 p-5">
            <p className="font-serif text-lg font-bold text-amber-400">Temple Admin</p>
            <p className="mt-1 truncate text-xs text-slate-400">
              {me.username} · {me.roles.join(', ').replace(/_/g, ' ').toLowerCase()}
            </p>
          </div>

          <nav className="flex-1 space-y-4 p-3">
            {groups.map((group) => (
              <div key={group}>
                <p className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-500">{group}</p>
                <ul className="space-y-0.5">
                  {visible
                    .filter((item) => item.group === group)
                    .map(({ name, href, icon: Icon }) => {
                      const active = href === '/admin' ? pathname === '/admin' : pathname.startsWith(href);
                      return (
                        <li key={href}>
                          <Link
                            href={href}
                            onClick={() => setSidebarOpen(false)}
                            aria-current={active ? 'page' : undefined}
                            className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm ${
                              active ? 'bg-slate-700 text-white' : 'text-slate-300 hover:bg-slate-800'
                            }`}
                          >
                            <Icon className="h-4 w-4" />
                            {name}
                          </Link>
                        </li>
                      );
                    })}
                </ul>
              </div>
            ))}
          </nav>

          <div className="space-y-1 border-t border-slate-700 p-3">
            <Link href="/" className="block rounded-md px-3 py-2 text-sm text-slate-300 hover:bg-slate-800">
              ← View website
            </Link>
            <Link href="/admin/change-password" className="block rounded-md px-3 py-2 text-sm text-slate-300 hover:bg-slate-800">
              Change password
            </Link>
            <button
              type="button"
              onClick={logout}
              className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-slate-300 hover:bg-red-700 hover:text-white"
            >
              <LogOut className="h-4 w-4" /> Sign out
            </button>
          </div>
        </aside>

        <main className="min-w-0 flex-1 overflow-auto">
          {!hasAnyAccess && !pathname.startsWith('/admin/change-password') ? (
            <NoAccess message="Your account does not have access to the admin area. Please contact the temple administrator." />
          ) : !allowed ? (
            <NoAccess message="Your role does not include this section." />
          ) : (
            children
          )}
        </main>

        {sidebarOpen && <div className="fixed inset-0 z-30 bg-black/40 lg:hidden" onClick={() => setSidebarOpen(false)} aria-hidden="true" />}
      </div>
    </AuthContext.Provider>
  );
}

function NoAccess({ message }: { message: string }) {
  return (
    <div className="mx-auto max-w-md px-4 pt-24 text-center">
      <ShieldCheck className="mx-auto mb-4 h-12 w-12 text-gray-300" aria-hidden="true" />
      <h1 className="text-xl font-semibold text-gray-800">Access restricted</h1>
      <p className="mt-2 text-sm text-gray-500">{message}</p>
    </div>
  );
}
