import React from 'react'
import Link from 'next/link'

export const metadata = { title: 'Page not found', robots: { index: false } }

/** A Studio address that does not exist (an old link, a deleted listing): back to Studio home, or to the public site. */
export default function NotFound() {
  return (
    <div className="mx-auto max-w-md px-4 py-12">
      <p className="text-sm font-semibold uppercase tracking-wide text-[#a87a1c]">Page not found</p>
      <h1 className="mt-2 text-2xl font-bold text-slate-900">This page has moved or no longer exists</h1>
      <p className="mt-6 flex flex-wrap gap-3">
        <Link href="/studio" className="inline-flex min-h-[48px] items-center rounded-xl bg-[#0f2340] px-6 font-bold text-white no-underline">Studio home</Link>
        <a href="/" className="inline-flex min-h-[48px] items-center rounded-xl border-2 border-[#0f2340] px-6 font-bold text-[#0f2340] no-underline">The public site</a>
      </p>
    </div>
  )
}
