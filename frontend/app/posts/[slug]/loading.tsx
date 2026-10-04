import React from 'react'
import MarketingShell from '@/components/marketing/MarketingShell'

/** One post loading: the shape of the page (title, picture, text), not the list's grid. */
export default function Loading() {
  return (
    <MarketingShell>
      <div className="mx-auto max-w-3xl px-4 py-8 sm:py-12" aria-busy="true" data-testid="post-skeleton">
        <div className="h-4 w-24 rounded bg-slate-200" />
        <div className="mt-6 h-8 w-3/4 rounded bg-slate-200" />
        <div className="mt-6 aspect-[4/5] w-full max-w-md rounded-xl bg-slate-100" />
        <div className="mt-6 space-y-2">
          <div className="h-4 w-full rounded bg-slate-100" />
          <div className="h-4 w-5/6 rounded bg-slate-100" />
        </div>
      </div>
    </MarketingShell>
  )
}
