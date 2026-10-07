import React from 'react'
import { NEWS_TEXT, type NewsItem } from '@/lib/news/data'
import SocialStrip from '@/components/site/SocialStrip'
import NewsCard from './NewsCard'

export function NewsSkeleton({ count = 4 }: { count?: number }) {
  return (
    <ul aria-busy="true" aria-label="Loading news" className="list-none space-y-4 p-0" data-testid="news-skeleton">
      {Array.from({ length: count }).map((_, i) => (
        <li key={i} className="flex gap-4 border-t border-slate-200 py-5 first:border-t-0">
          <div className="flex-1 space-y-2">
            <div className="h-4 w-1/3 animate-pulse rounded-full bg-slate-200" />
            <div className="h-5 w-11/12 animate-pulse rounded bg-slate-200" />
            <div className="h-3 w-full animate-pulse rounded bg-slate-100" />
          </div>
          <div className="h-24 w-24 animate-pulse rounded-xl bg-slate-200" />
        </li>
      ))}
    </ul>
  )
}

/** Honest empty and error states: no placeholder stories, just where to follow us. */
export function NewsEmpty({ failed = false }: { failed?: boolean }) {
  return (
    <div role="status" className="rounded-2xl border border-dashed border-[#d9c48f] bg-[#fbf6ea] p-6 text-center" data-testid="news-empty">
      <p className="text-lg font-bold text-[#0f2340]">{failed ? NEWS_TEXT.error : NEWS_TEXT.empty}</p>
      <p className="mx-auto mt-1 max-w-md text-sm text-slate-700">{failed ? NEWS_TEXT.errorLead : NEWS_TEXT.emptyLead}</p>
      <SocialStrip className="mt-4 justify-center" />
    </div>
  )
}

export default function NewsGrid({ items, failed = false }: { items: NewsItem[]; failed?: boolean }) {
  if (!items.length) return <NewsEmpty failed={failed} />
  const [lead, ...rest] = items
  return (
    <ol className="list-none space-y-6 p-0">
      <NewsCard item={lead} featured />
      {rest.length > 0 && <li className="list-none"><ul className="list-none p-0">{rest.map((n) => <NewsCard key={n.id} item={n} />)}</ul></li>}
    </ol>
  )
}
