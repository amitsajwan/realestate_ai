import React from 'react'
import Link from 'next/link'
import EnquiryForm from '@/components/site/EnquiryForm'
import FinderCard from './FinderCard'
import CopyLink from './CopyLink'
import TrackedLink from '@/components/site/TrackedLink'
import { withParam } from '@/lib/site/links'
import { formatArea, formatPrice } from '@/lib/site/format'
import { monthYear } from '@/lib/site/register'
import {
  PAGE, SORTS, asked, bookedShare, byArea, describe, facets, findHomes, shareText, toSearch,
  type FinderItem, type FinderQuery, type Option,
} from '@/lib/site/finder'

export interface FinderMap { name: string; map: string; box: number[]; attribution: string }
export interface FinderLead { agentSlug: string; agentName: string; agentPhone?: string | null }

interface Props {
  items: FinderItem[]
  q: FinderQuery
  /** the page the choices link to ("/agent/house-deal", "/projects") */
  basePath: string
  title?: string
  /** who an empty result's enquiry goes to */
  lead: FinderLead
  /** the drawn area maps, by area slug: the map view shows when the chosen area has one */
  maps?: Record<string, FinderMap>
  id?: string
  /** the site's origin ("https://avasetu.in"), for the shared link */
  origin?: string
}

const chip = (on: boolean) =>
  'inline-flex min-h-[40px] shrink-0 items-center gap-1.5 rounded-full border px-3.5 text-sm font-semibold no-underline ' +
  (on ? 'border-[var(--site-primary,#0f2340)] bg-[var(--site-primary,#0f2340)] text-white'
    : 'border-slate-300 bg-white text-slate-800 hover:border-[var(--site-primary,#0f2340)]')

/** One question's choices as taps: a choice that gives nothing shows greyed, the picked one taps off. */
function Choices({ label, dim, options, q, base, anchor }: { label: string; dim: keyof FinderQuery; options: Option[]; q: FinderQuery; base: string; anchor: string }) {
  if (!options.length) return null
  return (
    <div className="flex items-center gap-2" role="group" aria-label={label}>
      <span className="w-20 shrink-0 text-xs font-bold uppercase tracking-wide text-slate-500">{label}</span>
      <ul className="-my-1 flex min-w-0 list-none gap-2 overflow-x-auto p-0 py-1 [scrollbar-width:none]">
        {options.map((o) => (
          <li key={o.key} className="shrink-0">
            {o.count === 0 && !o.on ? (
              <span className={chip(false) + ' cursor-default opacity-40'} aria-disabled="true">{o.label}</span>
            ) : (
              <Link href={base + toSearch(q, { [dim]: o.on ? undefined : o.key } as Partial<FinderQuery>) + anchor} scroll={false} rel="nofollow"
                className={chip(o.on)} aria-pressed={o.on}>
                {o.label}{!o.on && <span className="text-xs font-normal text-slate-500">{o.count}</span>}
              </Link>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

/** The chosen projects side by side: each home type's price, possession, the date's moves, homes booked. */
function Compare({ items, q, base, anchor }: { items: FinderItem[]; q: FinderQuery; base: string; anchor: string }) {
  if (items.length < 2) return null
  const bhks = Array.from(new Set(items.flatMap((i) => i.homes.map((h) => h.bhk)))).sort((a, b) => (a ?? 0) - (b ?? 0))
  const cheapest = (i: FinderItem, b: number | null) => i.homes.filter((h) => h.bhk === b && h.price != null).sort((x, y) => x.price! - y.price!)[0]
  const rows: [string, (i: FinderItem) => React.ReactNode][] = [
    ['Area', (i) => i.area],
    ...bhks.map((b): [string, (i: FinderItem) => React.ReactNode] => [b == null ? 'Plot' : `${b} BHK`, (i) => {
      const h = cheapest(i, b)
      return h ? <>{formatPrice(h.price!)}{h.sqft ? <span className="block text-xs text-slate-500">{formatArea(h.sqft)}</span> : null}</> : '–'
    }]),
    ['Possession (MahaRERA)', (i) => (i.possession ? monthYear(i.possession) : '–')],
    ['Date moved', (i) => (i.monthsLater == null ? '–' : i.monthsLater === 0 ? <span className="font-semibold text-emerald-700">Not moved</span> : `${i.monthsLater} months later`)],
    ['Homes booked', (i) => { const s = bookedShare(i); return s == null ? '–' : `${i.booked} of ${i.total} (${Math.round(s * 100)}%)` }],
    ['Video', (i) => (i.video ? 'Yes' : '–')],
  ]
  return (
    <section aria-labelledby="compare-title" className="mt-6 rounded-2xl border-2 border-[var(--site-primary,#0f2340)] bg-white p-4" data-testid="compare-table">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 id="compare-title" className="text-lg font-bold text-slate-900">Comparing {items.length} projects</h3>
        <Link href={base + toSearch(q, { compare: undefined }) + anchor} scroll={false} rel="nofollow" className="text-sm font-semibold text-[var(--site-primary,#0f2340)] underline">Clear comparison</Link>
      </div>
      <div className="mt-3 overflow-x-auto">
        <table className="w-full min-w-[32rem] text-left text-sm">
          <thead>
            <tr><th className="py-2 pr-3" />{items.map((i) => (
              <th key={i.id} className="py-2 pr-3 align-bottom"><Link href={i.href} className="font-semibold text-[var(--site-primary,#0f2340)] underline">{i.name}</Link></th>
            ))}</tr>
          </thead>
          <tbody>
            {rows.map(([label, cell]) => (
              <tr key={label} className="border-t border-slate-100">
                <th scope="row" className="py-2 pr-3 font-medium text-slate-600">{label}</th>
                {items.map((i) => <td key={i.id} className="py-2 pr-3 tabular-nums text-slate-900">{cell(i)}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

/** Pins for the results on the area's drawn map (the frame is south, west, north, east), numbered as the list below. */
function MapView({ items, map }: { items: FinderItem[]; map: FinderMap }) {
  const [s, w, n, e] = map.box
  const pins = items.map((i, k) => ({ i, k: k + 1, x: i.map ? (i.map.lon - w) / (e - w) : -1, y: i.map ? (n - i.map.lat) / (n - s) : -1 }))
    .filter((p) => p.x >= 0 && p.x <= 1 && p.y >= 0 && p.y <= 1)
  return (
    <div className="mt-6" data-testid="finder-map">
      <div className="relative mx-auto aspect-square w-full max-w-2xl overflow-hidden rounded-2xl border border-slate-200 bg-slate-50">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={map.map} alt="" aria-hidden="true" className="absolute inset-0 h-full w-full" />
        {pins.map((p) => (
          <Link key={p.i.id} href={p.i.href} title={p.i.name} aria-label={`${p.k}. ${p.i.name}`}
            className="absolute flex h-8 w-8 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border-2 border-white bg-[var(--site-primary,#0f2340)] text-xs font-bold text-white no-underline shadow"
            style={{ left: `${p.x * 100}%`, top: `${p.y * 100}%` }}>{p.k}</Link>
        ))}
      </div>
      <p className="mt-2 text-center text-xs text-slate-600">
        {pins.length} of {items.length} on the map of {map.name}; the rest have no checked position yet. {map.attribution}
      </p>
    </div>
  )
}

/**
 * The home finder (lib/site/finder): the four questions as taps, the MahaRERA switches, sort and a map, then the answers. With
 * nothing asked it shows each area's projects in a row to swipe; with no answer it asks for the enquiry, the question filled in.
 * Every choice is a link (works without JavaScript; the address is shareable), marked nofollow: the canonical page has none.
 */
export default function HomeFinder({ items, q, basePath, title = 'Find your home', lead, maps = {}, id = 'homes', origin = '' }: Props) {
  const anchor = '#' + id
  const f = facets(items, q)
  const found = findHomes(items, q)
  const areaName = f.area.find((a) => a.on)?.label ?? null
  const map = q.area ? maps[q.area] : undefined
  const grouped = !asked(q) && !q.sort && q.view !== 'map' && f.area.length > 1
  const shown = found.slice(0, q.more ?? PAGE)
  const comparing = (q.compare ?? []).map((c) => items.find((i) => i.id === c)).filter((i): i is FinderItem => !!i)
  const words = describe(q, areaName)
  // the view as a link to send: the answers asked (not the comparison, paging or map), marked so the visit it brings is counted
  const url = withParam(origin + basePath + toSearch(q, { compare: undefined, more: undefined, view: undefined }).replace(/^\?$/, ''), 'src', 'share') + anchor
  const message = shareText(found, q, { who: lead.agentName, url, areaName,
    fmt: { price: (n) => formatPrice(n), area: (n) => formatArea(n), month: (d) => monthYear(d) } })
  return (
    <section id={id} aria-labelledby={id + '-title'} className="scroll-mt-16" data-testid="home-finder">
      <h2 id={id + '-title'} className="text-2xl font-bold text-slate-900">{title}</h2>
      <div className="mt-4 space-y-2.5 rounded-2xl border border-slate-200 bg-slate-50 p-3 sm:p-4">
        <Choices label="Area" dim="area" options={f.area} q={q} base={basePath} anchor={anchor} />
        <Choices label="Budget" dim="budget" options={f.budget} q={q} base={basePath} anchor={anchor} />
        <Choices label="Size" dim="bhk" options={f.bhk} q={q} base={basePath} anchor={anchor} />
        <Choices label="Move in" dim="movein" options={f.movein} q={q} base={basePath} anchor={anchor} />
        <Choices label="Type" dim="type" options={f.type} q={q} base={basePath} anchor={anchor} />
        {f.toggles.length > 0 && (
          <div className="flex items-center gap-2" role="group" aria-label="Checked on MahaRERA">
            <span className="w-20 shrink-0 text-xs font-bold uppercase tracking-wide text-slate-500">Checked</span>
            <ul className="-my-1 flex min-w-0 list-none gap-2 overflow-x-auto p-0 py-1 [scrollbar-width:none]">
              {f.toggles.map((t) => (
                <li key={t.key} className="shrink-0">
                  <Link href={basePath + toSearch(q, { [t.key]: t.on ? undefined : true } as Partial<FinderQuery>) + anchor} scroll={false} rel="nofollow"
                    className={chip(t.on)} aria-pressed={t.on}>{t.on ? '✓ ' : ''}{t.label}</Link>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <p className="text-slate-800" aria-live="polite" data-testid="finder-summary">
          <span className="font-bold">{found.length} {found.length === 1 ? 'project' : 'projects'}</span>{words ? <> for {words}</> : null}
          {asked(q) && <> · <Link href={basePath + toSearch({}, { compare: q.compare }) + anchor} scroll={false} rel="nofollow" className="font-semibold text-[var(--site-primary,#0f2340)] underline">Clear</Link></>}
        </p>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          {map && (
            <Link href={basePath + toSearch(q, { view: q.view === 'map' ? undefined : 'map' }) + anchor} scroll={false} rel="nofollow" className={chip(q.view === 'map')}>
              {q.view === 'map' ? 'List' : 'Map'}
            </Link>
          )}
          <span className="text-slate-500">Sort:</span>
          {SORTS.map((s) => {
            const on = (q.sort ?? 'match') === s.key
            return on ? <span key={s.key} className="font-semibold text-slate-900">{s.label}</span>
              : <Link key={s.key} href={basePath + toSearch(q, { sort: s.key === 'match' ? undefined : s.key }) + anchor} scroll={false} rel="nofollow"
                  className="text-[var(--site-primary,#0f2340)] underline underline-offset-2">{s.label}</Link>
          })}
        </div>
      </div>

      {found.length > 0 && (
        <div className="mt-3 flex flex-wrap items-center gap-2" data-testid="finder-share">
          <TrackedLink href={'https://wa.me/?text=' + encodeURIComponent(message)} event="share" agentSlug={lead.agentSlug} target="_blank" rel="noopener noreferrer"
            className="inline-flex min-h-[40px] items-center gap-2 rounded-full bg-[#25D366] px-4 text-sm font-bold text-[#053b1a] no-underline">
            <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" fill="currentColor"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm5.3 14.2c-.2.6-1.3 1.2-1.8 1.2-.5.1-1 .2-3.4-.7-2.9-1.1-4.7-4-4.8-4.2-.1-.2-1.2-1.6-1.2-3s.7-2.1 1-2.4c.3-.3.6-.3.8-.3h.6c.2 0 .4 0 .6.5l.8 2c.1.2.1.4 0 .5l-.4.6-.4.4c-.1.2-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.2 1 2.1 1.3 2.4 1.5.3.1.5.1.6-.1l.9-1c.2-.3.4-.2.6-.1l1.9.9c.3.1.5.2.5.3.1.2.1.7-.1 1.2z" /></svg>
            {asked(q) ? `Send ${found.length === 1 ? 'this' : `these ${found.length}`} on WhatsApp` : 'Send on WhatsApp'}
          </TrackedLink>
          <CopyLink url={url} className="inline-flex min-h-[40px] items-center rounded-full border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-800" />
        </div>
      )}

      <Compare items={comparing} q={q} base={basePath} anchor={anchor} />

      {found.length === 0 ? (
        <div className="mt-6 grid gap-6 md:grid-cols-2" data-testid="finder-empty">
          <div>
            <p className="text-lg font-semibold text-slate-900">Nothing for {words || 'this'} right now.</p>
            <p className="mt-2 text-slate-700">
              Tell {lead.agentName} what you need: new projects and price changes come every week, and you get a WhatsApp when one fits.
              Or <Link href={basePath + toSearch({}, {}) + anchor} scroll={false} className="font-semibold text-[var(--site-primary,#0f2340)] underline">see every project</Link>.
            </p>
          </div>
          <EnquiryForm agentSlug={lead.agentSlug} agentName={lead.agentName} agentPhone={lead.agentPhone ?? undefined} id="finder-ask"
            topic={`Looking for: ${words}`} waMessage={`Hi ${lead.agentName}, I am looking for ${words}.`}
            title="Get a WhatsApp when one fits" submitLabel="Tell me when one fits" />
        </div>
      ) : q.view === 'map' && map ? (
        <MapView items={found} map={map} />
      ) : grouped ? (
        <div className="mt-6 space-y-8">
          {byArea(found).map((g) => (
            <div key={g.slug} data-testid="finder-area-row">
              <div className="flex items-baseline justify-between gap-2">
                <h3 className="text-xl font-semibold text-slate-900">{g.area} <span className="text-base font-normal text-slate-500">· {g.items.length}</span></h3>
                <Link href={basePath + toSearch(q, { area: g.slug }) + anchor} scroll={false} rel="nofollow" className="inline-flex min-h-[44px] items-center font-semibold text-[var(--site-primary,#0f2340)] underline underline-offset-2">
                  See all {g.items.length} →
                </Link>
              </div>
              <ul className="-mx-4 mt-2 flex list-none snap-x gap-4 overflow-x-auto px-4 pb-2 [scrollbar-width:thin] sm:mx-0 sm:px-0">
                {g.items.slice(0, 8).map((i) => (
                  <li key={i.id} className="w-[78%] shrink-0 snap-start sm:w-72"><FinderCard item={i} q={q} basePath={basePath} anchor={anchor} /></li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      ) : (
        <>
          <ul className="mt-6 grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3">
            {shown.map((i) => <li key={i.id}><FinderCard item={i} q={q} basePath={basePath} anchor={anchor} /></li>)}
          </ul>
          {found.length > shown.length && (
            <p className="mt-4 text-center">
              <Link href={basePath + toSearch(q, { more: shown.length + PAGE }) + anchor} scroll={false} rel="nofollow" className={chip(false)}>
                Show more ({found.length - shown.length} left)
              </Link>
            </p>
          )}
        </>
      )}
    </section>
  )
}
