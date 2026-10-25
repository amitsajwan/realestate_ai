import React from 'react'
import Link from 'next/link'
import AskPrompt from '@/components/site/AskPrompt'
import EnquiryForm from '@/components/site/EnquiryForm'
import StickyJoinBar from '@/components/marketing/StickyJoinBar'
import { PROJECT_CTA } from '@/lib/site/strings'
import VerifiedFacts from '@/components/site/VerifiedFacts'
import { jsonLdString } from '@/lib/marketing/seo'
import { registerProjectJsonLd } from '@/lib/site/projectSeo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import type { RegisterProject } from '@/lib/site/register'
import type { FacetLink } from '@/lib/site/facets'
import WebFactsBox from '@/components/site/WebFactsBox'
import ProjectProfile from '@/components/site/ProjectProfile'
import { distinctPhotos } from '@/components/site/ProfilePictures'
import CostBreakdown from '@/components/site/CostBreakdown'
import PriceBox from '@/components/site/PriceBox'
import type { Stage } from '@/lib/site/allin'
import { areaName, askedPrices, bhkRange, displayName, longDay, monthYear, offerPrice, otherNames, projectFaq, placePath, STAGE_LABEL, STAGE_NOTE } from '@/lib/site/register'
import type { EnrichCheck, Faq, Offer } from '@/lib/site/register'
import type { ProfilePicture } from '@/lib/site/profile'
import type { PropertyFactsView } from '@/lib/site/types'
import { formatPrice } from '@/lib/site/format'
import { OWN_CASH_NOTE, ownCash } from '@/lib/site/upfront'
import { projectUpdated, registerAnswer } from '@/lib/site/projectFacts'

function OfferBox({ facts, stage }: { facts: PropertyFactsView | null; stage: Stage }) {
  const o = (facts as unknown as { offer?: Offer } | null)?.offer
  if (!o || !(o.price_inr || o.plot_sqft || o.carpet_sqft || o.bhk)) return null
  const sheet = o.homes && o.homes.length > 1 ? o.homes : null
  // the home the headline price is for: its size decides the affordable GST rate, so it is never taken from another home
  const priced = sheet ? sheet.find((h) => h.price_inr === o.price_inr) : null
  const sizes = (sheet || []).map((h) => h.carpet_sqft || 0).filter(Boolean)
  const what = sheet
    ? [bhkRange(sheet), o.property_type ? `${o.property_type}s` : null,
      sizes.length ? `${Math.min(...sizes).toLocaleString('en-IN')} to ${Math.max(...sizes).toLocaleString('en-IN')} sq ft carpet` : null]
      .filter(Boolean).join(' · ')
    : [o.bhk ? `${o.bhk} BHK` : null, o.property_type, o.plot_sqft ? `plot ${o.plot_sqft.toLocaleString('en-IN')} sq ft` : null,
      o.carpet_sqft ? `${o.carpet_sqft.toLocaleString('en-IN')} sq ft carpet` : null].filter(Boolean).join(' · ')
  return (
    <section aria-labelledby="offer-title" className="rounded-2xl border border-amber-200 bg-amber-50 p-4" data-testid="offer">
      <h2 id="offer-title" className="text-lg font-bold text-slate-900">On offer</h2>
      {o.price_inr ? <p className="mt-1 text-2xl font-extrabold text-slate-900">{sheet ? 'From ' : ''}{formatPrice(o.price_inr)}</p> : null}
      {what && <p className="mt-1 text-slate-800">{what}</p>}
      {o.payment_plan ? (
        <p className="mt-2 text-slate-900" data-testid="payment-plan">
          Payment plan: <strong>{o.payment_plan}</strong> <span className="text-sm text-slate-600">(the builder&apos;s plan)</span>
        </p>
      ) : null}
      {sheet ? (
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[16rem] text-left text-sm" data-testid="price-sheet">
            <thead>
              <tr className="border-b border-amber-200 text-slate-600">
                <th className="py-1.5 pr-3 font-medium">Home</th>
                <th className="py-1.5 pr-3 font-medium">Carpet area</th>
                <th className="py-1.5 font-medium">Price</th>
              </tr>
            </thead>
            <tbody>
              {sheet.map((h, i) => (
                <tr key={i} className="border-b border-amber-100 last:border-0">
                  <td className="py-1.5 pr-3 font-semibold text-slate-900">{h.label}</td>
                  <td className="py-1.5 pr-3 text-slate-800">{h.carpet_sqft ? `${h.carpet_sqft.toLocaleString('en-IN')} sq ft` : '—'}</td>
                  <td className="py-1.5 font-semibold text-slate-900">{h.price_inr ? formatPrice(h.price_inr) : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
      {o.price_inr && o.transaction !== 'rent' ? (
        <p className="mt-2 text-sm text-slate-800" data-testid="own-cash">
          With a home loan, your own cash{priced ? ` for the ${priced.label}` : ''}: about <strong>{formatPrice(ownCash(o.price_inr))}</strong>
          <span className="mt-1 block text-xs text-slate-600">{OWN_CASH_NOTE}</span>
        </p>
      ) : null}
      {o.price_inr && o.transaction !== 'rent' && !/plot/i.test(o.property_type || '') ? (
        <CostBreakdown price={o.price_inr} stage={stage} sqft={sheet ? priced?.carpet_sqft : o.carpet_sqft}
          what={`${priced ? `the ${priced.label}` : 'this home'} at ${formatPrice(o.price_inr)}`} />
      ) : null}
      <p className="mt-2 text-xs text-slate-600">From {o.source || "the agent's listing"}{o.read_at ? `, ${longDay(o.read_at)}` : ''}. Prices change: confirm before you book.</p>
    </section>
  )
}

const HOUSE_AGENT = process.env.NEXT_PUBLIC_DEFAULT_AGENT_SLUG || 'avasetu'
// enquiries here go to the house account (HOUSE_AGENT), so the team is who gets back to the buyer
const ASK_NOTE = 'The Avasetu team calls or WhatsApps you back; we never share your number without your OK.'

function Row({ label, value, note }: { label: string; value: React.ReactNode; note?: string }) {
  return (
    <div className="min-w-0 border-b border-slate-200 py-3">
      <dt className="text-sm text-slate-600">{label}</dt>
      <dd className="mt-0.5 text-lg font-semibold text-slate-900">{value}</dd>
      {note && <dd className="mt-0.5 text-xs text-slate-500">{note}</dd>}
    </div>
  )
}

const H2 = 'text-xl font-semibold text-slate-900'
const n = (v: number | null | undefined) => (v == null ? null : v.toLocaleString('en-IN'))
const months = (m: number) => `${m} month${m === 1 ? '' : 's'}`

type Source = 'rera' | 'checked' | 'unchecked'

/** Where a block's facts come from: MahaRERA (the regulator's own record), gathered from other sources and checked by us, or not checked. */
function SourceTag({ kind, children }: { kind: Source; children?: React.ReactNode }) {
  const style = kind === 'rera' ? 'bg-emerald-50 text-emerald-800 ring-emerald-200'
    : kind === 'checked' ? 'bg-sky-50 text-sky-800 ring-sky-200' : 'bg-slate-100 text-slate-700 ring-slate-300'
  const text = children ?? (kind === 'rera' ? 'From MahaRERA' : kind === 'checked' ? 'Gathered and checked' : 'Not checked yet')
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${style}`}>
      <span aria-hidden>{kind === 'unchecked' ? '?' : '✓'}</span>{text}
    </span>
  )
}

function SectionHead({ id, title, kind, tag, sub }: { id: string; title: string; kind?: Source; tag?: React.ReactNode; sub?: boolean }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      {sub ? <h3 id={id} className="text-lg font-semibold text-slate-900">{title}</h3> : <h2 id={id} className={H2}>{title}</h2>}
      {kind && <SourceTag kind={kind}>{tag}</SourceTag>}
    </div>
  )
}

function Stat({ label, value, sub }: { label: string; value: React.ReactNode; sub?: React.ReactNode }) {
  return (
    <div className="min-w-0 rounded-xl bg-white/10 px-3 py-2.5 ring-1 ring-inset ring-white/15">
      <dt className="text-xs text-slate-300">{label}</dt>
      <dd className="mt-0.5 text-lg font-bold text-white">{value}</dd>
      {sub && <dd className="text-xs text-slate-300">{sub}</dd>}
    </div>
  )
}

/** "by Goyal Properties": the brand buyers know. The company MahaRERA has (often an SPV such as "Manjari Housing Projects LLP")
 *  is in the record's promoter row; in the headline it read as a second builder (design review 2026-10-25). */
function brandLine(p: RegisterProject): string | null {
  const brand = p.builder?.name || p.promoter
  return brand ? `by ${brand}` : null
}

/** The page's opening: the builder's first picture, then name, builder, area and registration on a dark band, with the headline
 *  numbers. The picture comes first on phones because a navy card of numbers was all the first screen showed (design review
 *  2026-10-25); it is only ever the builder's own picture, never an AI illustration standing in for a real one. */
function Hero({ p, price, photo }: { p: RegisterProject; price: { from: string; bhks: string } | null; photo: ProfilePicture | null }) {
  const d = p.details
  const moved = d?.completion_moved_months
  const stats: [string, React.ReactNode, React.ReactNode?][] = []
  // the agent's live sheet when there is one, else the portals' prices: one price on the page, never both
  const asked = price ?? askedPrices(p)
  if (asked) stats.push(['Asking price', `from ${asked.from}`, asked.bhks || undefined])
  if (p.completion_now) stats.push(['Completion filed', longDay(p.completion_now),
    moved != null ? (moved > 0 ? `moved ${months(moved)} later` : 'not moved') : undefined])
  if (d?.booked_pct != null) stats.push(['Booked', `${d.booked_pct}%`, p.units_booked != null && p.units_total ? `${n(p.units_booked)} of ${n(p.units_total)}` : undefined])
  else if (p.units_total) stats.push(['Units', n(p.units_total)])
  if (d?.towers) stats.push(['Towers', n(d.towers), d.max_floors ? `up to ${d.max_floors} floors` : undefined])
  const where = p.area ? `${p.area.name}, Pune` : [p.pune_place?.name ?? p.place, p.taluka, 'Pune district'].filter(Boolean).join(', ')
  const shown = displayName(p)
  const area = areaName(p)
  const aka = otherNames(p, [p.name])   // the legal name has its own line
  const legal = p.name.trim().toLowerCase() !== shown.trim().toLowerCase()
  return (
    <header id="project-hero" className={`overflow-hidden rounded-3xl bg-[#0f2340] text-white shadow-lg ${photo ? 'lg:grid lg:grid-cols-5' : ''}`}>
      {photo && (
        <figure className="relative m-0 aspect-[16/9] bg-slate-800 lg:order-last lg:col-span-2 lg:aspect-auto lg:h-full" data-testid="hero-photo">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={photo.url} alt={photo.alt} width={photo.width ?? undefined} height={photo.height ?? undefined}
            loading="eager" fetchPriority="high" decoding="async" className="h-full w-full object-cover" />
          <figcaption className="absolute bottom-2 right-2 rounded bg-black/60 px-2 py-0.5 text-xs text-white">
            The builder&apos;s picture{photo.site ? `, ${photo.site}` : ''}
          </figcaption>
        </figure>
      )}
      <div className="px-5 py-7 sm:px-8 sm:py-9 lg:col-span-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-400/15 px-3 py-1 text-xs font-semibold text-emerald-200 ring-1 ring-inset ring-emerald-300/30" data-testid="regno">
          <span aria-hidden>✓</span> MahaRERA registered <span className="font-mono font-normal text-slate-200">{p.regno}</span>
        </span>
        {p.completion_passed && <span className="rounded-full bg-amber-400/20 px-3 py-1 text-xs font-semibold text-amber-200">Completion date passed</span>}
        {/* plain words on the badge; how the stage is worked out (by dates, not a site check) is its title */}
        {p.stage && p.stage !== 'passed' && <span className="rounded-full bg-sky-400/20 px-3 py-1 text-xs font-semibold text-sky-100" title={STAGE_NOTE} data-testid="stage">{STAGE_LABEL[p.stage]}</span>}
        {p.sold_out && <span className="rounded-full bg-rose-400/20 px-3 py-1 text-xs font-semibold text-rose-100">Sold out on MahaRERA</span>}
      </div>
      <h1 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">{shown}{area && !shown.toLowerCase().includes(area.toLowerCase()) ? `, ${area}` : ''}</h1>
      {legal && <p className="mt-2 text-sm text-slate-300" data-testid="legal-name">Filed on MahaRERA as {p.name}</p>}
      {aka.length > 0 && <p className="mt-1 text-sm text-slate-300" data-testid="aka">Also known as: {aka.join(', ')}</p>}
      {p.group && (
        <p className="mt-2 text-base text-white" data-testid="group">
          Sold as <span className="font-semibold">{p.group.name}</span>{p.group.tower ? ` (${p.group.tower})` : ''} —{' '}
          <Link href={p.group.path} className="inline-flex min-h-[44px] items-center font-semibold text-amber-300 underline underline-offset-2">see all {p.group.towers} towers</Link>
        </p>
      )}
      <p className="mt-2 text-base text-slate-200">{[brandLine(p), where, p.pincode].filter(Boolean).join(' · ')}</p>
      {stats.length > 0 && (
        <dl className="mt-6 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {stats.map(([l, v, sub]) => <Stat key={l} label={l} value={v} sub={sub} />)}
        </dl>
      )}
      <div className="mt-6 flex flex-wrap gap-3">
        <a href="#enquire" className="inline-flex min-h-[48px] items-center rounded-full bg-amber-400 px-6 font-bold text-slate-900 no-underline">{PROJECT_CTA.full}</a>
        {p.maharera_url && (
          <a href={p.maharera_url} target="_blank" rel="noopener noreferrer" className="inline-flex min-h-[48px] items-center rounded-full px-5 font-semibold text-white no-underline ring-1 ring-inset ring-white/30 hover:bg-white/10">
            MahaRERA record<span className="sr-only"> (opens in a new tab)</span>
          </a>
        )}
      </div>
      </div>
    </header>
  )
}

const CHECK_KEYS = ['maharera_general', 'buildings', 'places', 'text'] as const
const CHECK_NAMES: Record<string, string> = { maharera_general: 'Dates and homes booked', buildings: 'Buildings and wings',
  places: 'Location and nearby', text: 'Description' }

/** Every check behind the page: what came from MahaRERA, what we gathered elsewhere and checked, and what is still waiting. */
function ChecksPanel({ p }: { p: RegisterProject }) {
  const byKey = Object.fromEntries((p.checks ?? []).map((c) => [c.key, c])) as Record<string, EnrichCheck | undefined>
  const rows: { label: string; kind: Source; note: string }[] = [
    { label: 'Registration, promoter, pincode', kind: 'rera', note: p.listed_or_updated ? `MahaRERA listing, updated ${longDay(p.listed_or_updated)}` : 'MahaRERA listing' },
  ]
  for (const key of CHECK_KEYS) {
    const c = byKey[key]
    const label = CHECK_NAMES[key]
    const fromRera = key === 'maharera_general' || key === 'buildings'
    if (!c) rows.push({ label, kind: 'unchecked', note: 'Waiting for its turn; this page fills in by itself' })
    else rows.push({ label, kind: c.ok ? (fromRera ? 'rera' : 'checked') : 'unchecked',
      note: (c.ok ? '' : 'Not confirmed: ') + c.note + (c.at ? ` (${longDay(c.at)})` : '') })
  }
  const ok = rows.filter((r) => r.kind !== 'unchecked').length
  return (
    <section aria-labelledby="checks-title" className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5" data-testid="checks">
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="checks-title" className="text-lg font-semibold text-slate-900">How we checked this page</h2>
        <span className="text-sm font-semibold text-slate-700">{ok} of {rows.length}</span>
      </div>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100" aria-hidden>
        <div className="h-full rounded-full bg-emerald-500" style={{ width: `${Math.round((100 * ok) / rows.length)}%` }} />
      </div>
      <ul className="mt-3 list-none space-y-3 p-0">
        {rows.map((r) => (
          <li key={r.label}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="font-medium text-slate-900">{r.label}</span>
              <SourceTag kind={r.kind} />
            </div>
            <p className="mt-0.5 text-xs text-slate-600">{r.note}</p>
          </li>
        ))}
      </ul>
      <p className="mt-3 border-t border-slate-100 pt-3 text-xs text-slate-600">
        <strong>From MahaRERA</strong>: the regulator&apos;s own record. <strong>Gathered and checked</strong>: found in other public
        sources and checked by us against MahaRERA and the map. <strong>Not checked yet</strong>: still waiting, or could not be confirmed.
      </p>
    </section>
  )
}

/** 'Check before you book': the weak points the record shows, each with what to ask (backend areastats/cautions.py). */
function Cautions({ p }: { p: RegisterProject }) {
  const rows = p.cautions ?? []
  if (!rows.length) return null
  const web = rows.some((c) => c.source === 'web')
  return (
    <section aria-labelledby="cautions-title" data-testid="cautions">
      <SectionHead id="cautions-title" title="Check before you book" kind={web ? 'checked' : 'rera'}
        tag={web ? 'From MahaRERA and checked sites' : 'From MahaRERA'} />
      <ul className="mt-3 list-none space-y-2 p-0">
        {rows.map((c) => (
          <li key={c.key} className="flex gap-3 rounded-xl border border-amber-200 bg-amber-50 p-3 text-slate-800">
            <span aria-hidden className="font-bold text-amber-700">!</span><span>{c.text}</span>
          </li>
        ))}
      </ul>
      <p className="mt-2 text-xs text-slate-600">Worked out from the facts on this page, not an opinion of the project. Every project has some; these are the ones its record shows.</p>
    </section>
  )
}

function BuildingsTable({ p }: { p: RegisterProject }) {
  const rows = p.buildings ?? []
  if (!rows.length) return null
  return (
    <section aria-labelledby="buildings-title">
      <SectionHead id="buildings-title" title="Buildings" kind="rera" sub />
      <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr><th className="px-3 py-2 font-semibold">Building</th><th className="px-3 py-2 font-semibold">Floors</th><th className="px-3 py-2 font-semibold">Homes</th><th className="px-3 py-2 font-semibold">Other</th></tr>
          </thead>
          <tbody>
            {rows.map((b, i) => (
              <tr key={i} className="border-t border-slate-200">
                <td className="px-3 py-2 font-semibold text-slate-900">{[b.name, b.wing].filter(Boolean).join(', ') || `Building ${i + 1}`}</td>
                <td className="px-3 py-2">{n(b.floors) ?? '-'}</td>
                <td className="px-3 py-2">{n(b.units_residential) ?? '-'}</td>
                <td className="px-3 py-2">{n(b.units_other) ?? '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-slate-500">As filed with MahaRERA (sanctioned floors).</p>
    </section>
  )
}

/** One project that MahaRERA holds tower by tower or phase by phase: every registration, each with its own dates and bookings. */
function TowersTable({ p }: { p: RegisterProject }) {
  const rows = p.towers ?? []
  if (rows.length < 2) return null
  const total = rows.reduce((s, t) => s + (t.units_total ?? 0), 0)
  const sold = rows.every((t) => t.units_booked != null) ? rows.reduce((s, t) => s + (t.units_booked ?? 0), 0) : null
  return (
    <section aria-labelledby="towers-title" data-testid="towers">
      <SectionHead id="towers-title" title={`Towers and phases (${rows.length} registrations)`} kind="rera" sub />
      <p className="mt-2 text-slate-800">
        MahaRERA holds {displayName(p)} as {rows.length} registrations.
        {total > 0 && <> Together they list {n(total)} homes{sold != null ? `, ${n(sold)} booked` : ''}.</>}
      </p>
      <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr><th className="px-3 py-2 font-semibold">Registration</th><th className="px-3 py-2 font-semibold">Completion filed</th><th className="px-3 py-2 font-semibold">Booked</th></tr>
          </thead>
          <tbody>
            {rows.map((t) => (
              <tr key={t.regno} className="border-t border-slate-200 align-top">
                <td className="px-3 py-2">
                  <span className="block font-semibold text-slate-900">{t.name}</span>
                  {t.maharera_url ? <a href={t.maharera_url} target="_blank" rel="noopener noreferrer" className="font-mono text-xs text-[#0f2340] underline underline-offset-2">{t.regno}<span className="sr-only"> (opens in a new tab)</span></a>
                    : <span className="font-mono text-xs text-slate-600">{t.regno}</span>}
                </td>
                <td className="px-3 py-2">{t.completion_now ? longDay(t.completion_now) : '-'}
                  {t.completion_at_registration && t.completion_now && t.completion_at_registration !== t.completion_now &&
                    <span className="block text-xs text-slate-500">at registration {longDay(t.completion_at_registration)}</span>}</td>
                <td className="px-3 py-2">{t.units_total ? (t.units_booked != null ? `${n(t.units_booked)} of ${n(t.units_total)}` : `${n(t.units_total)} homes`) : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-slate-500">Each row is its own MahaRERA registration, as filed.</p>
    </section>
  )
}

/** The tower and building tables, folded: long on a big project and the numbers a buyer checks last, so the page stays short on a
 *  phone (design review 2026-10-25: 15,700 px). Folded content is still in the page, so search engines read it. */
function TowerByTower({ p }: { p: RegisterProject }) {
  const towers = (p.towers ?? []).length >= 2
  const buildings = (p.buildings ?? []).length > 0
  if (!towers && !buildings) return null
  return (
    <details className="group rounded-2xl border border-slate-200 bg-white p-4 sm:p-5" data-testid="tower-by-tower">
      <summary className="flex min-h-[44px] cursor-pointer items-center justify-between gap-2 text-xl font-semibold text-slate-900">
        <h2 className="m-0 text-xl font-semibold">Tower by tower</h2>
        <span className="text-sm font-normal text-slate-600">
          {[towers ? `${p.towers!.length} registrations` : null, buildings ? `${p.buildings!.length} building${p.buildings!.length === 1 ? '' : 's'}` : null].filter(Boolean).join(', ')}
        </span>
      </summary>
      <div className="mt-4 space-y-8">
        <TowersTable p={p} />
        <BuildingsTable p={p} />
      </div>
    </details>
  )
}

type Near = { label: string; name: string; km: number }

/** The map: OpenStreetMap around the position we checked against the pincode; without one, a map search by name and area, marked
 *  as not checked. Nearby places (from the gathered fact sheet, OpenStreetMap distances) sit beside it. */
function MapBox({ p, nearby }: { p: RegisterProject; nearby: Near[] }) {
  const m = p.map
  const where = [p.name, p.area?.name ?? p.place, 'Pune', p.pincode].filter(Boolean).join(', ')
  let src: string, link: string
  if (m) {
    const d = 0.01
    const bbox = [m.lon - d, m.lat - d, m.lon + d, m.lat + d].map((x) => x.toFixed(5)).join(',')
    src = `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${m.lat.toFixed(5)},${m.lon.toFixed(5)}`
    link = `https://www.openstreetmap.org/?mlat=${m.lat.toFixed(5)}&mlon=${m.lon.toFixed(5)}#map=15/${m.lat.toFixed(5)}/${m.lon.toFixed(5)}`
  } else {
    src = `https://maps.google.com/maps?q=${encodeURIComponent(where)}&z=14&output=embed`
    link = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(where)}`
  }
  const km = (x: number) => `${Number.isInteger(x) ? x : x.toFixed(1)} km`
  return (
    <section aria-labelledby="map-title">
      <SectionHead id="map-title" title="Location" kind={m ? 'checked' : 'unchecked'} tag={m ? 'Position checked' : 'Position not checked'} />
      <div className={`mt-3 grid gap-3 ${nearby.length ? 'lg:grid-cols-5' : ''}`}>
        <iframe title={`Map around ${p.name}`} src={src} loading="lazy" referrerPolicy="no-referrer-when-downgrade"
          className={`h-64 w-full rounded-xl border border-slate-200 sm:h-80 ${nearby.length ? 'lg:col-span-3' : ''}`} />
        {nearby.length > 0 && (
          <ul className="list-none space-y-2 p-0 lg:col-span-2" data-testid="nearby">
            {nearby.slice(0, 8).map((x) => (
              <li key={x.label + x.name} className="flex items-baseline justify-between gap-3 rounded-lg bg-slate-50 px-3 py-2 text-sm">
                <span className="min-w-0"><span className="text-slate-600">{x.label}</span><span className="block truncate font-semibold text-slate-900">{x.name}</span></span>
                <span className="whitespace-nowrap font-semibold text-slate-900">{km(x.km)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
      <p className="mt-2 text-xs text-slate-500">
        {m && p.map_from === 'google' ? "The project's pin on Google Maps, checked against its MahaRERA name and pincode."
          : m ? "Approximate area from OpenStreetMap, checked to be near the project's pincode; not the exact plot."
          : "A map search for the project's name and area; we have not checked this position yet."}
        {nearby.length > 0 && ' Distances are straight-line; the drive is longer.'}{' '}
        <a href={link} target="_blank" rel="noopener noreferrer" className="text-[#0f2340] underline underline-offset-2">Open the map<span className="sr-only"> (opens in a new tab)</span></a>
      </p>
    </section>
  )
}

function BuilderBox({ p }: { p: RegisterProject }) {
  const b = p.builder
  if (!b || !b.count) return null
  const others = b.projects.filter((x) => !x.this)
  return (
    <section aria-labelledby="builder-title">
      <SectionHead id="builder-title" title="About the builder" kind="rera" tag="From MahaRERA records" />
      <p className="mt-2 text-slate-800">
        {b.name} has {b.count} project{b.count === 1 ? '' : 's'} in our MahaRERA register for Pune.
        {b.record_ok ? <> {b.moved_later} of {b.with_dates} with both dates moved the completion date 3 months or more later{b.avg_months_later ? `, by ${months(b.avg_months_later)} on average` : ''}.</>
          : b.with_dates > 0 ? <> Only {b.with_dates} with both dates: too few to judge their record.</> : null}
      </p>
      {others.length > 0 && (
        <ul className="mt-3 space-y-1 p-0">
          {others.map((x) => (
            <li key={x.regno} className="list-none">
              {x.slug ? <Link href={`/projects/${x.slug}`} className="inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">{x.name}</Link>
                : <span className="font-semibold text-slate-900">{x.name}</span>}
              <span className="ml-2 text-sm text-slate-600">
                {x.completion_now ? `completion filed ${longDay(x.completion_now)}` : x.regno}
                {x.months_later ? `, moved ${months(x.months_later)} later` : ''}
              </span>
            </li>
          ))}
        </ul>
      )}
      {p.builder_slug && b.count > 1 && (
        <p className="mt-2"><Link href={`/builders/${p.builder_slug}`} className="inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">All {b.count} projects by {b.name} in Pune</Link></p>
      )}
      <p className="mt-2 text-xs text-slate-500">Counted from MahaRERA records we hold; projects outside Pune are not included.</p>
    </section>
  )
}

function FaqBox({ faq }: { faq: Faq[] }) {
  if (!faq.length) return null
  return (
    <section aria-labelledby="faq-title">
      <h2 id="faq-title" className={H2}>FAQ</h2>
      <div className="mt-3 space-y-2">
        {faq.map((f) => (
          <details key={f.q} className="rounded-xl border border-slate-200 bg-white p-3">
            <summary className="min-h-[44px] cursor-pointer py-2 font-semibold text-slate-900">{f.q}</summary>
            <p className="mt-1 text-slate-800">{f.a}</p>
          </details>
        ))}
      </div>
    </section>
  )
}

/** Avasetu's own page for a MahaRERA project: our facts first (each with source and date), then the official record. */
export default function RegisterProjectPage({ p, siteUrl, facts, lists = [], whatsappUrl }: { p: RegisterProject; siteUrl: string; facts: PropertyFactsView | null; lists?: FacetLink[]; whatsappUrl?: string | null }) {
  const url = `${siteUrl}/projects/${p.slug}`
  const moved = p.completion_now && p.completion_at_registration && p.completion_now !== p.completion_at_registration
  const shown = displayName(p)
  // GST is added only while MahaRERA's completion date is ahead; past it (or not yet read) the OC decides, so the page asks
  const stage: Stage = p.completion_now && !p.completion_passed ? 'building' : 'completion_passed'
  // the Pune place page listing this project's neighbours (every Pune district project has one)
  const placeName = p.pune_place?.name ?? null
  const placeHref = p.pune_place ? placePath(p.pune_place.key.replace(/_/g, '-')) : null
  // the same copies the gallery keeps (a render saved twice shows once), so the hero's picture is the one the gallery skips
  const ownPhotos = distinctPhotos(p.profile?.photos ?? []).filter((x) => (x.source ?? 'builder') === 'builder' && !!x.url)
  // the hero's picture: the builder's first one; the gallery below starts from the next, so it is not shown twice
  const heroPhoto = ownPhotos[0] ?? null
  const nearby = (facts as unknown as { nearby?: Near[] } | null)?.nearby ?? []
  const offer = (facts as unknown as { offer?: Offer } | null)?.offer
  // the agent's live price sheet is the page's one price: the hero quotes it and the portals' prices are not shown beside it
  const price = offerPrice(offer)
  const faq = projectFaq(p, nearby, offer?.price_inr ? `${offer.homes && offer.homes.length > 1 ? 'from ' : ''}${formatPrice(offer.price_inr)}` : null)
  // the dated answer AI answers and snippets quote, first in the page's text; only once the record's dates or homes are read
  const answer = p.completion_now || p.units_total ? registerAnswer(p, price) : null
  const updated = projectUpdated(p)
  const d = p.details
  const movedMonths = d?.completion_moved_months
  const byPromoter = (p.same_promoter ?? []).filter((x) => x.slug && x.slug !== p.slug)
  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:py-8" style={AVASETU_SITE_VARS}>
      {registerProjectJsonLd({ p, siteUrl, faq, photos: ownPhotos, offer, updated }).map((x, i) => (
        <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(x) }} />
      ))}
      <nav aria-label="Breadcrumb" className="mb-4 text-sm">
        <Link href="/" className="text-[#0f2340] underline underline-offset-2">Home</Link>
        <span aria-hidden className="px-1 text-slate-400">/</span>
        <Link href="/projects" className="text-[#0f2340] underline underline-offset-2">Projects</Link>
        {p.area && <> <span aria-hidden className="px-1 text-slate-400">/</span> <Link href={`/localities/${p.area.slug}`} className="text-[#0f2340] underline underline-offset-2">{p.area.name}</Link></>}
        {!p.area && placeName && placeHref && <> <span aria-hidden className="px-1 text-slate-400">/</span> <Link href={placeHref} className="text-[#0f2340] underline underline-offset-2">{placeName}</Link></>}
      </nav>

      <Hero p={p} price={price} photo={heroPhoto} />

      {/* pictures first: what a buyer looks for before reading (owner 2026-10-20) */}
      <div className="mt-8"><ProjectProfile profile={p.profile} name={shown} part="photos" skip={heroPhoto?.url} /></div>

      <div className="mt-8 grid gap-8 lg:grid-cols-3">
        <div className="min-w-0 space-y-10 lg:col-span-2">
          {/* the agent's price sheet right after the pictures, at every width: in the side column a phone reached it at ~11,200 px
              (design review 2026-10-25) */}
          <OfferBox facts={facts} stage={stage} />
          <section aria-labelledby="about-title">
            <SectionHead id="about-title" title={`About ${shown}`} kind={p.text_checked ? 'checked' : 'rera'}
              tag={p.text_checked ? 'Written from checked facts' : 'From MahaRERA'} />
            {updated && <p className="mt-1 text-sm text-slate-600" data-testid="updated">Updated {longDay(updated)}</p>}
            {answer && <p className="mt-3 text-lg font-medium leading-relaxed text-slate-900" data-testid="project-answer">{answer}</p>}
            <p className="mt-3 text-lg leading-relaxed text-slate-800" data-testid="paragraph">{p.paragraph}</p>
            {(p.sections ?? []).map((x) => (
              <div key={x.heading} className="mt-5">
                <h3 className="text-base font-semibold text-slate-900">{x.heading}</h3>
                <p className="mt-1.5 leading-relaxed text-slate-800">{x.text}</p>
              </div>
            ))}
          </section>

          <ProjectProfile profile={p.profile} name={shown} part="highlights" />
          {!price && <PriceBox prices={p.prices} name={shown} stage={stage} />}
          <ProjectProfile profile={p.profile} name={shown} part="plans" lead={{ agentSlug: HOUSE_AGENT, agentName: 'Avasetu',
            topic: `${p.name} (MahaRERA ${p.regno})`, waMessage: `Hi, I want to know about ${p.name} (MahaRERA ${p.regno}): ${url}` }} />

          {/* one record: the register's facts and MahaRERA's buildings summary used to be two sections ("The record" and
              "Project details") repeating the same dates and counts (design review 2026-10-25) */}
          <section aria-labelledby="facts-title">
            <SectionHead id="facts-title" title="The record" kind="rera" tag={p.details_read_at ? `From MahaRERA, read ${longDay(p.details_read_at)}` : 'From MahaRERA'} />
            <dl className="mt-2 grid gap-x-6 sm:grid-cols-2">
              {p.completion_now && <Row label="Completion date filed with MahaRERA" value={longDay(p.completion_now)}
                note={moved ? `At registration: ${longDay(p.completion_at_registration)}.` : movedMonths === 0 ? 'Not moved since registration.' : undefined} />}
              {p.units_total ? <Row label="Homes booked" value={p.units_booked != null ? `${p.units_booked} of ${p.units_total}` : `Not reported (${p.units_total} homes)`} /> : null}
              {d?.towers ? <Row label="Towers" value={n(d.towers)} note={d.max_floors ? `The tallest has ${d.max_floors} floors.` : undefined} /> : null}
              {/* the total is in "Homes booked" already: a row of its own only for the split, or when bookings are not there */}
              {d?.units_total && (d.units_other || !p.units_total) ? <Row label="Units" value={n(d.units_total)}
                note={d.units_other ? `${n(d.units_residential ?? d.units_total - d.units_other)} homes, ${n(d.units_other)} shops or offices.` : undefined} /> : null}
              {d?.registered_on && <Row label="Registered on" value={longDay(d.registered_on)} />}
              <Row label="MahaRERA registration" value={p.regno} note={p.listed_or_updated ? `Listed or updated on MahaRERA ${longDay(p.listed_or_updated)}.` : undefined} />
              {p.promoter && <Row label="Promoter (builder)" value={p.promoter} />}
              {p.pincode && <Row label="Pincode" value={p.pincode} />}
            </dl>
            {p.completion_passed && <p className="mt-3 rounded-xl bg-amber-50 p-3 text-sm text-amber-900">The filed completion date has passed. Ask for the occupancy certificate (OC) before you book.</p>}
            {!p.completion_now && <p className="mt-3 text-sm text-slate-600">We are still reading this project&apos;s details from MahaRERA; this page fills in by itself.</p>}
          </section>

          <AskPrompt name={shown} note={ASK_NOTE} whatsappUrl={whatsappUrl} />

          <Cautions p={p} />
          <TowerByTower p={p} />
          <MapBox p={p} nearby={nearby} />
          <BuilderBox p={p} />
          <WebFactsBox web={p.web_facts} name={displayName(p)} />
          <FaqBox faq={faq} />

          {byPromoter.length > 0 && p.promoter && (
            <section aria-labelledby="promoter-title" data-testid="same-promoter">
              <h2 id="promoter-title" className={H2}>More by {p.promoter}</h2>
              <ul className="mt-3 grid list-none gap-2 p-0 sm:grid-cols-2">
                {byPromoter.map((s) => (
                  <li key={s.slug}>
                    <Link href={`/projects/${s.slug}`} className="block min-h-[44px] rounded-xl border border-slate-200 bg-white px-3 py-2 no-underline hover:border-[#0f2340]">
                      <span className="block font-semibold text-[#0f2340]">{displayName(s)}</span>
                      {s.completion_now && <span className="text-sm text-slate-600">possession {monthYear(s.completion_now)}</span>}
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {p.same_area.length > 0 && (p.area || placeName) && (
            <section aria-labelledby="same-title">
              <h2 id="same-title" className={H2}>Other projects in {p.area?.name ?? placeName}</h2>
              <ul className="mt-3 grid list-none gap-2 p-0 sm:grid-cols-2">
                {p.same_area.map((s) => (
                  <li key={s.slug}>
                    <Link href={`/projects/${s.slug}`} className="block min-h-[44px] rounded-xl border border-slate-200 bg-white px-3 py-2 no-underline hover:border-[#0f2340]">
                      <span className="block font-semibold text-[#0f2340]">{s.name}</span>
                      {s.completion_now && <span className="text-sm text-slate-600">completion filed {longDay(s.completion_now)}</span>}
                    </Link>
                  </li>
                ))}
              </ul>
              <div className="mt-3 flex flex-wrap gap-x-5">
                {placeHref && <Link href={placeHref} className="inline-flex min-h-[44px] items-center text-[#0f2340] underline underline-offset-2">All projects and flats in {placeName ?? p.area?.name}</Link>}
                {/* the place's lists (docs/plan/area-intent-pages.md): links into them from every project page in the place */}
                {lists.map((f) => (
                  <Link key={f.path} href={f.path} className="inline-flex min-h-[44px] items-center text-[#0f2340] underline underline-offset-2" data-testid="facet-link">
                    {f.label} in {placeName ?? p.area?.name}
                  </Link>
                ))}
                {p.area && <Link href={`/localities/${p.area.slug}`} className="inline-flex min-h-[44px] items-center text-[#0f2340] underline underline-offset-2">{p.area.name} area guide</Link>}
                {p.near_guide && <Link href={p.near_guide.path} className="inline-flex min-h-[44px] items-center text-[#0f2340] underline underline-offset-2" data-testid="near-guide">Near {p.near_guide.name} ({p.near_guide.km} km): neighbourhood guide</Link>}
              </div>
            </section>
          )}
        </div>

        <aside className="min-w-0 space-y-6 lg:sticky lg:top-20 lg:self-start">
          {/* the side column stays in view on desktop, so the ask does too; phones get the bottom bar instead */}
          <div className="hidden lg:block"><AskPrompt name={shown} note={ASK_NOTE} whatsappUrl={whatsappUrl} compact /></div>
          <ChecksPanel p={p} />
          <VerifiedFacts f={facts} hideNearby />
        </aside>
      </div>

      <div className="mt-10 space-y-8">
      <EnquiryForm agentSlug={HOUSE_AGENT} agentName="Avasetu" topic={`${p.name} (MahaRERA ${p.regno})`}
        waMessage={`Hi, I want to know about ${p.name} (MahaRERA ${p.regno}): ${url}`}
        title={PROJECT_CTA.formTitle(p.name)} note={ASK_NOTE} submitLabel={PROJECT_CTA.full} />

      <footer className="border-t border-slate-200 pt-4 text-sm text-slate-600">
        Source: {p.source}.{' '}
        {p.maharera_url && <a href={p.maharera_url} target="_blank" rel="noopener noreferrer" className="text-[#0f2340] underline underline-offset-2">See the official MahaRERA record<span className="sr-only"> (opens in a new tab)</span></a>}
        {' '}Facts can change; check the record and your agreement before you book.
      </footer>
      </div>
      <StickyJoinBar watchId="project-hero" formId="enquire" label={PROJECT_CTA.short} whatsappUrl={whatsappUrl} whatsappLabel="WhatsApp" />
    </div>
  )
}
