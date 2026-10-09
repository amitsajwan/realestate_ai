import React from 'react'
import { LANDING } from '@/lib/marketing/strings'

/**
 * HTML/CSS mock of the product's core moment: a comment on a post ("INTERESTED") becomes a lead card with labelled fields
 * and a next step. Pure markup, no images, labelled as sample data. The buttons are pictures of buttons, hidden from assistive tech.
 */
export default function LeadCardMock({ className = '' }: { className?: string }) {
  const M = LANDING.mock
  return (
    <figure className={'mx-auto w-full max-w-[22rem] ' + className}>
      <div className="overflow-hidden rounded-2xl bg-white text-slate-900 shadow-2xl shadow-black/30 ring-1 ring-black/5">
        {/* where it came from */}
        <div className="flex items-center gap-3 border-b border-[#ead9ae] bg-[#fbf6ea] px-4 py-3">
          <span aria-hidden="true" className="flex h-8 w-8 flex-none items-center justify-center rounded-full bg-[#0f2340] text-xs font-bold text-white">S</span>
          <p className="min-w-0 text-[13px] leading-snug text-slate-600">
            <span className="font-semibold text-slate-800">{M.source}</span>: &ldquo;<span className="font-bold text-[#0f2340]">{M.comment}</span>&rdquo;
          </p>
          <span className="ml-auto flex-none text-xs text-slate-500">{M.when}</span>
        </div>
        {/* the lead card */}
        <div className="p-4">
          <div className="flex items-center justify-between gap-2">
            <p className="text-lg font-bold text-[#0f2340]">{M.name}</p>
            <span className="rounded-full bg-[#c2410c] px-2.5 py-1 text-xs font-extrabold uppercase tracking-wide text-white">{M.hot}</span>
          </div>
          <p className="mt-1 text-[15px] leading-snug text-slate-700">{M.summary}</p>
          <dl className="mt-3 grid grid-cols-2 gap-px overflow-hidden rounded-lg bg-slate-200 ring-1 ring-slate-200">
            {M.fields.map((f) => (
              <div key={f.label} className="bg-white px-3 py-2.5">
                <dt className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">{f.label}</dt>
                <dd className="m-0 text-[15px] font-bold text-[#0f2340]">{f.value}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-3 rounded-lg bg-[#fbf6ea] px-3 py-2 text-sm text-[#0f2340]">
            <strong className="text-[#8a5d00]">{M.nextLabel}</strong> {M.next}
          </p>
          <div aria-hidden="true" className="mt-4 grid grid-cols-2 gap-2 text-center text-sm font-bold">
            <span className="flex h-11 items-center justify-center rounded-lg bg-[#0f766e] text-white">{M.whatsapp}</span>
            <span className="flex h-11 items-center justify-center rounded-lg border-2 border-[#0f2340] text-[#0f2340]">{M.call}</span>
          </div>
        </div>
        <figcaption className="border-t border-slate-200 px-4 py-2 text-xs text-slate-500">{M.sample}</figcaption>
      </div>
    </figure>
  )
}
