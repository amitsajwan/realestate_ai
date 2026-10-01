import React from 'react'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import ContactButtons from '@/components/site/ContactButtons'
import EnquiryForm from '@/components/site/EnquiryForm'
import Hero from '@/components/site/Hero'
import ListingBrowser from '@/components/site/ListingBrowser'
import SiteShell from '@/components/site/SiteShell'
import TrackingBeacon from '@/components/site/TrackingBeacon'
import { agentCity, getAgent, getListings } from '@/lib/site/api'
import { whatsappMessage } from '@/lib/site/links'
import { agentJsonLd, agentMetadata, jsonLdString } from '@/lib/site/seo'
import { normalizeSlug } from '@/lib/site/slug'
import AboutAgent from '@/components/site/AboutAgent'
import Link from 'next/link'
import { INSIGHTS } from '@/lib/marketing/insights'

interface Props {
  params: Promise<{ slug: string }>
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const slug = normalizeSlug((await params).slug)
  const agent = slug ? await getAgent(slug) : null
  if (!slug || !agent) return { title: 'Agent not found', robots: { index: false } }
  const { items } = await getListings(slug)
  return agentMetadata(agent, items, agentCity(agent, items))
}

export default async function AgentHomePage({ params }: Props) {
  const slug = normalizeSlug((await params).slug)
  const agent = slug ? await getAgent(slug) : null
  if (!slug || !agent) notFound()
  const { items } = await getListings(slug)
  const city = agentCity(agent, items)
  const msg = whatsappMessage(agent.agent_name)

  return (
    <SiteShell agent={agent}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(agentJsonLd(agent, city)) }} />
      <TrackingBeacon agentSlug={slug} />
      <Hero agent={agent} city={city} />

      <div className="mx-auto max-w-5xl space-y-12 px-4 py-10">
        <section id="listings" aria-labelledby="listings-title" className="scroll-mt-16">
          <h2 id="listings-title" className="mb-4 text-2xl font-bold">Properties</h2>
          <ListingBrowser slug={slug} items={items} />
        </section>

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

        <section id="contact" aria-labelledby="contact-title" className="scroll-mt-16 space-y-4">
          <h2 id="contact-title" className="text-2xl font-bold">Tell us what you are looking for</h2>
          <ContactButtons agentSlug={slug} phone={agent.phone} waMessage={msg} size="md" className="max-w-md" />
          {agent.office_address && <p className="text-slate-700">{agent.office_address}</p>}
          <EnquiryForm agentSlug={slug} agentName="PUNE Property" agentPhone={agent.phone} waMessage={msg} id="enquire" />
        </section>
      </div>
    </SiteShell>
  )
}
