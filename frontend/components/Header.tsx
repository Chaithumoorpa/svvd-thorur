'use client';
import Link from 'next/link';
import Image from 'next/image';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Header() {
  const router = useRouter();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [dateTime, setDateTime] = useState({ date: '', time: '' });
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    // Auth Check
    const storedUser = localStorage.getItem('user');
    const token = localStorage.getItem('token');
    if (storedUser && token) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        localStorage.removeItem('user');
        localStorage.removeItem('token');
      }
    }

    const currentDate = new Date().toLocaleDateString('en-IN', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });

    const currentTime = new Date().toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });

    setDateTime({ date: currentDate, time: currentTime });
  }, []);

  const handleAuthClick = () => {
    if (!user) {
      router.push('/login');
      return;
    }

    if (['ADMIN', 'SUPER_ADMIN', 'TRUSTEE'].includes(user.role)) {
      router.push('/admin/dashboard');
    } else {
      router.push('/profile');
    }
  };

  return (
    <header className="bg-white">
      {/* ROW 1: Top Utility Bar */}
      <div className="bg-red-900 text-white text-sm">
        <div className="max-w-6xl mx-auto px-4 py-2 flex items-center justify-between">
          <div>
            {dateTime.date ? `${dateTime.date} | ${dateTime.time}` : 'Loading...'}
          </div>
          <div className="flex items-center gap-4">
            <div className="flex gap-3">
              <a href="#" className="hover:text-yellow-400 transition" aria-label="Facebook">
                f
              </a>
              <a href="#" className="hover:text-yellow-400 transition" aria-label="Instagram">
                📷
              </a>
              <a href="#" className="hover:text-yellow-400 transition" aria-label="YouTube">
                ▶
              </a>
            </div>
            <div className="border-l border-red-700 pl-4">
              <select className="bg-red-900 text-white text-xs border-none focus:outline-none">
                <option>English</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* ROW 2: Main Header */}
      <div className="bg-yellow-500">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          {/* Logo & Temple Name */}
          <Link href="/" className="flex items-center gap-4 hover:opacity-90 transition">
            <div className="w-12 h-12 flex-shrink-0">
              <Image src="/logo.png" alt="Temple Logo" width={48} height={48} />
            </div>
            <div className="hidden sm:block text-left">
              <h1 className="text-lg font-serif font-bold text-red-900 leading-tight">
                Sri Varasiddhi Vinayaka Swamy Temple
              </h1>
              <p className="text-xs text-red-800">Thorur</p>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex gap-6 text-sm font-medium text-red-900">
            <Link href="/" className="hover:text-red-700 transition">
              Home
            </Link>
            <Link href="/poojas" className="hover:text-red-700 transition">
              Poojas
            </Link>
            <Link href="/festivals" className="hover:text-red-700 transition">
              Festivals
            </Link>
            <Link href="/announcements" className="hover:text-red-700 transition">
              Announcements
            </Link>
          </nav>

          {/* Mobile Menu Toggle */}
          <button
            className="md:hidden text-red-900 font-bold text-xl"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            aria-label="Toggle menu"
          >
            ☰
          </button>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden bg-yellow-400 border-t border-yellow-600">
            <nav className="flex flex-col gap-3 p-4 text-sm font-medium text-red-900">
              <Link href="/" onClick={() => setIsMobileMenuOpen(false)} className="hover:text-red-700 transition">
                Home
              </Link>
              <Link href="/poojas" onClick={() => setIsMobileMenuOpen(false)} className="hover:text-red-700 transition">
                Poojas
              </Link>
              <Link href="/festivals" onClick={() => setIsMobileMenuOpen(false)} className="hover:text-red-700 transition">
                Festivals
              </Link>
              <Link href="/announcements" onClick={() => setIsMobileMenuOpen(false)} className="hover:text-red-700 transition">
                Announcements
              </Link>
              <div className="border-t border-yellow-600 pt-3 flex gap-2">
                <button
                  onClick={() => { setIsMobileMenuOpen(false); handleAuthClick(); }}
                  className="flex-1 bg-white text-red-900 px-3 py-2 rounded font-semibold hover:bg-gray-100 transition"
                >
                  {user ? 'Dashboard' : 'Sign In'}
                </button>
                {!user && (
                  <button
                    onClick={() => { setIsMobileMenuOpen(false); router.push('/signup'); }}
                    className="flex-1 bg-red-900 text-white px-3 py-2 rounded font-semibold hover:bg-red-800 transition"
                  >
                    Sign Up
                  </button>
                )}
              </div>
            </nav>
          </div>
        )}
      </div>

      {/* ROW 3: Auth & Actions Bar */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-3 flex justify-end gap-3">
          <button
            onClick={handleAuthClick}
            className="bg-white text-red-900 px-6 py-2 rounded border-2 border-red-900 font-semibold hover:bg-red-50 transition"
          >
            {user ? 'Dashboard' : 'Sign In'}
          </button>
          {!user && (
            <button
              onClick={() => router.push('/signup')}
              className="bg-red-900 text-white px-6 py-2 rounded font-semibold hover:bg-red-800 transition"
            >
              Sign Up
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
