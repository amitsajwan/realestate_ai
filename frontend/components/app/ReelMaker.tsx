'use client'
import React, { useState } from 'react'
import {
  POLL_MS,
  REEL_LANGS,
  friendlyReelError,
  isActive,
  reelFilename,
  reelVideoUrl,
  whatsappReelUrl,
} from '@/lib/app/reels'
import type { ReelJob, ReelJobs, ReelLang, ReelSource } from '@/lib/app/reels'
import { Btn, LinkBtn } from './ui'

/**
 * 'Make my reel': a real video from the listing's photos and facts, voiced in English, Hindi or Marathi. The server renders it
 * (a few minutes); this polls every 5 s, then shows the video with Download and Share on WhatsApp.
 * `source` is the agent's own listing, or the owner acting for an agent (concierge).
 */
export function ReelMaker({ source, caption, label = 'Make my reel', onDone }: {
  source: ReelSource
  caption: string
  label?: string
  onDone?: (job: ReelJob) => void
}) {
  const [lang, setLang] = useState<ReelLang>('en')
  const [jobs, setJobs] = useState<ReelJobs>({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const sourceRef = React.useRef(source)
  sourceRef.current = source
  const job = jobs[lang]
  const active = isActive(job)
  const onDoneRef = React.useRef(onDone)
  onDoneRef.current = onDone

  const refresh = React.useCallback(async () => {
    try {
      const latest = await sourceRef.current.latest()
      setJobs(latest)
      Object.values(latest).forEach((j) => j && j.status === 'done' && onDoneRef.current?.(j))
    } catch {
      /* keep what we have; the next poll tries again */
    }
  }, [])

  React.useEffect(() => {
    void refresh()
  }, [refresh])

  const anyActive = Object.values(jobs).some((j) => isActive(j))
  React.useEffect(() => {
    if (!anyActive) return
    const id = setInterval(() => void refresh(), POLL_MS)
    return () => clearInterval(id)
  }, [anyActive, refresh])

  async function make(again = false) {
    setBusy(true)
    setError(null)
    try {
      const j = await source.make(lang, again)
      setJobs((prev) => ({ ...prev, [lang]: j }))
    } catch (e) {
      setError(friendlyReelError(e))
    } finally {
      setBusy(false)
    }
  }

  const url = job?.status === 'done' && job.video_path ? reelVideoUrl(job) : null
  return (
    <div className="space-y-3" data-testid="reel-maker">
      <p className="text-sm font-semibold text-gray-700">Your reel, made for you</p>
      <div role="radiogroup" aria-label="Reel language" className="grid grid-cols-3 gap-2">
        {REEL_LANGS.map((l) => (
          <button key={l.code} type="button" role="radio" aria-checked={lang === l.code} onClick={() => setLang(l.code)}
            className={`min-h-[44px] rounded-xl border text-sm font-semibold ${lang === l.code ? 'border-blue-600 bg-blue-50 text-blue-900' : 'border-gray-300 text-gray-700'}`}>
            {l.label}
          </button>
        ))}
      </div>

      {active && (
        <div role="status" className="flex items-center gap-3 rounded-xl bg-blue-50 p-3 text-sm text-blue-900" data-testid="reel-progress">
          <span aria-hidden className="h-5 w-5 flex-none animate-spin rounded-full border-2 border-blue-200 border-t-blue-600" />
          <span>Making your reel... this takes a few minutes. You can leave this page and come back.</span>
        </div>
      )}

      {url && job && (
        <div className="space-y-2" data-testid="reel-done">
          <video src={url} controls playsInline preload="metadata" className="mx-auto aspect-[9/16] w-full max-w-[280px] rounded-xl bg-black" data-testid="reel-video" />
          {job.note && <p className="text-xs text-gray-500">{job.note}</p>}
          <div className="grid grid-cols-2 gap-2">
            <a href={url} download={reelFilename(job)} className="flex min-h-[52px] items-center justify-center rounded-xl border border-gray-300 bg-white px-3 text-base font-semibold text-gray-900">
              Download
            </a>
            <LinkBtn variant="whatsapp" href={whatsappReelUrl(url, caption)} target="_blank" rel="noopener noreferrer">
              Share on WhatsApp
            </LinkBtn>
          </div>
          <Btn variant="ghost" onClick={() => make(true)} disabled={busy}>Make it again</Btn>
        </div>
      )}

      {job?.status === 'failed' && (
        <div role="alert" className="space-y-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700" data-testid="reel-failed">
          <p>The reel could not be made. {job.error}</p>
          <Btn variant="secondary" onClick={() => make(true)} disabled={busy}>Try again</Btn>
        </div>
      )}

      {!job && (
        <Btn onClick={() => make()} disabled={busy}>{busy ? 'Starting...' : label}</Btn>
      )}
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
    </div>
  )
}
