import React from 'react'
import Link from 'next/link'
import { formatNewsDate, NEWS_TEXT, type NewsItem } from '@/lib/news/data'
import { policyDisclaimer } from '@/lib/news/disclaimer'
import InterestStrip from './InterestStrip'
import { TEAM } from '@/lib/brand'

const CHANNEL = { facebook: 'Facebook', instagram: 'Instagram' } as const

/** The detail view of one news item: headline, our summary, our labelled view, what to check, the source (as a named link, never a bare URL),
 *  the standing disclaimer and the interest strip. */
export default function NewsArticle({ item }: { item: NewsItem }) {
  const date = formatNewsDate(item.as_of)
  const digest = item.kind === 'digest'
  return (
    <article data-testid="news-article" className="mx-auto max-w-3xl px-4 py-8 sm:py-12">
      <p className="text-sm"><Link href="/news" className="text-[#0f2340] underline underline-offset-2">{NEWS_TEXT.all}</Link></p>
      <p className="mt-4 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
        <span className="rounded-full bg-[#f0b440] px-2.5 py-1 font-bold uppercase tracking-wide text-[#0f2340]">News &middot; {item.pillar_label}</span>
        {item.areas.map((a) => <Link key={a.slug} href={`/localities/${a.slug}`} className="font-semibold uppercase tracking-wide text-slate-700 underline-offset-2 hover:underline">{a.name}</Link>)}
      </p>
      <h1 className="mt-3 text-3xl font-extrabold leading-tight tracking-tight text-[#0f2340] sm:text-4xl">{item.headline}</h1>
      <p className="mt-3 text-sm text-slate-700">
        By the {TEAM}{date && <> &middot; {NEWS_TEXT.asOf} <time dateTime={item.as_of ?? undefined}>{date}</time></>}
      </p>
      {!digest && <p className="mt-1 text-sm font-medium text-slate-600" data-testid="summary-badge">{NEWS_TEXT.badge}{item.source_name && <> by {item.source_name}</>}</p>}

      {item.image_url && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={item.image_url} alt={item.headline} width={720} height={720} decoding="async" className="mt-6 aspect-square w-full rounded-2xl border border-slate-200 object-cover" />
      )}

      {digest ? (
        <section className="mt-8" aria-labelledby="digest-h">
          <h2 id="digest-h" className="text-xl font-bold text-[#0f2340]">{NEWS_TEXT.digestHeading}</h2>
          <ul className="mt-3 list-none space-y-3 p-0">
            {item.items.map((i) => (
              <li key={i.id} className="rounded-xl border border-slate-200 bg-white p-4">
                <Link href={`/news/${i.id}`} className="font-bold text-[#0f2340] underline-offset-2 hover:underline">{i.headline}</Link>
                {i.source_name && <p className="mt-1 text-xs text-slate-600">Source: {i.source_name}</p>}
              </li>
            ))}
          </ul>
          {item.tip && (
            <div className="mt-6 rounded-xl border-l-4 border-[#f0b440] bg-[#fbf6ea] p-4">
              <p className="text-sm font-bold uppercase tracking-wide text-[#0f2340]">{NEWS_TEXT.tipHeading}</p>
              <p className="mt-1 text-slate-800">{item.tip}</p>
            </div>
          )}
        </section>
      ) : (
        <>
          <p className="mt-8 text-lg leading-relaxed text-slate-900" data-testid="news-summary">{item.summary}</p>
          <p className="mt-2 text-xs text-slate-600">{NEWS_TEXT.summaryNote}</p>

          {item.our_view && (
            <section className="mt-6 rounded-xl bg-slate-50 p-4" data-testid="news-our-view" aria-labelledby="view-h">
              <h2 id="view-h" className="text-sm font-bold uppercase tracking-wide text-slate-700">{NEWS_TEXT.ourView}</h2>
              <p className="mt-1 text-slate-800">{item.our_view}</p>
              <p className="mt-1 text-xs text-slate-600">{NEWS_TEXT.ourViewNote}</p>
            </section>
          )}

          {item.what_to_check && (
            <section className="mt-6 rounded-xl border-l-4 border-[#f0b440] bg-[#fbf6ea] p-4" data-testid="what-to-check" aria-labelledby="check-h">
              <h2 id="check-h" className="text-sm font-bold uppercase tracking-wide text-[#0f2340]">{NEWS_TEXT.weCheck}</h2>
              <p className="mt-1 text-slate-900">{item.what_to_check}</p>
            </section>
          )}

          <section className="mt-6 border-t border-slate-200 pt-5" aria-labelledby="source-h">
            <h2 id="source-h" className="text-lg font-semibold text-slate-900">Source</h2>
            <p className="mt-1 text-sm text-slate-700">{item.source_name || 'The source'}{date && <>, {NEWS_TEXT.asOf} {date}</>}</p>
            {item.source_url && (
              <a href={item.source_url} target="_blank" rel="noopener noreferrer nofollow" data-testid="read-original"
                className="mt-2 inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-4">
                {NEWS_TEXT.readOriginal(item.source_name)}<span className="sr-only"> (opens in a new tab)</span>
              </a>
            )}
          </section>
        </>
      )}

      {item.permalinks.length > 0 && (
        <p className="mt-4 flex flex-wrap gap-3 text-sm">
          {item.permalinks.map((l) => (
            <a key={l.channel} href={l.url} target="_blank" rel="noopener noreferrer" className="inline-flex min-h-[44px] items-center text-slate-700 underline underline-offset-4">
              Also on {CHANNEL[l.channel]}<span className="sr-only"> (opens in a new tab)</span>
            </a>
          ))}
        </p>
      )}

      <p data-testid="news-disclaimer" className="mt-8 rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-700">{item.disclaimer || policyDisclaimer}</p>
      <InterestStrip areas={item.areas} />
    </article>
  )
}
