'use client'

import React, { useState } from 'react'
import { MapTypeSwitch, mapsEmbedKey, satelliteSrc, sendFeature, type MapMode } from './mapsEmbed'

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
  const embedKey = mapsEmbedKey()
  const [mode, setMode] = useState<MapMode>('map')
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

  const satSrc = satelliteSrc(embedKey, lat, lon, 17)

  function switchToSat() {
    if (!satCreated) setSatCreated(true)
    setMode('satellite')
    sendFeature('satellite_open')
  }

  return (
    <>
      <MapTypeSwitch mode={mode} onMap={() => setMode('map')} onSatellite={switchToSat} />
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
