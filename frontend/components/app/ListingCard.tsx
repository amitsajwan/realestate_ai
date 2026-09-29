'use client'
import Link from 'next/link'
import React from 'react'
import { formatPrice } from '@/lib/app/format'
import { t } from '@/lib/app/strings'
import type { Listing, PerformanceItem } from '@/lib/app/types'
import { StatusChip } from './ui'

export function PerformanceRow({ perf }: { perf: PerformanceItem }) {
  const stats: Array<[number, Parameters<typeof t>[0]]> = [
    [perf.views, 'perfViews'],
    [perf.enquiries, 'perfEnquiries'],
    [perf.qualified, 'perfQualified'],
    [perf.site_visits, 'perfVisits'],
  ]
  return (
    <ul className="mt-2 grid grid-cols-4 gap-1 border-t border-gray-100 pt-2" data-testid="performance">
      {stats.map(([n, label]) => (
        <li key={label} className="text-center leading-tight">
          <span className="block text-base font-bold text-gray-900">{n}</span>
          <span className="block text-[11px] text-gray-500">{t(label)}</span>
        </li>
      ))}
    </ul>
  )
}

/** "2 deals · ₹1.7 Cr", only when at least one deal closed on this listing. */
export function DealsLine({ perf }: { perf: PerformanceItem }) {
  const n = perf.deals ?? 0
  if (n <= 0) return null
  const value = perf.deal_value_inr ? formatPrice(perf.deal_value_inr) : ''
  return (
    <p className="mt-1 text-xs font-semibold text-green-800" data-testid="performance-deals">
      {[`${n} ${n === 1 ? t('perfDeal') : t('perfDeals')}`, value].filter(Boolean).join(' · ')}
    </p>
  )
}

export function ListingCard({ listing, performance }: { listing: Listing; performance?: PerformanceItem | null }) {
  const thumb = listing.media?.[0]?.url
  return (
    <Link
      href={`/studio/listings/${listing.id}`}
      className="block min-h-[88px] rounded-2xl border border-gray-200 bg-white p-3 active:bg-gray-50"
    >
      <div className="flex gap-3">
        {thumb ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={thumb} alt="" className="h-20 w-20 flex-none rounded-xl bg-gray-100 object-cover" />
        ) : (
          <div className="flex h-20 w-20 flex-none items-center justify-center rounded-xl bg-gray-100 text-2xl">🏠</div>
        )}
        <div className="min-w-0 flex-1">
          <p className="truncate font-semibold text-gray-900">{listing.title || 'Untitled listing'}</p>
          <p className="truncate text-sm text-gray-500">{[listing.locality, listing.city].filter(Boolean).join(', ')}</p>
          <div className="mt-1 flex items-center gap-2">
            <span className="font-bold text-blue-700">{formatPrice(listing.price_inr, listing.transaction === 'rent') || '-'}</span>
            <StatusChip status={listing.status} />
          </div>
        </div>
      </div>
      {performance && <PerformanceRow perf={performance} />}
      {performance && <DealsLine perf={performance} />}
    </Link>
  )
}
