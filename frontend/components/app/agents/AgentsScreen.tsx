'use client'
import Link from 'next/link'
import React, { useState } from 'react'
import { adminApi } from '@/lib/app/admin'
import type { InviteRequest, InvitedRequest } from '@/lib/app/admin'
import { conciergeApi } from '@/lib/app/concierge'
import type { AgentSummary } from '@/lib/app/concierge'
import { timeAgo } from '@/lib/app/format'
import { useAsync } from '@/lib/app/useAsync'
import { getNotifications, markNotificationRead } from '@/lib/app/whatsapp'
import { StatusPill, TabBar, useUrlTab } from '../list'
import { Btn, ErrorBox, PageTitle, Spinner } from '../ui'
import { AddAgentSheet } from './AddAgentSheet'
import { CodeSheet, InviteRow } from './InviteRequests'
import { ProgressRing } from './ProgressRing'
import { BRAND_NAME } from '@/lib/brand'

const TABS = ['setup', 'active', 'all', 'asked']
const settingUp = (a: AgentSummary) => a.progress.done < a.progress.total

function AgentRow({ a }: { a: AgentSummary }) {
  const next = a.checklist.find((c) => !c.done)
  return (
    <li>
      <Link href={`/studio/agents/${encodeURIComponent(a.id)}`} data-testid="agent-row"
        className="min-h-[72px] items-center gap-3 rounded-2xl border border-gray-200 bg-white p-3 active:bg-gray-50 [display:flex]">
        <ProgressRing done={a.progress.done} total={a.progress.total} />
        <div className="min-w-0 flex-1">
          <p className="truncate font-semibold text-gray-900">{a.name}</p>
          <p className="truncate text-sm text-gray-600">{a.mobile}{a.label ? ` · ${a.label}` : ''}</p>
          <p className="truncate text-xs text-gray-500">
            {next ? `Next: ${next.label}` : 'All set'}{a.last_activity ? ` · ${timeAgo(a.last_activity)}` : ''}
          </p>
        </div>
        {settingUp(a) ? <StatusPill tone="action">Setting up</StatusPill> : <StatusPill tone="ok">Active</StatusPill>}
      </Link>
    </li>
  )
}

/**
 * Studio > Agents (owner only): every agent you set up, with how far along each one is, and the people who asked to join
 * on the website (moved here from Admin, which links to the Asked to join tab).
 */
export function AgentsScreen() {
  const { data, error, loading, reload } = useAsync(() => conciergeApi.list(), [])
  const requests = useAsync<InviteRequest[]>(() => adminApi.inviteRequests().catch(() => []), [])
  const [adding, setAdding] = useState(false)
  const [invited, setInvited] = useState<InvitedRequest | null>(null)

  const agents = data ?? []
  const asked = requests.data ?? []
  const setup = agents.filter(settingUp)
  const active = agents.filter((a) => !settingUp(a))
  const [tab, setTab] = useUrlTab('tab', setup.length ? 'setup' : 'all', TABS)

  // opening Asked to join is seeing the requests: the 'new request to join' alerts on Studio home are cleared
  React.useEffect(() => {
    if (tab !== 'asked') return
    getNotifications(true)
      .then((n) => Promise.all(n.items.filter((x) => x.kind === 'invite_request').map((x) => markNotificationRead(x.id))))
      .catch(() => undefined)
  }, [tab])

  if (loading && !data) return <Spinner />
  if (error && !data) return <ErrorBox message={error} onRetry={reload} />

  const shown = tab === 'setup' ? setup : tab === 'active' ? active : agents
  const empty: Record<string, string> = {
    setup: 'Everyone is set up.',
    active: 'No agent has finished setting up yet.',
    all: 'No agents yet. Add the first one.',
  }
  const refresh = () => { reload(); requests.reload() }

  return (
    <div className="space-y-4">
      <PageTitle>Agents</PageTitle>
      <TabBar label="Agents" value={tab} onChange={setTab} tabs={[
        { key: 'setup', label: 'Setting up', count: setup.length },
        { key: 'active', label: 'Active', count: active.length },
        { key: 'all', label: 'All', count: agents.length },
        { key: 'asked', label: 'Asked to join', count: asked.length, tone: 'urgent' },
      ]} />
      {error && <ErrorBox message={error} onRetry={reload} />}
      {tab === 'asked' ? (
        <>
          <p className="text-sm text-gray-600">People who asked to join on the website. Invite makes the agent and gives you his code to send.</p>
          {requests.loading && !requests.data ? <Spinner /> : asked.length === 0 ? (
            <p className="rounded-2xl bg-white p-6 text-center text-gray-600">Nobody is waiting to join.</p>
          ) : (
            <ul className="space-y-2">
              {asked.map((r) => (
                <InviteRow key={r.id} req={r} onInvited={(res) => { setInvited(res); refresh() }} onDismissed={() => requests.reload()} />
              ))}
            </ul>
          )}
        </>
      ) : (
        <>
          <p className="text-sm text-gray-600">Agents you set up. Their listings go on the {BRAND_NAME} pages with their name, and buyers reach them.</p>
          {shown.length === 0 ? (
            <p className="rounded-2xl bg-white p-6 text-center text-gray-600">{agents.length === 0 ? empty.all : empty[tab]}</p>
          ) : (
            <ul className="space-y-3">{shown.map((a) => <AgentRow key={a.id} a={a} />)}</ul>
          )}
          <Btn onClick={() => setAdding(true)}>+ Add agent</Btn>
        </>
      )}
      {adding && <AddAgentSheet onClose={() => setAdding(false)} onCreated={reload} />}
      {invited && <CodeSheet result={invited} onClose={() => setInvited(null)} />}
    </div>
  )
}
