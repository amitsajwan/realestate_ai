'use client'
import React from 'react'
import { timeAgo } from '@/lib/app/format'
import type { NewsroomStatus } from '@/lib/app/newsroom'
import { BRAND_NAME } from '@/lib/brand'

const SHOWN: Array<[string, string]> = [
  ['pending_review', 'To review'],
  ['scheduled', 'Scheduled'],
  ['published', 'Published'],
  ['rejected', 'Rejected'],
]

/** Disabled banner, counts, last run and last error in one compact strip. */
export function StatusStrip({ status }: { status: NewsroomStatus }) {
  return (
    <section aria-label="Newsroom status" className="space-y-2">
      {!status.enabled && (
        <p role="alert" className="rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm font-semibold text-amber-900">
          The newsroom is switched off, so no new drafts are being written. Ask your {BRAND_NAME} admin to turn it on.
        </p>
      )}
      {status.last_error && (
        <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-800">
          <span className="font-semibold">The last run had a problem: </span>
          {status.last_error}
        </p>
      )}
      <div className="rounded-2xl bg-blue-900 p-3 text-white">
        <ul className="grid grid-cols-4 gap-1 text-center">
          {SHOWN.map(([key, label]) => (
            <li key={key}>
              <p className="text-xl font-bold text-amber-400" data-testid={`count-${key}`}>{status.counts[key] ?? 0}</p>
              <p className="text-[11px] leading-tight text-blue-100">{label}</p>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-center text-xs text-blue-100">
          {status.enabled ? 'On' : 'Off'} &middot; {status.last_run_at ? `last run ${timeAgo(status.last_run_at)}` : 'has not run yet'}
        </p>
      </div>
    </section>
  )
}
