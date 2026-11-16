'use client'

import React, { useState } from 'react'

/** Map / Satellite tab switch shown when the project has a checked position and the Maps Embed key is set.
 *  The satellite frame is never created until the user first taps Satellite, so non-tappers pay no Google cost. */
export default function LocationMapSwitch({
  lat, lon, shown, osmSrc, osmLink,
}: {
  lat: number
  lon: number
  shown: string
  osmSrc: string
  osmLink: string
}) {
  const embedKey = process.env.NEXT_PUBLIC_MAPS_EMBED_KEY
  const [mode, setMode] = useState<'map' | 'satellite'>('map')
  const [satCreated, setSatCreated] = useState(false)

  const iframeClass = 'mt-3 h-64 w-full rounded-xl border border-slate-200 sm:h-80'

  if (!embedKey) {
    return (
      <iframe
        title={`Map around ${shown}`}
        src={osmSrc}
        loading="lazy"
        referrerPolicy="no-referrer-when-downgrade"
        className={iframeClass}
      />
    )
  }

  const satSrc = `https://www.google.com/maps/embed/v1/view?key=${embedKey}&center=${lat},${lon}&zoom=17&maptype=satellite`

  function switchToSat() {
    if (!satCreated) setSatCreated(true)
    setMode('satellite')
    try {
      fetch('/api/v1/t/feature', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feature: 'satellite_open' }),
        keepalive: true,
      }).catch(() => undefined)
    } catch {
      // tracking must never break the page
    }
  }

  return (
    <>
      <div
        role="group"
        aria-label="Map type"
        className="mt-3 flex gap-1"
        data-testid="map-type-switch"
      >
        <button
          type="button"
          aria-pressed={mode === 'map'}
          onClick={() => setMode('map')}
          className={
            'min-h-[44px] rounded-full border px-4 text-sm font-semibold ' +
            (mode === 'map'
              ? 'border-[var(--site-primary)] bg-[var(--site-primary)] text-[var(--site-on-primary)]'
              : 'border-slate-300 bg-white text-slate-700')
          }
        >
          Map
        </button>
        <button
          type="button"
          aria-pressed={mode === 'satellite'}
          onClick={switchToSat}
          className={
            'min-h-[44px] rounded-full border px-4 text-sm font-semibold ' +
            (mode === 'satellite'
              ? 'border-[var(--site-primary)] bg-[var(--site-primary)] text-[var(--site-on-primary)]'
              : 'border-slate-300 bg-white text-slate-700')
          }
        >
          Satellite
        </button>
      </div>
      <iframe
        title={`Map around ${shown}`}
        src={osmSrc}
        loading="lazy"
        referrerPolicy="no-referrer-when-downgrade"
        className={iframeClass + (mode === 'satellite' ? ' hidden' : '')}
      />
      {satCreated && (
        <iframe
          title={`Satellite view of ${shown}`}
          src={satSrc}
          loading="lazy"
          referrerPolicy="no-referrer-when-downgrade"
          className={iframeClass + (mode === 'map' ? ' hidden' : '')}
          data-testid="satellite-frame"
        />
      )}
      {mode === 'satellite' && (
        <p className="mt-2 text-xs text-slate-500" data-testid="satellite-note">
          {"Google’s satellite picture of the checked position. It can be months or years old, so a site being built may look emptier than it is today."}
        </p>
      )}
    </>
  )
}
