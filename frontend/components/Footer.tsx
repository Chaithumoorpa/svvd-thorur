'use client';
import Link from 'next/link';
import { useState, useEffect } from 'react';
import { getVisitorStats, VisitorStats } from '@/lib/api';

export default function Footer() {
  const currentYear = new Date().getFullYear();
  const [stats, setStats] = useState<VisitorStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getVisitorStats()
      .then((data) => {
        setStats(data);
        setLoading(false);
      })
      .catch((err) => {
        // eslint-disable-next-line no-console
        console.error('Failed to fetch visitor stats:', err);
        setLoading(false);
      });
  }, []);

  function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  return (
    <footer className="bg-templeDark text-gray-100">
      {/* Newsletter Strip */}
      <div className="bg-templeGold py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <span className="text-templeDark font-semibold">Subscribe to our Newsletter</span>
          <div className="flex w-full sm:w-auto">
            <input
              type="email"
              placeholder="Enter your email"
              className="flex-1 sm:flex-none px-4 py-2 rounded-l text-templeDark placeholder-templeDark/60 focus:outline-none"
              disabled
            />
            <button
              className="bg-templeDark text-templeGold px-4 py-2 rounded-r font-semibold hover:bg-templeDark/80 transition"
              disabled
            >
              ↓
            </button>
          </div>
        </div>
      </div>

      {/* Main Footer Content Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-7 gap-8">
          {/* Column 1: About Temple */}
          <div>
            <h3 className="text-lg font-semibold text-templeGold mb-4">About Temple</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/about" className="hover:text-templeGold transition">
                  Overview
                </Link>
              </li>
              <li>
                <Link href="/history" className="hover:text-templeGold transition">
                  History
                </Link>
              </li>
              <li>
                <Link href="/timings" className="hover:text-templeGold transition">
                  Temple Timings
                </Link>
              </li>
              <li>
                <Link href="/information" className="hover:text-templeGold transition">
                  General Information
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 2: Sevas & Poojas */}
          <div>
            <h3 className="text-lg font-semibold text-templeGold mb-4">Sevas & Poojas</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/poojas" className="hover:text-templeGold transition">
                  Daily Poojas
                </Link>
              </li>
              <li>
                <Link href="/coming-soon" className="hover:text-templeGold transition text-gray-400">
                  Special Sevas
                </Link>
              </li>
              <li>
                <Link href="/festivals" className="hover:text-templeGold transition">
                  Festival Sevas
                </Link>
              </li>
              <li>
                <Link href="/coming-soon" className="hover:text-templeGold transition">
                  Booking Information
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 3: Donations */}
          <div>
            <h3 className="text-lg font-semibold text-templeGold mb-4">Donations</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/coming-soon" className="hover:text-templeGold transition text-gray-400">
                  Donation Overview
                </Link>
              </li>
              <li>
                <Link href="/coming-soon" className="hover:text-templeGold transition text-gray-400">
                  Online Donations
                </Link>
              </li>
              <li>
                <Link href="/coming-soon" className="hover:text-templeGold transition">
                  Annadanam
                </Link>
              </li>
              <li>
                <Link href="/contact" className="hover:text-templeGold transition">
                  Trust Information
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 4: Visitor Information */}
          <div>
            <h3 className="text-lg font-semibold text-templeGold mb-4">Visitor Info</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/timings" className="hover:text-templeGold transition">
                  Darshan Information
                </Link>
              </li>
              <li>
                <Link href="/contact" className="hover:text-templeGold transition">
                  Facilities
                </Link>
              </li>
              <li>
                <Link href="/information" className="hover:text-templeGold transition">
                  Rules & Guidelines
                </Link>
              </li>
              <li>
                <Link href="/coming-soon" className="hover:text-templeGold transition text-gray-400">
                  FAQs
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 5: Media & Updates */}
          <div>
            <h3 className="text-lg font-semibold text-templeGold mb-4">Media & Updates</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/announcements" className="hover:text-templeGold transition">
                  Announcements
                </Link>
              </li>
              <li>
                <Link href="/gallery" className="hover:text-templeGold transition">
                  Gallery
                </Link>
              </li>
              <li>
                <Link href="/gallery" className="hover:text-templeGold transition">
                  Events
                </Link>
              </li>
              <li>
                <Link href="/announcements" className="hover:text-templeGold transition">
                  News & Updates
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 6: Support */}
          <div>
            <h3 className="text-lg font-semibold text-templeGold mb-4">Support</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/contact" className="hover:text-templeGold transition">
                  Contact Us
                </Link>
              </li>
              <li>
                <Link href="/contact" className="hover:text-templeGold transition">
                  Help Desk
                </Link>
              </li>
              <li>
                <Link href="/contact" className="hover:text-templeGold transition">
                  Feedback
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 7: Legal */}
          <div>
            <h3 className="text-lg font-semibold text-templeGold mb-4">Legal</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/privacy-policy" className="hover:text-templeGold transition">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" className="hover:text-templeGold transition">
                  Terms & Conditions
                </Link>
              </li>
              <li>
                <Link href="/terms" className="hover:text-templeGold transition">
                  Refund Policy
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Contact & Maps Section */}
      <div className="border-t border-gray-700 py-12">
        <div className="max-w-6xl mx-auto px-4 grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Contact Info */}
          <div>
            <h3 className="text-lg font-semibold text-templeGold mb-6">Contact & Location</h3>
            <div className="space-y-4">
              <div className="flex gap-3">
                <span className="text-templeGold text-xl">📍</span>
                <div>
                  <p className="font-semibold">Sri Varasiddhi Vinayaka Swamy Temple</p>
                  <p className="text-sm text-gray-400">Thorur Village, Andhra Pradesh, India</p>
                </div>
              </div>
              <div className="flex gap-3">
                <span className="text-templeGold text-xl">📞</span>
                <div>
                  <p className="text-sm">Phone: +91-XXXXXXXXXX</p>
                </div>
              </div>
              <div className="flex gap-3">
                <span className="text-templeGold text-xl">📧</span>
                <div>
                  <p className="text-sm">Email: info@svvdthorur.org</p>
                </div>
              </div>
            </div>
          </div>

          {/* Maps */}
          <div>
            <h3 className="text-lg font-semibold text-templeGold mb-6">Location Map</h3>
            <div className="rounded-lg overflow-hidden shadow-lg">
              <iframe
                src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d881002.5788503479!2d79.21050739825243!3d13.641851241157436!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3a4d5bc04479e687%3A0x9365d686a757f596!2ssri%20vinayaka%20temple!5e0!3m2!1sen!2sin!4v1766833981047!5m2!1sen!2sin"
                width="100%"
                height="250"
                style={{ border: 0 }}
                allowFullScreen
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
              ></iframe>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-gray-700 py-6">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm">
          <p className="text-gray-400">
            © {currentYear} Sri Varasiddhi Vinayaka Swamy Temple. All rights reserved.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 sm:gap-6">
            <div className="flex items-center gap-2">
              <span className="text-gray-400">Today:</span>
              <span className="text-templeGold font-semibold">
                {loading ? '...' : stats?.today_visitors.toLocaleString() || '0'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-400">Total Visitors:</span>
              <span className="text-templeGold font-semibold">
                {loading ? '...' : stats?.total_visitors.toLocaleString() || '0'}
              </span>
            </div>
            <button
              onClick={scrollToTop}
              className="bg-templeGold text-templeDark px-3 py-1 rounded font-semibold hover:bg-templeGold/80 transition\"
              aria-label="Scroll to top"
            >
              ↑
            </button>
          </div>
        </div>
      </div>
    </footer>
  );
}
