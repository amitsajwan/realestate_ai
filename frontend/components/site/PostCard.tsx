import React from 'react'
import { formatPostDate, POSTS_TEXT, type PublicPost } from '@/lib/posts/data'
import Skyline from './Skyline'

const LABEL = { facebook: 'Facebook', instagram: 'Instagram' } as const

/** One published post: image, short excerpt, links to the real post on each channel. */
export default function PostCard({ post }: { post: PublicPost }) {
  const date = formatPostDate(post.published_at)
  return (
    <li className="flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm" data-testid="post-card">
      <div className="relative aspect-[4/3] bg-slate-100">
        {post.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={post.image_url} alt={post.title} width={600} height={450} loading="lazy" decoding="async" className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full w-full flex-col justify-end bg-gradient-to-b from-[#102340] to-[#183a5d]" aria-hidden="true">
            <Skyline className="block h-1/2 w-full" />
          </div>
        )}
        {post.sample && (
          <span className="absolute left-2 top-2 rounded-full bg-amber-400 px-3 py-1 text-xs font-bold text-slate-900">{POSTS_TEXT.sampleBadge}</span>
        )}
      </div>
      <div className="flex flex-1 flex-col p-4">
        {date && <p className="text-xs font-medium text-slate-600"><time dateTime={post.published_at}>{date}</time></p>}
        <h3 className="mt-1 line-clamp-2 text-base font-bold text-[#0f2340]">{post.title}</h3>
        {post.excerpt && post.excerpt !== post.title && <p className="mt-1 line-clamp-3 text-sm text-slate-700">{post.excerpt}</p>}
        {post.sample && <p className="mt-2 text-xs text-slate-600">{POSTS_TEXT.sampleNote}</p>}
        <div className="mt-auto flex flex-wrap gap-2 pt-4">
          {post.links.map((l) => (
            <a key={l.channel} href={l.url} target="_blank" rel="noopener noreferrer"
              className="inline-flex min-h-[44px] items-center rounded-full border border-[#0f2340]/40 px-4 text-sm font-semibold text-[#0f2340] no-underline hover:bg-[#0f2340]/5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#0f2340]">
              View on {LABEL[l.channel]}<span className="sr-only"> (opens in a new tab)</span>
            </a>
          ))}
        </div>
      </div>
    </li>
  )
}
