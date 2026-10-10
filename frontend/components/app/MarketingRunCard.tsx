'use client'
import Link from 'next/link'
import React, { useCallback, useEffect, useRef, useState } from 'react'
import { api, errorMessage } from '@/lib/app/client'
import { t } from '@/lib/app/strings'
import type { CampaignResult, DraftLanguage, MarketingRun, RunQuestion } from '@/lib/app/types'
import { BoostStep } from './BoostStep'
import { CampaignPostEditor } from './CampaignPostEditor'
import { RunFileUpload } from './RunFileUpload'
import { Btn, ErrorBox } from './ui'

const POLL_MS = 3000
const RUNNING: MarketingRun['status'][] = ['queued', 'facts', 'posts']

type StepState = 'waiting' | 'working' | 'done' | 'failed'

const ORDER = ['facts', 'plan', 'content', 'design', 'reels'] as const

/** Discovery, Facts, Plan, Content, Design: each step's state from where the run is. Discovery and facts share the job's
 *  'facts' step; questions keep discovery open. Older runs (no plan saved) show plan, content and design together. */
function stepStates(run: MarketingRun | null): StepState[] {
  if (!run) return ['waiting', 'waiting', 'waiting', 'waiting', 'waiting']
  if (run.status === 'done') return ['done', 'done', 'done', 'done', 'done']
  const factsDone = !!run.facts_done_at
  const at = run.status === 'posts' ? Math.max(1, ORDER.indexOf((run.step || 'plan') as (typeof ORDER)[number])) : 0
  const s: StepState[] = [0, 1, 2, 3, 4].map((i) => {
    if (i < 2) return factsDone ? 'done' : 'working'
    return i - 1 < at ? 'done' : i - 1 === at ? 'working' : 'waiting'
  })
  if (run.status === 'asking') s[0] = 'working'
  if (run.status === 'posts' && at === 1) s[2] = 'working'
  if (run.status === 'failed') {
    const i = s.findIndex((x) => x === 'working')
    if (i >= 0) s[i] = 'failed'
    else if (!factsDone) s[0] = 'failed'
  }
  return s
}

const angleName = (a: string) => (a.charAt(0).toUpperCase() + a.slice(1)).replace(/_/g, ' ')

/** "See more" under a step: closed by default so the five steps stay a short list. */
function More({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <details className="mt-1 text-sm">
      <summary className="cursor-pointer font-semibold text-blue-700">{label}</summary>
      <div className="mt-2">{children}</div>
    </details>
  )
}

function Step({ n, title, state, children }: { n: number; title: string; state: StepState; children?: React.ReactNode }) {
  const badge = {
    waiting: 'bg-gray-200 text-gray-600',
    working: 'bg-blue-600 text-white animate-pulse',
    done: 'bg-emerald-600 text-white',
    failed: 'bg-red-600 text-white',
  }[state]
  const label = { waiting: t('stepWaiting'), working: t('stepWorking'), done: t('stepDone'), failed: t('runFailed') }[state]
  return (
    <li className="flex gap-3">
      <span aria-hidden className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-sm font-bold ${badge}`}>
        {state === 'done' ? '✓' : n}
      </span>
      <div className="min-w-0 flex-1">
        <p className="font-semibold text-gray-900">
          {title} <span className="text-sm font-normal text-gray-500">· {label}</span>
        </p>
        {children}
      </div>
    </li>
  )
}

/** "Start marketing", one page in step order: 1 checks the project facts (and asks what it cannot work out), 2 makes the posts,
 *  3 shows each post in the approval calendar, 4 the leads each post brought. Posts are drafts: publishing needs approval. */
const POST_LANGS: Array<{ key: DraftLanguage; label: 'langEnglish' | 'langMarathi' | 'langHindi' }> = [
  { key: 'en', label: 'langEnglish' },
  { key: 'mr', label: 'langMarathi' },
  { key: 'hi', label: 'langHindi' },
]

/** Which language the posts are made in (cards and captions). */
function LanguagePicker({ value, onChange }: { value: DraftLanguage; onChange: (l: DraftLanguage) => void }) {
  return (
    <div className="flex flex-wrap items-center gap-2" role="radiogroup" aria-label={t('postsLanguage')}>
      <span className="text-sm text-gray-600">{t('postsLanguage')}</span>
      {POST_LANGS.map((l) => (
        <button
          key={l.key}
          type="button"
          role="radio"
          aria-checked={value === l.key}
          onClick={() => onChange(l.key)}
          className={`min-h-[44px] rounded-full border px-4 text-sm font-semibold ${
            value === l.key ? 'border-blue-600 bg-blue-600 text-white' : 'border-gray-300 bg-white text-gray-800'
          }`}
        >
          {t(l.label)}
        </button>
      ))}
    </div>
  )
}

/** What Start marketing read from the listing's project files: the builder's claims, kept for the assistant. */
function ProjectFilesRead({ run }: { run: MarketingRun }) {
  const b = run.files?.brochure
  const heard = run.reels?.find((r) => r.kind === 'video')?.heard ?? []
  if (!b && heard.length === 0) return null
  return (
    <div className="space-y-2 rounded-xl border border-gray-200 bg-gray-50 p-3 text-sm">
      <p className="font-semibold text-gray-800">From the project files (the builder&apos;s claims, not checked by us)</p>
      {b?.rera_missing && <p role="alert" className="rounded-lg bg-amber-50 p-2 font-semibold text-amber-900">The brochure shows no MahaRERA number. Ask the builder for it before marketing a project that must be registered.</p>}
      {b?.rera_no && <p className="text-gray-700">MahaRERA number on the brochure: {b.rera_no}</p>}
      {b?.error && <p className="text-red-800">{b.error}</p>}
      {(b?.claims?.length ?? 0) > 0 && (
        <div><p className="text-gray-600">Brochure{b?.pages ? ` (${b.pages} pages; its maps and plans are used behind the posts)` : ''}:</p>
          <ul className="list-disc pl-5 text-gray-800">{b!.claims!.map((c) => <li key={c}>{c}</li>)}</ul></div>
      )}
      {heard.length > 0 && (
        <div><p className="text-gray-600">Said in the video:</p><ul className="list-disc pl-5 text-gray-800">{heard.map((c) => <li key={c}>{c}</li>)}</ul></div>
      )}
      <p className="text-xs text-gray-500">The assistant answers buyers with these as &quot;the builder says&quot;.</p>
    </div>
  )
}

/** What the run could not work out by itself: one quick choice per question; the last answer lets it make the posts.
 *  The brochure and video are uploaded right here; once one is attached the 'files' question answers itself. */
function RunQuestions({ listingId, questions, onAnswer }: {
  listingId: string
  questions: RunQuestion[]
  onAnswer: (key: string, value: unknown) => Promise<void>
}) {
  const [typed, setTyped] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState<string | null>(null)
  const send = async (key: string, value: unknown) => {
    setBusy(key)
    try {
      await onAnswer(key, value)
    } finally {
      setBusy(null)
    }
  }
  return (
    <div className="mt-2 space-y-3 rounded-xl border border-amber-300 bg-amber-50 p-3">
      <p className="text-sm font-semibold text-amber-900">
        A few quick questions before the posts are made. Only what you confirm goes into the posts.
      </p>
      {questions.map((q) => (
        <fieldset key={q.key} disabled={busy !== null} className="space-y-2">
          <legend className="text-sm font-medium text-gray-900">{q.text}</legend>
          {q.key === 'selling_points' && (
            <Link href={`/studio/listings/${encodeURIComponent(listingId)}?tab=details#selling-points`} className="inline-flex min-h-[44px] items-center text-sm font-semibold text-blue-700 underline" data-testid="selling-points-link">
              {t('spChooseInListing')}
            </Link>
          )}
          {q.key === 'files' && <RunFileUpload listingId={listingId} onAdded={() => send('files', 'added')} />}
          <div className="flex flex-wrap gap-2">
            {q.options.filter((o) => q.key !== 'files' || o.value !== 'added').map((o) => (
              <button key={o.label} type="button" onClick={() => void send(q.key, o.value)}
                className="min-h-[44px] rounded-full border border-gray-300 bg-white px-4 text-sm font-semibold text-gray-800">
                {o.label}
              </button>
            ))}
          </div>
          {q.free_text && (
            <form className="flex flex-wrap gap-2" onSubmit={(e) => { e.preventDefault(); if (typed[q.key]?.trim()) void send(q.key, typed[q.key].trim()) }}>
              <input aria-label={q.free_text} placeholder={q.free_text} value={typed[q.key] ?? ''}
                onChange={(e) => setTyped({ ...typed, [q.key]: e.target.value })}
                className="min-h-[44px] min-w-0 flex-1 rounded-lg border border-gray-300 px-3 text-sm" />
              <Btn type="submit" block={false}>Save</Btn>
            </form>
          )}
        </fieldset>
      ))}
    </div>
  )
}

const STATE_LABEL: Record<CampaignResult['state'], string> = {
  waiting: 'Waiting for your approval', approved: 'Approved, will post', posted: 'Posted',
  failed: 'Could not post', skipped: 'Skipped', removed: 'Removed',
}
const STATE_STYLE: Record<CampaignResult['state'], string> = {
  waiting: 'bg-amber-100 text-amber-900', approved: 'bg-blue-100 text-blue-900', posted: 'bg-emerald-100 text-emerald-900',
  failed: 'bg-red-100 text-red-900', skipped: 'bg-gray-100 text-gray-600', removed: 'bg-gray-100 text-gray-600',
}

const when = (iso: string | null) =>
  iso ? new Date(iso).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' }) : ''
const channelName = (c: string) => (c === 'instagram' ? 'Instagram' : 'Facebook')

/** The run's calendar rows grouped by post (angle), in campaign order. */
function byPost(items: CampaignResult[]): [string, CampaignResult[]][] {
  const out = new Map<string, CampaignResult[]>()
  for (const it of items) out.set(it.angle, [...(out.get(it.angle) ?? []), it])
  return Array.from(out.entries())
}

/** Step 3: where each post stands in the approval calendar, per channel. */
function CalendarState({ items }: { items: CampaignResult[] }) {
  return (
    <div className="mt-2 space-y-2">
      <ul className="list-none space-y-2 p-0">
        {byPost(items).map(([angle, rows]) => (
          <li key={angle} className="rounded-xl border border-gray-200 p-3 text-sm">
            <p className="font-semibold text-gray-900">{angle}{rows[0].kind === 'reel' ? ' (reel)' : ''}</p>
            {rows.map((r) => (
              <p key={r.channel} className="mt-1 flex flex-wrap items-center gap-2 text-gray-700">
                <span>{channelName(r.channel)} · {when(r.state === 'posted' ? r.posted_at : r.due_at)}</span>
                <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${STATE_STYLE[r.state]}`}>{STATE_LABEL[r.state] ?? r.state}</span>
                {r.permalink && <a href={r.permalink} target="_blank" rel="noopener noreferrer" className="text-blue-700 underline">See post</a>}
              </p>
            ))}
          </li>
        ))}
      </ul>
      <a href="/studio/content" className="inline-block font-semibold text-blue-700 underline">{t('approveInCalendar')}</a>
    </div>
  )
}

/** Step 4: what each post brought: taps on its interest link and "I am interested" presses. */
function PostLeads({ items }: { items: CampaignResult[] }) {
  const clicks = items.reduce((n, r) => n + r.clicks, 0)
  const interests = items.reduce((n, r) => n + r.interests, 0)
  return (
    <div className="mt-2 space-y-2 text-sm">
      <p className="text-gray-700">{clicks} clicks · {interests} interested, from all posts</p>
      <ul className="list-none divide-y divide-gray-100 rounded-xl border border-gray-200 p-0">
        {byPost(items).map(([angle, rows]) => (
          <li key={angle} className="flex items-center justify-between gap-2 px-3 py-2">
            <span className="min-w-0 truncate text-gray-900">{angle}</span>
            <span className="shrink-0 text-gray-700">
              {rows.reduce((n, r) => n + r.clicks, 0)} clicks · {rows.reduce((n, r) => n + r.interests, 0)} interested
            </span>
          </li>
        ))}
      </ul>
      {interests > 0 && <a href="/studio/leads" className="inline-block font-semibold text-blue-700 underline">See them in Leads</a>}
    </div>
  )
}

/** `autoStart`: a language to start in once on load (from `?start=1&lang=`), unless a run in that language is already
 *  going or done; `onAutoStarted` fires once it has been handled so the page can drop the param. */
export function MarketingRunCard({ listingId, autoStart, onAutoStarted }: {
  listingId: string
  autoStart?: DraftLanguage | null
  onAutoStarted?: () => void
}) {
  const [run, setRun] = useState<MarketingRun | null>(null)
  const [results, setResults] = useState<CampaignResult[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [open, setOpen] = useState<string | null>(null)
  const [lang, setLang] = useState<DraftLanguage>('en')
  const picked = useRef(false)
  const alive = useRef(true)

  useEffect(() => {
    alive.current = true
    return () => {
      alive.current = false
    }
  }, [])

  const refresh = useCallback(async () => {
    try {
      const r = await api.getMarketingRun(listingId)
      if (alive.current) {
        setRun(r)
        if (r?.language && !picked.current) setLang(r.language)
      }
    } catch (e) {
      if (alive.current) setError(errorMessage(e))
    } finally {
      if (alive.current) setLoading(false)
    }
  }, [listingId])

  useEffect(() => {
    void refresh()
  }, [refresh])

  useEffect(() => {
    if (!run || (!RUNNING.includes(run.status) && run.reels_state !== 'making')) return
    const id = setTimeout(() => void refresh(), POLL_MS)
    return () => clearTimeout(id)
  }, [run, refresh])

  // calendar state and leads per post, once the posts are in the calendar (read only; a failure just leaves them out)
  const sent = run?.calendar?.length ?? 0
  useEffect(() => {
    if (!sent) return
    api.getCampaignResults(listingId).then((r) => { if (alive.current) setResults(r) }, () => undefined)
  }, [listingId, sent])

  const start = async (again = false, language: DraftLanguage = lang) => {
    setError(null)
    try {
      const r = await api.startMarketingRun(listingId, again, language)
      if (alive.current) setRun(r)
    } catch (e) {
      if (alive.current) setError(errorMessage(e))
    }
  }

  // start once from the URL; the ref survives strict-mode's double effect, so only one run is asked for
  const autoDone = useRef(false)
  useEffect(() => {
    if (!autoStart || loading || autoDone.current) return
    autoDone.current = true
    picked.current = true
    setLang(autoStart)
    const has = run && run.language === autoStart && run.status !== 'failed'
    void (has ? Promise.resolve() : start(!!run, autoStart)).finally(() => onAutoStarted?.())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoStart, loading])

  const remakeReels = async () => {
    setError(null)
    try {
      const r = await api.remakeReels(listingId)
      if (alive.current) setRun(r)
    } catch (e) {
      if (alive.current) setError(errorMessage(e))
    }
  }

  const answer = async (key: string, value: unknown) => {
    setError(null)
    try {
      const r = await api.answerRunQuestion(listingId, key, value)
      if (alive.current) setRun(r)
    } catch (e) {
      if (alive.current) setError(errorMessage(e))
    }
  }

  const toCalendar = async () => {
    setError(null)
    try {
      const r = await api.sendRunToCalendar(listingId)
      if (alive.current) setRun(r)
    } catch (e) {
      if (alive.current) setError(errorMessage(e))
    }
  }

  const firstDay = (rows: NonNullable<MarketingRun['calendar']>): string => {
    const first = rows.map((c) => c.due_at).sort()[0]
    return first ? new Date(first).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) : ''
  }

  const selected = run?.posts.find((p) => p.angle === open) || null
  const [s1, s2, s3, s4, s5] = stepStates(run)
  // older runs saved no plan: the posts stand in for it
  const plan: NonNullable<MarketingRun['plan']> = run?.plan?.length
    ? run.plan
    : (run?.posts ?? []).map((p) => ({ angle: p.angle, headline: p.caption.split('\n')[0], state: 'designed' as const }))
  const skipped = Object.entries(run?.skipped ?? {})
  const written = plan.filter((p) => p.state !== 'planned')
  const designed = plan.filter((p) => p.state === 'designed').length
  const dropped = Array.from(new Set([...plan.filter((p) => p.state === 'dropped').map((p) => p.angle), ...Object.keys(run?.dropped ?? {})]))
  const running = !!run && RUNNING.includes(run.status)
  const f = run?.facts

  return (
    <section aria-labelledby="run-title" className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4">
      <h2 id="run-title" className="text-lg font-bold text-gray-900">{t('startMarketing')}</h2>
      {!run && !loading && (
        <>
          <p className="text-sm text-gray-600">{t('startMarketingHelp')}</p>
          <LanguagePicker value={lang} onChange={(l) => { picked.current = true; setLang(l) }} />
          <Btn onClick={() => start()}>{t('startMarketing')}</Btn>
        </>
      )}
      {error && <ErrorBox message={error} />}
      {run && (
        <ol className="list-none space-y-4 p-0">
          <Step n={1} title="Discovery" state={s1}>
            <p className="mt-1 text-sm text-gray-700">
              {f?.maharera ? `MahaRERA ${f.maharera} matched${f.how ? ` (${f.how})` : ''}` : f ? 'No MahaRERA project matched' : 'Reading the listing, its files and MahaRERA'}
            </p>
            {run.status === 'asking' && (run.questions?.length ?? 0) > 0 && (
              <>
                <RunQuestions listingId={listingId} questions={run.questions!} onAnswer={answer} />
                <button type="button" onClick={() => void start(true)} className="min-h-[44px] text-sm font-semibold text-gray-600 underline">
                  Start over
                </button>
              </>
            )}
            {(run.files?.brochure || run.reels?.some((r) => r.heard?.length)) && (
              <More label="What we read"><ProjectFilesRead run={run} /></More>
            )}
          </Step>
          <Step n={2} title="Facts" state={s2}>
            {f && (
              <>
                <p className="mt-1 text-sm text-gray-700">
                  {f.usable} {t('factsFound')}{f.held ? ` · ${f.held} held back (not sure enough)` : ''}{f.nearby ? ` · ${f.nearby} places nearby` : ''} ·{' '}
                  <a href={`/studio/listings/${listingId}?tab=facts`} className="font-semibold text-blue-700 underline">See checked facts</a>
                </p>
                {f.notes.length > 0 && (
                  <More label={`${f.notes.length} not found`}>
                    <ul className="list-disc pl-5 text-gray-700">{f.notes.map((n) => <li key={n}>{n}</li>)}</ul>
                  </More>
                )}
              </>
            )}
          </Step>
          <Step n={3} title="Plan" state={s3}>
            {plan.length > 0 && (
              <>
                <p className="mt-1 text-sm text-gray-700">{plan.length} posts: {plan.map((p) => angleName(p.angle)).join(', ')}</p>
                {skipped.length > 0 && (
                  <More label={`${skipped.length} ideas left out`}>
                    <ul className="list-disc pl-5 text-gray-700">{skipped.map(([k, why]) => <li key={k}>{angleName(k)}: {why}</li>)}</ul>
                  </More>
                )}
              </>
            )}
          </Step>
          <Step n={4} title="Content" state={s4}>
            {written.length > 0 && (
              <>
                <p className="mt-1 text-sm text-gray-700">{written.length} of {plan.length} headlines written</p>
                <More label="See headlines">
                  <ul className="list-none space-y-2 p-0">
                    {written.map((p) => (
                      <li key={p.angle}>
                        <span className="text-xs text-gray-500">{angleName(p.angle)}</span>
                        <p className="text-gray-900">{p.headline}</p>
                        {p.was && <p className="text-xs text-gray-500 line-through">{p.was}</p>}
                      </li>
                    ))}
                  </ul>
                </More>
              </>
            )}
          </Step>
          <Step n={5} title="Design" state={s5}>
            {run.status !== 'done' && designed + dropped.length > 0 && (
              <p className="mt-1 text-sm text-gray-700">{designed} of {plan.length} cards made</p>
            )}
            {dropped.length > 0 && (
              <More label={`${dropped.length} left out (did not pass the checks)`}>
                <ul className="list-disc pl-5 text-gray-700">
                  {dropped.map((a) => <li key={a}>{angleName(a)}{run.dropped?.[a] ? `: ${run.dropped[a]}` : ''}</li>)}
                </ul>
              </More>
            )}
            {run.status === 'done' && (
              <div className="mt-2 space-y-2">
                <p className="text-sm text-gray-700">{run.posts.length} {t(run.posts.length === 1 ? 'postReady' : 'postsReady')}</p>
                <ul className="grid list-none grid-cols-3 gap-2 p-0 sm:grid-cols-4">
                  {run.posts.map((p) => (
                    <li key={p.angle}>
                      <button type="button" onClick={() => setOpen(open === p.angle ? null : p.angle)} aria-pressed={open === p.angle}
                        className={`block w-full rounded-lg text-left ${open === p.angle ? 'ring-2 ring-blue-600' : ''}`}>
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={p.images[0]} alt={p.caption.split('\n')[0]} className="aspect-[4/5] w-full rounded-lg object-cover" />
                        <span className="text-xs text-gray-500">
                          {p.images.length > 1 ? `+${p.images.length - 1} ` : ''}{p.edited ? t('editedTag') : ''}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
                {selected && (
                  <div className="rounded-xl border border-gray-200 p-3">
                    <div className="flex gap-2 overflow-x-auto">
                      {selected.images.map((src) => (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img key={src} src={src} alt="" className="h-40 w-32 shrink-0 rounded-lg object-cover" />
                      ))}
                    </div>
                    <CampaignPostEditor key={selected.angle + (selected.redos || 0)} listingId={listingId} post={selected} onRun={setRun} />
                  </div>
                )}
                {run.reels && run.reels.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-sm font-semibold text-gray-800">{t('reelsTitle')}</p>
                    <ul className="grid list-none grid-cols-3 gap-2 p-0 sm:grid-cols-4">
                      {run.reels.filter((r) => r.video && (r.kind === 'ad' || r.kind === 'slides' || r.status === 'done')).map((r) => (
                        <li key={r.kind + (r.angle || '')}>
                          <video src={r.video || undefined} controls preload="metadata" playsInline
                            aria-label={r.kind === 'walkthrough' ? t('walkthroughReel') : r.kind === 'video' ? 'Reel from your video' : r.angle}
                            className="aspect-[9/16] w-full rounded-lg bg-black object-cover" />
                          {r.kind === 'ad' && r.script && (
                            <p className="mt-1 text-xs text-gray-600" title={[r.script.hook, ...r.script.beats, r.script.payoff].join(' / ')}>
                              <span className="font-medium">{(r.format || '').replace(/_/g, ' ')}</span>: {r.script.hook.replace(/\*/g, '')}
                            </p>
                          )}
                        </li>
                      ))}
                    </ul>
                    {run.reels.filter((r) => r.kind === 'walkthrough' && r.status !== 'done').map((r) => (
                      <p key="walk" className="text-xs text-gray-500">
                        {t('walkthroughReel')}: {r.status === 'skipped' ? `${t('walkthroughSkipped')}${r.note ? ` (${r.note})` : ''}` : t('walkthroughMaking')}
                      </p>
                    ))}
                    {run.reels.filter((r) => r.kind === 'video' && r.status === 'skipped').map((r) => (
                      <p key="video" className="text-xs text-gray-500">Reel from your video: not made{r.note ? ` (${r.note})` : ''}</p>
                    ))}
                  </div>
                )}
                {run.status === 'done' && (
                  <div className="space-y-1">
                    <Btn disabled={run.reels_state === 'making'} onClick={remakeReels}>
                      {run.reels_state === 'making' ? 'Making the reels…' : 'Make the reels again (ad style)'}
                    </Btn>
                    <p className="text-xs text-gray-500">
                      Every post becomes a short ad reel (hook, quick cuts, price at the end, "Comment VISIT"). Uses these posts,
                      facts and photos; waiting calendar posts are swapped for their reels.
                    </p>
                    {run.reels_state === 'failed' && run.reels_error && <p className="text-xs text-red-600">{run.reels_error}</p>}
                  </div>
                )}
                {!sent && <Btn onClick={toCalendar}>{t('sendToCalendar')}</Btn>}
              </div>
            )}
          </Step>
          {run.status === 'done' && sent > 0 && (
            <>
              <Step n={6} title="In the calendar" state="done">
                <p className="mt-1 text-sm text-gray-700">{sent} {t('sentToCalendar')} {firstDay(run.calendar!)}.</p>
                {results.length > 0 && <CalendarState items={results} />}
              </Step>
              <Step n={7} title="Leads from these posts" state={results.some((r) => r.state === 'posted') ? 'done' : 'waiting'}>
                {results.length > 0 && <PostLeads items={results} />}
              </Step>
            </>
          )}
          {run.status === 'done' && run.boost && (
            <Step n={sent > 0 ? 8 : 6} title={t('boostTitle')}
              state={run.boost.state === 'failed' ? 'failed' : run.boost.state === 'making' ? 'working'
                : run.boost.state === 'boosted' || run.boost.state === 'finished' ? 'done' : 'waiting'}>
              <BoostStep listingId={listingId} run={run} onRun={setRun} />
            </Step>
          )}
        </ol>
      )}
      {run?.status === 'failed' && run.error && <ErrorBox message={run.error} />}
      {run && !running && (
        <>
          <LanguagePicker value={lang} onChange={(l) => { picked.current = true; setLang(l) }} />
          <Btn onClick={() => start(true)}>{run.status === 'failed' ? t('tryAgain') : t('makeAgain')}</Btn>
        </>
      )}
    </section>
  )
}
