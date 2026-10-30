import React from 'react'
import Link from 'next/link'
import Skyline from '@/components/site/Skyline'
import { BRAND_NAME } from '@/lib/brand'
import { formatArea, formatPrice } from '@/lib/site/format'
import { monthYear } from '@/lib/site/register'
import { bhkRange, bookedShare, matchingHomes, MAX_COMPARE, toSearch, type FinderItem, type FinderQuery } from '@/lib/site/finder'

const bhkText = (b: number | null) => (b == null ? 'Plot' : `${b} BHK`)

/**
 * One project in the finder's results. When the buyer asked a BHK or budget it names the home that fits ("3 BHK · 1,115 sq ft ·
 * ₹1.84 Cr"), not the project's lowest price; otherwise its home types and starting price. Possession, whether the filed date
 * moved and the share booked come from MahaRERA. A partner agent's listing says whose it is ("Listed by House Deal", the line
 * their posts and reels carry); the card still opens our project page, where the enquiry is passed on to them. "Compare" adds it to the comparison in the address (up to three).
 */
export default function FinderCard({ item, q, basePath, anchor = '' }: { item: FinderItem; q: FinderQuery; basePath: string; anchor?: string }) {
  const fit = q.bhk || q.budget ? matchingHomes(item, q) : []
  const from = item.homes.map((h) => h.price).filter((p): p is number => p != null).sort((a, b) => a - b)[0]
  const share = bookedShare(item)
  const comparing = q.compare?.includes(item.id) ?? false
  const full = (q.compare?.length ?? 0) >= MAX_COMPARE
  const compareHref = basePath + toSearch(q, { compare: comparing ? q.compare!.filter((x) => x !== item.id) : [...(q.compare ?? []), item.id] }) + anchor
  return (
    <article className="flex h-full flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm" data-testid="finder-card">
      <Link href={item.href} className="relative block aspect-[4/3] bg-slate-100 no-underline">
        {item.image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={item.image} alt={item.name} loading="lazy" className="h-full w-full object-cover" />
        ) : (
          // no picture yet: a light card with the site's skyline drawing, not a block of colour (owner 2026-10-30)
          <span className="flex h-full w-full flex-col justify-end bg-gradient-to-b from-slate-50 to-slate-100">
            <span className="px-4 pb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">Pictures coming soon</span>
            <Skyline className="block h-20 w-full" tower="#cbd5e1" lit="#f0b440" />
          </span>
        )}
        {item.video && <span className="absolute left-2 top-2 rounded-full bg-black/70 px-2.5 py-1 text-xs font-semibold text-white">▶ Video</span>}
        {/* our own account's listings are just Avasetu's page, so only a partner agent gets the badge (owner 2026-10-30) */}
        {item.listedBy && item.listedBy !== BRAND_NAME && <span className="absolute bottom-2 left-2 rounded-full bg-[var(--site-accent,#f0b440)] px-2.5 py-1 text-xs font-bold text-[var(--site-on-accent,#0f2340)]">Listed by {item.listedBy}</span>}
      </Link>
      <div className="flex flex-1 flex-col gap-1.5 p-4">
        <h3 className="text-lg font-semibold leading-snug text-slate-900">
          <Link href={item.href} className="text-inherit no-underline hover:underline">{item.name}</Link>
        </h3>
        <p className="text-sm text-slate-600">{[item.area, item.builder].filter(Boolean).join(' · ')}</p>
        {fit.length > 0 ? (
          <p className="font-semibold text-[var(--site-primary,#0f2340)]" data-testid="fit">
            {bhkText(fit[0].bhk)}{fit[0].sqft ? ` · ${formatArea(fit[0].sqft)}` : ''}{fit[0].price ? ` · ${formatPrice(fit[0].price)}` : ''}
            {fit.length > 1 && <span className="font-normal text-slate-600"> · {fit.length - 1} more {fit.length === 2 ? 'size' : 'sizes'}</span>}
          </p>
        ) : (
          <p className="font-semibold text-[var(--site-primary,#0f2340)]">{bhkRange(item)}{from ? ` · from ${formatPrice(from)}` : ''}</p>
        )}
        <ul className="mt-1 flex list-none flex-wrap gap-x-3 gap-y-1 p-0 text-sm text-slate-700">
          {item.possession && <li>Possession {monthYear(item.possession)}</li>}
          {item.monthsLater === 0 && <li className="font-semibold text-emerald-700">✓ Date not moved</li>}
          {item.monthsLater != null && item.monthsLater > 0 && <li className="text-amber-800">Moved {item.monthsLater} months</li>}
          {share != null && share > 0 && <li>{Math.round(share * 100)}% booked</li>}
        </ul>
        <div className="mt-auto flex items-center justify-between gap-2 pt-2">
          <Link href={item.href} className="inline-flex min-h-[44px] items-center font-semibold text-[var(--site-primary,#0f2340)] underline underline-offset-2">See prices</Link>
          {(comparing || !full) && (
            <Link href={compareHref} scroll={false} rel="nofollow" aria-pressed={comparing}
              className={'inline-flex min-h-[40px] items-center rounded-full border px-3 text-sm font-semibold no-underline ' +
                (comparing ? 'border-[var(--site-primary,#0f2340)] bg-[var(--site-primary,#0f2340)] text-white' : 'border-slate-300 text-slate-700')}>
              {comparing ? '✓ Comparing' : '+ Compare'}
            </Link>
          )}
        </div>
      </div>
    </article>
  )
}
