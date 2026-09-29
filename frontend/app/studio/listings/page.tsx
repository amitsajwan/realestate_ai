'use client'
import React from 'react'
import { ListingCard } from '@/components/app/ListingCard'
import { ErrorBox, LinkBtn, PageTitle, Spinner } from '@/components/app/ui'
import { api } from '@/lib/app/client'
import { t } from '@/lib/app/strings'
import type { PerformanceItem } from '@/lib/app/types'
import { useAsync } from '@/lib/app/useAsync'

export default function ListingsPage() {
  const { data, error, loading, reload } = useAsync(async () => {
    // Performance is a nice-to-have: the list still shows if it cannot be loaded.
    const [listings, perf] = await Promise.all([api.listListings(), api.getPerformance().catch(() => [] as PerformanceItem[])])
    return { listings, perf: new Map((perf ?? []).map((p) => [p.listing_id, p])) }
  })
  return (
    <div className="space-y-3">
      <PageTitle>{t('listings')}</PageTitle>
      <LinkBtn href="/studio/listings/new">{t('addListing')}</LinkBtn>
      {loading && !data && <Spinner />}
      {error && <ErrorBox message={error} onRetry={reload} />}
      {data && data.listings.length === 0 && <p className="py-8 text-center text-gray-500">{t('noListings')}</p>}
      {data?.listings.map((l) => <ListingCard key={l.id} listing={l} performance={data.perf.get(l.id)} />)}
    </div>
  )
}
