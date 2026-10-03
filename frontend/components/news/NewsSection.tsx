import React from 'react'
import Link from 'next/link'
import { fetchNews } from '@/lib/news/data'
import NewsCard from './NewsCard'

/** The latest local news on the landing page (three items, link to /news). Server component; renders nothing when empty. */
export default async function NewsSection() {
  const res = await fetchNews(3)
  if (!res.ok || !res.items.length) return null
  return (
    <section id="news" aria-labelledby="home-news-title" className="scroll-mt-16 bg-slate-50 py-12 sm:py-16">
      <div className="mx-auto max-w-5xl px-4">
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 id="home-news-title" className="text-2xl font-extrabold tracking-tight text-[#0f2340] sm:text-3xl">Kharadi and Wagholi news</h2>
            <p className="mt-2 text-slate-700">Local updates that matter to buyers, each with its source.</p>
          </div>
          <Link href="/news" className="inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-4">All news</Link>
        </div>
        <ul className="mt-6 max-w-3xl list-none rounded-2xl border border-slate-200 bg-white px-4">
          {res.items.slice(0, 3).map((item) => <NewsCard key={item.id} item={item} />)}
        </ul>
      </div>
    </section>
  )
}
