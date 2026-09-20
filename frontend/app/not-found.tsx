import Link from 'next/link';
import Ornament from '@/components/public/Ornament';

export default function NotFound() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center bg-cream px-4 py-24 text-center">
      <p className="font-serif text-6xl font-bold text-saffron">404</p>
      <Ornament className="my-4" />
      <h1 className="font-serif text-2xl font-bold text-maroon">This page could not be found</h1>
      <p className="mt-2 max-w-md text-gray-600">The page may have moved. You can return to the home page or browse the timings and poojas.</p>
      <div className="mt-6 flex flex-wrap justify-center gap-3">
        <Link href="/" className="rounded-full bg-maroon px-6 py-2 font-semibold text-white hover:bg-maroon-dark">Home</Link>
        <Link href="/timings" className="rounded-full border border-maroon px-6 py-2 font-semibold text-maroon hover:bg-amber-50">Timings</Link>
      </div>
    </main>
  );
}
