import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound, permanentRedirect } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import ContactButtons from '@/components/site/ContactButtons'
import EnquiryForm from '@/components/site/EnquiryForm'
import ProjectCard from '@/components/site/ProjectCard'
import ProjectDetails from '@/components/site/ProjectDetails'
import { BRAND_NAME } from '@/lib/brand'
import { getMarketingConfig } from '@/lib/marketing/config'
import { localityByName } from '@/lib/marketing/localities'
import { breadcrumbJsonLd, jsonLdString } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { getCatalog, getCatalogProject, getPropertyFacts } from '@/lib/site/api'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import { pageMetadata } from '@/lib/marketing/seo'
import { getRegisterProject } from '@/lib/site/register'
import { bhkRange, mainAgent, priceRange, projectWhatsAppMessage } from '@/lib/site/projects'
import { catalogProjectMetadata, projectJsonLd } from '@/lib/site/seo'
import { agentPath } from '@/lib/site/slug'
import type { CatalogProject } from '@/lib/site/types'

export const revalidate = 300

type Props = { params: Promise<{ slug: string }> }

const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+){0,15}$/

async function load(params: Props['params']): Promise<CatalogProject | null> {
  const { slug } = await params
  if (!SLUG.test(slug)) return null
  try {
    return await getCatalogProject(slug)
  } catch (e) {
    // the agent catalog could not be reached (a restart, a timeout): our own register page still serves the project when it has
    // one; only with neither does the temporary-error page show (never a 404)
    if (await getRegisterProject(slug).catch(() => null)) return null
    throw e
  }
}

/** A project with no agent listing yet: Avasetu's own page from the MahaRERA register (docs/plan/project-pages.md). */
async function loadRegister(params: Props['params']) {
  const { slug } = await params
  return SLUG.test(slug) ? getRegisterProject(slug) : null
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const p = await load(params)
  if (p && p.agents.length) return catalogProjectMetadata(p, priceRange(p) + ', ' + bhkRange(p.bhk_options))
  const r = await loadRegister(params)
  if (!r) return { title: 'Project not found', robots: { index: false } }
  const meta = pageMetadata(getMarketingConfig(), {
    title: `${r.name}${r.area ? `, ${r.area.name}` : ''}: MahaRERA completion date and homes booked`,
    description: r.paragraph.slice(0, 155),
    path: `/projects/${r.slug}`,
  })
  return r.indexable ? meta : { ...meta, robots: { index: false, follow: true } }   // thin pages stay out of search until filled in
}

export default async function SharedProjectPage({ params }: Props) {
  const { slug } = await params
  const p = await load(params)
  if (!p || !p.agents.length) {
    const r = await loadRegister(params)
    if (!r) notFound()
    if (r.slug !== slug) permanentRedirect(`/projects/${r.slug}`)
    // an agent lists this project: its shared page (with the agents) is the project's page
    const listed = (await getCatalog()).find((x) => x.rera_no === r.regno && x.agents.length)
    if (listed) permanentRedirect(`/projects/${listed.slug}`)
    const facts = await getPropertyFacts({ rera: r.regno, project: r.name, locality: r.area?.name }).catch(() => null)
    return (
      <MarketingShell>
        <RegisterProjectPage p={r} siteUrl={getMarketingConfig().siteUrl} facts={facts} />
      </MarketingShell>
    )
  }
  if (p.slug !== slug) permanentRedirect(`/projects/${p.slug}`) // an agent's own slug for the same project
  const cfg = getMarketingConfig()
  const main = mainAgent(p)
  const url = cfg.siteUrl + '/projects/' + p.slug
  const msg = projectWhatsAppMessage(p, url)
  const area = localityByName(p.locality)
  const others = (await getCatalog()).filter((x) => x.slug !== p.slug)
  const similar = [...others.filter((x) => x.locality === p.locality), ...others.filter((x) => x.locality !== p.locality)].slice(0, 3)
  const ld = [
    projectJsonLd(p, url),
    breadcrumbJsonLd(cfg.siteUrl, [
      { name: 'Home', path: '/' }, { name: 'Projects', path: '/projects' }, { name: p.name, path: '/projects/' + p.slug },
    ]),
  ]

  return (
    <MarketingShell>
      <div className="mx-auto max-w-5xl space-y-8 px-4 py-8 sm:py-10" style={AVASETU_SITE_VARS}>
        {ld.map((x, i) => <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(x) }} />)}
        <nav aria-label="Breadcrumb" className="text-sm">
          <Link href="/projects" className="inline-flex min-h-[44px] items-center text-[#0f2340] underline underline-offset-2">All projects</Link>
          {area && <> <span aria-hidden className="px-1 text-slate-400">/</span> <Link href={`/localities/${area.slug}`} className="inline-flex min-h-[44px] items-center text-[#0f2340] underline underline-offset-2">{area.name}</Link></>}
        </nav>

        <header>
          <p className="text-sm font-bold uppercase tracking-wide text-[var(--site-accent-text)]">{p.locality}, Pune</p>
          <h1 className="mt-1 text-3xl font-extrabold leading-tight text-slate-900">{p.name}</h1>
          <p className="mt-1 text-slate-600">by {p.builder}{p.rera?.promoter ? ` (promoter on MahaRERA: ${p.rera.promoter})` : ''}</p>
          <p className="mt-3 text-2xl font-extrabold text-[var(--site-primary)]">{priceRange(p)} <span className="text-base font-semibold text-slate-700">· {bhkRange(p.bhk_options)}</span></p>
          {p.positioning && <p className="mt-2 max-w-2xl text-lg text-slate-800">{p.positioning}</p>}
          {area && (
            <p className="mt-2 text-sm">
              <Link href={`/localities/${area.slug}`} className="inline-flex min-h-[44px] items-center font-semibold text-[var(--site-primary)] underline underline-offset-2">
                Buyer guide to {area.name}: who it suits, commute and what to check
              </Link>
            </p>
          )}
          <div className="mt-4 max-w-sm">
            <ContactButtons agentSlug={main.slug} phone={main.phone ?? undefined} waMessage={msg} size="md" />
          </div>
        </header>

        <ProjectDetails p={p} agentName={main.name} />

        <section aria-labelledby="agents-title">
          <h2 id="agents-title" className="text-xl font-bold">{p.agents.length > 1 ? 'Agents for this project' : 'Agent for this project'}</h2>
          <ul className="mt-3 grid list-none gap-3 p-0 sm:grid-cols-2">
            {p.agents.map((a) => (
              <li key={a.slug} className="rounded-2xl border border-slate-200 p-4">
                <p className="font-bold">{a.name}</p>
                <Link href={agentPath(a.slug, 'projects/' + a.project_slug)} className="mt-1 inline-flex min-h-[44px] items-center font-semibold text-[var(--site-primary)] underline underline-offset-2">
                  {p.name} on {a.name}&apos;s page
                </Link>
              </li>
            ))}
          </ul>
          <p className="mt-2 text-xs text-slate-600">An enquiry here goes to {main.name}.</p>
        </section>

        {similar.length > 0 && (
          <section aria-labelledby="similar-title">
            <h2 id="similar-title" className="text-xl font-bold">Other projects</h2>
            <ul className="mt-3 grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3">
              {similar.map((x) => <li key={x.slug}><ProjectCard p={x} href={`/projects/${x.slug}`} /></li>)}
            </ul>
          </section>
        )}

        <EnquiryForm agentSlug={main.slug} agentName={BRAND_NAME} agentPhone={main.phone ?? undefined} topic={`${p.name} (${p.rera_no})`} waMessage={msg} id="enquire" />
      </div>
    </MarketingShell>
  )
}
