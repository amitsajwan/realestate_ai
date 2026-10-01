'use client'
import React from 'react'
import type { NewsroomCard, NewsroomChannel } from '@/lib/app/newsroom'

export interface PostPreviewProps {
  card: NewsroomCard | null
  channels: NewsroomChannel[]
  captions: Record<string, string>
  problems: Record<string, string[]>
  dryRun: boolean
  updating?: boolean
  title: string
}

/** What the owner is about to publish: the card as it will look, the channels it goes to, and the exact final caption of each channel. */
export function PostPreview({ card, channels, captions, problems, dryRun, updating = false, title }: PostPreviewProps) {
  if (!card && channels.length === 0 && Object.keys(captions).length === 0) return null
  return (
    <section aria-label="What will be posted" data-testid="post-preview" className="space-y-3 rounded-xl border border-blue-100 bg-blue-50/40 p-3">
      <h3 className="text-sm font-bold uppercase tracking-wide text-blue-900">What will be posted</h3>

      {channels.length > 0 && (
        <ul className="flex list-none flex-wrap gap-2 p-0" data-testid="preview-channels" aria-label="Channels">
          {channels.map((c) => (
            <li key={c.id} className="rounded-full bg-white px-3 py-1 text-sm font-semibold text-blue-900 ring-1 ring-blue-200">
              {c.label}{c.post && <span className="font-normal text-gray-600">: {c.post}</span>}
            </li>
          ))}
        </ul>
      )}
      {dryRun && <p className="rounded-lg bg-amber-50 p-2 text-xs font-semibold text-amber-900" data-testid="preview-dry-run">Test mode: approving will not post anything for real.</p>}

      {card && (
        <div className="flex gap-3 overflow-x-auto pb-1" data-testid="preview-card">
          {card.ig && (
            <a href={card.ig} target="_blank" rel="noopener noreferrer" className="block flex-none">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={card.ig} alt={`Instagram card: ${title}`} width={160} height={200} className="h-[200px] w-[160px] rounded-lg border border-gray-200 object-cover" />
              <span className="mt-1 block text-center text-xs text-gray-600">Instagram{card.slides.length > 1 ? ` (${card.slides.length} slides)` : ''}</span>
            </a>
          )}
          <a href={card.fb} target="_blank" rel="noopener noreferrer" className="block flex-none">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={card.fb} alt={`Facebook card: ${title}`} width={200} height={200} className="h-[160px] w-[160px] rounded-lg border border-gray-200 object-cover" />
            <span className="mt-1 block text-center text-xs text-gray-600">Facebook</span>
          </a>
        </div>
      )}
      {!card && channels.length > 0 && <p className="text-xs text-gray-600" data-testid="preview-no-card">The card is drawn when this is published.</p>}

      {channels.map((c) => {
        const text = captions[c.id]
        const bad = problems[c.id] ?? []
        if (!text) return null
        return (
          <div key={c.id}>
            <p className="mb-1 flex items-center justify-between text-sm font-medium text-gray-700">
              <span>{c.label} caption</span>
              {updating && <span className="text-xs font-normal text-gray-500">Updating...</span>}
            </p>
            <div data-testid={`caption-${c.id}`} className="whitespace-pre-wrap break-words rounded-lg border border-gray-200 bg-white p-3 text-sm text-gray-900">{text}</div>
            {bad.length > 0 && (
              <ul role="alert" data-testid={`caption-problems-${c.id}`} className="mt-1 list-disc space-y-0.5 rounded-lg bg-red-50 p-2 pl-6 text-sm text-red-800">
                {bad.map((p, i) => <li key={i}>{p}</li>)}
              </ul>
            )}
          </div>
        )
      })}
    </section>
  )
}
