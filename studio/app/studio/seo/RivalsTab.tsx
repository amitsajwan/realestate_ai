'use client'
import React from 'react'
import { ErrorBox, Spinner } from '@/components/app/ui'
import { getRankings } from '@/lib/app/insights'
import { useAsync } from '@/lib/app/useAsync'
import { Board } from './RankingsTab'

// SEO → Rivals (2026-11-19): who sits above us on Google, and MagicBricks head to head. It was the top of Rankings and pushed
// the week's own numbers and the fixes two screens down; it is read weekly, so it has its own tab.
export default function RivalsTab() {
  const q = useAsync(() => getRankings(), [])
  if (q.loading && !q.data) return <Spinner />
  if (q.error) return <ErrorBox message={q.error} onRetry={q.reload} />
  const b = q.data!.scoreboard
  if (!b?.at) return <p className="rounded-2xl bg-white p-4 text-sm text-gray-600">No weekly count yet: the scoreboard is counted once a week from the Google searches we run.</p>
  return <Board b={b} />
}
