'use client'
import React, { useEffect, useState } from 'react'
import { Btn, Chip, ErrorBox } from '@/components/app/ui'
import { channelLabel, countdown, dueLabel, friendlyContentError, kindLabel, mediaUrl, statusLabel } from '@/lib/app/content'
import type { ContentGroup, ContentItem } from '@/lib/app/content'
import { ReviewChip } from '../quality/ReviewChip'

export interface ContentCardProps {
  /** The Instagram and Facebook copies of one post; actions apply to every copy still open. */
  group: ContentGroup
  onApprove: (id: string) => Promise<void>
  onSkip: (id: string) => Promise<void>
  onPostNow: (id: string) => Promise<void>
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

function whenLine(item: ContentItem, now: number): string {
  if (item.status === 'planned') return `Planned for ${dueLabel(item.due_at)}. Approve it to post then, or Post now.`
  const left = countdown(item.due_at, now + 2 * 60_000)   // due within 2 minutes (or a Post now just tapped): it is going out
  return left ? `Goes out ${countdown(item.due_at, now)} (${dueLabel(item.due_at)})` : 'Posting now: it appears within a few minutes.'
}

export function ContentCard({ group, onApprove, onSkip, onPostNow }: ContentCardProps) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const now = useNow()
  const first = group.items[0]
  const open = group.items.filter((i) => OPEN.includes(i.status))
  const planned = open.filter((i) => i.status === 'planned')
  const dup = group.items.find((i) => i.duplicate_of)?.duplicate_of ?? null

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
    <li className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4" data-testid="content-card">
      <div className="flex flex-wrap items-center gap-2">
        {group.items.map((i) => (
          <Chip key={i.id} tone={i.channel === 'instagram' ? 'purple' : 'blue'}>{channelLabel(i.channel)}</Chip>
        ))}
        <Chip tone="gray">{kindLabel(first.kind)}</Chip>
        <Chip tone={planned.length ? 'amber' : 'green'}>{statusLabel(planned.length ? 'planned' : first.status)}</Chip>
      </div>

      <ul className="space-y-1 p-0 text-sm" data-testid="when">
        {group.items.map((i) => (
          <li key={i.id} className="list-none text-gray-700">
            <span className="font-semibold">{channelLabel(i.channel)}:</span> {whenLine(i, now)}
          </li>
        ))}
      </ul>

      {dup && (
        <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900" data-testid="duplicate">
          This repeats “{dup.slug}”, already posted{dup.published_at ? ` on ${dueLabel(dup.published_at)}` : ''}. It will be held back, not
          posted twice. Skip it, or change it first.
        </p>
      )}

      {first.image_urls.length > 0 && (
        <div className="-mx-1 flex snap-x snap-mandatory gap-2 overflow-x-auto px-1 pb-1" data-testid="carousel" aria-label="Post images">
          {first.image_urls.map((u, i) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              key={u + i}
              src={mediaUrl(u)}
              alt={`${first.slug} image ${i + 1} of ${first.image_urls.length}`}
              loading="lazy"
              className="h-72 w-auto max-w-none snap-center rounded-xl border border-gray-100 bg-gray-100"
            />
          ))}
        </div>
      )}
      {first.kind === 'reel' && (
        <div className="rounded-xl bg-gray-900 p-4 text-sm text-white" data-testid="reel-note">
          {first.video_url ? <video src={mediaUrl(first.video_url)} controls className="mx-auto max-h-80 rounded-lg" /> : 'Short video. It is made automatically about two hours before it goes out.'}
        </div>
      )}

      <p className="whitespace-pre-wrap text-sm text-gray-800" data-testid="caption">{first.caption}</p>
      {group.items.map((i) => i.error && <p key={i.id} className="text-xs text-red-700">{channelLabel(i.channel)} last error: {i.error}</p>)}
      {error && <ErrorBox message={error} />}

      {planned.length > 0 && first.kind !== 'reel' && first.image_urls.length > 0 && <ReviewChip kind="calendar" id={first.id} />}
      {open.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {planned.length > 0 && (
            <Btn disabled={busy} onClick={() => each(planned.map((i) => i.id), onApprove)}>
              Approve
            </Btn>
          )}
          {!dup && (
            <Btn variant="secondary" disabled={busy} onClick={() => each(open.map((i) => i.id), onPostNow)}>
              Post now
            </Btn>
          )}
          <Btn variant="danger" disabled={busy} onClick={() => each(open.map((i) => i.id), onSkip)}>
            Skip
          </Btn>
        </div>
      )}
    </li>
  )
}
