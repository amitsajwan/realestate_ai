import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import ContactButtons from '@/components/site/ContactButtons'
import EnquiryForm from '@/components/site/EnquiryForm'
import ProjectDetails from '@/components/site/ProjectDetails'
import SiteShell from '@/components/site/SiteShell'
import StickyBar from '@/components/site/StickyBar'
import TrackingBeacon from '@/components/site/TrackingBeacon'
import { getAgent, getProject } from '@/lib/site/api'
import { bhkRange, priceRange, projectWhatsAppMessage } from '@/lib/site/projects'
import { jsonLdString, projectJsonLd, projectMetadata } from '@/lib/site/seo'
import { breadcrumbJsonLd } from '@/lib/marketing/seo'
import { localityByName } from '@/lib/marketing/localities'
import { agentPath, normalizeSlug, siteOrigin } from '@/lib/site/slug'
import { displayName } from '@/lib/site/theme'
import { BRAND_NAME } from '@/lib/brand'
import DemoRibbon from '../../DemoRibbon'

interface Props {
  params: Promise<{ slug: string; project: string }>
}

async function load(params: Props['params']) {
  const { slug: rawSlug, project } = await params
  const slug = normalizeSlug(rawSlug)
  const agent = slug ? await getAgent(slug) : null
  const p = slug && agent ? await getProject(slug, project) : null
  return { slug, agent, p }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { agent, p } = await load(params)
  if (!agent || !p) return { title: 'Project not found', robots: { index: false } }
  return projectMetadata(agent, p, priceRange(p) + ', ' + bhkRange(p.bhk_options))
}

export default async function ProjectPage({ params }: Props) {
  const { slug, agent, p } = await load(params)
  if (!slug || !agent || !p) notFound()
  const name = displayName(agent)
  const url = siteOrigin() + agentPath(slug, 'projects/' + p.slug)
  const msg = projectWhatsAppMessage(p, url)
  const ld = projectJsonLd(p, url)
  const area = localityByName(p.locality)
  const crumbs = breadcrumbJsonLd(siteOrigin(), [
    { name: 'Home', path: '/' }, { name: name, path: agentPath(slug) }, { name: p.name, path: agentPath(slug, 'projects/' + p.slug) },
  ])

  return (
    <SiteShell agent={agent} bottomPad>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(ld) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(crumbs) }} />
      <TrackingBeacon agentSlug={slug} />
      <DemoRibbon agent={agent} />

      <div className="mx-auto max-w-5xl space-y-8 px-4 py-6">
        <p className="text-sm">
          <Link href={agentPath(slug) + '#projects'} className="inline-flex min-h-[44px] items-center text-[var(--site-primary)]">&larr; All projects</Link>
        </p>

        <header>
          <p className="text-sm font-bold uppercase tracking-wide text-[var(--site-accent-text)]">{p.locality}, Pune</p>
          <h1 className="mt-1 text-3xl font-extrabold leading-tight">{p.name}</h1>
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
          <div className="mt-4 hidden max-w-sm md:flex">
            <ContactButtons agentSlug={slug} phone={agent.phone} waMessage={msg} size="md" />
          </div>
        </header>

        <ProjectDetails p={p} agentName={name} />

        <p className="text-sm">
          <Link href={agentPath(slug, 'projects/compare')} className="font-semibold text-[var(--site-primary)]">Compare all projects side by side &rarr;</Link>
        </p>

        <EnquiryForm agentSlug={slug} agentName={BRAND_NAME} agentPhone={agent.phone} topic={`${p.name} (${p.rera_no})`} waMessage={msg} id="enquire" />
      </div>
      <StickyBar agentSlug={slug} phone={agent.phone} waMessage={msg} />
    </SiteShell>
  )
}
