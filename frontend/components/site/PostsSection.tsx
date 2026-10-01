import React from 'react'
import Link from 'next/link'
import { fetchPosts, POSTS_TEXT } from '@/lib/posts/data'
import PostsGrid from './PostsGrid'

/** 'Latest from PUNE Property' for the landing page. Server component, data cached 60 s. */
export default async function PostsSection() {
  const res = await fetchPosts(3)
  return (
    <section id="posts" aria-labelledby="posts-title" className="scroll-mt-16 bg-white py-12 sm:py-16">
      <div className="mx-auto max-w-5xl px-4">
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 id="posts-title" className="text-2xl font-extrabold tracking-tight text-[#0f2340] sm:text-3xl">{POSTS_TEXT.heading}</h2>
            <p className="mt-2 text-slate-700">{POSTS_TEXT.lead}</p>
          </div>
          {res.posts.length > 0 && (
            <Link href="/posts" className="inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-4">{POSTS_TEXT.all}</Link>
          )}
        </div>
        <div className="mt-6"><PostsGrid posts={res.posts} failed={!res.ok} /></div>
      </div>
    </section>
  )
}
