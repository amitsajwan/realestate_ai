'use client'
import Link from 'next/link'
import React from 'react'
import { formatPrice } from '@/lib/app/format'
import type { Listing } from '@/lib/app/types'
import { StatusChip } from './ui'

export function ListingCard({ listing }: { listing: Listing }) {
  const thumb = listing.media?.[0]?.url
  return (
    <Link
      href={`/studio/listings/${listing.id}`}
      className="flex min-h-[88px] gap-3 rounded-2xl border border-gray-200 bg-white p-3 active:bg-gray-50"
    >
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
    </Link>
  )
}
