'use client'
import React from 'react'

/** Circular setup progress: done of total, with the count in the middle. Amber while in progress, green when complete. */
export function ProgressRing({ done, total, size = 52 }: { done: number; total: number; size?: number }) {
  const r = (size - 8) / 2
  const c = 2 * Math.PI * r
  const frac = total ? Math.min(1, done / total) : 0
  const complete = total > 0 && done >= total
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }} role="img" aria-label={`${done} of ${total} steps done`} data-testid="progress-ring">
      <svg width={size} height={size} className="-rotate-90" aria-hidden>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" strokeWidth={5} className="stroke-gray-200" />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none" strokeWidth={5} strokeLinecap="round"
          className={complete ? 'stroke-green-600' : 'stroke-amber-500'}
          strokeDasharray={c} strokeDashoffset={c * (1 - frac)}
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-gray-900">{done}/{total}</span>
    </div>
  )
}
