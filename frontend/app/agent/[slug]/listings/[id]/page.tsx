import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import ContactButtons from '@/components/site/ContactButtons'
import DescriptionSwitch from '@/components/site/DescriptionSwitch'
import EnquiryForm from '@/components/site/EnquiryForm'
import Gallery from '@/components/site/Gallery'
import ListingAbout from '@/components/site/ListingAbout'
import ListingFacts from '@/components/site/ListingFacts'
import { isSampleListing } from '@/lib/site/format'
import ShareButton from '@/components/site/ShareButton'
import SiteShell from '@/components/site/SiteShell'
import { enquiryName } from '@/lib/site/theme'
import StickyBar from '@/components/site/StickyBar'
import TrackingBeacon from '@/components/site/TrackingBeacon'
import VerifiedFacts from '@/components/site/VerifiedFacts'
import { getAgent, getCatalog, getListing, getListings, getPropertyFacts } from '@/lib/site/api'
import { formatPrice } from '@/lib/site/format'
import { whatsappMessage } from '@/lib/site/links'
import { jsonLdString, listingJsonLd, listingMetadata } from '@/lib/site/seo'
import { agentPath, normalizeSlug, siteOrigin } from '@/lib/site/slug'
import { localityByName, localitySlug } from '@/lib/marketing/localities'
import { BRAND_NAME } from '@/lib/brand'
import DemoRibbon from '../../DemoRibbon'
import type { PublicListing } from '@/lib/site/types'
import { projectForListing } from '@/lib/site/listingProject'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import { getRegisterProjectByRegno, projectPageOfListing } from '@/lib/site/register'

interface Props {
  params: Promise<{ slug: string; id: string }>
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug: rawSlug, id } = await params
  const slug = normalizeSlug(rawSlug)
  const agent = slug ? await getAgent(slug) : null
  const listing = slug && agent ? await getListing(slug, id) : null
  if (!agent || !listing) return { title: 'Property not found', robots: { index: false } }
  const md = listingMetadata(agent, listing)
  // a listing of a project with its own page in search is that page in the agent's colours: the project page is the one to rank
  const regno = listing.rera_no || projectForListing(listing, await getCatalog())?.rera_no
  const shown = isSampleListing(listing.title) ? null : await projectPageOfListing(regno)
  if (shown) md.alternates = { canonical: siteOrigin() + '/projects/' + shown }
  return md
}

export default async function ListingPage({ params }: Props) {
  const { slug: rawSlug, id } = await params
  const slug = normalizeSlug(rawSlug)
  const agent = slug ? await getAgent(slug) : null
  if (!slug || !agent) notFound()
  const l = await getListing(slug, id)
  if (!l) notFound()

  const url = siteOrigin() + agentPath(slug, 'listings/' + l.id)
  const msg = whatsappMessage(agent.agent_name, l, url)
  const phone = agent.phone || (l.agent && l.agent.phone)
  const locality = localityByName(l.locality)
  const fallbackLocalitySlug = locality ? '' : localitySlug(l.locality)
  const localityHref = locality ? `/localities/${locality.slug}` : (fallbackLocalitySlug ? `/localities/${fallbackLocalitySlug}` : '')
  const projectName = (l.project_name || '').trim()
  const project = projectName || l.rera_no || l.about?.project_name ? projectForListing(l, await getCatalog()) : null
  const projectLabel = projectName || project?.name || ''
  // a listing of a MahaRERA project we have a page for gets the whole page (pictures, price sheet, facts, map, the record),
  // with this listing's sheet and photos, in the agent's colours and with enquiries to them (owner 2026-10-30: "the listing
  // is what sells; why should it not have it")
  const register = isSampleListing(l.title) ? null : await getRegisterProjectByRegno(l.rera_no || project?.rera_no)
  // the listing's own number first: a project MahaRERA files in phases is one page under its first phase's number, and the
  // sheet kept for a phase 2 listing is only found by phase 2's (Yashwin Enchante lost its pictures and prices, 2026-10-30)
  const facts = await getPropertyFacts({ rera: l.rera_no || register?.regno || project?.rera_no, project: projectLabel, locality: l.locality, listing: l.id })

  if (register) {
    // the agent's other live listings, same area first: what "More from <agent>" shows instead of other agents' projects
    const own = (await getListings(slug).catch(() => ({ items: [] as PublicListing[] }))).items.filter((x) => x.id !== l.id && !isSampleListing(x.title))
    const others = [...own.filter((x) => x.locality === l.locality), ...own.filter((x) => x.locality !== l.locality)]
    return (
      <SiteShell agent={agent} bottomPad>
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(listingJsonLd(agent, l)) }} />
        <TrackingBeacon agentSlug={slug} listingId={l.id} />
        <DemoRibbon agent={agent} />
        <RegisterProjectPage p={register} siteUrl={siteOrigin()} facts={facts}
          seller={{ slug, name: enquiryName(agent), home: agentPath(slug), listingId: l.id, others,
            photos: (l.media || []).filter((m) => m.kind === 'image').sort((a, b) => a.order - b.order).map((m) => m.url) }} />
      </SiteShell>
    )
  }

  return (
    <SiteShell agent={agent} bottomPad>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(listingJsonLd(agent, l)) }} />
      <TrackingBeacon agentSlug={slug} listingId={l.id} />
      <DemoRibbon agent={agent} />
      <Gallery media={l.media} title={l.title} />

      <div className="mx-auto max-w-5xl space-y-8 px-4 py-6">
        <p className="text-sm">
          <Link href={agentPath(slug) + '#listings'} className="inline-flex min-h-[44px] items-center text-[var(--site-primary)]">&larr; All properties</Link>
        </p>
        <header>
          <p className="text-3xl font-extrabold text-[var(--site-primary)]">{l.price_inr ? formatPrice(l.price_inr, l.transaction) : 'Price on request'}</p>
          {isSampleListing(l.title) && (
            <p role="note" className="mt-2 rounded-lg bg-amber-100 px-3 py-2 text-sm font-semibold text-amber-900">
              Sample listing: an illustration of how a listing looks on {BRAND_NAME}. This home is not available. Tell us what you are looking for and we will find real options.
            </p>
          )}
          <h1 className="mt-1 text-2xl font-bold leading-snug">{l.title}</h1>
          <p className="mt-1 text-slate-600">
            {project ? (
              <Link href={`/projects/${project.slug}`} className="font-semibold text-[var(--site-primary)] underline underline-offset-2">{projectLabel}</Link>
            ) : projectLabel}
            {projectLabel && (l.locality || l.city) ? ', ' : ''}
            {localityHref ? (
              <Link href={localityHref} className="font-semibold text-[var(--site-primary)] underline underline-offset-2">{l.locality}</Link>
            ) : l.locality}
            {l.locality && l.city ? ', ' : ''}
            {l.city}
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
        <VerifiedFacts f={facts} />

        {l.amenities.length > 0 && (
          <section aria-labelledby="amen-title">
            <h2 id="amen-title" className="text-lg font-bold">Amenities</h2>
            <ul className="mt-2 flex list-none flex-wrap gap-2 p-0">
              {l.amenities.map((a) => <li key={a} className="rounded-full bg-slate-100 px-3 py-1.5 text-sm">{a}</li>)}
            </ul>
          </section>
        )}

        <ListingAbout about={l.about} listingAmenities={l.amenities} />

        <EnquiryForm agentSlug={slug} agentName={enquiryName(agent)} agentPhone={phone} listingId={l.id} waMessage={msg} id="enquire" />
      </div>
      <StickyBar agentSlug={slug} phone={phone} waMessage={msg} listingId={l.id} />
    </SiteShell>
  )
}
