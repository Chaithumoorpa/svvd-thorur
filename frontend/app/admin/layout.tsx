'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import {
  LayoutDashboard,
  Megaphone,
  Users,
  Heart,
  LogOut,
  Menu,
  X,
  Calendar,
  Image,
  Ticket,
  Mail,
  Banknote,
} from 'lucide-react';

import { getToken, verifyTokenStatus } from '@/app/utils/auth';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const token = getToken();

      if (!token) {
        router.push('/login');
        return;
      }

      try {
        const status = await verifyTokenStatus();

        if (status.mustChangePassword && !pathname.includes('/admin/change-password')) {
          router.push('/admin/change-password');
          return;
        }

        setIsAuthorized(true);
      } catch (err) {
        console.error('Auth check failed', err);
        router.push('/login');
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, [router]);

  const navItems = [
    { name: 'Dashboard', href: '/admin', icon: LayoutDashboard },
    { name: 'Poojas', href: '/admin/poojas', icon: Calendar },
    { name: 'Gallery', href: '/admin/gallery', icon: Image },
    { name: 'Announcements', href: '/admin/announcements', icon: Megaphone },
    { name: 'Festivals', href: '/admin/festivals', icon: Calendar },
    { name: 'Members', href: '/admin/members', icon: Users },
    { name: 'Donors', href: '/admin/donors', icon: Heart },
    { name: 'Seva Tickets', href: '/admin/seva-tickets', icon: Ticket },
    { name: 'Messages', href: '/admin/messages', icon: Mail },
    { name: 'Finance', href: '/admin/finance', icon: Banknote },
    { name: 'Users', href: '/admin/users', icon: Users, superAdminOnly: true },
  ];

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/');
  };

  const isActive = (href: string) =>
    href === '/admin' ? pathname === '/admin' : pathname.startsWith(href);

  /* ---------------- RENDER ---------------- */

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-white">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-gray-200 border-t-slate-900 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Verifying access…</p>
        </div>
      </div>
    );
  }

  if (!isAuthorized) return null;

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Mobile toggle */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 bg-white rounded-lg shadow"
        >
          {sidebarOpen ? <X /> : <Menu />}
        </button>
      </div>

      {/* Sidebar */}
      <aside
        className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          } lg:translate-x-0 fixed lg:relative z-40 w-64 bg-slate-900 text-white transition-transform`}
      >
        <div className="p-6 border-b border-slate-700 font-bold">
          Temple Admin
        </div>

        <nav className="p-4 space-y-1">
          {navItems.map(({ name, href, icon: Icon, superAdminOnly }: any) => {
            // Check if user is super admin for restricted items
            const isSuper = localStorage.getItem('token') ? (JSON.parse(atob(localStorage.getItem('token')!.split('.')[1])).roles || []).includes('SUPER_ADMIN') : false;
            if (superAdminOnly && !isSuper) return null;

            return (
              <Link
                key={name}
                href={href}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center gap-3 px-4 py-2 rounded-md ${isActive(href)
                  ? 'bg-slate-700'
                  : 'text-slate-300 hover:bg-slate-800'
                  }`}
              >
                <Icon className="w-5 h-5" />
                <span className="text-sm font-medium">{name}</span>
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-slate-700">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-4 py-2 rounded-md hover:bg-red-600"
          >
            <LogOut className="w-5 h-5" />
            Logout
          </button>
        </div>
      </aside>

      {/* Content */}
      <main className="flex-1 overflow-auto">{children}</main>

      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
