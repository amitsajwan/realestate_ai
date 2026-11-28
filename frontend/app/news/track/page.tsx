import React from 'react'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import { NewsEmpty } from '@/components/news/NewsGrid'
import { TrackerGrid } from '@/components/news/Trackers'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { fetchTrackers, TRACKER_TEXT, TRACKERS_PATH, trackerPath } from '@/lib/news/trackers'

export const revalidate = 60

export function generateMetadata(): Metadata {
  return pageMetadata(getMarketingConfig(), { title: TRACKER_TEXT.indexTitle, description: TRACKER_TEXT.indexLead, path: TRACKERS_PATH })
}

/** Every tracker, newest change first: the hub the status pages link back to. An outage shows the empty note, never fake rows. */
export default async function TrackersIndex() {
  const cfg = getMarketingConfig()
  const items = await fetchTrackers()
  const list = {
    '@context': 'https://schema.org', '@type': 'ItemList', name: TRACKER_TEXT.indexHeading,
    itemListElement: items.map((t, i) => ({ '@type': 'ListItem', position: i + 1, name: t.name, url: cfg.siteUrl + trackerPath(t.slug) })),
  }
  return (
    <MarketingShell>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(breadcrumbJsonLd(cfg.siteUrl, [
        { name: 'Home', path: '/' }, { name: 'News', path: '/news' }, { name: TRACKER_TEXT.all, path: TRACKERS_PATH },
      ])) }} />
      {items.length > 0 && <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(list) }} />}
      <div className="mx-auto max-w-5xl px-4 py-8 sm:py-12" data-testid="trackers-index">
        <h1 className="text-3xl font-extrabold leading-tight tracking-tight text-[#0f2340] sm:text-4xl">{TRACKER_TEXT.indexHeading}</h1>
        <p className="mt-3 max-w-3xl text-lg leading-relaxed text-slate-700">{TRACKER_TEXT.indexLead}</p>
        <div className="mt-8">{items.length ? <TrackerGrid items={items} /> : <NewsEmpty failed />}</div>
      </div>
    </MarketingShell>
  )
}
