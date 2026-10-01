import React from 'react'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import PostsGrid from '@/components/site/PostsGrid'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { fetchPosts, POSTS_TEXT } from '@/lib/posts/data'

export const revalidate = 60

export const metadata: Metadata = pageMetadata(getMarketingConfig(), {
  title: POSTS_TEXT.pageTitle,
  description: POSTS_TEXT.pageDescription,
  path: '/posts',
})

export default async function PostsPage() {
  const res = await fetchPosts(24)
  return (
    <MarketingShell showInviteCta={false}>
      <section aria-labelledby="posts-page-title" className="py-10 sm:py-14">
        <div className="mx-auto max-w-5xl px-4">
          <h1 id="posts-page-title" className="text-3xl font-extrabold tracking-tight text-[#0f2340] sm:text-4xl">{POSTS_TEXT.heading}</h1>
          <p className="mt-2 text-slate-700">{POSTS_TEXT.lead}</p>
          <div className="mt-8"><PostsGrid posts={res.posts} failed={!res.ok} /></div>
        </div>
      </section>
    </MarketingShell>
  )
}
