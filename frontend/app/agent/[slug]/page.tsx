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
import SocialLinks from '@/components/site/SocialLinks'
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
                <Link href={`/insights/${a.slug}`} className="flex h-full flex-col rounded-2xl border border-slate-200 bg-white p-4 no-underline hover:border-[var(--site-accent)]">
                  <span className="text-xs font-bold uppercase tracking-wide text-[var(--site-accent)]">Guide</span>
                  <span className="mt-1 font-semibold text-slate-900">{a.title}</span>
                  <span className="mt-2 text-sm text-slate-600">{a.summary}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <section id="about" aria-labelledby="about-title" className="scroll-mt-16">
          <h2 id="about-title" className="mb-3 text-2xl font-bold">About PUNE Property</h2>
          {(agent.photo || agent.branding_data?.logo) && (
            <div className="mb-3 flex items-center gap-3">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              {agent.photo && <img src={agent.photo} alt={'Photo of ' + agent.agent_name} width={64} height={64} className="h-16 w-16 rounded-full object-cover" />}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              {agent.branding_data?.logo && <img src={agent.branding_data.logo} alt={agent.agent_name + ' logo'} height={48} className="h-12 w-auto max-w-[9rem] object-contain" />}
            </div>
          )}
          {agent.bio && <p className="leading-relaxed text-slate-800">{agent.bio}</p>}
          <SocialLinks instagram={agent.branding_data?.social?.instagram} facebook={agent.branding_data?.social?.facebook} />
          <ul className="mt-3 flex list-none flex-wrap gap-2 p-0">
            {(agent.specialties || []).map((s) => (
              <li key={s} className="rounded-full bg-slate-100 px-3 py-1 text-sm">{s}</li>
            ))}
          </ul>
          {agent.languages && agent.languages.length > 0 && (
            <p className="mt-3 text-sm text-slate-600">Speaks {agent.languages.join(', ')}</p>
          )}
          {agent.experience && <p className="mt-1 text-sm text-slate-600">Experience: {agent.experience}</p>}
        </section>

        <section id="contact" aria-labelledby="contact-title" className="scroll-mt-16 space-y-4">
          <h2 id="contact-title" className="text-2xl font-bold">Tell us what you are looking for</h2>
          <ContactButtons agentSlug={slug} phone={agent.phone} waMessage={msg} size="md" className="max-w-md" />
          {agent.office_address && <p className="text-slate-700">{agent.office_address}</p>}
          <EnquiryForm agentSlug={slug} agentName={agent.agent_name} agentPhone={agent.phone} waMessage={msg} id="enquire" />
        </section>
      </div>
    </SiteShell>
  )
}
