import React from 'react'
import Link from 'next/link'
import AgentStrip from '@/components/marketing/AgentStrip'
import MarketingShell from '@/components/marketing/MarketingShell'
import HomePlanBox from '@/components/site/homeplan/HomePlanBox'
import CorridorMap, { CorridorStatus } from '@/components/site/CorridorMap'
import ListingCard from '@/components/site/ListingCard'
import ProjectCard from '@/components/site/ProjectCard'
import ActiveProjects from '@/components/site/ActiveProjects'
import AreaMap, { showsMap } from '@/components/site/AreaMap'
import AreaFromAbove from '@/components/site/AreaFromAbove'
import { mapsEmbedKey } from '@/components/site/mapsEmbed'
import { AREA_CENTRES } from '@/lib/site/areaCentres'
import FacetChips from '@/components/site/FacetChips'
import PostsGrid from '@/components/site/PostsGrid'
import AreaLatest from '@/components/localities/AreaLatest'
import AreaPhotos from '@/components/localities/AreaPhotos'
import AreaRecords from '@/components/localities/AreaRecords'
import AreaGrowth from '@/components/localities/AreaGrowth'
import AreaFromSpace from '@/components/localities/AreaFromSpace'
import AreaLandmarks, { areaQuestions, getAreaLandmarks } from '@/components/localities/AreaLandmarks'
import { PairLinks } from '@/components/localities/AreaCompare'
import { getAreaPhotos } from '@/components/localities/areaPhotoData'
import { readAreaPictures } from '@/components/localities/areaPictures'
import { getAreaNews, getAreaPosts } from '@/components/localities/areaFeed'
import { getAreaStats, longDate, recordLinks, type AreaStats } from '@/components/localities/areaStats'
import { getCommunities } from '@/components/localities/communities'
import { AreaTrackers } from '@/components/news/Trackers'
import { Body, TopicLinks, TopicStatus, TopicStory, UI, day } from '@/components/guides/TopicBody'
import { getMarketingConfig } from '@/lib/marketing/config'
import { INSIGHT_NOTE, getInsight } from '@/lib/marketing/insights'
import { localitiesByTier, localitySource, localitySourceFromSlug, type LocalityTier } from '@/lib/marketing/localities'
import { articleJsonLd, breadcrumbJsonLd, jsonLdString } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { fetchTrackers } from '@/lib/news/trackers'
import { getCatalog, getLocalityListings } from '@/lib/site/api'
import { getAreaFromSpace } from '@/lib/site/areaFromSpace'
import { areaGuidePath } from '@/lib/site/areaGuide'
import { getAreaPairs, pairsWith } from '@/lib/site/compare'
import { getFacets, placeChips } from '@/lib/site/facets'
import { livePages } from '@/lib/site/filters'
import { getActive, getAreaMap, getListed, type ListedProject } from '@/lib/site/hubs'
import { getRegisterPlaces, placePath } from '@/lib/site/register'
import { say, type Topic } from '@/lib/site/topics'
import SectionNav, { type SectionLink } from './SectionNav'
import type { PageLocality } from './pageLocality'

/** One page per area (2026-11-23). An area with a written guide (`/guides/<slug>`, calendar/topics) and an area without one
 *  (`/localities/<slug>`) are the same page: the guide's text is one section of it, and the map, projects, getting around, growth
 *  and news are the others. Before, Upper Kharadi had two pages, each with half of this, and Google kept both for "upper kharadi"
 *  (Search Console: the locality page chosen as its own canonical despite naming the guide). Every section is rendered on the
 *  server and stays on the page; the section bar (SectionNav) jumps to them. */

/** "Other <word> areas we cover" (the tier titles in TIER_LABELS read badly there). */
const TIER_WORD: Record<LocalityTier, string> = { affordable: 'affordable', it: 'IT corridor' }

/** Project cards on an area page: a few, since the area's projects page lists them all (and ranks them) */
export const AREA_PROJECTS = 6

// the guides in East Pune (app/core/pune_places.py zone), where the home plan has projects to pick from
export const EAST_GUIDES = new Set(['kharadi', 'upper-kharadi', 'wagholi', 'lohegaon', 'keshav-nagar'])

/** Where "I'm interested" leads: the enquiry page (app/enquire). `?src=locality_<key>` is picked up by the site's attribution
 *  (lib/site/tracking.ts readAttribution) and stored as the lead's source. */
const enquireHref = (l: PageLocality) => `/enquire?src=${l.fallback ? localitySourceFromSlug(l.slug) : localitySource(l)}`

const h2 = 'text-xl font-semibold text-slate-900'
const link = 'font-semibold text-[#0f2340] underline underline-offset-2'

/** The area's MahaRERA figures in three tiles at the top: projects, homes registered, share booked. A booked share only beside a
 *  total it fits inside (the same rule as AreaRecords). */
export function KeyFigures({ stats, allHref }: { stats: AreaStats | null; allHref: string | null }) {
  if (!stats || stats.projects <= 0) return null
  const total = stats.units_total, booked = stats.units_booked
  const share = total && booked != null && booked <= total ? Math.round((booked / total) * 100) : null
  const tiles = [
    { value: stats.projects.toLocaleString('en-IN'), label: stats.projects === 1 ? 'project on MahaRERA' : 'projects on MahaRERA', href: allHref },
    ...(total ? [{ value: total.toLocaleString('en-IN'), label: 'homes registered', href: null }] : []),
    ...(share != null ? [{ value: `${share}%`, label: 'of those homes booked', href: null }] : []),
  ]
  return (
    <div className="mt-6" data-testid="key-figures">
      {/* the number first, in the text too: it reads "9 projects on MahaRERA", as it looks */}
      <ul className="grid list-none grid-cols-3 gap-2 p-0 sm:gap-3">
        {tiles.map((t) => (
          <li key={t.label} className="rounded-xl border border-slate-200 bg-white p-3 sm:p-4">
            <span className="block text-xl font-bold text-[#0f2340] sm:text-2xl">
              {t.href ? <Link href={t.href} className="text-[#0f2340] no-underline hover:underline">{t.value}</Link> : t.value}
            </span>{' '}
            <span className="mt-0.5 block text-xs leading-snug text-slate-600 sm:text-sm">{t.label}</span>
          </li>
        ))}
      </ul>
      <p className="mt-1.5 text-xs text-slate-500">MahaRERA register, as of {longDate(stats.as_of)}</p>
    </div>
  )
}

/** One of the page's sections: a jump target with its tab's name over it. The parts inside keep their own headings. */
function Part({ id, label, children }: { id: string; label: string; children: React.ReactNode }) {
  return (
    <section id={id} aria-label={label} data-part={id}
      className="mt-12 scroll-mt-32 border-t border-slate-200 pt-8 first:mt-8 first:border-t-0 first:pt-0 lg:scroll-mt-24 [&>*:nth-child(2)]:mt-2">
      <p className="text-xs font-bold uppercase tracking-wider text-amber-700" aria-hidden="true">{label}</p>
      {children}
    </section>
  )
}

/** The questions an area page answers, one list: the guide's own, the area's, then the ones the landmarks and MahaRERA counts
 *  answer ("People also ask"), each asked once. Only an English page carries the English ones. */
export function areaFaqs(l: PageLocality, topic: Topic | null, more: { q: string; a: string }[]): { q: string; a: string }[] {
  const lang = topic?.lang ?? 'en'
  const all = [...(topic?.faq ?? []).map((f) => ({ q: say(f.q, lang), a: say(f.a, lang) })), ...(lang === 'en' ? [...l.faqs, ...more] : [])]
  const seen = new Set<string>()
  return all.filter((f) => {
    const k = f.q.toLowerCase().replace(/[^a-z0-9ऀ-ॿ]+/g, ' ').trim()
    if (seen.has(k)) return false
    seen.add(k)
    return true
  })
}

export default async function AreaPage({ l, topic = null, path }: { l: PageLocality; topic?: Topic | null; path: string }) {
  const area = !l.fallback
  const [listings, projects, stats, posts, news, hoods, active, facets, map, listed, trackers, places, landmarks, pairs, photos, pictures, space] = await Promise.all([
    getLocalityListings(l.listingName), getCatalog(l.listingName), area ? getAreaStats(l.slug) : Promise.resolve(null),
    area ? getAreaPosts(l, 6) : Promise.resolve([]), area ? getAreaNews(l, 5) : Promise.resolve([]),
    area ? getCommunities(l.key) : Promise.resolve([]),
    area ? getActive({ area: l.key }) : Promise.resolve([]),
    area ? getFacets() : Promise.resolve([]),
    area ? getAreaMap(l.key) : Promise.resolve(null),
    area ? getListed() : Promise.resolve(new Map<string, ListedProject>()),
    area ? fetchTrackers(l.key) : Promise.resolve([]),
    area ? getRegisterPlaces() : Promise.resolve([]),
    area ? getAreaLandmarks(l.slug) : Promise.resolve(null),
    area ? getAreaPairs() : Promise.resolve([]),
    area ? getAreaPhotos(l.slug) : Promise.resolve([]),
    area ? readAreaPictures(l.slug) : Promise.resolve([]),
    area ? getAreaFromSpace(l.slug) : Promise.resolve(null),
  ])
  const cfg = getMarketingConfig()
  const lang = topic?.lang ?? 'en'
  const east = EAST_GUIDES.has(l.slug)
  const allHref = area ? placePath(l.slug) : null
  // the block shows when something tracked touches this area; the city-wide rates come along with it, never alone
  const nearby = trackers.some((t) => t.areas.some((a) => a.slug === l.slug)) ? trackers : []
  // the area's own lists in search (new launches, 2 BHK flats ...) and the agents' pages that still answer here
  const lists = area ? placeChips({ key: l.key, slug: l.slug }, facets, livePages(projects, [l])).filter((c) => c.path !== allHref) : []
  const more = area && lang === 'en' ? areaQuestions(l.name, landmarks, stats?.registered ?? [], stats?.as_of ?? null,
    [...(topic?.faq ?? []).map((f) => say(f.q, 'en')), ...l.faqs.map((f) => f.q)]) : []
  const faqs = areaFaqs(l, topic, more)
  const guides = l.guides.map((s) => getInsight(s)).filter((g): g is NonNullable<typeof g> => !!g)
  const sameTier = localitiesByTier(l.tier).filter((o) => o.slug !== l.slug)
  const growth = (stats?.projects ?? 0) > 0 || pictures.length >= 2 || Boolean(space?.video)
  const hasNews = nearby.length > 0 || posts.length > 0 || news.length > 0 || (topic?.updates.length ?? 0) > 0
  // a guide's sources are other sites' pages (nofollow, as the guide had them); the area's are official sources
  const sources = [...(topic?.sources ?? []).map((s) => ({ label: s.name + (s.read_on ? ` (${s.read_on})` : ''), href: s.url ?? null, rel: 'nofollow noopener' })),
    ...l.sources.map((s) => ({ label: s.label, href: s.href, rel: 'noopener noreferrer' }))]

  const parts: (SectionLink & { show: boolean; body: React.ReactNode })[] = [
    {
      // the area's most active projects on its street map, first after the intro (owner, 2026-10-26); no drawn map yet: Google's
      // view from above, on tap
      id: 'map', label: 'Map', show: area && (showsMap(map) || Boolean(mapsEmbedKey() && AREA_CENTRES[l.slug]) || hoods.length > 0),
      body: <>
        {showsMap(map) ? <AreaMap data={map} listed={listed} allHref={allHref ?? undefined} className="mt-2" />
          : <AreaFromAbove slug={l.slug} name={l.name} className="mt-2" />}
        {hoods.length > 0 && (
          <section className="mt-9" aria-labelledby="hoods-title">
            <h2 id="hoods-title" className={h2}>Neighbourhoods in {l.name}</h2>
            <ul className="mt-3 grid list-none gap-3 p-0 sm:grid-cols-2">
              {hoods.map((h) => (
                <li key={h.slug}><Link href={`/localities/${h.area_slug}/${h.slug}`} className="block h-full rounded-xl border border-slate-200 p-4 no-underline hover:border-slate-400">
                  <span className="font-semibold text-[#0f2340]">{h.name}</span>
                  {h.summary && <span className="mt-1 block text-sm text-slate-600">{h.summary}</span>}
                </Link></li>
              ))}
            </ul>
          </section>
        )}
      </>,
    },
    topic ? {
      // the written guide: its dates, sections and tables (the status line sits at the top of the page)
      id: 'guide', label: 'Guide', show: true,
      body: <div lang={lang} className="[&>*:first-child]:mt-2"><TopicStory t={topic} lang={lang} status={false} /></div>,
    } : {
      id: 'overview', label: 'Overview', show: true,
      body: <section><h2 className={h2}>Who {l.name} suits</h2>
        <ul className="mt-3 list-disc space-y-2 pl-6 leading-relaxed text-slate-800">{l.suits.map((s) => <li key={s}>{s}</li>)}</ul></section>,
    },
    {
      // a taste of the area's projects; the full list and its rankings live on the place page, which owns "projects in X"
      id: 'projects', label: 'Projects', show: true,
      body: <>
        <section style={AVASETU_SITE_VARS} aria-labelledby="projects-title">
          <h2 id="projects-title" className={h2}>Projects and flats in {l.name}</h2>
          {projects.length > 0 && <>
            <p className="mt-1 text-sm text-slate-600">With the completion date filed on MahaRERA and how many homes are booked.</p>
            <ul className="mt-4 grid list-none gap-4 p-0 sm:grid-cols-2">
              {projects.slice(0, AREA_PROJECTS).map((p) => <li key={p.slug}><ProjectCard p={p} href={`/projects/${p.slug}`} /></li>)}
            </ul>
          </>}
          <p className="mt-4"><Link href={allHref ?? '/projects'} className={link}>{allHref ? `See every project in ${l.name}` : 'All projects'}</Link>
            {allHref && ', with possession dates and homes booked from MahaRERA.'}</p>
          <FacetChips chips={lists} label={`Lists for ${l.name}`} className="mt-3" />
        </section>
        {!showsMap(map) && <ActiveProjects title={`Most active projects in ${l.name}`} items={active} />}
        {east && <div className="mt-9"><HomePlanBox area={l.name} /></div>}
        <section className="mt-9" aria-labelledby="homes-title"><h2 id="homes-title" className={h2}>Homes in {l.name}</h2>
          {listings.length > 0 ? (
            <ul className="mt-4 grid list-none gap-4 p-0 sm:grid-cols-2">{listings.map((x) => x.agent?.slug ? <ListingCard key={x.id} slug={x.agent.slug} listing={x} /> : null)}</ul>
          ) : (
            <p className="mt-3 rounded-xl bg-slate-50 p-4 text-slate-700">{projects.length > 0 ? 'No individual homes are listed here yet; the new projects above have prices. ' : 'We do not have live listings here yet. '}Tell us your budget and preferred type and we will send you options as they come.</p>
          )}
        </section>
      </>,
    },
    {
      id: 'getting-around', label: 'Getting around', show: true,
      body: <>
        {/* a written guide says it in its own metro and roads section */}
        {!topic && <section><h2 className={h2}>Getting around</h2>
          {l.gettingAround.map((p) => <p key={p} className="mt-3 leading-relaxed text-slate-800">{p}</p>)}</section>}
        {/* the east Pune corridor, running and coming (owner 2026-10-29, "show what is coming") */}
        {east && (
          <div className="mt-9 overflow-hidden rounded-xl border border-slate-200" data-testid="area-corridor">
            <div className="bg-[#0f2340] p-3 sm:p-4"><CorridorMap /></div>
            <CorridorStatus />
          </div>
        )}
        <AreaLandmarks data={landmarks} homesNearWork={east ? '/home-plan' : undefined} />
      </>,
    },
    {
      id: 'growth', label: 'Growth', show: area && growth,
      body: <>
        <AreaRecords name={l.name} stats={stats} links={recordLinks(l, places, facets)} />
        <AreaGrowth name={l.name} stats={stats} pictures={pictures} siteUrl={cfg.siteUrl} />
        {/* the area month by month from space, with each season's line (backend areastats/areaspace.py) */}
        <AreaFromSpace view={space} />
      </>,
    },
    {
      id: 'news', label: 'News', show: hasNews,
      body: <>
        <AreaTrackers name={l.name} items={nearby} />
        <AreaLatest name={l.name} posts={posts} news={news} />
        {topic && topic.updates.length > 0 && (
          <section className="mt-9">
            <h2 lang={lang} className={h2}>{say(UI.updates, lang)}</h2>
            <div className="mt-4"><PostsGrid posts={topic.updates} /></div>
          </section>
        )}
      </>,
    },
    {
      id: 'questions', label: 'Questions', show: true,
      body: <>
        {/* a written guide has its own list of what to check */}
        {!topic && <section><h2 className={h2}>Before you visit or book</h2>
          <ul className="mt-3 list-disc space-y-2 pl-6 leading-relaxed text-slate-800">{l.checks.map((s) => <li key={s}>{s}</li>)}</ul></section>}
        {faqs.length > 0 && (
          <section className="mt-9" aria-labelledby="faq-title"><h2 id="faq-title" lang={lang} className={h2}>{topic ? say(UI.faq, lang) : 'Questions buyers ask'}</h2>
            {/* each answer is in the page (and in the FAQPage data) even while folded; the first is open */}
            <div className="mt-3 space-y-2">
              {faqs.map((f, i) => (
                <details key={f.q} open={i === 0} className="group rounded-xl border border-slate-200 bg-white p-4 open:border-slate-300">
                  <summary className="cursor-pointer list-none font-semibold text-slate-900 [&::-webkit-details-marker]:hidden">
                    <span className="flex items-start justify-between gap-3">{f.q}<span aria-hidden="true" className="text-slate-400 transition group-open:rotate-45">+</span></span>
                  </summary>
                  <p className="mt-2 leading-relaxed text-slate-800">{f.a}</p>
                </details>
              ))}
            </div>
          </section>
        )}
        {topic && <div lang={lang}><TopicLinks t={topic} lang={lang} /></div>}
      </>,
    },
  ]
  const shown = parts.filter((p) => p.show)

  const breadcrumb = breadcrumbJsonLd(cfg.siteUrl, [{ name: 'Home', path: '/' }, { name: 'Area guides', path: '/localities' }, { name: `${l.name}, Pune`, path }])
  const faqLd = faqs.length > 0 ? {
    '@context': 'https://schema.org', '@type': 'FAQPage',
    mainEntity: faqs.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })),
  } : null
  const ld = [
    ...(topic ? [{ ...articleJsonLd(cfg, { title: topic.title.en, summary: topic.summary.en, path, updated: topic.checked_on ?? '' }), inLanguage: lang === 'en' ? 'en-IN' : `${lang}-IN` }] : []),
    breadcrumb, ...(faqLd ? [faqLd] : []),
  ]
  const checked = topic?.checked_on ? day(topic.checked_on, lang) : l.updatedLabel ?? null

  return (
    <MarketingShell hot={{ area: l.slug }}>
      <article className="mx-auto max-w-6xl px-4 py-10 sm:py-14 lg:grid lg:grid-cols-[11rem_minmax(0,48rem)] lg:justify-center lg:gap-x-12">
        {ld.map((x, i) => <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(x) }} />)}

        <header className="lg:col-start-2">
          <p className="text-sm"><Link href="/localities" className="text-[#0f2340] underline underline-offset-2">All area guides</Link></p>
          <h1 lang={lang} className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">{topic ? say(topic.title, lang) : `${l.name}, Pune`}</h1>
          {!topic && <p className="mt-1 font-semibold text-amber-700">{l.tagline}</p>}
          {checked && <p className="mt-2 text-sm text-slate-600">{topic ? say(UI.checked, lang) : 'Last updated'}: {topic ? checked : <time dateTime={l.updated}>{checked}</time>}</p>}
          <p lang={lang} className="mt-5 text-lg leading-relaxed text-slate-800">{topic ? say(topic.summary, lang) : l.summary}</p>
          {topic && <div lang={lang}><TopicStatus t={topic} lang={lang} className="mt-5" /></div>}
          <KeyFigures stats={stats} allHref={allHref} />
          <div className="mt-6 flex flex-wrap gap-3">
            {allHref && <Link href={allHref} className="inline-flex min-h-[48px] items-center rounded-full bg-[#0f2340] px-6 font-bold text-white no-underline">See every project</Link>}
            <a href={enquireHref(l)} className="inline-flex min-h-[48px] items-center rounded-full bg-amber-400 px-6 font-bold text-slate-900 no-underline">Tell us what you are looking for</a>
          </div>
          {/* real photos of the place, credited (Studio > Area photos); nothing when none is published */}
          <AreaPhotos name={l.name} photos={photos} className="mt-10" />
        </header>

        {/* a child of the page itself, so it stays stuck the whole way down; on a laptop the column beside both rows */}
        <SectionNav items={shown.map(({ id, label }) => ({ id, label }))} className="mt-8 lg:col-start-1 lg:row-span-2 lg:row-start-1 lg:mt-0" />

        <div className="lg:col-start-2">
          {shown.map((p) => <Part key={p.id} id={p.id} label={p.label}>{p.body}</Part>)}

          <aside aria-label={`More about ${l.name}`} className="mt-12 border-t border-slate-200 pt-8">
            {guides.length > 0 && (
              <section><h2 className={h2}>Related guides</h2>
                <ul className="mt-3 space-y-1">{guides.map((g) => <li key={g.slug}><Link href={`/insights/${g.slug}`} className="text-[#0f2340] underline underline-offset-2">{g.title}</Link></li>)}</ul></section>
            )}
            {/* the neighbouring areas side by side (lib/site/compare.ts): only areas near this one, nearest first */}
            <PairLinks pairs={pairsWith(pairs, l.slug)} title={`Compare ${l.name} with nearby areas`} />
            {/* Same tier only, never "nearby" or a distance: the IT corridor spans both ends of the city. */}
            <section className="mt-9" aria-labelledby="other-areas-title">
              <h2 id="other-areas-title" className={h2}>{l.fallback ? 'Pune area guides we cover' : `Other ${TIER_WORD[l.tier]} areas we cover`}</h2>
              <ul className="mt-3 flex list-none flex-wrap gap-2 p-0">
                {sameTier.map((o) => (
                  <li key={o.slug}><Link href={areaGuidePath(o.slug)} className="inline-flex min-h-[44px] items-center rounded-full border border-slate-300 px-4 text-sm font-semibold text-[#0f2340] no-underline hover:border-[#0f2340]">{o.name}</Link></li>
                ))}
                <li><Link href="/localities" className="inline-flex min-h-[44px] items-center px-2 text-sm font-semibold text-[#0f2340] underline underline-offset-2">All Pune area guides</Link></li>
              </ul>
            </section>

            {topic && lang !== 'en' && (
              <details className="mt-10 rounded-xl border border-slate-200 p-4">
                <summary className="cursor-pointer font-semibold text-[#0f2340]">{say(UI.english, lang)}</summary>
                <h2 className="mt-4 text-2xl font-bold text-slate-900">{topic.title.en}</h2>
                <p className="mt-2 text-slate-700">{topic.summary.en}</p>
                <div className="mt-4"><Body t={topic} lang="en" /></div>
              </details>
            )}

            {sources.length > 0 && (
              <section className="mt-10 border-t border-slate-200 pt-6"><h2 className="text-lg font-semibold text-slate-900">Sources</h2>
                <ul className="mt-2 list-disc space-y-1 pl-6 text-sm">{sources.map((s) => (
                  <li key={s.label}>{s.href ? <a href={s.href} target="_blank" rel={s.rel} className="text-[#0f2340] underline underline-offset-2">{s.label}</a> : s.label}</li>
                ))}</ul></section>
            )}
            <p className="mt-8 rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-700">{INSIGHT_NOTE}</p>
            <AgentStrip />
          </aside>
        </div>
      </article>
    </MarketingShell>
  )
}
