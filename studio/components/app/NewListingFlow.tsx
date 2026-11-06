'use client'
import { compressImage } from '@/lib/app/imageCompress'
import Link from 'next/link'
import React, { useEffect, useMemo, useRef, useState } from 'react'
import { ApiError } from '@/lib/app/api'
import { api, errorMessage } from '@/lib/app/client'
import { conciergeApi, firstName } from '@/lib/app/concierge'
import { getSiteUrl } from '@/lib/app/session'
import { listingHints } from '@/lib/app/listingHints'
import { listingLink } from '@/lib/app/share'
import { compactAbout } from '@/lib/app/about'
import { t } from '@shared/strings'
import { MAX_BROCHURE_MB, MAX_VIDEO_MB, uploadBrochure, uploadVideo } from '@/lib/app/video'
import type { About, AIDraft, Listing, ListingInput, UploadedFile } from '@/lib/app/types'
import { qualityFields } from '@/lib/app/quality'
import { FIELD_LABELS, lowConfidenceFields, missingFields, priceSanity } from '@/lib/app/validate'
import { AboutStep } from './AboutStep'
import { PhotoPicker } from './PhotoPicker'
import { PagePhotos, ProjectPick } from './ProjectPick'
import { ReviewForm } from './ReviewForm'
import { ShareBar } from './ShareBar'
import { VoiceRecorder } from './VoiceRecorder'
import { Btn, ErrorBox, LinkBtn, Spinner, inputCls } from './ui'
import { BRAND_NAME } from '@shared/brand'

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

/** The builder's brochure: stored with the listing, never read (reading PDFs is heavy). */
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

/** Where the agent is in Add listing: describe, check, live. */
function StepDots({ at, first = 'Describe' }: { at: 1 | 2; first?: string }) {
  const steps = [first, 'Check', 'Live']
  return (
    <ol aria-label={`Step ${at} of 3`} className="items-center gap-2 text-xs font-semibold [display:flex]">
      {steps.map((s, i) => (
        <li key={s} aria-current={i + 1 === at ? 'step' : undefined}
          className={`items-center gap-1.5 [display:flex] ${i + 1 === at ? 'text-[#0f2340]' : i + 1 < at ? 'text-green-700' : 'text-gray-400'}`}>
          <span aria-hidden className={`h-5 w-5 items-center justify-center rounded-full text-[11px] [display:flex] ${
            i + 1 === at ? 'bg-[#0f2340] text-white' : i + 1 < at ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-500'}`}>{i + 1 < at ? '✓' : i + 1}</span>
          {s}
          {i < steps.length - 1 && <span aria-hidden className="ml-0.5 h-px w-4 bg-gray-300" />}
        </li>
      ))}
    </ol>
  )
}

type Step = 'start' | 'capture' | 'drafting' | 'about' | 'review' | 'posting' | 'done'

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
  const [step, setStep] = useState<Step>('start')
  const [text, setText] = useState('')
  const [audio, setAudio] = useState<Blob | null>(null)
  const [photos, setPhotos] = useState<File[]>([])
  const [newProject, setNewProject] = useState(false)
  const [brochure, setBrochure] = useState<File | null>(null)
  const [video, setVideo] = useState<File | null>(null)
  const [draft, setDraft] = useState<AIDraft | null>(null)
  const [form, setForm] = useState<ListingInput>({})
  const [about, setAbout] = useState<About>({})
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)
  const [posted, setPosted] = useState<Listing | null>(null)
  const [pagePicked, setPagePicked] = useState<string[]>([])   // the project page's pictures this listing uses
  const createdId = useRef<string | null>(null)
  const uploaded = useRef<{ key: string; files: UploadedFile[] } | null>(null)
  const uploadedDocs = useRef<Map<File, string>>(new Map())

  const previews = useMemo(() => photos.map((f) => URL.createObjectURL(f)), [photos])
  useEffect(() => () => previews.forEach((u) => URL.revokeObjectURL(u)), [previews])

  const view: ListingInput = {
    ...form,
    media: [...pagePicked, ...previews].map((url, order) => ({ url, kind: 'image' as const, order })),
  }
  const missing = missingFields(view, draft?.missing ?? [])
  // An unusual price must be confirmed on purpose; the tick is tied to the exact warning text, so changing the price clears it.
  const priceWarning = priceSanity(view)
  const [priceAck, setPriceAck] = useState<string | null>(null)
  const priceBlocked = !!priceWarning && priceAck !== priceWarning
  const low = draft ? lowConfidenceFields(draft.confidence).filter((k) => draft.sources?.[k] !== 'maharera') : []
  const hasInput = text.trim().length > 0 || !!audio || photos.length > 0
  // A brochure means a builder project: no tick needed.
  const projectDefault = newProject || !!brochure

  /** A project we have a page for: straight to the check, with what the page holds (docs/plan/listing-flow.md). */
  async function startFromProject(regno: string) {
    setError(null)
    setStep('drafting')
    try {
      const d = await api.aiDraftProject(regno)
      const { about: found, ...rest } = d.draft
      setDraft(d)
      setForm({ visibility: 'network', ...rest })
      setAbout(found ?? {})
      setPagePicked((d.page?.photos ?? []).map((p) => p.url))
      setStep('review')
    } catch (e) {
      setError(errorMessage(e))
      setStep('start')
    }
  }

  // 'List this project' on a project's page lands here with its number
  useEffect(() => {
    const regno = new URLSearchParams(window.location.search).get('project')
    if (regno) void startFromProject(regno)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function runDraft() {
    if (!hasInput) return setError(t('needSomething'))
    setError(null)
    setStep('drafting')
    try {
      const d = await api.aiDraft({ text, audio: audio ?? undefined, image_count: photos.length })
      setDraft(d)
      const { about: found, ...rest } = d.draft
      // a draft with one carpet area is one flat even with a brochure attached (a 3 BHK went out as "Homes from ₹2.24 crore")
      const project = projectDefault && !rest.carpet_sqft
      setForm({ visibility: 'network', ...(project ? { listing_scope: 'layout' as const } : {}), ...rest })
      setAbout(found ?? {})
      // straight to the short check (owner 2026-10-19): 'About the project and area' is opened from there when wanted
      setStep('review')
    } catch (e) {
      setError(errorMessage(e))
      setStep('capture')
    }
  }

  function fillManually() {
    setDraft({ draft: {}, confidence: {}, missing: [], warnings: [] })
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

  async function confirmAndPost() {
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
      const images = [
        ...pagePicked.map((url) => ({ url, kind: 'image' as const, order: 0 })),
        ...uploaded.current.files.map((f) => ({ url: f.url, kind: 'image' as const, order: 0, ...qualityFields(f) })),
      ].map((m, order) => ({ ...m, order }))
      const extra: Array<{ url: string; kind: 'document' | 'video'; order: number }> = []
      if (brochure) extra.push({ url: await uploadOnce(brochure, uploadBrochure), kind: 'document', order: images.length + extra.length })
      if (isProject && video) extra.push({ url: await uploadOnce(video, uploadVideo), kind: 'video', order: images.length + extra.length })
      const body = cleanInput({ ...form, about: compactAbout(about), media: [...images, ...extra] })
      // Retry-safe: never create the same draft twice if publish fails.
      const saved = onBehalfOf
        ? createdId.current ? await conciergeApi.updateListing(onBehalfOf.id, createdId.current, body) : await conciergeApi.createListing(onBehalfOf.id, body)
        : createdId.current ? await api.updateListing(createdId.current, body) : await api.createListing(body)
      createdId.current = saved.id
      const live = onBehalfOf ? await conciergeApi.publishListing(onBehalfOf.id, saved.id) : await api.publishListing(saved.id)
      setPosted(live)
      setStep('done')
    } catch (e) {
      if (e instanceof ApiError && e.status === 422) setErrors(e.fields)
      setError(e instanceof ApiError && e.missing.length ? `${t('required')}: ${e.missing.map((m) => FIELD_LABELS[m] ?? m).join(', ')}` : errorMessage(e))
      setStep('review')
    }
  }

  // The capture screen stays mounted (hidden) while other steps show, so a recorded clip survives "Back".
  let overlay: React.ReactNode = null
  if (step === 'start') {
    overlay = (
      <ProjectPick title={onBehalfOf ? `Listing for ${firstName(onBehalfOf.name)}` : t('addListing').replace('+ ', '')} backHref={backHref} error={error}
        onPick={(h) => startFromProject(h.regno)} onDescribe={() => { setError(null); setStep('capture') }} />
    )
  } else if (step === 'drafting') overlay = <Spinner label={t('reading')} />
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
        {draft?.page && <a href={`/projects/${draft.page.slug}`} className="block text-center font-semibold text-blue-700 underline">See it on the project page</a>}
        {photos.length === 0 && pagePicked.length === 0 && (
          <div role="note" className="rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
            <p className="font-semibold">Add 3 photos to make this post much better</p>
            <p className="mt-1">Listings with real photos look far better on Facebook and Instagram. It takes a minute.</p>
            <LinkBtn variant="secondary" href={`/studio/listings/${posted.id}`}>Add photos</LinkBtn>
          </div>
        )}
        {/* one clear next step: marketing is a deliberate tap, never automatic (owner 2026-10-14) */}
        <LinkBtn href={`/studio/listings/${posted.id}/marketing`}>{t('startMarketing')}</LinkBtn>
        <LinkBtn variant="secondary" href={`/studio/listings/${posted.id}?tab=ai`}>Ask AI (ChatGPT / Gemini) for a picture plan and posts</LinkBtn>
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
        onDone={() => setStep('review')}
        onSkip={() => setStep('review')}
      />
    )
  } else if (step === 'review' && draft) {
    overlay = (
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <button type="button" onClick={() => setStep(draft.page ? 'start' : 'capture')} className="min-h-[44px] min-w-[44px] text-xl" aria-label={t('back')}>←</button>
          <h1 className="text-2xl font-bold">{t('review')}</h1>
        </div>
        <StepDots at={2} first={draft.page ? 'Project' : 'Describe'} />
        {draft.page?.mine && (
          <div role="alert" className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900" data-testid="already-listed">
            <p className="font-semibold">You already list this project.</p>
            <Link href={`/studio/listings/${draft.page.mine}`} className="underline">Open your listing</Link> to change it.
          </div>
        )}
        {!!draft.page?.others && !draft.page.mine && (
          <p className="rounded-xl bg-blue-50 p-3 text-sm text-blue-900" data-testid="also-listed">
            Other agents list this project too. The page shows the most complete listing, so add every size, price and photo you can.
          </p>
        )}
        {draft.transcript && (
          <div className="rounded-xl bg-blue-50 p-3 text-sm">
            <p className="font-semibold text-blue-800">{t('transcript')}</p>
            <p className="text-blue-900">{draft.transcript}</p>
          </div>
        )}
        {draft.warnings.length > 0 && (
          <div role="alert" className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900">
            <p className="font-semibold">{t('warnings')}</p>
            <ul className="list-disc pl-5">{draft.warnings.map((w) => <li key={w}>{w}</li>)}</ul>
          </div>
        )}
        {low.length > 0 && <p className="text-sm text-amber-700">{t('pleaseCheck')}: {low.map((k) => FIELD_LABELS[k] ?? k.replace('_', ' ')).join(', ')}</p>}
        {photos.length === 0 && !draft.page && <PhotoPicker files={photos} onChange={setPhotos} />}
        <ReviewForm compact maharera={draft.maharera} value={view} about={about} onEditAbout={() => setStep('about')} onChange={({ media, ...rest }) => setForm(rest)} confidence={draft.confidence} missing={missing} errors={errors}
          sources={draft.sources} reraCandidates={draft.rera_candidates} />
        {/* from a project's page the prices are the agent's job, so the pictures come after them */}
        {!!draft.page?.photos.length && <PagePhotos photos={draft.page.photos} picked={pagePicked} onChange={setPagePicked} />}
        {photos.length === 0 && !!draft.page && <PhotoPicker files={photos} onChange={setPhotos} />}
        {priceWarning && (
          <label className="flex min-h-[44px] items-center gap-3 rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm font-semibold text-amber-900">
            <input type="checkbox" className="h-5 w-5" checked={priceAck === priceWarning} onChange={(e) => setPriceAck(e.target.checked ? priceWarning : null)} />
            Yes, this price is correct
          </label>
        )}
        {error && <ErrorBox message={error} />}
        <div className="sticky bottom-0 -mx-4 border-t border-gray-200 bg-white p-4" style={{ paddingBottom: 'calc(1rem + env(safe-area-inset-bottom, 0px))' }}>
          <Btn onClick={() => confirmAndPost()} disabled={missing.length > 0 || priceBlocked}>
            {t('confirmPost')}
          </Btn>
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
      <StepDots at={1} />
      <div className="space-y-2">
        <label htmlFor="new-listing-text" className="block font-semibold text-gray-900">Describe it the way you would tell a buyer</label>
        <textarea
          id="new-listing-text"
          aria-label={t('describe')}
          rows={6}
          className={`${inputCls} !min-h-[160px] py-3`}
          placeholder="e.g. 2 BHK in Baner, 85 lakh, 950 sq ft carpet, 7th floor, ready to move, covered parking, gym and pool"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <ul aria-label="What to include" className="flex flex-wrap gap-1.5">
          {listingHints(text).map((h) => (
            <li key={h.key} data-found={h.found}
              className={`rounded-full px-2.5 py-1 text-xs font-semibold ${h.found ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
              {h.found ? '✓ ' : ''}{h.label}
            </li>
          ))}
        </ul>
      </div>
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
