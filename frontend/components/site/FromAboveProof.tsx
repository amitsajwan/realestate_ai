'use client'

import React, { useState } from 'react'

/** The Sentinel-2 timeline folded into a badge under Google's sharp view (owner 2026-11-21: at 10 m a pixel it is proof that
 *  work went on, not the picture a buyer looks at). Its words are always in the page, so search reads them; the video and the
 *  yearly pictures are made only once the reader opens it, so a closed badge costs no download. */
export default function FromAboveProof({ summary, media, children }: {
  summary: React.ReactNode; media: React.ReactNode; children?: React.ReactNode
}) {
  const [opened, setOpened] = useState(false)
  return (
    <details className="mt-4 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2" data-testid="from-above-proof"
      onToggle={(e) => { if ((e.currentTarget as HTMLDetailsElement).open) setOpened(true) }}>
      <summary className="flex min-h-[44px] cursor-pointer items-center gap-2 text-sm font-semibold text-slate-900">{summary}</summary>
      {opened && <div data-testid="from-above-media">{media}</div>}
      {children}
    </details>
  )
}
