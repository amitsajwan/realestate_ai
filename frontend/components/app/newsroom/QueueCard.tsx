'use client'
import React, { useEffect, useState } from 'react'
import { Btn, Chip, ErrorBox } from '@/components/app/ui'
import { StatusPill } from '@/components/app/list'
import type { PillTone } from '@/components/app/list'
import { ageLabel, friendlyNewsroomError, pillarLabel, whenToIso } from '@/lib/app/newsroom'
import type { ApproveBody, NewsroomItem, NewsroomPreview } from '@/lib/app/newsroom'
import { CheckResult } from './CheckResult'
import { FactsList } from './FactsList'
import { PostPreview } from './PostPreview'
import { ReviewChip } from '../quality/ReviewChip'

export interface QueueCardProps {
  item: NewsroomItem
  onApprove: (id: string, body: ApproveBody) => Promise<void>
  onReject: (id: string, reason?: string) => Promise<void>
  /** Optional: the final captions for edited text, without saving (the owner sees what will really be sent). */
  onPreview?: (id: string, text: string) => Promise<NewsroomPreview>
  /** Compact row until opened; the page keeps one open at a time. */
  open?: boolean
  onToggle?: () => void
}

/** The one check result a row shows before it is opened. */
export function checkStatus(item: Pick<NewsroomItem, 'check' | 'captionProblems'>): { tone: PillTone; text: string } {
  if (!item.check.ok) return { tone: 'bad', text: 'Needs a fix' }
  if (Object.values(item.captionProblems).some((p) => p.length > 0)) return { tone: 'bad', text: 'Caption needs a fix' }
  return { tone: 'ok', text: 'Checks passed' }
}

/** Area chips shared by the queue rows and the list rows. */
export function AreaChips({ areas }: { areas: string[] }) {
  if (areas.length === 0) return null
  return <>{areas.map((a) => <Chip key={a} tone="amber" className="!px-2 !py-0.5">{a}</Chip>)}</>
}

const PREVIEW_DELAY_MS = 600

export function QueueCard({ item, onApprove, onReject, onPreview, open = false, onToggle }: QueueCardProps) {
  const [text, setText] = useState(item.draft)
  const [editing, setEditing] = useState(false)
  const [live, setLive] = useState<{ captions: Record<string, string>; problems: Record<string, string[]> } | null>(null)
  const [updating, setUpdating] = useState(false)
  const [when, setWhen] = useState('')
  const [scheduling, setScheduling] = useState(false)
  const [rejecting, setRejecting] = useState(false)
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const edited = text !== item.draft
  const fieldId = `draft-${item.id}`

  // When the owner edits the text, ask the server for the captions that edit would really produce (and their checks), after a short pause.
  useEffect(() => {
    if (!edited || !onPreview) {
      setLive(null)
      setUpdating(false)
      return
    }
    let stale = false
    setUpdating(true)
    const t = setTimeout(() => {
      onPreview(item.id, text)
        .then((p) => { if (!stale) setLive({ captions: p.captions, problems: p.captionProblems }) })
        .catch(() => { if (!stale) setLive(null) })
        .finally(() => { if (!stale) setUpdating(false) })
    }, PREVIEW_DELAY_MS)
    return () => { stale = true; clearTimeout(t) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text, edited])
  const captions = live?.captions ?? item.captions
  const problems = live?.problems ?? item.captionProblems
  const captionsBlocked = Object.values(problems).some((p) => p.length > 0)

  async function run(fn: () => Promise<void>) {
    setBusy(true)
    setError(null)
    try {
      await fn()
    } catch (e) {
      setError(friendlyNewsroomError(e))
      setBusy(false)
    }
  }

  const approve = () => {
    const body: ApproveBody = {}
    if (edited) body.text = text
    const iso = scheduling ? whenToIso(when) : undefined
    if (iso) body.when = iso
    return run(() => onApprove(item.id, body))
  }
  const reject = () => run(() => onReject(item.id, reason.trim() || undefined))

  const head = checkStatus(item)

  return (
    <li className={`list-none rounded-2xl border bg-white ${open ? 'border-[#0f2340]/20 shadow-sm' : 'border-gray-200'}`} data-testid="queue-card">
      <button type="button" onClick={onToggle} aria-expanded={open}
        className="min-h-[72px] w-full items-center gap-3 rounded-2xl p-3 text-left active:bg-gray-50 [display:flex]">
        <span className="min-w-0 flex-1">
          <span className="block truncate text-[15px] font-semibold text-gray-900" data-testid="row-title">{item.title}</span>
          <span className="mt-1 flex-wrap items-center gap-1.5 text-xs text-gray-600 [display:flex]">
            <AreaChips areas={item.areas} />
            <span>{ageLabel(item.age_days)}</span>
            <StatusPill tone={head.tone}>{head.text}</StatusPill>
          </span>
        </span>
        <span aria-hidden className={`text-gray-400 transition-transform ${open ? 'rotate-90' : ''}`}>›</span>
      </button>

      {open && (
        <div className="space-y-3 px-4 pb-4">
          <div className="flex-wrap items-center gap-2 [display:flex]">
            <Chip tone="blue">{pillarLabel(item.pillar)}</Chip>
          </div>
          <h2 className="text-lg font-bold leading-snug text-blue-900">{item.title}</h2>

          {editing ? (
            <div>
              <label htmlFor={fieldId} className="mb-1 items-center justify-between text-sm font-medium text-gray-700 [display:flex]">
                <span>Post text</span>
                {edited && <span className="text-xs font-semibold text-amber-700">Edited, will be re-checked</span>}
              </label>
              <textarea
                id={fieldId}
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={6}
                autoFocus
                className="w-full rounded-xl border border-gray-300 bg-white p-3 text-base text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              />
            </div>
          ) : (
            <div>
              <p className="whitespace-pre-wrap break-words text-sm text-gray-800" data-testid="draft-text">{text}</p>
              <button type="button" onClick={() => setEditing(true)} className="min-h-[44px] text-sm font-semibold text-[#0f2340] underline">Edit text</button>
            </div>
          )}

          <CheckResult check={item.check} />
          <PostPreview card={item.card} channels={item.channels} captions={captions} problems={problems} dryRun={item.dryRun} updating={updating} title={item.title} />
          {captionsBlocked && <p className="text-sm font-semibold text-red-800" data-testid="approve-blocked">Fix the text so every caption passes the checks, then approve.</p>}
          <FactsList facts={item.facts} />

          {item.sources.length > 0 && (
            <p className="text-sm text-gray-600">
              Sources:{' '}
              {item.sources.map((s, i) => (
                <span key={i}>
                  {i > 0 && ', '}
                  {s.url ? (
                    <a href={s.url} target="_blank" rel="noopener noreferrer" className="inline-flex min-h-[44px] items-center font-semibold text-blue-700 underline">{s.name}</a>
                  ) : (
                    <span className="font-semibold">{s.name}</span>
                  )}
                </span>
              ))}
            </p>
          )}

          {scheduling && (
            <div>
              <label htmlFor={`when-${item.id}`} className="mb-1 block text-sm font-medium text-gray-700">Post at (leave empty for the next slot)</label>
              <input
                id={`when-${item.id}`}
                type="datetime-local"
                value={when}
                onChange={(e) => setWhen(e.target.value)}
                className="w-full min-h-[52px] rounded-xl border border-gray-300 bg-white px-4 text-base focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              />
            </div>
          )}
          {rejecting && (
            <div>
              <label htmlFor={`reason-${item.id}`} className="mb-1 block text-sm font-medium text-gray-700">Reason (optional)</label>
              <input
                id={`reason-${item.id}`}
                type="text"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="For example: old news"
                className="w-full min-h-[52px] rounded-xl border border-gray-300 bg-white px-4 text-base focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              />
            </div>
          )}
          {error && <ErrorBox message={error} />}

          {rejecting ? (
            <div className="gap-2 [display:flex]">
              <Btn variant="danger" onClick={reject} disabled={busy}>{busy ? 'Rejecting...' : 'Confirm reject'}</Btn>
              <Btn variant="ghost" onClick={() => setRejecting(false)} disabled={busy}>Cancel</Btn>
            </div>
          ) : (
            <div className="space-y-2">
              <ReviewChip kind="news" id={item.id} />
              <Btn onClick={approve} disabled={busy || !text.trim() || captionsBlocked} className="!bg-blue-900 active:!bg-blue-950 disabled:!bg-blue-300">
                {busy ? 'Approving...' : scheduling ? 'Approve and schedule' : 'Approve'}
              </Btn>
              <div className="gap-2 [display:flex]">
                <Btn variant="secondary" onClick={() => setScheduling((s) => !s)} disabled={busy}>{scheduling ? 'Use next slot' : 'Pick a time'}</Btn>
                <Btn variant="danger" onClick={() => setRejecting(true)} disabled={busy}>Reject</Btn>
              </div>
            </div>
          )}
        </div>
      )}
    </li>
  )
}
