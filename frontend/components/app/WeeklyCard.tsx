'use client'
import Link from 'next/link'
import React from 'react'
import { api } from '@/lib/app/client'
import { getSiteUrl } from '@/lib/app/session'
import { useAsync } from '@/lib/app/useAsync'

function origin(): string {
  try { return new URL(getSiteUrl() || '').origin } catch { return typeof window !== 'undefined' ? window.location.origin : '' }
}

/** Where each to-do line takes the agent. */
const TODO_HREF: Record<string, string> = {
  photos: '/studio/listings', freshness: '/studio/listings', followup: '/studio/leads?tab=new',
  answer: '/studio/inbox?tab=needs', post: '/studio/listings/new', share: '/studio/listings',
}

/** "This week" on the agent's home screen: real counts, up to four concrete next steps, and a message they can share on WhatsApp. Every number and line opens the screen behind it. */
export function WeeklyCard() {
  const { data } = useAsync(() => api.getWeeklyReport(), [])
  if (!data) return null
  const n = data.numbers
  const stats: Array<[string, number, string]> = [
    ['Views', n.listing_views, '/studio/results'], ['Enquiries', n.new_enquiries, '/studio/leads?tab=all'],
    ['Facebook interest', n.facebook_interest, '/studio/inbox?tab=comments'], ['Website chats', n.chats, '/studio/inbox?tab=buyers'],
  ]
  const text = data.share_text.replace(/\/agent\//, origin() + '/agent/')
  return (
    <section aria-label="This week" className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">This week</h2>
        <span className="text-xs text-gray-500">last {data.period_days} days</span>
      </div>
      <div className="grid grid-cols-4 gap-2 text-center">
        {stats.map(([label, value, href]) => (
          <Link key={label} href={href} className="block rounded-xl bg-gray-50 p-2 no-underline active:bg-gray-100">
            <span className="block text-2xl font-extrabold text-blue-700">{value}</span>
            <span className="block text-[11px] leading-tight text-gray-600">{label}</span>
          </Link>
        ))}
      </div>
      {data.top_listing && (
        <Link href={`/studio/listings/${data.top_listing.listing_id}`} className="block text-sm text-gray-700 no-underline">
          Most viewed: <b className="text-blue-700 underline">{data.top_listing.title}</b> ({data.top_listing.views} views)
        </Link>
      )}
      {data.todo.length > 0 && (
        <ul className="space-y-1 text-sm">
          {data.todo.map((t) => (
            <li key={t.kind}>
              <Link href={TODO_HREF[t.kind] ?? '/studio'} className="flex min-h-[44px] items-center gap-2 rounded-lg bg-amber-50 px-3 py-2 text-amber-900 no-underline active:bg-amber-100">
                <span className="flex-1">{t.text}</span><span aria-hidden="true" className="text-lg">›</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
      {text && (
        <a href={`https://wa.me/?text=${encodeURIComponent(text)}`} target="_blank" rel="noopener noreferrer"
          className="flex min-h-[48px] items-center justify-center rounded-xl bg-[#25D366] px-4 font-semibold text-[#053b1a] no-underline">Share my week on WhatsApp</a>
      )}
    </section>
  )
}
