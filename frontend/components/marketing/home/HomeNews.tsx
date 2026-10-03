import React from 'react'
import NewsCard from '@/components/news/NewsCard'
import { NewsEmpty } from '@/components/news/NewsGrid'
import { HOME } from '@/lib/marketing/strings'
import type { NewsItem } from '@/lib/news/data'
import SectionHead from './SectionHead'
import { wrap } from './shared'

/** The latest few news notes (same source as /news), each with its source and date; honest when empty or down. */
export default function HomeNews({ items, failed = false }: { items: NewsItem[]; failed?: boolean }) {
  return (
    <section id="news" aria-labelledby="home-news-title" className="scroll-mt-16 py-12 sm:py-16">
      <div className={wrap}>
        <SectionHead id="home-news-title" title={HOME.news.heading} lead={HOME.news.lead} more={{ href: '/news', label: HOME.news.all }} />
        <div className="mt-4">
          {items.length ? (
            <ul className="list-none p-0">{items.map((n) => <NewsCard key={n.id} item={n} />)}</ul>
          ) : (
            <NewsEmpty failed={failed} />
          )}
        </div>
      </div>
    </section>
  )
}
