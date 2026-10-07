'use client'
import React, { useState } from 'react'
import { FreshnessSection } from '@/components/app/FreshnessPrompt'
import { ListingCard } from '@/components/app/ListingCard'
import { TabBar, useUrlTab } from '@/components/app/list'
import { ErrorBox, LinkBtn, PageTitle, Spinner } from '@/components/app/ui'
import { api } from '@/lib/app/client'
import { conciergeApi } from '@/lib/app/concierge'
import type { AgentSummary } from '@/lib/app/concierge'
import { needingConfirmation } from '@/lib/app/freshness'
import { t } from '@/lib/app/strings'
import type { Listing, ListingStatus, PerformanceItem } from '@/lib/app/types'
import { useAsync } from '@/lib/app/useAsync'

const TABS = ['needs', 'live', 'drafts', 'closed']
const IN_TAB: Record<string, ListingStatus[]> = {
  live: ['live', 'under_offer'],
  drafts: ['draft'],
  closed: ['sold', 'rented', 'paused', 'expired'],
}
const EMPTY: Record<string, string> = {
  needs: 'Nothing needs you. Every live listing is confirmed.',
  live: 'No live listings. Add one, or open Drafts to post one.',
  drafts: 'No drafts.',
  closed: 'Nothing sold, rented or paused yet.',
}

/** The agent filter (owner only), kept in the address as ?agent=. '' is your own listings. */
function readAgent(): string {
  if (typeof window === 'undefined') return ''
  return new URLSearchParams(window.location.search).get('agent') ?? ''
}

export default function ListingsPage() {
  const [agent, setAgentState] = useState<string>(readAgent)
  const setAgent = (id: string) => {
    setAgentState(id)
    if (typeof window !== 'undefined') {
      const u = new URL(window.location.href)
      if (id) u.searchParams.set('agent', id)
      else u.searchParams.delete('agent')
      window.history.replaceState(window.history.state, '', u.toString())
    }
  }
  // The owner sees the agents he set up; for everyone else this 403s and there is no filter.
  const agents = useAsync<AgentSummary[] | null>(() => conciergeApi.list().catch(() => null), [])
  const { data, error, loading, reload, setData } = useAsync(async () => {
    if (agent) {
      const a = await conciergeApi.get(agent)
      return { agent, listings: a.listings ?? [], perf: new Map<string, PerformanceItem>() }
    }
    // Performance is a nice-to-have: the list still shows if it cannot be loaded.
    const [listings, perf] = await Promise.all([api.listListings(), api.getPerformance().catch(() => [] as PerformanceItem[])])
    return { agent, listings, perf: new Map((perf ?? []).map((p) => [p.listing_id, p])) }
  }, [agent])

  const listings = data?.listings ?? []
  const need = needingConfirmation(listings)
  // The default is fixed when the list first loads, so answering the last prompt does not jump to another tab.
  // Worked out once per list (yours, or the agent you picked), from that list's own data.
  const [initial, setInitial] = useState<{ agent: string; tab: string } | null>(null)
  React.useEffect(() => {
    if (data && data.agent === agent && initial?.agent !== agent) {
      const hash = typeof window !== 'undefined' && window.location.hash === '#confirm'
      setInitial({ agent, tab: hash || needingConfirmation(data.listings).length ? 'needs' : 'live' })
    }
  }, [data, initial, agent])
  const [tab, setTab] = useUrlTab('tab', initial?.tab ?? 'live', TABS)

  // Arriving from the home "Listings that need your confirmation" card: the list loads after the page, so scroll once it is there.
  const loaded = !!data
  React.useEffect(() => {
    if (loaded && typeof window !== 'undefined' && window.location.hash === '#confirm') {
      document.getElementById('confirm')?.scrollIntoView?.({ block: 'start' })
    }
  }, [loaded])
  // After "still available?" / sold / paused the server returns the listing: swap it in so its card and chip update.
  const replace = (updated: Listing) =>
    setData((d) => (d ? { ...d, listings: d.listings.map((l) => (l.id === updated.id ? updated : l)) } : d))

  const count = (k: string) => listings.filter((l) => IN_TAB[k].includes(l.status)).length
  const shown = tab === 'needs' ? [] : listings.filter((l) => IN_TAB[tab].includes(l.status))
  const others = agents.data ?? []
  const agentHref = agent ? `/studio/agents/${encodeURIComponent(agent)}` : undefined

  return (
    <div className="space-y-3">
      <PageTitle>{t('listings')}</PageTitle>
      {others.length > 0 && (
        <div className="items-center gap-2 [display:flex]">
          <label htmlFor="listing-agent" className="flex-none text-sm font-semibold text-gray-700">Agent</label>
          <select id="listing-agent" value={agent} onChange={(e) => { setAgent(e.target.value) }}
            className="min-h-[44px] min-w-0 flex-1 rounded-xl border border-gray-300 bg-white px-3 text-base text-gray-900">
            <option value="">My listings</option>
            {others.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
          </select>
        </div>
      )}
      {!agent && <LinkBtn href="/studio/listings/new">{t('addListing')}</LinkBtn>}
      {agent && <LinkBtn variant="secondary" href={agentHref}>Open {others.find((a) => a.id === agent)?.name ?? 'the agent'}&apos;s page</LinkBtn>}
      {data && (
        <TabBar label="Listings" value={tab} onChange={setTab} tabs={[
          { key: 'needs', label: 'Needs you', count: need.length, tone: 'urgent' },
          { key: 'live', label: 'Live', count: count('live') },
          { key: 'drafts', label: 'Drafts', count: count('drafts') },
          { key: 'closed', label: 'Closed', count: count('closed') },
        ]} />
      )}
      {loading && !data && <Spinner />}
      {error && <ErrorBox message={error} onRetry={reload} />}
      {data && tab === 'needs' && (agent ? (
        // Only the agent can answer for his own listings (the confirm endpoints are his): show them, opening his page.
        need.map((l) => <ListingCard key={l.id} listing={l} href={agentHref} />)
      ) : (
        <FreshnessSection listings={listings} onUpdated={replace} />
      ))}
      {data && (tab === 'needs' ? need.length === 0 : shown.length === 0) && (
        <p className="rounded-2xl bg-white p-4 text-center text-sm text-gray-600">{listings.length === 0 ? t('noListings') : EMPTY[tab]}</p>
      )}
      {shown.map((l) => <ListingCard key={l.id} listing={l} performance={data?.perf.get(l.id)} href={agentHref} />)}
    </div>
  )
}
