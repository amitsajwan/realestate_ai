import React from 'react'
import { shortMonth } from '@/lib/site/fromAbove'
import { datesSaid, metresAcross, tileOf, tileSrc, waybackLink, type EsriPast } from '@/lib/site/esriPast'

/** Esri's sharp past pictures of a place, oldest to newest, each drawn from Esri's own tiles centred on the point (two tiles
 *  across: about 580 m for a project at zoom 17, the Sentinel frame; about 1.2 km for an area at 16; further out the sharp
 *  pictures blur to Sentinel's level), with the 100 m ring around a project's pin, two to a row so a phone shows them large. Replaces the framed Wayback viewer, which asked a buyer to find releases and drag a divider (owner 2026-11-21). The
 *  dates are said in the text and the middle tile of each picture carries an alt naming the place and the month, so search
 *  reads what the pictures are; the tiles load lazily, from Esri, and nothing is stored by us. */
export default function EsriPastPictures({ past, lat, lon, name, centredOn, ringM = 0, className = 'mt-4' }: {
  past: EsriPast; lat: number; lon: number; name: string; centredOn: string; ringM?: number; className?: string
}) {
  const { zoom, shots } = past
  const t = tileOf(lat, lon, zoom)
  const across = metresAcross(lat, zoom)
  const acrossSaid = across >= 1500 ? `about ${(across / 1000).toFixed(1)} km` : `about ${Math.round(across / 10) * 10} m`
  const sources = Array.from(new Set(shots.map((s) => s.source).filter(Boolean)))
  const sharp = shots.map((s) => s.res).filter((r): r is number => r !== null)
  const ring = ringM > 0 ? (2 * ringM / across) * 100 : 0
  return (
    <div className={className} data-testid="esri-past">
      <h3 className="text-base font-semibold text-slate-900">{name}, year by year, up close</h3>
      <p className="mt-1 text-sm text-slate-700">
        Sharp satellite pictures taken in {datesSaid(shots)}, centred on {centredOn}, {acrossSaid} across
        {sharp.length ? ` at about ${Math.max(...sharp).toFixed(1)} m a pixel` : ''}.
      </p>
      <ol className="mt-2 grid list-none grid-cols-2 gap-2 p-0">
        {shots.map((s, i) => {
          const month = shortMonth(s.captured)
          const newest = i === shots.length - 1
          return (
            <li key={s.release}>
              <figure className="m-0">
                <div className="relative aspect-square w-full overflow-hidden rounded-lg border border-slate-200 bg-slate-200"
                  data-testid="esri-past-picture">
                  <div className="absolute grid grid-cols-3" style={{ width: '150%', height: '150%', left: `${-t.fx * 50}%`, top: `${-t.fy * 50}%` }}>
                    {[-1, 0, 1].flatMap((dy) => [-1, 0, 1].map((dx) => (
                      <img key={`${dx}${dy}`} src={tileSrc(s.release, zoom, t.row + dy, t.col + dx)} loading="lazy" decoding="async"
                        width={256} height={256} className="block h-full w-full" referrerPolicy="no-referrer-when-downgrade"
                        alt={dx === 0 && dy === 0 ? `${name} from above, satellite picture of ${month}` : ''} />
                    )))}
                  </div>
                  {ring > 0 && (
                    <span aria-hidden="true" className="absolute rounded-full border-2 border-[#ffd200]"
                      style={{ width: `${ring}%`, height: `${ring}%`, left: `${50 - ring / 2}%`, top: `${50 - ring / 2}%` }} />
                  )}
                </div>
                <figcaption className="mt-1 text-xs text-slate-700">
                  <span className="font-semibold text-slate-900">{month}</span>{newest ? ' · latest' : ''}
                </figcaption>
              </figure>
            </li>
          )
        })}
      </ol>
      <p className="mt-1 text-xs text-slate-600">
        Esri World Imagery{sources.length ? ` · ${sources.join(', ')}` : ''}. Each picture is dated by when it was taken{ring > 0 ? '; the ring is 100 m around the pin' : ''}.{' '}
        <a href={waybackLink(lat, lon, zoom)} target="_blank" rel="noopener noreferrer"
          className="inline-flex min-h-[44px] items-center font-semibold underline underline-offset-2">Compare every release ↗</a>
      </p>
    </div>
  )
}
