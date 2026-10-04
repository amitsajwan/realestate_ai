import React from 'react'
import Link from 'next/link'
import { type AreaNews, type AreaPost, feedDate, newsPath, postPath } from './areaFeed'

const KIND_LABEL: Record<AreaPost['kind'], string> = { post: 'Post', showcase: 'Home', reel: 'Reel' }

/** "Latest from <Area>": our posts and news stories about this area, each linking to its own page. Each list is left out when
 *  empty; with neither, the whole block renders nothing. */
export default function AreaLatest({ name, posts, news }: { name: string; posts: AreaPost[]; news: AreaNews[] }) {
  if (!posts.length && !news.length) return null
  return (
    <section className="mt-9" aria-labelledby="latest-title">
      <h2 id="latest-title" className="text-xl font-semibold text-slate-900">Latest from {name}</h2>

      {posts.length > 0 && (
        <div className="mt-4" role="group" aria-labelledby="latest-posts-title">
          <h3 id="latest-posts-title" className="font-semibold text-slate-900">Our posts about {name}</h3>
          <ul className="mt-2 list-none space-y-3 p-0">
            {posts.map((p) => (
              <li key={p.slug} className="min-w-0 rounded-xl border border-slate-200 p-3">
                <Link href={postPath(p.slug)} className="break-words font-semibold text-[#0f2340] underline underline-offset-2">{p.title}</Link>
                {p.excerpt && <span className="mt-1 line-clamp-2 break-words text-sm leading-relaxed text-slate-700">{p.excerpt}</span>}
                <span className="mt-1 block text-sm text-slate-600">{[KIND_LABEL[p.kind], feedDate(p.published_at)].filter(Boolean).join(' · ')}</span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-sm"><Link href="/posts" className="font-semibold text-[#0f2340] underline underline-offset-2">All posts</Link></p>
        </div>
      )}

      {news.length > 0 && (
        <div className="mt-5" role="group" aria-labelledby="latest-news-title">
          <h3 id="latest-news-title" className="font-semibold text-slate-900">News about {name}</h3>
          <ul className="mt-2 list-none space-y-3 p-0">
            {news.map((n) => (
              <li key={n.id} className="min-w-0 rounded-xl border border-slate-200 p-3">
                <Link href={newsPath(n.id)} className="break-words font-semibold text-[#0f2340] underline underline-offset-2">{n.headline}</Link>
                {n.summary && <span className="mt-1 line-clamp-2 break-words text-sm leading-relaxed text-slate-700">{n.summary}</span>}
                {(n.source_name || feedDate(n.published_at)) && (
                  <span className="mt-1 block break-words text-sm text-slate-600">
                    {[n.source_name && `Source: ${n.source_name}`, feedDate(n.published_at)].filter(Boolean).join(' · ')}
                  </span>
                )}
              </li>
            ))}
          </ul>
          <p className="mt-3 text-sm"><Link href="/news" className="font-semibold text-[#0f2340] underline underline-offset-2">All local news</Link></p>
        </div>
      )}
    </section>
  )
}
