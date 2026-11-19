'use client'
import React, { useState } from 'react'
import { CAPTION_MAX, CREDIT_MAX, LICENCES, areaPhotosApi, factsProblem } from '@/lib/app/areaPhotos'
import type { AreaPhotoItem, AreaPhotoList, PhotoFacts, PhotoKind, PhotoStatus } from '@/lib/app/areaPhotos'
import { errorMessage } from '@/lib/app/client'
import { compressImage } from '@/lib/app/imageCompress'
import { useAsync } from '@/lib/app/useAsync'
import { LOCALITIES } from '@shared/marketing/localities'
import { t } from '@shared/strings'
import { Btn, ErrorBox, inputCls, Spinner } from '../ui'

/** The long side sent: the backend keeps 1600 px for the page, so a phone's 4000 px photo is shrunk here first. */
const SEND_SIDE = 1600
const STATUS_WORD: Record<PhotoStatus, string> = {
  pending: 'Waiting for the owner', live: 'On the area guide', hidden: 'Hidden', suggested: 'Suggested by the photo scout',
  refused: 'Refused',
}
const STATUS_TONE: Record<PhotoStatus, string> = {
  pending: 'bg-amber-100 text-amber-900', live: 'bg-green-100 text-green-900', hidden: 'bg-gray-200 text-gray-700',
  suggested: 'bg-sky-100 text-sky-900', refused: 'bg-gray-200 text-gray-500',
}

function today(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** Pick photos, write a caption for each, and say once who took them, when, and whose they are. */
function UploadForm({ area, onDone }: { area: string; onDone: () => void }) {
  const [files, setFiles] = useState<File[]>([])
  const [captions, setCaptions] = useState<string[]>([])
  const [facts, setFacts] = useState<Omit<PhotoFacts, 'caption'>>({ taken_on: '', credit: '', kind: 'own', licence: '', source_url: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const set = (patch: Partial<typeof facts>) => setFacts({ ...facts, ...patch })

  async function send() {
    setError(null)
    if (!files.length) return setError('Choose at least one photo.')
    for (let i = 0; i < files.length; i++) {
      const problem = factsProblem({ ...facts, caption: captions[i] ?? '' }, today())
      if (problem) return setError(files.length > 1 ? `Photo ${i + 1}: ${problem}` : problem)
    }
    setBusy(true)
    try {
      for (let i = 0; i < files.length; i++) {
        const small = await compressImage(files[i], SEND_SIDE, 0.85)
        await areaPhotosApi.upload(area, small, { ...facts, caption: captions[i] })
      }
      setFiles([])
      setCaptions([])
      onDone()
    } catch (e) {
      setError(errorMessage(e))
      onDone()
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-3 rounded-2xl border border-gray-200 bg-white p-3" data-testid="area-photo-upload">
      <p className="text-sm text-gray-600">
        Only real photos: ones you or the team took, or free-licensed ones (Wikimedia Commons) with their author, licence and link.
        Never a photo from a portal or a builder&apos;s site, never an AI picture.
      </p>
      <label className="block text-sm font-semibold text-gray-800">Photos
        <input type="file" accept="image/jpeg,image/png,image/webp" multiple data-testid="area-photo-files" className="mt-1 block w-full text-sm"
          onChange={(e) => {
            const picked = Array.from(e.target.files ?? []).slice(0, 8)
            setFiles(picked)
            setCaptions(picked.map((_, i) => captions[i] ?? ''))
          }} />
      </label>
      {files.map((f, i) => (
        <label key={`${f.name}-${i}`} className="block text-xs font-semibold text-gray-700">Caption for {f.name}: what it shows and where
          <input className={inputCls} value={captions[i] ?? ''} maxLength={CAPTION_MAX} data-testid="area-photo-caption"
            placeholder="e.g. Kharadi bypass road at the EON IT Park signal"
            onChange={(e) => setCaptions(captions.map((c, j) => (j === i ? e.target.value : c)))} />
        </label>
      ))}
      <div className="grid gap-2 sm:grid-cols-2">
        <label className="text-xs font-semibold text-gray-700">Date taken
          <input type="date" className={inputCls} value={facts.taken_on} max={today()} data-testid="area-photo-date"
            onChange={(e) => set({ taken_on: e.target.value })} />
        </label>
        <label className="text-xs font-semibold text-gray-700">Who took it (or the author)
          <input className={inputCls} value={facts.credit} maxLength={CREDIT_MAX} data-testid="area-photo-credit"
            onChange={(e) => set({ credit: e.target.value })} />
        </label>
      </div>
      <fieldset className="flex flex-wrap gap-4 text-sm">
        <legend className="text-xs font-semibold text-gray-700">Whose photo</legend>
        {([['own', 'Our own (team or agent)'], ['licensed', 'Free-licensed (e.g. Wikimedia Commons)']] as [PhotoKind, string][]).map(([k, label]) => (
          <label key={k} className="flex min-h-[44px] items-center gap-2">
            <input type="radio" name="area-photo-kind" value={k} checked={facts.kind === k} onChange={() => set({ kind: k })} />{label}
          </label>
        ))}
      </fieldset>
      {facts.kind === 'licensed' && (
        <div className="grid gap-2 sm:grid-cols-2">
          <label className="text-xs font-semibold text-gray-700">Licence
            <select className={inputCls} value={facts.licence} data-testid="area-photo-licence" onChange={(e) => set({ licence: e.target.value })}>
              <option value="">Choose</option>
              {LICENCES.map((l) => <option key={l} value={l}>{l}</option>)}
            </select>
          </label>
          <label className="text-xs font-semibold text-gray-700">Link to the photo&apos;s page (https)
            <input className={inputCls} value={facts.source_url} inputMode="url" data-testid="area-photo-source"
              placeholder="https://commons.wikimedia.org/wiki/File:..." onChange={(e) => set({ source_url: e.target.value })} />
          </label>
        </div>
      )}
      {error && <ErrorBox message={error} />}
      <Btn type="button" onClick={send} disabled={busy} data-testid="area-photo-send">
        {busy ? 'Sending...' : files.length > 1 ? `Send ${files.length} photos` : 'Send photo'}
      </Btn>
    </div>
  )
}

function PhotoRow({ p, i, count, canPublish, busy, act, move }: {
  p: AreaPhotoItem; i: number; count: number; canPublish: boolean; busy: boolean
  act: (p: AreaPhotoItem, what: 'publish' | 'hide' | 'refuse') => void; move: (i: number, by: number) => void
}) {
  const suggested = p.status === 'suggested'
  return (
    <li data-testid="area-photo-row" data-status={p.status} className="flex gap-3 rounded-2xl border border-gray-200 bg-white p-3">
      <img src={p.small_url} alt={p.caption} width={96} height={72} className="h-[72px] w-24 shrink-0 rounded-lg bg-gray-100 object-cover" />
      <div className="min-w-0 flex-1 space-y-1">
        <p className="text-sm font-semibold text-gray-900">{p.caption}</p>
        <p className="text-xs text-gray-600">
          Photo: {p.credit}, {p.taken_on}{p.kind === 'licensed' && p.licence ? ` · ${p.licence}` : ''}
          {p.source_url && <> · <a href={p.source_url} target="_blank" rel="noopener noreferrer" className="underline">source</a></>}
        </p>
        {p.ai?.reason && <p className="text-xs text-sky-800" data-testid="area-photo-ai-reason">{p.ai.reason}</p>}
        <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${STATUS_TONE[p.status]}`}>{STATUS_WORD[p.status]}</span>
        {canPublish && (
          <div className="flex flex-wrap gap-1 pt-1">
            {p.status !== 'live' && (
              <button type="button" disabled={busy} onClick={() => act(p, 'publish')} data-testid="area-photo-publish"
                className="min-h-[44px] rounded-lg bg-[#102340] px-3 text-sm font-semibold text-white disabled:opacity-50">Publish</button>
            )}
            {p.status === 'live' && (
              <button type="button" disabled={busy} onClick={() => act(p, 'hide')} data-testid="area-photo-hide"
                className="min-h-[44px] rounded-lg border border-gray-300 px-3 text-sm font-semibold text-gray-800 disabled:opacity-50">Hide</button>
            )}
            {suggested && (
              <button type="button" disabled={busy} onClick={() => act(p, 'refuse')} data-testid="area-photo-refuse"
                className="min-h-[44px] rounded-lg border border-gray-300 px-3 text-sm font-semibold text-gray-800 disabled:opacity-50">Refuse</button>
            )}
            {!suggested && (
              <>
                <button type="button" aria-label="Move up" disabled={busy || i === 0} onClick={() => move(i, -1)}
                  className="h-11 w-11 rounded-lg border border-gray-200 disabled:opacity-40">↑</button>
                <button type="button" aria-label="Move down" disabled={busy || i === count - 1} onClick={() => move(i, 1)}
                  className="h-11 w-11 rounded-lg border border-gray-200 disabled:opacity-40">↓</button>
              </>
            )}
          </div>
        )}
      </div>
    </li>
  )
}

/** Studio > Area photos: real photos of each area for the top of its guide. Agents send; the owner publishes, hides, orders. */
/** `embedded`: shown as a tab of the owner's Site screen, which has its own title. */
export function AreaPhotosScreen({ embedded = false }: { embedded?: boolean } = {}) {
  const [area, setArea] = useState(LOCALITIES[0]?.key ?? 'kharadi')
  const { data, error, loading, reload, setData } = useAsync(() => areaPhotosApi.list(area), [area])
  const [busy, setBusy] = useState(false)
  const [actError, setActError] = useState<string | null>(null)
  const list = data as AreaPhotoList | null
  const items = list?.items ?? []
  const suggested = items.filter((p) => p.status === 'suggested')
  const rest = items.filter((p) => p.status !== 'suggested')
  const page = LOCALITIES.find((l) => l.key === area)

  async function run(fn: () => Promise<unknown>) {
    setBusy(true)
    setActError(null)
    try {
      await fn()
      reload()
    } catch (e) {
      setActError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  const act = (p: AreaPhotoItem, what: 'publish' | 'hide' | 'refuse') => run(() => areaPhotosApi[what](p.id))
  const publishAll = () => run(() => areaPhotosApi.publishAll(area))
  const move = (i: number, by: number) => {
    const j = i + by
    if (!list || j < 0 || j >= rest.length) return
    const next = [...rest];
    [next[i], next[j]] = [next[j], next[i]]
    setData({ ...list, items: [...suggested, ...next] })
    run(() => areaPhotosApi.reorder(area, next.map((p) => p.id)))
  }

  return (
    <div className="space-y-4 pb-4" data-testid="area-photos-screen">
      <header>
        {!embedded && <h1 className="text-2xl font-extrabold text-[#102340]">{t('areaPhotos')}</h1>}
        <p className="text-sm text-gray-600">Real photos of each area, shown at the top of its guide once the owner publishes them, with who took them and when.</p>
      </header>
      <label className="block text-sm font-semibold text-gray-800">Area
        <select className={inputCls} value={area} onChange={(e) => setArea(e.target.value)} data-testid="area-photos-area">
          {LOCALITIES.map((l) => <option key={l.key} value={l.key}>{l.name}</option>)}
        </select>
      </label>
      {page && <a href={`/localities/${page.slug}`} target="_blank" rel="noopener noreferrer" className="text-sm text-[#102340] underline">See the {page.name} guide</a>}

      <UploadForm area={area} onDone={reload} />

      {actError && <ErrorBox message={actError} />}
      {loading && !data ? <Spinner /> : error && !data ? <ErrorBox message={error} onRetry={reload} /> : (
        <>
          {suggested.length > 0 && (
            <section className="space-y-2" data-testid="area-photos-suggested">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold text-[#102340]">Suggested by the photo scout</h2>
                {list?.can_publish && (
                  <button type="button" disabled={busy} onClick={publishAll} data-testid="area-photo-publish-all"
                    className="min-h-[40px] rounded-lg bg-[#102340] px-3 text-xs font-semibold text-white disabled:opacity-50">
                    Publish all suggested
                  </button>
                )}
              </div>
              <ul className="space-y-2">
                {suggested.map((p, i) => (
                  <PhotoRow key={p.id} p={p} i={i} count={suggested.length} canPublish={!!list?.can_publish} busy={busy} act={act} move={move} />
                ))}
              </ul>
            </section>
          )}
          {rest.length === 0 ? (
            <p className="rounded-2xl bg-white p-4 text-center text-gray-600">No photos of {page?.name ?? 'this area'} yet.</p>
          ) : (
            <ul className="space-y-2">
              {rest.map((p, i) => <PhotoRow key={p.id} p={p} i={i} count={rest.length} canPublish={!!list?.can_publish} busy={busy} act={act} move={move} />)}
            </ul>
          )}
        </>
      )}
    </div>
  )
}
