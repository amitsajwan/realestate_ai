'use client'
import { compressImage } from '@/lib/app/imageCompress'
import Link from 'next/link'
import React, { useEffect, useMemo, useRef, useState } from 'react'
import { ApiError } from '@/lib/app/api'
import { api, errorMessage } from '@/lib/app/client'
import { getSiteUrl } from '@/lib/app/session'
import { listingLink } from '@/lib/app/share'
import { t } from '@/lib/app/strings'
import type { AIDraft, Listing, ListingInput } from '@/lib/app/types'
import { FIELD_LABELS, lowConfidenceFields, missingFields } from '@/lib/app/validate'
import { PhotoPicker } from './PhotoPicker'
import { ReviewForm } from './ReviewForm'
import { ShareBar } from './ShareBar'
import { VoiceRecorder } from './VoiceRecorder'
import { Btn, ErrorBox, LinkBtn, Spinner, inputCls } from './ui'

type Step = 'capture' | 'drafting' | 'review' | 'posting' | 'done'

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

export function NewListingFlow() {
  const [step, setStep] = useState<Step>('capture')
  const [text, setText] = useState('')
  const [audio, setAudio] = useState<Blob | null>(null)
  const [photos, setPhotos] = useState<File[]>([])
  const [draft, setDraft] = useState<AIDraft | null>(null)
  const [form, setForm] = useState<ListingInput>({})
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)
  const [posted, setPosted] = useState<Listing | null>(null)
  const createdId = useRef<string | null>(null)
  const uploaded = useRef<{ key: string; urls: string[] } | null>(null)

  const previews = useMemo(() => photos.map((f) => URL.createObjectURL(f)), [photos])
  useEffect(() => () => previews.forEach((u) => URL.revokeObjectURL(u)), [previews])

  const view: ListingInput = {
    ...form,
    media: previews.map((url, order) => ({ url, kind: 'image' as const, order })),
  }
  const missing = missingFields(view, draft?.missing ?? [])
  const low = draft ? lowConfidenceFields(draft.confidence) : []
  const hasInput = text.trim().length > 0 || !!audio || photos.length > 0

  async function runDraft() {
    if (!hasInput) return setError(t('needSomething'))
    setError(null)
    setStep('drafting')
    try {
      const d = await api.aiDraft({ text, audio: audio ?? undefined, image_count: photos.length })
      setDraft(d)
      setForm({ visibility: 'network', ...d.draft })
      setStep('review')
    } catch (e) {
      setError(errorMessage(e))
      setStep('capture')
    }
  }

  function fillManually() {
    setDraft({ draft: {}, confidence: {}, missing: [], warnings: [] })
    setForm({ visibility: 'network', description: { en: text.trim() } })
    setStep('review')
  }

  async function confirmAndPost() {
    if (missing.length) return setError(`${t('required')}: ${missing.map((m) => FIELD_LABELS[m] ?? m).join(', ')}`)
    setError(null)
    setErrors({})
    setStep('posting')
    try {
      const key = photos.map((f) => `${f.name}:${f.size}`).join('|')
      if (!uploaded.current || uploaded.current.key !== key) {
        // Photos are optional: nothing to upload means no call (the upload endpoint rejects an empty request).
        // Compressing first keeps files small = cheap storage and fast on mobile data.
        const files = photos.length ? await api.uploadImages(await Promise.all(photos.map((p) => compressImage(p)))) : []
        uploaded.current = { key, urls: files.map((f) => f.url) }
      }
      const body = cleanInput({
        ...form,
        media: uploaded.current.urls.map((url, order) => ({ url, kind: 'image' as const, order })),
      })
      // Retry-safe: never create the same draft twice if publish fails.
      const saved = createdId.current ? await api.updateListing(createdId.current, body) : await api.createListing(body)
      createdId.current = saved.id
      setPosted(await api.publishListing(saved.id))
      setStep('done')
    } catch (e) {
      if (e instanceof ApiError && e.status === 422) setErrors(e.fields)
      setError(e instanceof ApiError && e.missing.length ? `${t('required')}: ${e.missing.map((m) => FIELD_LABELS[m] ?? m).join(', ')}` : errorMessage(e))
      setStep('review')
    }
  }

  // The capture screen stays mounted (hidden) while other steps show, so a recorded clip survives "Back".
  let overlay: React.ReactNode = null
  if (step === 'drafting') overlay = <Spinner label={t('reading')} />
  else if (step === 'posting') overlay = <Spinner label={t('posting')} />
  else if (step === 'done' && posted) {
    const link = listingLink(getSiteUrl(), posted.id)
    overlay = (
      <div className="space-y-5 text-center">
        <div className="text-5xl" aria-hidden>✅</div>
        <h1 className="text-2xl font-bold">{t('posted')}</h1>
        <p className="font-semibold">{posted.title}</p>
        <p className="break-all rounded-xl bg-white p-3 text-sm text-blue-700">{link}</p>
        <ShareBar url={link} message={`New property: ${posted.title}.`} />
        <Btn variant="secondary" onClick={() => window.location.assign('/studio/listings/new')}>{t('postAnother')}</Btn>
        <LinkBtn variant="ghost" href="/studio/listings">{t('listings')}</LinkBtn>
      </div>
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
        {draft.warnings.length > 0 && (
          <div role="alert" className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900">
            <p className="font-semibold">{t('warnings')}</p>
            <ul className="list-disc pl-5">{draft.warnings.map((w) => <li key={w}>{w}</li>)}</ul>
          </div>
        )}
        {low.length > 0 && <p className="text-sm text-amber-700">{t('pleaseCheck')}: {low.map((k) => FIELD_LABELS[k] ?? k.replace('_', ' ')).join(', ')}</p>}
        <PhotoPicker files={photos} onChange={setPhotos} />
        <ReviewForm value={view} onChange={({ media, ...rest }) => setForm(rest)} confidence={draft.confidence} missing={missing} errors={errors} />
        {error && <ErrorBox message={error} />}
        <div className="sticky bottom-0 -mx-4 border-t border-gray-200 bg-white p-4" style={{ paddingBottom: 'calc(1rem + env(safe-area-inset-bottom, 0px))' }}>
          <Btn variant="whatsapp" onClick={confirmAndPost} disabled={missing.length > 0} className="!bg-blue-600 disabled:!bg-blue-300">
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
        <Link href="/studio/listings" className="flex min-h-[44px] min-w-[44px] items-center text-xl" aria-label={t('back')}>←</Link>
        <h1 className="text-2xl font-bold">{t('addListing').replace('+ ', '')}</h1>
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
