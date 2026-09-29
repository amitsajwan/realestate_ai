'use client'
import Link from 'next/link'
import React, { useState } from 'react'
import { ErrorBox, PageTitle, STAGES, Spinner, TempChip } from '@/components/app/ui'
import { api } from '@/lib/app/client'
import { displayPhone, timeAgo } from '@/lib/app/format'
import { sortLeads, sourceLabel } from '@/lib/app/leads'
import { t } from '@/lib/app/strings'
import { useAsync } from '@/lib/app/useAsync'
import type { Stage } from '@/lib/app/types'

export default function LeadsPage() {
  const [stage, setStage] = useState<Stage | ''>('')
  const { data, error, loading, reload } = useAsync(async () => {
    const [leads, listings] = await Promise.all([api.listLeads(stage || undefined), api.listListings().catch(() => [])])
    return { leads: sortLeads(leads), titles: Object.fromEntries(listings.map((l) => [l.id, l.title])) as Record<string, string> }
  }, [stage])

  return (
    <div className="space-y-3">
      <PageTitle>{t('leads')}</PageTitle>
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
      {loading && !data && <Spinner />}
      {error && <ErrorBox message={error} onRetry={reload} />}
      {data && data.leads.length === 0 && <p className="py-8 text-center text-gray-500">{t('noLeads')}</p>}
      {data?.leads.map((l) => (
        <Link key={l.id} href={`/studio/leads/${l.id}`} className="block min-h-[88px] rounded-2xl border border-gray-200 bg-white p-4 active:bg-gray-50">
          <div className="flex items-center justify-between gap-2">
            <p className="truncate font-semibold text-gray-900">{l.name}</p>
            <TempChip temperature={l.temperature} score={l.score} />
          </div>
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
