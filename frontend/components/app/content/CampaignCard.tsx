'use client'
import React, { useState } from 'react'
import { Btn, ErrorBox } from '@/components/app/ui'
import { ConfirmSheet, StatusPill } from '@/components/app/list'
import { friendlyContentError, mediaUrl } from '@/lib/app/content'
import type { ContentGroup } from '@/lib/app/content'
import { ContentCard, TypeTag } from './ContentCard'
import type { ContentCardProps } from './ContentCard'

const OPEN = ['planned', 'approved', 'scheduled']

export interface CampaignCardProps extends Omit<ContentCardProps, 'group' | 'showType'> {
  title: string
  /** Each post of the campaign (its IG and FB copies together), in the order they go out. */
  groups: ContentGroup[]
}

const plural = (n: number, one: string, many = `${one}s`) => `${n} ${n === 1 ? one : many}`

/** Every post of one property campaign ("Gulmohar City · 4 posts") as one card; opened, its posts and Approve all / Skip all. */
export function CampaignCard({ title, groups, open = false, onToggle, onApprove, onSkip, ...rest }: CampaignCardProps) {
  const [inner, setInner] = useState<string | null>(null)
  const [ask, setAsk] = useState<'approve' | 'skip' | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const items = groups.flatMap((g) => g.items)
  const planned = items.filter((i) => i.status === 'planned')
  const openItems = items.filter((i) => OPEN.includes(i.status))
  const plannedPosts = groups.filter((g) => g.items.some((i) => i.status === 'planned')).length
  const openPosts = groups.filter((g) => g.items.some((i) => OPEN.includes(i.status))).length
  const failed = items.some((i) => i.status === 'failed')
  const cover = groups.flatMap((g) => g.items).find((i) => i.image_urls[0])?.image_urls[0]

  async function approveAll() {
    setBusy(true)
    setError(null)
    try {
      for (const i of planned) await onApprove(i.id)
      setAsk(null)
    } catch (e) {
      setError(friendlyContentError(e))
      setAsk(null)
    } finally {
      setBusy(false)
    }
  }

  return (
    <li className={`list-none rounded-2xl border bg-white ${open ? 'border-[#0f2340]/20 shadow-sm' : 'border-gray-200'}`} data-testid="campaign-card">
      <button type="button" onClick={onToggle} aria-expanded={open}
        className="min-h-[72px] w-full items-center gap-3 rounded-2xl p-2 pr-3 text-left active:bg-gray-50 [display:flex]">
        {cover ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={mediaUrl(cover)} alt="" loading="lazy" className="h-14 w-14 flex-none rounded-xl bg-gray-100 object-cover" />
        ) : (
          <span aria-hidden className="h-14 w-14 flex-none items-center justify-center rounded-xl bg-[#0f2340] text-xs font-bold text-[#f0b440] [display:flex]">Campaign</span>
        )}
        <span className="min-w-0 flex-1">
          <span className="block truncate text-[15px] font-semibold text-gray-900" data-testid="row-title">{title} · {plural(groups.length, 'post')}</span>
          <span className="mt-1 flex-wrap items-center gap-1.5 text-xs text-gray-600 [display:flex]">
            <TypeTag>Listing</TypeTag>
            <span className="whitespace-nowrap">Campaign</span>
            {plannedPosts > 0 ? <StatusPill tone="action">{plannedPosts} need your OK</StatusPill>
              : failed ? <StatusPill tone="bad">Not posted</StatusPill>
              : <StatusPill tone="info">Approved</StatusPill>}
          </span>
        </span>
        <span aria-hidden className={`text-gray-400 transition-transform ${open ? 'rotate-90' : ''}`}>›</span>
      </button>

      {open && (
        <div className="space-y-3 px-3 pb-3">
          {error && <ErrorBox message={error} />}
          {(planned.length > 0 || openItems.length > 0) && (
            <div className="gap-2 [display:flex]">
              {planned.length > 0 && (
                <Btn disabled={busy} className="!bg-[#0f2340]" onClick={() => setAsk('approve')}>Approve all {plannedPosts}</Btn>
              )}
              {openItems.length > 0 && (
                <Btn variant="danger" disabled={busy} onClick={() => setAsk('skip')}>Skip all {openPosts}</Btn>
              )}
            </div>
          )}
          <ul className="space-y-2 p-0">
            {groups.map((g) => (
              <ContentCard key={g.key} group={g} showType={false} open={inner === g.key} onToggle={() => setInner((k) => (k === g.key ? null : g.key))}
                onApprove={onApprove} onSkip={onSkip} {...rest} />
            ))}
          </ul>
        </div>
      )}

      {ask === 'approve' && (
        <ConfirmSheet title={`Approve all ${plural(plannedPosts, 'post')} of ${title}?`} confirmLabel={`Approve ${plannedPosts}`} busy={busy}
          onCancel={() => setAsk(null)} onConfirm={approveAll}>
          <p>Each goes out at its planned time, one a day, on Instagram and Facebook. Check Going out for the times.</p>
        </ConfirmSheet>
      )}
      {ask === 'skip' && (
        <ConfirmSheet title={`Skip all ${plural(openPosts, 'post')} of ${title}?`} confirmLabel={`Skip ${openPosts}`}
          onCancel={() => setAsk(null)} onConfirm={() => { setAsk(null); onSkip(openItems.map((i) => i.id)) }}>
          <p>None of them will be posted. You can undo for a few seconds, or send the campaign again from the listing.</p>
        </ConfirmSheet>
      )}
    </li>
  )
}
