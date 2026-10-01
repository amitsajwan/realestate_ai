import React from 'react'
import { LANDING } from '@/lib/marketing/strings'

/**
 * HTML/CSS phone mock of the product's core moment: a comment on a post ("INTERESTED") becomes a lead card.
 * Pure markup, no images, labelled as sample data. Decorative for assistive tech except the caption text.
 */
export default function LeadCardMock({ className = '' }: { className?: string }) {
  const M = LANDING.mock
  return (
    <figure className={'mx-auto w-full max-w-[19rem] ' + className}>
      <div className="rounded-[2.2rem] border-[7px] border-[#050d1a] bg-[#050d1a] shadow-2xl shadow-black/40">
        <div className="space-y-3 rounded-[1.7rem] bg-[#fbf6ea] p-3">
          {/* the comment */}
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-600">{M.postLabel}</p>
            <div className="mt-1 flex items-center gap-2 rounded-2xl bg-white p-2.5 shadow-sm">
              <span aria-hidden="true" className="flex h-8 w-8 flex-none items-center justify-center rounded-full bg-[#183a5d] text-xs font-bold text-white">S</span>
              <p className="text-sm text-slate-800"><span className="font-semibold">{M.commenter}</span>{' '}<span className="rounded bg-[#f0b440] px-1.5 py-0.5 text-xs font-extrabold tracking-wide text-[#0f2340]">{M.comment}</span></p>
            </div>
          </div>
          <p aria-hidden="true" className="text-center text-xl leading-none text-[#14877b]">&#8595;</p>
          {/* the lead card */}
          <div className="rounded-2xl border border-[#ead9ae] bg-white p-3 shadow-md">
            <div className="flex items-center justify-between gap-2">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-600">{M.cardLabel}</p>
              <span className="rounded-full bg-[#c2410c] px-2.5 py-0.5 text-xs font-extrabold tracking-wide text-white">{M.hot}</span>
            </div>
            <p className="mt-1 text-base font-bold text-[#0f2340]">{M.cardName}</p>
            <p className="mt-1 text-[13px] leading-snug text-slate-700">{M.summary}</p>
            <ul className="mt-2 flex flex-wrap gap-1.5 p-0">
              {M.chips.map((c) => <li key={c} className="list-none rounded-full bg-[#e6f4f1] px-2.5 py-0.5 text-xs font-semibold text-[#0b5f56]">{c}</li>)}
            </ul>
            <p className="mt-2 text-xs font-medium text-slate-700">{M.next}</p>
            <div aria-hidden="true" className="mt-3 grid grid-cols-2 gap-2 text-center text-sm font-bold">
              <span className="rounded-lg bg-[#0f2340] py-2 text-white">{M.call}</span>
              <span className="rounded-lg bg-[#14877b] py-2 text-white">{M.whatsapp}</span>
            </div>
          </div>
        </div>
      </div>
      <figcaption className="mt-3 text-center text-sm text-slate-300">{M.sample}</figcaption>
    </figure>
  )
}
