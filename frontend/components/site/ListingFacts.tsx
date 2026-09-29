import React from 'react'
import { bhkLabel, floorLabel, formatArea, furnishingLabel, possessionLabel, titleCase } from '@/lib/site/format'
import type { PublicListing } from '@/lib/site/types'

export function listingFacts(l: PublicListing): [string, string][] {
  const rows: [string, string][] = [
    ['Type', bhkLabel(l.bhk, l.property_type)],
    ['Property', l.bhk ? titleCase(l.property_type) : ''],
    ['Carpet area', formatArea(l.carpet_sqft)],
    ['Super built-up', formatArea(l.super_built_up_sqft)],
    ['Floor', floorLabel(l.floor, l.total_floors)],
    ['Furnishing', furnishingLabel(l.furnishing)],
    ['Possession', possessionLabel(l.possession)],
    ['RERA no.', l.rera_no || ''],
  ]
  return rows.filter((r) => r[1])
}

export default function ListingFacts({ listing }: { listing: PublicListing }) {
  const rows = listingFacts(listing)
  return (
    <section aria-labelledby="facts-title">
      <h2 id="facts-title" className="text-lg font-bold">Key facts</h2>
      <dl className="mt-2 grid grid-cols-2 gap-3 sm:grid-cols-3">
        {rows.map(([k, v]) => (
          <div key={k} className="rounded-xl bg-slate-50 p-3">
            <dt className="text-xs uppercase tracking-wide text-slate-500">{k}</dt>
            <dd className="mt-0.5 font-semibold text-slate-900">{v}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}
