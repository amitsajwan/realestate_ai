import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import { getMarketingConfig } from '@/lib/marketing/config'
import { INSIGHT_NOTE, INSIGHTS, getInsight } from '@/lib/marketing/insights'
import { pageMetadata } from '@/lib/marketing/seo'

type Props = { params: Promise<{ slug: string }> }

export function generateStaticParams() {
  return INSIGHTS.map((a) => ({ slug: a.slug }))
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params
  const a = getInsight(slug)
  if (!a) return {}
  return pageMetadata(getMarketingConfig(), { title: a.title, description: a.summary, path: `/insights/${a.slug}` })
}

export default async function InsightPage({ params }: Props) {
  const { slug } = await params
  const a = getInsight(slug)
  if (!a) notFound()
  const others = INSIGHTS.filter((x) => x.slug !== a.slug)
  return (
    <MarketingShell>
      <article className="mx-auto max-w-3xl px-4 py-10 sm:py-14">
        <p className="text-sm"><Link href="/insights" className="text-blue-800 underline underline-offset-2">All insights</Link></p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">{a.title}</h1>
        <p className="mt-2 text-sm text-slate-600">Last updated: <time dateTime={a.updated}>{a.updatedLabel}</time></p>
        <p className="mt-5 text-lg leading-relaxed text-slate-800">{a.summary}</p>
        <div className="mt-8 space-y-9">
          {a.sections.map((s) => (
            <section key={s.heading}>
              <h2 className="text-xl font-semibold text-slate-900">{s.heading}</h2>
              {s.paragraphs?.map((p, i) => <p key={i} className="mt-3 leading-relaxed text-slate-800">{p}</p>)}
              {s.bullets && <ul className="mt-3 list-disc space-y-2 pl-6 leading-relaxed text-slate-800">{s.bullets.map((b, i) => <li key={i}>{b}</li>)}</ul>}
            </section>
          ))}
        </div>
        {a.sources.length > 0 && (
          <section className="mt-10 border-t border-slate-200 pt-6">
            <h2 className="text-lg font-semibold text-slate-900">Sources</h2>
            <ul className="mt-2 list-disc space-y-1 pl-6 text-sm">
              {a.sources.map((s) => <li key={s.href}><a href={s.href} rel="noopener noreferrer" target="_blank" className="text-blue-800 underline underline-offset-2">{s.label}</a></li>)}
            </ul>
          </section>
        )}
        <p className="mt-8 rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-700">{INSIGHT_NOTE}</p>
        {others.length > 0 && (
          <nav aria-label="More guides" className="mt-8 text-sm">
            <p className="font-semibold text-slate-900">More guides</p>
            <ul className="mt-2 space-y-1">
              {others.map((o) => <li key={o.slug}><Link href={`/insights/${o.slug}`} className="text-blue-800 underline underline-offset-2">{o.title}</Link></li>)}
            </ul>
          </nav>
        )}
      </article>
    </MarketingShell>
  )
}
