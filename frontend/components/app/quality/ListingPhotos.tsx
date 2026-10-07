'use client'
import React from 'react'
import { displayUrl } from '@/lib/app/quality'
import type { Media } from '@/lib/app/types'
import { EnhanceToggle, QualityBadge, QualityTip } from './QualityBadge'

/**
 * The listing's photos as buyers will see them, each with its quality badge, a one-line tip and, when an enhanced copy
 * exists, the 'Use enhanced' switch with a before/after peek. Tiny and scrollable on a phone.
 */
export function ListingPhotos({ media, onToggle, busy = false }: { media: Media[]; onToggle?: (index: number, useEnhanced: boolean) => void; busy?: boolean }) {
  if (!media.length) return null
  return (
    <ul className="-mx-1 flex snap-x gap-3 overflow-x-auto px-1 pb-1" data-testid="listing-photos">
      {media.map((m, i) => (
        <li key={m.url + i} className="w-44 flex-none snap-start space-y-1">
          <div className="relative h-28 w-44 overflow-hidden rounded-xl bg-gray-100">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={displayUrl(m)} alt={`Photo ${i + 1}`} className="h-full w-full object-cover" />
            <QualityBadge quality={m.quality} overlay />
          </div>
          <QualityTip quality={m.quality} />
          {m.enhanced_url && onToggle && (
            <fieldset disabled={busy}>
              <EnhanceToggle original={m.url} enhanced={m.enhanced_url} value={!!m.use_enhanced} onChange={(v) => onToggle(i, v)}
                scores={{ before: m.quality?.score, after: m.quality?.enhanced_score }} />
            </fieldset>
          )}
        </li>
      ))}
    </ul>
  )
}
