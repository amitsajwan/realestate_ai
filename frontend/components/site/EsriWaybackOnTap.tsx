'use client'

import React, { useId, useState } from 'react'
import { pillClass, sendFeature } from './mapsEmbed'

const WAYBACK = 'https://livingatlas.arcgis.com/wayback/'

/** Esri's public World Imagery Wayback viewer, centred on the pin, in its swipe mode: sharp pictures (well under a metre a pixel)
 *  from Esri's past releases. Sentinel-2 cannot show the plot at 10 m; this can (owner 2026-11-21: "embed esri"). Its parameters
 *  are the ones the viewer reads from its hash (`mapCenter=<lon>,<lat>,<zoom>`, `mode`; read from its code 2026-11-21); on a
 *  phone it opens in its plain explore view. Shown from Esri's viewer with Esri's credits, never stored, and the frame is made
 *  on the first tap: nothing is asked of Esri for a reader who never taps. Give it a checked pin only. */
export function waybackSrc(lat: number, lon: number, zoom = 17): string {
  return `${WAYBACK}#mapCenter=${lon.toFixed(6)}%2C${lat.toFixed(6)}%2C${zoom}&mode=swipe`
}

export default function EsriWaybackOnTap({ lat, lon, label }: { lat: number; lon: number; label: string }) {
  const [open, setOpen] = useState(false)
  const [made, setMade] = useState(false)
  const frameId = useId()
  const src = waybackSrc(lat, lon)
  function toggle() {
    if (!made) {
      setMade(true)
      sendFeature('satellite_open')
    }
    setOpen((o) => !o)
  }
  return (
    <div className="mt-3" data-testid="esri-wayback">
      <button type="button" onClick={toggle} aria-expanded={open} aria-controls={frameId} className={pillClass(open)}>
        Compare sharp past pictures
      </button>
      <div id={frameId} className={open ? '' : 'hidden'}>
        {made && (
          <iframe title={`${label}, past satellite pictures, Esri World Imagery Wayback`} src={src} loading="lazy"
            referrerPolicy="no-referrer-when-downgrade" allowFullScreen data-testid="esri-wayback-frame"
            className="mt-3 aspect-[4/3] w-full rounded-lg border border-slate-200 sm:aspect-[16/9]" />
        )}
        <p className="mt-1 text-xs text-slate-600">
          Esri World Imagery Wayback: Esri&apos;s earlier releases of its satellite pictures, centred on the project&apos;s map pin.
          Drag the divider to compare two releases; each says its date in the viewer. Not every release has a new picture of this
          spot, so two may look the same.{' '}
          <a href={src} target="_blank" rel="noopener noreferrer" className="font-semibold underline underline-offset-2">Open full screen ↗</a>
        </p>
      </div>
    </div>
  )
}
