'use client';

import React, { useEffect, useState } from 'react';
import {
  Users,
  Heart,
  Megaphone,
  Calendar,
  Image as ImageIcon,
  Ticket,
  Clock,
  User as UserIcon,
  ChevronRight,
  PlusCircle,
  QrCode
} from 'lucide-react';
import Link from 'next/link';
import { verifyTokenStatus } from '@/app/utils/auth';

export default function AdminDashboard() {
  const [userInfo, setUserInfo] = useState<{
    username?: string;
    lastLogin?: string;
    isAdmin: boolean;
  } | null>(null);

  const [dashboardData, setDashboardData] = useState<{
    stats: any;
    activity: any[];
    loading: boolean;
  }>({
    stats: null,
    activity: [],
    loading: true
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const { api } = await import('@/lib/api');
        const authStatus = await verifyTokenStatus();

        setUserInfo({
          username: authStatus.username,
          lastLogin: authStatus.lastLogin,
          isAdmin: authStatus.isAdmin
        });

        const [statsRes, activityRes] = await Promise.all([
          api.get('/meta/stats'),
          api.get('/meta/activity')
        ]);

        setDashboardData({
          stats: statsRes.data,
          activity: activityRes.data,
          loading: false
        });
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
        setDashboardData(prev => ({ ...prev, loading: false }));
      }
    };
    fetchData();
  }, []);

  const stats = [
    { label: 'Poojas', value: dashboardData.stats?.poojas ?? '...', icon: Calendar, color: 'text-blue-600', bg: 'bg-blue-50', href: '/admin/poojas' },
    { label: 'Announcements', value: dashboardData.stats?.announcements ?? '...', icon: Megaphone, color: 'text-purple-600', bg: 'bg-purple-50', href: '/admin/announcements' },
    { label: 'Donors', value: dashboardData.stats?.donors ?? '...', icon: Heart, color: 'text-red-600', bg: 'bg-red-50', href: '/admin/donors' },
    { label: 'Gallery', value: dashboardData.stats?.gallery ?? '...', icon: ImageIcon, color: 'text-emerald-600', bg: 'bg-emerald-50', href: '/admin/gallery' },
    { label: 'Members', value: dashboardData.stats?.members ?? '...', icon: Users, color: 'text-indigo-600', bg: 'bg-indigo-50', href: '/admin/members' },
    { label: 'Seva Tickets', value: dashboardData.stats?.seva_tickets ?? '...', icon: Ticket, color: 'text-orange-600', bg: 'bg-orange-50', href: '/admin/seva-tickets' },
  ];

  const formatLastLogin = (dateStr?: string) => {
    if (!dateStr) return 'First time login';
    try {
      const date = new Date(dateStr);
      return date.toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      });
    } catch (e) {
      return 'N/A';
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8">
      {/* Header with User Info */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-slate-900 rounded-full flex items-center justify-center text-white">
            <UserIcon className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Welcome back, <span className="text-blue-600">{userInfo?.username || 'Admin'}</span>
            </h1>
            <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
              <Clock className="w-4 h-4" />
              <span>Last login: {formatLastLogin(userInfo?.lastLogin)}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-emerald-50 text-emerald-700 rounded-full text-sm font-medium border border-emerald-100">
          <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
          System Online
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {stats.map((stat) => (
          <Link
            key={stat.label}
            href={stat.href}
            className="group bg-white p-5 rounded-2xl shadow-sm border border-gray-100 hover:border-blue-200 hover:shadow-md transition-all"
          >
            <div className={`${stat.bg} ${stat.color} w-10 h-10 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
              <stat.icon className="w-5 h-5" />
            </div>
            <p className="text-sm font-medium text-gray-500">{stat.label}</p>
            <div className="flex items-end justify-between mt-1">
              <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-blue-500 transition-colors" />
            </div>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Quick Actions */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h2 className="text-lg font-bold text-gray-900 mb-6 flex items-center gap-2">
              <PlusCircle className="w-5 h-5 text-blue-500" />
              Quick Actions
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Link href="/admin/poojas" className="flex items-center justify-between p-4 rounded-xl border border-gray-50 bg-gray-50 hover:bg-white hover:border-blue-200 hover:shadow-sm transition-all group">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center">
                    <Calendar className="w-5 h-5" />
                  </div>
                  <span className="font-medium text-gray-700">Add New Pooja</span>
                </div>
                <ChevronRight className="w-4 h-4 text-gray-400 group-hover:translate-x-1 transition-transform" />
              </Link>

              <Link href="/admin/announcements" className="flex items-center justify-between p-4 rounded-xl border border-gray-50 bg-gray-50 hover:bg-white hover:border-purple-200 hover:shadow-sm transition-all group">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-purple-100 text-purple-600 flex items-center justify-center">
                    <Megaphone className="w-5 h-5" />
                  </div>
                  <span className="font-medium text-gray-700">Post Announcement</span>
                </div>
                <ChevronRight className="w-4 h-4 text-gray-400 group-hover:translate-x-1 transition-transform" />
              </Link>

              <Link href="/admin/seva-tickets" className="flex items-center justify-between p-4 rounded-xl border border-gray-50 bg-gray-50 hover:bg-white hover:border-orange-200 hover:shadow-sm transition-all group">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-orange-100 text-orange-600 flex items-center justify-center">
                    <QrCode className="w-5 h-5" />
                  </div>
                  <span className="font-medium text-gray-700">Scan Seva Ticket</span>
                </div>
                <ChevronRight className="w-4 h-4 text-gray-400 group-hover:translate-x-1 transition-transform" />
              </Link>

              <Link href="/admin/donors" className="flex items-center justify-between p-4 rounded-xl border border-gray-50 bg-gray-50 hover:bg-white hover:border-red-200 hover:shadow-sm transition-all group">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-red-100 text-red-600 flex items-center justify-center">
                    <Heart className="w-5 h-5" />
                  </div>
                  <span className="font-medium text-gray-700">Record Donation</span>
                </div>
                <ChevronRight className="w-4 h-4 text-gray-400 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <h2 className="text-lg font-bold text-gray-900 mb-6 flex items-center gap-2">
            <Clock className="w-5 h-5 text-gray-400" />
            Recent Activity
          </h2>
          <div className="space-y-6">
            {dashboardData.activity.length > 0 ? (
              dashboardData.activity.map((activity, i) => {
                const Icon = activity.icon === 'Users' ? Users :
                  activity.icon === 'Ticket' ? Ticket :
                    activity.icon === 'Heart' ? Heart : Calendar;
                return (
                  <div key={i} className="flex gap-4">
                    <div className={`mt-1 w-8 h-8 rounded-full bg-gray-50 ${activity.color} flex items-center justify-center flex-shrink-0`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-800">{activity.text}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{activity.time}</p>
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="text-sm text-gray-400 italic">No recent activity found.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
