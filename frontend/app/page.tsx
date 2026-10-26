import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import NewsSection from '@/components/news/NewsSection'
import ProjectRail from '@/components/site/ProjectRail'
import ProjectSearch from '@/components/site/ProjectSearch'
import { AGENTS_PATH, agentAnchorForward, buyerEnquirePath } from '@/components/marketing/siteLinks'
import { getCityStats, longDate } from '@/components/localities/areaStats'
import { getMarketingConfig } from '@/lib/marketing/config'
import { LOCALITIES, TIER_LABELS, localitiesByTier } from '@/lib/marketing/localities'
import { jsonLdString, organizationJsonLd, pageMetadata } from '@/lib/marketing/seo'
import { socialLinks } from '@/lib/marketing/social'
import { BRAND_NAME } from '@/lib/brand'
import { getFacetQuiet, getFacets } from '@/lib/site/facets'
import { getBuilders, getSpotlight } from '@/lib/site/hubs'
import { getRegisterPlaces, placePath } from '@/lib/site/register'

// The buyers' home (2026-10-22; the agents' home moved to /agents). One topic for Google and for people: new projects in Pune,
// checked on MahaRERA. Every section is links into the pages that answer buyers' searches: areas, the project lists, the hottest
// projects, builders. Each block hides itself when its data is not there (an outage, or the build with no API), so the page never
// breaks; kept 5 minutes like the lists it links.
export const revalidate = 300

// Google shows about 70 characters of a title and 160 of a description: both fit, so none of the facts is cut off
const TITLE = 'New Projects in Pune, MahaRERA Checked: Possession, Bookings, Builders'
const DESCRIPTION = 'Every new project in Kharadi, Wagholi, Lohegaon, Hinjawadi, Wakad and more: possession filed with MahaRERA, whether it moved, homes booked, builders\' records.'

export const metadata: Metadata = pageMetadata(getMarketingConfig(), {
  title: TITLE,
  description: DESCRIPTION,
  path: '/',
  image: { path: '/brand/og-landing.jpg', width: 1200, height: 630, alt: `${BRAND_NAME}: new projects in Pune, checked on MahaRERA` },
})

const wrap = 'mx-auto max-w-5xl px-4'
const section = 'py-10 sm:py-14'
const h2 = 'text-2xl font-extrabold tracking-tight text-[#0f2340] sm:text-3xl'
const card = 'block h-full rounded-2xl border border-slate-200 bg-white p-4 no-underline hover:border-[#0f2340]'
const chip = 'inline-flex min-h-[44px] items-center rounded-full border border-slate-300 bg-white px-4 text-sm font-semibold text-[#0f2340] no-underline hover:border-[#0f2340]'

export default async function BuyerHome() {
  const cfg = getMarketingConfig()
  const [city, places, facets, hot, builders] = await Promise.all([getCityStats(), getRegisterPlaces(), getFacets(), getSpotlight(), getBuilders()])
  const placeOf = (l: { key: string; name: string }) => places.find((p) => p.key === l.key || p.name.toLowerCase() === l.name.toLowerCase())
  // a list's own label says what it is, not where ("New launch projects"): side by side here, each chip has to name its area
  const where = (f: { place: string; place_slug: string }) => places.find((p) => p.key === f.place)?.name
    ?? f.place_slug.split('-').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
  // our areas first, in the area list's order (east Pune leads: owner 2026-10-26, "our main target for now is east Pune"),
  // then every other place, biggest list first; sorted by size alone, Moshi's Top list was the home page's row of cards
  const ours = (key: string) => { const i = LOCALITIES.findIndex((l) => l.key === key); return i < 0 ? LOCALITIES.length : i }
  const byOurs = (a: { place: string; count: number }, b: { place: string; count: number }) => ours(a.place) - ours(b.place) || b.count - a.count
  const launches = facets.filter((f) => f.intent === 'new-launches' && f.indexable && !f.builder && !f.possession && !f.bhk)
    .sort(byOurs).slice(0, 12)
  const ready = facets.filter((f) => f.intent === 'ready-to-move' && f.indexable && !f.builder && !f.possession && !f.bhk)
    .sort(byOurs).slice(0, 8)
  // the Top lists rank homes a buyer can still buy (areastats/pages.py buyable): our first area's as cards, every area's as a chip
  const tops = facets.filter((f) => f.intent === 'top' && f.indexable && !f.builder && !f.possession && !f.bhk)
    .sort(byOurs).slice(0, 8)
  const topList = tops.length ? await getFacetQuiet(tops[0].place_slug, ['top']) : null
  const brands = builders.filter((b) => b.indexable).sort((a, b) => Number(!!b.brand) - Number(!!a.brand) || b.projects - a.projects).slice(0, 12)
  const tracked = city?.areas.reduce((n, a) => n + a.projects, 0) ?? 0
  const ld = [
    organizationJsonLd(cfg, `${BRAND_NAME} (आवास + सेतु: home + bridge) lists every new project in Pune's main areas with its MahaRERA record: possession filed, homes booked and builders' delivery records, and connects buyers with local agents.`, Object.values(socialLinks())),
    { '@context': 'https://schema.org', '@type': 'WebSite', name: cfg.businessName, url: cfg.siteUrl,
      potentialAction: { '@type': 'SearchAction', target: { '@type': 'EntryPoint', urlTemplate: `${cfg.siteUrl}/projects?q={search_term_string}` },
        'query-input': 'required name=search_term_string' } },
  ]

  return (
    <MarketingShell hot={false}>
      {/* old links to the agents' sections that were on this page (/#invite, /#faq) go on to /agents */}
      <script dangerouslySetInnerHTML={{ __html: agentAnchorForward() }} />
      {ld.map((x, i) => <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(x) }} />)}

      <section aria-labelledby="home-title" className="bg-gradient-to-b from-[#0f2340] to-[#183a5d] pb-10 pt-10 text-white sm:pt-14">
        <div className={wrap}>
          <p className="text-sm font-bold uppercase tracking-wide text-[#f5c75e]">Pune homes, checked on MahaRERA</p>
          <h1 id="home-title" className="mt-2 text-[2rem] font-extrabold leading-tight [text-wrap:balance] sm:text-5xl">New projects in Pune, with the facts ads leave out</h1>
          <p className="mt-3 max-w-2xl text-lg text-white/85">
            The possession date each builder filed and whether it moved, how many homes are booked, and each builder&apos;s delivery record.
            {tracked > 0 && city ? <> {tracked.toLocaleString('en-IN')} projects in our areas, read from MahaRERA on {longDate(city.asOf)}.</> : null}
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <a href={buyerEnquirePath()} className="inline-flex min-h-[48px] items-center rounded-xl bg-[#f0b440] px-5 font-bold text-[#0f2340] no-underline hover:bg-[#f5c75e]">Tell us what you need</a>
            {cfg.whatsappUrl && (
              <a href={cfg.whatsappUrl} target="_blank" rel="noopener noreferrer" className="inline-flex min-h-[48px] items-center rounded-xl border-2 border-white/70 px-5 font-bold text-white no-underline hover:bg-white/10">
                Ask on WhatsApp<span className="sr-only"> (opens in a new tab)</span>
              </a>
            )}
          </div>
        </div>
      </section>

      <div className={wrap}>
        <ProjectSearch />
      </div>

      {hot.length > 0 && (
        <section aria-labelledby="hot-title" className={wrap + ' pt-10'} data-testid="home-hot">
          <h2 id="hot-title" className={h2}>Hot right now</h2>
          {/* swiped on a phone, a grid on a laptop; it never moves by itself (ProjectRail) */}
          <ul className="-mx-4 mt-4 flex list-none snap-x snap-mandatory gap-3 overflow-x-auto px-4 pb-2 sm:mx-0 sm:grid sm:grid-cols-2 sm:overflow-visible sm:px-0 lg:grid-cols-3">
            {hot.map((p) => (
              <li key={p.slug} className="w-[78%] max-w-[300px] shrink-0 snap-start sm:w-auto sm:max-w-none">
                <Link href={`/projects/${p.slug}`} className={card}>
                  <span className="block font-bold text-[#0f2340]">{p.name}</span>
                  {p.area && <span className="block text-sm text-slate-600">{p.area}, Pune</span>}
                  {' '}<span className="mt-1 block text-sm text-slate-800">{p.note || `${p.fact} (${p.source})`}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {topList && (
        <div className={wrap}>
          <ProjectRail id="home-top" title={`Top projects in ${topList.place.name} you can still buy`} sub="Most homes booked first, with 10 or more open (MahaRERA)"
            href={topList.path} count={topList.count} rows={topList.rows} ranked />
        </div>
      )}

      <section aria-labelledby="areas-title" className={wrap + ' ' + section}>
        <h2 id="areas-title" className={h2}>Projects by area</h2>
        {(['it', 'affordable'] as const).map((tier) => (
          <div key={tier} className="mt-6">
            <h3 className="text-lg font-bold text-slate-900">{TIER_LABELS[tier].title}</h3>
            <p className="text-sm text-slate-600">{TIER_LABELS[tier].blurb}</p>
            <ul className="mt-3 grid list-none gap-3 p-0 sm:grid-cols-2 lg:grid-cols-4" data-testid={`home-areas-${tier}`}>
              {localitiesByTier(tier).map((l) => {
                const place = placeOf(l)
                const live = place && place.indexable > 0
                return (
                  <li key={l.slug} className="relative flex flex-col rounded-2xl border border-slate-200 bg-white p-4 hover:border-[#0f2340]">
                    {/* the whole card opens the area page (a tap beside the title did nothing: owner 2026-10-26); its name is the
                        page's own ("Flats and residential projects in Kharadi"), "new projects" being the new-launches list's search */}
                    <Link href={live ? placePath(place.slug) : `/localities/${l.slug}`}
                      className="font-bold text-[#0f2340] underline-offset-2 after:absolute after:inset-0 after:rounded-2xl after:content-[''] hover:underline">
                      {live ? `Projects in ${l.name}` : l.name}
                    </Link>
                    <span className="mt-1 text-sm text-slate-600">{l.tagline}</span>
                    {/* the projects a buyer of a new home looks at: every registration ever (303 in Kharadi) counted old ones too */}
                    {place && (place.current ?? place.projects) > 0 && <span className="mt-1 text-sm font-semibold text-slate-800">
                      {place.current != null ? `${place.current} being built or just finished` : `${place.projects} projects on MahaRERA`}</span>}
                    <Link href={`/localities/${l.slug}`} className="relative z-10 mt-auto inline-flex min-h-[44px] items-center pt-2 text-sm font-semibold text-[#0f2340] underline underline-offset-2">
                      Living in {l.name}
                    </Link>
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
        <p className="mt-5"><Link href="/projects" className="font-semibold text-[#0f2340] underline underline-offset-4">All projects in Pune, by place</Link></p>
      </section>

      {(launches.length > 0 || ready.length > 0 || tops.length > 0) && (
        <section aria-labelledby="lists-title" className={'border-y border-[#ead9ae] bg-[#fbf6ea] ' + section}>
          <div className={wrap}>
            <h2 id="lists-title" className={h2}>Top projects, new launches and ready homes</h2>
            {tops.length > 0 && (
              <ul className="mt-4 flex list-none flex-wrap gap-2 p-0" data-testid="home-tops">
                {tops.map((f) => <li key={f.path}><Link href={f.path} className={chip}>Top projects in {where(f)} ({f.count})</Link></li>)}
              </ul>
            )}
            {launches.length > 0 && (
              <ul className="mt-3 flex list-none flex-wrap gap-2 p-0" data-testid="home-launches">
                {launches.map((f) => <li key={f.path}><Link href={f.path} className={chip}>New launches in {where(f)} ({f.count})</Link></li>)}
              </ul>
            )}
            {ready.length > 0 && (
              <ul className="mt-3 flex list-none flex-wrap gap-2 p-0">
                {ready.map((f) => <li key={f.path}><Link href={f.path} className={chip}>Ready to move in {where(f)} ({f.count})</Link></li>)}
              </ul>
            )}
          </div>
        </section>
      )}

      {brands.length > 0 && (
        <section aria-labelledby="builders-title" className={wrap + ' ' + section}>
          <h2 id="builders-title" className={h2}>Builders and their delivery records</h2>
          <p className="mt-1 text-slate-700">Every Pune project of a builder in one place, with the possession dates they filed and how often those moved.</p>
          <ul className="mt-4 grid list-none gap-2 p-0 sm:grid-cols-3 lg:grid-cols-4" data-testid="home-builders">
            {brands.map((b) => (
              <li key={b.slug}>
                <Link href={`/builders/${b.slug}`} className={card + ' py-3'}>
                  <span className="block font-semibold text-[#0f2340]">{b.name}</span>
                  {' '}<span className="block text-sm text-slate-600">{b.projects} projects</span>
                </Link>
              </li>
            ))}
          </ul>
          <p className="mt-4"><Link href="/builders" className="font-semibold text-[#0f2340] underline underline-offset-4">All builders in Pune</Link></p>
        </section>
      )}

      <section aria-labelledby="check-title" className={'bg-[#0f2340] text-white ' + section}>
        <div className={wrap}>
          <h2 id="check-title" className="text-2xl font-extrabold sm:text-3xl">Check before you pay a token</h2>
          <ul className="mt-4 grid list-none gap-3 p-0 sm:grid-cols-3">
            <li><Link href="/check" className="block h-full rounded-2xl bg-white/10 p-4 text-white no-underline hover:bg-white/15"><b className="block">Check your project</b>{' '}<span className="text-sm text-white/80">Registration, possession filed, delays and cautions, in one page</span></Link></li>
            <li><Link href="/pune-maharera-tracker" className="block h-full rounded-2xl bg-white/10 p-4 text-white no-underline hover:bg-white/15"><b className="block">Pune MahaRERA tracker</b>{' '}<span className="text-sm text-white/80">What was registered and what completes, area by area</span></Link></li>
            <li><Link href="/insights" className="block h-full rounded-2xl bg-white/10 p-4 text-white no-underline hover:bg-white/15"><b className="block">Buyer guides</b>{' '}<span className="text-sm text-white/80">Offers, site visits, stamp duty and the questions to ask</span></Link></li>
          </ul>
        </div>
      </section>

      <NewsSection />

      <section aria-label="For real estate agents" className={'border-t border-slate-200 ' + section}>
        <div className={wrap + ' flex flex-wrap items-center justify-between gap-3'}>
          <p className="text-slate-700"><b className="text-slate-900">Are you a real estate agent in Pune?</b> Get your own page, buyer enquiries and posts made for you.</p>
          <Link href={AGENTS_PATH} className="inline-flex min-h-[48px] items-center rounded-xl border-2 border-[#0f2340] px-5 font-bold text-[#0f2340] no-underline hover:bg-[#0f2340] hover:text-white">For agents</Link>
        </div>
      </section>
    </MarketingShell>
  )
}
