import React from 'react'
import ListingCard from '@/components/site/ListingCard'
import { HOME } from '@/lib/marketing/strings'
import { isSampleListing } from '@/lib/site/format'
import type { PublicListing } from '@/lib/site/types'
import SectionHead from './SectionHead'
import { wrap } from './shared'

/** Agent-site colours that ListingCard reads, set to the Avasetu navy for this surface. */
const CARD_THEME = {
  '--site-primary': '#0f2340', '--site-on-primary': '#ffffff', '--site-secondary': '#0f2340', '--site-on-secondary': '#ffffff',
} as React.CSSProperties

/** Only real homes: anything without an agent page or labelled as a sample is left out, and each home appears once. */
export function realListings(items: PublicListing[]): PublicListing[] {
  const seen = new Set<string>()
  return items.filter((l) => {
    if (!l.agent?.slug || isSampleListing(l.title) || seen.has(l.id)) return false
    seen.add(l.id)
    return true
  })
}

/** Real homes from local agents. Renders nothing when there are none: the page says so in a line instead. */
export default function HomeListings({ items }: { items: PublicListing[] }) {
  const homes = realListings(items)
  if (!homes.length) return null
  return (
    <section id="homes" aria-labelledby="home-homes-title" className="scroll-mt-16 py-12 sm:py-16">
      <div className={wrap}>
        <SectionHead id="home-homes-title" title={HOME.homes.heading} lead={HOME.homes.lead} />
        <ul style={CARD_THEME} className="mt-6 grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3">
          {homes.map((l) => <ListingCard key={l.id} slug={l.agent!.slug} listing={l} />)}
        </ul>
      </div>
    </section>
  )
}
