import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import PickButtons from '@/components/site/PickButtons'
import PicksRedirect from '@/components/site/PicksRedirect'
import ProjectSearch from '@/components/site/ProjectSearch'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { compareName, compareRows } from '@/lib/site/projectCompare'
import { COMPARE_MAX, parseSlugs } from '@/lib/site/picks'
import { getPageRegister } from '@/lib/site/register'
import type { RegisterProject } from '@/lib/site/register'

export const revalidate = 300

type Props = { searchParams?: Promise<Record<string, string | string[] | undefined>> }

/** Out of search, links followed: every pair of projects would be a near copy of the two project pages it links to. One
 *  canonical (/compare) for every ?projects= so no combination is counted as a page of its own. */
export async function generateMetadata(): Promise<Metadata> {
  return pageMetadata(getMarketingConfig(), {
    title: 'Compare Pune projects side by side',
    description: 'Up to three MahaRERA projects side by side: price, all-in cost, possession filed, homes booked and the builder\'s date record.',
    path: '/compare',
    noindex: true,
  })
}

/** A project that cannot be read now (unknown slug, the backend restarting) is left out of the table rather than failing it. */
async function read(slug: string): Promise<RegisterProject | null> {
  try {
    // an agent-listed page's slug (lodha-camelot) reads its register record and keeps that slug: the picks list holds it
    const p = await getPageRegister(slug)
    return p && { ...p, slug }
  } catch {
    return null
  }
}

export default async function ComparePage({ searchParams }: Props) {
  const sp = (await searchParams) ?? {}
  const slugs = parseSlugs(sp.projects, COMPARE_MAX)
  const projects = (await Promise.all(slugs.map(read))).filter((p): p is RegisterProject => !!p)
  const rows = compareRows(projects)
  return (
    <MarketingShell>
      <div className="mx-auto max-w-5xl space-y-6 px-4 py-8" style={AVASETU_SITE_VARS}>
        <header>
          <h1 className="text-3xl font-extrabold text-[#0f2340]">Compare projects</h1>
          <p className="mt-1 text-slate-700">
            Up to {COMPARE_MAX} projects side by side. Dates and bookings from MahaRERA&apos;s public record; prices as the builder or two
            property sites publish them. A dash means we do not have that fact yet.
          </p>
        </header>
        {projects.length < 2 && (
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid="compare-empty">
            {!slugs.length && <PicksRedirect list="compare" />}
            <p className="text-slate-800">
              {projects.length === 1 ? 'Add one more project to compare.' : 'Pick projects to compare.'} Press <b>+ Compare</b> on any project
              page, or find one here:
            </p>
            <div className="mt-3"><ProjectSearch /></div>
          </div>
        )}
        {projects.length > 0 && (
          <div className="overflow-x-auto rounded-2xl border border-slate-200">
            <table className="w-full min-w-[640px] text-left text-sm" data-testid="compare-table">
              <thead>
                <tr className="bg-[#0f2340] text-white">
                  <th scope="col" className="sticky left-0 bg-[#0f2340] px-3 py-3 font-semibold"><span className="sr-only">Fact</span></th>
                  {projects.map((p) => (
                    <th key={p.slug} scope="col" className="px-3 py-3 align-bottom font-semibold">
                      <Link href={`/projects/${p.slug}`} className="text-white underline underline-offset-2">{compareName(p)}</Link>
                      {p.area && <span className="block text-xs font-normal text-slate-200">{p.area.name}</span>}
                      <span className="block font-mono text-xs font-normal text-slate-300">MahaRERA {p.regno}</span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.key} className="border-t border-slate-100 align-top" data-testid={`compare-row-${r.key}`}>
                    <th scope="row" className="sticky left-0 bg-slate-50 px-3 py-2 font-semibold text-slate-700">{r.label}</th>
                    {r.cells.map((c, i) => (
                      <td key={projects[i].slug} className="px-3 py-2">
                        {!c ? <span className="text-slate-400">—</span> : (
                          <>
                            {c.href ? <Link href={c.href} className="font-semibold text-[#0f2340] underline underline-offset-2">{c.text}</Link>
                              : <span className="font-semibold text-slate-900">{c.text}</span>}
                            {c.sub && <span className="block text-xs text-slate-600">{c.sub}</span>}
                          </>
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
                <tr className="border-t border-slate-100">
                  <th scope="row" className="sticky left-0 bg-slate-50 px-3 py-2"><span className="sr-only">Pick</span></th>
                  {projects.map((p) => <td key={p.slug} className="px-3 py-2"><PickButtons slug={p.slug} name={compareName(p)} /></td>)}
                </tr>
              </tbody>
            </table>
          </div>
        )}
        <p className="text-xs text-slate-600">
          The all-in cost adds GST, stamp duty (7%) and registration to the lowest published price; parking, club house and other
          charges come from the builder&apos;s cost sheet. A per sq ft figure is the site&apos;s own: some quote carpet, some saleable area.
        </p>
      </div>
    </MarketingShell>
  )
}
