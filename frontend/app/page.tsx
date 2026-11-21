import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import NewsSection from '@/components/news/NewsSection'
import CardPicture from '@/components/site/CardPicture'
import { RailCard } from '@/components/site/ListCard'
import ProjectSearch from '@/components/site/ProjectSearch'
import { AGENTS_PATH, agentAnchorForward, buyerEnquirePath } from '@/components/marketing/siteLinks'
import { getCityStats, longDate } from '@/components/localities/areaStats'
import { getMarketingConfig } from '@/lib/marketing/config'
import { LOCALITIES } from '@/lib/marketing/localities'
import { jsonLdString, organizationJsonLd, pageMetadata } from '@/lib/marketing/seo'
import { brandProfiles } from '@/lib/marketing/social'
import { fetchTrackers, trackerPath } from '@/lib/news/trackers'
import { organizationId, teamForOrganization } from '@/lib/site/team'
import { BRAND_NAME, BRAND_NAME_DEVANAGARI } from '@/lib/brand'
import { getFacetQuiet, getFacets, type FacetLink, type FacetPage } from '@/lib/site/facets'
import { getBuilders, getListedSlugs, getSpotlight, linkListed } from '@/lib/site/hubs'
import { getProjectVideos, videoPagePath } from '@/lib/site/projectVideos'
import { getFromSpace, getRegisterPlaces, placePath } from '@/lib/site/register'
import { placeNow as now, zonesOf } from '@/lib/site/zones'
import { WORK } from '@/lib/site/homeplan'

// The buyers' home (2026-10-22; the agents' home moved to /agents), and since 2026-11-21 the page every profile links to
// (LinkedIn, Instagram, Facebook), so it speaks for all of Pune: each zone and its areas, the lists by size and stage, videos,
// trackers. East Pune, where we work first, still leads each list; its corridor diagram moved to the east area guides (before,
// it filled the hero and a second section, and the page read as an east Pune site). Every block hides itself when its data is
// not there (an outage, or the build with no API), so the page never breaks; kept 5 minutes like the lists it links.
export const revalidate = 300

// Google shows about 70 characters of a title and 160 of a description: both fit, so none of the facts is cut off. This page
// is the brand's face, and it faces buyers (owner 2026-10-29: "our main goal is now end users, not agents. When someone searches
// avasetu, it should be able to search projects"): the title leads with the brand, then says what a buyer does here.
const TITLE = `${BRAND_NAME}: Search New Projects in Pune, Checked Against MahaRERA`
const DESCRIPTION = 'Search new projects across Pune, from Kharadi and Wagholi to Hinjawadi, Baner, Ravet and Katraj: possession filed on MahaRERA, homes booked, builders\' records.'
const ABOUT = `${BRAND_NAME} (आवास + सेतु: home + bridge) is where home buyers search every new project across Pune with its MahaRERA record: possession filed, homes booked and builders' delivery records, and ask local agents about the ones they like.`

export const metadata: Metadata = pageMetadata(getMarketingConfig(), {
  title: TITLE,
  description: DESCRIPTION,
  path: '/',
  image: { path: '/brand/og-landing.jpg', width: 1200, height: 630, alt: `${BRAND_NAME}: search new projects in Pune, checked against MahaRERA` },
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

const n = (x: number) => x.toLocaleString('en-IN')

export default async function BuyerHome() {
  const cfg = getMarketingConfig()
  const [city, places, facets, spot, builders, listed, videos, space, trackers] = await Promise.all([
    getCityStats(), getRegisterPlaces(), getFacets(), getSpotlight(), getBuilders(), getListedSlugs(), getProjectVideos(), getFromSpace(),
    fetchTrackers(),
  ])
  // an agent-listed project's card opens its listed page, never its register page that 301s there (as the banner does)
  const hot = linkListed(spot, listed)
  const zones = zonesOf(places)
  const zoneOf = new Map(places.map((p) => [p.key, p.zone]))
  const total = zones.reduce((s, z) => s + z.current, 0)
  // a list's own label says what it is, not where ("New launch projects"): side by side here, each chip has to name its area
  const where = (f: { place: string; place_slug: string }) => places.find((p) => p.key === f.place)?.name
    ?? f.place_slug.split('-').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
  // our areas first, in the area list's order (east Pune leads: owner 2026-10-26, "our main target for now is east Pune"),
  // then every other place, biggest list first
  const ours = (key: string) => { const i = LOCALITIES.findIndex((l) => l.key === key); return i < 0 ? LOCALITIES.length : i }
  const byOurs = (a: { place: string; count: number }, b: { place: string; count: number }) => ours(a.place) - ours(b.place) || b.count - a.count
  const plain = (f: FacetLink) => f.indexable && !f.builder && !f.possession && !f.budget
  const pick = (test: (f: FacetLink) => boolean, most: number) => facets.filter((f) => plain(f) && test(f)).sort(byOurs).slice(0, most)
  const tops = pick((f) => f.intent === 'top' && !f.bhk, 10)
  const launches = pick((f) => f.intent === 'new-launches' && !f.bhk, 12)
  const ready = pick((f) => f.intent === 'ready-to-move' && !f.bhk, 8)
  const twos = pick((f) => f.bhk === 2, 10)
  const threes = pick((f) => f.bhk === 3, 10)
  // the most booked project of each part of Pune: each zone's biggest Top list, read in full for its first card, four zones
  const leadLists = zones.slice(0, 6).flatMap((z) => {
    const f = facets.filter((x) => plain(x) && x.intent === 'top' && !x.bhk && zoneOf.get(x.place) === z.name).sort((a, b) => b.count - a.count)[0]
    return f ? [{ zone: z.name, slug: f.place_slug }] : []
  }).slice(0, 4)
  const leads = (await Promise.all(leadLists.map(async (l) => ({ zone: l.zone, list: await getFacetQuiet(l.slug, ['top']) }))))
    .filter((x): x is { zone: string; list: FacetPage } => !!x.list && x.list.rows.length > 0)
  const brands = builders.filter((b) => b.indexable).sort((a, b) => Number(!!b.brand) - Number(!!a.brand) || b.projects - a.projects).slice(0, 12)
  // a video shows its picture before it plays: only the ones with a picture make the row
  const clips = videos.flatMap((v) => {
    const poster = v.video?.poster || v.agent_videos?.find((a) => a.poster)?.poster
    return poster ? [{ slug: v.slug, name: v.name, poster }] : []
  }).slice(0, 4)
  const seen = space.find((x) => x.video) ?? space[0]
  // the ask on a phone: the offices east and west, then anywhere else; working from home has the plan's own question
  const offices = WORK.filter((w) => w.key !== 'home')
  const ld = [
    { ...organizationJsonLd(cfg, ABOUT, brandProfiles()), alternateName: [BRAND_NAME_DEVANAGARI], ...teamForOrganization(cfg.siteUrl) },
    // Google retired the sitelinks search box in 2024, so the SearchAction draws no box in results; it still names the search,
    // and /projects?q= answers on the server, with or without JavaScript
    { '@context': 'https://schema.org', '@type': 'WebSite', name: cfg.businessName, alternateName: [BRAND_NAME_DEVANAGARI], url: cfg.siteUrl,
      description: ABOUT, publisher: { '@id': organizationId(cfg.siteUrl) },
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
        <div className={wrap + ' grid gap-8 pb-10 pt-10 sm:pb-14 sm:pt-16 lg:grid-cols-[1.25fr_1fr] lg:items-center lg:gap-12'}>
          <div>
            <h1 id="home-title" className="max-w-3xl text-[2rem] font-semibold leading-[1.15] tracking-tight [text-wrap:balance] sm:text-[2.75rem] lg:text-[2.5rem]">
              New projects in Pune, checked against MahaRERA
            </h1>
            <p className="mt-4 max-w-2xl text-lg leading-relaxed text-white/80">
              Every project&apos;s record in one place: the possession date the builder filed and whether it moved, how many homes
              are booked, and the builder&apos;s delivery record.
            </p>
            <ProjectSearch hero />
            <p className="mt-4 text-[15px] text-white/75">
              Not sure where to start?{' '}
              <Link href="/home-plan" className="font-semibold text-white underline decoration-[#f0b440] decoration-2 underline-offset-4 hover:text-[#f5c75e]">Get a free home plan for your family</Link>,{' '}
              <a href={buyerEnquirePath()} className="font-semibold text-white underline decoration-white/40 underline-offset-4 hover:decoration-white">tell us what you need</a>
              {cfg.whatsappUrl && <>
                {' '}or{' '}
                <a href={cfg.whatsappUrl} target="_blank" rel="noopener noreferrer" className="font-semibold text-white underline decoration-white/40 underline-offset-4 hover:decoration-white">
                  ask on WhatsApp<span className="sr-only"> (opens in a new tab)</span>
                </a>
              </>}
            </p>
            {total > 0 && (
              <p className="mt-8 border-t border-white/15 pt-4 text-sm text-white/65">
                {/* the count opens the tracker, which breaks it down area by area */}
                <Link href="/pune-maharera-tracker" className="text-white/80 underline underline-offset-2 hover:text-white">
                  {n(total)} projects being built across Pune</Link>{city ? <>, read from MahaRERA on {longDate(city.asOf)}</> : null}.
              </p>
            )}
          </div>
          {/* Pune at a glance: each zone with its projects being built, opening its areas further down the page */}
          {zones.length > 0 && (
            <nav aria-label="Pune by zone" className="rounded-xl bg-white/[0.04] p-4 ring-1 ring-inset ring-white/15 sm:p-5" data-testid="hero-zones">
              <p className="font-semibold text-white">Pune by zone</p>
              <p className="text-sm text-white/65">Projects being built or just finished</p>
              <ul className="mt-3 list-none border-t border-white/15 p-0">
                {zones.map((z) => (
                  <li key={z.id} className="border-b border-white/10 last:border-0">
                    <a href={`#${z.id}`} className="group flex min-h-[48px] items-center gap-3 py-2 text-white no-underline">
                      <span className="min-w-0 flex-1">
                        <span className="block font-medium group-hover:underline group-hover:underline-offset-4">{z.name}</span>
                        <span className="block truncate text-xs text-white/55">{z.places.slice(0, 3).map((p) => p.name).join(', ')}</span>
                      </span>
                      <span className="text-sm tabular-nums text-white/80">{n(z.current)}</span>
                      <Chevron className="text-white/40 group-hover:text-white" />
                    </a>
                  </li>
                ))}
              </ul>
            </nav>
          )}
        </div>
      </section>

      {hot.length > 0 && (
        <section aria-labelledby="hot-title" className={wrap + ' pt-10 sm:pt-14'} data-testid="home-hot">
          {/* "Hot" and "Top" are different rankings, so each says what it is (owner 2026-11-04, "getting confused which is correct") */}
          <SectionHead id="hot-title" title="Hot right now" text="Picked by our team, or drawing the most bookings, searches and news right now. Each card says why." />
          {/* swiped on a phone, a grid on a laptop; it never moves by itself. On a phone the card in the middle is in focus
              (globals.css .focus-row): snapped to the centre, with the row padded so the first and last cards can reach it */}
          <ul className="focus-row -mx-4 mt-5 flex list-none snap-x snap-mandatory gap-3 overflow-x-auto px-[10%] pb-2 sm:mx-0 sm:grid sm:grid-cols-2 sm:overflow-visible sm:px-0 lg:grid-cols-3">
            {hot.map((p) => (
              <li key={p.slug} className="w-[80%] max-w-[300px] shrink-0 snap-center sm:w-auto sm:max-w-none">
                {/* a picture on top (owner 2026-11-01, "places where we don't have images"): the project's pictures as a
                    slideshow, else its street map and the builder's logo; the picture links itself, its arrows are buttons */}
                <div className="flex h-full flex-col overflow-hidden rounded-xl border border-slate-200 bg-white transition-shadow hover:border-slate-300 hover:shadow-md">
                  <CardPicture m={p} name={p.name} href={`/projects/${p.slug}`} />
                  <Link href={`/projects/${p.slug}`} className="group flex flex-1 flex-col p-4 no-underline">
                    <span className="flex items-start justify-between gap-3">
                      <span className="font-semibold text-slate-900 group-hover:text-[#0f2340]">{p.name}</span>
                      <Chevron className="mt-1" />
                    </span>
                    {p.area && <span className="block text-sm text-slate-500">{p.area}, Pune</span>}
                    {' '}<span className="mt-3 block border-t border-slate-100 pt-3 text-sm text-slate-700">{p.note || `${p.fact} (${p.source})`}</span>
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* one card per part of Pune, so the first projects a visitor sees are not all one area's */}
      {leads.length >= 2 && (
        <section aria-labelledby="leads-title" className={wrap + ' pt-12 sm:pt-14'} data-testid="home-leads">
          <SectionHead id="leads-title" title="Most booked in each part of Pune" text="The first of each zone's Top list: most homes booked, with 10 or more still open (MahaRERA)." />
          <ul className="-mx-4 mt-5 flex list-none snap-x gap-3 overflow-x-auto px-4 pb-2 sm:mx-0 sm:grid sm:grid-cols-2 sm:overflow-visible sm:px-0 lg:grid-cols-4">
            {leads.map(({ zone, list }) => (
              <li key={list.path} className="flex w-[72%] max-w-[280px] shrink-0 snap-start flex-col sm:w-auto sm:max-w-none">
                <p className={groupLabel + ' mb-2'}>{zone}</p>
                <div className="flex-1"><RailCard r={list.rows[0]} rank={1} /></div>
                <Link href={list.path} className="mt-2 text-sm font-medium text-[#0f2340] underline underline-offset-4">Top {list.count} in {list.place.name}</Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section aria-labelledby="areas-title" className={wrap + ' ' + section}>
        <SectionHead id="areas-title" title="Projects by area" href="/projects" link="All places in Pune"
          text={zones.length ? 'Every part of Pune, with the projects being built or just finished in each area.' : undefined} />
        {zones.length > 0 && (
          <div className="mt-6 grid gap-x-10 gap-y-8 sm:grid-cols-2" data-testid="home-zones">
            {zones.map((z) => (
              <div key={z.id} id={z.id} className="scroll-mt-20">
                <h3 className="flex items-baseline justify-between gap-3 text-base font-semibold text-slate-900">
                  {z.name}<span className="text-sm font-normal tabular-nums text-slate-500">{n(z.current)} projects</span>
                </h3>
                <ul className="mt-2 list-none border-t border-slate-200 p-0">
                  {z.places.slice(0, 6).map((p) => (
                    <li key={p.key} className="border-b border-slate-200">
                      <Link href={placePath(p.slug)} className="group flex min-h-[48px] items-center gap-3 py-2.5 no-underline">
                        <span className="min-w-0 flex-1 font-medium text-slate-900 underline-offset-4 group-hover:text-[#0f2340] group-hover:underline">Projects in {p.name}</span>
                        <span className="text-sm tabular-nums text-slate-500">{n(now(p))}</span>
                        <Chevron />
                      </Link>
                    </li>
                  ))}
                </ul>
                {z.places.length > 6 && (
                  <p className="mt-2 text-sm"><Link href="/projects" className="text-slate-600 underline decoration-slate-300 underline-offset-2 hover:text-[#0f2340]">
                    {z.places.length - 6} more in {z.name}</Link></p>
                )}
              </div>
            ))}
          </div>
        )}
        {/* the area guides (who an area suits, getting around, what is coming): static, so they show even when the API is down */}
        <div className="mt-8">
          <p className={groupLabel}>Area guides</p>
          <ul className="mt-2 flex list-none flex-wrap gap-x-5 gap-y-1 p-0 text-sm" data-testid="home-guides">
            {LOCALITIES.map((l) => (
              <li key={l.slug}><Link href={`/localities/${l.slug}`} className="inline-flex min-h-[36px] items-center text-slate-700 underline decoration-slate-300 underline-offset-2 hover:text-[#0f2340]">{l.name}</Link></li>
            ))}
          </ul>
        </div>
        <p className="mt-6 sm:hidden"><Link href="/projects" className={more}>All places in Pune</Link></p>
      </section>

      {(tops.length > 0 || launches.length > 0 || ready.length > 0 || twos.length > 0 || threes.length > 0) && (
        <section aria-labelledby="lists-title" className={'border-y border-slate-200 bg-slate-50 ' + section}>
          <div className={wrap}>
            <SectionHead id="lists-title" title="Find projects by what you need"
              text="Each area's lists, read from MahaRERA. Top: most homes booked, with homes still open. New launches: registered in the last 12 months." />
            <div className="mt-6 space-y-6">
              {[
                { label: 'Most booked', list: tops, text: (f: FacetLink) => `Top projects in ${where(f)}`, id: 'home-tops' },
                { label: '2 BHK flats', list: twos, text: (f: FacetLink) => `2 BHK in ${where(f)}`, id: 'home-2bhk' },
                { label: '3 BHK flats', list: threes, text: (f: FacetLink) => `3 BHK in ${where(f)}`, id: 'home-3bhk' },
                { label: 'New launches', list: launches, text: (f: FacetLink) => `New launches in ${where(f)}`, id: 'home-launches' },
                { label: 'Completion date passed', list: ready, text: (f: FacetLink) => `Ready to move in ${where(f)}`, id: 'home-ready' },
              ].filter((g) => g.list.length > 0).map((g) => (
                <div key={g.id}>
                  <p className={groupLabel}>{g.label}</p>
                  <ul className="mt-2 flex list-none flex-wrap gap-2 p-0" data-testid={g.id}>
                    {g.list.map((f) => <li key={f.path}><Link href={f.path} className={chip}>{g.text(f)} ({f.count})</Link></li>)}
                  </ul>
                </div>
              ))}
              <p className="text-sm">
                <Link href="/projects/upcoming" className="font-medium text-[#0f2340] underline underline-offset-4">Coming soon: projects announced but not yet registered</Link>
              </p>
            </div>
          </div>
        </section>
      )}

      {/* the home plan (docs/plan/home-plan.md): one tap per office opens the questions with it already picked */}
      <section aria-labelledby="plan-title" className={wrap + ' ' + section} data-testid="home-plan">
        <SectionHead id="plan-title" title="Homes near your office" href="/home-plan" link="How the home plan picks" />
        <p className="mt-2 max-w-2xl text-slate-700">
          Tell us where you work, your budget and your family, and see the projects that fit, with the MahaRERA facts behind each
          pick. Free, and no phone number needed.
        </p>
        <ul className="mt-4 flex list-none flex-wrap gap-3 p-0">
          {offices.map((w) => (
            <li key={w.key}>
              <Link href={`/home-plan?work=${w.key}`}
                className="inline-flex min-h-[48px] items-center rounded-full border border-[#0f2340] px-5 font-semibold text-[#0f2340] no-underline hover:bg-[#0f2340] hover:text-white">
                {w.key === 'elsewhere' ? 'I work elsewhere in Pune' : `I work in ${w.label}`}
              </Link>
            </li>
          ))}
        </ul>
      </section>

      {/* what we film and what the satellite sees: the site's own pictures, each opening its project's page */}
      {(clips.length > 0 || seen) && (
        <section aria-labelledby="see-title" className={'border-t border-slate-200 ' + section} data-testid="home-see">
          <div className={wrap}>
            <SectionHead id="see-title" title="See the projects" text="Short videos of projects on sale, and each site from space, season by season since 2021." />
            <div className="mt-6 grid gap-6 lg:grid-cols-[2fr_1fr]">
              {clips.length > 0 && (
                <ul className="-mx-4 flex list-none snap-x gap-3 overflow-x-auto px-4 pb-2 sm:mx-0 sm:grid sm:grid-cols-4 sm:overflow-visible sm:px-0" data-testid="home-videos">
                  {clips.map((c) => (
                    <li key={c.slug} className="w-[42%] shrink-0 snap-start sm:w-auto">
                      <Link href={videoPagePath(c.slug)} className="group block no-underline">
                        <span className="relative block aspect-[9/16] overflow-hidden rounded-xl bg-slate-200">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img src={c.poster} alt="" loading="lazy" className="h-full w-full object-cover transition-transform group-hover:scale-[1.02]" />
                          <span aria-hidden className="absolute bottom-2 left-2 flex h-9 w-9 items-center justify-center rounded-full bg-black/55 text-white">
                            <svg viewBox="0 0 20 20" className="ml-0.5 h-4 w-4" fill="currentColor"><path d="M6 4.5v11l9-5.5z" /></svg>
                          </span>
                        </span>
                        <span className="mt-2 block text-sm font-medium leading-snug text-slate-900 group-hover:text-[#0f2340] group-hover:underline">{c.name}<span className="sr-only">, video</span></span>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
              {seen && (
                <Link href="/projects/from-space" className="group flex flex-col overflow-hidden rounded-xl border border-slate-200 bg-white no-underline hover:border-slate-300 hover:shadow-md">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={seen.picture} alt={`${seen.name} from space, ${seen.years[1]}`} loading="lazy" width={600} height={600} className="aspect-square w-full object-cover" />
                  <span className="flex items-start justify-between gap-3 p-4">
                    <span>
                      <span className="block font-semibold text-slate-900 group-hover:text-[#0f2340]">Pune projects from space</span>
                      <span className="mt-1 block text-sm text-slate-600">Satellite timelines of {n(space.length)} project sites, checked against what each builder filed.</span>
                    </span>
                    <Chevron className="mt-1" />
                  </span>
                </Link>
              )}
            </div>
          </div>
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
          {/* the works and rules that move prices, each with the stage it has actually reached (newsroom trackers) */}
          {trackers.length > 0 && (
            <div className="mt-10">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/60">What is changing in Pune</h3>
              <ul className="mt-2 grid list-none gap-x-10 border-t border-white/15 p-0 sm:grid-cols-2" data-testid="home-trackers">
                {trackers.map((t) => (
                  <li key={t.slug} className="border-b border-white/10">
                    <Link href={trackerPath(t.slug)} className="group flex min-h-[52px] items-center gap-3 py-3 text-white no-underline">
                      <span className="min-w-0 flex-1">
                        <span className="block font-medium group-hover:underline group-hover:underline-offset-4">{t.name}</span>
                        {t.status && <span className="block text-sm text-white/65">{t.status}</span>}
                      </span>
                      <Chevron className="text-white/40 group-hover:text-white" />
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </section>

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
