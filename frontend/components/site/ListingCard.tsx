import React from 'react'
import Link from 'next/link'
import { bhkLabel, formatArea, formatPrice } from '@/lib/site/format'
import { agentPath } from '@/lib/site/slug'
import { firstImage } from '@/lib/site/seo'
import type { PublicListing } from '@/lib/site/types'

export default function ListingCard({ slug, listing: l }: { slug: string; listing: PublicListing }) {
  const image = firstImage(l)
  const facts = [bhkLabel(l.bhk, l.property_type), formatArea(l.carpet_sqft)].filter(Boolean).join(' · ')
  return (
    <li className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <Link href={agentPath(slug, 'listings/' + l.id)} className="block no-underline">
        <div className="relative aspect-[4/3] bg-slate-100">
          {image && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={image} alt={l.title} width={600} height={450} loading="lazy" decoding="async" className="h-full w-full object-cover" />
          )}
          <span className="absolute left-2 top-2 rounded-full bg-[var(--site-secondary)] px-3 py-1 text-xs font-semibold text-[var(--site-on-secondary)]">
            {l.transaction === 'rent' ? 'For rent' : 'For sale'}
          </span>
          {l.status === 'under_offer' && (
            <span className="absolute right-2 top-2 rounded-full bg-amber-400 px-3 py-1 text-xs font-semibold text-slate-900">Under offer</span>
          )}
        </div>
        <div className="p-4">
          <p className="text-xl font-extrabold text-[var(--site-primary)]">{formatPrice(l.price_inr, l.transaction)}</p>
          <h3 className="mt-1 line-clamp-2 text-base font-semibold text-slate-900">{l.title}</h3>
          <p className="mt-1 text-sm text-slate-600">{l.locality}, {l.city}</p>
          {facts && <p className="mt-1 text-sm text-slate-700">{facts}</p>}
        </div>
      </Link>
    </li>
  )
}
