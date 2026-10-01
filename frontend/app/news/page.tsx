import React from 'react'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import NewsGrid from '@/components/news/NewsGrid'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { fetchNews, NEWS_TEXT } from '@/lib/news/data'

export const revalidate = 60

export const metadata: Metadata = pageMetadata(getMarketingConfig(), {
  title: NEWS_TEXT.pageTitle,
  description: NEWS_TEXT.pageDescription,
  path: '/news',
})

export default async function NewsPage() {
  const res = await fetchNews(24)
  return (
    <MarketingShell showInviteCta={false}>
      <section aria-labelledby="news-page-title" className="py-8 sm:py-14">
        <div className="mx-auto max-w-3xl px-4">
          <h1 id="news-page-title" className="text-3xl font-extrabold tracking-tight text-[#0f2340] sm:text-4xl">{NEWS_TEXT.heading}</h1>
          <p className="mt-2 text-slate-700">{NEWS_TEXT.lead}</p>
          <div className="mt-8"><NewsGrid items={res.items} failed={!res.ok} /></div>
          <aside className="mt-10 rounded-2xl border border-[#ead9ae] bg-[#fbf6ea] p-5" aria-labelledby="news-how">
            <h2 id="news-how" className="text-lg font-bold text-[#0f2340]">{NEWS_TEXT.how}</h2>
            <p className="mt-1 text-sm leading-relaxed text-slate-800">{NEWS_TEXT.howLead}</p>
          </aside>
        </div>
      </section>
    </MarketingShell>
  )
}
