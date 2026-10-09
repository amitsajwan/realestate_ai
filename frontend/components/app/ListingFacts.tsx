'use client'
import React, { useEffect, useState } from 'react'
import VerifiedFacts from '@/components/site/VerifiedFacts'
import { Spinner } from '@/components/app/ui'
import { API_BASE_URL } from '@/lib/config/api'
import type { Listing, MarketingRun } from '@/lib/app/types'
import type { PropertyFactsView } from '@/lib/site/types'

/** Read-only: the facts Start marketing checked for this listing (MahaRERA, the map, worked-out numbers — the same box
 *  buyers see as "Checked for you") and what the builder's brochure says, labelled as the builder's claims. */
export function ListingFacts({ listing, run }: { listing: Listing; run: MarketingRun | null }) {
  const [facts, setFacts] = useState<PropertyFactsView | null | undefined>(undefined)
  useEffect(() => {
    const p = new URLSearchParams()
    if (listing.rera_no) p.set('rera', listing.rera_no)
    if (listing.project_name) p.set('project', listing.project_name)
    if (listing.locality) p.set('locality', listing.locality)
    if (!listing.rera_no && !listing.project_name) { setFacts(null); return }
    let live = true
    fetch(`${API_BASE_URL.replace(/\/+$/, '')}/api/v1/public/property-facts?${p.toString()}`, { headers: { Accept: 'application/json' } })
      .then((r) => (r.ok ? (r.json() as Promise<PropertyFactsView>) : null))
      .catch(() => null)
      .then((f) => { if (live) setFacts(f) })
    return () => { live = false }
  }, [listing.rera_no, listing.project_name, listing.locality])

  if (facts === undefined) return <Spinner />
  const claims = run?.files?.brochure?.claims ?? []
  const hasFacts = !!facts && !!(facts.maharera || facts.nearby?.length || facts.numbers)
  if (!hasFacts && claims.length === 0) {
    return (
      <p className="rounded-2xl border border-gray-200 bg-white p-4 text-sm text-gray-700">
        Nothing checked yet. Start marketing checks MahaRERA, the map and the numbers for you.
      </p>
    )
  }
  return (
    <div className="space-y-4">
      <VerifiedFacts f={facts ?? null} />
      {claims.length > 0 && (
        <section aria-label="Builder's claims" className="rounded-2xl border border-gray-200 bg-white p-4">
          <h2 className="text-sm font-bold uppercase tracking-wide text-gray-700">Builder&apos;s claims</h2>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
            {claims.map((c) => <li key={c}>{c}</li>)}
          </ul>
          <p className="mt-2 text-xs text-gray-600">From the builder&apos;s brochure. Not checked by us.</p>
        </section>
      )}
    </div>
  )
}
