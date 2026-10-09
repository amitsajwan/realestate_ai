'use client'
import React, { useState } from 'react'
import { errorMessage } from '@/lib/app/client'
import { timeAgo } from '@/lib/app/format'
import { radarApi } from '@/lib/app/radar'
import type { RadarSignal, SkipReason } from '@/lib/app/radar'
import { useAsync } from '@/lib/app/useAsync'
import { Btn, ErrorBox, Spinner } from '../ui'

const SKIPS: { key: SkipReason; label: string }[] = [
  { key: 'broker', label: 'Broker' },
  { key: 'not_buyer', label: 'Not a buyer' },
  { key: 'wrong_area', label: 'Wrong area' },
  { key: 'already_answered', label: 'Already answered' },
  { key: 'old', label: 'Too old' },
]

const SOURCE: Record<string, string> = { youtube: 'YouTube', manual: 'Pasted', instagram: 'Instagram', reddit: 'Reddit' }

function SignalCard({ s, onDone }: { s: RadarSignal; onDone: (id: string) => void }) {
  const [reply, setReply] = useState(s.draft ?? '')
  const [copied, setCopied] = useState(false)
  const [skipping, setSkipping] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function copyAndOpen() {
    try {
      await navigator.clipboard.writeText(reply)
      setCopied(true)
    } catch {
      setCopied(false)
    }
    window.open(s.url, '_blank', 'noopener')
  }

  async function mark(label: 'sent' | 'skipped', reason?: SkipReason) {
    setError(null)
    try {
      await radarApi.label(s.id, label, reason, label === 'sent' && reply !== s.draft ? reply : undefined)
      onDone(s.id)
    } catch (e) {
      setError(errorMessage(e))
    }
  }

  const pct = s.score != null ? Math.round(s.score * 100) : null
  return (
    <li data-testid="radar-signal" className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs text-gray-500">
            {SOURCE[s.source] ?? s.source}
            {s.author ? ` · ${s.author}` : ''}
            {s.posted_at ? ` · ${timeAgo(s.posted_at)}` : ''}
          </p>
          {s.context && <p className="truncate text-xs text-gray-500">on “{s.context}”</p>}
        </div>
        {pct != null && <span className="shrink-0 rounded-full bg-[#102340] px-2 py-0.5 text-xs font-bold text-[#F0B13B]">{pct}</span>}
      </div>
      <p className="whitespace-pre-wrap text-gray-900">{s.text}</p>
      {s.why && s.why.length > 0 && <p className="text-xs text-gray-600">{s.why.join(' · ')}</p>}
      <label className="block">
        <span className="text-xs font-semibold text-gray-700">Reply (edit before sending)</span>
        <textarea
          value={reply}
          onChange={(e) => setReply(e.target.value)}
          rows={4}
          className="mt-1 w-full rounded-xl border border-gray-300 bg-white p-2 text-sm text-gray-900"
        />
      </label>
      {error && <ErrorBox message={error} />}
      <div className="flex flex-wrap gap-2">
        <Btn block={false} onClick={copyAndOpen}>{copied ? 'Copied, opening…' : 'Copy reply & open'}</Btn>
        <Btn block={false} variant="secondary" onClick={() => mark('sent')}>Mark sent</Btn>
        <Btn block={false} variant="secondary" onClick={() => setSkipping((v) => !v)}>Skip</Btn>
      </div>
      {skipping && (
        <div className="flex flex-wrap gap-2">
          {SKIPS.map((k) => (
            <button key={k.key} type="button" onClick={() => mark('skipped', k.key)}
              className="rounded-full border border-gray-300 px-3 py-1 text-sm text-gray-700 active:bg-gray-100">
              {k.label}
            </button>
          ))}
        </div>
      )}
    </li>
  )
}

function PasteBox({ onAdded }: { onAdded: (s: RadarSignal) => void }) {
  const [url, setUrl] = useState('')
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit() {
    setBusy(true)
    setError(null)
    try {
      onAdded(await radarApi.manual(url.trim(), text.trim()))
      setUrl('')
      setText('')
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <details className="rounded-2xl border border-gray-200 bg-white p-4">
      <summary className="cursor-pointer font-semibold text-[#102340]">Paste a post (Facebook group, WhatsApp…)</summary>
      <div className="mt-3 space-y-2">
        <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="Link to the post"
          className="w-full rounded-xl border border-gray-300 bg-white p-2 text-sm text-gray-900" />
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={3} placeholder="What they wrote"
          className="w-full rounded-xl border border-gray-300 bg-white p-2 text-sm text-gray-900" />
        {error && <ErrorBox message={error} />}
        <Btn block={false} disabled={busy || !url.trim() || text.trim().length < 3} onClick={submit}>
          {busy ? 'Reading…' : 'Find match & draft reply'}
        </Btn>
      </div>
    </details>
  )
}

export function RadarScreen() {
  const { data, error, loading, reload } = useAsync(() => radarApi.signals(), [])
  const [done, setDone] = useState<Set<string>>(new Set())
  const [added, setAdded] = useState<RadarSignal[]>([])
  const items = [...added, ...(data ?? [])].filter((s) => !done.has(s.id))

  return (
    <main className="mx-auto max-w-2xl space-y-4 px-4 py-6">
      <header>
        <h1 className="text-2xl font-extrabold text-[#102340]">Buyer radar</h1>
        <p className="text-sm text-gray-600">People asking about homes in Pune, best first. Reply as a person, then mark it.</p>
      </header>
      <PasteBox onAdded={(s) => setAdded((a) => [s, ...a])} />
      {loading && <Spinner label="Loading…" />}
      {error && <ErrorBox message={error} onRetry={reload} />}
      {!loading && !error && items.length === 0 && (
        <p className="rounded-2xl border border-dashed border-gray-300 p-6 text-center text-gray-600">
          Nothing waiting. New questions are checked every 2 hours.
        </p>
      )}
      <ul className="space-y-3">
        {items.map((s) => (
          <SignalCard key={s.id} s={s} onDone={(id) => setDone((d) => new Set(d).add(id))} />
        ))}
      </ul>
    </main>
  )
}
