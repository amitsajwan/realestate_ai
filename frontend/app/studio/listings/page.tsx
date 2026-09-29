'use client'
import React from 'react'
import { ListingCard } from '@/components/app/ListingCard'
import { ErrorBox, LinkBtn, PageTitle, Spinner } from '@/components/app/ui'
import { api } from '@/lib/app/client'
import { t } from '@/lib/app/strings'
import { useAsync } from '@/lib/app/useAsync'

export default function ListingsPage() {
  const { data, error, loading, reload } = useAsync(() => api.listListings())
  return (
    <div className="space-y-3">
      <PageTitle>{t('listings')}</PageTitle>
      <LinkBtn href="/studio/listings/new">{t('addListing')}</LinkBtn>
      {loading && !data && <Spinner />}
      {error && <ErrorBox message={error} onRetry={reload} />}
      {data && data.length === 0 && <p className="py-8 text-center text-gray-500">{t('noListings')}</p>}
      {data?.map((l) => <ListingCard key={l.id} listing={l} />)}
    </div>
  )
}
