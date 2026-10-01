import React from 'react'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { getMarketingConfig } from '@/lib/marketing/config'
import { absoluteImage, getInterest } from '@/lib/interest/api'
import InterestActions, { type Step } from './InterestActions'

interface Props {
  params: Promise<{ code: string }>
  searchParams: Promise<{ done?: string; e?: string }>
}

const headline = (s: { title: string; kind: string }) => s.title || (s.kind === 'listing' ? 'A home in Pune' : 'From PUNE Property')

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { code } = await params
  const s = await getInterest(code)
  const cfg = getMarketingConfig()
  if (!s) return { title: 'Link not found', robots: { index: false } }
  const title = `${headline(s)} | ${cfg.businessName}`
  const description = s.sample
    ? 'A sample home, shown for illustration. Tap to say you are interested.'
    : `Tap to tell ${s.agent_name} you are interested${s.locality ? ' in this home in ' + s.locality : ''}.`
  const image = absoluteImage(cfg.siteUrl, s.image_url) || cfg.siteUrl + '/brand/og.jpg'
  return {
    title, description, robots: { index: false, follow: false },
    openGraph: { title, description, url: `${cfg.siteUrl}/i/${s.code}`, siteName: cfg.businessName, type: 'website', locale: 'en_IN', images: [{ url: image, width: 1200, height: 630 }] },
    twitter: { card: 'summary_large_image', title, description, images: [image] },
  }
}

export default async function InterestPage({ params, searchParams }: Props) {
  const { code } = await params
  const q = await searchParams
  const s = await getInterest(code)
  if (!s) notFound()
  const cfg = getMarketingConfig()
  const step: Step = q.done === '2' ? 'saved' : q.done === '1' ? 'tapped' : 'start'
  const img = s.image_url || null

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col">
      <header className="flex items-center gap-2 bg-[#0f2340] px-4 py-3 text-white">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/brand/logo.png" alt="" width={32} height={32} className="h-8 w-8 rounded-full" />
        <span className="text-base font-bold">{cfg.businessName}</span>
      </header>
      <div className="flex-1 px-4 pb-10 pt-5">
        <article className="overflow-hidden rounded-2xl border border-[#ead9ae] bg-white shadow-sm">
          {img && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={img} alt={s.sample ? 'Photo of a sample home, for illustration' : headline(s)} className="aspect-[4/3] w-full object-cover" />
          )}
          <div className="p-4">
            {s.sample && (
              <p className="mb-2 inline-block rounded-full bg-[#0f2340] px-3 py-1 text-xs font-bold tracking-wide text-[#f0b440]">SAMPLE HOME</p>
            )}
            {s.kind !== 'listing' && !s.sample && (
              <p className="mb-2 text-xs font-bold uppercase tracking-wide text-[#a87a12]">{s.kind === 'post' ? 'From our post' : 'Guide'}</p>
            )}
            <h1 className="text-2xl font-bold leading-snug text-[#0f2340]">{headline(s)}</h1>
            {s.locality && <p className="mt-1 text-base font-medium text-slate-700">{s.locality}, Pune</p>}
            {s.subtitle && <p className="mt-2 text-[15px] leading-relaxed text-slate-600">{s.subtitle}</p>}
            {!s.sample && s.kind === 'listing' && <p className="mt-2 text-sm text-slate-600">Listed by {s.agent_name}</p>}
          </div>
        </article>

        <div className="mt-5">
          <InterestActions code={s.code} agentName={s.agent_name} sample={s.sample} consentWording={s.consent_wording}
            initialStep={step} initialError={q.e || ''} />
        </div>
        <p className="mt-8 text-center text-xs text-slate-500">
          We only store what you type here, and only if you tick the box. See our <a href="/privacy" className="underline">privacy page</a>.
        </p>
      </div>
    </div>
  )
}
