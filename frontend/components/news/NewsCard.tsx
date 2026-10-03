import React from 'react'
import Link from 'next/link'
import { formatNewsDate, NEWS_TEXT, type NewsItem } from '@/lib/news/data'
import BuyerLine from './BuyerLine'

function Meta({ item }: { item: NewsItem }) {
  const date = formatNewsDate(item.as_of)
  return (
    <p className="mt-2 text-xs font-medium text-slate-600">
      {item.kind === 'digest' ? 'Our weekly roundup' : <>Source: {item.source_name}</>}
      {date && <> &middot; {NEWS_TEXT.asOf} <time dateTime={item.as_of ?? undefined}>{date}</time></>}
    </p>
  )
}

function Kicker({ item }: { item: NewsItem }) {
  return (
    <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
      <span className="rounded-full bg-[#f0b440] px-2.5 py-1 font-bold uppercase tracking-wide text-[#0f2340]">News &middot; {item.pillar_label}</span>
      {item.areas.length > 0 && <span className="font-semibold uppercase tracking-wide text-slate-600">{item.areas.map((a) => a.name).join(' · ')}</span>}
    </p>
  )
}

/** One news item. `featured` is the lead story (big image); the others are compact rows with a small card thumbnail. */
export default function NewsCard({ item, featured = false }: { item: NewsItem; featured?: boolean }) {
  const href = `/news/${item.id}`
  const img = item.image_url && (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={item.image_url} alt="" width={featured ? 720 : 112} height={featured ? 720 : 112} loading={featured ? 'eager' : 'lazy'} decoding="async"
      className={featured ? 'aspect-square w-full rounded-2xl object-cover' : 'aspect-square w-24 flex-none rounded-xl object-cover sm:w-28'} />
  )
  if (featured) {
    return (
      <li data-testid="news-card" className="list-none overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm sm:grid sm:grid-cols-2 sm:items-stretch">
        {img && <Link href={href} tabIndex={-1} aria-hidden="true" className="block sm:order-2">{img}</Link>}
        <div className="flex flex-col justify-center p-5 sm:p-7">
          <Kicker item={item} />
          <h2 className="mt-3 text-2xl font-extrabold leading-tight tracking-tight text-[#0f2340] sm:text-3xl">
            <Link href={href} className="text-[#0f2340] no-underline hover:underline">{item.headline}</Link>
          </h2>
          {item.summary && item.kind !== 'digest' && <p className="mt-3 line-clamp-3 leading-relaxed text-slate-800">{item.summary}</p>}
          <BuyerLine line={item.buyer_line} />
          <Meta item={item} />
        </div>
      </li>
    )
  }
  return (
    <li data-testid="news-card" className="flex list-none items-start gap-4 border-t border-slate-200 py-5 first:border-t-0">
      <div className="min-w-0 flex-1">
        <Kicker item={item} />
        <h3 className="mt-2 text-lg font-bold leading-snug text-[#0f2340]">
          <Link href={href} className="text-[#0f2340] no-underline hover:underline">{item.headline}</Link>
        </h3>
        {item.summary && item.kind !== 'digest' && <p className="mt-1 line-clamp-2 text-sm text-slate-700">{item.summary}</p>}
        <BuyerLine line={item.buyer_line} compact />
        <Meta item={item} />
      </div>
      {img && <Link href={href} tabIndex={-1} aria-hidden="true">{img}</Link>}
    </li>
  )
}
