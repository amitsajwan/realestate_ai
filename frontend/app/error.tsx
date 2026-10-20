'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { BRAND_NAME, LOGO } from '@/lib/brand'

/** A page that failed (the API busy or restarting, or a bug in the page): in the site's colours, with a retry that reloads the
 *  page and a way out. No shared shell: the shell itself may be what failed. */
export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error('Application Error:', error)
  }, [error])

  return (
    <div data-surface="v2" className="min-h-screen bg-white text-slate-900">
      <header className="border-b border-[#1d3a63] bg-[#0f2340]">
        <div className="mx-auto flex max-w-5xl items-center px-4 py-1.5">
          <Link href="/" className="flex min-h-[44px] items-center gap-2 text-lg font-bold text-white no-underline">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={LOGO.mark} alt="" width={32} height={32} className="h-8 w-8" />
            {BRAND_NAME}
          </Link>
        </div>
      </header>
      <div className="mx-auto max-w-3xl px-4 py-12 sm:py-16">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">This page did not load</h1>
        <p className="mt-4 text-lg leading-relaxed text-slate-700">
          Something went wrong while opening it. Trying again usually works; if it keeps happening, tell us on WhatsApp.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <button type="button" onClick={() => { reset(); window.location.reload() }}
            className="inline-flex min-h-[48px] items-center rounded-xl bg-[#f0b440] px-6 font-bold text-[#0f2340] hover:bg-[#f5c75e]">
            Try again
          </button>
          <Link href="/" className="inline-flex min-h-[48px] items-center rounded-xl border-2 border-[#0f2340] px-6 font-bold text-[#0f2340] no-underline hover:bg-[#0f2340] hover:text-white">
            Home page
          </Link>
        </div>
      </div>
    </div>
  )
}
