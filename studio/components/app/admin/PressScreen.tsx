'use client'
import React, { useEffect, useState } from 'react'
import { errorMessage } from '@/lib/app/client'
import { gmailComposeUrl, mailtoUrl, pressApi } from '@/lib/app/press'
import type { PressFact, PressPitch, PressStatus, PressSummary } from '@/lib/app/press'
import { useAsync } from '@/lib/app/useAsync'
import { Btn, ErrorBox, Spinner } from '../ui'

function Fact({ f }: { f: PressFact }) {
  return (
    <li data-testid="press-fact" className="rounded-xl border border-gray-200 bg-white p-3 text-sm">
      <p className="text-gray-900">{f.text}</p>
      <p className="mt-1 text-xs text-gray-500">{f.source} · as of {f.as_of}</p>
    </li>
  )
}

function Summary({ s }: { s: PressSummary }) {
  return (
    <dl data-testid="press-summary" className="grid grid-cols-3 gap-2 text-center">
      {[['Sent', s.sent], ['Replies', s.replied], ['Links won', s.links_won]].map(([label, n]) => (
        <div key={label as string} className="rounded-xl border border-gray-200 bg-white p-3">
          <dt className="text-xs text-gray-500">{label}</dt>
          <dd className="text-2xl font-extrabold text-[#102340]">{n}</dd>
        </div>
      ))}
    </dl>
  )
}

const STATUS_LABEL: Record<PressStatus, string> = { draft: 'Draft', sent: 'Sent', skipped: 'Skipped' }

function PitchCard({ pitch, onChange }: { pitch: PressPitch; onChange: (p: PressPitch) => void }) {
  const [subject, setSubject] = useState(pitch.subject)
  const [body, setBody] = useState(pitch.body)
  const [linkUrl, setLinkUrl] = useState(pitch.link_won_url ?? '')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const dirty = subject !== pitch.subject || body !== pitch.body

  async function save(patch: Parameters<typeof pressApi.patch>[1]) {
    setBusy(true)
    setError(null)
    try {
      const out = await pressApi.patch(pitch.id, patch)
      onChange(out)
      setSubject(out.subject)
      setBody(out.body)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <li data-testid="press-pitch" className="space-y-2 rounded-2xl border border-gray-200 bg-white p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <a href={pitch.article.url} target="_blank" rel="noreferrer" className="font-semibold text-[#102340] underline">
            {pitch.article.title || pitch.journalist.outlet}
          </a>
          <p className="text-xs text-gray-500">{pitch.journalist.outlet}{pitch.journalist.name ? ` · ${pitch.journalist.name}` : ''}</p>
        </div>
        <span data-testid="press-status" className="shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-xs font-semibold text-gray-700">
          {STATUS_LABEL[pitch.status]}
        </span>
      </div>

      {!pitch.email && (
        <p className="text-sm text-amber-700">
          Find the contact
          {pitch.journalist.contact_page && (
            <>
              {' – '}
              <a href={pitch.journalist.contact_page} target="_blank" rel="noreferrer" className="underline">outlet's contact page</a>
            </>
          )}
        </p>
      )}

      <label className="block text-xs font-semibold text-gray-600">
        Subject
        <input data-testid="press-subject" value={subject} onChange={(e) => setSubject(e.target.value)}
              className="mt-0.5 w-full rounded-lg border border-gray-300 p-2 text-sm text-gray-900" />
      </label>
      <label className="block text-xs font-semibold text-gray-600">
        Body
        <textarea data-testid="press-body" value={body} onChange={(e) => setBody(e.target.value)} rows={6}
                 className="mt-0.5 w-full rounded-lg border border-gray-300 p-2 text-sm text-gray-900" />
      </label>
      {dirty && (
        <Btn block={false} variant="secondary" disabled={busy} onClick={() => save({ subject, body })}>Save edits</Btn>
      )}

      <div className="flex flex-wrap gap-2">
        <a data-testid="press-gmail" href={gmailComposeUrl({ ...pitch, subject, body })} target="_blank" rel="noreferrer"
          className="rounded-lg bg-[#102340] px-3 py-2 text-sm font-semibold text-white">Open in Gmail</a>
        <a data-testid="press-mailto" href={mailtoUrl({ ...pitch, subject, body })}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-semibold text-gray-700">Email app</a>
        <Btn block={false} variant="secondary" disabled={busy} onClick={() => save({ status: 'sent' })}>Mark sent</Btn>
        <Btn block={false} variant="secondary" disabled={busy} onClick={() => save({ status: 'skipped' })}>Skip</Btn>
        <Btn block={false} variant="secondary" disabled={busy} onClick={() => save({ replied: !pitch.replied })}>
          {pitch.replied ? 'Replied ✓' : 'Replied?'}
        </Btn>
      </div>
      <div className="flex gap-2">
        <input data-testid="press-link-input" value={linkUrl} onChange={(e) => setLinkUrl(e.target.value)} placeholder="Link they published"
              className="flex-1 rounded-lg border border-gray-300 p-2 text-sm text-gray-900" />
        <Btn block={false} variant="secondary" disabled={busy} onClick={() => save({ link_won_url: linkUrl || null })}>Got a link</Btn>
      </div>
      {pitch.link_won_url && <a href={pitch.link_won_url} target="_blank" rel="noreferrer" className="block text-sm text-green-700 underline">{pitch.link_won_url}</a>}
      {error && <ErrorBox message={error} />}
    </li>
  )
}

export function PressScreen() {
  const { data, error, loading, reload } = useAsync(async () => {
    const [story, pitches, summary] = await Promise.all([pressApi.story(), pressApi.pitches(), pressApi.summary()])
    return { story, pitches, summary }
  })
  const [pitches, setPitches] = useState<PressPitch[] | null>(null)
  useEffect(() => {
    if (data) setPitches(data.pitches)
  }, [data])

  if (loading) return <Spinner label="Loading Press" />
  if (error || !data) return <ErrorBox message={error ?? 'Could not load Press'} onRetry={reload} />

  function onPitchChange(updated: PressPitch) {
    setPitches((prev) => (prev ?? []).map((p) => (p.id === updated.id ? updated : p)))
  }

  return (
    <div className="space-y-6 p-4" data-testid="press-screen">
      <h1 className="text-xl font-extrabold text-[#102340]">Press</h1>
      <Summary s={data.summary} />
      <section aria-labelledby="press-story" className="space-y-2">
        <h2 id="press-story" className="border-b-4 border-[#F0B13B] pb-0.5 text-lg font-extrabold text-[#102340]">
          This month's story{data.story.month ? ` (${data.story.month})` : ''}
        </h2>
        {data.story.headline_facts.length === 0 ? (
          <p className="text-sm text-gray-600">No story yet this month.</p>
        ) : (
          <ul className="space-y-2">{data.story.headline_facts.map((f, i) => <Fact key={i} f={f} />)}</ul>
        )}
      </section>
      <section aria-labelledby="press-drafts" className="space-y-2">
        <h2 id="press-drafts" className="border-b-4 border-[#F0B13B] pb-0.5 text-lg font-extrabold text-[#102340]">Drafts</h2>
        {(pitches ?? []).length === 0 ? (
          <p className="text-sm text-gray-600">No drafts yet this month.</p>
        ) : (
          <ul className="space-y-3">{(pitches ?? []).map((p) => <PitchCard key={p.id} pitch={p} onChange={onPitchChange} />)}</ul>
        )}
      </section>
    </div>
  )
}
