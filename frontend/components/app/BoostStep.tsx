'use client'
import React, { useEffect, useRef, useState } from 'react'
import { api, errorMessage } from '@/lib/app/client'
import { t, tf } from '@/lib/app/strings'
import type { CampaignReport, MarketingRun, RunBoost } from '@/lib/app/types'
import { Btn, ErrorBox } from './ui'

const POLL_MS = 3000
const DAY_MS = 86_400_000
const inr = (n: number) => Math.round(n).toLocaleString('en-IN')

function readTicks(key: string): boolean[] {
  try {
    const v = JSON.parse(window.localStorage.getItem(key) || '[]')
    return Array.isArray(v) ? v : []
  } catch {
    return []
  }
}
function writeTicks(key: string, v: boolean[]) {
  try {
    window.localStorage.setItem(key, JSON.stringify(v))
  } catch {
    /* ignore */
  }
}

/** One tap copies; the button says "Copied ✓" for a moment. */
function CopyRow({ label, text }: { label: string; text: string }) {
  const [done, setDone] = useState(false)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setDone(true)
      setTimeout(() => setDone(false), 2000)
    } catch {
      /* clipboard blocked: the text stays visible to select by hand */
    }
  }
  return (
    <div className="flex items-start gap-2 rounded-lg border border-gray-200 p-2">
      <div className="min-w-0 flex-1">
        <p className="text-xs font-semibold text-gray-500">{label}</p>
        <p className="whitespace-pre-line break-words text-sm text-gray-900">{text}</p>
      </div>
      <button type="button" onClick={copy}
        className="min-h-[44px] shrink-0 rounded-lg border border-blue-200 px-3 text-sm font-semibold text-blue-700 active:bg-blue-50">
        {done ? t('boostCopied') : t('boostCopy')}
      </button>
    </div>
  )
}

/** Share the file (phone share sheet) when the browser can, else a plain download link. */
async function shareOrDownload(url: string, name: string) {
  try {
    const nav = navigator as Navigator & { canShare?: (d: ShareData) => boolean }
    if (nav.share && nav.canShare) {
      const blob = await (await fetch(url)).blob()
      const file = new File([blob], name, { type: blob.type })
      if (nav.canShare({ files: [file] })) {
        await nav.share({ files: [file] })
        return
      }
    }
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') return
  }
  const a = document.createElement('a')
  a.href = url
  a.download = name
  a.target = '_blank'
  a.rel = 'noopener'
  a.click()
}

function dayOf(b: RunBoost): number {
  if (!b.boosted_at) return 1
  return Math.max(1, Math.floor((Date.now() - new Date(b.boosted_at).getTime()) / DAY_MS) + 1)
}

/** Step 8: the paid boost kit, a Facebook checklist, "I've boosted it", and paid vs free results. Nothing without run.boost. */
export function BoostStep({ listingId, run, onRun }: { listingId: string; run: MarketingRun; onRun: (r: MarketingRun) => void }) {
  const b = run.boost
  const [open, setOpen] = useState(false)
  const [early, setEarly] = useState(false)
  const [showSteps, setShowSteps] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [report, setReport] = useState<CampaignReport | null>(null)
  const tickKey = `boost_ticks_${listingId}`
  const [ticks, setTicks] = useState<boolean[]>([])
  const [daily, setDaily] = useState('')
  const [days, setDays] = useState('')
  const alive = useRef(true)

  useEffect(() => {
    alive.current = true
    setTicks(readTicks(tickKey))
    return () => {
      alive.current = false
    }
  }, [tickKey])

  useEffect(() => {
    if (!b) return
    setDaily(String(b.daily_spend_inr ?? b.guide.daily_budget_inr))
    setDays(String(b.days ?? b.guide.days))
  }, [b?.daily_spend_inr, b?.days, b?.guide.daily_budget_inr, b?.guide.days]) // eslint-disable-line react-hooks/exhaustive-deps

  // poll while the reel is being made
  useEffect(() => {
    if (b?.state !== 'making') return
    const id = setTimeout(() => {
      api.getMarketingRun(listingId).then((r) => { if (alive.current && r) onRun(r) }, () => undefined)
    }, POLL_MS)
    return () => clearTimeout(id)
  }, [b, listingId, onRun])

  const boosted = b?.state === 'boosted' || b?.state === 'finished'
  useEffect(() => {
    if (!boosted) return
    api.getCampaignReport(listingId).then((r) => { if (alive.current) setReport(r) }, () => undefined)
  }, [boosted, listingId])

  if (!b) return null

  const act = async (fn: () => Promise<MarketingRun>) => {
    setBusy(true)
    setError(null)
    try {
      const r = await fn()
      if (alive.current && r) onRun(r)
    } catch (e) {
      if (alive.current) setError(errorMessage(e))
    } finally {
      if (alive.current) setBusy(false)
    }
  }

  const tick = (i: number) => {
    const next = [...ticks]
    next[i] = !next[i]
    setTicks(next)
    writeTicks(tickKey, next)
  }

  const g = b.guide
  const tooSoon = !!b.ready_at && Date.now() < new Date(b.ready_at).getTime() && !early
  const badge =
    b.state === 'boosted' ? tf('boostBoosted', { n: Math.min(dayOf(b), b.days ?? g.days), d: b.days ?? g.days })
      : b.state === 'finished' ? t('boostFinished')
        : b.state === 'ready' ? t('boostReady') : null
  const copy = b.copy?.reel ?? b.copy?.post
  const fbUrl = b.reel_permalink || b.meta_open_url
  const steps: React.ReactNode[] = [
    <>
      {t('boostS1')}{' '}
      <a href={fbUrl} target="_blank" rel="noopener noreferrer"
        className="mt-1 inline-flex min-h-[44px] items-center rounded-lg bg-blue-600 px-3 text-sm font-semibold text-white">
        {t('boostOpenFb')}
      </a>
    </>,
    t('boostS2'),
    tf('boostS3', { a: g.age_min, b: g.age_max, r: g.radius_km, area: g.area }),
    tf('boostS4', { daily: inr(g.daily_budget_inr), days: g.days, total: inr(g.daily_budget_inr * g.days) }),
    t('boostS5'),
    tf('boostS6', { n: g.carousel_delay_days, daily: inr(g.carousel_daily_inr) }),
  ]
  const br = report?.boost_results
  const org = report?.organic

  return (
    <div className="mt-2 space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <p className="text-sm text-gray-700">{t('boostSub')}</p>
        {badge && <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800">{badge}</span>}
      </div>

      {b.state === 'making' && <p className="animate-pulse text-sm text-blue-700">{t('boostMaking')}</p>}
      {b.state === 'failed' && (
        <>
          <ErrorBox message={b.error || t('runFailed')} />
          <Btn disabled={busy} onClick={() => act(() => api.remakeBoost(listingId))}>{t('boostMakeAgain')}</Btn>
        </>
      )}

      {b.state !== 'making' && b.state !== 'failed' && (
        <>
          {/* check before boosting: the reel plays and every carousel card shows here, not only inside the kit */}
          <div className="grid grid-cols-2 gap-2">
            {b.reel && (
              <div>
                <p className="mb-1 text-xs font-semibold text-gray-700">Boost reel{b.reel.duration_s ? ` · ${Math.round(b.reel.duration_s)} s` : ''}</p>
                <video src={b.reel.video_url} poster={b.reel.poster_url || undefined} controls playsInline preload="metadata"
                  className="aspect-[9/16] w-full rounded-lg bg-black object-cover" />
              </div>
            )}
            {b.carousel && b.carousel.images.length > 0 && (
              <div className="min-w-0">
                <p className="mb-1 text-xs font-semibold text-gray-700">Boost post · {b.carousel.images.length} cards, swipe</p>
                <div className="flex snap-x gap-2 overflow-x-auto">
                  {b.carousel.images.map((src, i) => (
                    <a key={src} href={src} target="_blank" rel="noopener noreferrer" className="shrink-0 snap-start" style={{ width: '100%' }}>
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={src} alt={`Card ${i + 1}`} className="aspect-[4/5] w-full rounded-lg object-cover" />
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>

          {b.state === 'ready' && tooSoon && (
            <p className="text-sm text-gray-700">
              {t('boostWait')}{' '}
              <button type="button" onClick={() => setEarly(true)} className="min-h-[44px] font-semibold text-blue-700 underline">
                {t('boostNowAnyway')}
              </button>
            </p>
          )}
          {b.state === 'ready' && !tooSoon && !open && <Btn onClick={() => setOpen(true)}>{t('boostGetReady')}</Btn>}

          {(open || boosted) && b.state !== 'finished' && (
            <details open={open} className="rounded-xl border border-gray-200 p-3">
              <summary className="min-h-[44px] cursor-pointer py-2 font-semibold text-gray-900">{t('boostKit')}</summary>
              <div className="space-y-3">
                {b.reel && (
                  <video src={b.reel.video_url} poster={b.reel.poster_url} controls playsInline preload="metadata"
                    className="mx-auto aspect-[9/16] w-full max-w-xs rounded-lg bg-black object-cover" />
                )}
                {b.carousel && b.carousel.images.length > 0 && (
                  <div className="flex snap-x snap-mandatory gap-2 overflow-x-auto">
                    {b.carousel.images.map((src) => (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img key={src} src={src} alt="" className="h-64 w-52 shrink-0 snap-start rounded-lg object-cover" />
                    ))}
                  </div>
                )}
                <div className="grid grid-cols-2 gap-2">
                  {b.reel && (
                    <Btn variant="secondary" onClick={() => shareOrDownload(b.reel!.video_url, 'boost-reel.mp4')}>{t('boostDlReel')}</Btn>
                  )}
                  {b.carousel?.zip_url && (
                    <Btn variant="secondary" onClick={() => shareOrDownload(b.carousel!.zip_url, 'boost-photos.zip')}>{t('boostDlPhotos')}</Btn>
                  )}
                </div>
                {copy && <CopyRow label={t('boostMainText')} text={copy.primary_text} />}
                {copy && <CopyRow label={t('boostHeadline')} text={copy.headline} />}
                {b.wa_prefill && <CopyRow label={t('boostGreeting')} text={b.wa_prefill} />}
                {b.tracked_link && (
                  <>
                    <CopyRow label={t('boostLink')} text={b.tracked_link} />
                    <p className="text-xs text-gray-500">{t('boostLinkHelp')}</p>
                  </>
                )}
                {!showSteps && !boosted && <Btn onClick={() => setShowSteps(true)}>{t('boostNext')}</Btn>}
              </div>
            </details>
          )}

          {(showSteps || boosted) && b.state !== 'finished' && (
            <div className="space-y-2">
              <ol className="list-none space-y-2 p-0">
                {steps.map((s, i) => (
                  <li key={i}>
                    <label className={`flex min-h-[44px] cursor-pointer gap-3 rounded-lg border p-3 text-sm ${ticks[i] ? 'border-emerald-300 bg-emerald-50' : 'border-gray-200'}`}>
                      <input type="checkbox" checked={!!ticks[i]} onChange={() => tick(i)} className="mt-0.5 h-5 w-5 shrink-0" />
                      <span className="text-gray-900"><b>{i + 1}.</b> {s}</span>
                    </label>
                  </li>
                ))}
              </ol>
              <p className="text-xs text-gray-500">{t('boostHousing')}</p>
            </div>
          )}

          {showSteps && b.state === 'ready' && (
            <div className="space-y-2 rounded-xl border border-gray-200 p-3">
              <p className="font-semibold text-gray-900">{t('boostDone')}</p>
              <p className="flex flex-wrap items-center gap-2 text-sm text-gray-700">
                {t('boostHowMuch')} ₹
                <input inputMode="numeric" value={daily} onChange={(e) => setDaily(e.target.value.replace(/\D/g, ''))}
                  aria-label="₹ a day" className="min-h-[44px] w-20 rounded-lg border border-gray-300 px-2" />
                {t('boostPerDay')}
                <input inputMode="numeric" value={days} onChange={(e) => setDays(e.target.value.replace(/\D/g, ''))}
                  aria-label={t('boostDays')} className="min-h-[44px] w-16 rounded-lg border border-gray-300 px-2" />
                {t('boostDays')}
              </p>
              <Btn disabled={busy || !Number(daily) || !Number(days)}
                onClick={() => act(() => api.markBoosted(listingId, Number(daily), Number(days)))}>
                {t('boostSave')}
              </Btn>
            </div>
          )}

          {boosted && (
            <div className="space-y-1 rounded-xl bg-gray-50 p-3 text-sm text-gray-800">
              {org && <p>{tf('boostFree', { c: org.clicks, i: org.interests })}</p>}
              {br && (
                <p>
                  {tf('boostPaid', { c: br.clicks, i: br.interests, s: inr(br.spend_inr) })}
                  {br.cost_per_enquiry != null && tf('boostPer', { p: inr(br.cost_per_enquiry) })}
                </p>
              )}
              {(!br || br.interests === 0) && <p>{t('boostNoMsgs')}</p>}
              <p className="text-xs text-gray-500">{t('boostUpdates')}</p>
            </div>
          )}
        </>
      )}
      {error && <ErrorBox message={error} />}
    </div>
  )
}
