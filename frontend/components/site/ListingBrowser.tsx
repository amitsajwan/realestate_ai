'use client'

import React, { useMemo, useState } from 'react'
import type { PublicListing } from '@/lib/site/types'
import ListingCard from './ListingCard'

type Tx = 'all' | 'sale' | 'rent'

export function filterListings(items: PublicListing[], tx: Tx, bhk: number | 'all'): PublicListing[] {
  return items.filter((l) => {
    if (tx !== 'all' && l.transaction !== tx) return false
    if (bhk === 'all') return true
    if (bhk >= 4) return !!l.bhk && l.bhk >= 4
    return !!l.bhk && Math.floor(l.bhk) === bhk
  })
}

const chip = (on: boolean) =>
  'min-h-[44px] rounded-full border px-4 text-sm font-semibold transition ' +
  (on ? 'border-[var(--site-primary)] bg-[var(--site-primary)] text-[var(--site-on-primary)]' : 'border-slate-300 bg-white text-slate-700')

export default function ListingBrowser({ slug, items }: { slug: string; items: PublicListing[] }) {
  const [tx, setTx] = useState<Tx>('all')
  const [bhk, setBhk] = useState<number | 'all'>('all')
  const shown = useMemo(() => filterListings(items, tx, bhk), [items, tx, bhk])

  if (items.length === 0) {
    return <p className="rounded-xl bg-slate-50 p-6 text-center text-slate-600">New properties are coming soon. Message us on WhatsApp to hear first.</p>
  }
  return (
    <div>
      <div className="mb-4 space-y-2" role="group" aria-label="Filter properties">
        <div className="flex flex-wrap gap-2">
          {([['all', 'All'], ['sale', 'Buy'], ['rent', 'Rent']] as [Tx, string][]).map(([v, label]) => (
            <button key={v} type="button" aria-pressed={tx === v} onClick={() => setTx(v)} className={chip(tx === v)}>{label}</button>
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          {([['all', 'Any BHK'], [1, '1 BHK'], [2, '2 BHK'], [3, '3 BHK'], [4, '4+ BHK']] as [number | 'all', string][]).map(([v, label]) => (
            <button key={String(v)} type="button" aria-pressed={bhk === v} onClick={() => setBhk(v)} className={chip(bhk === v)}>{label}</button>
          ))}
        </div>
      </div>
      <p className="sr-only" role="status" aria-live="polite">{shown.length} properties shown</p>
      {shown.length === 0 ? (
        <p className="rounded-xl bg-slate-50 p-6 text-center text-slate-600">No properties match these filters.</p>
      ) : (
        <ul className="grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3">
          {shown.map((l) => <ListingCard key={l.id} slug={slug} listing={l} />)}
        </ul>
      )}
    </div>
  )
}
