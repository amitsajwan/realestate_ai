'use client'

import React, { useState } from 'react'
import { AREA_CENTRES } from '@/lib/site/areaCentres'
import { mapsEmbedKey, pillClass, satelliteSrc, sendFeature } from './mapsEmbed'

/** "<area> from above" on an area guide without a drawn street map (docs/plan/area-pictures.md step 2): one button that opens
 *  Google's satellite view at the area's hand-set centre (lib/site/areaCentres.ts). The frame is made on the first tap, so the
 *  page sends Google nothing until the reader asks. Nothing at all without the embed key or a centre for the area. */
export default function AreaFromAbove({ slug, name, className = 'mt-9' }: { slug: string; name: string; className?: string }) {
  const embedKey = mapsEmbedKey()
  const at = AREA_CENTRES[slug]
  const [open, setOpen] = useState(false)
  const [made, setMade] = useState(false)
  if (!embedKey || !at) return null
  const frameId = `from-above-${slug}`
  function toggle() {
    if (!made) {
      setMade(true)
      sendFeature('satellite_open')
    }
    setOpen((o) => !o)
  }
  return (
    <section className={className} aria-labelledby={`${frameId}-title`} data-testid="area-from-above">
      <h2 id={`${frameId}-title`} className="text-xl font-semibold text-slate-900">{name} from above</h2>
      <button type="button" onClick={toggle} aria-expanded={open} aria-controls={frameId} className={'mt-3 ' + pillClass(open)}>
        {open ? 'Hide the satellite view' : 'Show the satellite view'}
      </button>
      <div id={frameId} className={open ? '' : 'hidden'}>
        {made && (
          <iframe title={`Satellite view of ${name}`} src={satelliteSrc(embedKey, at.lat, at.lon, at.zoom)} loading="lazy"
            referrerPolicy="no-referrer-when-downgrade" data-testid="area-satellite-frame"
            className="mt-3 h-72 w-full rounded-2xl border border-slate-200 sm:h-96" />
        )}
        <p className="mt-2 text-xs text-slate-600">{`Google’s satellite picture of ${name}. It can be months or years old.`}</p>
      </div>
    </section>
  )
}
