import { getTranslations } from 'next-intl/server'
import PageContainer from '@/components/PageContainer'

export default async function HelpDeskPage() {
  const t = await getTranslations('support.helpDesk')
  return (
    <PageContainer>
      <h1 className="text-3xl font-serif font-semibold text-templeDark">{t('title')}</h1>
      <p className="mt-4 text-gray-700">{t('intro')}</p>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">{t('sectionHeading')}</h2>
        <p className="mt-2 text-gray-600">{t('sectionText')}</p>
      </section>
    </PageContainer>
  )
}
