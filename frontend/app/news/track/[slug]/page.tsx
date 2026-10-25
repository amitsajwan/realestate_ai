import React from 'react'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import { NewsEmpty } from '@/components/news/NewsGrid'
import { TrackerPage } from '@/components/news/Trackers'
import { getMarketingConfig } from '@/lib/marketing/config'
import { articleJsonLd, breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { fetchTracker, trackerDate, trackerPath } from '@/lib/news/trackers'

export const revalidate = 60

type Props = { params: Promise<{ slug: string }> }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params
  const res = await fetchTracker(slug)
  if (!res.ok) return {}
  const t = res.tracker
  // people search "<thing> status": the title says it, the description is today's status with its date
  return pageMetadata(getMarketingConfig(), {
    title: `${t.title}`,
    description: `${t.status} (as of ${trackerDate(t.status_date)})`.slice(0, 300),
    path: trackerPath(t.slug),
  })
}

export default async function TrackerRoute({ params }: Props) {
  const { slug } = await params
  const res = await fetchTracker(slug)
  if (!res.ok && res.notFound) notFound()
  const cfg = getMarketingConfig()
  return (
    <MarketingShell>
      {res.ok ? (
        <>
          <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(articleJsonLd(cfg, {
            title: res.tracker.title, summary: res.tracker.status, path: trackerPath(res.tracker.slug), updated: res.tracker.updated,
          })) }} />
          <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(breadcrumbJsonLd(cfg.siteUrl, [
            { name: 'Home', path: '/' }, { name: 'News', path: '/news' }, { name: res.tracker.name, path: trackerPath(res.tracker.slug) },
          ])) }} />
          <TrackerPage t={res.tracker} />
        </>
      ) : (
        <div className="mx-auto max-w-3xl px-4 py-12"><NewsEmpty failed /></div>
      )}
    </MarketingShell>
  )
}
