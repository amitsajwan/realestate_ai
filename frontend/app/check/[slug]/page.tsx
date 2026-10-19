import React from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound, redirect } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import CheckNext from '@/components/site/CheckNext'
import InstallApp from '@/components/site/InstallApp'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { CHECK_STYLE, checkPill, checkState, checkVerdict, extensionMonths, monthsLater } from '@/lib/site/check'
import type { CheckState } from '@/lib/site/check'
import { displayName, getRegisterProject, longDay, monthYear } from '@/lib/site/register'
import type { RegisterProject } from '@/lib/site/register'

/** The status card (docs/plan/project-check.md): what one project's possession date did, from MahaRERA, made to be read on a phone
 *  and shared. ?r=<regno> is the registration the buyer picked (one tower of a project MahaRERA holds tower by tower). A tool, not a
 *  second copy of the project page: kept out of search. */
type Props = { params: Promise<{ slug: string }>; searchParams?: Promise<{ r?: string | string[] }> }

const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+){0,15}$/

interface Picked {
  regno: string
  label: string | null
  now: string | null
  first: string | null
  moved: number | null
  ext: number
  booked: number | null
  total: number | null
  maharera_url: string | null
}

async function load({ params, searchParams }: Props): Promise<{ p: RegisterProject; t: Picked; slug: string } | null> {
  const { slug } = await params
  if (!SLUG.test(slug)) return null
  const p = await getRegisterProject(slug).catch(() => null)
  if (!p) return null
  const raw = (await searchParams)?.r
  const r = (Array.isArray(raw) ? raw[0] : raw ?? '').trim().toUpperCase()
  const tower = (p.towers ?? []).find((x) => x.regno === r && x.regno !== p.regno)
  const t: Picked = tower
    ? { regno: tower.regno, label: tower.name, now: tower.completion_now, first: tower.completion_at_registration,
        moved: monthsLater(tower.completion_now, tower.completion_at_registration, tower.registered_on),
        ext: extensionMonths(tower.completion_now, tower.registered_on), booked: tower.units_booked, total: tower.units_total,
        maharera_url: tower.maharera_url }
    : { regno: p.regno, label: (p.towers ?? []).length > 1 ? p.name : null, now: p.completion_now, first: p.completion_at_registration,
        moved: p.details?.completion_moved_months ?? monthsLater(p.completion_now, p.completion_at_registration, p.details?.registered_on),
        ext: extensionMonths(p.completion_now, p.details?.registered_on),
        booked: p.units_booked, total: p.units_total, maharera_url: p.maharera_url }
  return { p, t, slug }
}

export async function generateMetadata(props: Props): Promise<Metadata> {
  const got = await load(props)
  if (!got) return { title: 'Project not found', robots: { index: false } }
  const { p, t } = got
  const v = checkVerdict(checkState(t.now, t.moved), t.now, t.first, t.moved, t.ext)
  const meta = pageMetadata(getMarketingConfig(), {
    title: `${displayName(p)}: ${v.title}`,
    description: `${v.sub} MahaRERA ${t.regno}. Checked on MahaRERA's public records.`,
    path: `/check/${p.slug}`,
  })
  return { ...meta, alternates: { canonical: `${getMarketingConfig().siteUrl}/projects/${p.slug}` }, robots: { index: false, follow: true } }
}

const n = (v: number) => v.toLocaleString('en-IN')

function Fact({ label, value, sub }: { label: string; value: React.ReactNode; sub?: React.ReactNode }) {
  return (
    <div className="rounded-2xl bg-white p-4 ring-1 ring-inset ring-slate-200">
      <dt className="text-sm text-slate-600">{label}</dt>
      <dd className="mt-1 text-xl font-bold text-slate-900">{value}</dd>
      {sub && <dd className="mt-1 text-sm text-slate-600">{sub}</dd>}
    </div>
  )
}

function Dates({ first, now, state }: { first: string | null; now: string | null; state: CheckState }) {
  if (!now) return null
  return (
    <dl className="mt-4 grid grid-cols-2 gap-2 text-sm">
      <div className="rounded-xl bg-white/70 p-3">
        <dt className="text-slate-600">At registration</dt>
        <dd className="mt-0.5 text-base font-semibold">{first ? monthYear(first) : 'not shown'}</dd>
      </div>
      <div className="rounded-xl bg-white/70 p-3">
        <dt className="text-slate-600">{state === 'passed' ? 'Filed date (passed)' : 'Now'}</dt>
        <dd className="mt-0.5 text-base font-semibold">{monthYear(now)}</dd>
      </div>
    </dl>
  )
}

export default async function CheckCardPage(props: Props) {
  const got = await load(props)
  if (!got) notFound()
  const { p, t, slug } = got
  if (p.slug !== slug) redirect(`/check/${p.slug}?r=${encodeURIComponent(t.regno)}`)   // a tower's slug: its project's card
  const cfg = getMarketingConfig()
  const name = displayName(p)
  const state = checkState(t.now, t.moved)
  const v = checkVerdict(state, t.now, t.first, t.moved, t.ext)
  const url = `${cfg.siteUrl}/check/${p.slug}?r=${encodeURIComponent(t.regno)}`
  const where = p.area?.name ?? p.pune_place?.name ?? p.place ?? null
  const towers = p.towers ?? []
  const b = p.builder
  return (
    <MarketingShell>
      <div className="mx-auto max-w-xl space-y-5 px-4 py-6 sm:py-10">
        <Link href="/check" className="inline-flex min-h-[44px] items-center text-sm font-semibold text-[#0f2340] underline underline-offset-2">← Check another project</Link>

        <header>
          <h1 className="text-3xl font-bold leading-tight tracking-tight text-slate-900">{name}</h1>
          <p className="mt-1 text-slate-600">{[p.promoter && `by ${p.promoter}`, where].filter(Boolean).join(' · ')}</p>
          <p className="mt-1 font-mono text-sm text-slate-600">MahaRERA {t.regno}{t.label ? ` · ${t.label}` : ''}</p>
        </header>

        <section aria-label="Possession date" className={`rounded-3xl p-5 ring-1 ring-inset ${CHECK_STYLE[state].block}`} data-testid="verdict" data-state={state}>
          <p className="text-2xl font-bold leading-snug">{v.title}</p>
          <p className="mt-2 text-base">{v.sub}</p>
          <Dates first={t.first} now={t.now} state={state} />
        </section>

        <dl className="grid grid-cols-2 gap-2">
          {t.total ? (
            <Fact label="Homes booked" value={t.booked != null && t.booked <= t.total ? `${Math.round((100 * t.booked) / t.total)}%` : 'Not reported'}
              sub={t.booked != null && t.booked <= t.total ? `${n(t.booked)} of ${n(t.total)}` : `${n(t.total)} homes`} />
          ) : null}
          {p.details?.registered_on && <Fact label="Registered" value={monthYear(p.details.registered_on)} sub={longDay(p.details.registered_on)} />}
          {towers.length > 1 && <Fact label="Registrations" value={towers.length} sub="towers or phases, each with its own date" />}
        </dl>

        {towers.length > 1 && (
          <section aria-labelledby="towers-title">
            <h2 id="towers-title" className="text-lg font-semibold text-slate-900">Each tower or phase</h2>
            <ul className="mt-2 list-none divide-y divide-slate-100 rounded-2xl border border-slate-200 p-0">
              {towers.map((x) => {
                const m = monthsLater(x.completion_now, x.completion_at_registration, x.registered_on)
                const s = checkState(x.completion_now, m)
                const mine = x.regno === t.regno
                return (
                  <li key={x.regno} className={mine ? 'bg-amber-50' : ''}>
                    <Link href={`/check/${p.slug}?r=${encodeURIComponent(x.regno)}`} className="flex min-h-[56px] flex-col justify-center gap-1 px-3 py-2 no-underline">
                      <span className="flex flex-wrap items-center gap-2">
                        <span className="font-semibold text-slate-900">{x.name}</span>
                        <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ring-inset ${CHECK_STYLE[s].pill}`}>{checkPill(s, m)}</span>
                        {mine && <span className="text-xs font-semibold text-amber-800">shown above</span>}
                      </span>
                      <span className="text-sm text-slate-600">{[x.completion_now && `Possession ${monthYear(x.completion_now)}`, x.regno].filter(Boolean).join(' · ')}</span>
                    </Link>
                  </li>
                )
              })}
            </ul>
          </section>
        )}

        {b && b.with_dates > 1 && (
          <section aria-labelledby="builder-title" className="rounded-2xl bg-slate-50 p-4 ring-1 ring-inset ring-slate-200">
            <h2 id="builder-title" className="text-lg font-semibold text-slate-900">{b.name}&apos;s record</h2>
            <p className="mt-1 text-slate-800">
              {b.moved_later === 0
                ? `None of their ${b.with_dates} projects with dates in our register moved their possession date later.`
                : `${b.moved_later} of their ${b.with_dates} projects with dates moved possession later${b.avg_months_later ? `, by ${b.avg_months_later} months on average` : ''}.`}
            </p>
            {p.builder_slug && <Link href={`/builders/${p.builder_slug}`} className="mt-2 inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">See their projects</Link>}
          </section>
        )}

        <p className="text-sm text-slate-600">
          From MahaRERA&apos;s public records{p.details_read_at ? `, read ${longDay(p.details_read_at)}` : ''}.{' '}
          {t.maharera_url && <a href={t.maharera_url} target="_blank" rel="noopener noreferrer" className="font-semibold text-[#0f2340] underline underline-offset-2">Open on MahaRERA<span className="sr-only"> (opens in a new tab)</span></a>}
        </p>

        <CheckNext slug={p.slug} regno={t.regno} name={name} verdict={v.title} url={url} />

        <div className="flex flex-wrap gap-x-5 gap-y-1">
          <Link href={`/projects/${p.slug}`} className="inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">Full project page</Link>
          <Link href="/check" className="inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-2">Check another project</Link>
        </div>
        <InstallApp />
      </div>
    </MarketingShell>
  )
}
