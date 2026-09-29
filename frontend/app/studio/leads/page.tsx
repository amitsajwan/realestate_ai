'use client'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import React, { Suspense, useState } from 'react'
import { OutcomeBadge } from '@/components/app/OutcomeSheets'
import { ErrorBox, PageTitle, STAGES, Spinner, TempChip } from '@/components/app/ui'
import { api } from '@/lib/app/client'
import { displayPhone, timeAgo } from '@/lib/app/format'
import { sortLeads, sourceLabel } from '@/lib/app/leads'
import { t } from '@/lib/app/strings'
import { useAsync } from '@/lib/app/useAsync'
import type { Lead, Stage } from '@/lib/app/types'

/** Home-screen tiles link here with ?filter=. */
type Filter = 'new' | 'hot' | 'site_visit' | 'followups' | ''
const FILTER_LABEL = { new: 'tileNew', hot: 'tileHot', site_visit: 'tileVisits', followups: 'tileFollowUps' } as const

async function loadFiltered(filter: Filter, stage: Stage | ''): Promise<Lead[]> {
  if (filter === 'hot') return (await api.listLeads()).filter((l) => l.temperature === 'hot' && l.stage !== 'won' && l.stage !== 'lost')
  if (filter === 'followups') {
    const [today, leads] = await Promise.all([api.getToday(), api.listLeads()])
    const ids = new Set(today.follow_ups.map((f) => f.id))
    return leads.filter((l) => ids.has(l.id))
  }
  if (filter === 'new') return api.listLeads('new')
  if (filter === 'site_visit') return api.listLeads('site_visit')
  return api.listLeads(stage || undefined)
}

function LeadsList() {
  const param = useSearchParams()?.get('filter') ?? ''
  const [filter, setFilter] = useState<Filter>(((['new', 'hot', 'site_visit', 'followups'] as string[]).includes(param) ? param : '') as Filter)
  const [stage, setStage] = useState<Stage | ''>('')
  const { data, error, loading, reload } = useAsync(async () => {
    const [leads, listings] = await Promise.all([loadFiltered(filter, stage), api.listListings().catch(() => [])])
    return { leads: sortLeads(leads), titles: Object.fromEntries(listings.map((l) => [l.id, l.title])) as Record<string, string> }
  }, [stage, filter])

  return (
    <div className="space-y-3">
      <PageTitle>{t('leads')}</PageTitle>
      {filter ? (
        <div className="flex items-center justify-between rounded-xl bg-blue-50 px-4 py-2 text-sm text-blue-900">
          <span>
            {t('filterShowing')}: <b>{t(FILTER_LABEL[filter])}</b>
          </span>
          <button type="button" className="min-h-[44px] font-semibold underline" onClick={() => setFilter('')}>
            {t('clearFilter')}
          </button>
        </div>
      ) : (
        <div className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1" role="tablist" aria-label="Stage">
          {[{ key: '' as const, label: t('all') }, ...STAGES].map((s) => (
            <button
              key={s.key}
              type="button"
              role="tab"
              aria-selected={stage === s.key}
              onClick={() => setStage(s.key as Stage | '')}
              className={`min-h-[44px] flex-none rounded-full border px-4 text-sm font-semibold ${stage === s.key ? 'border-blue-600 bg-blue-600 text-white' : 'border-gray-300 bg-white text-gray-700'}`}
            >
              {s.label}
            </button>
          ))}
        </div>
      )}
      {loading && !data && <Spinner />}
      {error && <ErrorBox message={error} onRetry={reload} />}
      {data && data.leads.length === 0 && <p className="py-8 text-center text-gray-500">{t('noLeads')}</p>}
      {data?.leads.map((l) => (
        <Link key={l.id} href={`/studio/leads/${l.id}`} className="block min-h-[88px] rounded-2xl border border-gray-200 bg-white p-4 active:bg-gray-50">
          <div className="flex items-center justify-between gap-2">
            <p className="truncate font-semibold text-gray-900">{l.name}</p>
            <span className="flex flex-none items-center gap-1">
              <OutcomeBadge outcome={l.outcome} />
              <TempChip temperature={l.temperature} score={l.score} />
            </span>
          </div>
          {l.requirement_line && <p className="truncate text-sm font-medium text-gray-800">{l.requirement_line}</p>}
          <p className="text-sm text-gray-500">{displayPhone(l.phone)}</p>
          {l.message && <p className="mt-1 truncate text-sm text-gray-700">“{l.message}”</p>}
          <p className="mt-1 truncate text-xs text-gray-500">
            {[sourceLabel(l.source), l.first_listing_id ? data.titles[l.first_listing_id] : '', timeAgo(l.last_activity_at)].filter(Boolean).join(' - ')}
          </p>
        </Link>
      ))}
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
