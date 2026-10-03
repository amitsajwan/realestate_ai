import React from 'react'
/** The item's fixed 'Worth checking: ...' line (the same one its Facebook and Instagram captions carry), as a small gold-edged callout under
 *  the summary. Renders nothing when the item has no line (education and digest items). */
export default function BuyerLine({ line, compact = false }: { line: string | null; compact?: boolean }) {
  if (!line) return null
  return (
    <p data-testid="buyer-line"
      className={(compact ? 'mt-2 px-2.5 py-1.5 text-xs' : 'mt-4 px-3 py-2 text-sm') + ' flex items-start gap-2 rounded-lg border-l-4 border-[#f0b440] bg-[#fbf6ea] font-medium leading-snug text-[#0f2340]'}>
      <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" className="mt-px flex-none text-[#a87a12]">
        <path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
      </svg>
      <span>{line}</span>
    </p>
  )
}
