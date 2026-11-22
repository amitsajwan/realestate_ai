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
import { briefLine, compareName } from '@/lib/site/projectCompare'
import { COMPARE_MAX, SAVED_MAX, comparePath, parseSlugs, shortlistMessage, shortlistPath, whatsappShare } from '@/lib/site/picks'
import { getRegisterProject } from '@/lib/site/register'
import type { RegisterProject } from '@/lib/site/register'

export const revalidate = 300

type Props = { searchParams?: Promise<Record<string, string | string[] | undefined>> }

/** A buyer's list to send the family: out of search (it is the project pages, shortened), one canonical for every ?ids=. */
export async function generateMetadata(): Promise<Metadata> {
  return pageMetadata(getMarketingConfig(), {
    title: 'A shortlist of Pune projects',
    description: 'Projects saved on Avasetu, each with its price, possession filed with MahaRERA and homes booked.',
    path: '/shortlist',
    noindex: true,
  })
}

async function read(slug: string): Promise<RegisterProject | null> {
  try {
    return await getRegisterProject(slug)
  } catch {
    return null
  }
}

export default async function ShortlistPage({ searchParams }: Props) {
  const cfg = getMarketingConfig()
  const sp = (await searchParams) ?? {}
  const slugs = parseSlugs(sp.ids, SAVED_MAX)
  const projects = (await Promise.all(slugs.map(read))).filter((p): p is RegisterProject => !!p)
  const shown = projects.map((p) => p.slug)
  const link = cfg.siteUrl + shortlistPath(shown)
  const share = whatsappShare(shortlistMessage(projects.map(compareName), link))
  return (
    <MarketingShell>
      <div className="mx-auto max-w-3xl space-y-6 px-4 py-8" style={AVASETU_SITE_VARS}>
        <header>
          <h1 className="text-3xl font-extrabold text-[#0f2340]">{projects.length ? `Shortlist: ${projects.length} project${projects.length === 1 ? '' : 's'}` : 'Your shortlist'}</h1>
          <p className="mt-1 text-slate-700">
            No sign-in: the list is kept on this phone and in this page&apos;s link, so anyone you send it to sees the same projects.
          </p>
        </header>
        {!projects.length ? (
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid="shortlist-empty">
            <PicksRedirect list="saved" />
            <p className="text-slate-800">Press <b>♡ Save</b> on a project page to add it here, or find one:</p>
            <div className="mt-3"><ProjectSearch /></div>
          </div>
        ) : (
          <>
            <div className="flex flex-wrap gap-2">
              <a href={share} target="_blank" rel="noopener noreferrer" data-testid="shortlist-whatsapp"
                className="inline-flex min-h-[48px] items-center gap-2 rounded-xl bg-[#25D366] px-5 font-bold text-white no-underline">
                Send on WhatsApp
              </a>
              {projects.length >= 2 && (
                <Link href={comparePath(shown.slice(0, COMPARE_MAX))} className="inline-flex min-h-[48px] items-center rounded-xl border border-[#0f2340] px-5 font-semibold text-[#0f2340] no-underline"
                  data-testid="shortlist-compare">
                  Compare {Math.min(projects.length, COMPARE_MAX)} side by side
                </Link>
              )}
            </div>
            <ol className="space-y-3 p-0" data-testid="shortlist">
              {projects.map((p) => (
                <li key={p.slug} className="list-none rounded-2xl border border-slate-200 bg-white p-4">
                  <Link href={`/projects/${p.slug}`} className="text-lg font-bold text-[#0f2340] underline-offset-2 hover:underline">{compareName(p)}</Link>
                  {p.area && <span className="text-slate-600">, {p.area.name}</span>}
                  {briefLine(p) && <p className="mt-1 text-sm text-slate-800">{briefLine(p)}</p>}
                  <p className="mt-1 font-mono text-xs text-slate-500">MahaRERA {p.regno}</p>
                  <div className="mt-2"><PickButtons slug={p.slug} name={compareName(p)} /></div>
                </li>
              ))}
            </ol>
          </>
        )}
      </div>
    </MarketingShell>
  )
}
