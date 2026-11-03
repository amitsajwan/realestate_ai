'use client'
import React from 'react'
import { CONTENT_TYPES, typeLabel } from '@/lib/app/content'
import type { ContentType } from '@/lib/app/content'

export type TypeFilter = ContentType | 'all'
export const TYPE_FILTERS: TypeFilter[] = ['all', ...CONTENT_TYPES]

/** All · Listings · News · Guides · Agents (· Other), with counts; empty types are left out (the chosen one always shows). */
export function TypeChips({ counts, value, onChange }: { counts: Record<ContentType, number>; value: TypeFilter; onChange: (t: TypeFilter) => void }) {
  const total = CONTENT_TYPES.reduce((n, t) => n + counts[t], 0)
  const shown = TYPE_FILTERS.filter((t) => t === 'all' || t === value || counts[t] > 0)
  if (shown.length <= 2 && value === 'all') return null   // one type only: nothing to filter
  return (
    <div role="group" aria-label="Type" className="-mx-4 gap-2 overflow-x-auto px-4 pb-1 [display:flex] [scrollbar-width:none]">
      {shown.map((t) => {
        const on = t === value
        const n = t === 'all' ? total : counts[t]
        return (
          <button key={t} type="button" aria-pressed={on} onClick={() => onChange(t)}
            className={`inline-flex min-h-[44px] flex-none items-center gap-1.5 whitespace-nowrap rounded-full border px-3.5 text-sm font-semibold ${
              on ? 'border-[#0f2340] bg-[#0f2340] text-white' : 'border-gray-200 bg-white text-gray-700 active:bg-gray-100'}`}>
            {typeLabel(t)}
            <span className={`text-xs tabular-nums ${on ? 'text-[#f0b440]' : 'text-gray-500'}`}>{n}</span>
          </button>
        )
      })}
    </div>
  )
}
