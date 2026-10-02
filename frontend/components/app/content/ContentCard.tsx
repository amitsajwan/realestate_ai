'use client'
import React, { useState } from 'react'
import { Btn, Chip, ErrorBox } from '@/components/app/ui'
import { channelLabel, dueLabel, friendlyContentError, kindLabel, mediaUrl, statusLabel } from '@/lib/app/content'
import type { ContentItem } from '@/lib/app/content'
import { ReviewChip } from '../quality/ReviewChip'

export interface ContentCardProps {
  item: ContentItem
  onApprove: (id: string) => Promise<void>
  onSkip: (id: string) => Promise<void>
}

export function ContentCard({ item, onApprove, onSkip }: ContentCardProps) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const needsOk = item.status === 'planned'

  async function run(fn: () => Promise<void>) {
    setBusy(true)
    setError(null)
    try {
      await fn()
    } catch (e) {
      setError(friendlyContentError(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <li className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4" data-testid="content-card">
      <div className="flex flex-wrap items-center gap-2">
        <Chip tone={item.channel === 'instagram' ? 'purple' : 'blue'}>{channelLabel(item.channel)}</Chip>
        <Chip tone="gray">{kindLabel(item.kind)}</Chip>
        <Chip tone={needsOk ? 'amber' : 'green'}>{statusLabel(item.status)}</Chip>
        <span className="ml-auto text-xs text-gray-500">{dueLabel(item.due_at)}</span>
      </div>

      {item.image_urls.length > 0 && (
        <div className="-mx-1 flex snap-x snap-mandatory gap-2 overflow-x-auto px-1 pb-1" data-testid="carousel" aria-label="Post images">
          {item.image_urls.map((u, i) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              key={u + i}
              src={mediaUrl(u)}
              alt={`${item.slug} image ${i + 1} of ${item.image_urls.length}`}
              loading="lazy"
              className="h-72 w-auto max-w-none snap-center rounded-xl border border-gray-100 bg-gray-100"
            />
          ))}
        </div>
      )}
      {item.kind === 'reel' && (
        <div className="rounded-xl bg-gray-900 p-4 text-sm text-white" data-testid="reel-note">
          {item.video_url ? <video src={mediaUrl(item.video_url)} controls className="mx-auto max-h-80 rounded-lg" /> : 'Short video. It is made automatically about two hours before it goes out.'}
        </div>
      )}

      <p className="whitespace-pre-wrap text-sm text-gray-800" data-testid="caption">{item.caption}</p>
      {item.error && <p className="text-xs text-red-700">Last error: {item.error}</p>}
      {error && <ErrorBox message={error} />}

      {needsOk && item.kind !== 'reel' && item.image_urls.length > 0 && <ReviewChip kind="calendar" id={item.id} />}
      <div className="flex gap-2">
        {needsOk && (
          <Btn disabled={busy} onClick={() => run(() => onApprove(item.id))}>
            Approve
          </Btn>
        )}
        <Btn variant="danger" disabled={busy} onClick={() => run(() => onSkip(item.id))}>
          Skip
        </Btn>
      </div>
    </li>
  )
}
