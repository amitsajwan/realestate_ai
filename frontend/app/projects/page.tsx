import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import ProjectCard from '@/components/site/ProjectCard'
import { getMarketingConfig } from '@/lib/marketing/config'
import { LOCALITIES, localityByName } from '@/lib/marketing/localities'
import { breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { buyerEnquirePath } from '@/components/marketing/siteLinks'
import { getCatalog } from '@/lib/site/api'
import { byLocality } from '@/lib/site/projects'
import { getRegisterProjects } from '@/lib/site/register'
import type { RegisterListItem } from '@/lib/site/register'

export const revalidate = 300

export async function generateMetadata(): Promise<Metadata> {
  return pageMetadata(getMarketingConfig(), {
    title: 'New projects in Pune, checked on MahaRERA',
    description: 'Every MahaRERA project in Kharadi, Wagholi, Lohegaon, Hinjawadi, Wakad, Baner and more: the completion date filed, homes booked, and prices quoted by local agents.',
    path: '/projects',
  })
}

export default async function ProjectsPage() {
  const cfg = getMarketingConfig()
  const catalog = await getCatalog()
  const groups = byLocality(catalog)
  const listed = new Set(catalog.map((p) => p.rera_no))
  const register = (await getRegisterProjects()).filter((r) => !listed.has(r.regno))
  const byArea = LOCALITIES.map((l) => ({ l, items: register.filter((r) => r.area === l.key).sort((a, b) => a.name.localeCompare(b.name)) }))
    .filter((g) => g.items.length > 0)
  return (
    <MarketingShell>
      <div className="mx-auto max-w-5xl px-4 py-10 sm:py-14" style={AVASETU_SITE_VARS}>
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(breadcrumbJsonLd(cfg.siteUrl, [
          { name: 'Home', path: '/' }, { name: 'Projects', path: '/projects' },
        ])) }} />
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">New projects, checked on MahaRERA</h1>
        <p className="mt-4 max-w-3xl text-lg leading-relaxed text-slate-800">
          For each project we show the price as quoted by a local agent, and what MahaRERA&apos;s public record says: the completion
          date the builder has filed, whether it has moved, and how many homes are booked. When the builder&apos;s own target is
          earlier than the MahaRERA date, we say so.
        </p>

        {groups.length === 0 ? (
          <p className="mt-8 rounded-xl bg-slate-50 p-4 text-slate-700">
            No projects are listed yet. <a href={buyerEnquirePath()} className="font-semibold text-[#0f2340] underline underline-offset-2">Tell us what you are looking for</a> and
            we will send you options as they come.
          </p>
        ) : groups.map(([locality, items]) => {
          const area = localityByName(locality)
          return (
            <section key={locality} aria-labelledby={`area-${locality}`} className="mt-10">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h2 id={`area-${locality}`} className="text-2xl font-bold text-slate-900">Projects in {locality}</h2>
                {area && (
                  <Link href={`/localities/${area.slug}`} className="inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">
                    {area.name} buyer guide
                  </Link>
                )}
              </div>
              <ul className="mt-4 grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3">
                {items.map((p) => <li key={p.slug}><ProjectCard p={p} href={`/projects/${p.slug}`} /></li>)}
              </ul>
            </section>
          )
        })}

        {byArea.length > 0 && (
          <section aria-labelledby="register-title" className="mt-14">
            <h2 id="register-title" className="text-2xl font-bold text-slate-900">Every MahaRERA project in our areas</h2>
            <p className="mt-2 max-w-3xl text-slate-700">
              Our page for each project: the completion date filed with MahaRERA and how many homes are booked, with the date we read
              the record. {register.length} projects so far; new ones are added as MahaRERA lists them.
            </p>
            {byArea.map(({ l, items }, i) => (
              <details key={l.key} open={i === 0} className="mt-4 rounded-xl border border-slate-200 bg-white p-4">
                <summary className="flex min-h-[44px] cursor-pointer items-center justify-between gap-3 text-lg font-semibold text-slate-900">
                  <span>{l.name} <span className="font-normal text-slate-600">· {items.length} projects</span></span>
                </summary>
                <ul className="mt-3 list-none columns-1 p-0 sm:columns-2" data-testid={`register-${l.key}`}>
                  {items.map((r: RegisterListItem) => (
                    <li key={r.slug} className="break-inside-avoid py-1">
                      <Link href={`/projects/${r.slug}`} className="font-medium text-[#0f2340] underline underline-offset-2">{r.name}</Link>
                      {r.completion_now && <span className="ml-1 text-sm text-slate-600">· completion filed {r.completion_now.slice(0, 4)}</span>}
                    </li>
                  ))}
                </ul>
                <Link href={`/localities/${l.slug}`} className="mt-2 inline-flex min-h-[44px] items-center text-sm text-[#0f2340] underline underline-offset-2">{l.name} buyer guide</Link>
              </details>
            ))}
          </section>
        )}

        <p className="mt-10 text-sm text-slate-600">
          Prices change often and are as quoted by the agent named on each project. MahaRERA facts are read from the public record on the
          date shown on each page. This is general information, not investment or legal advice.
        </p>
      </div>
    </MarketingShell>
  )
}
