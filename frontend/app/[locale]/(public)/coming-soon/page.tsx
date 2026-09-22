'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/navigation';

export default function ComingSoon() {
    const t = useTranslations('comingSoon');
    return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] bg-templeWhite px-4 text-center">
            <div className="bg-white p-8 sm:p-12 rounded-2xl shadow-xl max-w-lg border border-gray-100">
                <div className="text-6xl mb-6">🚩</div>
                <h1 className="text-3xl font-serif font-bold text-templeDark mb-4">
                    {t('title')}
                </h1>
                <p className="text-lg text-gray-600 mb-8 leading-relaxed">
                    {t('text')}
                </p>
                <Link
                    href="/"
                    className="bg-templeGold text-white px-8 py-3 rounded-full font-semibold hover:bg-opacity-90 transition shadow-md inline-block"
                >
                    {t('returnHome')}
                </Link>
            </div>
        </div>
    );
}
