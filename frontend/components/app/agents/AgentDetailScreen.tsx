'use client'
import Link from 'next/link'
import React, { useState } from 'react'
import { CONSENT_TEXT, conciergeApi, firstName, friendlyConciergeError } from '@/lib/app/concierge'
import type { AgentDetail } from '@/lib/app/concierge'
import { formatPrice, timeAgo } from '@/lib/app/format'
import { useAsync } from '@/lib/app/useAsync'
import type { Listing } from '@/lib/app/types'
import { Btn, ErrorBox, LinkBtn, Spinner, StatusChip } from '../ui'
import { AgentBrandEditor } from './BrandEditorSlot'
import { PostSheet } from './PostSheet'
import { ProgressRing } from './ProgressRing'
import { BRAND_NAME } from '@/lib/brand'

const card = 'space-y-3 rounded-2xl border border-gray-200 bg-white p-4'

function Checklist({ agent }: { agent: AgentDetail }) {
  return (
    <section aria-label="Setup checklist" className={card}>
      <h2 className="text-base font-bold text-gray-900">Setup checklist</h2>
      <ul className="grid grid-cols-1 gap-1.5">
        {agent.checklist.map((c) => (
          <li key={c.key} data-testid={`check-${c.key}`} data-done={c.done} className="flex items-center gap-2 text-sm">
            <span aria-hidden className={`flex h-5 w-5 items-center justify-center rounded-full text-xs font-bold ${c.done ? 'bg-green-600 text-white' : 'border border-gray-300 text-transparent'}`}>✓</span>
            <span className={c.done ? 'text-gray-900' : 'text-gray-600'}>{c.label}</span>
            <span className="sr-only">{c.done ? 'done' : 'to do'}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}

function ConsentCard({ agent, onChange }: { agent: AgentDetail; onChange: () => void }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const given = agent.consent_given
  async function toggle() {
    setBusy(true)
    setError(null)
    try {
      await conciergeApi.setConsent(agent.id, !given)
      onChange()
    } catch (e) {
      setError(friendlyConciergeError(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <section aria-label="Consent" className={card}>
      <h2 className="text-base font-bold text-gray-900">Consent</h2>
      <p className="rounded-xl bg-gray-50 p-3 text-sm italic text-gray-700" data-testid="consent-text">&ldquo;{CONSENT_TEXT}&rdquo;</p>
      <p className="text-xs text-gray-500">Ask {firstName(agent.name)} to agree (for example on WhatsApp) before you record it here. You cannot post his listings without it.</p>
      <button type="button" role="switch" aria-checked={given} onClick={toggle} disabled={busy}
        className="flex min-h-[52px] w-full items-center justify-between gap-3 rounded-xl border border-gray-200 px-4 text-left text-sm font-semibold text-gray-900 disabled:opacity-60">
        <span>{given ? `${firstName(agent.name)} agreed${agent.consent.at ? ` (${timeAgo(agent.consent.at)})` : ''}` : `${firstName(agent.name)} has agreed`}</span>
        <span aria-hidden className={`relative h-7 w-12 rounded-full transition-colors ${given ? 'bg-green-600' : 'bg-gray-300'}`}>
          <span className={`absolute top-0.5 h-6 w-6 rounded-full bg-white shadow transition-all ${given ? 'left-[22px]' : 'left-0.5'}`} />
        </span>
      </button>
      {error && <ErrorBox message={error} />}
    </section>
  )
}

function ListingRow({ l, agent, onPost, onChanged }: { l: Listing; agent: AgentDetail; onPost: (l: Listing) => void; onChanged: () => void }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  async function publish() {
    setBusy(true)
    setError(null)
    try {
      await conciergeApi.publishListing(agent.id, l.id)
      onChanged()
    } catch (e) {
      setError(friendlyConciergeError(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <li className="space-y-2 rounded-xl border border-gray-200 p-3" data-testid="agent-listing">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-semibold text-gray-900">{l.title}</p>
          <p className="truncate text-sm text-gray-600">{formatPrice(l.price_inr, l.transaction === 'rent')} · {l.locality}</p>
        </div>
        <StatusChip status={l.status} />
      </div>
      {l.status === 'draft' && <Btn variant="secondary" onClick={publish} disabled={busy} className="!min-h-[44px]">{busy ? 'Publishing...' : 'Publish'}</Btn>}
      {l.status === 'live' && <Btn variant="secondary" onClick={() => onPost(l)} className="!min-h-[44px]">Post to {BRAND_NAME}</Btn>}
      {error && <ErrorBox message={error} />}
    </li>
  )
}

/** One agent: checklist, brand, listings, consent, preview of his page. */
export function AgentDetailScreen({ id }: { id: string }) {
  const { data: agent, error, loading, reload } = useAsync(() => conciergeApi.get(id), [id])
  const [posting, setPosting] = useState<Listing | null>(null)

  if (loading && !agent) return <Spinner />
  if (error && !agent) return <ErrorBox message={error} onRetry={reload} />
  if (!agent) return null
  const first = firstName(agent.name)

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Link href="/studio/agents" aria-label="Back to agents" className="flex min-h-[44px] min-w-[44px] items-center text-xl">←</Link>
        <ProgressRing done={agent.progress.done} total={agent.progress.total} />
        <div className="min-w-0">
          <h1 className="truncate text-xl font-bold text-gray-900">{agent.name}</h1>
          <p className="truncate text-sm text-gray-600">{agent.mobile}{agent.label ? ` · ${agent.label}` : ''}</p>
        </div>
      </div>
      {error && <ErrorBox message={error} onRetry={reload} />}

      <Checklist agent={agent} />
      {agent.slug && <LinkBtn variant="secondary" href={`/agent/${agent.slug}`} target="_blank" rel="noopener noreferrer">Preview {first}&apos;s page</LinkBtn>}

      <section aria-label="Brand" className={card}>
        <h2 className="text-base font-bold text-gray-900">Brand</h2>
        <AgentBrandEditor agentId={agent.id} onSaved={reload} />
      </section>

      <section aria-label="Listings" className={card}>
        <h2 className="text-base font-bold text-gray-900">Listings</h2>
        {agent.listings.length === 0 ? (
          <p className="text-sm text-gray-600">No listings yet. Add the first one from what {first} sent you.</p>
        ) : (
          <ul className="space-y-2">
            {agent.listings.map((l) => <ListingRow key={l.id} l={l} agent={agent} onPost={setPosting} onChanged={reload} />)}
          </ul>
        )}
        <LinkBtn href={`/studio/agents/${encodeURIComponent(agent.id)}/listings/new`}>Add listing for {first}</LinkBtn>
      </section>

      <ConsentCard agent={agent} onChange={reload} />

      {posting && (
        <PostSheet agentId={agent.id} agentName={agent.name} listingId={posting.id} listingTitle={posting.title}
          consentGiven={agent.consent_given} onClose={() => setPosting(null)} />
      )}
    </div>
  )
}
