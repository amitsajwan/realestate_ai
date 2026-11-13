import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString, organizationJsonLd, pageMetadata } from '@/lib/marketing/seo'
import { socialLinks } from '@/lib/marketing/social'
import { BRAND_NAME, BRAND_NAME_DEVANAGARI } from '@/lib/brand'
import { TEAM, teamAddress, teamForOrganization } from '@/lib/site/team'

// Who answers for the site and how to reach them (owner 2026-11-13: House Deal is the team behind Avasetu). /contact answered
// 404, and a site about a money decision with no address or phone is what Google's raters are told to distrust (rater
// guidelines 2.5.3). Only what House Deal publishes about itself (lib/site/team).

const PATH = '/contact'
const TITLE = `Contact ${BRAND_NAME}: House Deal, Upper Kharadi, Pune`
const DESCRIPTION = `${BRAND_NAME} is run by House Deal, a MahaRERA-registered agent (${TEAM.rera}) at RTC Silver, Upper Kharadi. Call, write or visit.`

export const metadata: Metadata = pageMetadata(getMarketingConfig(), { title: TITLE, description: DESCRIPTION, path: PATH })

const h2 = 'text-2xl font-semibold tracking-tight text-slate-900'
const p = 'mt-3 leading-relaxed text-slate-800'
const a = 'font-semibold text-[#0f2340] underline underline-offset-2'

export default function ContactPage() {
  const cfg = getMarketingConfig()
  const org = { ...organizationJsonLd(cfg, DESCRIPTION, Object.values(socialLinks())), alternateName: [BRAND_NAME_DEVANAGARI], ...teamForOrganization(cfg.siteUrl) }
  const ld = [
    { '@context': 'https://schema.org', '@type': 'ContactPage', name: TITLE, url: cfg.siteUrl + PATH, description: DESCRIPTION, mainEntity: org },
    breadcrumbJsonLd(cfg.siteUrl, [{ name: 'Home', path: '/' }, { name: 'Contact', path: PATH }]),
  ]
  return (
    <MarketingShell>
      {ld.map((x, i) => <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(x) }} />)}
      <article className="mx-auto max-w-3xl px-4 py-10 sm:py-14">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">Contact {BRAND_NAME}</h1>
        <p className="mt-4 text-lg leading-relaxed text-slate-800">
          The team behind {BRAND_NAME} is <a href={TEAM.page} className={a}>{TEAM.name}</a>, {TEAM.what}. They answer every enquiry
          sent from this website, take buyers on site visits and fix a page when someone tells us it is wrong.
        </p>

        <section aria-labelledby="reach-title" className="mt-10" data-testid="contact-team">
          <h2 id="reach-title" className={h2}>How to reach us</h2>
          <dl className="mt-4 grid gap-x-6 gap-y-3 sm:grid-cols-[10rem_1fr]">
            <dt className="font-semibold text-slate-900">Office</dt>
            <dd><address className="not-italic text-slate-800">{TEAM.name}<br />{teamAddress()}</address></dd>
            <dt className="font-semibold text-slate-900">Phone</dt>
            <dd><a href={`tel:${TEAM.tel}`} className={a}>{TEAM.phone}</a></dd>
            <dt className="font-semibold text-slate-900">Email</dt>
            <dd><a href={`mailto:${TEAM.email}`} className={a}>{TEAM.email}</a></dd>
            <dt className="font-semibold text-slate-900">MahaRERA agent</dt>
            <dd className="text-slate-800">{TEAM.rera}{' '}
              (<a href="https://maharera.maharashtra.gov.in" target="_blank" rel="noopener noreferrer" className={a}>check it on MahaRERA<span className="sr-only"> (opens in a new tab)</span></a>)</dd>
            <dt className="font-semibold text-slate-900">Website</dt>
            <dd><a href={TEAM.website} target="_blank" rel="noopener noreferrer" className={a}>{TEAM.website.replace(/^https:\/\//, '')}<span className="sr-only"> (opens in a new tab)</span></a></dd>
          </dl>
          <p className={p}>
            Or <a href="/enquire?src=contact" className={a}>tell us what you need</a> and we call or WhatsApp you back. We never share your
            number without your OK.
          </p>
        </section>

        <section aria-labelledby="fix-title" className="mt-10">
          <h2 id="fix-title" className={h2}>Found a mistake on a page?</h2>
          <p className={p}>
            Call, write or use the <a href="/enquire?src=about_correction" className={a}>enquiry form</a> with the project&apos;s name. We check
            it against MahaRERA and the builder&apos;s documents and fix the page, which then shows the new date.{' '}
            <Link href="/about#how-we-check" className={a}>How we check every project</Link>.
          </p>
        </section>

        <p className="mt-10 rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-700">
          {TEAM.name} also sells homes in some of the projects on this site. Its listings are marked on their pages, and that never
          moves a project up {BRAND_NAME}&apos;s lists, which are worked out from MahaRERA records by the same rules for every project.
        </p>
      </article>
    </MarketingShell>
  )
}
