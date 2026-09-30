'use client'
import React from 'react'
import { api } from '@/lib/app/client'
import { getSiteUrl } from '@/lib/app/session'
import { useAsync } from '@/lib/app/useAsync'

function origin(): string {
  try { return new URL(getSiteUrl() || '').origin } catch { return typeof window !== 'undefined' ? window.location.origin : '' }
}

/** "This week" on the agent's home screen: real counts, up to four concrete next steps, and a message they can share on WhatsApp. */
export function WeeklyCard() {
  const { data } = useAsync(() => api.getWeeklyReport(), [])
  if (!data) return null
  const n = data.numbers
  const stats: Array<[string, number]> = [['Views', n.listing_views], ['Enquiries', n.new_enquiries], ['Facebook interest', n.facebook_interest], ['Website chats', n.chats]]
  const text = data.share_text.replace(/\/agent\//, origin() + '/agent/')
  return (
    <section aria-label="This week" className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">This week</h2>
        <span className="text-xs text-gray-500">last {data.period_days} days</span>
      </div>
      <dl className="grid grid-cols-4 gap-2 text-center">
        {stats.map(([label, value]) => (
          <div key={label} className="rounded-xl bg-gray-50 p-2">
            <dd className="text-2xl font-extrabold text-blue-700">{value}</dd>
            <dt className="text-[11px] leading-tight text-gray-600">{label}</dt>
          </div>
        ))}
      </dl>
      {data.top_listing && <p className="text-sm text-gray-700">Most viewed: <b>{data.top_listing.title}</b> ({data.top_listing.views} views)</p>}
      {data.todo.length > 0 && (
        <ul className="space-y-1 text-sm">
          {data.todo.map((t) => <li key={t.kind} className="rounded-lg bg-amber-50 px-3 py-2 text-amber-900">{t.text}</li>)}
        </ul>
      )}
      {text && (
        <a href={`https://wa.me/?text=${encodeURIComponent(text)}`} target="_blank" rel="noopener noreferrer"
          className="flex min-h-[48px] items-center justify-center rounded-xl bg-[#25D366] px-4 font-semibold text-[#053b1a] no-underline">Share my week on WhatsApp</a>
      )}
    </section>
  )
}
