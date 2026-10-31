import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import { formatArea } from '@/lib/site/format'
import {
  checklist, complete, describePlan, familyNearby, finderLink, isEast, nearbyWanted, parsePlan, planHomes, toPlanSearch, type PlanAnswers, type PlanPick,
} from '@/lib/site/homeplan'
import { eastItems, nearbyOf } from '@/lib/site/homeplanData'
import { longDay } from '@/lib/site/register'
import PlanLeadForm from '@/components/site/homeplan/PlanLeadForm'

// one family's answers: never in search (pageMetadata noindex), and read fresh, so the plan shows today's facts
export const dynamic = 'force-dynamic'

export const metadata: Metadata = pageMetadata(getMarketingConfig(), {
  title: 'Your East Pune home plan',
  description: 'The East Pune projects that fit your answers, with the facts behind each pick.',
  path: '/home-plan/result',
  noindex: true,
})

type Props = { searchParams?: Promise<Record<string, string | string[] | undefined>> }

function Pick({ p, n, near }: { p: PlanPick; n: number; near: string[] }) {
  const i = p.item
  const reasons = [...p.reasons, ...near]
  return (
    <li className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm" data-testid="plan-pick">
      <p className="text-sm font-bold uppercase tracking-wide text-[var(--site-accent-text)]">{n}. {i.area ?? 'East Pune'}</p>
      <h2 className="mt-1 text-xl font-bold text-slate-900">
        <Link href={i.href} className="text-[#0f2340] underline underline-offset-2">{i.name}</Link>
      </h2>
      {i.builder && <p className="text-sm text-slate-600">by {i.builder}</p>}
      {i.listedBy && <p className="mt-1 text-sm text-slate-700">Listed by {i.listedBy}, a partner agent (not ranked higher for it)</p>}
      {p.home?.sqft ? <p className="mt-1 text-sm text-slate-700">{formatArea(p.home.sqft)} home on the price sheet</p> : null}
      {reasons.length > 0 && (
        <>
          <h3 className="mt-3 text-base font-semibold text-slate-900">Why it fits</h3>
          <ul className="mt-1 list-disc space-y-1 pl-5 text-slate-800">{reasons.map((r) => <li key={r}>{r}</li>)}</ul>
        </>
      )}
      {p.watch.length > 0 && (
        <>
          <h3 className="mt-3 text-base font-semibold text-slate-900">Worth checking</h3>
          <ul className="mt-1 list-disc space-y-1 pl-5 text-slate-800">{p.watch.map((r) => <li key={r}>{r}</li>)}</ul>
        </>
      )}
    </li>
  )
}

function NotEast({ a }: { a: PlanAnswers }) {
  return (
    <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-5" data-testid="plan-not-east">
      <h2 className="text-xl font-bold text-slate-900">We know East Pune best right now</h2>
      <p className="mt-2 text-slate-800">
        Our plans cover East Pune, where we have checked every project. For your side of the city, the project finder has every
        MahaRERA project with the same checks, and our team has your answers: we will tell you when plans cover your area.
      </p>
      <div className="mt-4 flex flex-wrap gap-3">
        <Link href={finderLink(a)} className="inline-flex min-h-[48px] items-center rounded-full bg-[#0f2340] px-6 font-bold text-white no-underline">
          See projects that fit
        </Link>
        <Link href={'/home-plan/result' + toPlanSearch({ ...a, work: 'home' })}
          className="inline-flex min-h-[48px] items-center rounded-full border-2 border-[#0f2340] px-6 font-bold text-[#0f2340] no-underline">
          Plan for East Pune anyway
        </Link>
      </div>
    </section>
  )
}

export default async function HomePlanResult({ searchParams }: Props) {
  const cfg = getMarketingConfig()
  const a = parsePlan((await searchParams) ?? {})
  const today = new Date().toISOString().slice(0, 10)
  const edit = '/home-plan' + toPlanSearch(a)
  const path = '/home-plan/result' + toPlanSearch(a)
  let picks: PlanPick[] = []
  let near = new Map<string, string[]>()
  if (complete(a) && isEast(a)) {
    const { items, regnos } = await eastItems()
    picks = planHomes(items, a, today)
    // schools and hospitals only for the families that asked about them, and only for the picks shown
    if (nearbyWanted(a).length) {
      const got = await nearbyOf(picks.map((p) => p.item.id), regnos)
      near = new Map(picks.map((p) => [p.item.id, familyNearby(a, got.get(p.item.id))]))
    }
  }
  return (
    <MarketingShell>
      <div className="mx-auto max-w-3xl px-4 py-10 sm:py-14" style={AVASETU_SITE_VARS}>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">Your East Pune home plan</h1>
        {complete(a) ? (
          <p className="mt-2 text-slate-700">
            For: {describePlan(a)}.{' '}
            <Link href={edit} className="inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">Edit answers</Link>
          </p>
        ) : (
          <p className="mt-3 text-lg text-slate-800">
            A few answers are missing. <Link href={edit} className="font-semibold text-[#0f2340] underline">Answer the six questions</Link> to see your plan.
          </p>
        )}

        {complete(a) && !isEast(a) && (
          <>
            <NotEast a={a} />
            <div className="mt-6"><PlanLeadForm answers={a} path={path} east={false} /></div>
          </>
        )}

        {complete(a) && isEast(a) && (picks.length ? (
          <>
            <ol className="mt-6 list-none space-y-4 p-0">{picks.map((p, n) => <Pick key={p.item.id} p={p} n={n + 1} near={near.get(p.item.id) ?? []} />)}</ol>
            <section className="mt-8 rounded-2xl bg-slate-50 p-5">
              <h2 className="text-xl font-bold text-slate-900">On the site visit</h2>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-800">{checklist(a).map((c) => <li key={c}>{c}</li>)}</ul>
            </section>
          </>
        ) : (
          <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-5" data-testid="plan-empty">
            <h2 className="text-xl font-bold text-slate-900">Nothing fits every answer yet</h2>
            <p className="mt-2 text-slate-800">
              No East Pune project we hold has a published price in your budget for this size, within reach of your office. Try the
              next budget, or any move-in date. Our team can also check projects with no published price: leave your number below.
            </p>
            <Link href={edit} className="mt-3 inline-flex min-h-[48px] items-center font-semibold text-[#0f2340] underline">Change answers</Link>
          </section>
        ))}

        {complete(a) && isEast(a) && (
          <div className="mt-8 space-y-4">
            <PlanLeadForm answers={a} path={path} />
            <div className="flex flex-wrap gap-3">
              {cfg.whatsappUrl && (
                <a href={cfg.whatsappUrl} target="_blank" rel="noopener noreferrer"
                  className="inline-flex min-h-[48px] items-center rounded-xl bg-[#25D366] px-6 font-bold text-[#053b1a] no-underline">
                  WhatsApp us now<span className="sr-only"> (opens in a new tab)</span>
                </a>
              )}
              <Link href={finderLink(a)} className="inline-flex min-h-[48px] items-center font-semibold text-[#0f2340] underline underline-offset-2">
                See every project that fits
              </Link>
            </div>
          </div>
        )}

        <p className="mt-8 text-xs text-slate-500">
          Read on {longDay(today)} from MahaRERA&apos;s public record (completion dates, homes booked) and asking prices published
          online. Distances are straight-line from our checked map position, not drive times. Picked on these facts only.
        </p>
      </div>
    </MarketingShell>
  )
}
