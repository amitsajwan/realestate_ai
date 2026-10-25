import React from 'react'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import NewsGrid, { NewsEmpty } from '@/components/news/NewsGrid'
import { TrackerGrid } from '@/components/news/Trackers'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { fetchNews, NEWS_TEXT } from '@/lib/news/data'
import { fetchTrackers, TRACKER_TEXT } from '@/lib/news/trackers'

export const revalidate = 60

export const metadata: Metadata = pageMetadata(getMarketingConfig(), {
  title: NEWS_TEXT.pageTitle,
  description: NEWS_TEXT.pageDescription,
  path: '/news',
})

/** The newsroom's front page: the trackers first (where each changing thing stands today), then our full reports. */
export default async function NewsPage() {
  const [res, trackers] = await Promise.all([fetchNews(24), fetchTrackers()])
  return (
    <MarketingShell>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(breadcrumbJsonLd(getMarketingConfig().siteUrl, [
        { name: 'Home', path: '/' }, { name: 'News', path: '/news' },
      ])) }} />
      <section aria-labelledby="news-page-title" className="py-8 sm:py-14">
        <div className="mx-auto max-w-4xl px-4">
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-[#a87a12]">{NEWS_TEXT.kicker}</p>
          <h1 id="news-page-title" className="mt-2 text-3xl font-extrabold tracking-tight text-[#0f2340] sm:text-4xl">{NEWS_TEXT.heading}</h1>
          <p className="mt-2 max-w-2xl text-slate-700">{NEWS_TEXT.lead}</p>

          {trackers.length > 0 && (
            <section aria-labelledby="trackers-h" className="mt-9" data-testid="news-trackers">
              <h2 id="trackers-h" className="text-2xl font-bold tracking-tight text-[#0f2340]">{TRACKER_TEXT.heading}</h2>
              <p className="mt-1 max-w-2xl text-sm text-slate-700">{TRACKER_TEXT.lead}</p>
              <div className="mt-5"><TrackerGrid items={trackers} /></div>
            </section>
          )}

          {res.items.length > 0 ? (
            <section aria-labelledby="reports-h" className="mt-12">
              <h2 id="reports-h" className="text-2xl font-bold tracking-tight text-[#0f2340]">{NEWS_TEXT.reportsHeading}</h2>
              <p className="mt-1 max-w-2xl text-sm text-slate-700">{NEWS_TEXT.reportsLead}</p>
              <div className="mt-5 max-w-3xl"><NewsGrid items={res.items} /></div>
            </section>
          ) : trackers.length === 0 && <div className="mt-8"><NewsEmpty failed={!res.ok} /></div>}

          <aside className="mt-12 max-w-3xl rounded-2xl border border-[#ead9ae] bg-[#fbf6ea] p-5" aria-labelledby="news-how">
            <h2 id="news-how" className="text-lg font-bold text-[#0f2340]">{NEWS_TEXT.how}</h2>
            <p className="mt-1 text-sm leading-relaxed text-slate-800">{NEWS_TEXT.howLead}</p>
          </aside>
        </div>
      </section>
    </MarketingShell>
  )
}
