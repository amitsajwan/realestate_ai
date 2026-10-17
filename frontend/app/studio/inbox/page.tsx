'use client'
import Link from 'next/link'
import React from 'react'
import { TabBar, useUrlTab } from '@/components/app/list'
import { ErrorBox, PageTitle, Spinner } from '@/components/app/ui'
import { timeAgo } from '@/lib/app/format'
import { CHANNEL_CHIP, CHANNEL_LABEL, inboxApi, type InboxThread } from '@/lib/app/inbox'
import { useAsync } from '@/lib/app/useAsync'
import { getNotifications, markNotificationRead } from '@/lib/app/whatsapp'

const TABS = ['needs', 'all', 'agents', 'buyers']
const FROM: Record<string, string> = { them: 'They wrote', bot: 'Bot', you: 'You' }

function ThreadRow({ t }: { t: InboxThread }) {
  return (
    <li>
      <Link href={`/studio/inbox/${encodeURIComponent(t.id)}`} data-testid="inbox-row"
        className={'block space-y-1 rounded-2xl border bg-white p-4 active:bg-gray-50 ' + (t.needs_you ? 'border-amber-400' : 'border-gray-200')}>
        <div className="flex items-center justify-between gap-2">
          <p className="min-w-0 truncate font-semibold text-gray-900">{t.name || (t.role === 'agent' ? 'Agent' : t.channel === 'website' ? 'Website visitor' : 'Buyer')}</p>
          <span className="shrink-0 text-xs text-gray-500">{t.last_at ? timeAgo(t.last_at) : ''}</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          <span className={'rounded-full px-2 py-0.5 text-xs font-semibold ' + (CHANNEL_CHIP[t.channel] ?? CHANNEL_CHIP.website)}>{CHANNEL_LABEL[t.channel] ?? t.channel}</span>
          <span className={'rounded-full px-2 py-0.5 text-xs font-semibold ' + (t.role === 'agent' ? 'bg-sky-100 text-sky-800' : 'bg-orange-100 text-orange-800')}>{t.role === 'agent' ? 'Agent' : 'Buyer'}</span>
          {t.needs_you && <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-900">Needs you</span>}
          {t.lead_saved && <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-800">Lead saved</span>}
          {t.opted_out && <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-800">Said STOP</span>}
        </div>
        {t.summary && <p className="text-sm text-gray-700">{t.summary}</p>}
        <p className="line-clamp-2 text-sm text-gray-600"><span className="font-semibold">{t.last_from ? `${FROM[t.last_from]}: ` : ''}</span>{t.last_text}</p>
      </Link>
    </li>
  )
}

/** Studio > Inbox: every conversation in one list. Needs you first (their message is the last one), then everything, agents, buyers. */
export default function InboxPage() {
  const { data, error, loading, reload } = useAsync(() => inboxApi.threads(), [])
  const all = data ?? []
  const needs = all.filter((t) => t.needs_you)
  const [tab, setTab] = useUrlTab('tab', 'all', TABS)
  // opening the inbox is seeing the new messages: the WhatsApp alerts on Studio home are cleared
  React.useEffect(() => {
    if (!data) return
    getNotifications(true)
      .then((n) => Promise.all(n.items.filter((x) => x.kind.includes('whatsapp') || x.kind.includes('chat')).map((x) => markNotificationRead(x.id))))
      .catch(() => undefined)
  }, [data])
  if (loading && !data) return <Spinner />
  if (error && !data) return <ErrorBox message={error} onRetry={reload} />
  const shown = tab === 'needs' ? needs : tab === 'agents' ? all.filter((t) => t.role === 'agent') : tab === 'buyers' ? all.filter((t) => t.role !== 'agent') : all
  return (
    <div className="space-y-4">
      <PageTitle>Inbox</PageTitle>
      <p className="text-sm text-gray-600">Every conversation in one place: WhatsApp, Facebook and Instagram messages, and your website chat. Tap one to read it all and reply.</p>
      <TabBar label="Inbox" value={tab} onChange={setTab} tabs={[
        { key: 'needs', label: 'Needs you', count: needs.length, tone: 'urgent' },
        { key: 'all', label: 'All', count: all.length },
        { key: 'agents', label: 'Agents', count: all.filter((t) => t.role === 'agent').length },
        { key: 'buyers', label: 'Buyers', count: all.filter((t) => t.role !== 'agent').length },
      ]} />
      {shown.length === 0 ? (
        <p className="rounded-2xl bg-white p-6 text-center text-gray-600">{tab === 'needs' ? 'Nothing waiting for you.' : 'No conversations yet.'}</p>
      ) : (
        <ul className="space-y-2">{shown.map((t) => <ThreadRow key={t.id} t={t} />)}</ul>
      )}
    </div>
  )
}
