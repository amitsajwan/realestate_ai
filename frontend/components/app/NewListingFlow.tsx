'use client'
import { compressImage } from '@/lib/app/imageCompress'
import Link from 'next/link'
import React, { useEffect, useMemo, useRef, useState } from 'react'
import { ApiError } from '@/lib/app/api'
import { api, errorMessage } from '@/lib/app/client'
import { conciergeApi, firstName } from '@/lib/app/concierge'
import { getSiteUrl } from '@/lib/app/session'
import { listingLink } from '@/lib/app/share'
import { compactAbout } from '@/lib/app/about'
import { t, type Lang } from '@/lib/app/strings'
import { MAX_BROCHURE_MB, MAX_VIDEO_MB, uploadBrochure, uploadVideo } from '@/lib/app/video'
import type { About, AIDraft, Listing, ListingInput, UploadedFile } from '@/lib/app/types'
import { qualityFields } from '@/lib/app/quality'
import { FIELD_LABELS, lowConfidenceFields, missingFields, priceSanity } from '@/lib/app/validate'
import { AboutStep } from './AboutStep'
import { MarketingRunCard } from './MarketingRunCard'
import { PhotoPicker } from './PhotoPicker'
import { ReviewForm } from './ReviewForm'
import { ShareBar } from './ShareBar'
import { VoiceRecorder } from './VoiceRecorder'
import { Btn, ErrorBox, LinkBtn, Spinner, inputCls } from './ui'
import { BRAND_NAME } from '@/lib/brand'

/** The marketing page starts the run itself when opened with ?start=1. */
export const marketingHref = (id: string, lang: Lang) => `/studio/listings/${id}/marketing?start=1&lang=${lang}`

function FilePick({ label, empty, file, accept, onPick, testid }: { label: string; empty: string; file: File | null; accept: string; onPick: (f: File | null) => void; testid: string }) {
  return (
    <div className="flex items-center gap-2">
      <label data-testid={testid} className="flex min-h-[44px] min-w-0 flex-1 cursor-pointer items-center justify-center truncate rounded-xl border border-dashed border-gray-300 p-3 text-sm font-semibold text-blue-700">
        {file ? `${label}: ${file.name}` : empty}
        <input type="file" accept={accept} className="sr-only" onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ''; if (f) onPick(f) }} />
      </label>
      {file && <button type="button" onClick={() => onPick(null)} className="min-h-[44px] min-w-[44px] text-sm font-semibold text-gray-600" aria-label={`Remove ${label}`}>✕</button>}
    </div>
  )
}

/** The builder's brochure: a first-class input next to voice, text and photos. The draft reads it. */
function BrochurePick({ file, onPick }: { file: File | null; onPick: (f: File | null) => void }) {
  return (
    <section className="space-y-1" aria-label={t('brochurePdf')}>
      <FilePick label={t('brochurePdf')} empty={`+ ${t('brochureHave')}`} file={file} accept="application/pdf,.pdf" onPick={onPick} testid="pick-brochure" />
      <p className="text-xs text-gray-500">PDF up to {MAX_BROCHURE_MB} MB.</p>
    </section>
  )
}

/** Optional builder video for a new project: picked once here, uploaded with the photos. */
function ProjectVideo({ video, onVideo }: { video: File | null; onVideo: (f: File | null) => void }) {
  return (
    <section className="space-y-1" aria-label="Project video">
      <FilePick label={t('builderVideo')} empty={`+ ${t('builderVideo')} (optional)`} file={video} accept="video/mp4,video/quicktime,video/webm,.mp4,.mov,.webm" onPick={onVideo} testid="pick-video" />
      <p className="text-xs text-gray-500">Video up to {MAX_VIDEO_MB} MB.</p>
    </section>
  )
}

type DraftPhase = 'upload' | 'read' | 'fill'
const PHASES: Array<[DraftPhase, Parameters<typeof t>[0]]> = [['upload', 'brochureStepUpload'], ['read', 'brochureStepRead'], ['fill', 'brochureStepFill']]

function BrochureProgress({ phase }: { phase: DraftPhase }) {
  const at = PHASES.findIndex(([p]) => p === phase)
  return (
    <div className="space-y-4 py-10" role="status" aria-live="polite" data-testid="brochure-progress">
      <Spinner label={t('brochureReading')} />
      <ol className="mx-auto max-w-xs space-y-2">
        {PHASES.map(([p, label], i) => (
          <li key={p} className={`flex min-h-[44px] items-center gap-3 rounded-xl px-3 text-sm font-semibold ${i === at ? 'bg-blue-50 text-blue-800' : i < at ? 'text-emerald-700' : 'text-gray-400'}`}>
            <span aria-hidden>{i < at ? '✓' : i === at ? '…' : '○'}</span>
            {t(label)}
          </li>
        ))}
      </ol>
    </div>
  )
}

type Step = 'capture' | 'drafting' | 'about' | 'review' | 'posting' | 'done'

/** Drop empty values so PATCH/POST bodies stay clean. media is set separately. */
export function cleanInput(v: ListingInput): ListingInput {
  const out: Record<string, unknown> = {}
  for (const [k, val] of Object.entries(v)) {
    if (val === undefined || val === null || val === '') continue
    if (k === 'description') {
      const d = Object.fromEntries(Object.entries(val as unknown as Record<string, string>).filter(([, s]) => s && s.trim()))
      out.description = { en: '', ...d }
      continue
    }
    out[k] = val
  }
  return out as ListingInput
}

/** The owner entering a listing for an agent (white-glove): everything is created under that agent. */
export interface OnBehalfOf {
  id: string
  name: string
}

export function NewListingFlow({ onBehalfOf }: { onBehalfOf?: OnBehalfOf } = {}) {
  const agentHome = onBehalfOf ? `/studio/agents/${encodeURIComponent(onBehalfOf.id)}` : null
  const backHref = agentHome ?? '/studio/listings'
  const [step, setStep] = useState<Step>('capture')
  const [text, setText] = useState('')
  const [audio, setAudio] = useState<Blob | null>(null)
  const [photos, setPhotos] = useState<File[]>([])
  const [newProject, setNewProject] = useState(false)
  const [brochure, setBrochure] = useState<File | null>(null)
  const [video, setVideo] = useState<File | null>(null)
  const [lang, setLang] = useState<Lang>('en')
  const [draft, setDraft] = useState<AIDraft | null>(null)
  const [phase, setPhase] = useState<DraftPhase | null>(null)
  // The brochure the draft read: its claims go with the listing only while that same file is attached.
  const readBrochure = useRef<File | null>(null)
  const [form, setForm] = useState<ListingInput>({})
  const [about, setAbout] = useState<About>({})
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)
  const [posted, setPosted] = useState<Listing | null>(null)
  const createdId = useRef<string | null>(null)
  const uploaded = useRef<{ key: string; files: UploadedFile[] } | null>(null)
  const uploadedDocs = useRef<Map<File, string>>(new Map())

  const previews = useMemo(() => photos.map((f) => URL.createObjectURL(f)), [photos])
  useEffect(() => () => previews.forEach((u) => URL.revokeObjectURL(u)), [previews])

  const view: ListingInput = {
    ...form,
    media: previews.map((url, order) => ({ url, kind: 'image' as const, order })),
  }
  const missing = missingFields(view, draft?.missing ?? [])
  // An unusual price must be confirmed on purpose; the tick is tied to the exact warning text, so changing the price clears it.
  const priceWarning = priceSanity(view)
  const [priceAck, setPriceAck] = useState<string | null>(null)
  const priceBlocked = !!priceWarning && priceAck !== priceWarning
  const low = draft ? lowConfidenceFields(draft.confidence) : []
  const hasInput = text.trim().length > 0 || !!audio || photos.length > 0 || !!brochure
  // A brochure means a builder project: no tick needed.
  const projectDefault = newProject || !!brochure

  async function runDraft() {
    if (!hasInput) return setError(t('needSomething'))
    setError(null)
    setStep('drafting')
    try {
      let brochure_url: string | undefined
      if (brochure) {
        setPhase('upload')
        brochure_url = await uploadOnce(brochure, uploadBrochure)
        setPhase('read')
      }
      const d = await api.aiDraft({ text, audio: audio ?? undefined, image_count: photos.length, brochure_url })
      if (brochure) setPhase('fill')
      readBrochure.current = brochure && d.brochure && !d.brochure.error ? brochure : null
      setDraft(d)
      const { about: found, ...rest } = d.draft
      setForm({ visibility: 'network', ...(projectDefault ? { listing_scope: 'layout' as const } : {}), ...rest })
      setAbout(found ?? {})
      setStep('about') // quick and skippable: what the assistant uses to answer buyers
    } catch (e) {
      setError(errorMessage(e))
      setStep('capture')
    } finally {
      setPhase(null)
    }
  }

  function fillManually() {
    setDraft({ draft: {}, confidence: {}, missing: [], warnings: [] })
    readBrochure.current = null
    setForm({ visibility: 'network', description: { en: text.trim() }, ...(projectDefault ? { listing_scope: 'layout' as const } : {}) })
    setAbout({})
    setStep('review')
  }

  const isProject = form.listing_scope ? form.listing_scope === 'layout' : projectDefault

  async function uploadOnce(file: File, up: (f: File) => Promise<{ url: string }>) {
    const done = uploadedDocs.current.get(file)
    if (done) return done
    const { url } = await up(file)
    uploadedDocs.current.set(file, url)
    return url
  }

  async function confirmAndPost(market: boolean) {
    if (missing.length) return setError(`${t('required')}: ${missing.map((m) => FIELD_LABELS[m] ?? m).join(', ')}`)
    if (priceBlocked) return setError('Please check the price, then tick "Yes, this price is correct".')
    setError(null)
    setErrors({})
    setStep('posting')
    try {
      const key = photos.map((f) => `${f.name}:${f.size}`).join('|')
      if (!uploaded.current || uploaded.current.key !== key) {
        // Photos are optional: nothing to upload means no call (the upload endpoint rejects an empty request).
        // Compressing first keeps files small = cheap storage and fast on mobile data.
        const files = photos.length ? await api.uploadImages(await Promise.all(photos.map((p) => compressImage(p)))) : []
        uploaded.current = { key, files }
      }
      const images = uploaded.current.files.map((f, order) => ({ url: f.url, kind: 'image' as const, order, ...qualityFields(f) }))
      const extra: Array<{ url: string; kind: 'document' | 'video'; order: number }> = []
      // The brochure was usually uploaded at Draft already: uploadOnce reuses that URL.
      if (brochure) extra.push({ url: await uploadOnce(brochure, uploadBrochure), kind: 'document', order: images.length + extra.length })
      if (isProject && video) extra.push({ url: await uploadOnce(video, uploadVideo), kind: 'video', order: images.length + extra.length })
      const claims = brochure && readBrochure.current === brochure ? draft?.brochure?.claims ?? [] : []
      const body = cleanInput({ ...form, about: compactAbout(about), media: [...images, ...extra], ...(claims.length ? { file_claims: { brochure: claims } } : {}) })
      // Retry-safe: never create the same draft twice if publish fails.
      const saved = onBehalfOf
        ? createdId.current ? await conciergeApi.updateListing(onBehalfOf.id, createdId.current, body) : await conciergeApi.createListing(onBehalfOf.id, body)
        : createdId.current ? await api.updateListing(createdId.current, body) : await api.createListing(body)
      createdId.current = saved.id
      const live = onBehalfOf ? await conciergeApi.publishListing(onBehalfOf.id, saved.id) : await api.publishListing(saved.id)
      setPosted(live)
      if (market && !onBehalfOf) return window.location.assign(marketingHref(live.id, lang))
      setStep('done')
    } catch (e) {
      if (e instanceof ApiError && e.status === 422) setErrors(e.fields)
      setError(e instanceof ApiError && e.missing.length ? `${t('required')}: ${e.missing.map((m) => FIELD_LABELS[m] ?? m).join(', ')}` : errorMessage(e))
      setStep('review')
    }
  }

  // The capture screen stays mounted (hidden) while other steps show, so a recorded clip survives "Back".
  let overlay: React.ReactNode = null
  if (step === 'drafting') overlay = phase ? <BrochureProgress phase={phase} /> : <Spinner label={t('reading')} />
  else if (step === 'posting') overlay = <Spinner label={t('posting')} />
  else if (step === 'done' && posted && onBehalfOf && agentHome) {
    overlay = (
      <div className="space-y-5" data-testid="behalf-done">
        <div className="space-y-2 text-center">
          <div className="text-5xl" aria-hidden>✅</div>
          <h1 className="text-2xl font-bold">Saved for {firstName(onBehalfOf.name)}</h1>
          <p className="font-semibold">{posted.title}</p>
          <p className="text-sm text-gray-600">It is live on his website. Open his page to post it on {BRAND_NAME}.</p>
        </div>
        <LinkBtn href={agentHome}>Back to {firstName(onBehalfOf.name)}</LinkBtn>
        <Btn variant="secondary" onClick={() => window.location.assign(`${agentHome}/listings/new`)}>{t('postAnother')}</Btn>
      </div>
    )
  } else if (step === 'done' && posted) {
    const link = listingLink(getSiteUrl(), posted.id)
    overlay = (
      <div className="space-y-5">
        <div className="space-y-2 text-center">
          <div className="text-5xl" aria-hidden>✅</div>
          <h1 className="text-2xl font-bold">{t('propertyReady')}</h1>
          <p className="font-semibold">{posted.title}</p>
          <p className="text-sm text-gray-600">{t('propertyReadySub')}</p>
        </div>
        {photos.length === 0 && (
          <div role="note" className="rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
            <p className="font-semibold">Add 3 photos to make this post much better</p>
            <p className="mt-1">Listings with real photos look far better on Facebook and Instagram. It takes a minute.</p>
            <LinkBtn variant="secondary" href={`/studio/listings/${posted.id}`}>Add photos</LinkBtn>
          </div>
        )}
        <LinkBtn href={marketingHref(posted.id, lang)}>{t('startMarketing')}</LinkBtn>
        <MarketingRunCard listingId={posted.id} />
        <section className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4">
          <p className="break-all text-sm text-blue-700">{link}</p>
          <ShareBar url={link} message={`New property: ${posted.title}.`} />
        </section>
        <Btn variant="secondary" onClick={() => window.location.assign('/studio/listings/new')}>{t('postAnother')}</Btn>
        <LinkBtn variant="ghost" href="/studio/listings">{t('listings')}</LinkBtn>
      </div>
    )
  } else if (step === 'about' && draft) {
    overlay = (
      <AboutStep
        value={about}
        onChange={setAbout}
        context={{ locality: form.locality ?? undefined, project_name: form.project_name ?? undefined, bhk: form.bhk ?? undefined, description: text || form.description?.en || '' }}
        brochureClaims={draft.brochure?.error ? [] : draft.brochure?.claims}
        onDone={() => setStep('review')}
        onSkip={() => setStep('review')}
      />
    )
  } else if (step === 'review' && draft) {
    overlay = (
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <button type="button" onClick={() => setStep('capture')} className="min-h-[44px] min-w-[44px] text-xl" aria-label={t('back')}>←</button>
          <h1 className="text-2xl font-bold">{t('review')}</h1>
        </div>
        {draft.transcript && (
          <div className="rounded-xl bg-blue-50 p-3 text-sm">
            <p className="font-semibold text-blue-800">{t('transcript')}</p>
            <p className="text-blue-900">{draft.transcript}</p>
          </div>
        )}
        {draft.brochure?.error && (
          <div role="alert" className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900" data-testid="brochure-error">
            <p className="font-semibold">{t('brochureCouldNotRead')}</p>
            <p>{draft.brochure.error}</p>
          </div>
        )}
        {draft.warnings.length > 0 && (
          <div role="alert" className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900">
            <p className="font-semibold">{t('warnings')}</p>
            <ul className="list-disc pl-5">{draft.warnings.map((w) => <li key={w}>{w}</li>)}</ul>
          </div>
        )}
        {low.length > 0 && <p className="text-sm text-amber-700">{t('pleaseCheck')}: {low.map((k) => FIELD_LABELS[k] ?? k.replace('_', ' ')).join(', ')}</p>}
        <PhotoPicker files={photos} onChange={setPhotos} />
        <BrochurePick file={brochure} onPick={setBrochure} />
        {isProject && <ProjectVideo video={video} onVideo={setVideo} />}
        <ReviewForm value={view} about={about} onEditAbout={() => setStep('about')} onChange={({ media, ...rest }) => setForm(rest)} confidence={draft.confidence} missing={missing} errors={errors}
          sources={draft.sources} reraCandidates={draft.rera_candidates}
          priceHint={draft.brochure && !draft.brochure.error && missing.length === 1 && missing[0] === 'price_inr' ? t('brochureNoPrice') : null} />
        {priceWarning && (
          <label className="flex min-h-[44px] items-center gap-3 rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm font-semibold text-amber-900">
            <input type="checkbox" className="h-5 w-5" checked={priceAck === priceWarning} onChange={(e) => setPriceAck(e.target.checked ? priceWarning : null)} />
            Yes, this price is correct
          </label>
        )}
        {error && <ErrorBox message={error} />}
        <div className="sticky bottom-0 -mx-4 border-t border-gray-200 bg-white p-4" style={{ paddingBottom: 'calc(1rem + env(safe-area-inset-bottom, 0px))' }}>
          {onBehalfOf ? (
            <Btn variant="whatsapp" onClick={() => confirmAndPost(false)} disabled={missing.length > 0 || priceBlocked} className="!bg-blue-600 disabled:!bg-blue-300">
              {t('confirmPost')}
            </Btn>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm" role="group" aria-label={t('postsIn')}>
                <span className="text-gray-600">{t('postsIn')}</span>
                {([['en', 'English'], ['mr', 'मराठी'], ['hi', 'हिन्दी']] as const).map(([l, label]) => (
                  <button key={l} type="button" aria-pressed={lang === l} onClick={() => setLang(l)}
                    className={`min-h-[44px] flex-1 rounded-lg font-semibold ${lang === l ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'}`}>{label}</button>
                ))}
              </div>
              <Btn variant="whatsapp" onClick={() => confirmAndPost(true)} disabled={missing.length > 0 || priceBlocked} className="!bg-blue-600 disabled:!bg-blue-300">
                {t('postAndMarket')}
              </Btn>
              <Btn variant="secondary" onClick={() => confirmAndPost(false)} disabled={missing.length > 0 || priceBlocked}>{t('postOnly')}</Btn>
            </div>
          )}
          {missing.length > 0 && <p className="mt-2 text-center text-xs text-red-600">{t('required')}: {missing.map((m) => FIELD_LABELS[m] ?? m).join(', ')}</p>}
        </div>
      </div>
    )
  }

  return (
    <>
      {overlay}
      <div className="space-y-5" hidden={!!overlay}>
      <div className="flex items-center gap-2">
        <Link href={backHref} className="flex min-h-[44px] min-w-[44px] items-center text-xl" aria-label={t('back')}>←</Link>
        <h1 className="text-2xl font-bold">{onBehalfOf ? `Listing for ${firstName(onBehalfOf.name)}` : t('addListing').replace('+ ', '')}</h1>
      </div>
      <textarea
        aria-label={t('describe')}
        className={`${inputCls} min-h-[150px] py-3`}
        placeholder={t('describe')}
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <VoiceRecorder onChange={setAudio} />
      <PhotoPicker files={photos} onChange={setPhotos} />
      <BrochurePick file={brochure} onPick={setBrochure} />
      <label className="flex min-h-[44px] items-center gap-3 text-sm font-semibold">
        <input type="checkbox" className="h-5 w-5" checked={newProject} onChange={(e) => setNewProject(e.target.checked)} />
        {t('newProject')}
      </label>
      {newProject && <ProjectVideo video={video} onVideo={setVideo} />}
      {error && (
        <div className="space-y-2">
          <ErrorBox message={error} />
          <Btn variant="secondary" onClick={fillManually}>Fill details myself</Btn>
        </div>
      )}
      <Btn onClick={runDraft} disabled={!hasInput}>{t('next')}</Btn>
      </div>
    </>
  )
}
