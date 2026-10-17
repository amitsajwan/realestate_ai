'use client'
import Link from 'next/link'
import React from 'react'
import { api } from '@/lib/app/client'
import { getSiteUrl } from '@/lib/app/session'
import { useAsync } from '@/lib/app/useAsync'

function origin(): string {
  try { return new URL(getSiteUrl() || '').origin } catch { return typeof window !== 'undefined' ? window.location.origin : '' }
}

/** "This week" on the agent's home screen: real counts, the most viewed listing and a message they can share on WhatsApp. Every number opens the screen behind it; the to-dos are rows in Needs you now. */
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
      {text && (
        <a href={`https://wa.me/?text=${encodeURIComponent(text)}`} target="_blank" rel="noopener noreferrer"
          className="flex min-h-[48px] items-center justify-center rounded-xl bg-[#25D366] px-4 font-semibold text-[#053b1a] no-underline">Share my week on WhatsApp</a>
      )}
    </section>
  )
}
