'use client'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import React, { Suspense, useState } from 'react'
import { StatusPill, TabBar, useUrlTab } from '@/components/app/list'
import { OutcomeBadge } from '@/components/app/OutcomeSheets'
import { ErrorBox, PageTitle, STAGES, Spinner, TempChip } from '@/components/app/ui'
import { api } from '@/lib/app/client'
import { displayPhone, timeAgo } from '@/lib/app/format'
import { buildWhatsappUrl, sortLeads, sourceLabel } from '@/lib/app/leads'
import { t } from '@/lib/app/strings'
import { useAsync } from '@/lib/app/useAsync'
import type { Lead, TodayFollowUp } from '@/lib/app/types'

/** Tabs: follow-ups due today first, then the stages, then everything. Kept in the address as ?tab= (and ?hot=1). */
const TABS = ['today', ...STAGES.map((s) => s.key as string), 'all']
/** Home tiles and older links used ?filter=: they still land on the right tab. */
const LEGACY: Record<string, { tab: string; hot?: boolean }> = {
  new: { tab: 'new' }, hot: { tab: 'all', hot: true }, site_visit: { tab: 'site_visit' }, followups: { tab: 'today' },
}
const EMPTY: Record<string, string> = { today: 'No follow-ups due today.', all: t('noLeads') }

const isOpen = (l: Lead) => l.stage !== 'won' && l.stage !== 'lost'

function setHotInUrl(on: boolean) {
  if (typeof window === 'undefined') return
  const u = new URL(window.location.href)
  if (on) u.searchParams.set('hot', '1')
  else u.searchParams.delete('hot')
  u.searchParams.delete('filter')
  window.history.replaceState(window.history.state, '', u.toString())
}

function LeadRow({ lead, title, due }: { lead: Lead; title?: string; due?: TodayFollowUp }) {
  return (
    <li className="rounded-2xl border border-gray-200 bg-white">
      <Link href={`/studio/leads/${lead.id}`} className="block min-h-[72px] rounded-t-2xl p-4 pb-2 active:bg-gray-50">
        <div className="items-center justify-between gap-2 [display:flex]">
          <p className="truncate font-semibold text-gray-900">{lead.name}</p>
          <span className="flex-none items-center gap-1 [display:flex]">
            <OutcomeBadge outcome={lead.outcome} />
            <TempChip temperature={lead.temperature} score={lead.score} />
          </span>
        </div>
        {due && (
          <p className="mt-1 items-center gap-2 text-sm text-gray-700 [display:flex]">
            <StatusPill tone={due.overdue ? 'bad' : 'action'}>{due.overdue ? 'Overdue' : 'Due today'}</StatusPill>
            <span className="truncate">{due.reason}</span>
          </p>
        )}
        {lead.requirement_line && <p className="truncate text-sm font-medium text-gray-800">{lead.requirement_line}</p>}
        <p className="text-sm text-gray-500">{displayPhone(lead.phone)}</p>
        {lead.message && <p className="mt-1 truncate text-sm text-gray-700">“{lead.message}”</p>}
        <p className="mt-1 truncate text-xs text-gray-500">
          {[sourceLabel(lead.source), title ?? '', timeAgo(lead.last_activity_at)].filter(Boolean).join(' - ')}
        </p>
      </Link>
      {lead.phone && (
        <div className="grid-cols-2 gap-2 border-t border-gray-100 px-3 py-1 [display:grid]">
          <a href={`tel:${lead.phone}`} aria-label={`${t('call')} ${lead.name}`}
            className="min-h-[44px] items-center justify-center rounded-xl text-sm font-semibold text-[#0f2340] active:bg-gray-100 [display:flex]">
            📞 {t('call')}
          </a>
          <a href={buildWhatsappUrl(lead.phone, '')} target="_blank" rel="noopener noreferrer" aria-label={`${t('whatsapp')} ${lead.name}`}
            className="min-h-[44px] items-center justify-center rounded-xl text-sm font-semibold text-green-700 active:bg-green-50 [display:flex]">
            {t('whatsapp')}
          </a>
        </div>
      )}
    </li>
  )
}

function LeadsList() {
  const params = useSearchParams()
  const legacy = LEGACY[params?.get('filter') ?? '']
  const [hot, setHotState] = useState<boolean>(params?.get('hot') === '1' || !!legacy?.hot)
  const setHot = (on: boolean) => {
    setHotState(on)
    setHotInUrl(on)
  }
  const { data, error, loading, reload } = useAsync(async () => {
    const [leads, listings, today] = await Promise.all([
      api.listLeads(),
      api.listListings().catch(() => []),
      // Follow-ups are a nice-to-have: without them the list still shows (no Follow up today tab count).
      Promise.resolve().then(() => api.getToday()).then((d) => d?.follow_ups ?? [], () => [] as TodayFollowUp[]),
    ])
    return {
      leads: sortLeads(leads),
      titles: Object.fromEntries(listings.map((l) => [l.id, l.title])) as Record<string, string>,
      followUps: today,
    }
  }, [])

  // The default (Follow up today when something is due, else All) is fixed once the list loads.
  const [initial, setInitial] = useState<string | null>(null)
  React.useEffect(() => {
    if (data && initial === null) setInitial(data.followUps.length ? 'today' : 'all')
  }, [data, initial])
  const [tab, setTab] = useUrlTab('tab', legacy?.tab ?? initial ?? 'all', TABS)

  const leads = (data?.leads ?? []).filter((l) => !hot || (l.temperature === 'hot' && isOpen(l)))
  const due = new Map((data?.followUps ?? []).map((f) => [f.id, f]))
  const inTab = (k: string) =>
    k === 'all' ? leads
      : k === 'today' ? (data?.followUps ?? []).map((f) => leads.find((l) => l.id === f.id)).filter((l): l is Lead => !!l)
        : leads.filter((l) => l.stage === k)
  const shown = inTab(tab)

  return (
    <div className="space-y-3">
      <PageTitle>{t('leads')}</PageTitle>
      {data && (
        <TabBar label="Leads" value={tab} onChange={setTab} tabs={[
          { key: 'today', label: 'Follow up today', count: inTab('today').length, tone: 'urgent' },
          ...STAGES.map((s) => ({ key: s.key as string, label: s.label, count: inTab(s.key).length })),
          { key: 'all', label: t('all'), count: leads.length },
        ]} />
      )}
      <div className="items-center justify-between gap-2 [display:flex]">
        <p className="text-xs text-gray-600">{hot ? 'Showing hot buyers only.' : 'Hottest first.'}</p>
        <button type="button" role="switch" aria-checked={hot} onClick={() => setHot(!hot)}
          className={`min-h-[44px] flex-none rounded-full border px-4 text-sm font-semibold ${hot ? 'border-red-600 bg-red-600 text-white' : 'border-gray-300 bg-white text-gray-700'}`}>
          🔥 Hot only
        </button>
      </div>
      {loading && !data && <Spinner />}
      {error && <ErrorBox message={error} onRetry={reload} />}
      {data && shown.length === 0 && (
        <p className="rounded-2xl bg-white p-4 text-center text-sm text-gray-600">
          {hot ? 'No hot buyers here.' : EMPTY[tab] ?? `No leads in ${STAGES.find((s) => s.key === tab)?.label ?? tab}.`}
        </p>
      )}
      {data && shown.length > 0 && (
        <ul className="space-y-2 p-0">
          {shown.map((l) => (
            <LeadRow key={l.id} lead={l} title={l.first_listing_id ? data.titles[l.first_listing_id] : undefined} due={tab === 'today' ? due.get(l.id) : undefined} />
          ))}
        </ul>
      )}
    </div>
  )
}

export default function LeadsPage() {
  return (
    <Suspense fallback={<Spinner />}>
      <LeadsList />
    </Suspense>
  )
}
