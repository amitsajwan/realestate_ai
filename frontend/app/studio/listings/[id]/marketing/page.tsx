'use client'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import React from 'react'
import { MarketingRunCard } from '@/components/app/MarketingRunCard'
import { ErrorBox, LinkBtn, Spinner } from '@/components/app/ui'
import { api } from '@/lib/app/client'
import { t } from '@/lib/app/strings'
import { useAsync } from '@/lib/app/useAsync'

/** Marketing comes after the listing: a draft is posted from the listing page first. */
export default function ListingMarketingPage() {
  const { id } = useParams<{ id: string }>()
  const { data, error, loading, reload } = useAsync(() => api.getListing(id), [id])

  if (loading && !data) return <Spinner />
  if (error || !data) return <ErrorBox message={error ?? t('notFound')} onRetry={reload} />
  const live = data.status === 'live' || data.status === 'under_offer'

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Link href={`/studio/listings/${id}`} className="flex min-h-[44px] min-w-[44px] items-center text-xl" aria-label={t('back')}>←</Link>
        <div className="min-w-0 flex-1">
          <h1 className="text-xl font-bold">{t('marketingTitle')}</h1>
          <p className="truncate text-sm text-gray-600">{data.title}</p>
        </div>
      </div>
      {live ? (
        <MarketingRunCard listingId={id} />
      ) : data.status === 'draft' ? (
        <div className="space-y-2 rounded-xl bg-amber-50 p-3">
          <p className="text-sm text-amber-900">This property is not on your website yet. Post the listing first, then start its marketing here.</p>
          <LinkBtn href={`/studio/listings/${id}?tab=status`}>Post the listing</LinkBtn>
        </div>
      ) : (
        <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900">This property is not live, so it cannot be marketed now.</p>
      )}
    </div>
  )
}
