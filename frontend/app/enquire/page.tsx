import React from 'react'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import EnquiryForm from '@/components/site/EnquiryForm'
import { BRAND_NAME } from '@/lib/brand'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'

/** The buyer's enquiry page: one job, the form, on the first screen of a phone. It is the page ad tools are given as "where
 *  customers fill out your form" (they refuse the bare domain), and where every "Tell us what you need" link lands, so the
 *  form is not at the bottom of a long agent page any more. `?src=` on the address is read by lib/site/tracking.ts as the
 *  lead's source, as on every other page. */
const HOUSE_AGENT = process.env.NEXT_PUBLIC_DEFAULT_AGENT_SLUG || 'avasetu'

export async function generateMetadata(): Promise<Metadata> {
  return pageMetadata(getMarketingConfig(), {
    title: 'Tell us the home you are looking for in Pune',
    description: 'Looking for a flat in Pune? Tell the Avasetu team your budget and area, and we call or WhatsApp you with projects checked against MahaRERA.',
    path: '/enquire',
  })
}

const POINTS: [string, string][] = [
  ['Checked on MahaRERA', 'every project we suggest has its registration, possession date and homes booked read from MahaRERA'],
  ['One call or WhatsApp', 'the Avasetu team gets back to you, at the time you prefer'],
  ['Your number stays with us', 'we do not pass it to anyone without your OK'],
]

export default function EnquirePage() {
  const cfg = getMarketingConfig()
  return (
    // no hot banner and no header search: both would push the form below the first screen on a phone
    <MarketingShell hot={false} search={false}>
      <div className="bg-[#0f2340] px-4 pb-10 pt-6 text-white sm:pb-14 sm:pt-10">
        <div className="mx-auto max-w-xl">
          <h1 className="text-2xl font-bold leading-tight tracking-tight sm:text-4xl">Tell us the home you are looking for</h1>
          <p className="mt-2 text-slate-200">New projects and homes across Pune. We call or WhatsApp you back.</p>
        </div>
      </div>
      <div className="mx-auto -mt-7 max-w-xl px-4 pb-12">
        <EnquiryForm agentSlug={HOUSE_AGENT} agentName={BRAND_NAME} agentPhone={cfg.whatsappDigits} topic="a home in Pune (from the enquiry page)"
          waMessage="Hi, I am looking for a home in Pune." title="Your details"
          note="Name and number are enough. Budget and timeline help us call with the right projects." submitLabel="Send" />
        {cfg.whatsappUrl && (
          <p className="mt-4 text-center text-slate-700">
            Prefer WhatsApp?{' '}
            <a href={cfg.whatsappUrl} target="_blank" rel="noopener noreferrer" className="font-semibold text-[#0f2340] underline underline-offset-2">
              Message {cfg.whatsappDisplay}<span className="sr-only"> (opens WhatsApp)</span>
            </a>
          </p>
        )}
        <ul className="mt-8 list-none space-y-3 p-0">
          {POINTS.map(([t, d]) => (
            <li key={t} className="flex gap-3">
              <span aria-hidden className="mt-1 inline-flex h-6 w-6 flex-none items-center justify-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-800">✓</span>
              <span className="text-slate-700"><span className="font-semibold text-slate-900">{t}</span>: {d}</span>
            </li>
          ))}
        </ul>
      </div>
    </MarketingShell>
  )
}
