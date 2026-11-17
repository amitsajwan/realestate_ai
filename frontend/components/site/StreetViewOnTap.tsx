'use client'

import React, { useId, useState } from 'react'
import { mapsEmbedKey, pillClass, sendFeature, streetViewSrc } from './mapsEmbed'

/** Google Street View of one spot, on tap (docs/plan/area-pictures.md step 4, "Street View on tap" at a few landmark spots). The
 *  frame is made on the first tap, so a reader who never asks costs no request; Google's pictures are shown from its embed only,
 *  never stored. Nothing at all without the embed key. Give it a position that was checked (a landmark's Google place or
 *  OpenStreetMap), never an area's centre: Street View there shows whatever road is nearest. */
export default function StreetViewOnTap({ lat, lon, label, heading }: { lat: number; lon: number; label: string; heading?: number }) {
  const embedKey = mapsEmbedKey()
  const [open, setOpen] = useState(false)
  const [made, setMade] = useState(false)
  const frameId = useId()
  if (!embedKey) return null
  function toggle() {
    if (!made) {
      setMade(true)
      sendFeature('streetview_open')
    }
    setOpen((o) => !o)
  }
  return (
    <div data-testid="street-view">
      <button type="button" onClick={toggle} aria-expanded={open} aria-controls={frameId} aria-label={`Street View of ${label}`}
        className={pillClass(open)}>
        Street View
      </button>
      <div id={frameId} className={open ? '' : 'hidden'}>
        {made && (
          <iframe title={`Street View of ${label}`} src={streetViewSrc(embedKey, lat, lon, heading)} loading="lazy"
            referrerPolicy="no-referrer-when-downgrade" allowFullScreen data-testid="street-view-frame"
            className="mt-3 h-64 w-full rounded-xl border border-slate-200 sm:h-80" />
        )}
        <p className="mt-2 text-xs text-slate-600">Google Street View. Pictures can be years old.</p>
      </div>
    </div>
  )
}
