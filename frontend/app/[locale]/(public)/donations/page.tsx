import type { Metadata } from 'next'
import { getTranslations } from 'next-intl/server'
import PageContainer from '@/components/PageContainer'
import { Link } from '@/i18n/navigation'
import { localizedAlternates } from '@/lib/site'

export async function generateMetadata(): Promise<Metadata> {
  return { alternates: await localizedAlternates('/donations') }
}

export default async function DonationsComingSoon() {
  const t = await getTranslations('donations')
  return (
    <PageContainer>
      <h1 className="text-4xl font-serif font-semibold text-templeDark">{t('title')}</h1>
      <p className="mt-4 text-gray-700">{t('intro')}</p>

      <div className="mb-12">
        <h2 className="text-2xl font-serif font-semibold text-templeDark mb-6">{t('recordsHeading')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Link href="/donations/archive" className="block p-6 border rounded-lg hover:shadow-md transition bg-white group border-templeGold/20">
            <h3 className="text-xl font-bold text-gray-900 group-hover:text-templeGold transition font-serif">{t('archiveCardTitle')}</h3>
            <p className="text-sm text-gray-500 mt-2">{t('archiveCardSubtitle')}</p>
          </Link>
          <Link href="/donations/old-donors" className="block p-6 border rounded-lg hover:shadow-md transition bg-white group border-templeGold/20">
            <h3 className="text-xl font-bold text-gray-900 group-hover:text-templeGold transition font-serif">{t('oldDonorsCardTitle')}</h3>
            <p className="text-sm text-gray-500 mt-2">{t('oldDonorsCardSubtitle')}</p>
          </Link>
          <Link href="/donations/trustees-history" className="block p-6 border rounded-lg hover:shadow-md transition bg-white group border-templeGold/20">
            <h3 className="text-xl font-bold text-gray-900 group-hover:text-templeGold transition font-serif">{t('trusteesCardTitle')}</h3>
            <p className="text-sm text-gray-500 mt-2">{t('trusteesCardSubtitle')}</p>
          </Link>
        </div>
        <p className="mt-8 italic text-sm text-gray-500 text-center">
          {t('recordsFootnote')}
        </p>
      </div>

      <div className="mt-8 border rounded p-6 bg-gray-50 shadow-inner text-center">
        <p className="text-2xl font-semibold text-gray-700">{t('onlineComingSoonTitle')}</p>
        <p className="mt-3 text-gray-500">{t('onlineComingSoonText')}</p>
        <div className="mt-6 flex justify-center gap-4">
          <button className="bg-white border text-gray-400 px-6 py-2 rounded font-semibold cursor-not-allowed" disabled>
            {t('donateDisabled')}
          </button>
        </div>
      </div>
    </PageContainer>
  )
}
