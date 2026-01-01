'use client';
import Link from 'next/link';

export default function ComingSoon() {
    return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] bg-templeWhite px-4 text-center">
            <div className="bg-white p-8 sm:p-12 rounded-2xl shadow-xl max-w-lg border border-gray-100">
                <div className="text-6xl mb-6">🚩</div>
                <h1 className="text-3xl font-serif font-bold text-templeDark mb-4">
                    Coming Soon
                </h1>
                <p className="text-lg text-gray-600 mb-8 leading-relaxed">
                    This feature is currently under development and will be available to devotees very soon.
                    Thank you for your patience and devotion.
                </p>
                <Link
                    href="/"
                    className="bg-templeGold text-white px-8 py-3 rounded-full font-semibold hover:bg-opacity-90 transition shadow-md inline-block"
                >
                    Return to Home
                </Link>
            </div>
        </div>
    );
}
