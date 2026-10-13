'use client'
/**
 * SellersCard – "Who else sells this project"
 *
 * Shows four groups of sites that market the same MahaRERA-registered project:
 *   agents   – channel partners and microsites (shown first)
 *   builder  – the promoter's own website
 *   portals  – national / regional listing portals
 *   platform – agents on avasetu.in with a live listing for the same project
 *
 * Agents only: never rendered on a public page (the studio is behind auth).
 */
import React from 'react'
import type { SellerGroups, SellerRow, SellersResult } from '@/lib/app/sellers'
import { fetchSellers } from '@/lib/app/sellers'
import { useAsync } from '@/lib/app/useAsync'
import { Spinner } from '@/components/app/ui'

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function PositionBadge({ position, ad }: { position: number | null; ad: boolean }) {
  if (ad) return <span className="shrink-0 rounded-full bg-amber-100 px-1.5 py-0.5 text-xs font-semibold text-amber-800">Ad</span>
  if (position != null) return <span className="shrink-0 w-6 text-right text-xs font-semibold tabular-nums text-gray-400">#{position}</span>
  return <span className="shrink-0 w-6" aria-hidden />
}

function RowLink({ row }: { row: SellerRow }) {
  return (
    <li className="flex items-start gap-2 py-0.5">
      <PositionBadge position={row.position} ad={row.ad} />
      <a
        href={row.link}
        target="_blank"
        rel="noopener noreferrer"
        className="min-w-0 flex-1 truncate text-sm text-blue-700 underline underline-offset-2 hover:text-blue-900"
        title={row.title || row.site}
      >
        {row.title || row.site}
      </a>
    </li>
  )
}

function Group({ heading, rows }: { heading: string; rows: SellerRow[] }) {
  if (rows.length === 0) return null
  return (
    <div className="space-y-1">
      <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">{heading}</p>
      <ul className="list-none space-y-0.5 p-0">
        {rows.map((r, i) => <RowLink key={`${r.link}${i}`} row={r} />)}
      </ul>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Search-date line
// ---------------------------------------------------------------------------

function SearchDate({ searched_at, query }: { searched_at: string | null; query: string | null }) {
  if (!searched_at) {
    return (
      <p className="text-xs text-gray-400">
        Web search not yet run for this project — results appear within a few days.
      </p>
    )
  }
  const d = new Date(searched_at)
  const label = d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
  return (
    <p className="text-xs text-gray-400">
      Search data from {label}
      {query ? <> · query: <em>&ldquo;{query}&rdquo;</em></> : null}
    </p>
  )
}

// ---------------------------------------------------------------------------
// Main card
// ---------------------------------------------------------------------------

const GROUP_ORDER: Array<{ key: keyof SellerGroups; heading: string }> = [
  { key: 'agents',   heading: 'Agents & channel partners' },
  { key: 'builder',  heading: 'Builder / developer' },
  { key: 'portals',  heading: 'Portals' },
  { key: 'platform', heading: 'On Avasetu' },
]

function SellersBody({ data }: { data: SellersResult }) {
  const { groups, searched_at, query } = data
  const total = GROUP_ORDER.reduce((n, g) => n + groups[g.key].length, 0)
  return (
    <div className="space-y-3">
      <SearchDate searched_at={searched_at} query={query} />
      {total === 0 ? (
        <p className="text-sm text-gray-500">No sellers found in the last search.</p>
      ) : (
        GROUP_ORDER.map(({ key, heading }) => (
          <Group key={key} heading={heading} rows={groups[key]} />
        ))
      )}
      <p className="border-t border-gray-100 pt-2 text-xs text-gray-400">
        Only sellers with a website that ranks on Google for this project&apos;s name are shown.
        MahaRERA publishes no agent list.
      </p>
    </div>
  )
}

export function SellersCard({ listingId }: { listingId: string }) {
  const { data, error, loading } = useAsync(() => fetchSellers(listingId), [listingId])

  return (
    <section
      aria-labelledby="sellers-title"
      className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4"
      data-testid="sellers-card"
    >
      <h2 id="sellers-title" className="text-base font-bold text-gray-900">
        Who else sells this project
      </h2>

      {loading && <Spinner />}

      {!loading && error && (
        error.includes('no_rera') || error.includes('404')
          ? <p className="text-sm text-gray-500">Add a MahaRERA number to this listing to see who else markets it.</p>
          : <p className="text-sm text-red-700">{error}</p>
      )}

      {!loading && data && <SellersBody data={data} />}
    </section>
  )
}
