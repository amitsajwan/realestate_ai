'use client'
import React, { useEffect, useState } from 'react'
import { AI_UNAVAILABLE, qualityApi, reviewSummary } from '@/lib/app/quality'
import type { QualityApi, QualityReview, ReviewKind } from '@/lib/app/quality'

/**
 * 'Quality 82/100 · Good' or 'Quality 54 · Check: text cut at the bottom', shown next to an Approve button.
 * Loads the visual review on mount (cached on the server per image), notes collapsed. Informs only: it never blocks approval,
 * and a failed review simply hides the chip.
 */
export function ReviewChip({ kind, id, initial, client = qualityApi }: { kind: ReviewKind; id: string; initial?: QualityReview | null; client?: QualityApi }) {
  const [review, setReview] = useState<QualityReview | null>(initial ?? null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    if (initial) return
    let alive = true
    client.review(kind, id).then((r) => { if (alive) setReview(r) }).catch(() => { if (alive) setFailed(true) })
    return () => { alive = false }
  }, [kind, id, initial, client])

  if (failed) return null
  if (!review) return <p className="text-xs text-gray-400" data-testid="review-chip-loading">Checking quality...</p>
  if (review.score === null) return null
  const tone = review.verdict === 'good' ? 'border-green-200 bg-green-50 text-green-900' : review.verdict === 'redo' ? 'border-red-200 bg-red-50 text-red-900' : 'border-amber-200 bg-amber-50 text-amber-900'
  const notes = review.notes.filter((n) => n !== AI_UNAVAILABLE)
  const offline = !review.ai_available
  return (
    <details className={`rounded-xl border px-3 py-1.5 text-xs ${tone}`} data-testid="review-chip">
      <summary className="cursor-pointer list-none font-semibold">
        {reviewSummary(review)}
        {(notes.length > 0 || offline) && <span className="ml-1 font-normal underline">details</span>}
      </summary>
      {(notes.length > 0 || offline) && (
        <ul className="mt-1 list-disc space-y-0.5 pl-4 font-normal" data-testid="review-notes">
          {notes.map((n) => <li key={n}>{n}</li>)}
          {offline && <li className="text-gray-600">{AI_UNAVAILABLE}: this score comes from automatic checks only.</li>}
        </ul>
      )}
    </details>
  )
}
