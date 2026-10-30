import React from 'react'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import ContactButtons from '@/components/site/ContactButtons'
import EnquiryForm from '@/components/site/EnquiryForm'
import Hero from '@/components/site/Hero'
import ListingBrowser from '@/components/site/ListingBrowser'
import HomeFinder, { type FinderMap } from '@/components/site/finder/HomeFinder'
import { parseQuery } from '@/lib/site/finder'
import { fromListings } from '@/lib/site/finderItems'
import { getRegisterProjects } from '@/lib/site/register'
import { getAreaMap } from '@/lib/site/hubs'
import { isSampleListing } from '@/lib/site/format'
import { agentPath, siteOrigin } from '@/lib/site/slug'
import SiteShell from '@/components/site/SiteShell'
import { enquiryName } from '@/lib/site/theme'
import TrackingBeacon from '@/components/site/TrackingBeacon'
import { agentCity, getAgent, getListings, getProjects } from '@/lib/site/api'
import ProjectsSection from '@/components/site/ProjectsSection'
import { whatsappMessage } from '@/lib/site/links'
import { agentJsonLd, agentMetadata, jsonLdString } from '@/lib/site/seo'
import { normalizeSlug } from '@/lib/site/slug'
import AboutAgent from '@/components/site/AboutAgent'
import TeamSection from '@/components/site/TeamSection'
import Link from 'next/link'
import { INSIGHTS } from '@/lib/marketing/insights'
import { BRAND_NAME, isHouseAgent } from '@/lib/brand'
import DemoRibbon from './DemoRibbon'

interface Props {
  params: Promise<{ slug: string }>
  searchParams?: Promise<Record<string, string | string[] | undefined>>
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const slug = normalizeSlug((await params).slug)
  const agent = slug ? await getAgent(slug) : null
  if (!slug || !agent) return { title: 'Agent not found', robots: { index: false } }
  const { items } = await getListings(slug)
  return agentMetadata(agent, items, agentCity(agent, items))
}

/** The drawn area map for the chosen area, when there is one (Upper Kharadi, Wagholi, Kharadi). */
async function finderMaps(area?: string): Promise<Record<string, FinderMap>> {
  if (!area) return {}
  const m = await getAreaMap(area.replace(/-/g, '_')).catch(() => null)
  return m ? { [area]: { name: m.name, map: m.map, box: m.box, attribution: m.attribution } } : {}
}

export default async function AgentHomePage({ params, searchParams }: Props) {
  const slug = normalizeSlug((await params).slug)
  const agent = slug ? await getAgent(slug) : null
  if (!slug || !agent) notFound()
  const [{ items }, projects] = await Promise.all([getListings(slug), getProjects(slug)])
  const city = agentCity(agent, items)
  // An agent with projects and no listings: the projects take the 'Properties' anchor the header links to.
  const projectsOnly = projects.length > 0 && items.length === 0
  const msg = whatsappMessage(agent.agent_name)
  const q = parseQuery(await searchParams)
  const live = items.filter((x) => !isSampleListing(x.title))
  const finderItems = live.length ? fromListings(live, slug, await getRegisterProjects(undefined, true)) : []

  return (
    <SiteShell agent={agent}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(agentJsonLd(agent, city)) }} />
      <TrackingBeacon agentSlug={slug} />
      <DemoRibbon agent={agent} />
      <Hero agent={agent} city={city} />
      {/* the team's own page ranked above the home page for "avasetu pune" (2026-10-29): it keeps its listings and the enquiry
          form every buyer button opens, names the home page as canonical (lib/site/seo) and sends a visitor there to search */}
      {isHouseAgent(slug) && (
        <p className="mx-auto max-w-5xl px-4 pt-8 text-slate-700" data-testid="house-home-link">
          These are the homes the {BRAND_NAME} team lists itself. For every new project in Pune with its MahaRERA record, see{' '}
          <Link href="/" className="font-semibold text-[var(--site-primary,#0f2340)] underline underline-offset-4">{BRAND_NAME}: search new projects in Pune, checked against MahaRERA</Link>.
        </p>
      )}

      <div className="mx-auto max-w-5xl space-y-12 px-4 py-10">
        <ProjectsSection agentSlug={slug} projects={projects} anchor={projectsOnly ? 'listings' : 'projects'} />

        {/* the home finder (lib/site/finder): area, budget, size, move-in and the MahaRERA checks over the agent's own listings */}
        {!projectsOnly && finderItems.length > 0 && (
          <HomeFinder id="listings" title={`Find your home with ${enquiryName(agent)}`} q={q} basePath={agentPath(slug)} items={finderItems}
            lead={{ agentSlug: slug, agentName: enquiryName(agent), agentPhone: agent.phone }} maps={await finderMaps(q.area)} origin={siteOrigin()} />
        )}
        {/* only sample homes (the demo agent): the plain list, which labels them */}
        {!projectsOnly && finderItems.length === 0 && (
          <section id="listings" aria-labelledby="listings-title" className="scroll-mt-16">
            <h2 id="listings-title" className="mb-4 text-2xl font-bold">Properties</h2>
            <ListingBrowser slug={slug} items={items} />
          </section>
        )}

        <section id="guides" aria-labelledby="guides-title" className="scroll-mt-16">
          <h2 id="guides-title" className="mb-1 text-2xl font-bold">Guides for Pune home buyers</h2>
          <p className="mb-4 text-slate-600">Plain-language, sourced, and no guesses on prices.</p>
          <ul className="grid gap-4 sm:grid-cols-3">
            {INSIGHTS.map((a) => (
              <li key={a.slug}>
                <Link href={`/insights/${a.slug}`} className="flex h-full flex-col rounded-2xl border border-slate-200 bg-white p-4 no-underline hover:border-[var(--site-primary)]">
                  <span className="text-xs font-bold uppercase tracking-wide text-[var(--site-accent-text)]">Guide</span>
                  <span className="mt-1 font-semibold text-slate-900">{a.title}</span>
                  <span className="mt-2 text-sm text-slate-600">{a.summary}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <AboutAgent agent={agent} />

        <TeamSection agent={agent} />

        <section id="contact" aria-labelledby="contact-title" className="scroll-mt-16 space-y-4">
          <h2 id="contact-title" className="text-2xl font-bold">Tell us what you are looking for</h2>
          <ContactButtons agentSlug={slug} phone={agent.phone} waMessage={msg} size="md" className="max-w-md" />
          <EnquiryForm agentSlug={slug} agentName={enquiryName(agent)} agentPhone={agent.phone} waMessage={msg} id="enquire" />
        </section>
      </div>
    </SiteShell>
  )
}
