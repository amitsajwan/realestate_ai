'use client'
import React from 'react'
import type { NewsroomFact } from '@/lib/app/newsroom'

/** Collapsed by default: each fact with the source sentence that backs it. */
export function FactsList({ facts }: { facts: NewsroomFact[] }) {
  if (facts.length === 0) return null
  return (
    <details className="rounded-lg border border-gray-200 bg-gray-50 p-2">
      <summary className="flex min-h-[44px] cursor-pointer items-center text-sm font-semibold text-blue-900">
        Facts and source quotes ({facts.length})
      </summary>
      <ul className="space-y-2 pb-1">
        {facts.map((f, i) => (
          <li key={i} className="text-sm">
            <p className="font-medium text-gray-900">{f.text}</p>
            {f.quote && <blockquote className="mt-0.5 border-l-4 border-amber-400 pl-2 text-gray-600">&ldquo;{f.quote}&rdquo;</blockquote>}
          </li>
        ))}
      </ul>
    </details>
  )
}
