'use client'
import React from 'react'
import { FreshnessSection } from '@/components/app/FreshnessPrompt'
import { ListingCard } from '@/components/app/ListingCard'
import { ErrorBox, LinkBtn, PageTitle, Spinner } from '@/components/app/ui'
import { api } from '@/lib/app/client'
import { t } from '@/lib/app/strings'
import type { Listing, PerformanceItem } from '@/lib/app/types'
import { useAsync } from '@/lib/app/useAsync'

export default function ListingsPage() {
  const { data, error, loading, reload, setData } = useAsync(async () => {
    // Performance is a nice-to-have: the list still shows if it cannot be loaded.
    const [listings, perf] = await Promise.all([api.listListings(), api.getPerformance().catch(() => [] as PerformanceItem[])])
    return { listings, perf: new Map((perf ?? []).map((p) => [p.listing_id, p])) }
  })
  // Arriving from the home "Listings that need your confirmation" card: the list loads after the page, so scroll once it is there.
  const loaded = !!data
  React.useEffect(() => {
    if (loaded && typeof window !== 'undefined' && window.location.hash === '#confirm') {
      document.getElementById('confirm')?.scrollIntoView?.({ block: 'start' })
    }
  }, [loaded])
  // After "still available?" / sold / paused the server returns the listing: swap it in so its card and chip update.
  const replace = (updated: Listing) =>
    setData((d) => (d ? { ...d, listings: d.listings.map((l) => (l.id === updated.id ? updated : l)) } : d))
  return (
    <div className="space-y-3">
      <PageTitle>{t('listings')}</PageTitle>
      <LinkBtn href="/studio/listings/new">{t('addListing')}</LinkBtn>
      {loading && !data && <Spinner />}
      {error && <ErrorBox message={error} onRetry={reload} />}
      {data && <FreshnessSection listings={data.listings} onUpdated={replace} />}
      {data && data.listings.length === 0 && <p className="py-8 text-center text-gray-500">{t('noListings')}</p>}
      {data?.listings.map((l) => <ListingCard key={l.id} listing={l} performance={data.perf.get(l.id)} />)}
    </div>
  )
}
