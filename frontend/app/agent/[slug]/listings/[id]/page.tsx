import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import ContactButtons from '@/components/site/ContactButtons'
import DescriptionSwitch from '@/components/site/DescriptionSwitch'
import EnquiryForm from '@/components/site/EnquiryForm'
import Gallery from '@/components/site/Gallery'
import ListingFacts from '@/components/site/ListingFacts'
import ShareButton from '@/components/site/ShareButton'
import SiteShell from '@/components/site/SiteShell'
import StickyBar from '@/components/site/StickyBar'
import TrackingBeacon from '@/components/site/TrackingBeacon'
import { getAgent, getListing } from '@/lib/site/api'
import { formatPrice } from '@/lib/site/format'
import { whatsappMessage } from '@/lib/site/links'
import { jsonLdString, listingJsonLd, listingMetadata } from '@/lib/site/seo'
import { agentPath, normalizeSlug, siteOrigin } from '@/lib/site/slug'

interface Props {
  params: { slug: string; id: string }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const slug = normalizeSlug(params.slug)
  const agent = slug ? await getAgent(slug) : null
  const listing = slug && agent ? await getListing(slug, params.id) : null
  if (!agent || !listing) return { title: 'Property not found', robots: { index: false } }
  return listingMetadata(agent, listing)
}

export default async function ListingPage({ params }: Props) {
  const slug = normalizeSlug(params.slug)
  const agent = slug ? await getAgent(slug) : null
  if (!slug || !agent) notFound()
  const l = await getListing(slug, params.id)
  if (!l) notFound()

  const url = siteOrigin() + agentPath(slug, 'listings/' + l.id)
  const msg = whatsappMessage(agent.agent_name, l, url)
  const phone = agent.phone || (l.agent && l.agent.phone)

  return (
    <SiteShell agent={agent} bottomPad>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(listingJsonLd(agent, l)) }} />
      <TrackingBeacon agentSlug={slug} listingId={l.id} />
      <Gallery media={l.media} title={l.title} />

      <div className="mx-auto max-w-5xl space-y-8 px-4 py-6">
        <p className="text-sm">
          <Link href={agentPath(slug) + '#listings'} className="inline-flex min-h-[44px] items-center text-[var(--site-primary)]">&larr; All properties</Link>
        </p>
        <header>
          <p className="text-3xl font-extrabold text-[var(--site-primary)]">{formatPrice(l.price_inr, l.transaction)}</p>
          <h1 className="mt-1 text-2xl font-bold leading-snug">{l.title}</h1>
          <p className="mt-1 text-slate-600">
            {[l.project_name, l.locality, l.city].filter(Boolean).join(', ')}
            {l.status === 'under_offer' && <span className="ml-2 rounded-full bg-amber-300 px-2 py-0.5 text-xs font-semibold">Under offer</span>}
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <ShareButton agentSlug={slug} listingId={l.id} title={l.title} />
            <div className="hidden min-w-[280px] flex-1 md:flex md:max-w-sm">
              <ContactButtons agentSlug={slug} phone={phone} waMessage={msg} listingId={l.id} size="md" />
            </div>
          </div>
        </header>

        <ListingFacts listing={l} />
        <DescriptionSwitch description={l.description} />

        {l.amenities.length > 0 && (
          <section aria-labelledby="amen-title">
            <h2 id="amen-title" className="text-lg font-bold">Amenities</h2>
            <ul className="mt-2 flex list-none flex-wrap gap-2 p-0">
              {l.amenities.map((a) => <li key={a} className="rounded-full bg-slate-100 px-3 py-1.5 text-sm">{a}</li>)}
            </ul>
          </section>
        )}

        <EnquiryForm agentSlug={slug} agentName={agent.agent_name} agentPhone={phone} listingId={l.id} waMessage={msg} id="enquire" />
      </div>
      <StickyBar agentSlug={slug} phone={phone} waMessage={msg} listingId={l.id} />
    </SiteShell>
  )
}
