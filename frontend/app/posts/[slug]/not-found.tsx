import React from 'react'
import Link from 'next/link'
import MarketingShell from '@/components/marketing/MarketingShell'
import { POSTS_TEXT } from '@/lib/posts/data'

export default function PostNotFound() {
  return (
    <MarketingShell>
      <section className="mx-auto max-w-3xl px-4 py-12">
        <h1 className="text-2xl font-bold text-[#0f2340]">This post is not here</h1>
        <p className="mt-2 text-slate-700">It may have been taken down. Our newest posts are on the posts page.</p>
        <p className="mt-4"><Link href="/posts" className="font-semibold text-[#0f2340] underline underline-offset-4">{POSTS_TEXT.allPosts}</Link></p>
      </section>
    </MarketingShell>
  )
}
