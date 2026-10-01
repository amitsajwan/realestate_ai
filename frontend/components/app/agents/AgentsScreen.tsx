'use client'
import Link from 'next/link'
import React, { useState } from 'react'
import { conciergeApi } from '@/lib/app/concierge'
import { timeAgo } from '@/lib/app/format'
import { useAsync } from '@/lib/app/useAsync'
import { Btn, ErrorBox, PageTitle, Spinner } from '../ui'
import { AddAgentSheet } from './AddAgentSheet'
import { ProgressRing } from './ProgressRing'

/** Studio > Agents (owner only): every agent you set up, with how far along each one is. */
export function AgentsScreen() {
  const { data, error, loading, reload } = useAsync(() => conciergeApi.list(), [])
  const [adding, setAdding] = useState(false)

  if (loading && !data) return <Spinner />
  if (error && !data) return <ErrorBox message={error} onRetry={reload} />

  return (
    <div className="space-y-4">
      <PageTitle>Agents</PageTitle>
      <p className="text-sm text-gray-600">Agents you set up. Their listings go on the PUNE Property pages with their name, and buyers reach them.</p>
      {error && <ErrorBox message={error} onRetry={reload} />}
      {data && data.length === 0 ? (
        <p className="rounded-2xl bg-white p-6 text-center text-gray-600">No agents yet. Add the first one.</p>
      ) : (
        <ul className="space-y-3">
          {(data ?? []).map((a) => {
            const next = a.checklist.find((c) => !c.done)
            return (
              <li key={a.id}>
                <Link href={`/studio/agents/${encodeURIComponent(a.id)}`} data-testid="agent-row"
                  className="flex min-h-[72px] items-center gap-3 rounded-2xl border border-gray-200 bg-white p-3 active:bg-gray-50">
                  <ProgressRing done={a.progress.done} total={a.progress.total} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-semibold text-gray-900">{a.name}</p>
                    <p className="truncate text-sm text-gray-600">{a.mobile}{a.label ? ` · ${a.label}` : ''}</p>
                    <p className="truncate text-xs text-gray-500">
                      {next ? `Next: ${next.label}` : 'All set'}{a.last_activity ? ` · ${timeAgo(a.last_activity)}` : ''}
                    </p>
                  </div>
                  <span aria-hidden className="text-xl text-gray-400">›</span>
                </Link>
              </li>
            )
          })}
        </ul>
      )}
      <Btn onClick={() => setAdding(true)}>+ Add agent</Btn>
      {adding && <AddAgentSheet onClose={() => setAdding(false)} onCreated={reload} />}
    </div>
  )
}
