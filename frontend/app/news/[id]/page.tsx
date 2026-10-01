import React from 'react'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import NewsArticle from '@/components/news/NewsArticle'
import { NewsEmpty } from '@/components/news/NewsGrid'
import { getMarketingConfig } from '@/lib/marketing/config'
import { jsonLdString } from '@/lib/marketing/seo'
import { fetchNewsItem } from '@/lib/news/data'
import { newsJsonLd, newsMetadata } from '@/lib/news/seo'

export const revalidate = 60

type Props = { params: Promise<{ id: string }> }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params
  const res = await fetchNewsItem(id)
  return res.ok ? newsMetadata(getMarketingConfig(), res.item) : {}
}

export default async function NewsItemPage({ params }: Props) {
  const { id } = await params
  const res = await fetchNewsItem(id)
  if (!res.ok && res.notFound) notFound()
  const cfg = getMarketingConfig()
  return (
    <MarketingShell showInviteCta={false}>
      {res.ok ? (
        <>
          <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(newsJsonLd(cfg, res.item)) }} />
          <NewsArticle item={res.item} />
        </>
      ) : (
        <div className="mx-auto max-w-3xl px-4 py-12"><NewsEmpty failed /></div>
      )}
    </MarketingShell>
  )
}
