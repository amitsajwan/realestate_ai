import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound, permanentRedirect } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import SlideStrip from '@/components/site/SlideStrip'
import { getMarketingConfig } from '@/lib/marketing/config'
import { LOCALITIES } from '@/lib/marketing/localities'
import { breadcrumbJsonLd, jsonLdString } from '@/lib/marketing/seo'
import { fetchPost, formatPostDate, postPath, POSTS_TEXT } from '@/lib/posts/data'
import { postJsonLd, postMetadata } from '@/lib/posts/seo'
import { postParagraphs, projectPath, withoutTitle } from '@/lib/posts/text'

export const revalidate = 60

type Props = { params: Promise<{ slug: string }> }

const LABEL = { facebook: 'Facebook', instagram: 'Instagram' } as const

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params
  const res = await fetchPost(slug)
  return res.ok ? postMetadata(getMarketingConfig(), res.post) : {}
}

export default async function PostPage({ params }: Props) {
  const { slug } = await params
  const res = await fetchPost(slug)
  if (!res.ok && res.notFound) notFound()
  if (res.ok && res.post.slug !== slug) permanentRedirect(postPath(res.post.slug)) // an older address of the same post
  const cfg = getMarketingConfig()
  if (!res.ok) {
    return (
      <MarketingShell>
        <section className="mx-auto max-w-3xl px-4 py-12" role="status">
          <h1 className="text-2xl font-bold text-[#0f2340]">{POSTS_TEXT.failed}</h1>
          <p className="mt-2 text-slate-700">{POSTS_TEXT.failedLead}</p>
          <p className="mt-4"><Link href="/posts" className="font-semibold text-[#0f2340] underline underline-offset-4">{POSTS_TEXT.allPosts}</Link></p>
        </section>
      </MarketingShell>
    )
  }
  const post = res.post
  const area = post.area ? LOCALITIES.find((l) => l.key === post.area) : undefined
  const project = projectPath(post.site_url, cfg.siteUrl)
  const date = formatPostDate(post.published_at)
  const slides = (post.images.length ? post.images : post.image_url ? [post.image_url] : [])
    .map((url, i, all) => ({ url, alt: all.length > 1 ? `${post.title} (slide ${i + 1} of ${all.length})` : post.title }))
  const paragraphs = postParagraphs(withoutTitle(post.text, post.title), cfg.siteUrl)
  return (
    <MarketingShell>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(postJsonLd(cfg, post, area?.name)) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(breadcrumbJsonLd(cfg.siteUrl, [
        { name: 'Home', path: '/' }, { name: 'Posts', path: '/posts' }, { name: post.title, path: postPath(post.slug) },
      ])) }} />
      <article className="mx-auto max-w-3xl px-4 py-8 sm:py-12" data-testid="post-page">
        <nav aria-label="Breadcrumb" className="text-sm text-slate-600">
          <Link href="/posts" className="font-semibold text-[#0f2340] underline underline-offset-4">{POSTS_TEXT.allPosts}</Link>
          {area && <> · <Link href={`/localities/${area.slug}`} className="underline underline-offset-4">{area.name}</Link></>}
        </nav>
        <header className="mt-4">
          {post.kind === 'reel' && <span className="inline-block rounded-full bg-black/80 px-3 py-1 text-xs font-bold text-white">{POSTS_TEXT.reel}</span>}
          {post.sample && <span className="inline-block rounded-full bg-amber-400 px-3 py-1 text-xs font-bold text-slate-900">{POSTS_TEXT.sampleBadge}</span>}
          <h1 className="mt-2 break-words text-2xl font-extrabold tracking-tight text-[#0f2340] sm:text-3xl">{post.title}</h1>
          {date && <p className="mt-2 text-sm text-slate-600">{POSTS_TEXT.postedOn} <time dateTime={post.published_at}>{date}</time></p>}
        </header>

        {slides.length > 1 ? (
          <SlideStrip slides={slides} label={post.title} className="mt-6" />
        ) : slides.length === 1 ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={slides[0].url} alt={slides[0].alt} width={1080} height={1350} decoding="async"
            className="mt-6 aspect-[4/5] h-auto w-full max-w-md rounded-xl border border-slate-200 bg-slate-100 object-cover" />
        ) : null}

        {paragraphs.length > 0 && (
          <div className="mt-6 space-y-4 break-words text-base leading-relaxed text-slate-800" data-testid="post-text">
            {paragraphs.map((p, i) => (
              <p key={i}>
                {p.map((pieces, j) => (
                  <React.Fragment key={j}>
                    {j > 0 && <br />}
                    {pieces.map((x, k) => ('href' in x
                      ? <Link key={k} href={x.href} className="font-semibold text-[#0f2340] underline underline-offset-4">{x.text}</Link>
                      : <React.Fragment key={k}>{x.text}</React.Fragment>))}
                  </React.Fragment>
                ))}
              </p>
            ))}
          </div>
        )}
        {post.sample && <p className="mt-4 text-sm text-slate-600">{POSTS_TEXT.sampleNote}</p>}

        <div className="mt-8 flex flex-wrap items-center gap-3">
          {project && (
            <Link href={project} data-testid="post-project-link"
              className="inline-flex min-h-[44px] items-center rounded-full bg-[#0f2340] px-5 text-sm font-bold text-white no-underline hover:bg-[#183a5d]">
              {POSTS_TEXT.seeProject}
            </Link>
          )}
          {post.links.map((l) => (
            <a key={l.channel} href={l.url} target="_blank" rel="noopener noreferrer"
              className="inline-flex min-h-[44px] items-center rounded-full border border-[#0f2340]/40 px-4 text-sm font-semibold text-[#0f2340] no-underline hover:bg-[#0f2340]/5">
              {(post.kind === 'reel' ? POSTS_TEXT.watchOn : POSTS_TEXT.viewOn)(LABEL[l.channel])}<span className="sr-only"> (opens in a new tab)</span>
            </a>
          ))}
        </div>

        {area && (
          <p className="mt-8 border-t border-slate-200 pt-6">
            <Link href={`/localities/${area.slug}`} data-testid="post-area-link"
              className="text-base font-bold text-[#0f2340] underline underline-offset-4">
              {POSTS_TEXT.moreAbout(area.name)}
            </Link>
          </p>
        )}
      </article>
    </MarketingShell>
  )
}
