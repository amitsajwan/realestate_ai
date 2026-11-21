'use client'

import React from 'react'
import Link from 'next/link'
import { comparePath, shortlistPath, writePicks } from '@/lib/site/picks'
import { usePicks } from './PickButtons'

/** The strip under the header once a project is picked to compare or saved: "Compare now" and "Shortlist", so a buyer who picks
 *  on one page finds the list on the next. Not fixed to the bottom: phones already have the chat bubble and the project page's
 *  call bar there. Nothing renders with both lists empty. */
export default function PicksBar() {
  const compare = usePicks('compare')
  const saved = usePicks('saved')
  if (!compare.length && !saved.length) return null
  return (
    <div data-print="hide" className="border-b border-amber-200 bg-amber-50 px-4 py-1" data-testid="picks-bar">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-2 text-sm">
        <span className="text-slate-700">
          {compare.length > 0 && <>{compare.length} to compare</>}
          {compare.length > 0 && saved.length > 0 && ' · '}
          {saved.length > 0 && <>{saved.length} saved</>}
        </span>
        <div className="flex flex-wrap gap-2">
          {compare.length > 0 && (
            <button type="button" onClick={() => writePicks('compare', [])} className="inline-flex min-h-[44px] items-center px-2 text-slate-600 underline underline-offset-2">
              Clear
            </button>
          )}
          {saved.length > 0 && (
            <Link href={shortlistPath(saved)} className="inline-flex min-h-[44px] items-center rounded-xl border border-[#0f2340] px-4 font-semibold text-[#0f2340] no-underline" data-testid="picks-shortlist">
              Shortlist ({saved.length})
            </Link>
          )}
          {compare.length > 1 ? (
            <Link href={comparePath(compare)} className="inline-flex min-h-[44px] items-center rounded-xl bg-[#0f2340] px-4 font-semibold text-white no-underline" data-testid="picks-compare">
              Compare now ({compare.length})
            </Link>
          ) : compare.length === 1 ? (
            <span className="inline-flex min-h-[44px] items-center px-2 text-slate-600">Pick one more to compare</span>
          ) : null}
        </div>
      </div>
    </div>
  )
}
