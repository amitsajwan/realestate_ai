import React from 'react'
import { formatPostDate, POSTS_TEXT, type PublicPost } from '@/lib/posts/data'
import Skyline from './Skyline'
import SlideStrip from './SlideStrip'

const LABEL = { facebook: 'Facebook', instagram: 'Instagram' } as const

/**
 * One published post, close to how it reads on Instagram: every carousel slide (swipe), the caption's opening line as the
 * title, the rest as a short excerpt; the main link goes to the page on our own site, Facebook and Instagram are small links.
 */
export default function PostCard({ post }: { post: PublicPost }) {
  const date = formatPostDate(post.published_at)
  const slides = (post.images.length ? post.images : post.image_url ? [post.image_url] : [])
    .map((url, i, all) => ({ url, alt: all.length > 1 ? `${post.title} (slide ${i + 1} of ${all.length})` : post.title }))
  return (
    <li className="flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm" data-testid="post-card">
      <div className="relative">
        {slides.length > 1 ? (
          <SlideStrip slides={slides} label={post.title} size="sm" className="p-3 pb-0" />
        ) : slides.length === 1 ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={slides[0].url} alt={slides[0].alt} width={1080} height={1350} loading="lazy" decoding="async"
            className="aspect-[4/5] w-full bg-slate-100 object-cover" />
        ) : (
          <div className="flex aspect-[4/3] w-full flex-col justify-end bg-gradient-to-b from-[#102340] to-[#183a5d]" aria-hidden="true">
            <Skyline className="block h-1/2 w-full" />
          </div>
        )}
        {post.sample && (
          <span className="absolute left-2 top-2 rounded-full bg-amber-400 px-3 py-1 text-xs font-bold text-slate-900">{POSTS_TEXT.sampleBadge}</span>
        )}
        {post.kind === 'reel' && (
          <span className="absolute left-5 top-5 rounded-full bg-black/70 px-3 py-1 text-xs font-bold text-white">Reel</span>
        )}
      </div>
      <div className="flex flex-1 flex-col p-4">
        {date && <p className="text-xs font-medium text-slate-600"><time dateTime={post.published_at}>{date}</time></p>}
        <h3 className="mt-1 line-clamp-2 text-base font-bold text-[#0f2340]">{post.title}</h3>
        {post.excerpt && post.excerpt !== post.title && <p className="mt-1 line-clamp-3 text-sm text-slate-700">{post.excerpt}</p>}
        {post.sample && <p className="mt-2 text-xs text-slate-600">{POSTS_TEXT.sampleNote}</p>}
        <div className="mt-auto flex flex-wrap items-center gap-x-4 gap-y-2 pt-4">
          {post.site_url && (
            <a href={post.site_url} data-testid="post-site-link"
              className="inline-flex min-h-[44px] items-center rounded-full bg-[#0f2340] px-5 text-sm font-bold text-white no-underline hover:bg-[#183a5d] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#0f2340]">
              See the project
            </a>
          )}
          {post.links.map((l) => (
            <a key={l.channel} href={l.url} target="_blank" rel="noopener noreferrer"
              className={post.site_url
                ? 'inline-flex min-h-[44px] items-center text-sm font-semibold text-[#0f2340] underline underline-offset-4'
                : 'inline-flex min-h-[44px] items-center rounded-full border border-[#0f2340]/40 px-4 text-sm font-semibold text-[#0f2340] no-underline hover:bg-[#0f2340]/5'}>
              {post.site_url ? LABEL[l.channel] : 'View on ' + LABEL[l.channel]}<span className="sr-only"> (opens in a new tab)</span>
            </a>
          ))}
        </div>
      </div>
    </li>
  )
}
