import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import MarketingShell from '@/components/marketing/MarketingShell'
import EnquiryForm from '@/components/site/EnquiryForm'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { DETAILS_COMING_PATH, detailsComing } from '@/lib/site/detailsComing'
import { agentOffers } from '@/lib/site/offers'
import { displayName, getRegisterProjects, longDay, projectSummary } from '@/lib/site/register'

// Our areas' new projects whose pages are not in search yet, on one page instead of hidden (lib/site/detailsComing). This page is in
// search though they are not (owner 2026-11-19: "what is preventing to have this page indexed"): one list of dated MahaRERA records is
// a page of its own, as an area list is; each project page alone says too little. Its title is "newly registered", so it does not
// compete with /projects for "new projects in Pune".

export const revalidate = 300

const HOUSE_AGENT = process.env.NEXT_PUBLIC_DEFAULT_AGENT_SLUG || 'avasetu'

export function generateMetadata(): Metadata {
  return pageMetadata(getMarketingConfig(), {
    title: 'Newly Registered MahaRERA Projects in Pune: What We Know So Far',
    description: 'Projects newly registered with MahaRERA in Kharadi, Wagholi, Lohegaon and our other Pune areas: builder, possession date filed and homes booked, while we collect prices, pictures and floor plans.',
    path: DETAILS_COMING_PATH,
  })
}

export default async function DetailsComingPage() {
  const [all, offers] = await Promise.all([getRegisterProjects(undefined, true), agentOffers()])
  const groups = detailsComing(all, new Set(offers.keys()))
  const total = groups.reduce((n, g) => n + g.items.length, 0)
  const cfg = getMarketingConfig()
  const url = cfg.siteUrl + DETAILS_COMING_PATH
  const newest = groups.flatMap((g) => g.items).map((r) => r.listed_or_updated ?? '').sort().pop() || null
  const ld = [
    breadcrumbJsonLd(cfg.siteUrl, [{ name: 'Home', path: '/' }, { name: 'Projects', path: '/projects' }, { name: 'Newly registered', path: DETAILS_COMING_PATH }]),
    { '@context': 'https://schema.org', '@type': 'ItemList', name: 'Newly registered MahaRERA projects in Pune',
      itemListElement: groups.flatMap((g) => g.items).map((r, i) => ({ '@type': 'ListItem', position: i + 1, name: displayName(r), url: `${cfg.siteUrl}/projects/${r.slug}` })) },
  ]
  return (
    <MarketingShell>
      <div className="mx-auto max-w-5xl space-y-6 px-4 py-8 sm:py-10" style={AVASETU_SITE_VARS}>
        {ld.map((x, i) => <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(x) }} />)}
        <nav aria-label="Breadcrumb" className="text-sm text-slate-600">
          <Link href="/" className="underline underline-offset-2">Home</Link> / <Link href="/projects" className="underline underline-offset-2">Projects</Link>
        </nav>
        <h1 className="text-3xl font-bold text-slate-900">Newly registered projects in Pune: what we know so far</h1>
        <p className="max-w-3xl text-lg leading-relaxed text-slate-800">
          Our team is working on these projects. We are collecting prices, the builder&apos;s pictures and floor plans, and checking
          them before they go on a full page. Until then, this is what we have now: each project&apos;s MahaRERA record. If one of them
          interests you, ask us and we send you what we find first.
        </p>
        {total === 0 ? (
          <p className="text-slate-700">Every project in our areas has its full page now. <Link href="/projects" className="underline underline-offset-2">See all projects</Link>.</p>
        ) : (
          <>
            <p className="text-sm text-slate-600">{total} projects in {groups.length} {groups.length === 1 ? 'area' : 'areas'}, the newest MahaRERA records first.{newest ? ` Updated ${longDay(newest)}.` : ''}</p>
            {groups.map((g) => (
              <section key={g.key} aria-labelledby={`area-${g.key}`} data-testid="details-coming-area">
                <h2 id={`area-${g.key}`} className="text-xl font-bold text-slate-900">{g.area} <span className="text-base font-normal text-slate-500">({g.items.length})</span></h2>
                <ul className="mt-3 grid list-none gap-2 p-0 sm:grid-cols-2">
                  {g.items.map((r) => {
                    const line = projectSummary(r)
                    return (
                      <li key={r.slug}>
                        <Link href={`/projects/${r.slug}`} className="block min-h-[44px] rounded-xl border border-slate-200 bg-white px-3 py-2 no-underline hover:border-[#0f2340]">
                          <span className="block font-semibold text-[#0f2340]">{displayName(r)}</span>
                          {line && <span className="text-sm text-slate-600">{line}</span>}
                        </Link>
                      </li>
                    )
                  })}
                </ul>
              </section>
            ))}
          </>
        )}
        <section id="enquire" aria-labelledby="enq-title" className="scroll-mt-20 rounded-2xl border border-slate-200 bg-white p-4 sm:p-6">
          <h2 id="enq-title" className="text-xl font-semibold text-slate-900">Ask about one of these projects</h2>
          <p className="mt-1 text-sm text-slate-600">Tell us which project; the Avasetu team sends you the prices and pictures as we get them. We never share your number without your OK.</p>
          <div className="mt-4">
            <EnquiryForm agentSlug={HOUSE_AGENT} agentName="Avasetu" topic="A new project we are still collecting details on"
              waMessage={`Hi, I want details of a new project from this list: ${url}`} />
          </div>
        </section>
      </div>
    </MarketingShell>
  )
}
