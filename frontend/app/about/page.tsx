import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import { getMarketingConfig } from '@/lib/marketing/config'
import { breadcrumbJsonLd, jsonLdString, organizationJsonLd, pageMetadata } from '@/lib/marketing/seo'
import { socialLinks } from '@/lib/marketing/social'
import { BRAND_NAME, BRAND_NAME_DEVANAGARI } from '@/lib/brand'
import { HOW } from '@/lib/site/listRules'
import { TEAM, teamAddress, teamForOrganization } from '@/lib/site/team'

// Who is behind the site and how its facts are made (owner 2026-11-04, the SEO review's first item): home buying is a money
// decision, so Google and the AI assistants look for this page before trusting a site's lists, and /about answered 404.
// Every sentence here is something the code does (backend seo/facets.py, areastats/pages.py). Who answers for it is House Deal
// (owner 2026-11-13), with its office, phone and MahaRERA number (lib/site/team); no person is named.

const PATH = '/about'
const TITLE = `About ${BRAND_NAME}: how we check Pune's new projects`
// the team is House Deal (owner 2026-11-13); still no person named
const DESCRIPTION = `What ${BRAND_NAME} is, who runs it (House Deal, Upper Kharadi), where every fact comes from and how the top, new launch and ready lists are ranked.`

export const metadata: Metadata = pageMetadata(getMarketingConfig(), { title: TITLE, description: DESCRIPTION, path: PATH })

const h2 = 'text-2xl font-semibold tracking-tight text-slate-900'
const p = 'mt-3 leading-relaxed text-slate-800'
const ul = 'mt-3 list-disc space-y-2 pl-6 leading-relaxed text-slate-800'
const a = 'font-semibold text-[#0f2340] underline underline-offset-2'

const LISTS: { name: string; how: string; example: string }[] = [
  { name: 'Top projects', how: HOW.top, example: '/projects/area/kharadi/top' },
  { name: 'New launches', how: HOW['new-launches'], example: '/projects/area/kharadi/new-launches' },
  { name: 'Ready to move', how: HOW['ready-to-move'], example: '/projects/area/kharadi/ready-to-move' },
]

export default function AboutPage() {
  const cfg = getMarketingConfig()
  const org = { ...organizationJsonLd(cfg, DESCRIPTION, Object.values(socialLinks())), alternateName: [BRAND_NAME_DEVANAGARI], ...teamForOrganization(cfg.siteUrl) }
  const ld = [
    { '@context': 'https://schema.org', '@type': 'AboutPage', name: TITLE, url: cfg.siteUrl + PATH, description: DESCRIPTION, mainEntity: org },
    breadcrumbJsonLd(cfg.siteUrl, [{ name: 'Home', path: '/' }, { name: 'About', path: PATH }]),
  ]
  return (
    <MarketingShell>
      {ld.map((x, i) => <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(x) }} />)}
      <article className="mx-auto max-w-3xl px-4 py-10 sm:py-14">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">About {BRAND_NAME}</h1>
        <p className="mt-4 text-lg leading-relaxed text-slate-800">
          {BRAND_NAME} ({BRAND_NAME_DEVANAGARI}: आवास, home, and सेतु, bridge) is a Pune website where home buyers look up every new
          project in the city&apos;s main areas with its public record: the possession date the builder filed with MahaRERA and whether
          it moved, how many homes are booked, and the builder&apos;s record on its other Pune projects. Then they can ask local agents
          about the ones they like.
        </p>

        <section aria-labelledby="what-title" className="mt-10">
          <h2 id="what-title" className={h2}>What you find here</h2>
          <ul className={ul}>
            <li>A page for each registered project, with its MahaRERA number, filed possession date, towers and homes booked.</li>
            <li>Lists for each area: <Link href="/projects/area/kharadi/top" className={a}>top projects</Link>, new launches, ready to move, and homes by size and price.</li>
            <li>A page for each <Link href="/builders" className={a}>builder</Link>, with how often its filed dates moved.</li>
            <li><Link href="/localities" className={a}>Area guides</Link> on living in each area, and the <Link href="/pune-maharera-tracker" className={a}>Pune MahaRERA tracker</Link>.</li>
            <li>A free <Link href="/home-plan" className={a}>home plan</Link> for families working in East Pune, and a <Link href="/check" className={a}>check</Link> for a project you have already booked.</li>
          </ul>
        </section>

        <section aria-labelledby="how-we-check" className="mt-10">
          <h2 id="how-we-check" className={h2}>How we check every project</h2>
          <ul className={ul}>
            <li><b>The MahaRERA register</b> is where the facts start: registration, the completion date filed and every change to it,
              the number of homes and how many are booked. Booked counts are the builders&apos; own, filed with MahaRERA each quarter. We read
              the register again and again, and every page shows the date we last read it.</li>
            <li><b>Prices</b> come from the builder&apos;s own site, from two property sites that agree, or from a local agent who quotes it.
              Each shows when it was read, and the project page&apos;s Sources panel says where it came from. Where only one site gives a
              price, we show a rounded rough guide marked as one, never as a price. Where we have no price, we say so.</li>
            <li><b>Towers and phases</b> of one project are one page and count once in every list.</li>
            <li><b>Places nearby</b> are measured from the project&apos;s own pin on the map, never from a brochure.</li>
            <li><b>Projects not yet registered</b> are never shown as for sale. A builder&apos;s announced project gets a page marked
              &ldquo;not yet registered with MahaRERA&rdquo;, with no price.</li>
          </ul>
        </section>

        <section aria-labelledby="how-we-rank" className="mt-10">
          <h2 id="how-we-rank" className={h2}>How the lists are ranked</h2>
          <p className={p}>Every list is worked out from the records above by the same rules for every area, and each list page repeats its rule.</p>
          <dl className="mt-4 space-y-5">
            {LISTS.map((l) => (
              <div key={l.name}>
                <dt className="font-semibold text-slate-900"><Link href={l.example} className={a}>{l.name}</Link></dt>
                <dd className="mt-1 leading-relaxed text-slate-800">{l.how}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section aria-labelledby="never-title" className="mt-10">
          <h2 id="never-title" className={h2}>What we never do</h2>
          <ul className={ul}>
            <li>Take money to put a project on the top, new launch or ready to move lists, or to move it up them. No builder pays to be on these lists.</li>
            <li>Rank a project higher on them because an agent who uses {BRAND_NAME} sells it. An agent&apos;s listing is marked on the project&apos;s page, and that is all.</li>
            <li>Call a project &ldquo;the best&rdquo;, or invent prices, distances or predictions. Every fact says where it came from.</li>
          </ul>
        </section>

        <section aria-labelledby="agents-title" className="mt-10">
          <h2 id="agents-title" className={h2}>{BRAND_NAME} and agents</h2>
          <p className={p}>
            We also make tools for real estate agents in Pune: their own page, buyer enquiries and posts made for them. That is
            how {BRAND_NAME} works as a business. Using the site is free for buyers.{' '}
            <a href="/agents" className={a}>For agents</a>.
          </p>
        </section>

        {/* the team behind the site (owner 2026-11-13: House Deal's contact is the main contact, House Deal the main team): only what
            House Deal publishes about itself (lib/site/team); its own site is linked as theirs */}
        <section aria-labelledby="partner-title" className="mt-10" data-testid="about-partner">
          <h2 id="partner-title" className={h2}>Who runs {BRAND_NAME}</h2>
          <p className={p}>
            The team behind {BRAND_NAME} is <a href={TEAM.page} className={a}>{TEAM.name}</a>, {TEAM.what}, registered with MahaRERA as a
            real estate agent ({TEAM.rera}). Its office is at {teamAddress()}. The team answers the enquiries sent from this website and
            fixes a page when someone tells us it is wrong. {TEAM.name} also sells homes in some of the projects here: its listings are
            marked on their pages, and that never moves a project up our lists.{' '}
            <a href="/contact" className={a}>Contact us</a> or see{' '}
            <a href={TEAM.website} target="_blank" rel="noopener noreferrer" className={a}>House Deal&apos;s own website<span className="sr-only"> (opens in a new tab)</span></a>.
          </p>
        </section>

        <section aria-labelledby="fix-title" className="mt-10">
          <h2 id="fix-title" className={h2}>Found a mistake?</h2>
          <p className={p}>
            Tell us through the <a href="/enquire?src=about_correction" className={a}>enquiry form</a>, a call or an email (on the <a href="/contact" className={a}>contact page</a>), or a message on our Facebook or Instagram page, with the project&apos;s name. We
            check it against MahaRERA and the builder&apos;s documents and fix the page, which then shows the new date.
          </p>
        </section>

        <p className="mt-10 rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-700">
          This is general information from public records, not investment or legal advice. Check the MahaRERA record and your agreement before you pay.
        </p>
      </article>
    </MarketingShell>
  )
}
