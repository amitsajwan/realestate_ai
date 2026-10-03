import React from 'react'
import ReraBox from '@/components/site/ReraBox'
import SlideStrip from '@/components/site/SlideStrip'
import { formatPrice, groupIndian } from '@/lib/site/format'
import { formatDay, mapsLink, possessionLines, sourceLabel } from '@/lib/site/projects'
import type { PublicProject } from '@/lib/site/types'

/** The body of a project page: photo, prices, the MahaRERA record, possession dates, fit, location, amenities and details.
 *  Shared by the agent's own project page and Avasetu's /projects page. `agentName` is who quoted the prices and dates. */
export default function ProjectDetails({ p, agentName }: { p: PublicProject; agentName: string }) {
  const name = agentName
  const quoted = sourceLabel('agent', name)
  const possession = possessionLines(p, name)
  const photo = p.media.find((m) => m.kind === 'image' && !m.slide)
  const slides = p.media.filter((m) => m.kind === 'image' && m.slide).map((m, i, all) => ({ url: m.url, alt: `${p.name}: ${m.caption || 'slide ' + (i + 1) + ' of ' + all.length}` }))
  return (
    <>
      {photo && (
        <figure className="overflow-hidden rounded-2xl bg-slate-100">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={photo.url} alt={photo.caption} width={1600} height={756} className="aspect-[16/8] w-full object-cover" />
          <figcaption className="px-3 py-2 text-xs text-slate-600">
            {photo.caption}{photo.credit ? ' · ' + photo.credit : ''}
          </figcaption>
        </figure>
      )}

      {slides.length > 0 && (
        <section aria-labelledby="slides-title">
          <h2 id="slides-title" className="text-xl font-bold">As posted on Instagram</h2>
          <SlideStrip slides={slides} label={`${p.name} carousel`} className="mt-3" />
        </section>
      )}

      <section aria-labelledby="prices-title">
        <h2 id="prices-title" className="text-xl font-bold">Prices and sizes</h2>
        <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr><th className="px-2 py-2 font-semibold sm:px-3">Home</th><th className="px-2 py-2 font-semibold sm:px-3">Carpet</th><th className="px-2 py-2 font-semibold sm:px-3">Price</th><th className="px-2 py-2 font-semibold sm:px-3">Per sq ft</th></tr>
            </thead>
            <tbody>
              {p.configurations.map((c) => (
                <tr key={c.label + c.carpet_sqft} className="border-t border-slate-100">
                  <td className="px-2 py-2 sm:px-3 font-semibold">{c.label}</td>
                  <td className="px-2 py-2 sm:px-3">{groupIndian(c.carpet_sqft)} sq ft</td>
                  <td className="px-2 py-2 sm:px-3 font-semibold">{formatPrice(c.price_inr)}</td>
                  <td className="px-2 py-2 sm:px-3">₹{groupIndian(c.price_per_sqft)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-slate-600">{quoted}. Builders change prices often: confirm the price, the floor and any extra charges (parking, GST, stamp duty) before you book.</p>
      </section>

      <ReraBox p={p} />

      {possession.length > 0 && (
        <section aria-labelledby="when-title">
          <h2 id="when-title" className="text-xl font-bold">When could you move in?</h2>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-800">
            {possession.map((l) => <li key={l}>{l}</li>)}
          </ul>
          <p className="mt-2 text-xs text-slate-600">Under RERA (section 18), if possession is late beyond the date in your agreement for sale, you can claim interest for the delay or withdraw with a refund.</p>
        </section>
      )}

      {(p.who_it_suits.length > 0 || p.highlights.length > 0) && (
        <section aria-labelledby="fit-title" className="grid gap-4 sm:grid-cols-2">
          {p.who_it_suits.length > 0 && (
            <div className="rounded-2xl border border-slate-200 p-4">
              <h2 id="fit-title" className="text-lg font-bold">Who it suits</h2>
              <ul className="mt-2 list-disc space-y-1 pl-5">{p.who_it_suits.map((w) => <li key={w}>{w}</li>)}</ul>
              <p className="mt-2 text-xs text-slate-500">{sourceLabel('avasetu', name)}, from the facts on this page.</p>
            </div>
          )}
          {p.highlights.length > 0 && (
            <div className="rounded-2xl border border-slate-200 p-4">
              <h2 className="text-lg font-bold">Worth knowing</h2>
              <ul className="mt-2 list-disc space-y-1 pl-5">{p.highlights.map((w) => <li key={w}>{w}</li>)}</ul>
            </div>
          )}
        </section>
      )}

      <section aria-labelledby="where-title">
        <h2 id="where-title" className="text-xl font-bold">Location</h2>
        {p.address && <p className="mt-1 text-slate-800">{p.address} <span className="text-xs text-slate-500">({quoted})</span></p>}
        {p.nearby.length > 0 && (
          <ul className="mt-3 grid gap-2 sm:grid-cols-2">
            {p.nearby.map((n) => (
              <li key={n.name} className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2 text-sm">
                <span>{n.name}</span>
                <span className="font-semibold">{n.km != null ? `${n.km} km by road` : ''}</span>
              </li>
            ))}
          </ul>
        )}
        {p.nearby.some((n) => n.km != null) && (
          <p className="mt-2 text-xs text-slate-500">Road distances from {p.place?.note || 'the project'} (OpenStreetMap routing, no traffic).</p>
        )}
        <a href={mapsLink(p)} target="_blank" rel="noopener noreferrer"
          className="mt-3 inline-flex min-h-[44px] items-center rounded-xl border border-slate-300 px-4 font-semibold text-[var(--site-primary)] no-underline">
          Find it on Google Maps
        </a>
      </section>

      {p.amenities.length > 0 && (
        <section aria-labelledby="amen-title">
          <h2 id="amen-title" className="text-xl font-bold">Amenities</h2>
          <ul className="mt-2 flex list-none flex-wrap gap-2 p-0">
            {p.amenities.map((a) => <li key={a} className="rounded-full bg-slate-100 px-3 py-1.5 text-sm">{a}</li>)}
          </ul>
          <p className="mt-2 text-xs text-slate-500">{quoted}.</p>
        </section>
      )}

      {Object.keys(p.specs).length > 0 && (
        <section aria-labelledby="spec-title">
          <h2 id="spec-title" className="text-xl font-bold">Project details</h2>
          <dl className="mt-2 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {Object.entries(p.specs).map(([k, v]) => (
              <div key={k} className="rounded-xl bg-slate-50 px-3 py-2">
                <dt className="text-xs text-slate-500">{k}</dt>
                <dd className="font-semibold">{v}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-2 text-xs text-slate-500">{quoted}.{p.possession_target ? ` Builder's target possession: ${formatDay(p.possession_target)}.` : ''}</p>
        </section>
      )}
    </>
  )
}
