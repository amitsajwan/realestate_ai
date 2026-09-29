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

interface Props {
  params: { slug: string }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const slug = normalizeSlug(params.slug)
  const agent = slug ? await getAgent(slug) : null
  if (!slug || !agent) return { title: 'Agent not found', robots: { index: false } }
  const { items } = await getListings(slug)
  return agentMetadata(agent, items, agentCity(agent, items))
}

export default async function AgentHomePage({ params }: Props) {
  const slug = normalizeSlug(params.slug)
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

        <section id="about" aria-labelledby="about-title" className="scroll-mt-16">
          <h2 id="about-title" className="mb-3 text-2xl font-bold">About {agent.agent_name}</h2>
          {agent.bio && <p className="leading-relaxed text-slate-800">{agent.bio}</p>}
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
          <h2 id="contact-title" className="text-2xl font-bold">Get in touch</h2>
          <ContactButtons agentSlug={slug} phone={agent.phone} waMessage={msg} size="md" className="max-w-md" />
          {agent.office_address && <p className="text-slate-700">{agent.office_address}</p>}
          <EnquiryForm agentSlug={slug} agentName={agent.agent_name} agentPhone={agent.phone} waMessage={msg} id="enquire" />
        </section>
      </div>
    </SiteShell>
  )
}
