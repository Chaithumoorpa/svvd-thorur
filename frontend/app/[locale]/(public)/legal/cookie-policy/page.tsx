import type { Metadata } from 'next'
import { getTranslations } from 'next-intl/server'
import PageContainer from '@/components/PageContainer'
import { pageMetadata } from '@/lib/site'

export async function generateMetadata(): Promise<Metadata> {
  return pageMetadata('/legal/cookie-policy');
}

export default async function CookiePolicyPage() {
  const t = await getTranslations('legal.cookiePolicy')
  return (
    <PageContainer>
      <h1 className="text-3xl font-serif font-semibold text-templeDark">{t('title')}</h1>
      <p className="mt-4 text-gray-700">{t('intro')}</p>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">{t('whatWeUseHeading')}</h2>
        <p className="mt-2 text-gray-700">{t('whatWeUseText')}</p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">{t('whyNecessaryHeading')}</h2>
        <p className="mt-2 text-gray-700">{t('whyNecessaryText')}</p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">{t('acceptDeclineHeading')}</h2>
        <p className="mt-2 text-gray-700">{t('acceptDeclineText')}</p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">{t('rightsHeading')}</h2>
        <p className="mt-2 text-gray-700">{t('rightsText')}</p>
      </section>

      <p className="mt-8 text-sm text-gray-500">{t('lastUpdated', { date: '2026-09-30' })}</p>
    </PageContainer>
  )
}
