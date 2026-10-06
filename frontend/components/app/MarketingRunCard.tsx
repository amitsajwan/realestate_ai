'use client'
import React, { useCallback, useEffect, useRef, useState } from 'react'
import { api, errorMessage } from '@/lib/app/client'
import { t } from '@/lib/app/strings'
import type { DraftLanguage, MarketingRun } from '@/lib/app/types'
import { CampaignPostEditor } from './CampaignPostEditor'
import { Btn, ErrorBox } from './ui'

const POLL_MS = 3000
const RUNNING: MarketingRun['status'][] = ['queued', 'facts', 'posts']

type StepState = 'waiting' | 'working' | 'done' | 'failed'

function stepStates(run: MarketingRun | null): [StepState, StepState] {
  if (!run) return ['waiting', 'waiting']
  const factsDone = !!run.facts_done_at
  if (run.status === 'failed') return factsDone ? ['done', 'failed'] : ['failed', 'waiting']
  if (run.status === 'done') return ['done', 'done']
  if (run.status === 'posts') return ['done', 'working']
  return ['working', 'waiting']
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

/** "Start marketing": step 1 checks the project facts and puts them on the listing page; step 2 makes the posts from them.
 *  Posts are drafts here: publishing still needs approval. */
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

export function MarketingRunCard({ listingId }: { listingId: string }) {
  const [run, setRun] = useState<MarketingRun | null>(null)
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
    if (!run || !RUNNING.includes(run.status)) return
    const id = setTimeout(() => void refresh(), POLL_MS)
    return () => clearTimeout(id)
  }, [run, refresh])

  const start = async (again = false) => {
    setError(null)
    try {
      const r = await api.startMarketingRun(listingId, again, lang)
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
  const [s1, s2] = stepStates(run)
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
          <Step n={1} title={t('stepFacts')} state={s1}>
            {f && (
              <div className="mt-1 space-y-1 text-sm text-gray-700">
                <p>
                  {f.usable} {t('factsFound')}
                  {f.maharera ? ` · ${t('onMaharera')} ${f.maharera}` : ''}
                  {f.nearby ? ` · ${f.nearby} ${t('nearbyFound')}` : ''}
                </p>
                {f.notes.map((n) => <p key={n} className="text-xs text-gray-500">{n}</p>)}
                {run.page_url && (
                  <a href={run.page_url} target="_blank" rel="noopener noreferrer" className="font-semibold text-blue-700 underline">
                    {t('viewPage')}
                  </a>
                )}
              </div>
            )}
          </Step>
          <Step n={2} title={t('stepPosts')} state={s2}>
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
                      {run.reels.filter((r) => r.video && (r.kind === 'slides' || r.status === 'done')).map((r) => (
                        <li key={r.kind + (r.angle || '')}>
                          <video src={r.video || undefined} controls preload="metadata" playsInline
                            aria-label={r.kind === 'walkthrough' ? t('walkthroughReel') : r.angle}
                            className="aspect-[9/16] w-full rounded-lg bg-black object-cover" />
                        </li>
                      ))}
                    </ul>
                    {run.reels.filter((r) => r.kind === 'walkthrough' && r.status !== 'done').map((r) => (
                      <p key="walk" className="text-xs text-gray-500">
                        {t('walkthroughReel')}: {r.status === 'skipped' ? `${t('walkthroughSkipped')}${r.note ? ` (${r.note})` : ''}` : t('walkthroughMaking')}
                      </p>
                    ))}
                  </div>
                )}
                {run.calendar && run.calendar.length > 0 ? (
                  <p role="status" className="rounded-xl bg-emerald-50 p-3 text-sm text-emerald-900">
                    {run.calendar.length} {t('sentToCalendar')} {firstDay(run.calendar)}.{' '}
                    <a href="/studio/content" className="font-semibold underline">{t('approveInCalendar')}</a>
                  </p>
                ) : (
                  <Btn onClick={toCalendar}>{t('sendToCalendar')}</Btn>
                )}
              </div>
            )}
          </Step>
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
