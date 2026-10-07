import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import SiteShell from '@/components/site/SiteShell'
import TrackingBeacon from '@/components/site/TrackingBeacon'
import { getAgent, getProjects } from '@/lib/site/api'
import { formatPrice, groupIndian } from '@/lib/site/format'
import { bhkRange, formatDay, minPerSqft } from '@/lib/site/projects'
import { withPreview } from '@/lib/site/seo'
import { agentPath, normalizeSlug } from '@/lib/site/slug'
import { displayName } from '@/lib/site/theme'
import DemoRibbon from '../../DemoRibbon'

interface Props {
  params: Promise<{ slug: string }>
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const slug = normalizeSlug((await params).slug)
  const agent = slug ? await getAgent(slug) : null
  if (!agent) return { title: 'Agent not found', robots: { index: false } }
  return withPreview(agent, { title: `Compare projects | ${agent.agent_name}` })
}

export default async function ComparePage({ params }: Props) {
  const slug = normalizeSlug((await params).slug)
  const agent = slug ? await getAgent(slug) : null
  if (!slug || !agent) notFound()
  const projects = await getProjects(slug)
  if (!projects.length) notFound()
  const name = displayName(agent)
  const rows: { k: string; v: (p: (typeof projects)[number]) => React.ReactNode }[] = [
    { k: 'Area', v: (p) => p.locality },
    { k: 'Starting price', v: (p) => (p.price_min != null ? formatPrice(p.price_min) : '—') },
    { k: 'Homes', v: (p) => bhkRange(p.bhk_options) },
    { k: 'From, per sq ft', v: (p) => { const v = minPerSqft(p); return v != null ? '₹' + groupIndian(v) : '—' } },
    { k: 'Carpet area', v: (p) => { const a = p.configurations.map((c) => c.carpet_sqft); return a.length ? `${Math.min(...a)}–${Math.max(...a)} sq ft` : '—' } },
    { k: "Builder's target", v: (p) => formatDay(p.possession_target) || '—' },
    { k: 'MahaRERA date', v: (p) => formatDay(p.rera?.completion_now) || '—' },
    { k: 'Homes booked', v: (p) => (p.booked_pct != null ? `${p.booked_pct}% of ${p.rera?.units_total}` : '—') },
    { k: 'MahaRERA no.', v: (p) => p.rera_no },
  ]

  return (
    <SiteShell agent={agent}>
      <TrackingBeacon agentSlug={slug} />
      <DemoRibbon agent={agent} />
      <div className="mx-auto max-w-5xl space-y-6 px-4 py-6">
        <p className="text-sm">
          <Link href={agentPath(slug) + '#projects'} className="inline-flex min-h-[44px] items-center text-[var(--site-primary)]">&larr; All projects</Link>
        </p>
        <header>
          <h1 className="text-3xl font-extrabold">Compare {projects.length} projects</h1>
          <p className="mt-1 text-slate-700">Prices and sizes as quoted by {name}. Dates and bookings from MahaRERA&apos;s public record.</p>
        </header>
        <div className="overflow-x-auto rounded-2xl border border-slate-200">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="bg-[var(--site-primary)] text-[var(--site-on-primary)]">
                <th scope="col" className="sticky left-0 bg-[var(--site-primary)] px-3 py-3 font-semibold">&nbsp;</th>
                {projects.map((p) => (
                  <th key={p.slug} scope="col" className="px-3 py-3 align-bottom font-semibold">
                    <Link href={agentPath(slug, 'projects/' + p.slug)} className="text-[var(--site-on-primary)] underline underline-offset-2">{p.name}</Link>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.k} className="border-t border-slate-100">
                  <th scope="row" className="sticky left-0 bg-slate-50 px-3 py-2 font-semibold text-slate-700">{r.k}</th>
                  {projects.map((p) => <td key={p.slug} className="px-3 py-2">{r.v(p)}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-slate-600">Per sq ft is the quoted price divided by carpet area. Confirm prices, floor and extra charges before booking.</p>
      </div>
    </SiteShell>
  )
}
