'use client'
import React, { useState } from 'react'
import {
  downloadImage,
  hashtagsLine,
  imageFilename,
  instagramCopyText,
  reelScriptText,
  shareImage,
  whatsappPackUrl,
} from '@/lib/app/marketing'
import {
  POLL_MS,
  REEL_LANGS,
  friendlyReelError,
  isActive,
  reelFilename,
  reelVideoUrl,
  reelsApi,
  whatsappReelUrl,
} from '@/lib/app/reels'
import type { ReelJob, ReelJobs, ReelLang, ReelSource } from '@/lib/app/reels'
import { copyText } from '@/lib/app/share'
import { t } from '@/lib/app/strings'
import type { MarketingPack } from '@/lib/app/types'
import { SocialPublishSection } from './SocialPublishSection'
import { Btn, LinkBtn } from './ui'

export function CopyBtn({ text, label, variant = 'secondary' }: { text: string; label: string; variant?: 'primary' | 'secondary' }) {
  const [copied, setCopied] = useState(false)
  return (
    <Btn
      variant={variant}
      onClick={async () => {
        const ok = await copyText(text)
        setCopied(ok)
        if (ok) setTimeout(() => setCopied(false), 2000)
      }}
    >
      {copied ? t('copied') : label}
    </Btn>
  )
}

const CONTACT_KEY = 'pp_group_contact'

/** Text for WhatsApp / Facebook groups. Groups expect a way to reach the poster, so the agent adds their OWN contact line here; it is kept only on
 *  this phone and is never sent to us or put on our Page. */
function GroupCard({ post }: { post: string }) {
  const [contact, setContact] = useState('')
  React.useEffect(() => {
    try { setContact(window.localStorage.getItem(CONTACT_KEY) || '') } catch { /* ignore */ }
  }, [])
  const save = (v: string) => {
    setContact(v)
    try { window.localStorage.setItem(CONTACT_KEY, v) } catch { /* ignore */ }
  }
  const full = contact.trim() ? `${post}\n\u260e ${contact.trim()}` : post
  return (
    <Card title="For groups" testId="card-group">
      <p className="text-sm text-gray-600">Short, photo-first text for the WhatsApp and Facebook groups where you already post. Follow each group&apos;s rules: only genuine, current properties, and do not repost the same one again and again.</p>
      <label className="block text-sm font-semibold text-gray-700" htmlFor="group-contact">Your contact line (kept on this phone only)</label>
      <input id="group-contact" value={contact} onChange={(e) => save(e.target.value)} maxLength={80} placeholder="e.g. Rahul, call/WhatsApp 98xxxxxxxx"
        className="min-h-[48px] w-full rounded-xl border border-gray-300 px-3 text-base" />
      <p className={textBox} data-testid="group-post">{full}</p>
      <CopyBtn text={full} label="Copy for groups" variant="primary" />
    </Card>
  )
}

function Card({ title, children, testId }: { title: string; children: React.ReactNode; testId: string }) {
  return (
    <section className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4" aria-label={title} data-testid={testId}>
      <h2 className="text-lg font-bold text-gray-900">{title}</h2>
      {children}
    </section>
  )
}

const textBox = 'whitespace-pre-wrap break-words rounded-xl bg-gray-50 p-3 text-sm text-gray-900'

function InstagramCard({ pack }: { pack: MarketingPack }) {
  const { images, caption, hashtags } = pack.instagram
  const [active, setActive] = useState(0)
  const [note, setNote] = useState('')
  const current = images[Math.min(active, Math.max(0, images.length - 1))]
  const full = instagramCopyText(pack.instagram)

  return (
    <Card title={t('instagram')} testId="card-instagram">
      {images.length > 0 && (
        <>
          <div
            className="flex snap-x snap-mandatory gap-3 overflow-x-auto pb-2"
            data-testid="carousel"
            onScroll={(e) => {
              const el = e.currentTarget
              if (el.clientWidth > 0) setActive(Math.round(el.scrollLeft / (el.clientWidth * 0.86)))
            }}
          >
            {images.map((img) => (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                key={img.kind}
                src={img.url}
                alt={`Instagram ${img.kind} card`}
                width={img.width}
                height={img.height}
                className="aspect-square w-[86%] flex-none snap-center rounded-xl bg-gray-100 object-cover"
              />
            ))}
          </div>
          <p className="text-center text-xs text-gray-500" aria-live="polite">
            {Math.min(active, images.length - 1) + 1} / {images.length}
          </p>
        </>
      )}
      <p className={textBox} data-testid="ig-caption">{caption}</p>
      {hashtags.length > 0 && <p className="break-words text-sm text-blue-700" data-testid="ig-hashtags">{hashtagsLine(hashtags)}</p>}
      <CopyBtn text={full} label={t('copyCaption')} variant="primary" />
      {current && (
        <div className="grid grid-cols-2 gap-3">
          <Btn
            variant="secondary"
            onClick={async () => {
              const r = await shareImage(current, imageFilename(current, pack.listing_id), full)
              setNote(r === 'downloaded' ? 'Image saved. Add it to your post.' : r === 'opened' ? 'Image opened. Save it, then post.' : '')
            }}
          >
            {t('shareImage')}
          </Btn>
          <Btn variant="secondary" onClick={() => downloadImage(current, imageFilename(current, pack.listing_id))}>
            {t('downloadImage')}
          </Btn>
        </div>
      )}
      {note && <p role="status" className="text-center text-sm text-gray-600">{note}</p>}
    </Card>
  )
}

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

export function MarketingPackView({ pack }: { pack: MarketingPack }) {
  const statusImage = pack.whatsapp.status_image
  const waText = pack.whatsapp.message
  return (
    <div className="space-y-4" data-testid="pack">
      <div className="rounded-2xl bg-blue-50 p-4">
        <p className="text-sm text-blue-900">{pack.angle}</p>
        <p className="mt-1 font-bold text-blue-950">{pack.headline}</p>
      </div>

      <InstagramCard pack={pack} />

      <Card title={t('facebook')} testId="card-facebook">
        <p className={textBox} data-testid="fb-post">{pack.facebook.post}</p>
        <CopyBtn text={pack.facebook.post} label={t('copyPost')} variant="primary" />
      </Card>

      {pack.group?.post && <GroupCard post={pack.group.post} />}

      <Card title="WhatsApp" testId="card-whatsapp">
        <p className={textBox} data-testid="wa-message">{waText}</p>
        <LinkBtn variant="whatsapp" href={whatsappPackUrl(waText)} target="_blank" rel="noopener noreferrer">
          {t('sendOnWhatsapp')}
        </LinkBtn>
        <CopyBtn text={waText} label={t('copyMessage')} />
        <div className="space-y-2 border-t border-gray-100 pt-3">
          <p className="text-sm font-semibold text-gray-700">{t('whatsappStatus')}</p>
          <p className={textBox} data-testid="wa-status">{pack.whatsapp.status_text}</p>
          {statusImage && (
            <Btn variant="secondary" onClick={() => downloadImage(statusImage, imageFilename(statusImage, pack.listing_id))}>
              {t('downloadStatusImage')}
            </Btn>
          )}
        </div>
      </Card>

      <Card title={t('reel')} testId="card-reel">
        <p className="text-sm">
          <b>{t('reelHook')}:</b> {pack.reel.hook}
        </p>
        <ol className="list-decimal space-y-2 pl-5 text-sm" data-testid="reel-beats">
          {pack.reel.beats.map((b, i) => (
            <li key={i}>
              <span className="text-xs font-semibold text-gray-500">{/s$/.test(b.seconds) ? b.seconds : b.seconds + 's'}</span> {b.text}
              <span className="block text-xs text-gray-500">Show: {b.visual}</span>
            </li>
          ))}
        </ol>
        <p className="text-sm">
          <b>{t('reelCta')}:</b> {pack.reel.cta}
        </p>
        <CopyBtn text={reelScriptText(pack.reel)} label={t('copyScript')} variant="primary" />
        <div className="border-t border-gray-100 pt-3">
          <ReelMaker source={reelsApi.forListing(pack.listing_id)} caption={pack.headline} label="Make my reel" />
        </div>
      </Card>

      <SocialPublishSection pack={pack} />

      <PublishEverywhere />
    </div>
  )
}

/** Honest placeholder: no publishing exists yet, so the connect buttons are disabled and labelled. */
export function PublishEverywhere() {
  const items = [t('connectInstagram'), t('connectFacebook'), t('connectWhatsappBusiness')]
  return (
    <section className="space-y-3 rounded-2xl border border-dashed border-gray-300 bg-gray-50 p-4" aria-label={t('publishEverywhere')}>
      <h2 className="text-lg font-bold text-gray-900">{t('publishEverywhere')}</h2>
      <p className="text-sm text-gray-600">{t('publishNote')}</p>
      {items.map((label) => (
        <button
          key={label}
          type="button"
          disabled
          className="flex min-h-[52px] w-full items-center justify-between rounded-xl border border-gray-200 bg-white px-4 text-base font-semibold text-gray-400"
        >
          <span>{label}</span>
          <span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs">{t('comingSoon')}</span>
        </button>
      ))}
    </section>
  )
}
