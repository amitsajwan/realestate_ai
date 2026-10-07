import React from 'react'
import type { Metadata } from 'next'
import { notFound, permanentRedirect } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import NewsArticle from '@/components/news/NewsArticle'
import { NewsEmpty } from '@/components/news/NewsGrid'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString } from '@/lib/marketing/seo'
import { fetchNewsItem, newsPath } from '@/lib/news/data'
import { newsJsonLd, newsMetadata } from '@/lib/news/seo'

export const revalidate = 60

type Props = { params: Promise<{ id: string }> }

/** Next hands the segment over as written in the URL in some versions and decoded in others: compare it decoded. */
const decoded = (id: string): string => { try { return decodeURIComponent(id) } catch { return id } }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params
  const res = await fetchNewsItem(decoded(id))
  return res.ok ? newsMetadata(getMarketingConfig(), res.item) : {}
}

export default async function NewsItemPage({ params }: Props) {
  const { id } = await params
  const res = await fetchNewsItem(decoded(id))
  if (!res.ok && res.notFound) notFound()
  // an older address (the stored id that captions already posted link to, or an older slug): one permanent (308) hop to the current one
  if (res.ok && res.item.id !== decoded(id)) permanentRedirect(newsPath(res.item.id))
  const cfg = getMarketingConfig()
  return (
    <MarketingShell>
      {res.ok ? (
        <>
          <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(newsJsonLd(cfg, res.item)) }} />
          <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(breadcrumbJsonLd(cfg.siteUrl, [
            { name: 'Home', path: '/' }, { name: 'News', path: '/news' }, { name: res.item.headline, path: newsPath(res.item.id) },
          ])) }} />
          <NewsArticle item={res.item} />
        </>
      ) : (
        <div className="mx-auto max-w-3xl px-4 py-12"><NewsEmpty failed /></div>
      )}
    </MarketingShell>
  )
}
