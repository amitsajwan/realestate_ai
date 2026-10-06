'use client'
import React, { useEffect, useState } from 'react'
import { Btn, ErrorBox } from '@/components/app/ui'
import { ConfirmSheet, LinkOut, StatusPill } from '@/components/app/list'
import type { PillTone } from '@/components/app/list'
import { channelLabel, countdown, dueLabel, friendlyContentError, kindLabel, mediaUrl } from '@/lib/app/content'
import type { ContentGroup, ContentItem } from '@/lib/app/content'
import { ReviewChip } from '../quality/ReviewChip'

export interface ContentCardProps {
  /** The Instagram and Facebook copies of one post; actions apply to every copy still open. */
  group: ContentGroup
  open?: boolean
  onToggle?: () => void
  onApprove: (id: string) => Promise<void>
  /** The page wraps Skip in an 8-second Undo. */
  onSkip: (ids: string[]) => void
  onPostNow: (id: string) => Promise<void>
  onUnapprove?: (id: string) => Promise<void>
  onRetry?: (id: string) => Promise<void>
}

const OPEN = ['planned', 'approved', 'scheduled']

/** Re-render every 30 s so the countdown stays true while the screen is open. */
function useNow(): number {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 30_000)
    return () => clearInterval(t)
  }, [])
  return now
}

export function title(item: ContentItem): string {
  return (item.caption.split('\n').find((l) => l.trim()) || item.slug).replace(/\s+/g, ' ').trim()
}

/** The one status a channel copy is in, in plain words, with its tone. */
export function channelStatus(i: ContentItem, now: number): { tone: PillTone; text: string } {
  if (i.status === 'planned') return { tone: 'action', text: 'Needs your OK' }
  if (i.status === 'published') return { tone: 'ok', text: 'Posted' }
  if (i.status === 'failed') return { tone: 'bad', text: 'Not posted' }
  if (i.status === 'removed') return { tone: 'muted', text: 'Deleted' }
  if (i.status === 'skipped') return { tone: 'muted', text: 'Skipped' }
  const left = countdown(i.due_at, now + 2 * 60_000)
  return left ? { tone: 'info', text: `Goes out ${countdown(i.due_at, now)}` } : { tone: 'info', text: 'Posting now' }
}

function ChannelIcon({ channel }: { channel: ContentItem['channel'] }) {
  return (
    <span aria-label={channelLabel(channel)} title={channelLabel(channel)}
      className={`inline-flex h-5 min-w-[20px] items-center justify-center rounded px-1 text-[10px] font-bold text-white ${channel === 'instagram' ? 'bg-purple-600' : 'bg-blue-600'}`}>
      {channel === 'instagram' ? 'IG' : 'FB'}
    </span>
  )
}

function Thumb({ item }: { item: ContentItem }) {
  const src = item.image_urls[0]
  if (src) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={mediaUrl(src)} alt="" loading="lazy" className="h-14 w-14 flex-none rounded-xl bg-gray-100 object-cover" />
  }
  return <span aria-hidden className="h-14 w-14 flex-none items-center justify-center rounded-xl bg-[#0f2340] text-xs font-bold text-[#f0b440] [display:flex]">{item.kind === 'reel' ? 'Reel' : 'Post'}</span>
}

export function ContentCard({ group, open = false, onToggle, onApprove, onSkip, onPostNow, onUnapprove, onRetry }: ContentCardProps) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [confirm, setConfirm] = useState(false)
  const [more, setMore] = useState(false)
  const now = useNow()
  const first = group.items[0]
  const openItems = group.items.filter((i) => OPEN.includes(i.status))
  const planned = openItems.filter((i) => i.status === 'planned')
  const approved = openItems.filter((i) => i.status !== 'planned')
  const failed = group.items.filter((i) => i.status === 'failed')
  const dup = group.items.find((i) => i.duplicate_of)?.duplicate_of ?? null
  const head = channelStatus(group.items.find((i) => i.status === 'planned') ?? first, now)

  async function each(ids: string[], fn: (id: string) => Promise<void>) {
    setBusy(true)
    setError(null)
    try {
      for (const id of ids) await fn(id)
    } catch (e) {
      setError(friendlyContentError(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <li className={`list-none rounded-2xl border bg-white ${open ? 'border-[#0f2340]/20 shadow-sm' : 'border-gray-200'}`} data-testid="content-card">
      <button type="button" onClick={onToggle} aria-expanded={open}
        className="min-h-[72px] w-full items-center gap-3 rounded-2xl p-2 pr-3 text-left active:bg-gray-50 [display:flex]">
        <Thumb item={first} />
        <span className="min-w-0 flex-1">
          <span className="block truncate text-[15px] font-semibold text-gray-900" data-testid="row-title">{title(first)}</span>
          <span className="mt-1 items-center gap-1.5 text-xs text-gray-600 tabular-nums [display:flex]">
            {group.items.map((i) => <ChannelIcon key={i.id} channel={i.channel} />)}
            <span className="text-gray-400">·</span>
            <span>{kindLabel(first.kind)}</span>
            <StatusPill tone={head.tone}>{head.text}</StatusPill>
          </span>
        </span>
        <span aria-hidden className={`text-gray-400 transition-transform ${open ? 'rotate-90' : ''}`}>›</span>
      </button>

      {open && (
        <div className="space-y-3 px-4 pb-4">
          <ul className="space-y-1 p-0 text-sm" data-testid="when">
            {group.items.map((i) => {
              const st = channelStatus(i, now)
              return (
                <li key={i.id} className="list-none flex-wrap items-center gap-2 [display:flex]">
                  <ChannelIcon channel={i.channel} />
                  <StatusPill tone={st.tone}>{st.text}</StatusPill>
                  <time className="text-gray-600" dateTime={i.published_at || i.due_at}>
                    {i.status === 'published' && i.published_at ? dueLabel(i.published_at) : i.status === 'planned' ? `planned ${dueLabel(i.due_at)}` : dueLabel(i.due_at)}
                  </time>
                  {i.permalink && <LinkOut href={i.permalink} label={`on ${channelLabel(i.channel)}`}>{channelLabel(i.channel)}</LinkOut>}
                  {i.status === 'failed' && <span className="w-full text-red-700">{i.error || i.note}</span>}
                </li>
              )
            })}
          </ul>

          {dup && (
            <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900" data-testid="duplicate">
              This repeats “{dup.slug}”, already posted{dup.published_at ? ` on ${dueLabel(dup.published_at)}` : ''}. It will be held back, not posted twice. Skip it, or change it first.
            </p>
          )}

          {first.image_urls.length > 0 && (
            <div className="-mx-1 snap-x snap-mandatory gap-2 overflow-x-auto px-1 pb-1 [display:flex]" data-testid="carousel" aria-label="Post images">
              {first.image_urls.map((u, i) => (
                // eslint-disable-next-line @next/next/no-img-element
                <img key={u + i} src={mediaUrl(u)} alt={`${first.slug} image ${i + 1} of ${first.image_urls.length}`} loading="lazy"
                  className="h-56 w-auto max-w-none snap-center rounded-xl border border-gray-100 bg-gray-100" />
              ))}
            </div>
          )}
          {first.kind === 'reel' && (
            <div className="rounded-xl bg-gray-900 p-4 text-sm text-white" data-testid="reel-note">
              {first.video_url ? <video src={mediaUrl(first.video_url)} controls className="mx-auto max-h-80 rounded-lg" /> : 'Short video. It is made automatically about two hours before it goes out.'}
            </div>
          )}

          <div>
            <p className={`whitespace-pre-wrap text-sm text-gray-800 ${more ? '' : 'line-clamp-4'}`} data-testid="caption">{first.caption}</p>
            {first.caption.split('\n').length > 4 || first.caption.length > 240 ? (
              <button type="button" onClick={() => setMore((m) => !m)} className="min-h-[44px] text-sm font-semibold text-[#0f2340] underline">
                {more ? 'Less' : 'More'}
              </button>
            ) : null}
          </div>
          {error && <ErrorBox message={error} />}

          {planned.length > 0 && first.kind !== 'reel' && first.image_urls.length > 0 && <ReviewChip kind="calendar" id={first.id} />}
          <div className="space-y-2">
            {planned.length > 0 && (
              <Btn disabled={busy} className="!bg-[#0f2340]" onClick={() => each(planned.map((i) => i.id), onApprove)}>Approve</Btn>
            )}
            {failed.length > 0 && onRetry && (
              <Btn disabled={busy} className="!bg-[#0f2340]" onClick={() => each(failed.map((i) => i.id), onRetry)}>Retry</Btn>
            )}
            <div className="gap-2 [display:flex]">
              {openItems.length > 0 && !dup && (
                <Btn variant="secondary" disabled={busy} onClick={() => setConfirm(true)}>Post now…</Btn>
              )}
              {approved.length > 0 && onUnapprove && (
                <Btn variant="ghost" disabled={busy} onClick={() => each(approved.map((i) => i.id), onUnapprove)}>Back to To approve</Btn>
              )}
              {openItems.length > 0 && (
                <Btn variant="danger" disabled={busy} onClick={() => onSkip(openItems.map((i) => i.id))}>Skip</Btn>
              )}
            </div>
          </div>
        </div>
      )}

      {confirm && (
        <ConfirmSheet title={`Post now on ${openItems.map((i) => channelLabel(i.channel)).join(' and ')}?`} confirmLabel="Yes, post now" busy={busy}
          onCancel={() => setConfirm(false)}
          onConfirm={async () => { await each(openItems.map((i) => i.id), onPostNow); setConfirm(false) }}>
          <p>“{title(first).slice(0, 80)}” goes out within about 10 minutes. This cannot be undone from here.</p>
          <p>If another post on the same channel is going out, this one follows about 10 minutes after it.</p>
        </ConfirmSheet>
      )}
    </li>
  )
}
