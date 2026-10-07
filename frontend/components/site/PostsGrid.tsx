import React from 'react'
import { POSTS_TEXT, type PublicPost } from '@/lib/posts/data'
import PostCard from './PostCard'
import SocialStrip from './SocialStrip'

export function PostsSkeleton({ count = 3 }: { count?: number }) {
  return (
    <ul aria-busy="true" aria-label="Loading posts" className="grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3" data-testid="posts-skeleton">
      {Array.from({ length: count }).map((_, i) => (
        <li key={i} className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
          <div className="aspect-[4/3] animate-pulse bg-slate-200" />
          <div className="space-y-2 p-4">
            <div className="h-3 w-1/4 animate-pulse rounded bg-slate-200" />
            <div className="h-4 w-3/4 animate-pulse rounded bg-slate-200" />
            <div className="h-3 w-full animate-pulse rounded bg-slate-100" />
            <div className="h-11 w-1/2 animate-pulse rounded-full bg-slate-100" />
          </div>
        </li>
      ))}
    </ul>
  )
}

/** Honest empty / error state: no placeholder posts, just where to follow us. */
export function PostsEmpty({ failed = false }: { failed?: boolean }) {
  return (
    <div role="status" className="rounded-2xl border border-dashed border-[#d9c48f] bg-[#fbf6ea] p-6 text-center" data-testid="posts-empty">
      <p className="text-lg font-bold text-[#0f2340]">{failed ? POSTS_TEXT.error : POSTS_TEXT.empty}</p>
      <p className="mx-auto mt-1 max-w-md text-sm text-slate-700">{failed ? POSTS_TEXT.errorLead : POSTS_TEXT.emptyLead}</p>
      <SocialStrip className="mt-4 justify-center" />
    </div>
  )
}

export default function PostsGrid({ posts, failed = false }: { posts: PublicPost[]; failed?: boolean }) {
  if (!posts.length) return <PostsEmpty failed={failed} />
  return (
    <ul className="grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3">
      {posts.map((p) => <PostCard key={p.id} post={p} />)}
    </ul>
  )
}
