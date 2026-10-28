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

// The look (owner 2026-10-28, "professional, not as if AI made"): one weight for headings, lists as ruled rows rather than a box
// round every link, a chevron instead of a gold underline and arrow on every title, and colour kept for the hero and one band.
const wrap = 'mx-auto max-w-5xl px-4'
const section = 'py-10 sm:py-14'
const h2 = 'text-[1.375rem] font-semibold tracking-tight text-slate-900 sm:text-2xl'
const more = 'shrink-0 text-sm font-semibold text-[#0f2340] underline underline-offset-4'
const chip = 'inline-flex min-h-[44px] items-center rounded-lg border border-slate-300 bg-white px-3.5 text-sm font-medium text-slate-800 no-underline hover:border-[#0f2340] hover:text-[#0f2340]'
const groupLabel = 'text-xs font-semibold uppercase tracking-wider text-slate-500'

// a row or card still reads as a link on a phone, where there is no hover (owner 2026-10-26, "don't look clickable"): by the
// chevron at its end, the way an app's lists do
const Chevron = ({ className = '' }: { className?: string }) => (
  <svg aria-hidden viewBox="0 0 20 20" className={'h-4 w-4 shrink-0 text-slate-400 group-hover:text-[#0f2340] ' + className}>
    <path d="M7.5 4.5 13 10l-5.5 5.5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
)

/** A section's title, its one line, and on a laptop its "all" link at the right; phones get that link under the list instead. */
function SectionHead({ id, title, text, href, link }: { id: string; title: string; text?: string; href?: string; link?: string }) {
  return (
    <div className="flex items-end justify-between gap-4">
      <div className="min-w-0">
        <h2 id={id} className={h2}>{title}</h2>
        {text && <p className="mt-1 max-w-2xl text-slate-600">{text}</p>}
      </div>
      {href && link && <Link href={href} className={more + ' hidden sm:inline'}>{link}</Link>}
    </div>
  )
}

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
    <MarketingShell hot={false} search={false}>
      {/* old links to the agents' sections that were on this page (/#invite, /#faq) go on to /agents */}
      <script dangerouslySetInnerHTML={{ __html: agentAnchorForward() }} />
      {ld.map((x, i) => <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(x) }} />)}

      {/* the search is the hero's own action (so the header leaves its search pill off here); the enquiry is a quiet line under it */}
      <section aria-labelledby="home-title" className="bg-[#0f2340] text-white">
        <div className={wrap + ' pb-10 pt-10 sm:pb-14 sm:pt-16'}>
          <h1 id="home-title" className="max-w-3xl text-[2rem] font-semibold leading-[1.15] tracking-tight [text-wrap:balance] sm:text-[2.75rem]">
            New projects in Pune, checked against MahaRERA
          </h1>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-white/80">
            The possession date each builder filed and whether it moved, how many homes are booked, and each builder&apos;s delivery record.
          </p>
          <ProjectSearch hero />
          <p className="mt-4 text-[15px] text-white/75">
            Not sure where to start?{' '}
            <a href={buyerEnquirePath()} className="font-semibold text-white underline decoration-[#f0b440] decoration-2 underline-offset-4 hover:text-[#f5c75e]">Tell us what you need</a>
            {cfg.whatsappUrl && <>
              {' '}or{' '}
              <a href={cfg.whatsappUrl} target="_blank" rel="noopener noreferrer" className="font-semibold text-white underline decoration-white/40 underline-offset-4 hover:decoration-white">
                ask on WhatsApp<span className="sr-only"> (opens in a new tab)</span>
              </a>
            </>}
          </p>
          {tracked > 0 && city && (
            <p className="mt-8 border-t border-white/15 pt-4 text-sm text-white/65">
              {tracked.toLocaleString('en-IN')} projects in our areas, read from MahaRERA on {longDate(city.asOf)}.
            </p>
          )}
        </div>
      </section>

      {hot.length > 0 && (
        <section aria-labelledby="hot-title" className={wrap + ' pt-10 sm:pt-14'} data-testid="home-hot">
          <SectionHead id="hot-title" title="Hot right now" />
          {/* swiped on a phone, a grid on a laptop; it never moves by itself (ProjectRail) */}
          <ul className="-mx-4 mt-5 flex list-none snap-x snap-mandatory gap-3 overflow-x-auto px-4 pb-2 sm:mx-0 sm:grid sm:grid-cols-2 sm:overflow-visible sm:px-0 lg:grid-cols-3">
            {hot.map((p) => (
              <li key={p.slug} className="w-[80%] max-w-[300px] shrink-0 snap-start sm:w-auto sm:max-w-none">
                <Link href={`/projects/${p.slug}`} className="group flex h-full flex-col rounded-xl border border-slate-200 bg-white p-4 no-underline transition-shadow hover:border-slate-300 hover:shadow-md">
                  <span className="flex items-start justify-between gap-3">
                    <span className="font-semibold text-slate-900 group-hover:text-[#0f2340]">{p.name}</span>
                    <Chevron className="mt-1" />
                  </span>
                  {p.area && <span className="block text-sm text-slate-500">{p.area}, Pune</span>}
                  {' '}<span className="mt-3 block border-t border-slate-100 pt-3 text-sm text-slate-700">{p.note || `${p.fact} (${p.source})`}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {topList && (
        <div className={wrap}>
          <ProjectRail id="home-top" title={`Top projects in ${topList.place.name} you can still buy`} sub="Most homes booked first, with 10 or more open (MahaRERA)"
            href={topList.path} count={topList.count} rows={topList.rows} ranked className="mt-12" />
        </div>
      )}

      <section aria-labelledby="areas-title" className={wrap + ' ' + section}>
        <SectionHead id="areas-title" title="Projects by area" href="/projects" link="All projects in Pune, by place" />
        {(['it', 'affordable'] as const).map((tier) => (
          <div key={tier} className="mt-8">
            <h3 className="text-base font-semibold text-slate-900">{TIER_LABELS[tier].title}</h3>
            <p className="text-sm text-slate-600">{TIER_LABELS[tier].blurb}</p>
            <ul className="mt-3 grid list-none gap-x-10 border-t border-slate-200 p-0 sm:grid-cols-2" data-testid={`home-areas-${tier}`}>
              {localitiesByTier(tier).map((l) => {
                const place = placeOf(l)
                const live = place && place.indexable > 0
                const count = place && (place.current ?? place.projects) > 0
                return (
                  <li key={l.slug} className="group relative flex items-center gap-4 border-b border-slate-200 py-4">
                    <div className="min-w-0 flex-1">
                      {/* the whole row opens the area page (a tap beside the title did nothing: owner 2026-10-26); its name is the
                          page's own ("Flats and residential projects in Kharadi"), "new projects" being the new-launches list's search */}
                      <Link href={live ? placePath(place.slug) : `/localities/${l.slug}`}
                        className="font-semibold text-slate-900 no-underline underline-offset-4 after:absolute after:inset-0 after:content-[''] group-hover:text-[#0f2340] group-hover:underline">
                        {live ? `Projects in ${l.name}` : l.name}
                      </Link>
                      <p className="text-sm text-slate-600">{l.tagline}</p>
                      <p className="mt-1 flex flex-wrap items-center gap-x-2 text-sm">
                        {/* the projects a buyer of a new home looks at: every registration ever (303 in Kharadi) counted old ones too */}
                        {count && <span className="font-medium text-slate-800">
                          {place.current != null ? `${place.current} being built or just finished` : `${place.projects} projects on MahaRERA`}</span>}
                        {count && <span aria-hidden className="text-slate-300">·</span>}
                        <Link href={`/localities/${l.slug}`} className="relative z-10 inline-flex min-h-[32px] items-center text-slate-600 underline decoration-slate-300 underline-offset-2 hover:text-[#0f2340]">
                          Living in {l.name}
                        </Link>
                      </p>
                    </div>
                    <Chevron />
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
        <p className="mt-6 sm:hidden"><Link href="/projects" className={more}>All projects in Pune, by place</Link></p>
      </section>

      {(launches.length > 0 || ready.length > 0 || tops.length > 0) && (
        <section aria-labelledby="lists-title" className={'border-y border-slate-200 bg-slate-50 ' + section}>
          <div className={wrap}>
            <SectionHead id="lists-title" title="Top projects, new launches and ready homes" />
            <div className="mt-6 space-y-6">
              {tops.length > 0 && (
                <div>
                  <p className={groupLabel}>Most booked</p>
                  <ul className="mt-2 flex list-none flex-wrap gap-2 p-0" data-testid="home-tops">
                    {tops.map((f) => <li key={f.path}><Link href={f.path} className={chip}>Top projects in {where(f)} ({f.count})</Link></li>)}
                  </ul>
                </div>
              )}
              {launches.length > 0 && (
                <div>
                  <p className={groupLabel}>New launches</p>
                  <ul className="mt-2 flex list-none flex-wrap gap-2 p-0" data-testid="home-launches">
                    {launches.map((f) => <li key={f.path}><Link href={f.path} className={chip}>New launches in {where(f)} ({f.count})</Link></li>)}
                  </ul>
                </div>
              )}
              {ready.length > 0 && (
                <div>
                  <p className={groupLabel}>Completion date passed</p>
                  <ul className="mt-2 flex list-none flex-wrap gap-2 p-0">
                    {ready.map((f) => <li key={f.path}><Link href={f.path} className={chip}>Ready to move in {where(f)} ({f.count})</Link></li>)}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {brands.length > 0 && (
        <section aria-labelledby="builders-title" className={wrap + ' ' + section}>
          <SectionHead id="builders-title" title="Builders and their delivery records" href="/builders" link="All builders in Pune"
            text="Every Pune project of a builder in one place, with the possession dates they filed and how often those moved." />
          <ul className="mt-5 grid list-none gap-x-10 border-t border-slate-200 p-0 sm:grid-cols-2 lg:grid-cols-3" data-testid="home-builders">
            {brands.map((b) => (
              <li key={b.slug} className="border-b border-slate-200">
                <Link href={`/builders/${b.slug}`} className="group flex min-h-[52px] items-center gap-3 py-3 no-underline">
                  <span className="min-w-0 flex-1 font-medium text-slate-900 underline-offset-4 group-hover:text-[#0f2340] group-hover:underline">{b.name}</span>
                  {' '}<span className="text-sm tabular-nums text-slate-500">{b.projects} projects</span>
                  <Chevron />
                </Link>
              </li>
            ))}
          </ul>
          <p className="mt-6 sm:hidden"><Link href="/builders" className={more}>All builders in Pune</Link></p>
        </section>
      )}

      <section aria-labelledby="check-title" className={'bg-[#0f2340] text-white ' + section}>
        <div className={wrap}>
          <h2 id="check-title" className="text-[1.375rem] font-semibold tracking-tight sm:text-2xl">Check before you pay a token</h2>
          <ul className="mt-6 grid list-none gap-3 p-0 sm:grid-cols-3">
            {[
              { href: '/check', title: 'Check your project', text: 'Registration, possession filed, delays and cautions, in one page' },
              { href: '/pune-maharera-tracker', title: 'Pune MahaRERA tracker', text: 'What was registered and what completes, area by area' },
              { href: '/insights', title: 'Buyer guides', text: 'Offers, site visits, stamp duty and the questions to ask' },
            ].map((c) => (
              <li key={c.href}>
                <Link href={c.href} className="group flex h-full items-start gap-3 rounded-xl p-4 text-white no-underline ring-1 ring-inset ring-white/15 hover:bg-white/[0.06] hover:ring-white/30">
                  <span className="min-w-0 flex-1"><b className="block font-semibold">{c.title}</b>{' '}<span className="mt-1 block text-sm text-white/70">{c.text}</span></span>
                  <Chevron className="mt-1 text-white/50 group-hover:text-white" />
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <NewsSection quiet />

      <section aria-label="For real estate agents" className={'border-t border-slate-200 ' + section}>
        <div className={wrap + ' flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between'}>
          <div>
            <p className="font-semibold text-slate-900">Are you a real estate agent in Pune?</p>
            <p className="text-slate-600">Get your own page, buyer enquiries and posts made for you.</p>
          </div>
          <Link href={AGENTS_PATH} className="inline-flex min-h-[48px] items-center justify-center self-start rounded-lg border border-[#0f2340] px-5 font-semibold text-[#0f2340] no-underline hover:bg-[#0f2340] hover:text-white sm:self-auto">For agents</Link>
        </div>
      </section>
    </MarketingShell>
  )
}
