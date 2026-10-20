'use client'

import React, { useEffect, useState } from 'react'
import EnquiryForm from '@/components/site/EnquiryForm'
import { saveCheck } from '@/lib/site/check'
import { trackEvent } from '@/lib/site/tracking'

const HOUSE_AGENT = process.env.NEXT_PUBLIC_DEFAULT_AGENT_SLUG || 'avasetu'

type Stage = 'bought' | 'planning'

interface Props {
  slug: string
  regno: string
  name: string
  /** the verdict in one line, for the WhatsApp share text */
  verdict: string
  url: string
}

function ShareWhatsApp({ text, label }: { text: string; label: string }) {
  return (
    <a href={`https://wa.me/?text=${encodeURIComponent(text)}`} target="_blank" rel="noopener noreferrer"
      onClick={() => trackEvent('share', HOUSE_AGENT)}
      className="inline-flex min-h-[48px] items-center justify-center gap-2 rounded-full bg-[#25D366] px-5 font-semibold text-slate-900 no-underline">
      {label}<span className="sr-only"> (opens WhatsApp)</span>
    </a>
  )
}

/** After the card: "which are you?" Bought: what the buyer can do and sharing with co-buyers. Planning: what to check, then an agent.
 *  The project is remembered in this browser for "Checked before". */
export default function CheckNext({ slug, regno, name, verdict, url }: Props) {
  const [stage, setStage] = useState<Stage | null>(null)
  useEffect(() => { saveCheck({ slug, regno, name }) }, [slug, regno, name])
  const share = `${name}: ${verdict}. From MahaRERA, checked on Avasetu: ${url}`
  const btn = (s: Stage, label: string) => (
    <button type="button" aria-pressed={stage === s} onClick={() => setStage(s)}
      className={`min-h-[56px] flex-1 rounded-2xl px-4 text-base font-semibold ring-1 ring-inset ${stage === s ? 'bg-[#0f2340] text-white ring-[#0f2340]' : 'bg-white text-slate-900 ring-slate-300 hover:bg-slate-50'}`}>
      {label}
    </button>
  )
  return (
    <section aria-labelledby="next-title" className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
      <h2 id="next-title" className="text-lg font-semibold text-slate-900">Which are you?</h2>
      <div className="mt-3 flex gap-2">
        {btn('bought', 'I’ve bought here')}
        {btn('planning', 'Planning to buy')}
      </div>
      {stage === 'bought' && (
        <div className="mt-5 space-y-4" data-testid="next-bought">
          <ol className="list-decimal space-y-3 pl-5 text-slate-800">
            <li><span className="font-semibold">Find the possession date in your agreement.</span> That date, not the one on MahaRERA, is what the builder owes you.</li>
            <li><span className="font-semibold">If possession comes later than that date,</span> RERA (section 18) lets you claim interest for every month of delay, or withdraw and get a refund with interest.</li>
            <li><span className="font-semibold">Complaints go to MahaRERA,</span> online at{' '}
              <a href="https://maharera.maharashtra.gov.in/" target="_blank" rel="noopener noreferrer" className="font-semibold text-[#0f2340] underline underline-offset-2">maharera.maharashtra.gov.in</a>.
            </li>
          </ol>
          <p className="text-slate-700">Other buyers in {name} will want to see this.</p>
          <ShareWhatsApp text={share} label="Share with co-buyers" />
        </div>
      )}
      {stage === 'planning' && (
        <div className="mt-5 space-y-4" data-testid="next-planning">
          <ol className="list-decimal space-y-3 pl-5 text-slate-800">
            <li><span className="font-semibold">Look at the date and the builder&apos;s record above.</span> A builder whose projects often move later may do it again.</li>
            <li><span className="font-semibold">Homes booked</span> show how the project is selling; a new launch starts low.</li>
            <li><span className="font-semibold">Before you pay,</span> get the possession date written into the agreement and match the MahaRERA number on it.</li>
          </ol>
          <EnquiryForm agentSlug={HOUSE_AGENT} agentName="Avasetu" topic={`${name} (MahaRERA ${regno}), from the project check`}
            waMessage={`Hi, I checked ${name} (MahaRERA ${regno}) and I am planning to buy: ${url}`} id="check-enquire" />
        </div>
      )}
      {!stage && <div className="mt-4"><ShareWhatsApp text={share} label="Share this check on WhatsApp" /></div>}
    </section>
  )
}
