import React from 'react'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import { NewsEmpty } from '@/components/news/NewsGrid'
import { TrackerPage } from '@/components/news/Trackers'
import { getMarketingConfig } from '@/lib/marketing/config'
import { articleJsonLd, breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { fetchTracker, TRACKER_TEXT, TRACKERS_PATH, trackerDate, trackerFaqJsonLd, trackerPath } from '@/lib/news/trackers'

export const revalidate = 60

type Props = { params: Promise<{ slug: string }> }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params
  const res = await fetchTracker(slug)
  if (!res.ok) return {}
  const t = res.tracker
  // people search "<thing> status": the title says it with today's date, the description is the status itself
  return pageMetadata(getMarketingConfig(), {
    title: `${TRACKER_TEXT.h1(t.name)} (${trackerDate(t.status_date)})`,
    description: `${t.status} (as of ${trackerDate(t.status_date)})`.slice(0, 300),
    path: trackerPath(t.slug),
  })
}

export default async function TrackerRoute({ params }: Props) {
  const { slug } = await params
  const res = await fetchTracker(slug)
  if (!res.ok && res.notFound) notFound()
  const cfg = getMarketingConfig()
  const faq = res.ok ? trackerFaqJsonLd(res.tracker) : null
  return (
    <MarketingShell>
      {res.ok ? (
        <>
          {/* dateModified is the day the status line is true from: a new report alone does not change what the page says */}
          <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(articleJsonLd(cfg, {
            title: TRACKER_TEXT.h1(res.tracker.name), summary: res.tracker.status, path: trackerPath(res.tracker.slug), updated: res.tracker.status_date,
          })) }} />
          <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(breadcrumbJsonLd(cfg.siteUrl, [
            { name: 'Home', path: '/' }, { name: 'News', path: '/news' }, { name: TRACKER_TEXT.all, path: TRACKERS_PATH },
            { name: res.tracker.name, path: trackerPath(res.tracker.slug) },
          ])) }} />
          {faq && <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(faq) }} />}
          <TrackerPage t={res.tracker} />
        </>
      ) : (
        <div className="mx-auto max-w-3xl px-4 py-12"><NewsEmpty failed /></div>
      )}
    </MarketingShell>
  )
}
