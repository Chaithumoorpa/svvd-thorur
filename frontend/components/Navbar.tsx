'use client';
import Link from 'next/link';
import Image from 'next/image';

export default function Navbar() {
  return (
    <nav className="sticky top-0 z-50 bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Image src="/logo.png" alt="Temple Logo" width={40} height={40} />
          <span className="text-lg font-serif font-semibold text-templeDark">
            Sri Varasiddhi Vinayaka Swamy
          </span>
        </div>

        <div className="flex gap-6 text-sm font-medium">
          <Link href="/" className="text-templeDark hover:text-templeGold transition">
            Home
          </Link>
          <Link href="/poojas" className="text-templeDark hover:text-templeGold transition">
            Poojas
          </Link>
          <Link href="/festivals" className="text-templeDark hover:text-templeGold transition">
            Festivals
          </Link>
          <Link href="/announcements" className="text-templeDark hover:text-templeGold transition">
            Announcements
          </Link>
          <Link href="/donations" className="text-templeDark hover:text-templeGold transition">
            Donations
          </Link>
        </div>
      </div>
    </nav>
  );
}
