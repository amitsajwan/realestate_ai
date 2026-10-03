import React from 'react'
import MarketingShell from '@/components/marketing/MarketingShell'
import { PostsSkeleton } from '@/components/site/PostsGrid'
import { POSTS_TEXT } from '@/lib/posts/data'

export default function Loading() {
  return (
    <MarketingShell>
      <section className="py-10 sm:py-14">
        <div className="mx-auto max-w-5xl px-4">
          <h1 className="text-3xl font-extrabold tracking-tight text-[#0f2340] sm:text-4xl">{POSTS_TEXT.heading}</h1>
          <div className="mt-8"><PostsSkeleton count={6} /></div>
        </div>
      </section>
    </MarketingShell>
  )
}
