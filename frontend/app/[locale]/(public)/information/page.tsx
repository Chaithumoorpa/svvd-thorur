import React from 'react';
import { getTranslations } from 'next-intl/server';
import { ShieldCheck, Info, UserCheck } from 'lucide-react';

export default async function InformationPage() {
    const t = await getTranslations('information');
    return (
        <div className="max-w-4xl mx-auto px-4 py-12">
            <h1 className="text-4xl font-bold text-templeDark mb-8">{t('title')}</h1>

            <div className="space-y-12">
                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <UserCheck className="text-templeGold w-6 h-6" />
                        <h2 className="text-2xl font-bold text-templeDark">{t('dressCode.heading')}</h2>
                    </div>
                    <p className="text-gray-600 mb-4">
                        {t('dressCode.intro')}
                    </p>
                    <ul className="grid grid-cols-2 gap-4">
                        <li className="bg-gray-50 p-4 rounded-xl border border-gray-100">
                            <span className="font-bold block mb-1">{t('dressCode.men')}</span>
                            {t('dressCode.menText')}
                        </li>
                        <li className="bg-gray-50 p-4 rounded-xl border border-gray-100">
                            <span className="font-bold block mb-1">{t('dressCode.women')}</span>
                            {t('dressCode.womenText')}
                        </li>
                    </ul>
                </section>

                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <ShieldCheck className="text-templeGold w-6 h-6" />
                        <h2 className="text-2xl font-bold text-templeDark">{t('rules.heading')}</h2>
                    </div>
                    <ul className="space-y-4">
                        <li className="flex gap-3 text-gray-600">
                            <span className="text-templeGold font-bold">•</span>
                            {t('rules.photography')}
                        </li>
                        <li className="flex gap-3 text-gray-600">
                            <span className="text-templeGold font-bold">•</span>
                            {t('rules.phones')}
                        </li>
                        <li className="flex gap-3 text-gray-600">
                            <span className="text-templeGold font-bold">•</span>
                            {t('rules.silence')}
                        </li>
                        <li className="flex gap-3 text-gray-600">
                            <span className="text-templeGold font-bold">•</span>
                            {t('rules.food')}
                        </li>
                    </ul>
                </section>

                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <Info className="text-templeGold w-6 h-6" />
                        <h2 className="text-2xl font-bold text-templeDark">{t('facilities.heading')}</h2>
                    </div>
                    <p className="text-gray-600">
                        {t('facilities.text')}
                    </p>
                </section>
            </div>
        </div>
    );
}
