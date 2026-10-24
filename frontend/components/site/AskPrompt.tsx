import React from 'react'

/**
 * The ask placed where a buyer has just read the facts (possession, homes booked), so they need not scroll past every section to
 * the form at the end. It jumps to the page's enquiry form (`#enquire`); WhatsApp shows only when the page has a number for it.
 * `compact` is the desktop version at the top of the sticky side column.
 */
export default function AskPrompt({ name, note, whatsappUrl, compact = false }: {
  name: string; note: string; whatsappUrl?: string | null; compact?: boolean
}) {
  return (
    <section aria-label={`Ask about ${name}`} data-print="hide" data-testid={compact ? 'ask-prompt-side' : 'ask-prompt'}
      className={'rounded-2xl border border-amber-200 bg-amber-50 ' + (compact ? 'p-4' : 'p-4 sm:p-5')}>
      <p className={'font-bold text-slate-900 ' + (compact ? 'text-base' : 'text-lg')}>Planning to buy here?</p>
      <p className="mt-1 text-sm text-slate-700">Ask about prices, floor plans, offers or a site visit. {note}</p>
      <div className={'mt-3 flex gap-2 ' + (compact ? 'flex-col' : 'flex-wrap')}>
        <a href="#enquire" className="inline-flex min-h-[48px] items-center justify-center rounded-full bg-[#0f2340] px-6 font-bold text-white no-underline">
          Ask about this project
        </a>
        {whatsappUrl && (
          <a href={whatsappUrl} target="_blank" rel="noopener noreferrer"
            className="inline-flex min-h-[48px] items-center justify-center rounded-full bg-[#25D366] px-6 font-bold text-[#053b1a] no-underline">
            WhatsApp<span className="sr-only"> (opens in a new tab)</span>
          </a>
        )}
      </div>
    </section>
  )
}
