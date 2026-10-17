'use client'
import Link from 'next/link'
import React, { useState } from 'react'
import { adminApi } from '@/lib/app/admin'
import type { InviteRequest, InvitedRequest, TrialSignup } from '@/lib/app/admin'
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

const TABS = ['setup', 'active', 'all', 'signedup', 'asked']
const settingUp = (a: AgentSummary) => a.progress.done < a.progress.total

/** An agent who took the free trial himself: not one you set up, so no checklist; how far he got and his page. */
function SignupRow({ s }: { s: TrialSignup }) {
  const step = !s.signed_up ? 'Code sent, not signed in yet' : s.listings ? `${s.listings} listing${s.listings === 1 ? '' : 's'}` : 'Signed in, no listing yet'
  const body = (
    <div className="min-w-0 flex-1">
      <p className="truncate font-semibold text-gray-900">{s.name || 'Name not given yet'}</p>
      <p className="truncate text-sm text-gray-600">{s.mobile}{s.via ? ` · trial on ${s.via === 'whatsapp' ? 'WhatsApp' : s.via}` : ''}</p>
      <p className="truncate text-xs text-gray-500">{step}{s.claimed_at ? ` · claimed ${timeAgo(s.claimed_at)}` : ''}</p>
    </div>
  )
  const cls = 'min-h-[72px] items-center gap-3 rounded-2xl border border-gray-200 bg-white p-3 [display:flex]'
  return (
    <li data-testid="signup-row">
      {s.slug ? <a href={`/agent/${encodeURIComponent(s.slug)}`} target="_blank" rel="noopener noreferrer" className={`${cls} active:bg-gray-50`}>{body}<span className="text-sm text-gray-500">Page &rsaquo;</span></a>
        : <div className={cls}>{body}</div>}
    </li>
  )
}

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
  const signups = useAsync<TrialSignup[]>(() => adminApi.trialSignups().catch(() => []), [])
  const [adding, setAdding] = useState(false)
  const [invited, setInvited] = useState<InvitedRequest | null>(null)

  const agents = data ?? []
  const asked = requests.data ?? []
  const setup = agents.filter(settingUp)
  const active = agents.filter((a) => !settingUp(a))
  const [tab, setTab] = useUrlTab('tab', setup.length ? 'setup' : 'all', TABS)

  // opening Asked to join (Signed up) is seeing the requests (trial claims): their alerts on Studio home are cleared
  React.useEffect(() => {
    const kind = tab === 'asked' ? 'invite_request' : tab === 'signedup' ? 'trial_claimed' : null
    if (!kind) return
    getNotifications(true)
      .then((n) => Promise.all(n.items.filter((x) => x.kind === kind).map((x) => markNotificationRead(x.id))))
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
        { key: 'signedup', label: 'Signed up', count: (signups.data ?? []).length },
        { key: 'asked', label: 'Asked to join', count: asked.length, tone: 'urgent' },
      ]} />
      {error && <ErrorBox message={error} onRetry={reload} />}
      {tab === 'signedup' ? (
        <>
          <p className="text-sm text-gray-600">Agents who took the free trial themselves (TRIAL on WhatsApp). Reach out on WhatsApp and help with the first property.</p>
          {signups.loading && !signups.data ? <Spinner /> : (signups.data ?? []).length === 0 ? (
            <p className="rounded-2xl bg-white p-6 text-center text-gray-600">Nobody has taken the trial yet.</p>
          ) : (
            <ul className="space-y-2">{(signups.data ?? []).map((s) => <SignupRow key={s.id} s={s} />)}</ul>
          )}
        </>
      ) : tab === 'asked' ? (
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
