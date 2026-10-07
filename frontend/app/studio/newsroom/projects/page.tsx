'use client'
import React from 'react'
import Link from 'next/link'
import { LinkOut, StatusPill, TabBar, useUrlTab } from '@/components/app/list'
import type { PillTone } from '@/components/app/list'
import { ErrorBox, PageTitle, Spinner } from '@/components/app/ui'
import { timeAgo } from '@/lib/app/format'
import { getEnrichment } from '@/lib/app/enrichment'
import type { EnrichItem, EnrichStatus } from '@/lib/app/enrichment'
import { useAsync } from '@/lib/app/useAsync'

const TABS: EnrichStatus[] = ['ok', 'partial', 'failed', 'waiting']
const LABEL: Record<EnrichStatus, string> = { ok: 'Enriched', partial: 'Partial', failed: 'Failed', waiting: 'Waiting' }
const TONE: Record<EnrichStatus, PillTone> = { ok: 'ok', partial: 'action', failed: 'bad', waiting: 'muted' }
const STEP: Record<string, string> = { maharera_general: 'MahaRERA record', buildings: 'Buildings', places: 'Map position', text: 'Page text' }

function Row({ item }: { item: EnrichItem }) {
  return (
    <li className="list-none rounded-2xl bg-white p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-semibold text-gray-900">{item.name}</p>
          <p className="text-xs text-gray-600">{[item.regno, item.area, item.enriched_at ? `enriched ${timeAgo(item.enriched_at)}` : 'not enriched yet'].filter(Boolean).join(' · ')}</p>
        </div>
        <StatusPill tone={TONE[item.status]}>{item.score ?? LABEL[item.status]}</StatusPill>
      </div>
      {item.failed.length > 0 && (
        <ul className="mt-2 space-y-1 p-0 text-xs text-gray-700">
          {item.failed.map((k) => {
            const why = item.checks[k]
            return <li key={k} className="list-none"><span className="font-semibold">{STEP[k] ?? k}:</span> {Array.isArray(why) ? why.join('; ') : why || 'failed'}</li>
          })}
        </ul>
      )}
      {item.page && <LinkOut href={item.page} label={item.name}>Open page</LinkOut>}
    </li>
  )
}

/** Which project pages are enriched and checked (MahaRERA record, buildings, map position, text). */
export default function ProjectEnrichmentPage() {
  const [tab, setTab] = useUrlTab('status', 'failed', TABS)
  const all = useAsync(() => getEnrichment(), [])
  const list = useAsync(() => getEnrichment(tab as EnrichStatus), [tab])
  const counts = all.data?.counts
  return (
    <div className="space-y-3 pb-24">
      <PageTitle action={<Link href="/studio/newsroom" className="inline-flex min-h-[44px] items-center text-sm font-semibold text-[#0f2340] underline">Newsroom</Link>}>
        Project pages
      </PageTitle>
      {all.error && <ErrorBox message={all.error} onRetry={all.reload} />}
      <TabBar label="Enrichment" value={tab} onChange={setTab}
        tabs={TABS.map((k) => ({ key: k, label: LABEL[k], count: counts?.[k], tone: k === 'failed' ? 'urgent' : undefined }))} />
      <p className="text-xs text-gray-600">One project every 10 minutes. Each step is checked: the MahaRERA answers carry this project&apos;s registration number, and the map position is near its pincode.</p>
      {list.loading ? <Spinner /> : list.error ? <ErrorBox message={list.error} onRetry={list.reload} /> :
        !list.data?.items.length ? <p className="rounded-2xl bg-white p-4 text-sm text-gray-600">Nothing here.</p> : (
          <ul className="space-y-2 p-0">{list.data.items.map((i) => <Row key={i.regno} item={i} />)}</ul>
        )}
    </div>
  )
}
