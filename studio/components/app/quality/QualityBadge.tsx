'use client'
import React, { useState } from 'react'
import { badgeFor } from '@/lib/app/quality'
import type { PhotoQuality } from '@/lib/app/quality'

/** A tiny 'Good' / 'Check: too dark' pill. `overlay` places it on top of a thumbnail. */
export function QualityBadge({ quality, overlay = false }: { quality: Pick<PhotoQuality, 'issues'> | null | undefined; overlay?: boolean }) {
  const b = badgeFor(quality)
  if (!b) return null
  const tone = b.tone === 'good' ? 'bg-green-600/90 text-white' : 'bg-amber-400/95 text-amber-950'
  return (
    <span
      data-testid="quality-badge"
      className={`inline-block max-w-full truncate rounded-full px-2 py-0.5 text-[11px] font-semibold leading-4 ${tone} ${overlay ? 'absolute bottom-1 left-1 right-1 w-fit' : ''}`}
    >
      {b.text}
    </span>
  )
}

/** The one-line tip under a photo that needs a retake ('Take it again with lights on'). Nothing for a good photo. */
export function QualityTip({ quality, label }: { quality: Pick<PhotoQuality, 'issues'> | null | undefined; label?: string }) {
  const b = badgeFor(quality)
  if (!b?.tip) return null
  return (
    <p data-testid="quality-tip" className="text-xs text-amber-900">
      {label ? <span className="font-semibold">{label}: </span> : null}
      {b.tip}
    </p>
  )
}

/**
 * 'Use enhanced' switch with a before/after peek. The enhanced copy only changes light, colour, straightness and sharpness;
 * the original is always kept, so switching back is free.
 */
export function EnhanceToggle({ original, enhanced, value, onChange, label = 'Use enhanced', scores }: {
  original: string
  enhanced: string
  value: boolean
  onChange: (v: boolean) => void
  label?: string
  scores?: { before?: number | null; after?: number | null }
}) {
  const [peek, setPeek] = useState(false)
  return (
    <div className="space-y-1" data-testid="enhance-toggle">
      <div className="flex items-center gap-2 text-xs">
        <label className="flex min-h-[36px] items-center gap-2 font-semibold text-gray-800">
          <input type="checkbox" role="switch" aria-checked={value} checked={value} onChange={(e) => onChange(e.target.checked)} className="h-4 w-4" />
          {label}
        </label>
        <button type="button" onClick={() => setPeek((p) => !p)} aria-expanded={peek} className="min-h-[36px] text-blue-700 underline">
          {peek ? 'Hide' : 'Before / after'}
        </button>
      </div>
      {peek && (
        <div className="grid grid-cols-2 gap-1" data-testid="before-after">
          {[{ src: original, cap: 'Before', s: scores?.before }, { src: enhanced, cap: 'After', s: scores?.after }].map((x) => (
            <figure key={x.cap} className="space-y-0.5">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={x.src} alt={`${x.cap} enhancement`} className="aspect-[4/3] w-full rounded-lg bg-gray-100 object-cover" />
              <figcaption className="text-[11px] text-gray-600">{x.cap}{typeof x.s === 'number' ? ` · ${x.s}/100` : ''}</figcaption>
            </figure>
          ))}
          <p className="col-span-2 text-[11px] text-gray-500">Only light, colour and straightness change. Nothing in the photo is added or removed.</p>
        </div>
      )}
    </div>
  )
}
