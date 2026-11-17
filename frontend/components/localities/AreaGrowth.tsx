import React from 'react'
import { type AreaStats, longDate } from './areaStats'
import { type AreaPicture, monthYear, pictureAlt, thenAndNow } from './areaPictures'
import { jsonLdString } from '@/lib/marketing/seo'

/** Fewer years than this is not a story of growth: the chart is left out. */
export const MIN_YEARS = 3
const CHART_PX = 140
const n = (v: number) => v.toLocaleString('en-IN')

/** The years the chart shows, or null when there are too few (or none has a project). */
export function growthYears(stats: AreaStats | null): AreaStats['registered'] | null {
  const years = stats?.registered ?? []
  return years.length >= MIN_YEARS && years.some((y) => y.projects > 0) ? years : null
}

function Chart({ name, years, caption }: { name: string; years: AreaStats['registered']; caption: string }) {
  const top = Math.max(...years.map((y) => y.projects))
  return (
    <div className="mt-4">
      <h3 className="font-semibold text-slate-900">Projects registered with MahaRERA, per year</h3>
      {/* the bars are drawn for the eye; the table below carries the same numbers for screen readers and crawlers */}
      <div aria-hidden="true" data-testid="growth-chart" className="mt-3 flex items-end gap-[2px] border-b border-slate-300"
        style={{ height: CHART_PX + 24 }}>
        {years.map((y) => (
          <div key={y.year} title={`${y.year}: ${n(y.projects)} ${y.projects === 1 ? 'project' : 'projects'}`}
            className="flex h-full min-w-0 flex-1 flex-col items-center justify-end">
            <span className="text-xs font-semibold tabular-nums text-slate-700">{n(y.projects)}</span>
            <span data-bar={y.year} className="mt-1 w-full max-w-[40px] rounded-t bg-[#0f2340]"
              style={{ height: top > 0 ? Math.round((y.projects / top) * CHART_PX) : 0 }} />
          </div>
        ))}
      </div>
      <div aria-hidden="true" className="flex gap-[2px]">
        {years.map((y) => (
          <span key={y.year} className="min-w-0 flex-1 pt-1 text-center text-xs tabular-nums text-slate-600">
            {years.length > 10 ? `’${String(y.year).slice(2)}` : y.year}
          </span>
        ))}
      </div>
      <table className="sr-only">
        <caption>{caption}</caption>
        <thead><tr><th scope="col">Year</th><th scope="col">Projects registered in {name}</th></tr></thead>
        <tbody>{years.map((y) => <tr key={y.year}><th scope="row">{y.year}</th><td>{y.projects}</td></tr>)}</tbody>
      </table>
    </div>
  )
}

function Pictures({ name, pair, siteUrl }: { name: string; pair: [AreaPicture, AreaPicture]; siteUrl: string }) {
  const ld = pair.map((p) => ({
    '@context': 'https://schema.org', '@type': 'ImageObject',
    contentUrl: siteUrl + p.src, url: siteUrl + p.src, width: p.width, height: p.height,
    name: `${name} from above, ${monthYear(p.day)}`, caption: pictureAlt(name, p), dateCreated: p.day,
    creditText: p.credit, contentLocation: { '@type': 'Place', name: `${name}, Pune` },
  }))
  return (
    <div className="mt-6">
      <h3 className="font-semibold text-slate-900">{name} from above, then and now</h3>
      {ld.map((x) => <script key={x.contentUrl} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(x) }} />)}
      <div className="mt-3 grid grid-cols-2 gap-3">
        {pair.map((p) => (
          <figure key={p.year} className="m-0 min-w-0">
            {/* eslint-disable-next-line @next/next/no-img-element -- a fixed file in public/, already sized: nothing to optimise */}
            <img src={p.src} width={p.width} height={p.height} alt={pictureAlt(name, p)} loading="lazy" decoding="async"
              className="h-auto w-full rounded-lg border border-slate-200" />
            <figcaption className="mt-1 text-sm text-slate-700">
              <span className="font-semibold">{name}, {monthYear(p.day)}</span>
              <span className="block text-xs text-slate-600">{p.credit}</span>
            </figcaption>
          </figure>
        ))}
      </div>
      <p className="mt-2 text-xs text-slate-600">
        Sentinel-2 satellite, true colour, 10 m a pixel: the same box on the least cloudy February to April pass of each year.
      </p>
    </div>
  )
}

/** "How <area> grew": projects registered with MahaRERA per year, and, when public/areas/<slug>.json lists two or more years,
 *  the area from above in the oldest and the newest. Renders nothing when it has neither. */
export default function AreaGrowth({ name, stats, pictures = [], siteUrl }: {
  name: string; stats: AreaStats | null; pictures?: AreaPicture[]; siteUrl: string
}) {
  const years = growthYears(stats)
  const pair = thenAndNow(pictures)
  if (!years && !pair) return null
  const asOf = longDate(stats?.as_of)
  return (
    <section className="mt-9" aria-labelledby="growth-title">
      <h2 id="growth-title" className="text-xl font-semibold text-slate-900">How {name} grew</h2>
      {years && <Chart name={name} years={years}
        caption={`Projects registered with MahaRERA in ${name}, per year, ${years[0].year} to ${years[years.length - 1].year}`} />}
      {years && stats && (
        <p className="mt-3 text-sm text-slate-600">
          Source: {stats.source}{asOf ? `, as of ${asOf}` : ''}. Counted by the year each project was registered; {years[years.length - 1].year} so far.
        </p>
      )}
      {pair && <Pictures name={name} pair={pair} siteUrl={siteUrl} />}
    </section>
  )
}
