import React from 'react'

/** What the Google Maps Embed views share: the project pages' Map / Satellite switch (LocationMapSwitch), the area map's
 *  (AreaMapView), an area's view from above (AreaFromAbove) and Street View on tap (StreetViewOnTap). Plans:
 *  docs/plan/satellite-view.md, docs/plan/area-pictures.md. Google's imagery is only ever shown through its embed, never stored. */

/** The embed's own browser key (restricted to the site and to Maps Embed); the server's Maps key never reaches the browser.
 *  Without it every view here renders as if it did not exist. */
export function mapsEmbedKey(): string | undefined {
  return process.env.NEXT_PUBLIC_MAPS_EMBED_KEY || undefined
}

const EMBED = 'https://www.google.com/maps/embed/v1/'

export function satelliteSrc(key: string, lat: number, lon: number, zoom: number): string {
  return `${EMBED}view?key=${key}&center=${lat},${lon}&zoom=${zoom}&maptype=satellite`
}

export function streetViewSrc(key: string, lat: number, lon: number, heading?: number): string {
  return `${EMBED}streetview?key=${key}&location=${lat},${lon}${heading != null ? `&heading=${heading}` : ''}&fov=90`
}

/** The middle of a map box (south, west, north, east), rounded to about a metre. */
export function boxCentre(box: number[]): { lat: number; lon: number } {
  const [s, w, n, e] = box
  const r = (x: number) => Math.round(x * 1e5) / 1e5
  return { lat: r((s + n) / 2), lon: r((w + e) / 2) }
}

/** The largest Google zoom at which the whole box fits across `px` pixels (the drawn map is 640 wide on a laptop): at zoom z a
 *  pixel is 156543 m x cos(latitude) / 2^z. Kept between 10 and 18 so a bad box never shows the whole state or one roof. */
export function zoomToFit(box: number[], px = 640): number {
  const [s, w, n, e] = box
  const mid = ((s + n) / 2) * Math.PI / 180
  const across = Math.max((e - w) * 111320 * Math.cos(mid), (n - s) * 110574)
  if (!(across > 0)) return 14
  const z = Math.floor(Math.log2((156543.03 * Math.cos(mid) * px) / across))
  return Math.min(18, Math.max(10, z))
}

/** A tap on one of these views, for Studio's visit trail (docs/plan/satellite-view.md, "How we judge it"). */
export function sendFeature(feature: string, extra: Record<string, string> = {}): void {
  try {
    fetch('/api/v1/t/feature', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feature, ...extra }),
      keepalive: true,
    }).catch(() => undefined)
  } catch {
    // tracking must never break the page
  }
}

/** The pill look every switch and tap button here shares, 44 px tall for a thumb. The colours fall back to the site's navy where a
 *  page sets no site theme (the area guides do not). */
export function pillClass(on: boolean): string {
  return 'min-h-[44px] rounded-full border px-4 text-sm font-semibold ' +
    (on
      ? 'border-[var(--site-primary,#0f2340)] bg-[var(--site-primary,#0f2340)] text-[var(--site-on-primary,#fff)]'
      : 'border-slate-300 bg-white text-slate-700')
}

export type MapMode = 'map' | 'satellite'

/** The two buttons, Map and Satellite. */
export function MapTypeSwitch({ mode, onMap, onSatellite, className = 'mt-3 flex gap-1' }:
  { mode: MapMode; onMap: () => void; onSatellite: () => void; className?: string }) {
  return (
    <div role="group" aria-label="Map type" className={className} data-testid="map-type-switch">
      <button type="button" aria-pressed={mode === 'map'} onClick={onMap} className={pillClass(mode === 'map')}>Map</button>
      <button type="button" aria-pressed={mode === 'satellite'} onClick={onSatellite} className={pillClass(mode === 'satellite')}>Satellite</button>
    </div>
  )
}
